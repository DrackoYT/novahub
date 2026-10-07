#!/usr/bin/env python3
"""
NovaHub — panel web para arrancar, parar y vigilar los servicios del servidor.

Sin dependencias externas: solo la librería estándar de Python 3.9+.

    python3 server.py set-password          # define o cambia la contraseña
    python3 server.py [--host H] [--port P] # arranca el panel (por defecto 127.0.0.1:8686)
"""
from __future__ import annotations

import argparse
import asyncio
import codecs
import getpass
import hashlib
import http.client
import hmac
import json
import mimetypes
import os
import re
import secrets
import shlex
import shutil
import queue
import signal
import smtplib
import socket
import ssl
import stat
import subprocess
import sys
import threading
import time
import tempfile
import traceback
from collections import deque
from functools import partial
from datetime import datetime, timedelta
from email.message import EmailMessage
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

VERSION = "1.0.5"   # versión semántica (MAYOR.MENOR.PARCHE); cada versión publicada lleva su etiqueta vX.Y.Z en git
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
mimetypes.add_type("application/manifest+json", ".webmanifest")  # manifiesto de la app (PWA)
DATA_DIR = os.path.abspath(os.environ.get("NOVAHUB_DATA", os.path.join(BASE_DIR, "data")))
STATIC_DIR = os.path.join(BASE_DIR, "static")
LOG_DIR = os.path.join(DATA_DIR, "logs")
RUN_DIR = os.path.join(DATA_DIR, "run")
SERVICES_FILE = os.path.join(DATA_DIR, "services.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
AUTH_FILE = os.path.join(DATA_DIR, "auth.json")
ROADMAP_FILE = os.path.join(DATA_DIR, "roadmap.json")
NOTIFY_FILE = os.path.join(DATA_DIR, "notify.json")
SESSION_FILE = os.path.join(DATA_DIR, "session.json")

LOG_MAX_BYTES = 5 * 1024 * 1024    # al superarlo, el log se rota a <id>.log.1
LOG_TAIL_BYTES = 64 * 1024         # lo que se envía al abrir la consola
SESSION_DEFAULTS = {"idle_minutes": 15, "max_hours": 12, "lock_on_reload": True}
MAX_AUTO_RESTARTS = 5              # reinicios rápidos seguidos; después se reintenta en modo lento
SLOW_RETRY = 300                   # modo lento: un intento cada 5 min, sin rendirse nunca
BOOT_WINDOW = 300                  # primeros 5 min tras encender el servidor: fallos pasajeros sin correo
NETWORK_WAIT = 120                 # al encender el servidor, máximo que se espera a tener red y DNS
MEM_CHECK_EVERY = 10               # segundos entre lecturas de memoria
MEM_CHECKS = 3                     # lecturas seguidas por encima del límite antes de reiniciar (≈30 s)
MEM_RESTARTS_PER_HOUR = 3          # más que esto y se deja de reiniciar: el programa necesita más memoria
GATEWAY_OFFSET = 10000             # la pasarela de un servicio publicado escucha en su puerto + 10000
HEALTH_EVERY = 30                  # segundos entre comprobaciones de salud de cada servicio
HEALTH_FAILS = 3                   # fallos seguidos antes de reiniciar (≈90 s sin responder)
HEALTH_GRACE = 60                  # tras arrancar no se comprueba: margen para que el programa se inicie
HEALTH_RESTARTS_PER_HOUR = 3
HEALTH_MODES = ("auto", "http", "tcp", "off")
SHELL = shutil.which("bash") or "/bin/sh"
CLK_TCK = os.sysconf("SC_CLK_TCK")
PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")


# ───────────────────────────── utilidades ─────────────────────────────

class ApiError(Exception):
    def __init__(self, code: int, msg: str):
        super().__init__(msg)
        self.code = code
        self.msg = msg


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def write_json(path, data, mode=0o600, indent=2):  # privados: services.json guarda variables como tokens
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, separators=None if indent else (",", ":"))
    os.replace(tmp, path)


def log_path(sid):
    return os.path.join(LOG_DIR, f"{sid}.log")


def fifo_path(sid):
    return os.path.join(RUN_DIR, f"{sid}.stdin")


def uptime():
    with open("/proc/uptime") as f:
        return float(f.read().split()[0])


def wait_for_network(timeout=NETWORK_WAIT):
    """True cuando hay DNS (al encender, el túnel fallaba por arrancar antes que el resolvedor)."""
    end = time.time() + timeout
    while time.time() < end:
        try:
            socket.getaddrinfo("cloudflare.com", 443)
            return True
        except OSError:
            time.sleep(2)
    return False


def proc_stat(pid):
    """Campos de /proc/<pid>/stat a partir del estado (índice 0 = campo 3)."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            raw = f.read()
    except OSError:
        return None
    return raw[raw.rfind(")") + 2:].split()


def proc_alive(pid, starttime):
    if not pid:
        return False
    st = proc_stat(pid)
    return bool(st) and st[0] not in ("Z", "X") and int(st[19]) == starttime


def group_usage():
    """{pgid: (ticks de CPU, bytes RSS, nº procesos)} de todos los procesos."""
    usage = {}
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        st = proc_stat(name)
        if not st:
            continue
        pgid = int(st[2])
        ticks, rss, n = usage.get(pgid, (0, 0, 0))
        usage[pgid] = (ticks + int(st[11]) + int(st[12]), rss + int(st[21]) * PAGE_SIZE, n + 1)
    for sid, (t, r, n) in CONTAINERS.usage().items():  # los contenedores cuentan como parte de su servicio
        pid = (MANAGER.state.get(sid) or {}).get("pid")
        if pid:
            a = usage.get(pid, (0, 0, 0))
            usage[pid] = (a[0] + t, a[1] + r, a[2] + n)
    return usage


def listening_ports():
    ports = set()
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(path) as f:
                next(f)
                for line in f:
                    parts = line.split()
                    if parts[3] == "0A":  # LISTEN
                        ports.add(int(parts[1].rsplit(":", 1)[1], 16))
        except OSError:
            pass
    return ports


def lan_ip():
    """IP del servidor en la red local (no envía nada: solo consulta la tabla de rutas)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return None


def system_info():
    mem = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, val = line.split(":", 1)
            mem[key] = int(val.split()[0]) * 1024
    with open("/proc/uptime") as f:
        uptime = float(f.read().split()[0])
    disk = shutil.disk_usage("/")
    return {
        "hostname": socket.gethostname(),
        "load": os.getloadavg(),
        "cpus": os.cpu_count(),
        "mem_total": mem.get("MemTotal", 0),
        "mem_used": mem.get("MemTotal", 0) - mem.get("MemAvailable", 0),
        "disk_total": disk.total,
        "disk_used": disk.used,
        "uptime": uptime,
        "lan_ip": lan_ip(),
        "user": getpass.getuser(),
        "publish_domain": PUBLISHER.domain if PUBLISHER.enabled else None,
    }


def slugify(text):
    text = text.lower()
    for a, b in (("áàä", "a"), ("éèë", "e"), ("íìï", "i"), ("óòö", "o"), ("úùü", "u"), ("ñ", "n"), ("ç", "c")):
        for ch in a:
            text = text.replace(ch, b)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:32] or "servicio"


# ───────────────────────────── contenedores (Podman) ─────────────────────────────
# Un servicio puede ser un programa (comando), un contenedor (una imagen) o un proyecto docker-compose.
# Se usa Podman sin root: los contenedores corren como el usuario, no hay servicio de root ni grupo «docker».
# El contenedor se lanza en primer plano (podman run / podman-compose up), así encaja con el resto:
# la salida va a la consola, la entrada (stdin) llega al proceso y NovaHub lo vigila como a cualquier servicio.

SERVICE_KINDS = ("process", "container", "compose")
CONTAINER_KINDS = ("container", "compose")
IMAGE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/:@-]{0,254}")
COMPOSE_FILES = ("compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml")


def container_name(sid):
    return f"novahub-{sid}"


def full_image(image):
    """docker.io/… explícito: sin TTY, Podman no puede preguntar en qué registro buscar un nombre corto."""
    first = image.split("/")[0]
    if "/" in image and ("." in first or ":" in first or first == "localhost"):
        return image
    return "docker.io/" + (image if "/" in image else f"library/{image}")


def parse_volumes(text):
    """«carpeta:/ruta/en/el/contenedor[:ro]» por línea → [(carpeta, ruta, solo_lectura)]."""
    out = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        ro = len(parts) == 3 and parts[2] == "ro"
        if len(parts) not in (2, 3) or (len(parts) == 3 and parts[2] not in ("ro", "rw")) or not parts[1].startswith("/") or not parts[0]:
            raise ApiError(400, f"Carpeta inválida: «{line}». Formato: carpeta:/ruta/en/el/contenedor (o …:ro)")
        out.append((parts[0], parts[1], ro))
    return out


def container_command(sid, svc):
    """La orden real con la que arranca un servicio de tipo contenedor o compose."""
    q = shlex.quote
    if svc.get("kind") == "compose":
        base = f"podman-compose -p {q(container_name(sid))}" + (f" -f {q(svc['compose_file'])}" if svc.get("compose_file") else "")
        # down primero: si NovaHub se cerró de golpe, los contenedores anteriores no estorban
        return f"{base} down >/dev/null 2>&1; exec {base} up"
    parts = ["exec podman run --rm --replace -i", f"--name {q(container_name(sid))}", f"--label novahub.service={q(sid)}"]
    if svc.get("port") and not re.search(r"--network[= ]host\b", svc.get("cargs") or ""):
        parts.append(f"-p {svc['port']}:{svc.get('cport') or svc['port']}")
    root = os.path.realpath(os.path.expanduser(svc.get("cwd") or "~"))
    for host, path, ro in parse_volumes(svc.get("volumes")):
        host = os.path.join(root, os.path.expanduser(host)) if not os.path.isabs(os.path.expanduser(host)) else os.path.expanduser(host)
        parts.append(f"-v {q(host + ':' + path + (':ro' if ro else ''))}")
    for k in (svc.get("env") or {}):
        parts.append(f"-e {q(k)}")  # sin valor: Podman lo toma del entorno del proceso (no aparece en «ps»)
    if svc.get("cargs"):
        parts += [q(a) for a in shlex.split(svc["cargs"])]
    parts.append(q(full_image(svc["image"])))
    if svc.get("ccmd"):
        parts += [q(a) for a in shlex.split(svc["ccmd"])]
    return " ".join(parts)


def prepare_container(sid, svc, cwd):
    """Antes de arrancar: Podman instalado, carpetas de datos creadas y fichero compose presente."""
    if not shutil.which("podman") or (svc.get("kind") == "compose" and not shutil.which("podman-compose")):
        raise ApiError(400, "Podman no está instalado: sudo apt install podman podman-compose passt uidmap")
    if svc.get("kind") == "compose":
        name = svc.get("compose_file")
        if not any(os.path.isfile(os.path.join(cwd, n)) for n in ([name] if name else COMPOSE_FILES)):
            raise ApiError(400, f"No hay {name or 'compose.yaml / docker-compose.yml'} en {cwd}")
        return
    for host, _, _ in parse_volumes(svc.get("volumes")):
        full = os.path.join(cwd, os.path.expanduser(host)) if not os.path.isabs(os.path.expanduser(host)) else os.path.expanduser(host)
        os.makedirs(full, exist_ok=True)
    if svc.get("port") and svc["port"] in listening_ports():
        killed = kill_container_orphans(sid, svc["port"])
        if killed:
            MANAGER.log(sid, f"\x1b[33mrestos de un contenedor anterior ocupaban el puerto {svc['port']}: cerrados ({len(killed)} procesos)\x1b[0m")


def kill_container_orphans(sid, port):
    """Procesos de un contenedor que Podman ya no tiene registrado (p. ej. tras un --replace a medias) pero siguen vivos
    ocupando su puerto: conmon con su nombre, sus hijos y el pasta (red) de ese puerto. Solo si Podman no conoce ningún
    contenedor con ese nombre ni que publique ese puerto."""
    name = container_name(sid)
    if subprocess.run(["podman", "container", "exists", name], capture_output=True, timeout=15).returncode == 0:
        return []  # lo conoce: --replace se encarga
    ports = subprocess.run(["podman", "ps", "--format", "{{.Ports}}"], capture_output=True, text=True, timeout=15).stdout
    if port and re.search(rf":{port}->", ports):
        return []  # el puerto es de otro contenedor que sí existe
    procs = {}
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            if os.stat(f"/proc/{pid}").st_uid != os.getuid():
                continue
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                args = [a.decode("utf-8", "replace") for a in f.read().split(b"\0") if a]
            st = proc_stat(pid)
        except OSError:
            continue
        if args and st:
            procs[int(pid)] = (os.path.basename(args[0]), args, int(st[1]))
    roots = [p for p, (exe, args, _) in procs.items()
             if (exe == "conmon" and "-n" in args and args[args.index("-n") + 1:args.index("-n") + 2] == [name])
             or (port and exe.startswith("pasta") and any(a.startswith(f"{port}-{port}:") for a in args))]
    victims = set(roots)
    while True:  # y sus hijos (el propio programa del contenedor)
        more = {p for p, (_, _, ppid) in procs.items() if ppid in victims} - victims
        if not more:
            break
        victims |= more
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for p in victims:
            try:
                os.kill(p, sig)
            except (ProcessLookupError, PermissionError):
                pass
        time.sleep(2)
    return sorted(victims)


def stop_containers(sid, svc, timeout):
    """Parada ordenada: el contenedor recibe SIGTERM y su tiempo de espera; al acabar, el proceso de
    NovaHub (podman run / compose up) termina solo."""
    q = [] if svc.get("kind") != "compose" else ["-f", svc["compose_file"]] if svc.get("compose_file") else []
    cmd = (["podman", "stop", "-t", str(timeout), container_name(sid)] if svc.get("kind") == "container"
           else ["podman-compose", "-p", container_name(sid), *q, "down", "-t", str(timeout)])
    try:
        with open(log_path(sid), "ab") as logf:
            subprocess.run(cmd, cwd=os.path.expanduser(svc.get("cwd") or "~"), stdout=logf, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL, timeout=timeout + 30)
    except (OSError, subprocess.TimeoutExpired):
        pass


class Containers:
    """CPU y memoria de los contenedores. Sus procesos no son hijos de NovaHub (los lanza conmon), así que se
    buscan por su cgroup (libpod-<id>.scope) y se suman al servicio al que pertenecen."""

    REFRESH = 15

    def __init__(self):
        self.ids, self.at = {}, 0   # id de contenedor → servicio
        self.lock = threading.Lock()

    def _refresh(self):
        try:
            res = subprocess.run(["podman", "ps", "--no-trunc", "--format", "json"], capture_output=True, text=True, timeout=10)
            items = json.loads(res.stdout or "[]")
        except (OSError, subprocess.TimeoutExpired, ValueError):
            return
        ids = {}
        for c in items:
            labels = c.get("Labels") or {}
            sid = labels.get("novahub.service")
            project = labels.get("io.podman.compose.project") or labels.get("com.docker.compose.project") or ""
            if not sid and project.startswith("novahub-"):
                sid = project[len("novahub-"):]
            if sid:
                ids[c.get("Id", "")] = sid
        self.ids = ids

    def usage(self):
        """{servicio: (ticks de CPU, bytes RSS, nº procesos)} de los servicios de tipo contenedor en marcha."""
        if MANAGER is None or not any(s.get("kind") in CONTAINER_KINDS for s in list(MANAGER.services.values())):
            return {}
        with self.lock:
            if time.time() - self.at > self.REFRESH:
                self.at = time.time()
                self._refresh()
            ids = dict(self.ids)
        if not ids:
            return {}
        out = {}
        for name in os.listdir("/proc"):
            if not name.isdigit():
                continue
            try:
                with open(f"/proc/{name}/cgroup") as f:
                    cg = f.read()
            except OSError:
                continue
            m = re.search(r"libpod-(?:conmon-)?([0-9a-f]{64})", cg)
            if not m or m.group(1) not in ids or "conmon" in m.group(0):
                continue
            st = proc_stat(name)
            if not st:
                continue
            sid = ids[m.group(1)]
            t, r, n = out.get(sid, (0, 0, 0))
            out[sid] = (t + int(st[11]) + int(st[12]), r + int(st[21]) * PAGE_SIZE, n + 1)
        return out


CONTAINERS = Containers()


# ───────────────────────────── validación ─────────────────────────────

ENV_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def normalize_service(data: dict) -> dict:
    def text(key, maxlen, required=False):
        val = str(data.get(key) or "").strip()
        if key not in ("command", "description"):
            val = re.sub(r"[\x00-\x1f\x7f]+", " ", val)  # campos de una línea: sin saltos ni controles
        if required and not val:
            raise ApiError(400, f"El campo «{key}» es obligatorio")
        if len(val) > maxlen:
            raise ApiError(400, f"El campo «{key}» es demasiado largo")
        return val

    tags = data.get("tags") or []
    if isinstance(tags, str):
        tags = tags.split(",")
    clean_tags = []
    for t in tags:
        t = str(t).strip()[:24]
        if t and t.lower() not in (x.lower() for x in clean_tags):
            clean_tags.append(t)

    env = data.get("env") or {}
    if isinstance(env, str):
        pairs = {}
        for line in env.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ApiError(400, f"Variable de entorno inválida: {line}")
            k, v = line.split("=", 1)
            pairs[k.strip()] = v.strip()
        env = pairs
    for k in env:
        if not ENV_KEY.fullmatch(k):
            raise ApiError(400, f"Nombre de variable inválido: {k}")

    cwd = text("cwd", 500)
    if cwd and not os.path.isdir(os.path.expanduser(cwd)):
        if data.get("kind") == "container":  # la carpeta de datos de un contenedor nuevo se crea sola
            try:
                os.makedirs(os.path.expanduser(cwd), mode=0o755)
            except OSError as e:
                raise ApiError(400, f"No se pudo crear la carpeta {cwd}: {e.strerror}")
        else:
            raise ApiError(400, f"El directorio no existe: {cwd}")

    port = data.get("port")
    if port in ("", None):
        port = None
    else:
        try:
            port = int(port)
        except (TypeError, ValueError):
            raise ApiError(400, "El puerto debe ser un número")
        if not 1 <= port <= 65535:
            raise ApiError(400, "Puerto fuera de rango (1-65535)")

    url = text("url", 500)
    if url and not re.match(r"https?://", url):
        raise ApiError(400, "La URL debe empezar por http:// o https://")

    try:
        stop_timeout = int(data.get("stop_timeout") or 15)
    except (TypeError, ValueError):
        raise ApiError(400, "El tiempo de parada debe ser un número")

    health_check = str(data.get("health_check") or "auto")
    if health_check not in HEALTH_MODES:
        raise ApiError(400, "Modo de comprobación de salud desconocido")
    health_path = text("health_path", 200) or "/"
    if not health_path.startswith("/"):
        raise ApiError(400, "La ruta de la comprobación de salud debe empezar por /")

    kind = str(data.get("kind") or "process")
    if kind not in SERVICE_KINDS:
        raise ApiError(400, "Tipo de servicio desconocido")
    extra = {"kind": kind}
    if kind == "container":
        image = text("image", 255, required=True)
        if not IMAGE_RE.fullmatch(image):
            raise ApiError(400, "Nombre de imagen inválido (p. ej. louislam/uptime-kuma:1)")
        cport = data.get("cport")
        if cport in ("", None):
            cport = None
        else:
            try:
                cport = int(cport)
            except (TypeError, ValueError):
                raise ApiError(400, "El puerto del contenedor debe ser un número")
            if not 1 <= cport <= 65535:
                raise ApiError(400, "Puerto del contenedor fuera de rango (1-65535)")
        volumes = str(data.get("volumes") or "").strip()[:4000]
        parse_volumes(volumes)  # valida el formato
        cargs, ccmd = text("cargs", 1000), text("ccmd", 1000)
        for label, val in (("Opciones de podman", cargs), ("Comando del contenedor", ccmd)):
            try:
                shlex.split(val)
            except ValueError as e:
                raise ApiError(400, f"{label}: {e}")
        extra.update(image=image, cport=cport, volumes=volumes, cargs=cargs, ccmd=ccmd)
    elif kind == "compose":
        compose_file = text("compose_file", 200)
        if compose_file and (os.sep in compose_file or compose_file.startswith(".")):
            raise ApiError(400, "Pon solo el nombre del archivo compose, dentro del directorio del servicio")
        extra.update(compose_file=compose_file)
    if kind in CONTAINER_KINDS and not cwd:
        raise ApiError(400, "Indica el directorio del servicio: ahí se guardan los datos del contenedor"
                            + (" y está el compose.yaml" if kind == "compose" else ""))

    memory_limit = data.get("memory_limit")
    if memory_limit in ("", None, 0, "0"):
        memory_limit = None
    else:
        try:
            memory_limit = int(memory_limit)
        except (TypeError, ValueError):
            raise ApiError(400, "El límite de memoria debe ser un número de MB")
        if not 64 <= memory_limit <= 1024 * 1024:
            raise ApiError(400, "El límite de memoria debe estar entre 64 MB y 1 TB")

    return {
        "name": text("name", 60, required=True),
        "description": text("description", 500),
        "tags": clean_tags[:12],
        "command": text("command", 4000, required=kind == "process"),
        "cwd": cwd,
        "env": {str(k): str(v) for k, v in env.items()},
        "port": port,
        "url": url,
        "stop_command": text("stop_command", 200),
        "stop_timeout": max(1, min(stop_timeout, 120)),
        "autostart": bool(data.get("autostart")),
        "restart_on_crash": bool(data.get("restart_on_crash")),
        "memory_limit": memory_limit,
        "health_check": health_check,
        "health_path": health_path,
        **extra,
    }


# ───────────────────────────── gestor de procesos ─────────────────────────────

class Manager:
    """Lanza, vigila y detiene los servicios.

    Cada servicio corre en su propia sesión (grupo de procesos = PID del líder),
    con la salida volcada a data/logs/<id>.log y la entrada leída de un FIFO.
    Así sobreviven a un reinicio del panel, que al volver los «adopta» por PID.
    """

    def __init__(self):
        self.lock = threading.RLock()
        self.services = {s["id"]: s for s in read_json(SERVICES_FILE, [])}
        self.state = read_json(STATE_FILE, {})
        self.procs = {}       # sid -> Popen (solo los lanzados por esta instancia)
        self.autostart_done = True
        self.transition = {}  # sid -> "stopping"
        self.cpu_prev = {}    # sid -> (pid, ticks, monotonic)

    # ── persistencia ──
    def save_services(self):
        write_json(SERVICES_FILE, list(self.services.values()))

    def save_state(self):
        write_json(STATE_FILE, self.state)

    def st(self, sid):
        return self.state.setdefault(sid, {})

    # ── estado ──
    def running(self, sid):
        st = self.state.get(sid) or {}
        return proc_alive(st.get("pid"), st.get("starttime"))

    def status(self, sid):
        st = self.state.get(sid) or {}
        if sid in self.transition:
            return self.transition[sid]
        if st.get("restart_at"):
            return "retrying" if st["restart_at"] - time.time() > 15 else "starting"
        if self.running(sid):
            return "running"
        return "crashed" if st.get("crashed") else "stopped"

    def log(self, sid, msg):
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"\x1b[1;35m▌NovaHub\x1b[0m \x1b[2m{stamp}\x1b[0m {msg}\n"
        with open(log_path(sid), "ab") as f:
            f.write(line.encode())

    # ── arranque ──
    def boot(self):
        died = []
        with self.lock:
            for sid in list(self.state):
                if sid not in self.services:
                    del self.state[sid]
                    continue
                st = self.state[sid]
                st.pop("restart_at", None)
                if st.get("pid") and not self.running(sid):
                    died_while_away = st.get("desired") == "running"
                    st["pid"] = None
                    st["desired"] = "stopped"
                    if died_while_away and self.services[sid].get("restart_on_crash"):
                        st["desired"] = "running"  # lo relanza el autoarranque de abajo
                        died.append(sid)
            server_booted = uptime() < BOOT_WINDOW
            if not server_booted:  # con el servidor recién encendido es lo normal, no un fallo
                for sid in died:
                    name = self.services[sid]["name"]
                    self.log(sid, "\x1b[33mse paró mientras NovaHub no estaba en marcha: se relanza\x1b[0m")
                    NOTIFIER.notify("crash", sid, f"{name} se paró mientras NovaHub estaba caído",
                                    f"«{name}» dejó de funcionar mientras NovaHub no estaba en marcha. "
                                    "Como tiene «Reiniciar si se cae», NovaHub lo ha vuelto a arrancar.", log=True)
            # Autoarranque = al encender el servidor. Si solo se reinicia NovaHub, se respeta
            # lo que se apagó a propósito (desired «stopped»).
            todo = [sid for sid, svc in self.services.items()
                    if (svc.get("autostart") or sid in died) and not self.running(sid)
                    and (server_booted or (self.state.get(sid) or {}).get("desired") != "stopped")]
            self.save_state()
        self.autostart_done = False
        if server_booted and todo:
            # recién encendido: puede no haber red todavía; se espera en segundo plano para no
            # retrasar el arranque de NovaHub (systemd espera su READY)
            threading.Thread(target=self._autostart, args=(todo, True), name="autoarranque", daemon=True).start()
        else:
            self._autostart(todo, False)

    def _autostart(self, todo, wait_network):
        if wait_network and not wait_for_network():
            for sid in todo:
                self.log(sid, "\x1b[33mtras 2 min sigue sin haber red: se arranca igualmente\x1b[0m")
        with self.lock:
            for sid in todo:
                svc = self.services.get(sid)
                if not svc or self.running(sid):
                    continue
                try:
                    self.log(sid, "autoarranque al encender el servidor" if wait_network else "autoarranque al iniciar NovaHub")
                    self.spawn(sid)
                except Exception as e:  # noqa: BLE001
                    self.log(sid, f"\x1b[31mno se pudo iniciar: {e}\x1b[0m")
                    NOTIFIER.notify("crash", sid, f"{svc['name']} no ha podido arrancar",
                                    f"El autoarranque de «{svc['name']}» ha fallado:\n{e}", level="danger")
            self.save_state()
        self.autostart_done = True

    def spawn(self, sid):
        svc = self.services[sid]
        st = self.st(sid)
        cwd = os.path.expanduser(svc.get("cwd") or "~")
        if not os.path.isdir(cwd):
            raise ApiError(400, f"El directorio no existe: {cwd}")

        path = log_path(sid)
        if os.path.exists(path) and os.path.getsize(path) > LOG_MAX_BYTES:
            os.replace(path, path + ".1")

        fifo = fifo_path(sid)
        if os.path.lexists(fifo) and not stat.S_ISFIFO(os.lstat(fifo).st_mode):
            os.remove(fifo)
        if not os.path.exists(fifo):
            os.mkfifo(fifo, 0o600)

        env = os.environ.copy()
        env.update(svc.get("env") or {})
        env.setdefault("PYTHONUNBUFFERED", "1")
        if svc.get("subdomain") and PUBLISHER.domain:
            # Vite rechaza dominios que no conoce: así acepta el suyo sin tocar vite.config.js.
            env.setdefault("__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS", PUBLISHER.host(svc["subdomain"]))
        if svc.get("port"):
            env.setdefault("NOVAHUB_SERVICE_PORT", str(svc["port"]))

        command = svc["command"]
        if svc.get("kind") in CONTAINER_KINDS:
            prepare_container(sid, svc, cwd)
            command = container_command(sid, svc)
        self.log(sid, f"iniciando \x1b[2m$ {command}\x1b[0m")
        # O_RDWR: el hijo mantiene un escritor abierto, así nunca recibe EOF
        # y el panel puede escribir en el FIFO cuando quiera.
        stdin_fd = os.open(fifo, os.O_RDWR)
        try:
            with open(path, "ab") as logf:
                proc = subprocess.Popen(
                    [SHELL, "-lc", command],
                    cwd=cwd, env=env, stdin=stdin_fd, stdout=logf, stderr=subprocess.STDOUT,
                    start_new_session=True, close_fds=True,
                )
        finally:
            os.close(stdin_fd)

        pst = proc_stat(proc.pid)
        st.update(pid=proc.pid, starttime=int(pst[19]) if pst else 0, started_at=time.time(),
                  desired="running", crashed=False, restart_at=None)
        self.procs[sid] = proc
        self.save_state()

    def start(self, sid):
        with self.lock:
            if sid in self.transition:
                raise ApiError(409, "El servicio se está deteniendo, espera un momento")
            if self.running(sid):
                return
            self.st(sid)["restarts"] = []
            self.spawn(sid)

    # ── parada ──
    def stop(self, sid, then_start=False):
        with self.lock:
            st = self.st(sid)
            st.update(desired="stopped", crashed=False, restart_at=None, down_notified=False)
            if sid in self.transition:
                return
            if not self.running(sid):
                self.save_state()
                if then_start:
                    self.start(sid)
                return
            self.transition[sid] = "stopping"
            self.save_state()
        threading.Thread(target=self._do_stop, args=(sid, then_start), daemon=True).start()

    def _reap(self, sid):
        proc = self.procs.get(sid)
        if proc is None:
            return None
        code = proc.poll()
        if code is not None:
            self.procs.pop(sid, None)
        return code

    def _do_stop(self, sid, then_start):
        with self.lock:
            svc = dict(self.services.get(sid) or {})
            st = self.st(sid)
            pid, starttime = st.get("pid"), st.get("starttime")

        def wait(seconds):
            end = time.time() + seconds
            while time.time() < end:
                if not proc_alive(pid, starttime):
                    return True
                time.sleep(0.2)
            return not proc_alive(pid, starttime)

        def kill(sig):
            try:
                os.killpg(pid, sig)
            except (ProcessLookupError, PermissionError):
                pass

        try:
            done = False
            timeout = svc.get("stop_timeout", 15)
            if svc.get("stop_command"):
                self.log(sid, f"enviando comando de parada «{svc['stop_command']}»")
                try:
                    self.write_stdin(sid, svc["stop_command"])
                    done = wait(timeout)
                except OSError:
                    pass
            if not done and svc.get("kind") in CONTAINER_KINDS:
                self.log(sid, "deteniendo el contenedor…")
                stop_containers(sid, svc, timeout)
                done = wait(10)
            if not done:
                self.log(sid, "deteniendo (SIGTERM)…")
                kill(signal.SIGTERM)
                done = wait(10 if svc.get("stop_command") else timeout)
            if not done:
                self.log(sid, "\x1b[33mno responde, forzando el cierre (SIGKILL)\x1b[0m")
                kill(signal.SIGKILL)
                wait(5)
            kill(signal.SIGKILL)  # restos del grupo que hayan quedado vivos
        finally:
            with self.lock:
                code = self._reap(sid)
                st.update(pid=None, last_exit=code, last_exit_at=time.time())
                self.log(sid, "detenido" + (f" (código {code})" if code is not None else ""))
                self.transition.pop(sid, None)
                self.save_state()
                if then_start and sid in self.services:
                    try:
                        self.start(sid)
                    except ApiError as e:
                        self.log(sid, f"\x1b[31m{e.msg}\x1b[0m")

    def restart(self, sid):
        self.stop(sid, then_start=True)

    # ── entrada estándar ──
    def write_stdin(self, sid, line):
        fd = os.open(fifo_path(sid), os.O_WRONLY | os.O_NONBLOCK)
        try:
            os.write(fd, (line + "\n").encode())
        finally:
            os.close(fd)

    def send_input(self, sid, line):
        if not self.running(sid):
            raise ApiError(409, "El servicio no está en marcha")
        try:
            self.write_stdin(sid, line)
        except OSError as e:
            raise ApiError(500, f"No se pudo escribir en el proceso: {e}")
        with open(log_path(sid), "ab") as f:
            f.write(f"\x1b[36m› {line}\x1b[0m\n".encode())

    # ── vigilancia ──
    def monitor(self):
        tick = 0
        while True:
            time.sleep(1)
            tick += 1
            SUPERVISOR.beat("vigilancia")
            try:
                with self.lock:
                    self._check_all(rotate=tick % 30 == 0)
                if tick % MEM_CHECK_EVERY == 0:
                    usage = group_usage()  # fuera del lock: recorre todo /proc
                    with self.lock:
                        self._check_memory(usage)
                if tick % 5 == 0:
                    GATEWAY.sync()
            except Exception:  # noqa: BLE001
                traceback.print_exc()

    def _check_memory(self, usage):
        """Reinicia los servicios que pasan de su límite de memoria durante ~30 s seguidos."""
        now = time.time()
        for sid, svc in self.services.items():
            st = self.state.get(sid)
            limit = svc.get("memory_limit")
            if not st:
                continue
            if not limit or sid in self.transition or not self.running(sid):
                st.pop("mem_over", None)
                continue
            rss = usage.get(st["pid"], (0, 0, 0))[1]
            if rss <= limit * 2**20:
                st.pop("mem_over", None)
                continue
            st["mem_over"] = st.get("mem_over", 0) + 1
            if st["mem_over"] < MEM_CHECKS:
                continue
            st["mem_over"] = 0
            recent = [t for t in st.get("mem_restarts", []) if now - t < 3600]
            used = f"{rss / 2**20:.0f} MB"
            if len(recent) >= MEM_RESTARTS_PER_HOUR:
                if not st.get("mem_gave_up"):
                    st["mem_gave_up"] = True
                    self.log(sid, f"\x1b[31musa {used} (límite {limit} MB), pero ya se ha reiniciado {len(recent)} veces "
                                  "en la última hora: no se vuelve a reiniciar. Sube el límite o revisa el programa.\x1b[0m")
                    NOTIFIER.notify("memory", sid, f"{svc['name']} usa demasiada memoria",
                                    f"«{svc['name']}» usa {used} (límite {limit} MB) y ya se ha reiniciado {len(recent)} veces "
                                    "en la última hora, así que NovaHub ha dejado de reiniciarlo. Sube el límite o revisa el programa.",
                                    key="gaveup")
                    self.save_state()
                continue
            st["mem_gave_up"] = False
            recent.append(now)
            st["mem_restarts"] = recent
            self.log(sid, f"\x1b[33musa {used} de memoria (límite {limit} MB) desde hace "
                          f"{MEM_CHECKS * MEM_CHECK_EVERY} s: reiniciando\x1b[0m")
            NOTIFIER.notify("memory", sid, f"{svc['name']} se ha reiniciado por memoria",
                            f"«{svc['name']}» usaba {used} de memoria (límite {limit} MB) durante "
                            f"{MEM_CHECKS * MEM_CHECK_EVERY} s y se ha reiniciado.")
            self.save_state()
            self.stop(sid, then_start=True)

    def _check_all(self, rotate):
        now = time.time()
        for sid, svc in list(self.services.items()):
            st = self.state.get(sid)
            if not st or sid in self.transition:
                continue

            if st.get("restart_at") and now >= st["restart_at"]:
                try:
                    self.spawn(sid)
                except ApiError as e:
                    st.update(restart_at=None, crashed=True, desired="stopped")
                    self.log(sid, f"\x1b[31m{e.msg}\x1b[0m")
                continue

            if rotate and self.running(sid):
                self._rotate_live(sid)

            if self.running(sid):
                # lleva 2 min estable después de haber fallado en serio: se avisa de que ha vuelto
                if st.get("down_notified") and now - (st.get("started_at") or now) > 120:
                    st["down_notified"] = False
                    NOTIFIER.notify("crash", sid, f"{svc['name']} vuelve a funcionar",
                                    f"«{svc['name']}» lleva 2 minutos en marcha sin fallar.", level="ok", key="recovered")
                    self.save_state()
                continue
            if not st.get("pid"):
                continue

            # El proceso ha terminado sin que lo pidiéramos.
            code = self._reap(sid)
            st.update(pid=None, last_exit=code, last_exit_at=now)
            color = "32" if code == 0 else "31"
            self.log(sid, f"\x1b[{color}mel proceso ha terminado"
                          + (f" (código {code})" if code is not None else "") + "\x1b[0m")
            if st.get("desired") == "running" and svc.get("restart_on_crash") and code != 0:
                history = [t for t in st.get("restarts", []) if now - t < 3600]  # se muestra en la ficha (1 h)
                recent = [t for t in history if now - t < 60]                    # rápidos: por minuto
                st["restarts"] = history + [now]
                booting = uptime() < BOOT_WINDOW  # recién encendido: los fallos pasajeros no merecen correo
                if len(recent) < MAX_AUTO_RESTARTS:
                    delay = 2 * (len(recent) + 1)
                    st["restart_at"] = now + delay
                    self.log(sid, f"reinicio automático en {delay} s "
                                  f"(intento {len(recent) + 1}/{MAX_AUTO_RESTARTS})")
                    if not booting and not st.get("down_notified"):
                        NOTIFIER.notify("crash", sid, f"{svc['name']} se ha caído",
                                        f"«{svc['name']}» {_ended(code)} y se está reiniciando solo.",
                                        log=True, level="warning")
                else:
                    # Ya no son fallos pasajeros: se sigue intentando, pero cada 5 min (p. ej. sin internet
                    # un buen rato). Nunca se abandona del todo: el túnel debe volver solo.
                    st["restart_at"] = now + SLOW_RETRY
                    self.log(sid, f"\x1b[31mfalla una y otra vez: se reintentará cada {SLOW_RETRY // 60} min "
                                  "(apágalo si no quieres que siga intentándolo)\x1b[0m")
                    if not st.get("down_notified"):
                        st["down_notified"] = True
                        NOTIFIER.notify("crash", sid, f"{svc['name']} falla una y otra vez",
                                        f"«{svc['name']}» se ha caído {MAX_AUTO_RESTARTS} veces seguidas. NovaHub lo seguirá "
                                        f"intentando cada {SLOW_RETRY // 60} minutos y te avisará cuando vuelva a funcionar.",
                                        log=True, key="gaveup", level="danger")
            elif st.get("desired") == "running" and code != 0:
                st["crashed"] = True
                st["desired"] = "stopped"
                NOTIFIER.notify("crash", sid, f"{svc['name']} se ha caído",
                                f"«{svc['name']}» {_ended(code)}. No tiene activado «Reiniciar si se "
                                "cae», así que sigue parado.", log=True, level="danger")
            else:
                st["crashed"] = code not in (0, None)
                st["desired"] = "stopped"
            self.save_state()

    def _rotate_live(self, sid):
        path = log_path(sid)
        try:
            if os.path.getsize(path) > LOG_MAX_BYTES:
                shutil.copyfile(path, path + ".1")
                os.truncate(path, 0)  # el hijo escribe con O_APPEND: sigue al final
        except OSError:
            pass

    # ── CRUD ──
    def create(self, data, extra=None):
        svc = {**normalize_service(data), **(extra or {})}
        with self.lock:
            base = slugify(svc["name"])
            sid = base
            while sid in self.services:
                sid = f"{base}-{secrets.token_hex(2)}"
            svc = {"id": sid, **svc, "created_at": time.time()}
            if svc.get("kind") in CONTAINER_KINDS:
                svc["command"] = container_command(sid, svc)  # para verlo en la ficha; al arrancar se recalcula
            self.services[sid] = svc
            self.save_services()
            return sid

    def update(self, sid, data, extra=None):
        svc = {**normalize_service(data), **(extra or {})}
        with self.lock:
            merged = {**self.services[sid], **svc}
            if merged.get("kind") in CONTAINER_KINDS:
                merged["command"] = container_command(sid, merged)
            self.services[sid] = merged
            self.save_services()

    def delete(self, sid):
        with self.lock:
            if self.running(sid) or sid in self.transition:
                raise ApiError(409, "Detén el servicio antes de eliminarlo")
            if (self.state.get(sid) or {}).get("updating"):
                raise ApiError(409, "Espera a que termine de actualizarse antes de eliminarlo")
            self.services.pop(sid, None)
            self.state.pop(sid, None)
            self.save_services()
            self.save_state()
            for path in (log_path(sid), log_path(sid) + ".1", fifo_path(sid)):
                try:
                    os.remove(path)
                except FileNotFoundError:
                    pass
            shutil.rmtree(os.path.join(BUILDS_DIR, sid), ignore_errors=True)  # compilaciones de producción

    def clear_log(self, sid):
        try:
            os.truncate(log_path(sid), 0)
        except FileNotFoundError:
            pass

    # ── serialización ──
    def public(self, sid, usage, ports):
        svc = self.services[sid]
        st = self.state.get(sid) or {}
        running = self.running(sid)
        out = dict(svc)
        out.update(
            status=self.status(sid),
            pid=st.get("pid") if running else None,
            started_at=st.get("started_at") if running else None,
            uptime=time.time() - st["started_at"] if running and st.get("started_at") else None,
            last_exit=st.get("last_exit"),
            last_exit_at=st.get("last_exit_at"),
            auto_restarts=len([t for t in st.get("restarts", []) if time.time() - t < 3600]),
            updating=bool(st.get("updating")), last_update=st.get("last_update"),
            mem_restarts=len([t for t in st.get("mem_restarts", []) if time.time() - t < 3600]),
            health_mode=health_mode(svc), health=st.get("health"),
            mode=svc.get("mode", "dev"), can_build=build_info(svc) is not None,
            listening=(svc["port"] in ports) if svc.get("port") else None,
            backup={k: (st.get("backup") or {}).get(k) for k in ("last_name", "last_ok_at")},
            signups=CATALOG.signups_public(sid, svc) if svc.get("catalog") else None,
            cpu=None, memory=None, processes=None,
        )
        if running:
            pid = st["pid"]
            ticks, rss, n = usage.get(pid, (0, 0, 0))
            now = time.monotonic()
            prev = self.cpu_prev.get(sid)
            if prev and prev[0] == pid and now - prev[2] > 0.2:
                out["cpu"] = round((ticks - prev[1]) / CLK_TCK / (now - prev[2]) * 100, 1)
            if not prev or now - prev[2] > 0.2:
                self.cpu_prev[sid] = (pid, ticks, now)
            out.update(memory=rss, processes=n)
        return out

    def list_public(self):
        usage, ports = group_usage(), listening_ports()
        with self.lock:
            return [self.public(sid, usage, ports) for sid in self.services]

    def get_public(self, sid):
        usage, ports = group_usage(), listening_ports()
        with self.lock:
            return self.public(sid, usage, ports)


# ───────────────────────────── autenticación ─────────────────────────────

USERS_FILE = os.path.join(DATA_DIR, "users.json")
# Permisos por rol. «edit» y «admin» son solo del administrador; operador y lector pueden limitarse a algunos servicios.
ROLES = {
    "admin": {"view", "operate", "console", "edit", "admin"},
    "operator": {"view", "operate", "console"},
    "viewer": {"view"},
}
ROLE_LABELS = {"admin": "Administrador", "operator": "Operador", "viewer": "Lector"}
USERNAME_RE = re.compile(r"[a-z0-9][a-z0-9._-]{1,31}")


class Auth:
    """Usuarios con contraseña (PBKDF2) y sesiones firmadas «emitido:caduca:usuario:versión.firma».
    La versión cambia al cambiar la contraseña o el rol del usuario: así se cierran sus sesiones abiertas."""

    ITERATIONS = 600_000

    def __init__(self):
        self.data = read_json(AUTH_FILE, {})
        self.users = read_json(USERS_FILE, {})
        self.users_mtime = self._mtime()
        self.lock = threading.Lock()
        self.fails = {}    # ip -> [timestamps]
        self.revoked = {}  # «usuario:emitido» de la sesión -> caducidad máxima (sesiones cerradas antes de caducar)
        if not self.users and self.data.get("password"):
            # De la contraseña única de antes al primer usuario administrador (el usuario del sistema)
            name = re.sub(r"[^a-z0-9._-]", "", getpass.getuser().lower()) or "admin"
            name = name if USERNAME_RE.fullmatch(name) else "admin"
            self.users = {name: {"name": name, "role": "admin", "services": "*", "password": self.data["password"],
                                 "ver": 1, "created": time.time()}}
            write_json(USERS_FILE, self.users, mode=0o600)
            self.data.pop("password", None)
            write_json(AUTH_FILE, self.data, mode=0o600)

    def configured(self):
        return bool(self.users) and bool(self.data.get("secret"))

    def _hash(self, password):
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), self.ITERATIONS).hex()
        return f"pbkdf2_sha256${self.ITERATIONS}${salt}${digest}"

    @staticmethod
    def _verify(stored, password):
        try:
            _, iterations, salt, digest = stored.split("$")
        except (AttributeError, ValueError):
            return False
        test = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return hmac.compare_digest(test, digest)

    def _save_users(self):
        write_json(USERS_FILE, self.users, mode=0o600)
        self.users_mtime = self._mtime()

    @staticmethod
    def _mtime():
        try:
            return os.path.getmtime(USERS_FILE)
        except OSError:
            return None

    def _fresh(self):
        """Si users.json ha cambiado por fuera (python3 server.py set-password con NovaHub en marcha), se relee."""
        m = self._mtime()
        if m != self.users_mtime:
            self.users, self.users_mtime = read_json(USERS_FILE, self.users), m

    def set_password(self, password, username=None):
        """Desde la línea de órdenes (python3 server.py set-password [usuario]): crea o cambia un administrador."""
        with self.lock:
            if not self.data.get("secret"):
                self.data["secret"] = secrets.token_hex(32)
                write_json(AUTH_FILE, self.data, mode=0o600)
            if not username:
                username = next((u for u, d in self.users.items() if d["role"] == "admin"), None) \
                    or re.sub(r"[^a-z0-9._-]", "", getpass.getuser().lower()) or "admin"
            if not USERNAME_RE.fullmatch(username):
                raise ApiError(400, "Nombre de usuario inválido: letras minúsculas, números, punto, guion o _ (2–32)")
            u = self.users.get(username) or {"name": username, "role": "admin", "services": "*", "ver": 0, "created": time.time()}
            u.update(password=self._hash(password), ver=u.get("ver", 0) + 1)
            self.users[username] = u
            self._save_users()
            return username

    def login(self, username, password):
        """El usuario si la contraseña es correcta; si no, None (con el mismo coste aunque el usuario no exista)."""
        self._fresh()
        username = str(username or "").strip().lower()
        if not username and len(self.users) == 1:
            username = next(iter(self.users))  # compatibilidad: el formulario antiguo solo pedía contraseña
        u = self.users.get(username)
        ok = self._verify(u["password"] if u else f"pbkdf2_sha256${self.ITERATIONS}${'0' * 32}${'0' * 64}", password)
        if not (u and ok):
            return None
        with self.lock:
            u["last_login"] = time.time()
            self._save_users()
        return username

    # ── usuarios (solo administradores) ──
    def public_user(self, username):
        u = self.users[username]
        return {"username": username, "name": u.get("name") or username, "role": u["role"], "role_label": ROLE_LABELS[u["role"]],
                "services": u.get("services", "*"), "perms": sorted(ROLES[u["role"]]),
                "created": u.get("created"), "last_login": u.get("last_login")}

    def list_users(self):
        return [self.public_user(n) for n in sorted(self.users)]

    def _clean_user(self, data, current=None):
        name = re.sub(r"[\x00-\x1f\x7f]", "", str(data.get("name", (current or {}).get("name", "")) or "")).strip()[:60]
        role = data.get("role", (current or {}).get("role", "viewer"))
        if role not in ROLES:
            raise ApiError(400, "Rol desconocido")
        services = data.get("services", (current or {}).get("services", "*"))
        if services != "*":
            if not isinstance(services, list):
                raise ApiError(400, "Lista de servicios no válida")
            services = sorted({str(x) for x in services if str(x) in MANAGER.services})
        return name, role, "*" if role == "admin" else services

    def _check_password_rules(self, password):
        if len(password) < 8:
            raise ApiError(400, "La contraseña debe tener al menos 8 caracteres")
        if len(password) > 200:
            raise ApiError(400, "La contraseña es demasiado larga")

    def create_user(self, data):
        username = str(data.get("username") or "").strip().lower()
        if not USERNAME_RE.fullmatch(username):
            raise ApiError(400, "Nombre de usuario inválido: letras minúsculas, números, punto, guion o _ (2–32)")
        password = str(data.get("password") or "")
        self._check_password_rules(password)
        name, role, services = self._clean_user(data)
        with self.lock:
            self._fresh()
            if username in self.users:
                raise ApiError(409, "Ya existe un usuario con ese nombre")
            self.users[username] = {"name": name or username, "role": role, "services": services,
                                    "password": self._hash(password), "ver": 1, "created": time.time()}
            self._save_users()
        return self.public_user(username)

    def update_user(self, username, data, actor):
        with self.lock:
            self._fresh()
            u = self.users.get(username)
            if not u:
                raise ApiError(404, "Ese usuario no existe")
            name, role, services = self._clean_user(data, u)
            if u["role"] == "admin" and role != "admin":
                if username == actor:
                    raise ApiError(400, "No puedes quitarte a ti mismo el rol de administrador")
                if sum(1 for d in self.users.values() if d["role"] == "admin") <= 1:
                    raise ApiError(400, "Tiene que quedar al menos un administrador")
            changed = role != u["role"] or services != u.get("services", "*")
            u.update(name=name or username, role=role, services=services)
            if data.get("password"):
                self._check_password_rules(str(data["password"]))
                u["password"] = self._hash(str(data["password"]))
                changed = True
            if changed:
                u["ver"] = u.get("ver", 0) + 1  # sus sesiones abiertas se cierran: vuelven a entrar con lo nuevo
            self._save_users()
        return self.public_user(username)

    def delete_user(self, username, actor):
        with self.lock:
            self._fresh()
            if username not in self.users:
                raise ApiError(404, "Ese usuario no existe")
            if username == actor:
                raise ApiError(400, "No puedes borrar tu propio usuario")
            if self.users[username]["role"] == "admin" and sum(1 for d in self.users.values() if d["role"] == "admin") <= 1:
                raise ApiError(400, "Tiene que quedar al menos un administrador")
            del self.users[username]
            self._save_users()

    def change_own_password(self, username, current, new):
        if not self._verify(self.users[username]["password"], str(current or "")):
            raise ApiError(400, "La contraseña actual no es correcta")
        self._check_password_rules(str(new or ""))
        with self.lock:
            u = self.users[username]
            u.update(password=self._hash(str(new)), ver=u.get("ver", 0) + 1)
            self._save_users()

    def _sign(self, payload):
        return hmac.new(self.data["secret"].encode(), payload.encode(), hashlib.sha256).hexdigest()

    # ── sesiones: caducan tras X min sin actividad del usuario y, en todo caso, a las N horas ──
    @staticmethod
    def settings():
        cfg = {**SESSION_DEFAULTS, **read_json(SESSION_FILE, {})}
        return {"idle_minutes": int(cfg["idle_minutes"]), "max_hours": int(cfg["max_hours"]),
                "lock_on_reload": bool(cfg["lock_on_reload"])}

    @staticmethod
    def save_settings(data):
        cfg = Auth.settings()
        try:
            idle = int(data.get("idle_minutes", cfg["idle_minutes"]))
            max_hours = int(data.get("max_hours", cfg["max_hours"]))
        except (TypeError, ValueError):
            raise ApiError(400, "Los tiempos de la sesión deben ser números")
        if not 1 <= idle <= 24 * 60:
            raise ApiError(400, "El cierre por inactividad debe estar entre 1 minuto y 24 horas")
        if not 1 <= max_hours <= 24 * 30:
            raise ApiError(400, "La duración máxima de la sesión debe estar entre 1 hora y 30 días")
        cfg.update(idle_minutes=idle, max_hours=max_hours,
                   lock_on_reload=bool(data.get("lock_on_reload", cfg["lock_on_reload"])))
        write_json(SESSION_FILE, cfg)
        return cfg

    def make_token(self, username, issued=None):
        """Token «emitido:caduca:usuario:versión.firma». Caduca tras la inactividad, nunca después del máximo absoluto."""
        cfg, now = self.settings(), int(time.time())
        issued = issued or now
        expires = min(now + cfg["idle_minutes"] * 60, issued + cfg["max_hours"] * 3600)
        payload = f"{issued}:{expires}:{username}:{self.users[username].get('ver', 0)}"
        return f"{payload}.{self._sign(payload)}"

    def parse_token(self, token):
        """(emitido, caduca, usuario) si el token es auténtico, vigente, de un usuario que existe con la misma
        versión (no ha cambiado su contraseña ni su rol) y la sesión no se ha cerrado; si no, None."""
        if not token or "." not in token or not self.configured():
            return None
        payload, sig = token.rsplit(".", 1)
        if not hmac.compare_digest(sig, self._sign(payload)):
            return None
        self._fresh()
        try:
            issued, expires, username, ver = payload.split(":")
            issued, expires, ver = int(issued), int(expires), int(ver)
        except ValueError:
            return None
        u = self.users.get(username)
        if not u or u.get("ver", 0) != ver:
            return None
        if f"{username}:{issued}" in self.revoked:  # sesión cerrada: vale para todos sus tokens, también los renovados
            return None
        return (issued, expires, username) if expires > time.time() else None

    def valid_token(self, token):
        return self.parse_token(token) is not None

    def revoke(self, token):
        """Cerrar sesión invalida el token en el servidor, no solo en el navegador."""
        parsed = self.parse_token(token)
        if parsed:
            now = time.time()
            self.revoked = {i: exp for i, exp in self.revoked.items() if exp > now}  # limpia los caducados
            # ningún token de esta sesión puede durar más que su máximo absoluto
            self.revoked[f"{parsed[2]}:{parsed[0]}"] = max(parsed[1], parsed[0] + self.settings()["max_hours"] * 3600)

    def throttled(self, ip):
        now = time.time()
        for key in list(self.fails):  # limpia también las IPs antiguas
            self.fails[key] = [t for t in self.fails[key] if now - t < 300]
            if not self.fails[key]:
                del self.fails[key]
        return len(self.fails.get(ip, [])) >= 5

    def failed(self, ip):
        self.fails.setdefault(ip, []).append(time.time())


# ───────────────────────────── túnel de Cloudflare ─────────────────────────────

SUBDOMAIN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")
TUNNEL_CMD = re.compile(r"\bcloudflared\b.*\btunnel\b.*\brun\b")


class Publisher:
    """Publica servicios en <subdominio>.<NOVAHUB_DOMAIN> a través del túnel de cloudflared.

    Crea el CNAME con `cloudflared tunnel route dns` (usa ~/.cloudflared/cert.pem) y
    mantiene una regla de ingress por servicio en el config.yml del túnel. Los registros
    DNS no se borran al despublicar: cloudflared no sabe hacerlo.
    """

    def __init__(self):
        self.domain = os.environ.get("NOVAHUB_DOMAIN", "").strip().strip(".").lower()
        self.config = os.path.expanduser(os.environ.get("NOVAHUB_CLOUDFLARED_CONFIG", "~/.cloudflared/config.yml"))
        self.bin = shutil.which("cloudflared")
        self.lock = threading.Lock()

    @property
    def enabled(self):
        return bool(self.domain and self.bin and os.path.isfile(self.config))

    def host(self, sub):
        return f"{sub}.{self.domain}" if sub else None

    def tunnel(self):
        name = os.environ.get("NOVAHUB_TUNNEL", "").strip()
        if not name:
            m = re.search(r"^tunnel:\s*['\"]?([^'\"\s#]+)", "".join(self.read()), re.M)
            name = m.group(1) if m else ""
        if not name:
            raise ApiError(500, f"No se sabe qué túnel usar: define NOVAHUB_TUNNEL o «tunnel:» en {self.config}")
        return name

    # ── config.yml ──
    def read(self):
        with open(self.config, encoding="utf-8") as f:
            return f.readlines()

    def entries(self, lines):
        """[(inicio, fin, hostname, service)] de cada regla de la lista `ingress:`."""
        start = next((i for i, l in enumerate(lines) if re.match(r"ingress:\s*(#.*)?$", l)), None)
        if start is None:
            raise ApiError(500, f"No hay sección «ingress:» en {self.config}")
        out, dash, i = [], None, start + 1
        while i < len(lines):
            line = lines[i]
            indent = len(line) - len(line.lstrip(" "))
            is_item = line.lstrip(" ").startswith("- ")
            if line.strip() and not line.lstrip().startswith("#"):
                if dash is None and is_item:
                    dash = indent
                if is_item and indent == dash:
                    j = i + 1
                    while j < len(lines) and (not lines[j].strip()
                                              or len(lines[j]) - len(lines[j].lstrip(" ")) > dash):
                        j += 1
                    block = "".join(lines[i:j])
                    h = re.search(r"hostname:\s*['\"]?([^'\"\s#]+)", block)
                    s = re.search(r"service:\s*['\"]?([^'\"\s#]+)", block)
                    out.append((i, j, h.group(1).lower() if h else None, s.group(1) if s else None))
                    i = j
                    continue
                if dash is None or indent <= dash:
                    break
            i += 1
        return out, (dash if dash is not None else 2), i

    def find(self, lines, host):
        return next((e for e in self.entries(lines)[0] if e[2] == host), None)

    def upsert(self, lines, host, target):
        entries, dash, end = self.entries(lines)
        pad = " " * dash
        block = [f"{pad}- hostname: {host}\n", f"{pad}  service: {target}\n"]
        old = next((e for e in entries if e[2] == host), None)
        if old:
            return lines[:old[0]] + block + lines[old[1]:]
        # delante de la regla final sin hostname (el 404 de recogida)
        at = next((e[0] for e in entries if e[2] is None), end)
        return lines[:at] + block + lines[at:]

    def remove(self, lines, host):
        old = self.find(lines, host)
        return lines[:old[0]] + lines[old[1]:] if old else lines

    def dump(self, lines):
        tmp = self.config + ".tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.writelines(lines)
        os.replace(tmp, self.config)

    def write(self, lines):
        backup = self.read()
        self.dump(lines)
        res = self.run("tunnel", "--config", self.config, "ingress", "validate")
        if res.returncode != 0:
            self.dump(backup)  # config inválida: se deja la anterior
            raise ApiError(500, f"La configuración del túnel no es válida: {self.error_text(res)}")

    # ── cloudflared ──
    def run(self, *args, timeout=60):
        try:
            return subprocess.run([self.bin, *args], capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise ApiError(504, "cloudflared no responde (¿hay conexión con Cloudflare?)")

    @staticmethod
    def error_text(res):
        lines = [re.sub(r"^\S+Z\s+\w{3}\s+", "", l).strip() for l in (res.stderr + res.stdout).splitlines() if l.strip()]
        return next((l for l in reversed(lines) if "error" in l.lower() or "fail" in l.lower()),
                    lines[-1] if lines else "error desconocido")

    def route_dns(self, host):
        res = self.run("tunnel", "route", "dns", self.tunnel(), host)
        if res.returncode != 0:
            raise ApiError(502, f"No se pudo crear el DNS de {host}: {self.error_text(res)}")

    def restart_tunnel(self):
        for sid, svc in MANAGER.services.items():
            if TUNNEL_CMD.search(svc.get("command", "")):
                if not MANAGER.running(sid):
                    return "El túnel está parado: arráncalo para aplicar el cambio"

                def go():
                    try:
                        MANAGER.log(sid, "reinicio para aplicar cambios en las rutas del túnel")
                        MANAGER.restart(sid)
                    except ApiError as e:
                        MANAGER.log(sid, f"\x1b[31m{e.msg}\x1b[0m")
                # Con margen: esta misma petición puede estar llegando por el túnel.
                threading.Timer(1.0, go).start()
                return "El túnel se reinicia para aplicar el cambio"
        return "Reinicia cloudflared para aplicar el cambio"

    # ── servicios ──
    def apply(self, sid, old, new, raw):
        """Valida el subdominio pedido y ajusta DNS + ingress. Devuelve (campos extra, aviso)."""
        if not self.enabled or "subdomain" not in raw:
            return {}, None
        sub = str(raw.get("subdomain") or "").strip().lower()
        if sub.endswith("." + self.domain):
            sub = sub[: -len(self.domain) - 1]
        if sub and not SUBDOMAIN.fullmatch(sub):
            raise ApiError(400, "Subdominio inválido: usa letras, números y guiones (p. ej. mi-app)")
        if sub and not new.get("port"):
            raise ApiError(400, "Para publicarlo en internet, indica el puerto del servicio")
        for osid, s in MANAGER.services.items():
            if sub and osid != sid and s.get("subdomain") == sub:
                raise ApiError(409, f"{self.host(sub)} ya lo usa «{s['name']}»")

        old = old or {}
        old_host, new_host = self.host(old.get("subdomain")), self.host(sub)
        extra = {"subdomain": sub}
        old_url = f"https://{old_host}" if old_host else None
        if new_host and (not new.get("url") or new.get("url") == old_url):
            extra["url"] = f"https://{new_host}"
        elif not new_host and old_url and new.get("url") == old_url:
            extra["url"] = ""

        target = f"http://localhost:{gateway_port(new['port'])}" if new_host else None
        if new_host == old_host and (not new_host or new.get("port") == old.get("port")):
            return extra, None
        with self.lock:
            lines = self.read()
            if new_host:
                taken = self.find(lines, new_host)
                if taken and new_host != old_host and taken[3] != target:
                    raise ApiError(409, f"{new_host} ya está en el túnel apuntando a {taken[3]}")
                if new_host != old_host:
                    self.route_dns(new_host)
                lines = self.upsert(lines, new_host, target)
            if old_host and old_host != new_host:
                lines = self.remove(lines, old_host)
            self.write(lines)
        notice = self.restart_tunnel()
        return extra, f"Publicado en {new_host}. {notice}" if new_host else f"{old_host} despublicado. {notice}"

    def reconcile(self):
        """Al arrancar: que cada servicio publicado apunte a su pasarela (migra las reglas antiguas)."""
        if not self.enabled:
            return
        with self.lock:
            lines, changed = self.read(), []
            for svc in MANAGER.services.values():
                host, port = self.host(svc.get("subdomain")), svc.get("port")
                if not host or not port:
                    continue
                target = f"http://localhost:{gateway_port(port)}"
                entry = self.find(lines, host)
                if entry and entry[3] != target:
                    lines = self.upsert(lines, host, target)
                    changed.append(host)
            if changed:
                self.write(lines)
        if changed:
            print(f"[túnel] {', '.join(changed)} → pasarela de NovaHub. {self.restart_tunnel()}", flush=True)

    def unpublish(self, svc):
        host = self.host(svc.get("subdomain"))
        if not self.enabled or not host:
            return None
        with self.lock:
            lines = self.read()
            if not self.find(lines, host):
                return None
            self.write(self.remove(lines, host))
        return f"Ruta de {host} quitada del túnel (el registro DNS sigue en Cloudflare). {self.restart_tunnel()}"


# ───────────────────────────── apagado del servidor ─────────────────────────────

POWEROFF_CMD = ["sudo", "-n", "/usr/bin/systemctl", "poweroff"]
TAPO_PY = os.path.join(BASE_DIR, "tapo.py")
TAPO_VENV = os.path.join(BASE_DIR, ".venv", "bin", "python")
TAPO_FILE = os.path.join(DATA_DIR, "tapo.json")
TAPO_DELAY = 90  # segundos entre programar el corte en el enchufe y que llegue: de sobra para el poweroff


class Power:
    """Apaga el servidor con orden: para los servicios (con su comando de parada), programa
    en el enchufe Tapo el corte de corriente con cuenta atrás y lanza `systemctl poweroff`.
    El túnel no se para: así el panel puede seguir mostrando el progreso hasta el final."""

    def __init__(self):
        self.phase = None  # None | "stopping" | "poweroff"

    @staticmethod
    def sudo_ok():
        res = subprocess.run(["sudo", "-n", "-l", *POWEROFF_CMD[2:]], capture_output=True, timeout=10)
        return res.returncode == 0

    @staticmethod
    def tapo_configured():
        return os.path.isfile(TAPO_FILE) and os.path.isfile(TAPO_VENV)

    @staticmethod
    def tapo(*args):
        try:
            res = subprocess.run([TAPO_VENV, TAPO_PY, *args], capture_output=True, text=True, timeout=40)
        except subprocess.TimeoutExpired:
            return False, "el enchufe no responde"
        return res.returncode == 0, (res.stdout if res.returncode == 0 else res.stderr).strip()

    def status(self):
        return {"sudo": self.sudo_ok(), "tapo": self.tapo_configured(), "phase": self.phase}

    def shutdown(self):
        if self.phase:
            raise ApiError(409, "El servidor ya se está apagando")
        if not self.sudo_ok():
            raise ApiError(400, "NovaHub no tiene permiso para apagar el servidor (falta la regla de sudoers, ver README)")
        tapo = self.tapo_configured()
        if tapo:  # mejor fallar ahora que con los servicios ya parados
            ok, msg = self.tapo("status")
            if not ok:
                raise ApiError(502, msg)
        self.phase = "stopping"
        threading.Thread(target=self._run, args=(tapo,), daemon=True).start()

    def reboot(self):
        if self.phase:
            raise ApiError(409, "El servidor ya se está apagando o reiniciando")
        if not UPDATES.sudo_ok():
            raise ApiError(400, "Falta el permiso de sistema de NovaHub (Ajustes → Actualizaciones)")
        self.phase = "stopping"
        threading.Thread(target=self._run, args=(False, True), daemon=True).start()

    def _run(self, tapo, reboot=False):
        def say(msg):
            print(f"[{'reinicio' if reboot else 'apagado'}] {msg}", flush=True)

        try:
            sids = [sid for sid, s in MANAGER.services.items()
                    if not TUNNEL_CMD.search(s.get("command", "")) and (MANAGER.running(sid) or sid in MANAGER.transition)]
            say(f"parando {len(sids)} servicio(s)")
            for sid in sids:
                MANAGER.stop(sid)
            limit = time.time() + max([MANAGER.services[s].get("stop_timeout", 15) for s in sids] + [0]) + 30
            while time.time() < limit and any(MANAGER.running(s) or s in MANAGER.transition for s in sids):
                time.sleep(0.5)
            if reboot:
                NOTIFIER.send_now("power", "El servidor se está reiniciando",
                                  "Se ha pedido reiniciar el servidor desde el panel (actualizaciones). Los servicios con "
                                  "autoarranque volverán a encenderse solos.")
                self.phase = "reboot"
                say("reiniciando")
                res = subprocess.run(["sudo", "-n", SYSTEM_SCRIPT, "reboot"], capture_output=True, text=True, timeout=30)
                if res.returncode != 0:
                    raise RuntimeError(res.stderr.strip() or f"código {res.returncode}")
                return
            # el correo va antes de programar el corte: si Gmail tarda, no se come el margen del enchufe
            NOTIFIER.send_now("power", "El servidor se está apagando",
                              "Se ha pedido apagar el servidor desde el panel. Los servicios se han parado"
                              + (f" y el enchufe Tapo cortará la corriente {TAPO_DELAY} s después." if tapo else "."))
            if tapo:
                ok, msg = self.tapo("off-in", str(TAPO_DELAY))
                say(f"enchufe Tapo: corte en {TAPO_DELAY} s" if ok else f"enchufe Tapo: no se pudo programar el corte ({msg})")
            self.phase = "poweroff"
            say("systemctl poweroff")
            res = subprocess.run(POWEROFF_CMD, capture_output=True, text=True, timeout=30)
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip() or f"código {res.returncode}")
        except Exception as e:  # noqa: BLE001
            say(f"ERROR, el servidor sigue encendido: {e}")
            if tapo:
                self.tapo("cancel")
            self.phase = None


# ───────────────────────────── HTTP ─────────────────────────────

# Se crean en main(); aquí solo se declaran.
MANAGER: Manager = None
AUTH: Auth = None
PUBLISHER: Publisher = None
GATEWAY: "Gateway" = None
POWER = Power()


# ───────────────────────────── archivos de un servicio ─────────────────────────────

FILE_VIEW_MAX = 512 * 1024  # lo que se muestra de un archivo de texto
DIR_LIST_MAX = 2000


def service_root(svc):
    root = os.path.realpath(os.path.expanduser(svc.get("cwd") or "~"))
    if not os.path.isdir(root):
        raise ApiError(404, f"La carpeta del servicio no existe: {root}")
    return root


def safe_path(root, rel):
    """Ruta absoluta dentro de root: rechaza ../ y enlaces que lleven fuera de la carpeta."""
    full = os.path.realpath(os.path.join(root, str(rel or "").lstrip("/")))
    if full != root and not full.startswith(root + os.sep):
        raise ApiError(403, "Esa ruta está fuera de la carpeta del servicio")
    return full


def list_dir(svc, rel):
    root = service_root(svc)
    full = safe_path(root, rel)
    if not os.path.isdir(full):
        raise ApiError(404, "La carpeta no existe")
    entries = []
    with os.scandir(full) as it:
        for e in it:
            try:
                st, is_dir = e.stat(), e.is_dir()
            except OSError:  # enlace roto
                st, is_dir = None, False
            entries.append({"name": e.name, "dir": is_dir, "link": e.is_symlink(),
                            "size": st.st_size if st and not is_dir else None,
                            "mtime": st.st_mtime if st else None})
    entries.sort(key=lambda x: (not x["dir"], x["name"].lower()))
    return {"root": root, "path": "" if full == root else os.path.relpath(full, root),
            "entries": entries[:DIR_LIST_MAX], "total": len(entries)}


def read_file(svc, rel):
    root = service_root(svc)
    full = safe_path(root, rel)
    if not os.path.isfile(full):
        raise ApiError(404, "El archivo no existe")
    size = os.path.getsize(full)
    with open(full, "rb") as f:
        data = f.read(FILE_VIEW_MAX + 1)
    truncated = len(data) > FILE_VIEW_MAX
    data = data[:FILE_VIEW_MAX]
    binary, text = b"\0" in data[:8192], None
    if not binary:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as e:
            if truncated and e.start >= len(data) - 3:  # cortado a mitad de un carácter
                text = data[:e.start].decode("utf-8")
            else:
                binary = True
    return {"path": os.path.relpath(full, root), "size": size, "mtime": os.path.getmtime(full),
            "binary": binary, "truncated": truncated, "text": text}


BACKUP_DIR = os.path.join(DATA_DIR, "backups")
BACKUPS_PER_SERVICE = 50


def _check_writable(root, full):
    rel = os.path.relpath(full, root)
    if rel == "." or rel.split(os.sep)[0] == ".git" or f"{os.sep}.git{os.sep}" in f"{os.sep}{rel}{os.sep}":
        raise ApiError(403, "No se pueden editar archivos internos de git (.git)")
    return rel


def backup_file(sid, rel, full):
    """Guarda la versión anterior en data/backups/<servicio>/ (se conservan las últimas 50)."""
    folder = os.path.join(BACKUP_DIR, sid)
    os.makedirs(folder, mode=0o700, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")  # con microsegundos: dos guardados seguidos no se pisan
    shutil.copy2(full, os.path.join(folder, f"{stamp}__{rel.replace(os.sep, '__')}"))
    old = sorted(os.listdir(folder))
    for name in old[:-BACKUPS_PER_SERVICE]:
        try:
            os.remove(os.path.join(folder, name))
        except OSError:
            pass


def write_file(sid, svc, rel, data):
    """Guarda un archivo de texto (o lo crea). Escritura atómica, conserva permisos y saltos de línea,
    y avisa si el archivo cambió desde que se abrió (salvo que se fuerce)."""
    root = service_root(svc)
    content = data.get("content")
    if not isinstance(content, str):
        raise ApiError(400, "Falta el contenido del archivo")
    if len(content.encode("utf-8")) > FILE_VIEW_MAX:
        raise ApiError(413, f"El archivo es demasiado grande para editarlo aquí (máximo {FILE_VIEW_MAX // 1024} KB)")
    create = bool(data.get("create"))
    full = safe_path(root, rel)
    rel = _check_writable(root, full)
    if create:
        if os.path.lexists(full):
            raise ApiError(409, "Ya existe un archivo con ese nombre")
        if not os.path.isdir(os.path.dirname(full)):
            raise ApiError(400, "La carpeta donde quieres crearlo no existe")
        mode, crlf = 0o644, False
    else:
        if not os.path.isfile(full):
            raise ApiError(404, "El archivo no existe")
        info = read_file(svc, rel)
        if info["binary"] or info["truncated"]:
            raise ApiError(400, "Este archivo no se puede editar aquí (es binario o demasiado grande)")
        expected = data.get("mtime")
        if expected is not None and not data.get("force") and abs(os.path.getmtime(full) - float(expected)) > 0.001:
            raise ApiError(409, "El archivo ha cambiado desde que lo abriste (quizá desde otro editor)")
        mode = stat.S_IMODE(os.stat(full).st_mode)
        crlf = "\r\n" in info["text"]
        backup_file(sid, rel, full)
    text = content.replace("\r\n", "\n")
    if crlf:
        text = text.replace("\n", "\r\n")  # respeta el estilo de saltos de línea del archivo original
    tmp = os.path.join(os.path.dirname(full), f".{os.path.basename(full)}.novahub-tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, full)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    return read_file(svc, rel)


# ───────────────────────────── editor de variables (.env) ─────────────────────────────

ENV_FILE_NAME = re.compile(r"\.env(\.[A-Za-z0-9_-]{1,30})?")   # .env, .env.local, .env.production…
ENV_LINE = re.compile(r"^\s*(export\s+)?([A-Za-z_][A-Za-z0-9_.-]*)\s*=\s*(.*)$")
ENV_MAX_VARS = 300


def _env_unquote(raw):
    raw = raw.strip()
    m = re.fullmatch(r"'([^']*)'(\s+#.*)?", raw)
    if m:
        return m.group(1)
    m = re.fullmatch(r'"((?:\\.|[^"\\])*)"(\s+#.*)?', raw)
    if m:
        return re.sub(r'\\(["\\n])', lambda x: "\n" if x.group(1) == "n" else x.group(1), m.group(1))
    return re.sub(r"\s+#.*$", "", raw)  # sin comillas: « # …» es un comentario


def _env_quote(value):
    if value == "" or re.fullmatch(r"[A-Za-z0-9_./:@+,%=-]+", value):
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def env_files(root):
    try:
        return sorted(n for n in os.listdir(root) if ENV_FILE_NAME.fullmatch(n) and os.path.isfile(os.path.join(root, n)))
    except OSError:
        return []


def _env_path(svc, name):
    name = name or ".env"
    if not ENV_FILE_NAME.fullmatch(name):
        raise ApiError(400, "Nombre de archivo no válido: debe ser .env o .env.algo")
    root = service_root(svc)
    return root, name, safe_path(root, name)


def _env_git_warning(root, name):
    """Aviso si el .env iría a GitHub con el siguiente commit (ni ignorado ni ya fuera de git)."""
    if not os.path.isdir(os.path.join(root, ".git")) and git(root, "rev-parse", "--git-dir").returncode != 0:
        return None
    if name.endswith(".example") or name.endswith(".sample"):
        return None  # las plantillas sí se suben, sin valores reales
    if git(root, "ls-files", "--error-unmatch", name).returncode == 0:
        return "tracked"   # ya está en el repositorio: sus valores están (o estarán) en GitHub
    if git(root, "check-ignore", "-q", name).returncode != 0:
        return "not-ignored"
    return None


def read_env(svc, name):
    root, name, full = _env_path(svc, name)
    out = {"file": name, "files": env_files(root), "exists": os.path.isfile(full), "vars": [], "mtime": None,
           "git": _env_git_warning(root, name) if os.path.isfile(full) else None}
    if not out["exists"]:
        return out
    if os.path.getsize(full) > FILE_VIEW_MAX:
        raise ApiError(413, "Este archivo es demasiado grande para un .env")
    found, dupes = {}, []
    with open(full, encoding="utf-8", errors="replace") as f:
        for line in f.read().splitlines():
            m = ENV_LINE.match(line)
            if m and not line.lstrip().startswith("#"):
                if m.group(2) in found:
                    dupes.append(m.group(2))
                found[m.group(2)] = _env_unquote(m.group(3))  # repetida: vale la última, como en dotenv y en el shell
    out["vars"] = [{"key": k, "value": v} for k, v in found.items()]
    out["dupes"] = sorted(set(dupes))
    out["mtime"] = os.path.getmtime(full)
    return out


def write_env(sid, svc, name, data):
    """Guarda las variables conservando comentarios, líneas en blanco, orden y formato de lo que no cambia.
    Las nuevas van al final; las que ya no están se quitan."""
    root, name, full = _env_path(svc, name)
    items = data.get("vars")
    if not isinstance(items, list) or len(items) > ENV_MAX_VARS:
        raise ApiError(400, "Lista de variables no válida")
    wanted = {}
    for it in items:
        key = str((it or {}).get("key") or "").strip()
        value = str((it or {}).get("value") or "")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", key) or len(key) > 120:
            raise ApiError(400, f"Nombre de variable no válido: «{key[:40]}» (letras, números y _; sin empezar por número)")
        if key in wanted:
            raise ApiError(400, f"La variable {key} está repetida")
        if len(value) > 8000:
            raise ApiError(400, f"El valor de {key} es demasiado largo")
        wanted[key] = value
    exists = os.path.isfile(full)
    lines, mode, crlf = [], 0o600, False   # un .env nuevo, solo legible por ti: suele llevar claves
    if exists:
        expected = data.get("mtime")
        if expected is not None and not data.get("force") and abs(os.path.getmtime(full) - float(expected)) > 0.001:
            raise ApiError(409, "El archivo ha cambiado desde que lo abriste (quizá desde otro editor)")
        with open(full, encoding="utf-8", errors="replace", newline="") as f:
            text = f.read()
        crlf = "\r\n" in text
        lines = text.replace("\r\n", "\n").split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        mode = stat.S_IMODE(os.stat(full).st_mode)
        backup_file(sid, name, full)
    out, done = [], set()
    for line in lines:
        m = ENV_LINE.match(line)
        if not m or line.lstrip().startswith("#"):
            out.append(line)
            continue
        key = m.group(2)
        if key not in wanted or key in done:
            continue  # borrada (o repetida en el archivo: se queda la primera)
        done.add(key)
        if _env_unquote(m.group(3)) == wanted[key]:
            out.append(line)  # sin cambios: se respeta tal cual estaba escrita
        else:
            out.append(f"{m.group(1) or ''}{key}={_env_quote(wanted[key])}")
    out += [f"{k}={_env_quote(v)}" for k, v in wanted.items() if k not in done]
    body = "\n".join(out) + "\n"
    if crlf:
        body = body.replace("\n", "\r\n")
    tmp = os.path.join(os.path.dirname(full), f".{os.path.basename(full)}.novahub-tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(body)
        os.chmod(tmp, mode)
        os.replace(tmp, full)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    MANAGER.log(sid, f"variables guardadas en {name} ({len(wanted)}){'' if exists else ' · archivo nuevo'}")
    return read_env(svc, name)


# ───────────────────────────── git de un servicio ─────────────────────────────

GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}  # sin preguntas: falla en vez de colgarse


def git(cwd, *args, timeout=20):
    try:
        return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=timeout, env=GIT_ENV)
    except FileNotFoundError:
        raise ApiError(500, "git no está instalado en el servidor")
    except subprocess.TimeoutExpired:
        raise ApiError(504, "git no responde (¿hay conexión con GitHub?)")


def git_output(res):
    return (res.stdout + res.stderr).strip()


def git_status(svc):
    root = service_root(svc)
    top = git(root, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return {"repo": False, "root": root}
    lines = git(root, "status", "--porcelain=v1", "-b", "--untracked-files=all").stdout.splitlines()
    head = lines[0][3:] if lines and lines[0].startswith("## ") else ""
    head = head.removeprefix("No commits yet on ")
    track = re.search(r" \[(.*)\]$", head)
    head = head[:track.start()] if track else head
    branch, _, upstream = head.partition("...")
    ahead = re.search(r"ahead (\d+)", track.group(1)) if track else None
    behind = re.search(r"behind (\d+)", track.group(1)) if track else None
    last = git(root, "log", "-1", "--format=%h%x00%s%x00%an%x00%ct").stdout.strip()
    remote = git(root, "remote", "get-url", "origin").stdout.strip()
    return {
        "repo": True, "root": root, "top": top.stdout.strip(),
        "branch": branch or "HEAD", "upstream": upstream or None,
        "ahead": int(ahead.group(1)) if ahead else 0, "behind": int(behind.group(1)) if behind else 0,
        "changes": [{"code": l[:2], "path": l[3:]} for l in lines[1:501]],
        "total_changes": max(0, len(lines) - 1),
        "last": dict(zip(("hash", "subject", "author", "time"), last.split("\0"))) if last.count("\0") == 3 else None,
        "remote": re.sub(r"//[^@/]+@", "//", remote) or None,  # sin credenciales si las hubiera en la URL
    }


def git_repo(svc):
    root = service_root(svc)
    if git(root, "rev-parse", "--show-toplevel").returncode != 0:
        raise ApiError(400, "La carpeta de este servicio no es un repositorio de git")
    return root


def git_commit(svc, message):
    message = str(message or "").strip()
    if not message:
        raise ApiError(400, "Escribe un mensaje que explique los cambios")
    if len(message) > 5000:
        raise ApiError(400, "El mensaje es demasiado largo")
    root = git_repo(svc)
    res = git(root, "add", "-A")
    if res.returncode != 0:
        raise ApiError(500, f"No se pudieron preparar los cambios: {git_output(res)}")
    if not git(root, "config", "user.name").stdout.strip() or not git(root, "config", "user.email").stdout.strip():
        raise ApiError(400, "git no sabe quién eres: pon tu nombre y correo en Ajustes → Git")
    res = git(root, "commit", "-m", message)
    if res.returncode != 0:
        if "nothing to commit" in res.stdout:
            raise ApiError(400, "No hay cambios que guardar")
        raise ApiError(500, f"El commit ha fallado: {git_output(res)}")
    return git_output(res)


GIT_EMAIL = re.compile(r"[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+")


def git_identity():
    """Nombre y correo con los que firma git en el servidor (configuración global del usuario)."""
    def get(key):
        res = subprocess.run(["git", "config", "--global", "--get", key], capture_output=True, text=True, timeout=10, env=GIT_ENV)
        return res.stdout.strip()
    return {"name": get("user.name"), "email": get("user.email")}


def set_git_identity(data):
    name = re.sub(r"[\x00-\x1f\x7f]", "", str(data.get("name") or "")).strip()
    email = str(data.get("email") or "").strip()
    if not 1 <= len(name) <= 100:
        raise ApiError(400, "Escribe tu nombre para los commits (p. ej. tu usuario de GitHub)")
    if not GIT_EMAIL.fullmatch(email) or len(email) > 200:
        raise ApiError(400, "El correo no es válido")
    for key, val in (("user.name", name), ("user.email", email)):
        res = subprocess.run(["git", "config", "--global", key, val], capture_output=True, text=True, timeout=10, env=GIT_ENV)
        if res.returncode != 0:
            raise ApiError(500, f"No se pudo guardar en git: {res.stderr.strip()}")
    return git_identity()


def git_push(svc):
    root = git_repo(svc)
    has_upstream = git(root, "rev-parse", "--abbrev-ref", "@{u}").returncode == 0
    res = git(root, "push", *([] if has_upstream else ["-u", "origin", "HEAD"]), timeout=90)
    if res.returncode != 0:
        raise ApiError(502, f"No se pudo subir a GitHub: {git_output(res)}")
    return git_output(res)


def git_pull(svc):
    root = git_repo(svc)
    res = git(root, "pull", "--ff-only", timeout=90)
    if res.returncode != 0:
        raise ApiError(502, f"No se pudieron traer los cambios: {git_output(res)}")
    return git_output(res)


# ───────────────────────────── gestor de tareas ─────────────────────────────

# Nombres reconocibles para programas cuyo proceso se llama de forma poco clara (p. ej. «MainThread»).
KNOWN_APPS = [
    (re.compile(r"(^|/)claude(\s|$)"), "Claude Code"),  # antes que VS Code: puede ir dentro de sus extensiones
    (re.compile(r"\.vscode-server/"), "VS Code (remoto)"),
    (re.compile(r"(^|/)tailscaled\b"), "Tailscale"),
    (re.compile(r"(^|/)cloudflared\b"), "Túnel Cloudflare"),
    (re.compile(r"(^|/)sshd\b"), "SSH"),
    (re.compile(r"(^|/)(systemd[\w-]*|dbus[\w-]*|polkitd|cron|dhcpcd|agetty|login|rsyslogd|udevd|wpa_supplicant|NetworkManager)\b"), "Sistema"),
]


def meminfo():
    mem = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, val = line.split(":", 1)
            mem[key] = int(val.split()[0]) * 1024
    total, free, avail = mem.get("MemTotal", 0), mem.get("MemFree", 0), mem.get("MemAvailable", 0)
    used = total - avail
    return {"total": total, "used": used, "free": free, "cache": max(0, total - used - free),
            "swap_total": mem.get("SwapTotal", 0), "swap_used": mem.get("SwapTotal", 0) - mem.get("SwapFree", 0)}


def read_proc_text(pid, name):
    try:
        with open(f"/proc/{pid}/{name}", "rb") as f:
            return f.read().replace(b"\0", b" ").decode("utf-8", "replace").strip()
    except OSError:
        return ""


class Tasks:
    """Instantánea de procesos agrupados por aplicación; la CPU sale de comparar con la lectura anterior."""

    def __init__(self):
        self.prev = {}  # pid -> (starttime, ticks, monotonic)
        self.users = {}
        self.lock = threading.Lock()

    def user(self, uid):
        if uid not in self.users:
            try:
                import pwd
                self.users[uid] = pwd.getpwuid(uid).pw_name
            except (KeyError, ImportError):
                self.users[uid] = str(uid)
        return self.users[uid]

    def services_by_group(self):
        with MANAGER.lock:
            return {st["pid"]: MANAGER.services[sid]["name"]
                    for sid, st in MANAGER.state.items() if sid in MANAGER.services and MANAGER.running(sid)}

    def snapshot(self):
        services, me, cpus = self.services_by_group(), os.getpid(), os.cpu_count() or 1
        now, seen, procs = time.monotonic(), {}, []
        with self.lock:
            for name in os.listdir("/proc"):
                if not name.isdigit():
                    continue
                st = proc_stat(name)
                if not st or st[0] in ("Z", "X"):
                    continue
                rss = int(st[21]) * PAGE_SIZE
                if rss == 0:  # hilos del kernel
                    continue
                pid, pgid, start = int(name), int(st[2]), int(st[19])
                ticks = int(st[11]) + int(st[12])
                prev = self.prev.get(pid)
                cpu = None
                if prev and prev[0] == start and now - prev[2] > 0.2:
                    cpu = round((ticks - prev[1]) / CLK_TCK / (now - prev[2]) * 100 / cpus, 1)
                seen[pid] = (start, ticks, now)
                try:
                    uid = os.stat(f"/proc/{pid}").st_uid
                except OSError:
                    continue
                comm = read_proc_text(pid, "comm")
                cmd = read_proc_text(pid, "cmdline") or f"[{comm}]"
                if pgid in services:
                    kind, app = "service", services[pgid]
                elif pid == me:
                    kind, app = "service", "NovaHub (este panel)"
                else:
                    kind, app = "app", None
                    for rx, label in KNOWN_APPS:
                        if rx.search(cmd) or rx.search(comm):
                            app = label
                            break
                    app = app or os.path.basename(cmd.split(" ", 1)[0]) or comm
                procs.append({"pid": pid, "name": comm, "app": app, "kind": kind, "user": self.user(uid),
                              "own": uid == os.getuid(), "rss": rss, "cpu": cpu, "cmd": cmd[:400]})
            self.prev = seen
        groups = {}
        for p in procs:
            g = groups.setdefault(p["app"], {"name": p["app"], "kind": p["kind"], "rss": 0, "cpu": 0.0, "count": 0})
            g["rss"] += p["rss"]
            g["cpu"] = round(g["cpu"] + (p["cpu"] or 0), 1)
            g["count"] += 1
        return {"mem": meminfo(), "cpus": cpus, "load": os.getloadavg(),
                "groups": sorted(groups.values(), key=lambda g: -g["rss"]),
                "processes": sorted(procs, key=lambda p: -p["rss"])}

    def kill(self, pid, force):
        try:
            uid = os.stat(f"/proc/{pid}").st_uid
        except OSError:
            raise ApiError(404, "Ese proceso ya no existe")
        if uid != os.getuid():
            raise ApiError(403, f"Ese proceso es del usuario «{self.user(uid)}»: NovaHub no puede cerrarlo")
        if pid == os.getpid():
            raise ApiError(400, "Ese proceso es el propio NovaHub")
        st = proc_stat(pid)
        name = self.services_by_group().get(int(st[2])) if st else None
        if name:
            raise ApiError(409, f"Ese proceso es del servicio «{name}»: apágalo desde su ficha")
        try:
            os.kill(pid, signal.SIGKILL if force else signal.SIGTERM)
        except ProcessLookupError:
            raise ApiError(404, "Ese proceso ya no existe")


TASKS = Tasks()


# ───────────────────────────── comprobación de salud ─────────────────────────────

def health_mode(svc):
    mode = svc.get("health_check") or "auto"
    if mode == "auto":
        mode = "http" if svc.get("port") else "off"
    return "off" if not svc.get("port") else mode


# Los servicios se buscan por IPv4 y, si no, por IPv6 (no «localhost»: suele dar ::1 primero, y con Podman/pasta ::1
# acepta la conexión aunque el programa del contenedor solo escuche en IPv4, y luego la corta → 502 / «no responde»).
LOCAL_HOSTS = ("127.0.0.1", "::1")


def probe(mode, port, path):
    """(ok, milisegundos, detalle). HTTP sano = cualquier respuesta que no sea un error 5xx."""
    for host in LOCAL_HOSTS:
        res = _probe(mode, host, port, path)
        if res[0]:
            return res
    return res


def _probe(mode, host, port, path):
    t0 = time.monotonic()
    try:
        if mode == "tcp":
            socket.create_connection((host, port), timeout=5).close()
            return True, round((time.monotonic() - t0) * 1000), "acepta conexiones"
        conn = http.client.HTTPConnection(host, port, timeout=8)
        try:
            conn.request("GET", path, headers={"User-Agent": "NovaHub-health", "Connection": "close"})
            status = conn.getresponse().status
        finally:
            conn.close()
        ms = round((time.monotonic() - t0) * 1000)
        return status < 500, ms, f"HTTP {status}"
    except (OSError, http.client.HTTPException) as e:
        return False, round((time.monotonic() - t0) * 1000), (str(e) or type(e).__name__)[:120]


class Health:
    """Comprueba cada servicio encendido cada HEALTH_EVERY s y lo reinicia tras HEALTH_FAILS fallos seguidos.
    Corre en su propio hilo: una petición lenta no bloquea al gestor."""

    def __init__(self):
        self.next = {}  # sid -> monotonic de la próxima comprobación

    def loop(self):
        while True:
            time.sleep(2)
            try:
                self.tick()
            except Exception:  # noqa: BLE001
                traceback.print_exc()

    def tick(self):
        SUPERVISOR.beat("salud")
        now, mono = time.time(), time.monotonic()
        with MANAGER.lock:
            due = []
            for sid, svc in MANAGER.services.items():
                st = MANAGER.state.get(sid) or {}
                mode = health_mode(svc)
                running = MANAGER.running(sid) and sid not in MANAGER.transition and not st.get("updating")
                if mode == "off" or not running:
                    if st.get("health") and (mode == "off" or not MANAGER.running(sid)):
                        st.pop("health", None)
                    self.next.pop(sid, None)
                    continue
                if now - (st.get("started_at") or 0) < HEALTH_GRACE:
                    st["health"] = {"state": "starting", "at": now}
                    continue
                if mono >= self.next.get(sid, 0):
                    self.next[sid] = mono + HEALTH_EVERY
                    due.append((sid, mode, svc["port"], svc.get("health_path") or "/", st.get("pid")))
        for sid, mode, port, path, pid in due:
            SUPERVISOR.beat("salud")  # cada comprobación puede tardar 8 s: con varias, no parecer colgado
            ok, ms, detail = probe(mode, port, path)
            with MANAGER.lock:
                st = MANAGER.state.get(sid)
                if not st or st.get("pid") != pid or sid in MANAGER.transition:
                    continue  # se reinició o paró mientras tanto
                prev = st.get("health") or {}
                fails = 0 if ok else prev.get("fails", 0) + 1
                st["health"] = {"state": "ok" if ok else "failing", "at": time.time(), "ms": ms, "detail": detail, "fails": fails}
                if ok and (prev.get("fails") or st.get("health_gave_up")):
                    st["health_gave_up"] = False  # vuelve a vigilarse con normalidad
                    MANAGER.log(sid, f"\x1b[32mvuelve a responder ({detail}, {ms} ms)\x1b[0m")
                elif not ok and not st.get("health_gave_up"):  # rendido: no se llena la consola de avisos
                    MANAGER.log(sid, f"\x1b[33mcomprobación de salud fallida ({fails}/{HEALTH_FAILS}): {detail}\x1b[0m")
                if fails >= HEALTH_FAILS:
                    self.restart(sid, st, detail)

    def restart(self, sid, st, detail):
        now = time.time()
        recent = [t for t in st.get("health_restarts", []) if now - t < 3600]
        st["health"]["fails"] = 0
        if len(recent) >= HEALTH_RESTARTS_PER_HOUR:
            if not st.get("health_gave_up"):
                st["health_gave_up"] = True
                MANAGER.log(sid, f"\x1b[31mno responde ({detail}) y ya se ha reiniciado {len(recent)} veces en la última "
                                 "hora: no se vuelve a reiniciar. Revisa la consola o la ruta de la comprobación.\x1b[0m")
                name = MANAGER.services[sid]["name"]
                NOTIFIER.notify("health", sid, f"{name} no responde",
                                f"«{name}» no responde ({detail}) y ya se ha reiniciado {len(recent)} veces en la última hora: "
                                "NovaHub ha dejado de reiniciarlo.", log=True, key="gaveup")
                MANAGER.save_state()
            return
        st["health_gave_up"] = False
        recent.append(now)
        st["health_restarts"] = recent
        MANAGER.log(sid, f"\x1b[33mno responde desde hace {HEALTH_FAILS * HEALTH_EVERY} s: reiniciando\x1b[0m")
        name = MANAGER.services[sid]["name"]
        NOTIFIER.notify("health", sid, f"{name} no respondía y se ha reiniciado",
                        f"«{name}» no ha respondido a la comprobación de salud durante {HEALTH_FAILS * HEALTH_EVERY} s "
                        f"({detail}) y se ha reiniciado.", log=True)
        MANAGER.save_state()
        MANAGER.stop(sid, then_start=True)


HEALTH = Health()


# ───────────────────────────── vista de red ─────────────────────────────

class Network:
    """Túnel (conexiones con Cloudflare), dominios publicados y enchufe Tapo, para la vista «Red».
    El enchufe tarda unos segundos en responder: se consulta en segundo plano como mucho cada minuto."""

    TAPO_TTL = 60
    METRIC = re.compile(r"^(cloudflared_tunnel_\w+)(\{[^}]*\})?\s+([\d.e+-]+)$", re.M)

    def __init__(self):
        self.lock = threading.Lock()
        self.tapo_data, self.tapo_at, self.tapo_busy = None, 0, False

    @staticmethod
    def tunnel_sid():
        return next((sid for sid, s in MANAGER.services.items() if TUNNEL_CMD.search(s.get("command", ""))), None)

    def tunnel(self):
        sid = self.tunnel_sid()
        if not sid:
            return None
        svc = MANAGER.services[sid]
        out = {"sid": sid, "name": svc["name"], "status": MANAGER.status(sid), "connections": None,
               "locations": [], "requests": None, "errors": None}
        m = re.search(r"--metrics[=\s]+(\S+)", svc.get("command", ""))
        if not m or not MANAGER.running(sid):
            return out
        import urllib.request
        try:  # el servidor de métricas de cloudflared (solo escucha en 127.0.0.1)
            with urllib.request.urlopen(f"http://{m.group(1)}/metrics", timeout=2) as r:
                text = r.read(2_000_000).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            out["metrics_error"] = True
            return out
        locs = set()
        out["errors"] = 0
        for name, labels, val in self.METRIC.findall(text):
            if name == "cloudflared_tunnel_ha_connections":
                out["connections"] = int(float(val))
            elif name == "cloudflared_tunnel_total_requests":
                out["requests"] = int(float(val))
            elif name == "cloudflared_tunnel_response_by_code":
                # errores de verdad: respuestas 5xx (servicio caído o roto). No se usa request_errors porque
                # cuenta como fallo cada consola en directo que se cierra al salir de una ficha.
                code = re.search(r'status_code="(\d+)"', labels or "")
                if code and code.group(1).startswith("5"):
                    out["errors"] = (out["errors"] or 0) + int(float(val))
            elif name == "cloudflared_tunnel_server_locations" and float(val) > 0:
                loc = re.search(r'edge_location="([^"]+)"', labels or "")
                if loc:
                    locs.add(loc.group(1))
        out["locations"] = sorted(locs)
        return out

    def hosts(self):
        """Reglas del config.yml del túnel con el servicio de NovaHub al que llevan."""
        if not PUBLISHER.enabled:
            return []
        try:
            entries = PUBLISHER.entries(PUBLISHER.read())[0]
        except (OSError, ApiError):
            return []
        panel = SUPERVISOR.url[1] if SUPERVISOR.url else None
        out = []
        for _, _, host, target in entries:
            if not host:
                continue
            port = re.search(r":(\d+)/?$", target or "")
            port = int(port.group(1)) if port else None
            row = {"host": host, "target": target, "sid": None, "name": None, "status": None, "gateway": False}
            if port and port == panel:
                row["name"] = "NovaHub (este panel)"
                row["status"] = "running"
            for sid, s in MANAGER.services.items():
                if port and s.get("port") and port in (s["port"], gateway_port(s["port"])):
                    row.update(sid=sid, name=s["name"], status=MANAGER.status(sid),
                               gateway=port != s["port"])
            out.append(row)
        return out

    def tapo(self):
        if not Power.tapo_configured():
            return {"configured": False}
        with self.lock:
            stale = time.time() - self.tapo_at > self.TAPO_TTL
            if stale and not self.tapo_busy:
                self.tapo_busy = True
                threading.Thread(target=self._read_tapo, name="tapo", daemon=True).start()
            return {"configured": True, "at": self.tapo_at or None, "loading": self.tapo_busy and not self.tapo_data,
                    **(self.tapo_data or {})}

    def _read_tapo(self):
        ok, msg = Power.tapo("status")
        try:
            data = json.loads(msg) if ok else {"error": msg or "el enchufe no responde"}
        except ValueError:
            data = {"error": "respuesta del enchufe no válida"}
        with self.lock:
            self.tapo_data, self.tapo_at, self.tapo_busy = data, time.time(), False

    def public(self):
        return {"tunnel": self.tunnel(), "hosts": self.hosts(), "tapo": self.tapo(),
                "lan_ip": lan_ip(), "domain": PUBLISHER.domain if PUBLISHER.enabled else None}


NETWORK = Network()


# ───────────────────────────── pasarela de los servicios publicados ─────────────────────────────

def gateway_port(port):
    gp = port + GATEWAY_OFFSET if port else None
    return gp if gp and gp <= 65535 else port


UNAVAILABLE_PAGE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
{refresh}<title>{title} · {name}</title>
<style>
  :root {{ color-scheme: light dark; --bg: #e9e6ee; --card: #f7f5fa; --ink: #1c1924; --soft: #6a6478; --edge: #d3cddc; --nova: #6c3ff5; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg: #121017; --card: #1d1a24; --ink: #ece8f4; --soft: #a49db3; --edge: #09080c; --nova: #9a7bff; }} }}
  body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 16px; box-sizing: border-box;
         background: var(--bg); color: var(--ink); font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }}
  main {{ max-width: 420px; padding: 32px 28px; border-radius: 18px; background: var(--card); box-shadow: 0 2px 0 var(--edge); text-align: center; }}
  .orb {{ width: 44px; height: 44px; margin: 0 auto 18px; border-radius: 50%;
          background: radial-gradient(circle at 35% 30%, #fff, #b89cff 30%, #6a35f0 70%); box-shadow: 0 0 24px rgba(123, 77, 255, .7);
          {anim} }}
  @keyframes pulse {{ 50% {{ transform: scale(.85); opacity: .6; }} }}
  @media (prefers-reduced-motion: reduce) {{ .orb {{ animation: none; }} }}
  h1 {{ margin: 0 0 8px; font-size: 22px; }}
  p {{ margin: 0; color: var(--soft); }}
  small {{ display: block; margin-top: 18px; color: var(--soft); font-size: 13px; }}
</style>
</head>
<body><main><div class="orb"></div><h1>{title}</h1><p>{message}</p><small>{hint}</small></main></body>
</html>
"""


class Gateway:
    """Un puerto por servicio publicado que reenvía las conexiones tal cual (también websockets) al servicio.
    Si el servicio no responde, contesta 503 con una página que explica que se está reiniciando o está apagado,
    en vez del error genérico de Cloudflare."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.servers = {}   # sid -> (puerto pasarela, puerto servicio, servidor)
        self.failed = {}    # sid -> (puertos, momento) que no se pudieron abrir: se reintenta cada minuto

    def sync(self):
        want = {sid: (gateway_port(s["port"]), s["port"]) for sid, s in list(MANAGER.services.items())
                if s.get("subdomain") and s.get("port") and gateway_port(s["port"]) != s["port"]}
        for sid in list(self.servers):
            if self.servers[sid][:2] != want.get(sid):
                srv = self.servers.pop(sid)[2]
                self.loop.call_soon_threadsafe(srv.close)
        for sid, ports in want.items():
            failed = self.failed.get(sid)
            if sid in self.servers or (failed and failed[0] == ports and time.time() - failed[1] < 60):
                continue
            fut = asyncio.run_coroutine_threadsafe(
                asyncio.start_server(partial(self.handle, sid), "127.0.0.1", ports[0], reuse_address=True), self.loop)
            try:
                self.servers[sid] = (*ports, fut.result(5))
                self.failed.pop(sid, None)
            except Exception as e:  # noqa: BLE001
                if not failed or failed[0] != ports:  # se avisa una vez, no en cada reintento
                    print(f"[pasarela] no se pudo abrir el puerto {ports[0]} para «{sid}»: {e} (se reintenta cada minuto)", flush=True)
                self.failed[sid] = (ports, time.time())

    async def handle(self, sid, reader, writer):
        svc = MANAGER.services.get(sid)
        try:
            if not svc:
                raise OSError("servicio eliminado")
            up_reader, up_writer = await self.connect(svc["port"])
        except (OSError, asyncio.TimeoutError):
            await self.unavailable(sid, svc, reader, writer)
            return
        await asyncio.gather(self.pipe(reader, up_writer), self.pipe(up_reader, writer))

    @staticmethod
    async def connect(port):
        err = None
        for host in LOCAL_HOSTS:
            try:
                return await asyncio.wait_for(asyncio.open_connection(host, port), 3)
            except (OSError, asyncio.TimeoutError) as e:
                err = e
        raise err

    @staticmethod
    async def pipe(reader, writer):
        try:
            while data := await reader.read(65536):
                writer.write(data)
                await writer.drain()
        except (ConnectionError, OSError):
            pass
        finally:
            try:
                writer.close()
            except Exception:  # noqa: BLE001
                pass

    async def unavailable(self, sid, svc, reader, writer):
        try:
            await asyncio.wait_for(reader.read(65536), 1)  # la petición, para no cortar al cliente a media escritura
        except (asyncio.TimeoutError, OSError):
            pass
        name = svc["name"] if svc else "Este servicio"
        status = MANAGER.status(sid) if svc else "stopped"
        st = MANAGER.state.get(sid) or {}
        if status in ("starting", "stopping", "running") or st.get("updating"):
            title, message, hint = "Reiniciando…", f"{name} se está reiniciando. Volverá en unos segundos.", "Esta página se recarga sola."
            refresh, anim = '<meta http-equiv="refresh" content="5">\n', "animation: pulse 1.4s ease-in-out infinite;"
        elif status == "crashed":
            title, message, hint = "Problema temporal", f"{name} ha tenido un error y está parado.", "Vuelve a intentarlo dentro de un rato."
            refresh, anim = '<meta http-equiv="refresh" content="30">\n', ""
        else:
            title, message, hint = "Fuera de servicio", f"{name} está apagado en este momento.", "Vuelve a intentarlo más tarde."
            refresh, anim = '<meta http-equiv="refresh" content="30">\n', ""
        esc_ = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")  # noqa: E731
        body = UNAVAILABLE_PAGE.format(refresh=refresh, anim=anim, title=title, name=esc_(name),
                                       message=esc_(message), hint=hint).encode()
        head = ("HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(body)}\r\nRetry-After: 5\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n")
        try:
            writer.write(head.encode() + body)
            await writer.drain()
        except (ConnectionError, OSError):
            pass
        finally:
            writer.close()


# ───────────────────────────── lista de mejoras ─────────────────────────────

# Orden de prioridad inicial (de más a menos importante). Solo se usa la primera vez:
# después manda data/roadmap.json, donde se marcan las hechas y se añaden ideas nuevas.
# Lista de mejoras de la página oculta (#/mejoras). Las instalaciones nuevas empiezan vacías: cada uno apunta las suyas.
ROADMAP_DEFAULT = []


class Roadmap:
    def __init__(self):
        self.lock = threading.Lock()

    @staticmethod
    def enabled():
        """La página oculta de mejoras es una herramienta personal: solo existe si ya hay una lista guardada
        (data/roadmap.json) o con NOVAHUB_ROADMAP=1. Las instalaciones nuevas no la tienen."""
        return os.path.isfile(ROADMAP_FILE) or os.environ.get("NOVAHUB_ROADMAP") == "1"

    def load(self):
        if not self.enabled():
            raise ApiError(404, "No encontrado")
        items = read_json(ROADMAP_FILE, None)
        if items is None:
            items = [{"id": slugify(title), "tag": tag, "title": title, "desc": desc,
                      "done": False, "done_at": None, "custom": False}
                     for tag, title, desc in ROADMAP_DEFAULT]
            write_json(ROADMAP_FILE, items)
        return items

    def list(self):
        with self.lock:
            return self.load()

    def add(self, data):
        title = str(data.get("title") or "").strip()[:120]
        if not title:
            raise ApiError(400, "Escribe la mejora que quieres apuntar")
        with self.lock:
            items = self.load()
            base = slugify(title)
            iid = base
            while any(i["id"] == iid for i in items):
                iid = f"{base}-{secrets.token_hex(2)}"
            items.append({"id": iid, "tag": str(data.get("tag") or "Idea").strip()[:30] or "Idea", "title": title,
                          "desc": str(data.get("desc") or "").strip()[:500], "done": False, "done_at": None, "custom": True})
            write_json(ROADMAP_FILE, items)
            return items

    def update(self, iid, data):
        with self.lock:
            items = self.load()
            item = next((i for i in items if i["id"] == iid), None)
            if not item:
                raise ApiError(404, "Esa mejora no existe")
            if "done" in data:
                item["done"] = bool(data["done"])
                item["done_at"] = time.time() if item["done"] else None
            for key, size in (("title", 120), ("desc", 800), ("tag", 30)):  # editar el texto de una mejora
                if key in data:
                    val = re.sub(r"[\x00-\x1f\x7f]", " ", str(data[key] or "")).strip()[:size]
                    if key == "title" and not val:
                        raise ApiError(400, "La mejora necesita un título")
                    item[key] = val
            write_json(ROADMAP_FILE, items)
            return items

    def close_version(self, version):
        """Guarda las mejoras hechas (y aún sin versión) bajo una versión, p. ej. «1.0»: dejan de verse en la lista."""
        version = re.sub(r"[^0-9A-Za-z.\- ]", "", str(version or "")).strip()[:20]
        if not version:
            raise ApiError(400, "Pon un nombre de versión, p. ej. 1.1")
        with self.lock:
            items = self.load()
            pending = [i for i in items if i["done"] and not i.get("version")]
            if not pending:
                raise ApiError(400, "No hay mejoras hechas que guardar en una versión")
            for i in pending:
                i["version"] = version
            write_json(ROADMAP_FILE, items)
            return items

    def delete(self, iid):
        with self.lock:
            items = self.load()
            rest = [i for i in items if i["id"] != iid]
            if len(rest) == len(items):
                raise ApiError(404, "Esa mejora no existe")
            write_json(ROADMAP_FILE, rest)
            return rest


ROADMAP = Roadmap()


# ───────────────────────────── avisos por correo (Gmail) ─────────────────────────────

NOTIFY_EVENTS = {
    "crash": "Un servicio se cae, no arranca o se deja de reintentar",
    "health": "Un servicio deja de responder",
    "memory": "Un servicio usa más memoria de su límite",
    "power": "El servidor se enciende o se apaga",
    "update": "Falla una actualización desde GitHub",
    "novahub": "NovaHub se reinicia tras un fallo o tiene un problema interno",
    "backup": "Falla una copia de seguridad o una restauración",
    "task": "Falla una tarea programada",
    "updates": "Hay actualizaciones disponibles, o una actualización termina o falla",
}
NOTIFY_COOLDOWN = 600   # como mucho un correo por servicio y tipo de aviso cada 10 min
NOTIFY_MAX_HOUR = 30    # y nunca más de 30 por hora en total
EMAIL_RE = re.compile(r"[^@\s,]+@[^@\s,]+\.[^@\s,]+")
PANEL_URL = None        # dirección pública del panel para los enlaces de los correos (se calcula en main)


def _ended(code):
    return f"ha terminado con error (código {code})" if code is not None else "ha terminado inesperadamente"


def strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;?]*[@-~]", "", text)


# ───────────────────────────── buscar en los logs ─────────────────────────────

LOGSEARCH_PY = os.path.join(BASE_DIR, "logsearch.py")
LOG_REGEX_TIMEOUT = 5   # s: una expresión regular que tarde más se corta (se ejecuta en otro proceso)


def search_log(sid, q="", errors=False, regex=False, case=False):
    """Busca en el log del servicio (el actual y el anterior rotado): ver logsearch.py."""
    import logsearch
    q = q[:200]
    if not q and not errors:
        raise ApiError(400, "Escribe qué buscar o activa «Solo errores»")
    paths = [(log_path(sid) + ".1", "anterior"), (log_path(sid), "actual")]
    if not (regex and q):  # texto normal: tiempo lineal, se busca aquí mismo
        return logsearch.scan(paths, q, errors, False, case)
    args = json.dumps({"paths": paths, "q": q, "errors": errors, "regex": True, "case": case})
    try:
        res = subprocess.run([sys.executable, LOGSEARCH_PY], input=args, capture_output=True, text=True,
                             timeout=LOG_REGEX_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise ApiError(400, f"La expresión regular tarda demasiado (más de {LOG_REGEX_TIMEOUT} s): simplifícala")
    try:
        out = json.loads(res.stdout)
    except ValueError:
        raise ApiError(500, f"La búsqueda ha fallado: {res.stderr.strip()[-300:]}")
    if "error" in out:
        raise ApiError(400, out["error"])
    return out


def log_tail(sid, lines=20):
    try:
        with open(log_path(sid), "rb") as f:
            f.seek(max(0, os.path.getsize(log_path(sid)) - 16384))
            text = f.read().decode("utf-8", "replace")
    except OSError:
        return ""
    return "\n".join(strip_ansi(text).splitlines()[-lines:])


def make_orb_png(size=96):
    """El orbe de NovaHub como PNG (sin dependencias): degradado radial morado con halo."""
    import struct
    import zlib
    rows = []
    c = size / 2
    r = size * 0.36          # esfera
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            d = (dx * dx + dy * dy) ** 0.5
            if d <= r:
                # luz arriba a la izquierda: blanco → lila → morado intenso
                lx, ly = x + 0.5 - (c - r * 0.3), y + 0.5 - (c - r * 0.4)
                t = min(1.0, (lx * lx + ly * ly) ** 0.5 / (r * 1.55))
                stops = [(0.0, (255, 255, 255)), (0.3, (184, 156, 255)), (0.75, (106, 53, 240)), (1.0, (74, 31, 199))]
                for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
                    if t <= t1:
                        k = (t - t0) / (t1 - t0)
                        rgb = [round(a + (b - a) * k) for a, b in zip(c0, c1)]
                        break
                alpha = 255 if d <= r - 1 else round(255 * (r - d + 1))
                row += bytes(rgb + [max(0, min(255, alpha))])
            else:
                glow = max(0.0, 1 - (d - r) / (size / 2 - r))  # halo morado que se desvanece
                row += bytes([123, 77, 255, round(110 * glow ** 2)])
        rows.append(bytes(row))
    raw = zlib.compress(b"".join(rows), 9)
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)  # noqa: E731
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)) \
        + chunk(b"IDAT", raw) + chunk(b"IEND", b"")


ORB_PNG = make_orb_png()

EMAIL_LEVELS = {  # etiqueta, fondo, texto
    "danger": ("Problema", "#fde2e2", "#c0262d"),
    "warning": ("Aviso", "#fff0d6", "#9a5b00"),
    "ok": ("Todo bien", "#d9f7e3", "#0f7a3a"),
    "info": ("Información", "#ece6ff", "#5a2fe0"),
}


def email_html(subject, text, level, service, host, stamp, tail, link):
    """HTML para clientes de correo: tablas y estilos en línea (Gmail y Outlook ignoran el CSS externo)."""
    import html as h
    label, pill_bg, pill_fg = EMAIL_LEVELS.get(level, EMAIL_LEVELS["info"])
    font = "-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
    mono = "ui-monospace,Menlo,Consolas,'Courier New',monospace"
    paragraphs = "".join(f'<p style="margin:0 0 12px;font:15px/1.55 {font};color:#4a4456;">{h.escape(p)}</p>'
                         for p in text.split("\n") if p.strip())
    facts = [("Servicio", service), ("Servidor", host), ("Cuándo", stamp)]
    facts_html = "".join(
        f'<tr><td style="padding:7px 0;border-top:1px solid #e1dde8;font:13px {font};color:#6a6478;">{k}</td>'
        f'<td align="right" style="padding:7px 0;border-top:1px solid #e1dde8;font:600 13px {font};color:#1c1924;">{h.escape(v)}</td></tr>'
        for k, v in facts if v)
    console = (f'<p style="margin:18px 0 6px;font:600 11px {mono};letter-spacing:1.5px;text-transform:uppercase;color:#6a6478;">'
               f'Últimas líneas de la consola</p>'
               f'<pre style="margin:0;padding:14px 16px;background:#1b1822;color:#e8e4f0;border-radius:10px;'
               f'font:12px/1.55 {mono};white-space:pre-wrap;word-break:break-word;">{h.escape(tail)}</pre>') if tail else ""
    button = (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:22px 0 4px;"><tr>'
              f'<td style="background:#6c3ff5;border-radius:10px;border-bottom:3px solid #3d1bb0;">'
              f'<a href="{h.escape(link)}" style="display:inline-block;padding:12px 22px;font:700 15px {font};'
              f'color:#ffffff;text-decoration:none;">Abrir en el panel</a></td></tr></table>') if link else ""
    preheader = h.escape(text.split("\n")[0][:140])
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"><title>{h.escape(subject)}</title></head>
<body style="margin:0;padding:0;background:#e9e6ee;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#e9e6ee;">
<tr><td align="center" style="padding:28px 12px 36px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;">
    <tr><td style="padding:0 6px 14px;">
      <table role="presentation" cellpadding="0" cellspacing="0"><tr>
        <td style="vertical-align:middle;"><img src="cid:orb@novahub" width="34" height="34" alt="" style="display:block;border:0;"></td>
        <td style="vertical-align:middle;padding-left:8px;font:800 19px {font};letter-spacing:-0.3px;color:#1c1924;">NovaHub</td>
      </tr></table>
    </td></tr>
    <tr><td style="background:#f7f5fa;border-radius:18px;border-bottom:3px solid #d3cddc;padding:26px 26px 22px;">
      <span style="display:inline-block;padding:4px 10px;border-radius:7px;background:{pill_bg};color:{pill_fg};
        font:700 11px {mono};letter-spacing:1.2px;text-transform:uppercase;">{label}</span>
      <h1 style="margin:14px 0 14px;font:800 23px/1.25 {font};letter-spacing:-0.4px;color:#1c1924;">{h.escape(subject)}</h1>
      {paragraphs}
      {console}
      {button}
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:18px;">{facts_html}</table>
    </td></tr>
    <tr><td align="center" style="padding:16px 10px 0;font:12px/1.5 {font};color:#8a8496;">
      Te escribe NovaHub porque tienes activados estos avisos. Puedes cambiarlos en ⚙ Ajustes del panel.
    </td></tr>
  </table>
</td></tr></table>
</body></html>"""


NTFY_PRIORITY = {"danger": 5, "warning": 4, "info": 3, "ok": 2}
NTFY_TAGS = {"danger": "rotating_light", "warning": "warning", "info": "information_source", "ok": "white_check_mark"}
NTFY_TOPIC = re.compile(r"[A-Za-z0-9_-]{1,64}")


class Notifier:
    """Avisos por dos canales: el móvil con ntfy (servidor propio, sin terceros) y el correo con Gmail
    (contraseña de aplicación). Se encolan y los envía un hilo propio: nada del panel espera nunca a un envío."""

    def __init__(self):
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.last = {}        # (tipo, servicio, clave) -> momento del último correo
        self.sent = []        # momentos de los correos de la última hora
        self.last_error = None
        self.last_sent = None
        self.ntfy_error = None
        self.ntfy_sent = None

    def config(self):
        return read_json(NOTIFY_FILE, {})

    def configured(self, cfg=None):
        cfg = cfg or self.config()
        return bool(cfg.get("user") and cfg.get("app_password"))

    @staticmethod
    def ntfy_cfg(cfg):
        n = cfg.get("ntfy") or {}
        return n if n.get("url") and n.get("topic") and n.get("enabled", True) else None

    def public(self):
        cfg = self.config()
        events = cfg.get("events") or {}
        n = cfg.get("ntfy") or {}
        nev = n.get("events") or {}
        return {"configured": self.configured(cfg), "user": cfg.get("user", ""), "to": cfg.get("to", ""),
                "events": [{"key": k, "label": v, "on": events.get(k, True), "ntfy": nev.get(k, True)} for k, v in NOTIFY_EVENTS.items()],
                "ntfy": {"configured": bool(self.ntfy_cfg(cfg)), "enabled": n.get("enabled", True), "url": n.get("url", ""),
                         "public_url": n.get("public_url", ""), "topic": n.get("topic", ""), "token": bool(n.get("token")),
                         "service": n.get("service"), "phone_user": n.get("phone_user"), "urgent": n.get("urgent", True),
                         "last_sent": self.ntfy_sent, "last_error": self.ntfy_error},
                "last_error": self.last_error, "last_sent": self.last_sent,
                "heartbeat_url": cfg.get("heartbeat_url", ""),
                "heartbeat_last": SUPERVISOR.last_ping, "heartbeat_error": SUPERVISOR.ping_error}

    def save(self, data):
        cfg = self.config()
        # solo cambia lo que llega en la petición: un guardado parcial no borra el resto
        user = str(data["user"] if "user" in data else cfg.get("user", "")).strip()
        if user and not EMAIL_RE.fullmatch(user):
            raise ApiError(400, "Escribe una dirección de Gmail válida")
        password = re.sub(r"\s+", "", str(data.get("app_password") or ""))  # Google la muestra con espacios
        if password and not re.fullmatch(r"[a-zA-Z]{16}", password):
            raise ApiError(400, "La contraseña de aplicación son 16 letras (Google la muestra en grupos de 4)")
        to = ", ".join(t.strip() for t in str(data["to"] if "to" in data else cfg.get("to", "")).split(",") if t.strip())
        for addr in filter(None, (t.strip() for t in to.split(","))):
            if not EMAIL_RE.fullmatch(addr):
                raise ApiError(400, f"Dirección de destino inválida: {addr}")
        if "heartbeat_url" in data:
            url = str(data.get("heartbeat_url") or "").strip()
            if url and (not re.fullmatch(r"https://[^\s]{8,300}", url)):
                raise ApiError(400, "La dirección del vigilante externo debe empezar por https:// (p. ej. https://hc-ping.com/…)")
            cfg["heartbeat_url"] = url
            SUPERVISOR.last_ping = SUPERVISOR.ping_error = None
        # sin «events» en la petición se conservan los guardados (no se reactivan todos)
        events = data["events"] if isinstance(data.get("events"), dict) else (cfg.get("events") or {})
        cfg.update(user=user, to=to, events={k: bool(events.get(k, True)) for k in NOTIFY_EVENTS})
        if isinstance(data.get("ntfy"), dict):
            cfg["ntfy"] = self._clean_ntfy(data["ntfy"], cfg.get("ntfy") or {})
        if password:
            cfg["app_password"] = password   # vacío = se mantiene la guardada
        if not user:
            cfg.pop("app_password", None)    # sin cuenta no tiene sentido guardar la contraseña
        write_json(NOTIFY_FILE, cfg)
        return self.public()

    @staticmethod
    def _clean_ntfy(d, old):
        n = dict(old)
        if "url" in d:
            url = str(d.get("url") or "").strip().rstrip("/")
            if url and not re.fullmatch(r"https?://[A-Za-z0-9.\-\[\]:]+(/[\w./-]*)?", url):
                raise ApiError(400, "La dirección de ntfy debe ser como http://127.0.0.1:8093 o https://ntfy.tudominio.com")
            n["url"] = url
        if "topic" in d:
            topic = str(d.get("topic") or "").strip()
            if topic and not NTFY_TOPIC.fullmatch(topic):
                raise ApiError(400, "El tema solo puede tener letras, números, guion y _")
            n["topic"] = topic
        if d.get("token"):  # vacío = se mantiene la guardada
            token = str(d["token"]).strip()
            if not re.fullmatch(r"tk_[A-Za-z0-9]{20,64}", token):
                raise ApiError(400, "La llave de ntfy empieza por tk_")
            n["token"] = token
        if d.get("clear_token"):
            n.pop("token", None)
        for k in ("enabled", "urgent"):
            if k in d:
                n[k] = bool(d[k])
        if isinstance(d.get("events"), dict):
            n["events"] = {k: bool(d["events"].get(k, True)) for k in NOTIFY_EVENTS}
        return n

    # ── componer y enviar ──
    def ntfy_payload(self, n, subject, text, sid=None, log=False, level="info"):
        tail = log_tail(sid, 12) if sid and log else ""
        link = (f"{PANEL_URL}/#/s/{sid}" if sid else PANEL_URL) if PANEL_URL else None
        prio = NTFY_PRIORITY.get(level, 3)
        if prio == 5 and not n.get("urgent", True):
            prio = 4
        body = text + (f"\n\nÚltimas líneas de la consola:\n{tail}" if tail else "")
        p = {"topic": n["topic"], "title": re.sub(r"[\r\n]+", " ", subject), "message": body[:3800], "priority": prio,
             "tags": [NTFY_TAGS.get(level, "information_source")]}
        if link:
            p["click"] = link
        return p

    @staticmethod
    def deliver_ntfy(n, payload):
        """Publicación JSON en ntfy (admite acentos y emojis en el título); con la llave si la hay."""
        import urllib.request
        headers = {"Content-Type": "application/json", "User-Agent": "NovaHub"}
        if n.get("token"):
            headers["Authorization"] = f"Bearer {n['token']}"
        req = urllib.request.Request(n["url"], data=json.dumps(payload).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read(10000)

    def compose(self, cfg, subject, text, sid=None, log=False, level="info"):
        """Correo con versión en texto y en HTML (estilo NovaHub, con el orbe incrustado)."""
        tail = log_tail(sid) if sid and log else ""
        link = (f"{PANEL_URL}/#/s/{sid}" if sid else PANEL_URL) if PANEL_URL else None
        stamp = f"{datetime.now():%d/%m/%Y %H:%M}"
        host = socket.gethostname()
        name = MANAGER.services.get(sid, {}).get("name") if sid and MANAGER else None

        lines = [text, ""]
        if tail:
            lines += ["Últimas líneas de la consola:", "─" * 40, tail, "─" * 40, ""]
        if link:
            lines.append(f"Abrir en el panel: {link}")
        lines.append(f"— NovaHub en {host}, {stamp}")

        msg = EmailMessage()
        msg["Subject"] = "[NovaHub] " + re.sub(r"[\r\n]+", " ", subject)
        msg["From"] = f"NovaHub <{cfg['user']}>"
        msg["To"] = cfg.get("to") or cfg["user"]
        msg.set_content("\n".join(lines))
        msg.add_alternative(email_html(subject, text, level, name, host, stamp, tail, link), subtype="html")
        msg.get_payload()[1].add_related(ORB_PNG, "image", "png", cid="<orb@novahub>", filename="novahub.png")
        return msg

    @staticmethod
    def deliver(cfg, msg):
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20, context=ssl.create_default_context()) as smtp:
            try:
                smtp.login(cfg["user"], cfg["app_password"])
            except smtplib.SMTPServerDisconnected as e:
                # Gmail suele cortar la conexión (en vez de responder 535) si la contraseña no vale
                raise smtplib.SMTPAuthenticationError(535, b"Gmail ha cerrado la conexion al identificarse") from e
            smtp.send_message(msg)

    def notify(self, *args, **kwargs):
        """Encola un aviso. Nunca lanza excepciones: se llama desde la vigilancia y no debe romperla."""
        try:
            self._notify(*args, **kwargs)
        except Exception:  # noqa: BLE001
            traceback.print_exc()

    def _notify(self, event, sid, subject, text, log=False, key="", level=None):
        level = level or ("danger" if key == "gaveup" or event == "novahub" else "info" if event == "power" else "warning")
        cfg = self.config()
        n = self.ntfy_cfg(cfg)
        to_mail = self.configured(cfg) and (cfg.get("events") or {}).get(event, True)
        to_ntfy = bool(n) and (n.get("events") or {}).get(event, True)
        if not to_mail and not to_ntfy:
            return
        now = time.time()
        with self.lock:
            k = (event, sid, key)
            if now - self.last.get(k, 0) < NOTIFY_COOLDOWN:
                return
            self.sent = [t for t in self.sent if now - t < 3600]
            if len(self.sent) >= NOTIFY_MAX_HOUR:
                return
            self.last[k] = now
            self.sent.append(now)
        if to_ntfy:
            self.queue.put(("ntfy", self.ntfy_payload(n, subject, text, sid, log, level)))
        if to_mail:
            self.queue.put(("email", self.compose(cfg, subject, text, sid, log, level)))

    def send_now(self, event, subject, text, level="info"):
        """Envío inmediato (p. ej. justo antes de apagar el servidor): no se puede dejar en la cola."""
        cfg = self.config()
        n = self.ntfy_cfg(cfg)
        if n and (n.get("events") or {}).get(event, True):
            try:
                self.deliver_ntfy(n, self.ntfy_payload(n, subject, text, level=level))
                self.ntfy_sent, self.ntfy_error = time.time(), None
            except Exception as e:  # noqa: BLE001
                self.ntfy_error = f"{datetime.now():%H:%M} · {e}"
        if not self.configured(cfg) or not (cfg.get("events") or {}).get(event, True):
            return
        try:
            self.deliver(cfg, self.compose(cfg, subject, text, level=level))
            self.last_sent, self.last_error = time.time(), None
        except Exception as e:  # noqa: BLE001
            self.last_error = f"{datetime.now():%H:%M} · {e}"

    def test_ntfy(self):
        n = self.ntfy_cfg(self.config())
        if not n:
            raise ApiError(400, "Primero configura ntfy (dirección y tema)")
        try:
            self.deliver_ntfy(n, self.ntfy_payload(n, "Aviso de prueba", "Los avisos de NovaHub llegan a tu móvil. 👋", level="ok"))
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if "403" in msg or "401" in msg:
                msg = "ntfy ha rechazado el envío: revisa la llave (tk_…) y que tenga permiso de escritura en el tema"
            self.ntfy_error = f"{datetime.now():%H:%M} · {msg}"
            raise ApiError(502, f"No se pudo enviar a ntfy: {msg}")
        self.ntfy_sent, self.ntfy_error = time.time(), None
        return self.public()

    def test(self):
        cfg = self.config()
        if not self.configured(cfg):
            raise ApiError(400, "Primero guarda tu Gmail y la contraseña de aplicación")
        try:
            self.deliver(cfg, self.compose(cfg, "Correo de prueba",
                                           "Los avisos de NovaHub funcionan. Te escribiremos aquí cuando algo vaya mal.",
                                           level="ok"))
        except smtplib.SMTPAuthenticationError:
            self.last_error = f"{datetime.now():%H:%M} · Gmail ha rechazado el usuario o la contraseña de aplicación"
            raise ApiError(400, "Gmail ha rechazado el acceso: revisa la dirección y la contraseña de aplicación "
                                "(no sirve tu contraseña normal)")
        except (OSError, smtplib.SMTPException) as e:
            self.last_error = f"{datetime.now():%H:%M} · {e}"
            raise ApiError(502, f"No se pudo enviar: {e}")
        self.last_sent, self.last_error = time.time(), None
        return self.public()

    def loop(self):
        while True:
            channel, msg = self.queue.get()
            for attempt in range(3):  # un envío puede fallar un momento: dos reintentos espaciados
                try:
                    if channel == "ntfy":
                        n = self.ntfy_cfg(self.config())
                        if n:
                            self.deliver_ntfy(n, msg)
                            self.ntfy_sent, self.ntfy_error = time.time(), None
                    else:
                        self.deliver(self.config(), msg)
                        self.last_sent, self.last_error = time.time(), None
                    break
                except Exception as e:  # noqa: BLE001
                    err = f"{datetime.now():%H:%M} · {e}"
                    if channel == "ntfy":
                        self.ntfy_error = err
                    else:
                        self.last_error = err
                    title = msg["title"] if channel == "ntfy" else msg["Subject"]
                    print(f"[avisos] no se pudo enviar por {channel} «{title}»: {e}", flush=True)
                    if isinstance(e, smtplib.SMTPAuthenticationError) or "403" in str(e) or "401" in str(e):
                        break  # con la contraseña o la llave mal, reintentar no sirve
                    time.sleep(30 * (attempt + 1))


NOTIFIER = Notifier()


# ───────────────────────────── vigilancia de NovaHub ─────────────────────────────

WATCHDOG_EVERY = 10                                     # segundos entre revisiones internas
HEARTBEAT_EVERY = 60                                    # segundos entre señales de vida al vigilante externo
LIFECYCLE_FILE = os.path.join(RUN_DIR, "novahub.lifecycle")  # «running» mientras funciona, «stopped» al cerrar bien


def sd_notify(msg):
    """Mensaje a systemd (READY=1, WATCHDOG=1…). Sin systemd (arrancado a mano) no hace nada."""
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return False
    if addr.startswith("@"):
        addr = "\0" + addr[1:]
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.connect(addr)
            sock.sendall(msg.encode())
        return True
    except OSError:
        return False


def previous_run():
    """Cómo terminó la ejecución anterior: «running» = no se cerró bien; None = primera vez."""
    try:
        with open(LIFECYCLE_FILE) as f:
            return f.read().strip() or None
    except OSError:
        return None


def mark_run(state):
    try:
        with open(LIFECYCLE_FILE, "w") as f:
            f.write(state)
    except OSError:
        pass


class Supervisor:
    """Lanza los hilos de NovaHub, los relanza si mueren y avisa a systemd de que todo responde.
    Si algo se queda colgado (un bucle sin latir, la web o la pasarela sin responder) deja de avisar
    y systemd reinicia NovaHub (WatchdogSec en novahub.service). Los servicios siguen vivos."""

    def __init__(self):
        self.threads = {}   # nombre -> (función, hilo)
        self.beats = {}     # nombre -> monotonic del último latido
        self.url = None
        self.last_ping = None   # vigilante externo (healthchecks.io): última señal de vida enviada
        self.ping_error = None
        self.next_ping = 0

    def spawn(self, name, target):
        thread = threading.Thread(target=target, name=name, daemon=True)
        thread.start()
        self.threads[name] = (target, thread)

    def beat(self, name):
        self.beats[name] = time.monotonic()

    def loop(self):
        while True:
            time.sleep(WATCHDOG_EVERY)
            try:
                self.check()
            except Exception:  # noqa: BLE001
                traceback.print_exc()

    def ping(self):
        """Señal de vida al vigilante externo: si deja de llegar (servidor caído, sin internet,
        NovaHub colgado), healthchecks.io avisa. Se manda en un hilo aparte: nunca frena la revisión."""
        url = NOTIFIER.config().get("heartbeat_url")
        if not url:
            return
        import urllib.request
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NovaHub"})
            with urllib.request.urlopen(req, timeout=15) as r:
                r.read(64)
            self.last_ping, self.ping_error = time.time(), None
        except Exception as e:  # noqa: BLE001
            self.ping_error = f"{datetime.now():%H:%M} · {e}"

    def http_ok(self):
        try:
            conn = http.client.HTTPConnection(*self.url, timeout=5)
            conn.request("GET", "/api/me")
            conn.getresponse().read()
            conn.close()
            return True
        except (OSError, http.client.HTTPException):
            return False

    def check(self):
        restarted, hung = [], []
        for name, (target, thread) in list(self.threads.items()):
            if not thread.is_alive():
                restarted.append(f"el hilo «{name}» se había detenido y se ha relanzado")
                self.spawn(name, target)
        now = time.monotonic()
        for name, limit in (("vigilancia", 30), ("salud", 60)):
            if name in self.beats and now - self.beats[name] > limit:
                hung.append(f"«{name}» lleva {int(now - self.beats[name])} s sin dar señales")
        try:
            asyncio.run_coroutine_threadsafe(asyncio.sleep(0), GATEWAY.loop).result(5)
        except Exception:  # noqa: BLE001
            hung.append("la pasarela de las webs publicadas no responde")
        if self.url and not self.http_ok():
            hung.append("la web del panel no responde")
        if not hung:
            sd_notify("WATCHDOG=1")  # todo responde; si dejamos de decirlo, systemd reinicia NovaHub
            if time.monotonic() >= self.next_ping:
                self.next_ping = time.monotonic() + HEARTBEAT_EVERY
                threading.Thread(target=self.ping, name="señal-de-vida", daemon=True).start()
        problems = restarted + hung
        for p in problems:
            print(f"[vigilancia interna] {p}", flush=True)
        if problems:
            NOTIFIER.notify("novahub", None, "Problema interno en NovaHub",
                            "NovaHub ha detectado un problema interno:\n- " + "\n- ".join(problems)
                            + ("\n\nComo algo está colgado, systemd reiniciará NovaHub en unos segundos "
                               "(tus servicios siguen funcionando)." if hung else ""), key="interno")


SUPERVISOR = Supervisor()


def journal_tail(lines=40):
    try:
        res = subprocess.run(["journalctl", "--user", "-u", "novahub", "--no-pager", "-o", "short-iso", "-n", str(lines)],
                             capture_output=True, text=True, timeout=10)
        return res.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def startup_notice(prev, failed):
    """Al arrancar: avisa del encendido del servidor y de si NovaHub (o el servidor) se cerró de golpe."""
    up = uptime()
    if up < BOOT_WINDOW:
        # recién encendido: se espera a que el autoarranque termine y los servicios se asienten,
        # para contar cómo han quedado de verdad (no los fallos pasajeros de los primeros segundos)
        threading.Thread(target=_boot_report, args=(prev,), name="aviso-encendido", daemon=True).start()
    elif prev == "running":
        tail = journal_tail()
        autostart = (f"\nNo han podido arrancar: {', '.join(failed)}." if failed
                     else "\nTodos los servicios con autoarranque están en marcha.")
        NOTIFIER.notify("novahub", None, "NovaHub se ha reiniciado tras un fallo",
                        "NovaHub se cerró de forma inesperada (un error, falta de memoria o el watchdog de systemd) "
                        "y systemd lo ha vuelto a arrancar. Tus servicios no se han visto afectados."
                        + autostart + (f"\n\nÚltimas líneas del registro de NovaHub:\n{tail}" if tail else ""))


def _boot_report(prev):
    end = time.time() + 240
    while time.time() < end and not MANAGER.autostart_done:
        time.sleep(2)
    time.sleep(60)  # margen para reintentos y comprobaciones de salud
    with MANAGER.lock:
        auto = [(sid, s) for sid, s in MANAGER.services.items() if s.get("autostart")]
        down = [s["name"] for sid, s in auto if not MANAGER.running(sid)]
    ok = [s["name"] for sid, s in auto if s["name"] not in down]
    lines = [f"El servidor se encendió hace {int(uptime() // 60)} min y NovaHub está en marcha."]
    if prev == "running":
        lines.insert(0, "La última vez NovaHub no se cerró de forma ordenada: probablemente hubo un corte de luz "
                        "o un reinicio forzado.")
    if ok:
        lines.append(f"En marcha: {', '.join(ok)}.")
    if down:
        lines.append(f"No han podido arrancar: {', '.join(down)}. NovaHub lo sigue intentando.")
    subject = "El servidor se ha encendido tras un apagado inesperado" if prev == "running" else "El servidor se ha encendido"
    NOTIFIER.notify("power", None, subject, "\n".join(lines), level="warning" if (down or prev == "running") else "ok")


# ───────────────────────────── desplegar desde GitHub ─────────────────────────────

PROJECTS_DIR = os.path.expanduser(os.environ.get("NOVAHUB_PROJECTS", "~/proyectos"))
REPO_REF = re.compile(r"^(?:https://github\.com/|git@github\.com:)?([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")
NPM_FLAGS = ["--no-audit", "--no-fund"]


def gh_repos():
    if not shutil.which("gh"):
        raise ApiError(501, "La CLI de GitHub (gh) no está instalada en el servidor")
    try:
        res = subprocess.run(["gh", "repo", "list", "--limit", "100",
                              "--json", "nameWithOwner,name,description,isPrivate,updatedAt,url"],
                             capture_output=True, text=True, timeout=30, env=GIT_ENV)
    except subprocess.TimeoutExpired:
        raise ApiError(504, "GitHub no responde")
    if res.returncode != 0:
        raise ApiError(502, f"No se pudo leer tu lista de repositorios: {res.stderr.strip()}")
    repos = json.loads(res.stdout or "[]")
    for r in repos:
        r["cloned"] = os.path.isdir(os.path.join(PROJECTS_DIR, r["name"]))
    return {"repos": sorted(repos, key=lambda r: r.get("updatedAt") or "", reverse=True), "projects_dir": PROJECTS_DIR}


def free_port(start):
    used = listening_ports() | {s.get("port") for s in MANAGER.services.values()}
    port = start
    while port in used:
        port += 1
    return port


def detect_project(path):
    """Tipo de proyecto y un servicio sugerido (comando, puerto, etiquetas) a partir de sus archivos."""
    has = lambda name: os.path.exists(os.path.join(path, name))  # noqa: E731
    if has("package.json"):
        try:
            with open(os.path.join(path, "package.json"), encoding="utf-8") as f:
                pkg = json.load(f)
        except (OSError, ValueError):
            pkg = {}
        scripts = pkg.get("scripts") or {}
        deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
        if "vite" in deps or "vite" in str(scripts.get("dev", "")):
            port = free_port(5173)
            return {"kind": "Vite", "command": f"npm run dev -- --host 127.0.0.1 --port {port} --strictPort", "port": port, "tags": ["web"]}
        if "next" in deps:
            port = free_port(3000)
            return {"kind": "Next.js", "command": f"npm run dev -- -p {port}", "port": port, "tags": ["web"]}
        port = free_port(3000)
        if "start" in scripts:
            return {"kind": "Node", "command": "npm start", "port": port, "env": {"PORT": str(port)}, "tags": ["node"]}
        if "dev" in scripts:
            return {"kind": "Node", "command": "npm run dev", "port": port, "env": {"PORT": str(port)}, "tags": ["node"]}
        return {"kind": "Node", "command": f"node {pkg.get('main') or 'index.js'}", "port": None, "tags": ["node"]}
    if has("requirements.txt") or has("pyproject.toml"):
        python = ".venv/bin/python" if has(".venv/bin/python") else "python3"
        if has("manage.py"):
            port = free_port(8000)
            return {"kind": "Django", "command": f"{python} manage.py runserver 127.0.0.1:{port}", "port": port, "tags": ["python", "web"]}
        entry = next((f for f in ("app.py", "main.py", "bot.py", "server.py", "run.py") if has(f)), None)
        return {"kind": "Python", "command": f"{python} {entry}" if entry else "", "port": None, "tags": ["python"]}
    if has("index.html"):
        port = free_port(8080)
        return {"kind": "Web estática", "command": f"python3 -m http.server {port} --bind 127.0.0.1", "port": port, "tags": ["web"]}
    return {"kind": "Desconocido", "command": "", "port": None, "tags": []}


PROJECT_MARKERS = ("package.json", "requirements.txt", "pyproject.toml", "index.html")


def project_dir(path):
    """La carpeta del proyecto: la raíz del repo o, si está vacía de proyecto, su única subcarpeta con uno."""
    if any(os.path.exists(os.path.join(path, m)) for m in PROJECT_MARKERS):
        return path
    subs = [os.path.join(path, d) for d in sorted(os.listdir(path))
            if not d.startswith(".") and os.path.isdir(os.path.join(path, d))]
    found = [d for d in subs if any(os.path.exists(os.path.join(d, m)) for m in PROJECT_MARKERS)]
    return found[0] if len(found) == 1 else path


def install_steps(path, changed=None):
    """Órdenes para instalar dependencias; con `changed` (archivos tocados por un pull), solo si hacen falta."""
    has = lambda name: os.path.exists(os.path.join(path, name))  # noqa: E731
    touched = lambda *names: changed is None or any(c in names for c in changed)  # noqa: E731
    steps = []
    if has("package.json") and (touched("package.json", "package-lock.json") or not has("node_modules")):
        steps.append((["npm", "ci" if has("package-lock.json") else "install", *NPM_FLAGS], "instalando dependencias de Node"))
    if has("requirements.txt") and has(".venv/bin/pip") and touched("requirements.txt"):
        steps.append(([".venv/bin/pip", "install", "-r", "requirements.txt"], "instalando dependencias de Python"))
    return steps


class Deployer:
    """Clonados en segundo plano (Cloudflare corta las peticiones de más de 100 s) y actualizaciones."""

    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()

    # ── clonar un repositorio ──
    def clone(self, data):
        m = REPO_REF.match(str(data.get("repo") or "").strip())
        if not m:
            raise ApiError(400, "Indica el repositorio como usuario/nombre o con su dirección de GitHub")
        owner, name = m.groups()
        dest = os.path.abspath(os.path.expanduser(str(data.get("dest") or "").strip() or os.path.join(PROJECTS_DIR, name)))
        if os.path.exists(dest) and (not os.path.isdir(dest) or os.listdir(dest)):
            raise ApiError(409, f"La carpeta {dest} ya existe y no está vacía: elige otra")
        if not os.path.isdir(os.path.dirname(dest)):
            raise ApiError(400, f"No existe la carpeta {os.path.dirname(dest)}")
        job = self.new_job()
        threading.Thread(target=self._clone, args=(job, owner, name, dest), daemon=True).start()
        return job["id"]

    def new_job(self):
        job = {"id": secrets.token_hex(6), "status": "running", "log": [], "result": None, "error": None, "started": time.time()}
        with self.lock:
            self.jobs = {k: v for k, v in self.jobs.items() if time.time() - v["started"] < 3600}
            self.jobs[job["id"]] = job
        return job

    def _run(self, job, cmd, cwd, timeout):
        job["log"].append(f"$ {' '.join(cmd)}")
        # en modo texto, el \r del progreso de git también corta línea: cada actualización llega por separado
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=GIT_ENV)
        watchdog = threading.Timer(timeout, proc.kill)  # aunque no escriba nada, no se queda colgado para siempre
        watchdog.start()
        try:
            self._read_progress(job, proc)
        finally:
            watchdog.cancel()
        if proc.wait() != 0:
            if proc.returncode == -signal.SIGKILL:
                limit = f"{timeout} s" if timeout < 120 else f"{timeout // 60} min"
                raise RuntimeError(f"«{cmd[0]} {cmd[1]}» ha tardado más de {limit} y se ha cortado")
            raise RuntimeError(f"«{cmd[0]} {cmd[1]}» ha fallado (código {proc.returncode})")

    @staticmethod
    def _read_progress(job, proc):
        for line in proc.stdout:
            line = line.rstrip()
            if line and job["log"] and line.split(":")[0] == job["log"][-1].split(":")[0] and "%" in line:
                job["log"][-1] = line  # el progreso reemplaza su línea en vez de añadir cientos
            elif line:
                job["log"].append(line)
            del job["log"][:-400]

    def _clone(self, job, owner, name, dest):
        try:
            self._run(job, ["git", "clone", "--progress", f"https://github.com/{owner}/{name}.git", dest], PROJECTS_DIR, 600)
            path = project_dir(dest)
            if path != dest:
                job["log"].append(f"▌el proyecto está en la subcarpeta {os.path.relpath(path, dest)}/")
            for cmd, what in install_steps(path):
                job["log"].append(f"▌{what}…")
                self._run(job, cmd, path, 900)
            info = detect_project(path)
            job["result"] = {"path": path, "name": name, "repo": f"{owner}/{name}", **info}
            job["log"].append(f"▌listo: proyecto {info['kind']} en {path}")
            job["status"] = "done"
        except Exception as e:  # noqa: BLE001
            job["error"] = str(e)
            job["log"].append(f"▌error: {e}")
            job["status"] = "error"

    def job(self, job_id):
        job = self.jobs.get(job_id)
        if not job:
            raise ApiError(404, "Esa tarea ya no existe")
        return job

    # ── actualizar un servicio: pull + dependencias + reinicio ──
    def update(self, sid):
        svc = MANAGER.services[sid]
        if svc.get("kind") in CONTAINER_KINDS:
            with MANAGER.lock:
                st = MANAGER.st(sid)
                if st.get("updating"):
                    raise ApiError(409, "Ya se está actualizando")
                st["updating"] = True
            threading.Thread(target=self._update_container, args=(sid,), daemon=True).start()
            return
        root = git_repo(svc)
        with MANAGER.lock:
            st = MANAGER.st(sid)
            if st.get("updating"):
                raise ApiError(409, "Ya se está actualizando")
            st["updating"] = True
        threading.Thread(target=self._update, args=(sid, root), daemon=True).start()

    def _update_container(self, sid):
        """«Actualizar» de un contenedor: descarga la versión nueva de la imagen y, si cambió, reinicia."""
        ok, msg = False, ""
        svc = MANAGER.services[sid]
        cwd = os.path.expanduser(svc.get("cwd") or "~")
        try:
            MANAGER.log(sid, "\x1b[35mbuscando una versión nueva de la imagen…\x1b[0m")
            if svc.get("kind") == "compose":
                f = ["-f", svc["compose_file"]] if svc.get("compose_file") else []
                self._logged(sid, ["podman-compose", "-p", container_name(sid), *f, "pull"], cwd, 1800)
                changed = True  # compose no dice si ha cambiado algo: se reinicia
            else:
                image = full_image(svc["image"])
                before = subprocess.run(["podman", "image", "inspect", "--format", "{{.Id}}", image], capture_output=True, text=True, timeout=30).stdout.strip()
                self._logged(sid, ["podman", "pull", image], cwd, 1800)
                after = subprocess.run(["podman", "image", "inspect", "--format", "{{.Id}}", image], capture_output=True, text=True, timeout=30).stdout.strip()
                changed = before != after
            if not changed:
                ok, msg = True, "Ya tenía la última versión de la imagen"
                MANAGER.log(sid, "ya tenía la última versión: no hace falta reiniciar")
            elif MANAGER.running(sid):
                MANAGER.log(sid, "imagen nueva: reiniciando")
                MANAGER.restart(sid)
                ok, msg = True, "Imagen actualizada"
            else:
                ok, msg = True, "Imagen actualizada (el servicio está parado)"
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            MANAGER.log(sid, f"\x1b[31mno se pudo actualizar la imagen: {e}\x1b[0m")
            NOTIFIER.notify("update", sid, f"No se pudo actualizar {svc['name']}",
                            f"La actualización de la imagen de «{svc['name']}» ha fallado: {e}", log=True)
        finally:
            with MANAGER.lock:
                st = MANAGER.st(sid)
                st["updating"] = False
                st["last_update"] = {"at": time.time(), "ok": ok, "msg": msg}
                MANAGER.save_state()

    def _logged(self, sid, cmd, cwd, timeout):
        with open(log_path(sid), "ab") as logf:
            res = subprocess.run(cmd, cwd=cwd, stdout=logf, stderr=subprocess.STDOUT, env=GIT_ENV, timeout=timeout)
        if res.returncode != 0:
            raise RuntimeError(f"«{' '.join(cmd[:2])}» ha fallado (código {res.returncode})")

    def _update(self, sid, root):
        ok, msg = False, ""
        try:
            MANAGER.log(sid, "\x1b[35mactualizando desde GitHub…\x1b[0m")
            before = git(root, "rev-parse", "HEAD").stdout.strip()
            self._logged(sid, ["git", "pull", "--ff-only"], root, 120)
            after = git(root, "rev-parse", "HEAD").stdout.strip()
            changed = git(root, "diff", "--name-only", before, after).stdout.split() if before != after else []
            steps = install_steps(root, changed)
            if before == after and not steps:
                ok, msg = True, "Ya estaba al día"
                MANAGER.log(sid, "ya estaba al día: no hace falta reiniciar")
                return
            for cmd, what in steps:
                MANAGER.log(sid, what + "…")
                self._logged(sid, cmd, root, 900)
            if MANAGER.services[sid].get("mode") == "prod":
                info = self._build(sid, root)
                with MANAGER.lock:  # por si venía de una versión que servía dist/ directamente
                    MANAGER.services[sid]["command"] = self.prod_command(info)
                    MANAGER.save_services()
            if MANAGER.running(sid):
                MANAGER.log(sid, f"{len(changed)} archivo(s) nuevos: reiniciando")
                MANAGER.restart(sid)
            else:
                MANAGER.log(sid, "actualizado; el servicio está parado, enciéndelo cuando quieras")
            ok, msg = True, f"Actualizado ({before[:7]} → {after[:7]})"
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            MANAGER.log(sid, f"\x1b[31mno se pudo actualizar: {e}\x1b[0m")
            name = MANAGER.services[sid]["name"]
            NOTIFIER.notify("update", sid, f"No se pudo actualizar {name}",
                            f"La actualización desde GitHub de «{name}» ha fallado: {e}", log=True)
        finally:
            with MANAGER.lock:
                st = MANAGER.st(sid)
                st["updating"] = False
                st["last_update"] = {"at": time.time(), "ok": ok, "msg": msg}
                MANAGER.save_state()

    # ── modo producción: compilar la web y servirla con serve.py ──
    def _build(self, sid, root):
        info = build_info(MANAGER.services[sid])
        if not info:
            raise RuntimeError("este proyecto no tiene script «build» en package.json")
        if not os.path.isdir(os.path.join(root, "node_modules")):
            for cmd, what in install_steps(root):
                MANAGER.log(sid, what + "…")
                self._logged(sid, cmd, root, 900)
        MANAGER.log(sid, "\x1b[35mcompilando para producción (npm run build)…\x1b[0m")
        t0 = time.time()
        self._logged(sid, ["npm", "run", "build"], root, 900)
        if not os.path.isfile(os.path.join(root, info["dir"], "index.html")):
            raise RuntimeError(f"la compilación no ha generado {info['dir']}/index.html")
        MANAGER.log(sid, f"\x1b[32mcompilado en {time.time() - t0:.0f} s → {info['dir']}/\x1b[0m")
        info["serve"] = self._publish_build(sid, root, info)
        return info

    @staticmethod
    def _publish_build(sid, root, info):
        """Copia la compilación a data/builds/<id>/<versión> y apunta «current» a ella. serve.py sirve esa
        copia: una compilación a medias o fallida (npm vacía dist/ al empezar) nunca rompe la web en marcha."""
        base = os.path.join(BUILDS_DIR, sid)
        os.makedirs(base, mode=0o700, exist_ok=True)
        ver = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        shutil.copytree(os.path.join(root, info["dir"]), os.path.join(base, ver), symlinks=True)
        link, tmp = os.path.join(base, "current"), os.path.join(base, "current.tmp")
        if os.path.lexists(tmp):
            os.remove(tmp)
        os.symlink(ver, tmp)
        os.replace(tmp, link)  # cambio atómico de versión
        versions = sorted(d for d in os.listdir(base) if d not in ("current", "current.tmp"))
        for old in versions[:-2]:  # se conserva la anterior: serve.py la usa hasta que se reinicia
            shutil.rmtree(os.path.join(base, old), ignore_errors=True)
        return link

    @staticmethod
    def prod_command(info):
        return (f"exec python3 {shlex.quote(SERVE_PY)} {shlex.quote(info['serve'])} "
                f'--port "$NOVAHUB_SERVICE_PORT"' + (" --spa" if info["spa"] else ""))

    def set_mode(self, sid, mode):
        if mode not in ("dev", "prod"):
            raise ApiError(400, "Modo desconocido")
        svc = MANAGER.services[sid]
        if mode == "dev":
            if svc.get("mode") != "prod":
                return
            with MANAGER.lock:
                svc = MANAGER.services[sid]
                svc.update(mode="dev", command=svc.get("dev_command") or svc["command"])
                MANAGER.save_services()
                MANAGER.log(sid, "\x1b[35mmodo desarrollo\x1b[0m")
                if MANAGER.running(sid):
                    MANAGER.restart(sid)
            return
        if not build_info(svc):
            raise ApiError(400, "Este servicio no tiene un script «build» en package.json")
        if not svc.get("port"):
            raise ApiError(400, "Para servir la web en producción, el servicio necesita un puerto")
        root = service_root(svc)
        with MANAGER.lock:
            st = MANAGER.st(sid)
            if st.get("updating"):
                raise ApiError(409, "Ya se está actualizando o compilando")
            st["updating"] = True
        threading.Thread(target=self._to_prod, args=(sid, root), name="compilar", daemon=True).start()

    def _to_prod(self, sid, root):
        ok, msg = False, ""
        try:
            info = self._build(sid, root)
            with MANAGER.lock:
                svc = MANAGER.services[sid]
                if svc.get("mode") != "prod":
                    svc["dev_command"] = svc["command"]  # para poder volver a desarrollo tal cual
                svc.update(mode="prod", command=self.prod_command(info))
                MANAGER.save_services()
                if MANAGER.running(sid):
                    MANAGER.log(sid, "reiniciando con la versión compilada")
                    MANAGER.restart(sid)
                else:
                    MANAGER.log(sid, "listo: enciende el servicio para servir la versión compilada")
            ok, msg = True, "Compilado para producción"
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            MANAGER.log(sid, f"\x1b[31mno se pudo compilar: {e}\x1b[0m")
            name = MANAGER.services[sid]["name"]
            NOTIFIER.notify("update", sid, f"No se pudo compilar {name}",
                            f"La compilación para producción de «{name}» ha fallado: {e}", log=True)
        finally:
            with MANAGER.lock:
                st = MANAGER.st(sid)
                st["updating"] = False
                st["last_update"] = {"at": time.time(), "ok": ok, "msg": msg}
                MANAGER.save_state()


SERVE_PY = os.path.join(BASE_DIR, "serve.py")
ANDROID_APK = os.path.join(DATA_DIR, "app", "NovaHub.apk")   # lo deja ahí android/build.sh (NOVAHUB_APK_OUT)
BUILDS_DIR = os.path.join(DATA_DIR, "builds")


def build_info(svc):
    """Si el servicio es una web con «npm run build»: carpeta de salida y si es una SPA. Si no, None."""
    try:
        root = os.path.realpath(os.path.expanduser(svc.get("cwd") or "~"))
        with open(os.path.join(root, "package.json"), encoding="utf-8") as f:
            pkg = json.load(f)
    except (OSError, ValueError):
        return None
    if not (pkg.get("scripts") or {}).get("build"):
        return None
    deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
    if "next" in deps:
        return None  # Next.js necesita su propio servidor («next start»), no archivos estáticos
    out = "build" if "react-scripts" in deps else "dist"
    spa = any(d in deps for d in ("react", "vue", "svelte", "preact", "solid-js", "@angular/core"))
    return {"dir": out, "spa": spa}


DEPLOYER = Deployer()


# ───────────────────────────── gráficas de uso ─────────────────────────────

METRICS_FILE = os.path.join(DATA_DIR, "metrics.json")
METRICS_STEP = 10           # una muestra cada 10 s → 1 h = 360 puntos
METRICS_COARSE = 300        # y una media cada 5 min → 24 h = 288 puntos
METRICS_RANGES = {"1h": (METRICS_STEP, 3600), "24h": (METRICS_COARSE, 86400)}


def cpu_times():
    """(ticks totales, ticks en reposo) de todo el servidor, de /proc/stat."""
    with open("/proc/stat") as f:
        vals = [int(v) for v in f.readline().split()[1:]]
    return sum(vals[:8]), vals[3] + vals[4]  # sin guest (ya va dentro de user); reposo = idle + iowait


class Metrics:
    """Historial de CPU y RAM del servidor («system») y de cada servicio en marcha.
    Puntos [t, cpu %, memoria en bytes]; la CPU del servidor es % del total y la de un servicio,
    % de un núcleo (como en top). Un servicio parado no tiene puntos: en la gráfica sale un hueco."""

    def __init__(self):
        self.lock = threading.Lock()
        self.fine, self.coarse = {}, {}   # clave -> deque de puntos
        self.prev_sys, self.prev_svc = None, {}
        self.last_coarse = time.time()
        data = read_json(METRICS_FILE, {})
        now = time.time()
        for store, name, (step, span) in ((self.fine, "fine", METRICS_RANGES["1h"]), (self.coarse, "coarse", METRICS_RANGES["24h"])):
            for key, pts in (data.get(name) or {}).items():
                store[key] = deque((p for p in pts if isinstance(p, list) and len(p) == 3 and p[0] > now - span),
                                   maxlen=span // step)

    def sample(self):
        now = time.time()
        total, idle = cpu_times()
        mem = meminfo()["used"]
        points = {}
        if self.prev_sys and total > self.prev_sys[0]:
            busy = 1 - (idle - self.prev_sys[1]) / (total - self.prev_sys[0])
            points["system"] = [round(now), round(max(0.0, busy) * 100, 1), mem]
        self.prev_sys = (total, idle)
        usage, mono = group_usage(), time.monotonic()
        with MANAGER.lock:
            running = {sid: MANAGER.state[sid]["pid"] for sid in MANAGER.services if MANAGER.running(sid)}
        for sid, pid in running.items():
            ticks, rss, _ = usage.get(pid, (0, 0, 0))
            prev = self.prev_svc.get(sid)
            if prev and prev[0] == pid and mono > prev[2]:
                points[sid] = [round(now), round(max(0, ticks - prev[1]) / CLK_TCK / (mono - prev[2]) * 100, 1), rss]
            self.prev_svc[sid] = (pid, ticks, mono)
        for sid in set(self.prev_svc) - set(running):
            del self.prev_svc[sid]
        with self.lock:
            for key, p in points.items():
                self.fine.setdefault(key, deque(maxlen=3600 // METRICS_STEP)).append(p)
            if now - self.last_coarse >= METRICS_COARSE:
                self._roll_up(now)

    def _roll_up(self, now):
        """Media de los últimos 5 min para la gráfica de 24 h, y se guarda en disco."""
        since = self.last_coarse
        self.last_coarse = now
        for key, pts in self.fine.items():
            recent = [p for p in pts if p[0] > since]
            if recent:
                self.coarse.setdefault(key, deque(maxlen=86400 // METRICS_COARSE)).append(
                    [round(now), round(sum(p[1] for p in recent) / len(recent), 1),
                     round(sum(p[2] for p in recent) / len(recent))])
        with MANAGER.lock:
            live = set(MANAGER.services) | {"system"}
        for store in (self.fine, self.coarse):  # servicios borrados
            for key in set(store) - live:
                del store[key]
        self._dump()

    def _dump(self):
        write_json(METRICS_FILE, {"fine": {k: list(v) for k, v in self.fine.items()},
                                  "coarse": {k: list(v) for k, v in self.coarse.items()}}, indent=None)

    def series(self, key, rng):
        step, span = METRICS_RANGES[rng]
        with self.lock:
            pts = list((self.fine if rng == "1h" else self.coarse).get(key) or ())
            if rng == "24h":  # el tramo de los últimos minutos aún sin media, para que llegue hasta ahora
                cut = pts[-1][0] if pts else 0
                tail = [p for p in self.fine.get(key) or () if p[0] > cut]
                if tail:
                    pts.append([tail[-1][0], round(sum(p[1] for p in tail) / len(tail), 1),
                                round(sum(p[2] for p in tail) / len(tail))])
        now = time.time()
        return {"range": rng, "step": step, "from": round(now - span), "to": round(now),
                "points": [p for p in pts if p[0] > now - span]}

    def loop(self):
        while True:
            time.sleep(METRICS_STEP)
            SUPERVISOR.beat("graficas")
            try:
                self.sample()
            except Exception:  # noqa: BLE001
                traceback.print_exc()

    def save(self):
        with self.lock:
            self._dump()


METRICS = Metrics()


# ───────────────────────────── copias de seguridad ─────────────────────────────

# Las copias van al disco duro de datos (HDD), no al SSD del sistema: si el SSD muere, las copias siguen ahí.
# Punto de montaje de un disco aparte para las copias (p. ej. /mnt/datos). Si está puesto y el disco no está montado,
# no se hacen copias (no se escriben por error en el disco del sistema). Vacío = se guardan en data/novahub-copias.
BACKUP_MOUNT = os.environ.get("NOVAHUB_BACKUP_MOUNT", "")
SNAPSHOT_DIR = os.path.abspath(os.environ.get("NOVAHUB_BACKUP_DIR", os.path.join(BACKUP_MOUNT or DATA_DIR, "novahub-copias")))
# bk_DDMMAA_HHMMSS_tipo.tar.gz → bk_061026_040000_auto.tar.gz (fecha de la copia; la hora evita choques el mismo día)
SNAPSHOT_NAME = re.compile(r"bk_\d{6}_\d{6}_(auto|manual|antes-de-restaurar|antes-de-actualizar)\.tar\.gz")
BACKUP_DEFAULTS = {"enabled": False, "every": "daily", "at": "04:00", "hours": 6, "paths": [],
                   "exclude": ["node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build", ".cache", ".next"],
                   "keep": 7, "stop": False}
BACKUP_MIN_FREE = 1024 ** 3  # no se empieza una copia con menos de 1 GB libre
BACKUP_RETRY = 1800          # una copia automática fallida se reintenta a los 30 min


def backup_config(svc):
    return {**BACKUP_DEFAULTS, **(svc.get("backup") or {})}


def _own_rels(root):
    """Rutas relativas de data/ de NovaHub y de la carpeta de copias si están dentro de la del servicio
    (nunca se copian ni se borran)."""
    out = []
    for d in (DATA_DIR, SNAPSHOT_DIR):
        real = os.path.realpath(d)
        if real == root or real.startswith(root + os.sep):
            out.append(os.path.relpath(real, root))
    return out


def disk_kind(path):
    """«HDD» o «SSD» según el disco donde está la ruta (/sys/.../queue/rotational); None si no se sabe."""
    try:
        st = os.stat(path)
        dev = os.path.realpath(f"/sys/dev/block/{os.major(st.st_dev)}:{os.minor(st.st_dev)}")
        for d in (dev, os.path.dirname(dev)):  # partición → disco
            f = os.path.join(d, "queue", "rotational")
            if os.path.exists(f):
                with open(f) as fh:
                    return "HDD" if fh.read().strip() == "1" else "SSD"
    except (OSError, ValueError):
        pass
    return None


def backup_disk():
    """Dónde se guardan las copias y si el disco está disponible."""
    mounted = not BACKUP_MOUNT or os.path.ismount(BACKUP_MOUNT)
    probe = SNAPSHOT_DIR if os.path.isdir(SNAPSHOT_DIR) else (BACKUP_MOUNT or DATA_DIR)
    try:
        du = shutil.disk_usage(probe)
        free, total = du.free, du.total
    except OSError:
        free = total = None
    return {"path": SNAPSHOT_DIR, "mounted": mounted, "kind": disk_kind(probe) if mounted else None,
            "free": free, "total": total}


def snapshot_time(name, path=None):
    """Fecha de una copia a partir de su nombre (bk_DDMMAA_HHMMSS…); si no, la del archivo."""
    try:
        return datetime.strptime(name[3:16], "%d%m%y_%H%M%S").timestamp()
    except ValueError:
        return os.path.getmtime(path) if path else 0


SQLITE_SUFFIXES = (".sqlite", ".sqlite3", ".db")


def is_sqlite(path):
    """Base de datos SQLite (por la cabecera, no solo por la extensión)."""
    if not path.endswith(SQLITE_SUFFIXES) or not os.path.isfile(path) or os.path.islink(path):
        return False
    try:
        with open(path, "rb") as f:
            return f.read(16) == b"SQLite format 3\x00"
    except OSError:
        return False


def sqlite_copy(src, dest):
    """Copia coherente de una base de datos SQLite en uso (API de copia de SQLite: respeta el WAL y los bloqueos);
    copiar el archivo a pelo mientras la app escribe puede dejarla corrupta en la copia."""
    import sqlite3
    con = sqlite3.connect(f"file:{src}?mode=ro", uri=True, timeout=30)
    try:
        out = sqlite3.connect(dest)
        try:
            con.backup(out)
        finally:
            out.close()
    finally:
        con.close()


def _excluded(name, patterns):
    import fnmatch
    return any(fnmatch.fnmatch(name, p) for p in patterns)


class Backups:
    """Copias .tar.gz de la carpeta de un servicio (o de algunas subcarpetas), programadas o a mano,
    y restauración con copia previa del estado actual. Todo en segundo plano, con el progreso en la consola."""

    def __init__(self):
        self.lock = threading.Lock()
        self.busy = set()   # servicios con una copia o restauración en curso

    # ── configuración ──
    def save_config(self, sid, data):
        cfg = backup_config(MANAGER.services[sid])
        root = service_root(MANAGER.services[sid])
        every = data.get("every", cfg["every"])
        if every not in ("daily", "hours"):
            raise ApiError(400, "Frecuencia desconocida")
        at = str(data.get("at", cfg["at"])).strip()
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", at):
            raise ApiError(400, "La hora debe tener el formato HH:MM (p. ej. 04:00)")
        try:
            hours, keep = int(data.get("hours", cfg["hours"])), int(data.get("keep", cfg["keep"]))
        except (TypeError, ValueError):
            raise ApiError(400, "Las horas y el número de copias deben ser números")
        if not 1 <= hours <= 168 or not 1 <= keep <= 100:
            raise ApiError(400, "Cada 1–168 horas y entre 1 y 100 copias")
        paths = data.get("paths", cfg["paths"])
        if isinstance(paths, str):
            paths = [p.strip() for p in paths.replace("\n", ",").split(",") if p.strip()]
        clean = []
        for p in paths:
            full = safe_path(root, p)  # dentro de la carpeta del servicio
            if not os.path.exists(full):
                raise ApiError(400, f"No existe «{p}» dentro de la carpeta del servicio")
            clean.append(os.path.relpath(full, root))
        exclude = data.get("exclude", cfg["exclude"])
        if isinstance(exclude, str):
            exclude = [e.strip() for e in exclude.replace("\n", ",").split(",") if e.strip()]
        new = {"enabled": bool(data.get("enabled", cfg["enabled"])), "every": every, "at": at, "hours": hours,
               "paths": clean, "exclude": [str(e)[:100] for e in exclude][:50], "keep": keep,
               "stop": bool(data.get("stop", cfg["stop"]))}
        with MANAGER.lock:
            MANAGER.services[sid]["backup"] = new
            MANAGER.save_services()
        return self.public(sid)

    def folder(self, sid):
        return os.path.join(SNAPSHOT_DIR, sid)

    def list(self, sid, kind=None):
        """Copias de un servicio, de la más nueva a la más antigua."""
        folder = self.folder(sid)
        copies = []
        if os.path.isdir(folder):
            for name in os.listdir(folder):
                m = SNAPSHOT_NAME.fullmatch(name)
                if m and (kind is None or m.group(1) == kind):
                    full = os.path.join(folder, name)
                    copies.append({"name": name, "label": name.split("_")[0] + "_" + name.split("_")[1],
                                   "size": os.path.getsize(full), "created": snapshot_time(name, full),
                                   "kind": m.group(1)})
        return sorted(copies, key=lambda c: c["created"], reverse=True)

    def public(self, sid):
        state = (MANAGER.state.get(sid) or {}).get("backup") or {}
        return {"config": backup_config(MANAGER.services[sid]), "copies": self.list(sid), "running": sid in self.busy,
                "last": state, "next": self.next_run(sid), "disk": backup_disk()}

    def path_of(self, sid, name):
        if not SNAPSHOT_NAME.fullmatch(str(name or "")):
            raise ApiError(400, "Nombre de copia inválido")
        full = os.path.join(self.folder(sid), name)
        if not os.path.isfile(full):
            raise ApiError(404, "Esa copia no existe")
        return full

    def delete(self, sid, name):
        os.remove(self.path_of(sid, name))
        return self.public(sid)

    # ── hacer una copia ──
    def start(self, sid, kind="manual"):
        with self.lock:
            if sid in self.busy:
                raise ApiError(409, "Ya hay una copia o restauración en curso")
            self.busy.add(sid)
        threading.Thread(target=self._run, args=(sid, kind), name="copia", daemon=True).start()

    def _run(self, sid, kind):
        svc = MANAGER.services[sid]
        cfg = backup_config(svc)
        restart = False
        try:
            if cfg["stop"] and MANAGER.running(sid):
                MANAGER.log(sid, "copia de seguridad: se para el servicio para copiar sus datos sin cambios a medias")
                restart = self._stop_and_wait(sid)
            name = self.snapshot(sid, kind)
            self._record(sid, True, f"Copia {name}", name)
        except Exception as e:  # noqa: BLE001
            msg = e.msg if isinstance(e, ApiError) else str(e)
            MANAGER.log(sid, f"\x1b[31mla copia de seguridad ha fallado: {msg}\x1b[0m")
            self._record(sid, False, msg, failed_auto=kind == "auto")
            NOTIFIER.notify("backup", sid, f"Ha fallado la copia de seguridad de {svc['name']}",
                            f"La copia de seguridad de «{svc['name']}» ha fallado: {msg}", level="danger")
        finally:
            if restart:
                try:
                    MANAGER.start(sid)
                except ApiError as e:
                    MANAGER.log(sid, f"\x1b[31mno se pudo volver a arrancar: {e.msg}\x1b[0m")
            with self.lock:
                self.busy.discard(sid)

    def snapshot(self, sid, kind):
        """Crea la copia (en un temporal que se renombra al acabar) y aplica la retención."""
        import tarfile
        svc = MANAGER.services[sid]
        cfg, root = backup_config(svc), service_root(svc)
        disk = backup_disk()
        if not disk["mounted"]:
            # Sin el disco montado, /mnt/dades es una carpeta vacía del SSD: no se escribe ahí.
            raise ApiError(503, f"El disco duro de copias ({BACKUP_MOUNT}) no está montado")
        if (disk["free"] or 0) < BACKUP_MIN_FREE:
            raise ApiError(507, "Queda menos de 1 GB libre en el disco de copias: no se hace la copia")
        folder = self.folder(sid)
        os.makedirs(SNAPSHOT_DIR, mode=0o700, exist_ok=True)  # privada también la carpeta común (.env, claves…)
        os.makedirs(folder, mode=0o700, exist_ok=True)
        now = datetime.now()
        while True:  # dos copias en el mismo segundo (p. ej. la previa a restaurar justo tras otra)
            name = f"bk_{now:%d%m%y_%H%M%S}_{kind}.tar.gz"
            if not os.path.exists(os.path.join(folder, name)):
                break
            now += timedelta(seconds=1)
        final, tmp = os.path.join(folder, name), os.path.join(folder, f".{name}.tmp")
        scope = cfg["paths"] or ["."]
        MANAGER.log(sid, f"\x1b[35mcopia de seguridad ({', '.join(scope)})…\x1b[0m")
        t0, count = time.time(), [0]

        own = _own_rels(root)
        dbs = []  # bases de datos SQLite: se copian aparte, con la API de SQLite, al final

        def keep(info):
            if any((os.path.normpath(info.name) + "/").startswith(o + "/") for o in own):
                return None  # la carpeta de datos de NovaHub y la de copias nunca entran
            parts = info.name.split("/")
            if any(_excluded(p, cfg["exclude"]) for p in parts if p not in (".", "")):
                return None
            if info.isfile():
                full = os.path.join(root, info.name)
                if is_sqlite(full):
                    dbs.append(info.name)
                    return None
                for side in ("-wal", "-shm", "-journal"):  # lo pendiente del WAL ya va dentro de la copia coherente
                    if info.name.endswith(side) and is_sqlite(full[:-len(side)]):
                        return None
            count[0] += info.isfile()
            return info

        def add_databases(tar):
            for arc in dbs:
                full, tmp_db = os.path.join(root, arc), os.path.join(folder, f".{name}.sqlite.tmp")
                try:
                    sqlite_copy(full, tmp_db)
                    tar.add(tmp_db, arcname=arc)
                    MANAGER.log(sid, f"base de datos copiada sin cortes: {os.path.normpath(arc)}")
                except Exception as e:  # noqa: BLE001
                    MANAGER.log(sid, f"\x1b[33mno se pudo copiar {arc} con SQLite ({e}): se copia el archivo tal cual\x1b[0m")
                    for side in ("", "-wal", "-shm"):
                        if os.path.isfile(full + side):
                            tar.add(full + side, arcname=arc + side)
                finally:
                    try:
                        os.remove(tmp_db)
                    except OSError:
                        pass
                count[0] += 1

        try:
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            meta = {"novahub.exclude": json.dumps(cfg["exclude"])}  # para restaurar con las mismas exclusiones
            with os.fdopen(fd, "wb") as raw, tarfile.open(fileobj=raw, mode="w:gz", compresslevel=6,
                                                           format=tarfile.PAX_FORMAT, pax_headers=meta) as tar:
                for rel in scope:
                    tar.add(os.path.join(root, rel), arcname=os.path.normpath(rel), filter=keep)
                add_databases(tar)
            os.replace(tmp, final)
        except BaseException:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise
        size = os.path.getsize(final)
        MANAGER.log(sid, f"\x1b[32mcopia lista: {count[0]} archivos, {size / 2**20:.1f} MB en {time.time() - t0:.0f} s → {name}\x1b[0m")
        self.prune(sid, cfg["keep"])
        return name

    def prune(self, sid, keep):
        """Retención: las automáticas según «conservar»; de las previas a restaurar, las 3 últimas.
        Las manuales solo se borran a mano."""
        folder = self.folder(sid)
        for kind, limit in (("auto", keep), ("antes-de-restaurar", 3), ("antes-de-actualizar", 3)):
            for c in self.list(sid, kind)[limit:]:  # por fecha: el nombre DDMMAA no se ordena solo
                os.remove(os.path.join(folder, c["name"]))

    def _stop_and_wait(self, sid):
        """Para el servicio y espera a que termine. True si estaba en marcha o pendiente de reintento
        (hay que volver a arrancarlo al acabar)."""
        if not MANAGER.running(sid) and sid not in MANAGER.transition:
            pending = bool((MANAGER.state.get(sid) or {}).get("restart_at"))
            if pending:
                MANAGER.stop(sid)  # cancela el reintento: no puede arrancar a mitad de la restauración
            return pending
        MANAGER.stop(sid)
        end = time.time() + MANAGER.services[sid].get("stop_timeout", 15) + 20
        while time.time() < end and (MANAGER.running(sid) or sid in MANAGER.transition):
            time.sleep(0.5)
        if MANAGER.running(sid):
            raise ApiError(500, "el servicio no se ha detenido a tiempo")
        return True

    def _record(self, sid, ok, msg, name=None, failed_auto=False):
        with MANAGER.lock:
            st = MANAGER.st(sid)
            prev = st.get("backup") or {}
            st["backup"] = {**prev, "at": time.time(), "ok": ok, "msg": msg,
                            **({"last_name": name, "last_ok_at": time.time()} if name else {}),
                            **({"last_auto": time.time()} if name and name.endswith("_auto.tar.gz") else {}),
                            **({"auto_failed_at": time.time()} if failed_auto else {})}
            MANAGER.save_state()

    # ── restaurar ──
    def restore(self, sid, name):
        self.path_of(sid, name)
        with self.lock:
            if sid in self.busy:
                raise ApiError(409, "Ya hay una copia o restauración en curso")
            self.busy.add(sid)
        threading.Thread(target=self._restore, args=(sid, name), name="restaurar", daemon=True).start()

    def _restore(self, sid, name):
        import tarfile
        svc = MANAGER.services[sid]
        cfg, root = backup_config(svc), service_root(svc)
        restart = False
        try:
            MANAGER.log(sid, f"\x1b[35mrestaurando la copia {name}…\x1b[0m")
            restart = self._stop_and_wait(sid)
            safety = self.snapshot(sid, "antes-de-restaurar")
            MANAGER.log(sid, f"el estado actual queda guardado en {safety}")
            with tarfile.open(self.path_of(sid, name), "r:gz") as tar:
                members = tar.getmembers()
                try:  # lo que se excluyó al hacer ESA copia (si hoy se excluye otra cosa, no se borra nada de más)
                    exclude = json.loads(tar.pax_headers["novahub.exclude"])
                except (KeyError, ValueError):
                    exclude = cfg["exclude"]
                tops = {m.name.split("/")[0] for m in members}
                in_archive = {os.path.normpath(m.name) for m in members}
                # Deja cada carpeta copiada exactamente como en la copia: borra lo que no estaba en ella
                # (salvo lo excluido, que nunca se copió: node_modules, .git…).
                for top in tops:
                    base = root if top == "." else safe_path(root, top)
                    if os.path.isfile(base) or os.path.islink(base):
                        continue
                    own = {os.path.realpath(DATA_DIR), os.path.realpath(SNAPSHOT_DIR)}
                    for dirpath, dirnames, filenames in os.walk(base, topdown=True):
                        dirnames[:] = [d for d in dirnames if not _excluded(d, exclude)
                                       and os.path.realpath(os.path.join(dirpath, d)) not in own]
                        for fname in filenames:
                            full = os.path.join(dirpath, fname)
                            rel = os.path.normpath(os.path.join(top, os.path.relpath(full, base)))
                            if rel not in in_archive and not _excluded(fname, exclude):
                                os.remove(full)
                tar.extractall(root, filter="data")  # filtro «data»: nada fuera de la carpeta ni enlaces peligrosos
            MANAGER.log(sid, f"\x1b[32mrestaurada la copia {name}\x1b[0m")
            self._record(sid, True, f"Restaurada {name}")
        except Exception as e:  # noqa: BLE001
            msg = e.msg if isinstance(e, ApiError) else str(e)
            MANAGER.log(sid, f"\x1b[31mno se pudo restaurar: {msg}\x1b[0m")
            self._record(sid, False, f"Restauración fallida: {msg}")
            NOTIFIER.notify("backup", sid, f"Ha fallado la restauración de {svc['name']}",
                            f"No se pudo restaurar la copia {name} de «{svc['name']}»: {msg}", level="danger", log=True)
        finally:
            if restart:
                try:
                    MANAGER.start(sid)
                except ApiError as e:
                    MANAGER.log(sid, f"\x1b[31mno se pudo volver a arrancar: {e.msg}\x1b[0m")
            with self.lock:
                self.busy.discard(sid)

    # ── programación ──
    def next_run(self, sid):
        cfg = backup_config(MANAGER.services[sid])
        if not cfg["enabled"]:
            return None
        state = (MANAGER.state.get(sid) or {}).get("backup") or {}
        last = state.get("last_auto") or 0
        if cfg["every"] == "hours":
            nxt = max(time.time(), last + cfg["hours"] * 3600) if last else time.time()
        else:
            h, m = map(int, cfg["at"].split(":"))
            today = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0).timestamp()
            nxt = today if last < today else today + 86400
        failed = state.get("auto_failed_at") or 0
        if failed > last:  # la última automática falló (disco sin montar…): se reintenta cada 30 min
            nxt = max(nxt, failed + BACKUP_RETRY)
        return nxt

    def loop(self):
        while True:
            time.sleep(30)
            SUPERVISOR.beat("copias")
            try:
                for sid in list(MANAGER.services):
                    nxt = self.next_run(sid)
                    if nxt and nxt <= time.time() and sid not in self.busy:
                        MANAGER.log(sid, "copia de seguridad programada")
                        self.start(sid, "auto")
            except Exception:  # noqa: BLE001
                traceback.print_exc()


BACKUPS = Backups()


# ───────────────────────────── tareas programadas ─────────────────────────────

TASK_ACTIONS = {"start": "Encender", "stop": "Apagar", "restart": "Reiniciar", "input": "Escribir en la consola",
                "command": "Ejecutar un comando"}
TASK_MAX = 20                # tareas por servicio
TASK_GRACE = 180             # si NovaHub iba con retraso, una tarea se lanza hasta 3 min tarde (nunca dos veces)
TASK_COMMAND_TIMEOUT = 600   # un comando programado se corta a los 10 min


class Scheduler:
    """Tareas a una hora fija y ciertos días de la semana, por servicio: encender, apagar, reiniciar,
    escribir en su consola o ejecutar un comando en su carpeta. Lo que pasó queda en la consola del servicio."""

    def __init__(self):
        self.running = set()   # (servicio, tarea) en curso

    # ── configuración ──
    @staticmethod
    def normalize(raw):
        if not isinstance(raw, list):
            raise ApiError(400, "Se esperaba una lista de tareas")
        if len(raw) > TASK_MAX:
            raise ApiError(400, f"Como mucho {TASK_MAX} tareas por servicio")
        out, seen = [], set()
        for t in raw:
            if not isinstance(t, dict):
                raise ApiError(400, "Tarea inválida")
            action = t.get("action")
            if action not in TASK_ACTIONS:
                raise ApiError(400, "Acción desconocida")
            at = str(t.get("at") or "").strip()
            if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", at):
                raise ApiError(400, "La hora debe tener el formato HH:MM (p. ej. 04:30)")
            days = sorted({int(d) for d in (t.get("days") or []) if str(d).isdigit() and 0 <= int(d) <= 6})
            if not days:
                raise ApiError(400, "Elige al menos un día")
            text = str(t.get("text") or "")
            if action in ("input", "command"):
                if not text.strip() or "\n" in text or len(text) > 2000:
                    raise ApiError(400, "Escribe el texto o comando (una sola línea)")
            else:
                text = ""
            tid = str(t.get("id") or "")
            if not re.fullmatch(r"[0-9a-f]{8}", tid) or tid in seen:
                tid = secrets.token_hex(4)
            seen.add(tid)
            out.append({"id": tid, "action": action, "at": at, "days": days, "text": text,
                        "enabled": bool(t.get("enabled", True))})
        return out

    def save(self, sid, raw):
        tasks = self.normalize(raw)
        with MANAGER.lock:
            MANAGER.services[sid]["tasks"] = tasks
            st = MANAGER.st(sid)
            ids = {t["id"] for t in tasks}
            st["tasks"] = {k: v for k, v in (st.get("tasks") or {}).items() if k in ids}  # olvida las borradas
            MANAGER.save_services()
            MANAGER.save_state()
        return self.public(sid)

    @staticmethod
    def next_time(task, now=None):
        """Próxima vez que toca (timestamp), mirando hasta una semana adelante."""
        now = now or datetime.now()
        h, m = map(int, task["at"].split(":"))
        for add in range(8):
            day = (now + timedelta(days=add)).replace(hour=h, minute=m, second=0, microsecond=0)
            if day.weekday() in task["days"] and day > now:
                return day.timestamp()
        return None

    def public(self, sid):
        svc, st = MANAGER.services[sid], MANAGER.state.get(sid) or {}
        last = st.get("tasks") or {}
        return {"tasks": [{**t, "next": self.next_time(t) if t["enabled"] else None, "last": last.get(t["id"]),
                           "busy": (sid, t["id"]) in self.running} for t in svc.get("tasks") or []],
                "actions": TASK_ACTIONS}

    def run_now(self, sid, tid):
        """«Probar ahora» desde la interfaz: lanza la tarea en el momento, sin esperar a su hora."""
        task = next((dict(t) for t in MANAGER.services[sid].get("tasks") or [] if t["id"] == tid), None)
        if not task:
            raise ApiError(404, "Esa tarea no existe (¿has guardado los cambios?)")
        with MANAGER.lock:
            if (sid, tid) in self.running:
                raise ApiError(409, "Esa tarea ya está en marcha")
            self.running.add((sid, tid))
        threading.Thread(target=self.run, args=(sid, task, "manual"), name="tarea", daemon=True).start()
        return self.public(sid)

    # ── ejecución ──
    def loop(self):
        while True:
            time.sleep(15)
            SUPERVISOR.beat("tareas")
            try:
                self.tick(datetime.now())
            except Exception:  # noqa: BLE001
                traceback.print_exc()

    def tick(self, now):
        with MANAGER.lock:
            todo = [(sid, dict(t)) for sid, s in MANAGER.services.items() for t in s.get("tasks") or [] if t.get("enabled")]
        for sid, t in todo:
            h, m = map(int, t["at"].split(":"))
            when = now.replace(hour=h, minute=m, second=0, microsecond=0)
            key = when.strftime("%Y-%m-%d %H:%M")
            if when.weekday() not in t["days"] or not 0 <= (now - when).total_seconds() < TASK_GRACE:
                continue
            with MANAGER.lock:
                st = MANAGER.st(sid)
                done = st.setdefault("tasks", {})
                if (done.get(t["id"]) or {}).get("key") == key or (sid, t["id"]) in self.running:
                    continue
                done[t["id"]] = {"key": key, "at": time.time(), "ok": None, "msg": "en curso"}
                MANAGER.save_state()
                self.running.add((sid, t["id"]))
            threading.Thread(target=self.run, args=(sid, t, key), name="tarea", daemon=True).start()

    def run(self, sid, t, key):
        label = TASK_ACTIONS[t["action"]].lower()
        MANAGER.log(sid, f"\x1b[35mtarea programada ({t['at']}): {label}"
                         + (f" \x1b[2m{t['text']}\x1b[0m" if t["text"] else "") + "\x1b[0m")
        ok, msg = True, "Hecho"
        try:
            msg = self.do(sid, t)
        except Exception as e:  # noqa: BLE001
            ok, msg = False, e.msg if isinstance(e, ApiError) else str(e)
            MANAGER.log(sid, f"\x1b[31mla tarea programada ha fallado: {msg}\x1b[0m")
            name = MANAGER.services.get(sid, {}).get("name", sid)
            NOTIFIER.notify("task", sid, f"Ha fallado una tarea programada de {name}",
                            f"La tarea «{label}» de las {t['at']} de «{name}» ha fallado: {msg}", log=True)
        finally:
            with MANAGER.lock:
                self.running.discard((sid, t["id"]))
                if sid not in MANAGER.services:
                    return  # el servicio se ha borrado mientras tanto
                st = MANAGER.st(sid)
                done = st.setdefault("tasks", {})
                if key == "manual":  # «Probar» no cuenta como la ejecución programada de hoy
                    key = (done.get(t["id"]) or {}).get("key")
                done[t["id"]] = {"key": key, "at": time.time(), "ok": ok, "msg": msg}
                MANAGER.save_state()

    @staticmethod
    def do(sid, t):
        action = t["action"]
        if action == "start":
            if MANAGER.running(sid):
                return "Ya estaba encendido"
            MANAGER.start(sid)
            return "Encendido"
        if action == "stop":
            if not MANAGER.running(sid) and not (MANAGER.state.get(sid) or {}).get("restart_at"):
                return "Ya estaba apagado"
            MANAGER.stop(sid)
            return "Apagado"
        if action == "restart":
            if MANAGER.running(sid):
                MANAGER.restart(sid)
                return "Reiniciado"
            MANAGER.start(sid)
            return "Estaba apagado: encendido"
        if action == "input":
            MANAGER.send_input(sid, t["text"])
            return "Enviado a la consola"
        # command: en la carpeta del servicio, con sus variables, salida a su consola y límite de tiempo
        svc = MANAGER.services[sid]
        env = {**os.environ, **(svc.get("env") or {})}
        with open(log_path(sid), "ab") as logf:
            proc = subprocess.Popen(["bash", "-lc", t["text"]], cwd=service_root(svc), stdout=logf,
                                    stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env, start_new_session=True)
            try:
                code = proc.wait(timeout=TASK_COMMAND_TIMEOUT)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                raise RuntimeError(f"el comando seguía tras {TASK_COMMAND_TIMEOUT // 60} min y se ha cortado")
        if code != 0:
            raise RuntimeError(f"el comando ha terminado con código {code}")
        MANAGER.log(sid, "\x1b[32mcomando programado terminado\x1b[0m")
        return "Comando terminado (código 0)"


SCHEDULER = Scheduler()


# ───────────────────────────── varios servidores ─────────────────────────────
# Cada servidor extra ejecuta su propio NovaHub («agente») con una puerta solo de API (NOVAHUB_REMOTE_LISTEN,
# p. ej. su IP de Tailscale) que únicamente acepta llaves de acceso. El panel principal guarda esas llaves y
# reenvía las peticiones: /api/remote/<servidor>/… → http://<agente>/api/…

TOKENS_FILE = os.path.join(DATA_DIR, "tokens.json")
SERVERS_FILE = os.path.join(DATA_DIR, "servers.json")


class ApiTokens:
    """Llaves de acceso para otro panel NovaHub. Solo se guarda su huella (SHA-256): la llave se ve una vez."""

    def __init__(self):
        self.items = read_json(TOKENS_FILE, {})   # huella -> {name, user, created, last_used}
        self.lock = threading.Lock()

    @staticmethod
    def _hash(raw):
        return hashlib.sha256(raw.encode()).hexdigest()

    def create(self, name, user):
        name = re.sub(r"[\x00-\x1f\x7f]", "", str(name or "")).strip()[:60]
        if not name:
            raise ApiError(400, "Ponle un nombre a la llave (p. ej. el panel que la usará)")
        if user not in AUTH.users:
            raise ApiError(400, "Ese usuario no existe")
        raw = "nh_" + secrets.token_urlsafe(32)
        with self.lock:
            self.items[self._hash(raw)] = {"name": name, "user": user, "created": time.time(), "last_used": None}
            write_json(TOKENS_FILE, self.items, mode=0o600)
        return raw

    def public(self):
        return [{"id": h[:12], "name": t["name"], "user": t["user"], "created": t["created"], "last_used": t.get("last_used")}
                for h, t in sorted(self.items.items(), key=lambda x: x[1]["created"])]

    def revoke(self, tid):
        with self.lock:
            match = [h for h in self.items if h.startswith(tid)]
            if len(match) != 1:
                raise ApiError(404, "Esa llave no existe")
            del self.items[match[0]]
            write_json(TOKENS_FILE, self.items, mode=0o600)

    def check(self, raw):
        """El usuario de la llave, o None. Una llave de un usuario borrado no vale."""
        t = self.items.get(self._hash(raw)) if raw.startswith("nh_") else None
        if not t or t["user"] not in AUTH.users:
            return None
        if time.time() - (t.get("last_used") or 0) > 300:  # se anota como mucho cada 5 min
            with self.lock:
                t["last_used"] = time.time()
                write_json(TOKENS_FILE, self.items, mode=0o600)
        return t["user"]


TOKENS = ApiTokens()
SERVER_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,31}")


class Remotes:
    """Los otros servidores que se ven desde este panel."""

    STATUS_TTL = 10

    def __init__(self):
        self.items = read_json(SERVERS_FILE, [])   # [{id, name, url, token}]
        self.lock = threading.Lock()
        self.cache = {}   # id -> (momento, estado)

    def get(self, rid):
        s = next((x for x in self.items if x["id"] == rid), None)
        if not s:
            raise ApiError(404, "Ese servidor no existe")
        return s

    @staticmethod
    def _split(url):
        u = urlparse(url)
        return u.scheme, u.hostname, u.port or (443 if u.scheme == "https" else 80)

    def connect(self, s, timeout=15):
        scheme, host, port = self._split(s["url"])
        cls = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
        return cls(host, port, timeout=timeout)

    def call(self, s, method, path, body=None, timeout=6):
        """Petición a la API de un agente y su respuesta JSON (lanza ApiError si no se puede)."""
        try:
            conn = self.connect(s, timeout)
            conn.request(method, path, body=json.dumps(body).encode() if body is not None else None,
                         headers={"Authorization": f"Bearer {s['token']}", "X-NovaHub": "1", "Content-Type": "application/json"})
            res = conn.getresponse()
            data = json.loads(res.read(5_000_000) or b"{}")
            conn.close()
        except (OSError, http.client.HTTPException, ValueError) as e:
            raise ApiError(502, f"No se puede conectar con «{s['name']}»: {e}")
        if res.status == 401:
            raise ApiError(502, f"«{s['name']}» no acepta la llave (¿la han revocado?)")
        if res.status >= 400:
            raise ApiError(502, f"«{s['name']}» responde: {data.get('error', res.status)}")
        return data

    def add(self, data):
        name = re.sub(r"[\x00-\x1f\x7f]", "", str(data.get("name") or "")).strip()[:40]
        url = str(data.get("url") or "").strip().rstrip("/")
        token = str(data.get("token") or "").strip()
        if not name:
            raise ApiError(400, "Ponle un nombre al servidor")
        if not re.fullmatch(r"https?://[A-Za-z0-9.\-\[\]:]+(:\d+)?", url):
            raise ApiError(400, "La dirección debe ser como http://100.64.0.2:8687 (sin rutas)")
        if not token.startswith("nh_"):
            raise ApiError(400, "La llave empieza por nh_: créala en el otro NovaHub, en Ajustes → Acceso remoto")
        rid = slugify(name)
        with self.lock:
            while any(x["id"] == rid for x in self.items):
                rid = f"{slugify(name)[:26]}-{secrets.token_hex(2)}"
        s = {"id": rid, "name": name, "url": url, "token": token}
        me = self.call(s, "GET", "/api/me")  # antes de guardar: que conecte y que la llave valga
        if (me.get("user") or {}).get("role") != "admin":
            raise ApiError(400, "La llave tiene que ser de un administrador del otro servidor")
        with self.lock:
            self.items.append(s)
            write_json(SERVERS_FILE, self.items, mode=0o600)
        return self.public()

    def delete(self, rid):
        with self.lock:
            self.get(rid)
            self.items = [x for x in self.items if x["id"] != rid]
            write_json(SERVERS_FILE, self.items, mode=0o600)
        self.cache.pop(rid, None)

    def status(self, s):
        hit = self.cache.get(s["id"])
        if hit and time.time() - hit[0] < self.STATUS_TTL:
            return hit[1]
        try:
            sysinfo = self.call(s, "GET", "/api/system", timeout=4)
            svcs = self.call(s, "GET", "/api/services", timeout=4)["services"]
            num = lambda v: v if isinstance(v, (int, float)) and not isinstance(v, bool) else 0  # noqa: E731 — datos de otro servidor
            st = {"online": True, "hostname": str(sysinfo.get("hostname") or "")[:64], "cpus": num(sysinfo.get("cpus")),
                  "mem_used": num(sysinfo.get("mem_used")), "mem_total": num(sysinfo.get("mem_total")), "uptime": num(sysinfo.get("uptime")),
                  "services": len(svcs), "running": sum(1 for x in svcs if x.get("status") == "running"),
                  "crashed": sum(1 for x in svcs if x.get("status") == "crashed")}
        except (ApiError, TypeError, AttributeError, KeyError) as e:
            e = e if isinstance(e, ApiError) else ApiError(502, "respuesta inesperada")
            st = {"online": False, "error": e.msg}
        self.cache[s["id"]] = (time.time(), st)
        return st

    def public(self, with_status=False):
        items = [{"id": s["id"], "name": s["name"], "url": s["url"]} for s in self.items]
        if with_status and items:
            results = {}
            threads = [threading.Thread(target=lambda s=s: results.__setitem__(s["id"], self.status(s)), daemon=True) for s in self.items]
            for t in threads:
                t.start()
            for t in threads:
                t.join(6)
            for it in items:
                it["status"] = results.get(it["id"], {"online": False, "error": "no responde"})
        return items


REMOTES = Remotes()


# ───────────────────────────── catálogo de apps ─────────────────────────────
# Apps autoalojadas ya configuradas (catalogo.json): instalar crea un servicio de tipo contenedor o compose con sus
# puertos, carpetas y claves generadas, y lo arranca. Las apps de varios contenedores descargan su compose oficial.

CATALOG_FILE = os.path.join(BASE_DIR, "catalogo.json")
APPS_DIR = os.path.expanduser(os.environ.get("NOVAHUB_APPS_DIR", "~/apps"))


def local_tz():
    try:
        return os.path.realpath("/etc/localtime").split("zoneinfo/")[1]
    except (IndexError, OSError):
        return "UTC"


class Catalog:
    def __init__(self):
        self.apps = {a["id"]: a for a in read_json(CATALOG_FILE, {}).get("apps", [])}
        self.accounts = {}  # sid → nº de cuentas (apps con registro controlado, p. ej. Vaultwarden)
        self.seen_open = {}  # sid → registro abierto en la última vuelta

    # ── registro de cuentas (apps con «signups» en el catálogo) ──
    def signup_cfg(self, svc):
        app = self.apps.get(svc.get("catalog") or "")
        return app.get("signups") if app and svc.get("kind") == "container" else None

    def signups_public(self, sid, svc):
        cfg = self.signup_cfg(svc)
        if not cfg:
            return None
        return {"open": (svc.get("env") or {}).get(cfg["env"]) == cfg["open"], "accounts": self.accounts.get(sid),
                "auto": svc.get("signups_auto", True)}

    def count_accounts(self, svc):
        import sqlite3
        db = os.path.join(service_root(svc), self.signup_cfg(svc)["db"])
        if not os.path.isfile(db):
            return None
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
        try:
            return int(con.execute(self.signup_cfg(svc)["count"]).fetchone()[0])
        except sqlite3.OperationalError:
            return None  # aún sin tablas (primer arranque)
        finally:
            con.close()

    def set_signups(self, sid, data):
        svc = MANAGER.services[sid]
        cfg = self.signup_cfg(svc)
        if not cfg:
            raise ApiError(400, "Este servicio no tiene registro de cuentas que controlar")
        want_open = bool(data.get("open"))
        try:
            count = self.count_accounts(svc)
        except Exception:  # noqa: BLE001
            count = None
        with MANAGER.lock:
            svc = MANAGER.services[sid]
            was_open = (svc.get("env") or {}).get(cfg["env"]) == cfg["open"]
            svc["env"] = {**(svc.get("env") or {}), cfg["env"]: cfg["open"] if want_open else cfg["closed"]}
            if "auto" in data:
                svc["signups_auto"] = bool(data["auto"])
            if want_open and not was_open:
                svc["signups_base"] = count or 0  # se vuelve a cerrar en cuanto haya una cuenta más que ahora
            svc["command"] = container_command(sid, svc)
            MANAGER.save_services()
        if want_open != was_open:
            MANAGER.log(sid, f"\x1b[35mregistro de cuentas {'abierto' if want_open else 'cerrado'}"
                             f"{': se reinicia para aplicarlo' if MANAGER.running(sid) else ''}\x1b[0m")
            if MANAGER.running(sid):
                MANAGER.restart(sid)
        return MANAGER.get_public(sid)

    def watch(self):
        """Cuenta las cuentas de las apps con registro controlado y, si el cierre automático está puesto, cierra
        el registro en cuanto aparece una cuenta nueva (la tuya): nadie más puede registrarse aunque esté en internet."""
        while True:
            for sid, svc in list(MANAGER.services.items()):
                if not self.signup_cfg(svc):
                    continue
                try:
                    count = self.count_accounts(svc)
                except Exception:  # noqa: BLE001
                    continue
                self.accounts[sid] = count
                st = self.signups_public(sid, svc)
                if st["open"] and self.seen_open.get(sid) is False:  # abierto a mano (Variables): cuenta desde ahora
                    with MANAGER.lock:
                        svc["signups_base"] = count or 0
                        MANAGER.save_services()
                self.seen_open[sid] = st["open"]
                if st["open"] and st["auto"] and count is not None and count > svc.get("signups_base", 0) \
                        and sid not in MANAGER.transition:
                    MANAGER.log(sid, f"\x1b[32mya hay {count} cuenta{'s' if count != 1 else ''}: se cierra el registro "
                                     "para que nadie más pueda crear una\x1b[0m")
                    try:
                        self.set_signups(sid, {"open": False})
                    except Exception:  # noqa: BLE001
                        traceback.print_exc()
            time.sleep(15)

    def public(self):
        installed = {}
        for sid, s in MANAGER.services.items():
            if s.get("catalog"):
                installed.setdefault(s["catalog"], []).append(sid)
        keys = ("id", "name", "category", "replaces", "desc", "ram", "port", "fields", "https", "subdomain")
        return {"apps": [{**{k: a.get(k) for k in keys}, "kind": "compose" if a.get("compose") else "container",
                          "installed": installed.get(a["id"], [])} for a in self.apps.values()],
                "podman": bool(shutil.which("podman")), "compose": bool(shutil.which("podman-compose")),
                "apps_dir": APPS_DIR, "domain": PUBLISHER.domain if PUBLISHER.enabled else None}

    @staticmethod
    def free_port(want):
        used = {s.get("port") for s in MANAGER.services.values()} | listening_ports()
        used |= {gateway_port(p) for p in used if p}
        port = want
        while port in used and port < want + 100:
            port += 1
        return port

    def install(self, data):
        app = self.apps.get(str(data.get("app") or ""))
        if not app:
            raise ApiError(404, "Esa app no está en el catálogo")
        if not shutil.which("podman") or (app.get("compose") and not shutil.which("podman-compose")):
            raise ApiError(400, "Hace falta Podman: sudo apt install podman podman-compose passt uidmap")
        name = re.sub(r"[\x00-\x1f\x7f]", "", str(data.get("name") or app["name"])).strip()[:60] or app["name"]
        cwd = os.path.expanduser(str(data.get("cwd") or "").strip() or os.path.join(APPS_DIR, app["id"]))
        if os.path.isdir(cwd) and os.listdir(cwd) and not data.get("reuse"):
            raise ApiError(409, f"La carpeta {cwd} ya tiene archivos: elige otra (o es la de una instalación anterior)")
        try:
            port = int(data.get("port") or self.free_port(app["port"]))
        except (TypeError, ValueError):
            raise ApiError(400, "El puerto debe ser un número")
        sub = str(data.get("subdomain") or "").strip().lower()
        url = f"https://{sub}.{PUBLISHER.domain}" if sub and PUBLISHER.enabled else f"http://{lan_ip() or '127.0.0.1'}:{port}"
        secrets_named = {}

        def fill(text):
            def rep(m):
                key = m.group(1)
                if key == "secret":
                    return secrets.token_urlsafe(24)
                if key == "secret_alnum":
                    return secrets.token_hex(16)
                if key.startswith("secret:"):
                    return secrets_named.setdefault(key, secrets.token_urlsafe(12))
                return {"url": url, "host": urlparse(url).hostname or "", "uid": str(os.getuid()), "gid": str(os.getgid()),
                        "tz": local_tz()}.get(key, m.group(0))
            return re.sub(r"\{(secret(?::\w+)?|secret_alnum|url|host|uid|gid|tz)\}", rep, str(text))

        volumes = [fill(v) for v in app.get("volumes", [])]
        for f in app.get("fields", []):
            val = str((data.get("fields") or {}).get(f["key"]) or "").strip()
            if val:
                val = os.path.expanduser(val)
                if not os.path.isdir(val):
                    raise ApiError(400, f"No existe la carpeta «{val}» ({f['label']})")
                volumes.append(f["volume"].replace("{value}", val))
        os.makedirs(cwd, mode=0o755, exist_ok=True)
        body = {"name": name, "description": app["desc"], "tags": [app["category"]], "cwd": cwd, "port": port,
                "autostart": True, "restart_on_crash": True, "health_check": app.get("health", "auto"),
                "stop_timeout": app.get("stop_timeout", 20)}
        if app.get("compose"):
            c = app["compose"]
            import urllib.request
            for fname, src in c["files"].items():
                try:
                    with urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": "NovaHub"}), timeout=60) as r:
                        content = r.read(2_000_000).decode("utf-8")
                except Exception as e:  # noqa: BLE001
                    raise ApiError(502, f"No se pudo descargar {fname} de {app['name']}: {e}")
                if fname == c.get("env_file"):
                    lines = content.splitlines()
                    for key, val in c.get("env_set", {}).items():
                        val = fill(val)
                        hit = [i for i, l in enumerate(lines) if re.match(rf"\s*#?\s*{re.escape(key)}=", l)]
                        if hit:
                            lines[hit[0]] = f"{key}={val}"
                        else:
                            lines.append(f"{key}={val}")
                    content = "\n".join(lines) + "\n"
                fd = os.open(os.path.join(cwd, fname), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600 if fname == c.get("env_file") else 0o644)
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(content)
            body.update(kind="compose", compose_file="docker-compose.yml" if "docker-compose.yml" in c["files"] else "")
        else:
            body.update(kind="container", image=app["image"], cport=app.get("cport"), volumes="\n".join(volumes),
                        env={k: fill(v) for k, v in app.get("env", {}).items()}, cargs=fill(app.get("cargs", "")), ccmd=app.get("ccmd", ""))
        if sub:
            body["subdomain"] = sub
        extra, notice = PUBLISHER.apply(None, None, normalize_service(body), body)
        extra.update(catalog=app["id"], notes=fill(app.get("notes", "")))
        if app.get("backup"):  # copias diarias desde el primer día (p. ej. las contraseñas de Vaultwarden)
            extra["backup"] = {**BACKUP_DEFAULTS, **app["backup"]}
        if app.get("signups"):
            extra.update(signups_auto=True, signups_base=0)
        sid = MANAGER.create(body, extra)
        if app.get("backup"):
            with MANAGER.lock:  # la primera copia, a la hora programada (no ahora, con la app aún vacía)
                MANAGER.st(sid)["backup"] = {"last_auto": time.time()}
                MANAGER.save_state()
        MANAGER.log(sid, f"\x1b[35minstalado desde el catálogo: {app['name']}\x1b[0m")
        if data.get("start", True):
            try:
                MANAGER.start(sid)
            except ApiError as e:
                MANAGER.log(sid, f"\x1b[31mno se pudo arrancar: {e.msg}\x1b[0m")
        return {**MANAGER.get_public(sid), "notice": notice}


CATALOG = Catalog()


def ntfy_setup(sid):
    """Protege el ntfy instalado desde el catálogo y lo conecta a los avisos de NovaHub:
    usuarios activados y todo denegado por defecto; «movil» solo puede leer el tema y NovaHub solo escribir en él
    (con una llave). NovaHub publica por dentro del servidor (127.0.0.1): no depende del túnel."""
    svc = MANAGER.services.get(sid)
    if not svc or svc.get("catalog") != "ntfy" or svc.get("kind") != "container":
        raise ApiError(400, "Ese servicio no es un ntfy instalado desde el catálogo")
    topic = "novahub"
    env_add = {"NTFY_AUTH_FILE": "/var/cache/ntfy/user.db", "NTFY_AUTH_DEFAULT_ACCESS": "deny-all", "NTFY_ENABLE_LOGIN": "true"}
    with MANAGER.lock:
        svc = MANAGER.services[sid]
        changed = any((svc.get("env") or {}).get(k) != v for k, v in env_add.items())
        svc["env"] = {**(svc.get("env") or {}), **env_add}
        svc["command"] = container_command(sid, svc)
        MANAGER.save_services()
    old_pid = (MANAGER.state.get(sid) or {}).get("pid") if MANAGER.running(sid) else None
    if changed or not old_pid:
        MANAGER.log(sid, "\x1b[35mactivando los usuarios de ntfy (todo denegado por defecto) y reiniciando…\x1b[0m")
        if old_pid:
            MANAGER.restart(sid)  # en segundo plano: hay que esperar al proceso nuevo, no fiarse del viejo
        else:
            MANAGER.start(sid)
    else:
        old_pid = None
    import urllib.request
    end = time.time() + 150
    while True:  # esperar al contenedor nuevo (otro proceso) y a que responda
        time.sleep(2)
        if time.time() > end:
            raise ApiError(504, "ntfy no ha vuelto a arrancar: mira su consola")
        pid = (MANAGER.state.get(sid) or {}).get("pid")
        if sid in MANAGER.transition or not MANAGER.running(sid) or (old_pid and pid == old_pid):
            continue
        if subprocess.run(["podman", "container", "exists", container_name(sid)], capture_output=True, timeout=15).returncode != 0:
            continue
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{svc['port']}/v1/health", timeout=5) as r:
                if json.loads(r.read()).get("healthy"):
                    break
        except Exception:  # noqa: BLE001
            pass

    def ntfy(*args, password=None):
        cmd = ["podman", "exec", *(["-e", f"NTFY_PASSWORD={password}"] if password else []), container_name(sid), "ntfy", *args]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    phone_pass = secrets.token_urlsafe(12)
    res = ntfy("user", "add", "--role=user", "movil", password=phone_pass)
    if res.returncode != 0:  # ya existía: se le pone la contraseña nueva
        res = ntfy("user", "change-pass", "movil", password=phone_pass)
        if res.returncode != 0:
            raise ApiError(500, f"No se pudo crear el usuario del móvil: {(res.stderr or res.stdout).strip()}")
    ntfy("user", "add", "--role=user", "novahub", password=secrets.token_urlsafe(24))
    for user, perm in (("movil", "read-only"), ("novahub", "write-only")):
        res = ntfy("access", user, topic, perm)
        if res.returncode != 0:
            raise ApiError(500, f"No se pudieron dar los permisos en ntfy: {(res.stderr or res.stdout).strip()}")
    res = ntfy("token", "add", "novahub")
    m = re.search(r"tk_[A-Za-z0-9]+", res.stdout + res.stderr)
    if not m:
        raise ApiError(500, f"No se pudo crear la llave de NovaHub en ntfy: {(res.stderr or res.stdout).strip()}")
    cfg = NOTIFIER.config()
    old = cfg.get("ntfy") or {}
    public = (svc.get("env") or {}).get("NTFY_BASE_URL") or f"http://{lan_ip()}:{svc['port']}"
    cfg["ntfy"] = {**old, "url": f"http://127.0.0.1:{svc['port']}", "public_url": public, "topic": topic, "token": m.group(0),
                   "enabled": True, "service": sid, "phone_user": "movil"}
    write_json(NOTIFY_FILE, cfg)
    MANAGER.log(sid, "ntfy protegido: el usuario «movil» puede leer el tema «novahub» y NovaHub publicar en él")
    return {**NOTIFIER.public(), "phone_password": phone_pass}


# ───────────────────────────── copias fuera de casa ─────────────────────────────
# Las copias locales (novahub-copias) y la configuración de NovaHub (data/) van cifradas con restic a un disco USB o a
# otro servidor tuyo por SSH (p. ej. por Tailscale). Sin servicios de terceros ni suscripciones. Copia diaria con
# retención, y una vez al mes se comprueba el repositorio y se restaura de verdad un archivo de prueba.

OFFSITE_FILE = os.path.join(DATA_DIR, "offsite.json")
OFFSITE_LOG = os.path.join(LOG_DIR, "_fuera-de-casa.log")
SSH_DIR = os.path.join(DATA_DIR, "ssh")
SSH_KEY = os.path.join(SSH_DIR, "id_ed25519")
RESTORE_DIR = os.path.expanduser(os.environ.get("NOVAHUB_RESTORE_DIR", "~/novahub-recuperado"))
OFFSITE_DEFAULTS = {"enabled": True, "hour": 5, "keep_daily": 7, "keep_weekly": 4, "keep_monthly": 6, "verify_days": 30}
OFFSITE_EXCLUDE = ("logs", "metrics.json", "update-backups", "builds", "app", "running.json", "update-result.json")


def restic_bin():
    return os.environ.get("NOVAHUB_RESTIC") or shutil.which("restic")


class Offsite:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = read_json(OFFSITE_FILE, {})
        self.data.setdefault("destinations", [])
        self.job = None

    def save(self):
        with self.lock:
            write_json(OFFSITE_FILE, self.data, mode=0o600)

    def config(self):
        return {**OFFSITE_DEFAULTS, **self.data.get("config", {})}

    def dest(self, did):
        d = next((x for x in self.data["destinations"] if x["id"] == did), None)
        if not d:
            raise ApiError(404, "Ese destino no existe")
        return d

    # ── restic ──
    @staticmethod
    def _log(msg):
        with open(OFFSITE_LOG, "ab") as f:
            f.write(f"[{datetime.now():%d/%m %H:%M:%S}] {msg}\n".encode())

    @staticmethod
    def repo(d):
        if d["type"] == "local":
            return d["path"]
        return f"sftp:{d['user']}@{d['host']}:{d['rpath']}"

    @staticmethod
    def _env(d):
        return {**os.environ, "RESTIC_PASSWORD": d["password"], "RESTIC_PROGRESS_FPS": "0.2"}

    def _args(self, d):
        if d["type"] != "sftp":
            return []
        ssh = (f"ssh -p {int(d.get('port') or 22)} -i {shlex.quote(SSH_KEY)} -o BatchMode=yes -o ConnectTimeout=20 "
               f"-o StrictHostKeyChecking=accept-new -o UserKnownHostsFile={shlex.quote(os.path.join(SSH_DIR, 'known_hosts'))} "
               f"{d['user']}@{d['host']} -s sftp")
        return ["-o", f"sftp.command={ssh}"]

    def restic(self, d, *args, timeout=6 * 3600, log=True, capture=False):
        rb = restic_bin()
        if not rb:
            raise ApiError(400, "restic no está instalado: sudo apt install restic")
        cmd = [rb, "-r", self.repo(d), *self._args(d), *args]
        if capture:
            res = subprocess.run(cmd, env=self._env(d), capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        else:
            with open(OFFSITE_LOG, "ab") as f:
                if log:
                    f.write(f"$ restic {' '.join(args)}\n".encode())
                    f.flush()
                res = subprocess.run(cmd, env=self._env(d), stdout=f, stderr=subprocess.STDOUT, timeout=timeout, stdin=subprocess.DEVNULL)
        if res.returncode not in (0, 3):  # 3 = copia hecha pero algún archivo no se pudo leer
            err = (res.stderr or "").strip().splitlines()[-1:] if capture else []
            raise RuntimeError(f"restic {args[0]} ha fallado (código {res.returncode}){': ' + err[0] if err else ''}")
        return res

    def available(self, d):
        """(sí/no, motivo): un disco USB desconectado no es un error, se espera a la próxima vez."""
        if d["type"] == "local":
            if not os.path.isdir(d["path"]):
                return False, "el disco no está conectado (o la carpeta no existe)"
            return True, ""
        return True, ""

    # ── destinos ──
    def ssh_key(self, create=False):
        if not os.path.isfile(SSH_KEY + ".pub"):
            if not create:
                return None
            os.makedirs(SSH_DIR, mode=0o700, exist_ok=True)
            res = subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", f"novahub@{socket.gethostname()}", "-f", SSH_KEY],
                                 capture_output=True, text=True, timeout=30)
            if res.returncode != 0:
                raise ApiError(500, f"No se pudo crear la llave SSH: {res.stderr.strip()}")
        with open(SSH_KEY + ".pub") as f:
            return f.read().strip()

    def add(self, data):
        name = re.sub(r"[\x00-\x1f\x7f]", "", str(data.get("name") or "")).strip()[:40]
        kind = data.get("type")
        if not name:
            raise ApiError(400, "Ponle un nombre al destino (p. ej. «Disco USB» o «Casa de mis padres»)")
        d = {"id": slugify(name), "name": name, "type": kind, "created": time.time()}
        while any(x["id"] == d["id"] for x in self.data["destinations"]):
            d["id"] = f"{slugify(name)[:26]}-{secrets.token_hex(2)}"
        if kind == "local":
            path = os.path.realpath(os.path.expanduser(str(data.get("path") or "").strip()))
            if not str(data.get("path") or "").strip() or path == "/":
                raise ApiError(400, "Indica la carpeta del disco, p. ej. /media/usb/novahub")
            for own in (DATA_DIR, SNAPSHOT_DIR):
                o = os.path.realpath(own)
                if path == o or path.startswith(o + os.sep):
                    raise ApiError(400, "El destino no puede estar dentro de lo que se copia (data/ o novahub-copias)")
            if not os.path.isdir(os.path.dirname(path)):
                raise ApiError(400, "No existe esa carpeta: conecta el disco y comprueba la ruta")
            os.makedirs(path, mode=0o700, exist_ok=True)
            d["path"] = path
            # en el mismo disco que el sistema o que las copias locales no protege si falla ese disco
            d["same_disk"] = os.stat(path).st_dev in {os.stat(p).st_dev for p in ("/", DATA_DIR, SNAPSHOT_DIR) if os.path.exists(p)}
        elif kind == "sftp":
            user, host, rpath = (str(data.get(k) or "").strip() for k in ("user", "host", "rpath"))
            if not re.fullmatch(r"[a-z_][a-z0-9_.-]{0,31}", user):
                raise ApiError(400, "Usuario SSH no válido")
            if not re.fullmatch(r"[A-Za-z0-9.-]{1,253}|\[?[0-9a-fA-F:]+\]?", host):
                raise ApiError(400, "Servidor no válido (nombre o IP, p. ej. 100.64.0.5)")
            if not re.fullmatch(r"[A-Za-z0-9_./~-]{1,200}", rpath) or ".." in rpath:
                raise ApiError(400, "Carpeta remota no válida (p. ej. /srv/copias/novahub)")
            try:
                port = int(data.get("port") or 22)
            except (TypeError, ValueError):
                raise ApiError(400, "Puerto no válido")
            if not 1 <= port <= 65535:
                raise ApiError(400, "Puerto no válido")
            self.ssh_key(create=True)
            d.update(user=user, host=host, rpath=rpath, port=port)
        else:
            raise ApiError(400, "Tipo de destino desconocido")
        generated = not data.get("password")
        password = str(data.get("password") or "") or secrets.token_urlsafe(24)
        if len(password) < 12:
            raise ApiError(400, "La contraseña de cifrado debe tener al menos 12 caracteres")
        d["password"] = password
        # si ya hay un repositorio de restic ahí (otra instalación, o este mismo de antes) se usa; si no, se crea
        try:
            self.restic(d, "cat", "config", timeout=120, capture=True)
            self._log(f"«{name}»: repositorio existente, se usa")
        except (RuntimeError, subprocess.TimeoutExpired):
            try:
                res = self.restic(d, "init", timeout=300, capture=True)
            except subprocess.TimeoutExpired:
                raise ApiError(504, "El destino no responde")
            except RuntimeError as e:
                raise ApiError(400, f"No se pudo preparar el destino: {e}" + (" (¿has añadido la llave SSH de NovaHub en el otro servidor?)" if kind == "sftp" else ""))
            self._log(f"«{name}»: repositorio cifrado creado en {self.repo(d)} {res.stdout.strip()[:0]}")
        with self.lock:
            self.data["destinations"].append(d)
            write_json(OFFSITE_FILE, self.data, mode=0o600)
        return {**self.public(), "password": password if generated else None, "dest": d["id"]}

    def delete(self, did):
        self.dest(did)
        with self.lock:
            self.data["destinations"] = [x for x in self.data["destinations"] if x["id"] != did]
            write_json(OFFSITE_FILE, self.data, mode=0o600)
        return self.public()

    def save_config(self, data):
        cfg = self.config()
        try:
            new = {"enabled": bool(data.get("enabled", cfg["enabled"])), "hour": int(data.get("hour", cfg["hour"])),
                   "keep_daily": int(data.get("keep_daily", cfg["keep_daily"])), "keep_weekly": int(data.get("keep_weekly", cfg["keep_weekly"])),
                   "keep_monthly": int(data.get("keep_monthly", cfg["keep_monthly"])), "verify_days": cfg["verify_days"]}
        except (TypeError, ValueError):
            raise ApiError(400, "Los números no son válidos")
        if not 0 <= new["hour"] <= 23 or not all(0 <= new[k] <= 400 for k in ("keep_daily", "keep_weekly", "keep_monthly")) \
                or not (new["keep_daily"] or new["keep_weekly"] or new["keep_monthly"]):
            raise ApiError(400, "Hora entre 0 y 23 y al menos una copia que conservar")
        self.data["config"] = new
        self.save()
        return self.public()

    def public(self):
        log_tail = ""
        try:
            with open(OFFSITE_LOG, "rb") as f:
                f.seek(max(0, os.path.getsize(OFFSITE_LOG) - 6000))
                log_tail = f.read().decode("utf-8", "replace")
        except OSError:
            pass
        rb = restic_bin()
        version = None
        if rb:
            try:
                version = subprocess.run([rb, "version"], capture_output=True, text=True, timeout=10).stdout.split()[1]
            except (OSError, IndexError, subprocess.TimeoutExpired):
                version = "?"
        dests = []
        for d in self.data["destinations"]:
            ok, why = self.available(d)
            dests.append({k: d.get(k) for k in ("id", "name", "type", "path", "user", "host", "port", "rpath", "created",
                                                 "last_backup", "last_check", "same_disk")} | {"repo": self.repo(d), "available": ok, "why": why})
        return {"restic": version, "pubkey": self.ssh_key(), "config": self.config(), "destinations": dests,
                "job": self.job, "log": log_tail, "restore_dir": RESTORE_DIR,
                "sources": self.sources()}

    @staticmethod
    def sources():
        paths = [os.path.realpath(DATA_DIR)]
        snap = os.path.realpath(SNAPSHOT_DIR)
        if os.path.isdir(snap) and not snap.startswith(paths[0] + os.sep):
            paths.append(snap)
        return paths

    # ── trabajos ──
    def _job(self, label, fn):
        with self.lock:
            if self.job:
                raise ApiError(409, f"Ya hay un trabajo en curso ({self.job})")
            self.job = label

        def go():
            try:
                fn()
            except Exception as e:  # noqa: BLE001
                msg = e.msg if isinstance(e, ApiError) else str(e)
                self._log(f"✗ {msg}")
                NOTIFIER.notify("backup", None, f"Ha fallado la copia fuera de casa ({label})", f"{label}: {msg}", key=f"offsite-{label}", level="danger")
            finally:
                self.job = None
        threading.Thread(target=go, name="fuera-de-casa", daemon=True).start()
        return self.public()

    def run(self, did, verify=False):
        d = self.dest(did)
        return self._job(f"Copia a «{d['name']}»", lambda: self._backup(d, verify))

    def check(self, did):
        d = self.dest(did)
        return self._job(f"Comprobación de «{d['name']}»", lambda: self._verify(d))

    def _record(self, d, key, ok, msg, **extra):
        with self.lock:
            d[key] = {"at": time.time(), "ok": ok, "msg": msg, **extra}
            write_json(OFFSITE_FILE, self.data, mode=0o600)

    def _backup(self, d, verify=False):
        ok, why = self.available(d)
        if not ok:
            self._log(f"«{d['name']}»: {why}; se intentará en la próxima copia")
            self._record(d, "last_backup", None, why.capitalize() + ": se intentará en la próxima copia")  # no es un fallo
            return
        cfg = self.config()
        self._log(f"Copia cifrada a «{d['name']}» ({self.repo(d)})…")
        t0 = time.time()
        excludes = [a for x in OFFSITE_EXCLUDE for a in ("--exclude", os.path.join(os.path.realpath(DATA_DIR), x))]
        try:
            res = self.restic(d, "backup", "--tag", "novahub", "--host", socket.gethostname(), "--json", *excludes, *self.sources(), capture=True)
            summary = next((json.loads(l) for l in res.stdout.splitlines()[::-1] if '"message_type":"summary"' in l.replace(" ", "")), {})
            self.restic(d, "forget", "--tag", "novahub", "--prune", "--keep-daily", str(cfg["keep_daily"]),
                        "--keep-weekly", str(cfg["keep_weekly"]), "--keep-monthly", str(cfg["keep_monthly"]))
        except Exception as e:  # noqa: BLE001
            self._record(d, "last_backup", False, str(e))
            raise
        added = summary.get("data_added", 0)
        msg = (f"Copia {summary.get('snapshot_id', '')[:8]}: {summary.get('files_new', 0)} archivos nuevos, "
               f"{summary.get('files_changed', 0)} cambiados, {added / 2**20:.1f} MB enviados en {time.time() - t0:.0f} s")
        self._log(f"✓ «{d['name']}»: {msg}")
        self._record(d, "last_backup", True, msg, size=summary.get("total_bytes_processed"), added=added)
        last = (d.get("last_check") or {}).get("at") or 0
        if verify or time.time() - last > cfg["verify_days"] * 86400:
            self._verify(d)

    def _verify(self, d):
        """Comprueba el repositorio (una parte de los datos, al azar) y restaura de verdad un archivo de prueba."""
        ok, why = self.available(d)
        if not ok:
            self._record(d, "last_check", False, why.capitalize())
            return
        self._log(f"Comprobando «{d['name']}»: integridad y prueba de restauración…")
        try:
            self.restic(d, "check", "--read-data-subset=5%")
            probe = os.path.join(os.path.realpath(DATA_DIR), "services.json")
            tmp = tempfile.mkdtemp(prefix="novahub-prueba-")
            try:
                self.restic(d, "restore", "latest", "--tag", "novahub", "--target", tmp, "--include", probe)
                got = os.path.join(tmp, probe.lstrip("/"))
                with open(got, encoding="utf-8") as f:
                    restored = json.load(f)
                if not isinstance(restored, list):
                    raise RuntimeError("el archivo restaurado no es el esperado")
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
        except Exception as e:  # noqa: BLE001
            self._record(d, "last_check", False, f"Falla la comprobación: {e}")
            raise
        msg = f"Repositorio correcto y restauración de prueba bien ({len(restored)} servicios en la copia)"
        self._log(f"✓ «{d['name']}»: {msg}")
        self._record(d, "last_check", True, msg)

    def snapshots(self, did):
        d = self.dest(did)
        ok, why = self.available(d)
        if not ok:
            raise ApiError(400, why.capitalize())
        try:
            res = self.restic(d, "snapshots", "--tag", "novahub", "--json", timeout=120, capture=True)
            items = json.loads(res.stdout or "[]")
        except (RuntimeError, ValueError, subprocess.TimeoutExpired) as e:
            raise ApiError(502, f"No se pudieron leer las copias: {e}")
        out = [{"id": s.get("short_id") or s.get("id", "")[:8], "time": s.get("time"), "host": s.get("hostname"),
                "size": (s.get("summary") or {}).get("total_bytes_processed"),
                "files": (s.get("summary") or {}).get("total_files_processed")} for s in items]
        return {"snapshots": sorted(out, key=lambda s: s["time"] or "", reverse=True)}

    def restore(self, did, snap):
        d = self.dest(did)
        if not re.fullmatch(r"[0-9a-f]{8,64}|latest", str(snap or "")):
            raise ApiError(400, "Copia no válida")
        target = os.path.join(RESTORE_DIR, f"{datetime.now():%Y%m%d-%H%M%S}-{snap[:8]}")

        def fn():
            os.makedirs(target, mode=0o700, exist_ok=True)
            self._log(f"Recuperando la copia {snap} de «{d['name']}» en {target} (no se toca nada de lo actual)…")
            self.restic(d, "restore", snap, "--target", target)
            self._log(f"✓ Recuperada en {target}. Dentro están data/ (configuración de NovaHub) y las copias locales de cada servicio.")
        return {**self._job(f"Recuperar de «{d['name']}»", fn), "target": target}

    def loop(self):
        while True:
            time.sleep(60)
            SUPERVISOR.beat("fuera-de-casa")
            try:
                cfg, now = self.config(), datetime.now()
                if not cfg["enabled"] or now.hour != cfg["hour"] or self.job:
                    continue
                today = now.strftime("%Y-%m-%d")
                for d in list(self.data["destinations"]):
                    if self.data.get("ran", {}).get(d["id"]) == today:
                        continue
                    self.data.setdefault("ran", {})[d["id"]] = today
                    self.save()
                    self.job = f"Copia a «{d['name']}»"
                    try:
                        self._backup(d)
                    except Exception as e:  # noqa: BLE001
                        NOTIFIER.notify("backup", None, f"Ha fallado la copia fuera de casa a «{d['name']}»", str(e), key=f"offsite-{d['id']}", level="danger")
                    finally:
                        self.job = None
            except Exception:  # noqa: BLE001
                traceback.print_exc()


OFFSITE = Offsite()


# ───────────────────────────── centro de actualizaciones ─────────────────────────────
# NovaHub (versiones de GitHub o canal de desarrollo), el sistema (apt), el reinicio pendiente, las imágenes de los
# contenedores, los servicios con git y las dependencias de cada proyecto. Se comprueba solo cada pocas horas;
# aplicar cada cosa es un botón. Lo que necesita root pasa por un único script (tools/novahub-sistema) con sudo.

UPDATES_FILE = os.path.join(DATA_DIR, "updates.json")
UPDATE_LOG = os.path.join(LOG_DIR, "_actualizaciones.log")
UPDATE_RESULT = os.path.join(DATA_DIR, "update-result.json")   # lo escribe updater.py al acabar
RUNNING_FILE = os.path.join(DATA_DIR, "running.json")          # versión y commit con los que arrancó este proceso
SYSTEM_SCRIPT = "/usr/local/sbin/novahub-sistema"
UPDATE_REPO = os.environ.get("NOVAHUB_UPDATE_REPO", "").strip()  # «usuario/repo» si no se puede deducir del git
UPDATES_DEFAULTS = {"channel": "stable", "auto_security": False, "auto_hour": 4, "notify": True}
UPDATE_CHECK_EVERY = 6 * 3600
SEMVER = re.compile(r"v?(\d+)\.(\d+)(?:\.(\d+))?")


def semver(text):
    m = SEMVER.match(str(text or "").strip())
    return tuple(int(x or 0) for x in m.groups()) if m else (0, 0, 0)


def current_commit():
    res = git(BASE_DIR, "rev-parse", "HEAD") if os.path.isdir(os.path.join(BASE_DIR, ".git")) else None
    return res.stdout.strip() if res is not None and res.returncode == 0 else None


class Updates:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = read_json(UPDATES_FILE, {})
        self.data.setdefault("config", {})
        self.data.setdefault("history", [])
        self.job = None   # lo que se está aplicando ahora mismo («sistema», «novahub»…)
        self.checking = False

    # ── estado ──
    def config(self):
        return {**UPDATES_DEFAULTS, **self.data.get("config", {})}

    def save(self):
        with self.lock:
            write_json(UPDATES_FILE, self.data)

    def save_config(self, data):
        cfg = self.config()
        channel = data.get("channel", cfg["channel"])
        if channel not in ("stable", "dev"):
            raise ApiError(400, "Canal desconocido")
        try:
            hour = int(data.get("auto_hour", cfg["auto_hour"]))
        except (TypeError, ValueError):
            raise ApiError(400, "Hora no válida")
        if not 0 <= hour <= 23:
            raise ApiError(400, "La hora debe estar entre 0 y 23")
        self.data["config"] = {"channel": channel, "auto_security": bool(data.get("auto_security", cfg["auto_security"])),
                               "auto_hour": hour, "notify": bool(data.get("notify", cfg["notify"]))}
        self.save()
        if channel != cfg["channel"]:
            self.start_check()
        return self.public()

    def history(self, what, ok, msg):
        self.data["history"] = ([{"at": time.time(), "what": what, "ok": ok, "msg": msg}] + self.data["history"])[:50]
        self.save()

    @staticmethod
    def sudo_ok():
        if not os.path.isfile(SYSTEM_SCRIPT):
            return False
        try:
            return subprocess.run(["sudo", "-n", "-l", SYSTEM_SCRIPT, "upgrade"], capture_output=True, timeout=10).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    def public(self):
        self._collect_result()
        d = self.data
        log_tail = ""
        try:
            with open(UPDATE_LOG, "rb") as f:
                f.seek(max(0, os.path.getsize(UPDATE_LOG) - 6000))
                log_tail = strip_ansi(f.read().decode("utf-8", "replace"))
        except OSError:
            pass
        apt = d.get("apt") or {}
        counts = {
            "novahub": 1 if (d.get("novahub") or {}).get("available") else 0,
            "system": len(apt.get("packages") or []),
            "security": sum(1 for p in apt.get("packages") or [] if p.get("security")),
            "services": sum(1 for s in (d.get("services") or {}).values() if s.get("available")),
            "deps": sum(1 for s in (d.get("deps") or {}).values() if s.get("count")),
        }
        return {"version": VERSION, "commit": (current_commit() or "")[:7], "config": self.config(),
                "last_check": d.get("last_check"), "checking": self.checking, "job": self.job,
                "novahub": d.get("novahub"), "apt": apt, "reboot": self.reboot_info(), "sudo": self.sudo_ok(),
                "services": d.get("services") or {}, "deps": d.get("deps") or {}, "history": d["history"][:15],
                "counts": counts, "total": counts["novahub"] + counts["system"] + counts["services"] + counts["deps"],
                "log": log_tail}

    @staticmethod
    def reboot_info():
        if not os.path.exists("/var/run/reboot-required"):
            return None
        try:
            with open("/var/run/reboot-required.pkgs") as f:
                pkgs = sorted({l.strip() for l in f if l.strip()})
        except OSError:
            pkgs = []
        return {"since": os.path.getmtime("/var/run/reboot-required"), "packages": pkgs}

    def _collect_result(self):
        """Resultado de una actualización de NovaHub (lo deja updater.py; este proceso puede ser ya el nuevo)."""
        if not os.path.isfile(UPDATE_RESULT):
            return
        r = read_json(UPDATE_RESULT, None)
        try:
            os.remove(UPDATE_RESULT)
        except OSError:
            pass
        if r:
            self.history("NovaHub", r.get("ok"), r.get("msg", ""))
            if r.get("ok"):
                self.data["novahub"] = {**(self.data.get("novahub") or {}), "available": False}
                self.save()
            NOTIFIER.notify("updates", None, "NovaHub actualizado" if r.get("ok") else "La actualización de NovaHub ha fallado",
                            r.get("msg", ""), key="novahub-update", level="ok" if r.get("ok") else "danger")

    # ── comprobar ──
    def start_check(self):
        with self.lock:
            if self.checking:
                return
            self.checking = True
        threading.Thread(target=self.check_all, name="comprobar-actualizaciones", daemon=True).start()

    def check_all(self, pull_images=False):
        try:
            before = self.public()["total"]
            for name, fn in (("novahub", self.check_novahub), ("apt", self.check_apt),
                             ("services", lambda: self.check_services(pull_images)), ("deps", self.check_deps)):
                try:
                    self.data[name] = fn()
                except Exception as e:  # noqa: BLE001
                    self.data[name] = {"error": str(e)[:300]}
            self.data["last_check"] = time.time()
            self.save()
            p = self.public()
            if self.config()["notify"] and p["total"] > before:
                c = p["counts"]
                parts = [f"NovaHub {self.data['novahub'].get('latest')}" if c["novahub"] else "",
                         f"{c['system']} paquete(s) del sistema" + (f" ({c['security']} de seguridad)" if c["security"] else "") if c["system"] else "",
                         f"{c['services']} servicio(s)" if c["services"] else "", f"{c['deps']} proyecto(s) con dependencias nuevas" if c["deps"] else ""]
                NOTIFIER.notify("updates", None, "Hay actualizaciones disponibles",
                                "Hay actualizaciones en el servidor: " + ", ".join(x for x in parts if x)
                                + ". Revísalas en Ajustes → Actualizaciones.", key="disponibles", level="info")
        finally:
            self.checking = False

    def github_repo(self):
        if UPDATE_REPO:
            return UPDATE_REPO
        res = git(BASE_DIR, "remote", "get-url", "origin")
        m = re.search(r"github\.com[:/]([\w.-]+/[\w.-]+?)(?:\.git)?$", res.stdout.strip()) if res.returncode == 0 else None
        return m.group(1) if m else None

    def check_novahub(self):
        commit = current_commit()
        if not commit:
            return {"error": "NovaHub no está instalado con git: actualízalo a mano (o clónalo con git para tener actualizaciones)."}
        out = {"commit": commit[:7], "channel": self.config()["channel"], "available": False,
               "dirty": bool(git(BASE_DIR, "status", "--porcelain", "--untracked-files=no").stdout.strip()),
               "systemd": bool(os.environ.get("NOTIFY_SOCKET"))}
        if out["channel"] == "dev":
            branch = git(BASE_DIR, "symbolic-ref", "--short", "-q", "HEAD").stdout.strip() or "main"
            res = git(BASE_DIR, "fetch", "-q", "origin", branch, timeout=60)
            if res.returncode != 0:
                raise RuntimeError(git_output(res) or "no se pudo consultar GitHub")
            target = git(BASE_DIR, "rev-parse", f"origin/{branch}").stdout.strip()
            behind = git(BASE_DIR, "rev-list", "--count", f"HEAD..{target}").stdout.strip()
            ahead = git(BASE_DIR, "rev-list", "--count", f"{target}..HEAD").stdout.strip()
            log_lines = git(BASE_DIR, "log", "--format=%h %s", f"HEAD..{target}", "-n", "30").stdout.strip()
            out.update(branch=branch, target=target, latest=target[:7], behind=int(behind or 0), ahead=int(ahead or 0),
                       notes=log_lines, available=int(behind or 0) > 0)
            return out
        repo = self.github_repo()
        if not repo:
            raise RuntimeError("No se sabe de qué repositorio de GitHub viene NovaHub (define NOVAHUB_UPDATE_REPO)")
        import urllib.request
        try:
            req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/latest",
                                         headers={"User-Agent": "NovaHub", "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                rel = json.loads(r.read(1_000_000))
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"no se pudo consultar GitHub: {e}")
        tag = rel.get("tag_name") or ""
        out.update(repo=repo, latest=tag.lstrip("v"), tag=tag, name=rel.get("name") or tag, notes=(rel.get("body") or "")[:6000],
                   url=rel.get("html_url"), published=rel.get("published_at"), available=semver(tag) > semver(VERSION))
        return out

    def check_apt(self):
        if not shutil.which("apt"):
            return {"error": "Este sistema no usa apt (Debian/Ubuntu): las actualizaciones del sistema no están disponibles."}
        if self.sudo_ok():  # refresca las listas (como root, por el script)
            subprocess.run(["sudo", "-n", SYSTEM_SCRIPT, "update"], capture_output=True, timeout=300)
        res = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True, timeout=120, env={**os.environ, "LC_ALL": "C"})
        pkgs = []
        for line in res.stdout.splitlines():
            m = re.match(r"([^/\s]+)/(\S+)\s+(\S+)\s+\S+\s+\[upgradable from: ([^\]]+)\]", line)
            if m:
                pkgs.append({"name": m.group(1), "to": m.group(3), "from": m.group(4), "security": "-security" in m.group(2)})
        return {"packages": pkgs, "checked": time.time()}

    def check_services(self, pull_images=False):
        out = {}
        for sid, svc in list(MANAGER.services.items()):
            kind = svc.get("kind") or "process"
            try:
                if kind == "container" and shutil.which("podman"):
                    image = full_image(svc["image"])
                    if pull_images:  # se descarga ya: aplicar será solo reiniciar
                        subprocess.run(["podman", "pull", "-q", image], capture_output=True, timeout=1800)
                    have = subprocess.run(["podman", "image", "inspect", "--format", "{{.Id}}", image], capture_output=True, text=True, timeout=30).stdout.strip()
                    used = subprocess.run(["podman", "inspect", "--format", "{{.Image}}", container_name(sid)], capture_output=True, text=True, timeout=30).stdout.strip()
                    if used and have and used != have:
                        out[sid] = {"kind": "image", "available": True, "msg": "Imagen nueva descargada: se aplica al reiniciar"}
                elif kind == "process" and os.path.isdir(os.path.join(service_root(svc), ".git")):
                    root = service_root(svc)
                    if git(root, "rev-parse", "--abbrev-ref", "@{u}").returncode != 0:
                        continue
                    if git(root, "fetch", "-q", timeout=60).returncode != 0:
                        continue
                    behind = int(git(root, "rev-list", "--count", "HEAD..@{u}").stdout.strip() or 0)
                    if behind:
                        out[sid] = {"kind": "git", "available": True, "msg": f"{behind} cambio(s) nuevo(s) en GitHub",
                                    "log": git(root, "log", "--format=%h %s", "HEAD..@{u}", "-n", "10").stdout.strip()}
            except (ApiError, OSError, subprocess.TimeoutExpired, KeyError):
                continue
        return out

    def check_deps(self):
        out = {}
        for sid, svc in list(MANAGER.services.items()):
            if (svc.get("kind") or "process") != "process":
                continue
            try:
                root = service_root(svc)
            except ApiError:
                continue
            items = []
            if os.path.isfile(os.path.join(root, "package.json")) and os.path.isdir(os.path.join(root, "node_modules")) and shutil.which("npm"):
                res = subprocess.run(["npm", "outdated", "--json"], cwd=root, capture_output=True, text=True, timeout=180)
                try:
                    for name, v in (json.loads(res.stdout or "{}") or {}).items():
                        if isinstance(v, dict) and v.get("current"):
                            items.append({"name": name, "current": v.get("current"), "wanted": v.get("wanted"), "latest": v.get("latest"),
                                          "tool": "npm", "safe": v.get("wanted") not in (None, v.get("current"))})
                except ValueError:
                    pass
            venv = next((os.path.join(root, d) for d in (".venv", "venv") if os.path.isfile(os.path.join(root, d, "bin", "pip"))), None)
            if venv:
                res = subprocess.run([os.path.join(venv, "bin", "pip"), "list", "--outdated", "--format", "json"],
                                     cwd=root, capture_output=True, text=True, timeout=180)
                try:
                    for p in json.loads(res.stdout or "[]"):
                        items.append({"name": p["name"], "current": p["version"], "latest": p["latest_version"], "wanted": p["latest_version"],
                                      "tool": "pip", "safe": semver(p["latest_version"])[0] == semver(p["version"])[0]})
                except (ValueError, KeyError):
                    pass
            if items:
                out[sid] = {"count": len(items), "safe": sum(1 for i in items if i["safe"]), "items": items[:200]}
        return out

    # ── aplicar ──
    def _run_job(self, name, fn):
        with self.lock:
            if self.job:
                raise ApiError(409, f"Ya hay una actualización en curso ({self.job})")
            self.job = name

        def go():
            ok, msg = True, "Hecho"
            try:
                msg = fn() or msg
            except Exception as e:  # noqa: BLE001
                ok, msg = False, e.msg if isinstance(e, ApiError) else str(e)
            finally:
                self.job = None
            self._ulog(("✓ " if ok else "✗ ") + msg)
            self.history(name, ok, msg)
            if not ok:
                NOTIFIER.notify("updates", None, f"Ha fallado una actualización ({name})", msg, key=f"fallo-{name}", level="danger")
            self.start_check()
        threading.Thread(target=go, name="actualizar", daemon=True).start()
        return self.public()

    @staticmethod
    def _ulog(msg):
        with open(UPDATE_LOG, "ab") as f:
            f.write(f"[{datetime.now():%d/%m %H:%M:%S}] {msg}\n".encode())

    def _logged(self, cmd, cwd=None, timeout=3600):
        self._ulog("$ " + " ".join(cmd))
        with open(UPDATE_LOG, "ab") as f:
            res = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, timeout=timeout)
        if res.returncode != 0:
            raise RuntimeError(f"«{' '.join(cmd[-2:])}» ha terminado con código {res.returncode}")

    def apply_system(self, mode):
        if mode not in ("security", "upgrade"):
            raise ApiError(400, "Modo desconocido")
        if not self.sudo_ok():
            raise ApiError(400, "Falta el permiso para actualizar el sistema (mira las instrucciones en esta página)")

        def fn():
            self._ulog("Actualizando el sistema (" + ("solo seguridad" if mode == "security" else "todo") + ")…")
            self._logged(["sudo", "-n", SYSTEM_SCRIPT, mode])
            return "Sistema actualizado" + (" (seguridad)" if mode == "security" else "") + \
                (": hace falta reiniciar el servidor" if self.reboot_info() else "")
        return self._run_job("Sistema", fn)

    def apply_service(self, sid, what):
        svc = MANAGER.services.get(sid)
        if not svc:
            raise ApiError(404, "Servicio no encontrado")
        if what == "image":
            def fn():
                self._ulog(f"«{svc['name']}»: imagen nueva → reiniciando")
                if MANAGER.running(sid):
                    MANAGER.restart(sid)
                return f"«{svc['name']}» con la imagen nueva"
        elif what == "git":
            DEPLOYER.update(sid)  # el «Actualizar» de siempre: trae los cambios, instala y reinicia
            (self.data.get("services") or {}).pop(sid, None)  # deja de salir como pendiente (la próxima comprobación lo confirma)
            self.history(svc["name"], True, "Actualizando desde GitHub (progreso en su consola)")
            return self.public()
        elif what == "deps":
            def fn():
                root = service_root(svc)
                self._ulog(f"«{svc['name']}»: actualizando dependencias…")
                try:
                    BACKUPS.snapshot(sid, "antes-de-actualizar")
                    self._ulog("copia de seguridad del servicio hecha antes de actualizar")
                except Exception as e:  # noqa: BLE001
                    self._ulog(f"(sin copia previa: {e.msg if isinstance(e, ApiError) else e})")
                items = (self.data.get("deps") or {}).get(sid, {}).get("items") or []
                if any(i["tool"] == "npm" for i in items):
                    self._logged(["npm", "update", "--no-audit", "--no-fund"], cwd=root, timeout=1800)  # dentro de los rangos de package.json
                pips = [i["name"] for i in items if i["tool"] == "pip" and i["safe"] and re.fullmatch(r"[A-Za-z0-9._-]+", i["name"])]
                venv = next((os.path.join(root, d) for d in (".venv", "venv") if os.path.isfile(os.path.join(root, d, "bin", "pip"))), None)
                if pips and venv:
                    self._logged([os.path.join(venv, "bin", "pip"), "install", "-U", *pips], cwd=root, timeout=1800)
                if MANAGER.running(sid):
                    MANAGER.restart(sid)
                return f"«{svc['name']}»: dependencias actualizadas" + (" y reiniciado" if MANAGER.running(sid) else "")
        else:
            raise ApiError(400, "Tipo de actualización desconocido")
        return self._run_job(svc["name"], fn)

    def apply_novahub(self, port):
        info = self.data.get("novahub") or {}
        if not info.get("available"):
            raise ApiError(400, "No hay ninguna versión nueva de NovaHub")
        if not os.environ.get("NOTIFY_SOCKET"):
            raise ApiError(400, "NovaHub no está funcionando como servicio de systemd: actualízalo a mano (git pull y reiniciar)")
        if git(BASE_DIR, "status", "--porcelain", "--untracked-files=no").stdout.strip():
            raise ApiError(400, "Hay cambios sin guardar en los archivos de NovaHub (git status): no se actualiza para no perderlos")
        if info.get("channel") == "dev":
            if info.get("ahead"):
                raise ApiError(400, "Este NovaHub tiene commits propios que no están en GitHub: súbelos antes de actualizar")
            target, branch, label = info["target"], info["branch"], info["latest"]
        else:
            res = git(BASE_DIR, "fetch", "-q", "--tags", "--force", "origin", timeout=120)
            if res.returncode != 0:
                raise ApiError(502, f"No se pudo descargar la versión: {git_output(res)}")
            target = git(BASE_DIR, "rev-parse", f"{info['tag']}^{{commit}}").stdout.strip()
            if not target:
                raise ApiError(502, f"No se encuentra la versión {info['tag']} en el repositorio")
            branch, label = "", info["tag"]
        tmp = os.path.join(RUN_DIR, "updater.py")
        shutil.copy2(os.path.join(BASE_DIR, "updater.py"), tmp)  # fuera del repositorio: git puede cambiar el original
        self._ulog(f"Actualizando NovaHub a {label}: copia de datos, código nuevo, reinicio y comprobación (si falla, vuelve atrás)…")
        with open(UPDATE_LOG, "ab") as f:
            subprocess.Popen([sys.executable, tmp, "--base", BASE_DIR, "--data", DATA_DIR, "--target", target,
                              "--branch", branch, "--label", label, "--port", str(port),
                              "--unit", os.environ.get("NOVAHUB_UNIT", "novahub")],
                             stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True, close_fds=True)
        self.job = "NovaHub"
        return self.public()

    # ── programación ──
    def loop(self):
        last_pull = self.data.get("last_pull") or 0
        while True:
            time.sleep(60)
            SUPERVISOR.beat("actualizaciones")
            try:
                now = time.time()
                cfg = self.config()
                if now - (self.data.get("last_check") or 0) > UPDATE_CHECK_EVERY and not self.checking and not self.job:
                    pull = now - last_pull > 7 * 86400  # imágenes de contenedores: una vez por semana
                    if pull:
                        last_pull = self.data["last_pull"] = now
                    self.checking = True
                    self.check_all(pull_images=pull)
                today = datetime.now()
                if (cfg["auto_security"] and today.hour == cfg["auto_hour"] and not self.job
                        and self.data.get("auto_day") != today.strftime("%Y-%m-%d")
                        and any(p.get("security") for p in (self.data.get("apt") or {}).get("packages") or [])):
                    self.data["auto_day"] = today.strftime("%Y-%m-%d")
                    self.save()
                    self._ulog("Actualizaciones de seguridad automáticas")
                    try:
                        self.apply_system("security")
                    except ApiError as e:
                        self._ulog(f"✗ {e.msg}")
            except Exception:  # noqa: BLE001
                traceback.print_exc()


UPDATES = Updates()


# ───────────────────────────── plantillas de servicio ─────────────────────────────

def _has_venv():
    try:
        return subprocess.run(["python3", "-c", "import ensurepip"], capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


REQUIREMENTS = {
    "node": ("Node.js y npm", lambda: bool(shutil.which("node") and shutil.which("npm")), "sudo apt install nodejs npm"),
    "venv": ("Entornos de Python (venv)", _has_venv, "sudo apt install python3-venv"),
    "java": ("Java 21", lambda: bool(shutil.which("java")), "sudo apt install openjdk-21-jre-headless"),
}

STATIC_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{name_html}}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main>
    <h1>{{name_html}}</h1>
    <p>Tu web ya está en marcha. Edita <code>index.html</code> y <code>style.css</code> en <code>{{dir_html}}</code>.</p>
  </main>
</body>
</html>
"""
STATIC_CSS = """body { margin: 0; min-height: 100vh; display: grid; place-items: center; font-family: system-ui, sans-serif; background: #f4f2f8; color: #1c1924; }
main { max-width: 36rem; padding: 2rem; }
h1 { font-size: 2.5rem; margin: 0 0 .5rem; color: #6c3ff5; }
code { background: #e7e2f3; padding: .1em .35em; border-radius: 4px; }
"""

VITE_PACKAGE = """{
  "name": "{{slug}}",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": { "dev": "vite", "build": "vite build", "preview": "vite preview" },
  "dependencies": { "react": "^19.2.8", "react-dom": "^19.2.8" },
  "devDependencies": { "@vitejs/plugin-react": "^6.1.1", "vite": "^8.3.0" }
}
"""
VITE_CONFIG = """import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})
"""
VITE_INDEX = """<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{name_html}}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""
VITE_MAIN = """import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './App.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
"""
VITE_APP = """import { useState } from 'react'

const NAME = {{name_json}}

export default function App() {
  const [clicks, setClicks] = useState(0)
  return (
    <main>
      <h1>{NAME}</h1>
      <p>Edita <code>src/App.jsx</code>: los cambios se ven al momento.</p>
      <button onClick={() => setClicks(clicks + 1)}>Has pulsado {clicks} veces</button>
    </main>
  )
}
"""
VITE_CSS = """body { margin: 0; min-height: 100vh; display: grid; place-items: center; font-family: system-ui, sans-serif; background: #f4f2f8; color: #1c1924; }
main { text-align: center; padding: 2rem; }
h1 { font-size: 2.5rem; color: #6c3ff5; margin: 0 0 .5rem; }
button { font: inherit; padding: .6em 1.2em; border: 0; border-radius: 10px; background: #6c3ff5; color: #fff; cursor: pointer; }
code { background: #e7e2f3; padding: .1em .35em; border-radius: 4px; }
"""

EXPRESS_PACKAGE = """{
  "name": "{{slug}}",
  "private": true,
  "type": "module",
  "scripts": { "start": "node index.js" },
  "dependencies": { "express": "^5.2.1" }
}
"""
EXPRESS_INDEX = """import express from 'express'

const NAME = {{name_json}}
const app = express()
app.use(express.json())

app.get('/', (req, res) => {
  res.json({ servicio: NAME, estado: 'en marcha' })
})

app.get('/api/hora', (req, res) => {
  res.json({ hora: new Date().toISOString() })
})

const port = process.env.PORT || {{port}}
app.listen(port, '127.0.0.1', () => {
  console.log(`${NAME} escuchando en http://127.0.0.1:${port}`)
})
"""

DISCORD_PACKAGE = """{
  "name": "{{slug}}",
  "private": true,
  "type": "module",
  "scripts": { "start": "node bot.js" },
  "dependencies": { "discord.js": "^14.27.0" }
}
"""
DISCORD_BOT = """import { Client, Events, GatewayIntentBits } from 'discord.js'

// El token llega como variable de entorno (DISCORD_TOKEN): se cambia en «Editar» del servicio.
const client = new Client({ intents: [GatewayIntentBits.Guilds] })

client.once(Events.ClientReady, async (c) => {
  console.log(`Conectado como ${c.user.tag}`)
  // Registra /ping (los comandos globales pueden tardar unos minutos en aparecer)
  await c.application.commands.set([{ name: 'ping', description: 'Comprueba que el bot responde' }])
})

client.on(Events.InteractionCreate, async (interaction) => {
  if (interaction.isChatInputCommand() && interaction.commandName === 'ping') {
    await interaction.reply(`¡Pong! (${client.ws.ping} ms)`)
  }
})

client.login(process.env.DISCORD_TOKEN)
"""

FLASK_APP = """import html
import os

from flask import Flask

NAME = {{name_json}}
FOLDER = {{dir_json}}
app = Flask(__name__)


@app.get("/")
def index():
    return f"<h1>{html.escape(NAME)}</h1><p>Edita <code>app.py</code> en {html.escape(FOLDER)}.</p>"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", {{port}})))
"""

MC_PROPERTIES = """server-port={{port}}
motd={{name_motd}}
max-players=10
online-mode=true
"""


def download_paper(job, path):
    """Última versión estable del servidor Paper, comprobando su suma SHA-256."""
    import urllib.request
    api = "https://fill.papermc.io/v3/projects/paper"
    with urllib.request.urlopen(api, timeout=20) as r:
        groups = json.load(r)["versions"]
    candidates = [v for vs in groups.values() for v in vs if re.fullmatch(r"[\d.]+", v)]
    for version in candidates[:6]:
        with urllib.request.urlopen(f"{api}/versions/{version}/builds/latest", timeout=20) as r:
            build = json.load(r)
        if build.get("channel") != "STABLE":
            continue
        dl = build["downloads"]["server:default"]
        job["log"].append(f"descargando Paper {version} (build {build['id']}, {dl['size'] // 2**20} MB)…")
        digest = hashlib.sha256()
        with urllib.request.urlopen(dl["url"], timeout=60) as r, open(os.path.join(path, "server.jar"), "wb") as f:
            while chunk := r.read(1 << 16):
                digest.update(chunk)
                f.write(chunk)
        if digest.hexdigest() != dl["checksums"]["sha256"]:
            raise RuntimeError("la descarga de Paper está corrupta (la suma SHA-256 no coincide)")
        job["log"].append("descarga verificada")
        return
    raise RuntimeError("no se encontró ninguna versión estable de Paper")


# Cada plantilla: archivos que crea ({{name}}, {{slug}}, {{port}}, {{dir}} se sustituyen), pasos de instalación
# (órdenes o funciones), el servicio resultante y los campos extra que pide.
TEMPLATES = [
    {"id": "static", "name": "Web estática", "desc": "Una página HTML y su CSS, servidas con Python. Para webs sencillas o un portfolio.",
     "tags": ["web"], "port": 8080, "requires": [], "publishable": True,
     "files": {"index.html": STATIC_HTML, "style.css": STATIC_CSS},
     "install": [], "command": "python3 -m http.server {{port}} --bind 127.0.0.1"},
    {"id": "vite-react", "name": "Web React + Vite", "desc": "Proyecto React con recarga al instante, como LlunaTasks.",
     "tags": ["web", "react"], "port": 5173, "requires": ["node"], "publishable": True,
     "files": {"package.json": VITE_PACKAGE, "vite.config.js": VITE_CONFIG, "index.html": VITE_INDEX,
               "src/main.jsx": VITE_MAIN, "src/App.jsx": VITE_APP, "src/App.css": VITE_CSS,
               ".gitignore": "node_modules\ndist\n"},
     "install": [["npm", "install", *NPM_FLAGS]], "command": "npm run dev -- --host 127.0.0.1 --port {{port}} --strictPort"},
    {"id": "express", "name": "API con Node (Express)", "desc": "Una API mínima con dos rutas de ejemplo que responden JSON.",
     "tags": ["api", "node"], "port": 3000, "requires": ["node"], "publishable": True,
     "files": {"package.json": EXPRESS_PACKAGE, "index.js": EXPRESS_INDEX, ".gitignore": "node_modules\n"},
     "install": [["npm", "install", *NPM_FLAGS]], "command": "npm start", "env": {"PORT": "{{port}}"}},
    {"id": "discord", "name": "Bot de Discord", "desc": "Bot con discord.js que responde al comando /ping. Crea el bot en discord.com/developers.",
     "tags": ["bot", "discord"], "port": None, "requires": ["node"], "publishable": False,
     "fields": [{"key": "DISCORD_TOKEN", "label": "Token del bot", "secret": True, "required": True,
                 "help": "Discord Developer Portal → tu aplicación → Bot → Reset Token. Se guarda como variable de entorno."}],
     "files": {"package.json": DISCORD_PACKAGE, "bot.js": DISCORD_BOT, ".gitignore": "node_modules\n.env\n"},
     "install": [["npm", "install", *NPM_FLAGS]], "command": "npm start"},
    {"id": "flask", "name": "App Python (Flask)", "desc": "Web mínima en Python con su propio entorno virtual.",
     "tags": ["web", "python"], "port": 5000, "requires": ["venv"], "publishable": True,
     "files": {"app.py": FLASK_APP, "requirements.txt": "flask\n", ".gitignore": ".venv\n__pycache__\n"},
     "install": [["python3", "-m", "venv", ".venv"], [".venv/bin/pip", "install", "-r", "requirements.txt"]],
     "command": ".venv/bin/python app.py", "env": {"PORT": "{{port}}"}},
    {"id": "minecraft", "name": "Servidor de Minecraft (Paper)", "desc": "Servidor Java con la última versión estable de Paper. Al crearlo aceptas la EULA de Minecraft.",
     "tags": ["juego", "minecraft"], "port": 25565, "requires": ["java"], "publishable": False,
     "note": "El túnel de Cloudflare solo lleva tráfico web: para jugar desde fuera de casa abre el puerto en el router o usa Tailscale.",
     "fields": [{"key": "memory", "label": "Memoria (GB)", "default": "2", "required": True, "help": "RAM máxima para el servidor."}],
     "files": {"eula.txt": "eula=true\n", "server.properties": MC_PROPERTIES},
     "install": [download_paper], "command": "java -Xms1G -Xmx{{memory}}G -jar server.jar nogui",
     "stop_command": "stop", "stop_timeout": 60},
]


def fill(text, values):
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def templates_public():
    out = []
    for t in TEMPLATES:
        missing = [{"what": REQUIREMENTS[r][0], "install": REQUIREMENTS[r][2]} for r in t["requires"] if not REQUIREMENTS[r][1]()]
        out.append({k: t.get(k) for k in ("id", "name", "desc", "tags", "publishable", "note")} | {
            "port": free_port(t["port"]) if t["port"] else None, "missing": missing,
            "fields": [{k: f.get(k) for k in ("key", "label", "secret", "required", "help", "default")} for f in t.get("fields", [])],
        })
    return {"templates": out, "projects_dir": PROJECTS_DIR}


def template_create(data):
    t = next((x for x in TEMPLATES if x["id"] == data.get("template")), None)
    if not t:
        raise ApiError(404, "Esa plantilla no existe")
    missing = [REQUIREMENTS[r] for r in t["requires"] if not REQUIREMENTS[r][1]()]
    if missing:
        raise ApiError(400, f"Falta instalar {missing[0][0]} en el servidor: {missing[0][2]}")
    name = str(data.get("name") or "").strip()[:60]
    if not name:
        raise ApiError(400, "Ponle un nombre al servicio")
    slug = slugify(name)
    dest = os.path.abspath(os.path.expanduser(str(data.get("dest") or "").strip() or os.path.join(PROJECTS_DIR, slug)))
    if os.path.exists(dest) and (not os.path.isdir(dest) or os.listdir(dest)):
        raise ApiError(409, f"La carpeta {dest} ya existe y no está vacía: elige otra")
    if not os.path.isdir(os.path.dirname(dest)):
        raise ApiError(400, f"No existe la carpeta {os.path.dirname(dest)}")
    port = None
    if t["port"]:
        try:
            port = int(data.get("port") or free_port(t["port"]))
        except (TypeError, ValueError):
            raise ApiError(400, "El puerto debe ser un número")
        if port in listening_ports():
            raise ApiError(409, f"El puerto {port} ya está en uso")
    fields = data.get("fields") or {}
    import html as _html
    values = {"name": name, "slug": slug, "port": port or "", "dir": dest,
              # escapados para cada contexto: un nombre con comillas o <> no debe romper el código generado
              "name_html": _html.escape(name), "dir_html": _html.escape(dest),
              "name_json": json.dumps(name), "dir_json": json.dumps(dest),
              "name_motd": name.encode("unicode_escape").decode("ascii")}  # server.properties es ISO-8859-1 con escapes \u
    env = {}
    for f in t.get("fields", []):
        val = str(fields.get(f["key"]) or f.get("default") or "").strip()
        if f.get("required") and not val:
            raise ApiError(400, f"Falta «{f['label']}»")
        if f["key"].isupper():
            env[f["key"]] = val   # secretos y ajustes que el programa lee del entorno
        else:
            values[f["key"]] = val
    if "memory" in values and not values["memory"].isdigit():
        raise ApiError(400, "La memoria debe ser un número entero de GB")
    env.update({k: fill(v, values) for k, v in (t.get("env") or {}).items()})
    service = {
        "name": name, "description": t["desc"].split(".")[0] + ".", "tags": t["tags"], "cwd": dest,
        "command": fill(t["command"], values), "port": port, "env": env, "url": "",
        "autostart": True, "restart_on_crash": True,
        "stop_command": t.get("stop_command", ""), "stop_timeout": t.get("stop_timeout", 15),
        "subdomain": str(data.get("subdomain") or "").strip() if t["publishable"] else "",
    }
    normalize_service({**service, "cwd": ""})  # valida antes de crear nada en disco (la carpeta aún no existe)
    job = DEPLOYER.new_job()
    threading.Thread(target=_template_job, args=(job, t, dest, values, service, bool(data.get("start", True))), daemon=True).start()
    return job["id"]


def _template_job(job, t, dest, values, service, start):
    created = False
    try:
        os.makedirs(dest, exist_ok=True)
        created = True
        for rel, content in t["files"].items():
            full = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as f:
                f.write(fill(content, values))
        job["log"].append(f"▌archivos creados en {dest}: {', '.join(t['files'])}")
        for step in t["install"]:
            if callable(step):
                step(job, dest)
            else:
                DEPLOYER._run(job, step, dest, 900)
        extra, notice = PUBLISHER.apply(None, None, normalize_service(service), service)
        sid = MANAGER.create(service, extra)
        job["log"].append(f"▌servicio «{service['name']}» creado")
        if notice:
            job["log"].append(f"▌{notice}")
        if start:
            MANAGER.start(sid)
            job["log"].append("▌arrancado")
        job["result"] = {"sid": sid}
        job["status"] = "done"
    except Exception as e:  # noqa: BLE001
        msg = e.msg if isinstance(e, ApiError) else str(e)
        job["error"] = msg
        job["log"].append(f"▌error: {msg}")
        if created:
            job["log"].append(f"▌los archivos quedan en {dest}: bórralos o reutilízalos")
        job["status"] = "error"
JOB_ROUTE = re.compile(r"/api/deploy/jobs/([0-9a-f]+)")
ROADMAP_ROUTE = re.compile(r"/api/roadmap/([a-z0-9-]+)")
SERVICE_ROUTE = re.compile(r"/api/services/([a-z0-9-]+)(?:/(start|stop|restart|input|logs/stream|logs/clear|logs/download"
                           r"|files|file|file/download|git|git/commit|git/push|git/pull|update|mode"
                           r"|backups|backups/run|backups/restore|backups/delete|backups/download|tasks|tasks/run|logs/search|env|signups))?")
KILL_ROUTE = re.compile(r"/api/processes/(\d+)/kill")
USER_ROUTE = re.compile(r"/api/users/([a-z0-9][a-z0-9._-]{1,31})")
OFFSITE_ROUTE = re.compile(r"/api/offsite/destinations/([a-z0-9][a-z0-9-]{0,40})(?:/(run|check|snapshots|restore))?")
REMOTE_ROUTE = re.compile(r"/api/remote/([a-z0-9][a-z0-9-]{0,31})/(.+)")
SERVER_ROUTE = re.compile(r"/api/servers/([a-z0-9][a-z0-9-]{0,31})")
TOKEN_ROUTE = re.compile(r"/api/tokens/([0-9a-f]{12})")
REMOTE_LISTEN = os.environ.get("NOVAHUB_REMOTE_LISTEN", "").strip()   # «IP:puerto» de la puerta para otros paneles
# Lo que puede hacer quien no es administrador. Todo lo demás exige «admin» (denegado por defecto).
SERVICE_VIEW = {None, "logs/stream", "logs/search", "logs/download", "backups", "tasks"}
SERVICE_OPERATE = {"start", "stop", "restart", "backups/run", "tasks/run"}


def route_permission(method, path, service_param=""):
    """(permiso, servicio) que exige cada petición de la API; None = cualquier usuario con sesión."""
    if path == "/api/me" or (path == "/api/account" and method == "PUT"):
        return None, None
    if method == "GET" and path in ("/api/system", "/api/services", "/api/app/android"):
        return "view", None
    if method == "GET" and path == "/api/metrics":
        return "view", (service_param if service_param and service_param != "system" else None)
    m = SERVICE_ROUTE.fullmatch(path)
    if m:
        sid, action = m.groups()
        if method == "GET" and action in SERVICE_VIEW:
            return "view", sid
        if method == "POST" and action in SERVICE_OPERATE:
            return "operate", sid
        if method == "POST" and action == "input":
            return "console", sid
        return "edit", sid
    return "admin", None


class Handler(BaseHTTPRequestHandler):
    server_version = "NovaHub"
    sys_version = ""

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def do_PUT(self):
        self.route("PUT")

    def do_DELETE(self):
        self.route("DELETE")

    # ── helpers ──
    def client_ip(self):
        ip = self.client_address[0]
        if ip in ("127.0.0.1", "::1"):  # detrás de cloudflared / proxy local
            fwd = self.headers.get("Cf-Connecting-Ip") or (self.headers.get("X-Forwarded-For") or "").split(",")[0]
            ip = fwd.strip() or ip
        return ip

    def is_https(self):
        return (self.headers.get("X-Forwarded-Proto") == "https"
                or "https" in (self.headers.get("Cf-Visitor") or ""))

    def common_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                         "frame-ancestors 'none'; base-uri 'none'; form-action 'self'")

    def send_json(self, data, code=200, cookie=None):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        cookie = cookie if cookie is not None else getattr(self, "renewed_cookie", None)
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        self.common_headers()
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise ApiError(400, "Cabecera Content-Length inválida")
        if length < 0:
            raise ApiError(400, "Cabecera Content-Length inválida")
        if length > 1024 * 1024:
            raise ApiError(413, "Petición demasiado grande")
        if not length:
            return {}
        try:
            data = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            raise ApiError(400, "JSON inválido")
        if not isinstance(data, dict):
            raise ApiError(400, "Se esperaba un objeto JSON")
        return data

    def session_cookie(self, value, max_age=None):
        parts = [f"nh_session={value}", "Path=/", "HttpOnly", "SameSite=Strict"]
        if max_age is not None:  # sin Max-Age es una cookie de sesión: se borra al cerrar el navegador
            parts.append(f"Max-Age={max_age}")
        if self.is_https():
            parts.append("Secure")
        return "; ".join(parts)

    def session_token(self):
        morsel = SimpleCookie(self.headers.get("Cookie") or "").get("nh_session")
        return morsel.value if morsel else None

    def authed(self):
        """Valida la sesión. Si el usuario está activo (cabecera de la interfaz), alarga la caducidad:
        las peticiones automáticas de la pantalla no cuentan, así una pestaña olvidada se bloquea sola."""
        auth = self.headers.get("Authorization") or ""
        if auth.startswith("Bearer "):  # otro panel NovaHub con una llave de acceso: sin cookies ni renovación
            username = TOKENS.check(auth[7:].strip())
            if not username:
                AUTH.failed(self.client_ip())
                return False
            self.user = AUTH.public_user(username)
            return True
        if getattr(self.server, "remote_only", False):
            return False  # la puerta para otros paneles solo acepta llaves
        token = self.session_token()
        parsed = AUTH.parse_token(token)
        if not parsed:
            return False
        issued, expires, username = parsed
        self.user = AUTH.public_user(username)
        if self.headers.get("X-NovaHub-Activity") == "1" and expires - time.time() < AUTH.settings()["idle_minutes"] * 60 - 30:
            self.renewed_cookie = self.session_cookie(AUTH.make_token(username, issued))
        return True

    # ── permisos ──
    def can(self, perm, sid=None):
        u = self.user
        if perm not in ROLES[u["role"]]:
            return False
        return not sid or u["role"] == "admin" or u["services"] == "*" or sid in u["services"]

    def need(self, perm, sid=None):
        if perm and not self.can(perm, sid):
            raise ApiError(403, "No tienes acceso a este servicio" if self.can(perm) else "No tienes permiso para esto")

    def svc_out(self, data):
        """Lo que ve cada usuario de un servicio: sin comando, rutas ni variables si no es administrador."""
        if self.can("edit"):
            return data
        hidden = ("command", "dev_command", "cwd", "env", "volumes", "cargs", "ccmd", "compose_file", "stop_command", "tasks", "backup_cfg", "notes")
        return {k: v for k, v in data.items() if k not in hidden}

    # ── enrutado ──
    def route(self, method):
        self.renewed_cookie = None  # la conexión puede reutilizarse: nada de la petición anterior
        self.user = None
        path = urlparse(self.path).path
        try:
            if getattr(self.server, "remote_only", False) and (not path.startswith("/api/") or path in ("/api/login", "/api/logout")):
                raise ApiError(404, "No encontrado")  # puerta solo de API: ni interfaz ni inicio de sesión
            if path.startswith("/api/"):
                self.api(method, path)
            elif method == "GET":
                self.static(path)
            else:
                raise ApiError(404, "No encontrado")
        except ApiError as e:
            self.send_json({"error": e.msg}, e.code)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:  # noqa: BLE001
            traceback.print_exc()
            try:
                self.send_json({"error": "Error interno del servidor"}, 500)
            except OSError:
                pass

    def static(self, path):
        if path == "/":
            path = "/index.html"
        full = os.path.realpath(os.path.join(STATIC_DIR, path.lstrip("/")))
        if not full.startswith(STATIC_DIR + os.sep) or not os.path.isfile(full):
            raise ApiError(404, "No encontrado")
        with open(full, "rb") as f:
            body = f.read()
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "image/svg+xml"):
            ctype += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.common_headers()
        self.end_headers()
        self.wfile.write(body)

    def api(self, method, path):
        # Los navegadores no pueden enviar cabeceras propias a otro origen sin CORS:
        # exigirla en todo lo que modifica estado bloquea los ataques CSRF.
        if method != "GET" and self.headers.get("X-NovaHub") != "1":
            raise ApiError(403, "Petición no permitida")

        if path == "/api/login" and method == "POST":
            ip = self.client_ip()
            if AUTH.throttled(ip):
                raise ApiError(429, "Demasiados intentos. Espera unos minutos.")
            body = self.read_body()
            username = AUTH.login(body.get("username"), str(body.get("password") or ""))
            if not username:
                AUTH.failed(ip)
                raise ApiError(401, "Usuario o contraseña incorrectos")
            return self.send_json({"ok": True}, cookie=self.session_cookie(AUTH.make_token(username)))
        if path == "/api/logout" and method == "POST":
            AUTH.revoke(self.session_token())
            return self.send_json({"ok": True}, cookie=self.session_cookie("", 0))

        if AUTH.throttled(self.client_ip()) and (self.headers.get("Authorization") or "").startswith("Bearer "):
            raise ApiError(429, "Demasiados intentos. Espera unos minutos.")
        if not self.authed():
            raise ApiError(401, "No autorizado")
        m = REMOTE_ROUTE.fullmatch(path)
        if m:  # otro servidor: este panel reenvía la petición con la llave guardada
            self.need("admin")
            return self.proxy(m.group(1), m.group(2))
        perm, psid = route_permission(method, path, self.query("service"))
        self.need(perm, psid)  # todo lo que no está en route_permission es solo para administradores

        if path == "/api/me":
            return self.send_json({"ok": True, **AUTH.settings(), "user": self.user,
                                   "roadmap": ROADMAP.enabled() and self.can("admin")})
        if path == "/api/account" and method == "PUT":
            body = self.read_body()
            AUTH.change_own_password(self.user["username"], body.get("current"), body.get("password"))
            username = self.user["username"]  # la versión ha cambiado: sesión nueva para seguir dentro
            return self.send_json({"ok": True}, cookie=self.session_cookie(AUTH.make_token(username)))
        if path == "/api/servers":
            if method == "GET":
                return self.send_json({"servers": REMOTES.public(with_status=True)})
            if method == "POST":
                return self.send_json({"servers": REMOTES.add(self.read_body())}, 201)
            raise ApiError(405, "Método no permitido")
        m = SERVER_ROUTE.fullmatch(path)
        if m and method == "DELETE":
            REMOTES.delete(m.group(1))
            return self.send_json({"ok": True})
        if path == "/api/tokens":
            if method == "GET":
                return self.send_json({"tokens": TOKENS.public(), "listen": REMOTE_LISTEN or None})
            if method == "POST":
                body = self.read_body()
                raw = TOKENS.create(body.get("name"), self.user["username"])
                return self.send_json({"token": raw, "tokens": TOKENS.public()}, 201)
            raise ApiError(405, "Método no permitido")
        m = TOKEN_ROUTE.fullmatch(path)
        if m and method == "DELETE":
            TOKENS.revoke(m.group(1))
            return self.send_json({"tokens": TOKENS.public()})
        if path == "/api/users":
            if method == "GET":
                return self.send_json({"users": AUTH.list_users(), "roles": ROLE_LABELS})
            if method == "POST":
                return self.send_json(AUTH.create_user(self.read_body()), 201)
            raise ApiError(405, "Método no permitido")
        m = USER_ROUTE.fullmatch(path)
        if m:
            if method == "PUT":
                return self.send_json(AUTH.update_user(m.group(1), self.read_body(), self.user["username"]))
            if method == "DELETE":
                AUTH.delete_user(m.group(1), self.user["username"])
                return self.send_json({"ok": True})
            raise ApiError(405, "Método no permitido")
        if path == "/api/session-settings":
            if method == "GET":
                return self.send_json(AUTH.settings())
            if method == "PUT":
                return self.send_json(AUTH.save_settings(self.read_body()))
            raise ApiError(405, "Método no permitido")
        if path == "/api/system":
            info = {**system_info(), "android_apk": os.path.isfile(ANDROID_APK), "version": VERSION}
            if self.can("admin"):
                u = UPDATES.data
                info["updates"] = {"novahub": bool((u.get("novahub") or {}).get("available")),
                                   "security": sum(1 for p in (u.get("apt") or {}).get("packages") or [] if p.get("security")),
                                   "system": len((u.get("apt") or {}).get("packages") or []), "reboot": bool(UPDATES.reboot_info())}
            return self.send_json(info)
        if path == "/api/app/android" and method == "GET":
            return self.download_apk()
        if path == "/api/git-identity":
            if method == "GET":
                return self.send_json(git_identity())
            if method == "PUT":
                return self.send_json(set_git_identity(self.read_body()))
            raise ApiError(405, "Método no permitido")
        if path == "/api/catalog" and method == "GET":
            return self.send_json(CATALOG.public())
        if path == "/api/catalog/install" and method == "POST":
            return self.send_json(CATALOG.install(self.read_body()), 201)
        if path == "/api/offsite":
            if method == "GET":
                return self.send_json(OFFSITE.public())
            if method == "PUT":
                return self.send_json(OFFSITE.save_config(self.read_body()))
            raise ApiError(405, "Método no permitido")
        if path == "/api/offsite/destinations" and method == "POST":
            return self.send_json(OFFSITE.add(self.read_body()), 201)
        if path == "/api/offsite/key" and method == "POST":
            return self.send_json({"pubkey": OFFSITE.ssh_key(create=True)})
        m = OFFSITE_ROUTE.fullmatch(path)
        if m:
            did, act = m.groups()
            if act is None and method == "DELETE":
                return self.send_json(OFFSITE.delete(did))
            if act == "run" and method == "POST":
                return self.send_json(OFFSITE.run(did, verify=bool(self.read_body().get("verify"))), 202)
            if act == "check" and method == "POST":
                return self.send_json(OFFSITE.check(did), 202)
            if act == "snapshots" and method == "GET":
                return self.send_json(OFFSITE.snapshots(did))
            if act == "restore" and method == "POST":
                return self.send_json(OFFSITE.restore(did, self.read_body().get("snapshot")), 202)
            raise ApiError(405, "Método no permitido")
        if path == "/api/updates":
            if method == "GET":
                return self.send_json(UPDATES.public())
            if method == "PUT":
                return self.send_json(UPDATES.save_config(self.read_body()))
            raise ApiError(405, "Método no permitido")
        if path == "/api/updates/check" and method == "POST":
            UPDATES.start_check()
            return self.send_json(UPDATES.public(), 202)
        if path == "/api/updates/novahub" and method == "POST":
            return self.send_json(UPDATES.apply_novahub(self.server.server_address[1]), 202)
        if path == "/api/updates/system" and method == "POST":
            return self.send_json(UPDATES.apply_system(str(self.read_body().get("mode") or "")), 202)
        if path == "/api/updates/service" and method == "POST":
            body = self.read_body()
            return self.send_json(UPDATES.apply_service(str(body.get("id") or ""), str(body.get("what") or "")), 202)
        if path == "/api/updates/reboot" and method == "POST":
            POWER.reboot()
            return self.send_json({"ok": True}, 202)
        if path == "/api/network" and method == "GET":
            return self.send_json(NETWORK.public())
        if path == "/api/metrics" and method == "GET":
            rng, key = self.query("range") or "1h", self.query("service") or "system"
            if rng not in METRICS_RANGES:
                raise ApiError(400, "Rango desconocido (1h o 24h)")
            if key != "system" and key not in MANAGER.services:
                raise ApiError(404, "Servicio no encontrado")
            extra = ({"mem_total": meminfo()["total"], "cpus": os.cpu_count()} if key == "system"
                     else {"memory_limit": MANAGER.services[key].get("memory_limit")})
            return self.send_json({**METRICS.series(key, rng), **extra})
        if path == "/api/notify":
            if method == "GET":
                return self.send_json(NOTIFIER.public())
            if method == "PUT":
                return self.send_json(NOTIFIER.save(self.read_body()))
            raise ApiError(405, "Método no permitido")
        if path == "/api/notify/test" and method == "POST":
            return self.send_json(NOTIFIER.test())
        if path == "/api/notify/ntfy/test" and method == "POST":
            return self.send_json(NOTIFIER.test_ntfy())
        if path == "/api/notify/ntfy/setup" and method == "POST":
            return self.send_json(ntfy_setup(str(self.read_body().get("service") or "")))
        if path == "/api/templates" and method == "GET":
            return self.send_json(templates_public())
        if path == "/api/templates/create" and method == "POST":
            return self.send_json({"job": template_create(self.read_body())}, 202)
        if path == "/api/github/repos" and method == "GET":
            return self.send_json(gh_repos())
        if path == "/api/deploy/clone" and method == "POST":
            return self.send_json({"job": DEPLOYER.clone(self.read_body())}, 202)
        m = JOB_ROUTE.fullmatch(path)
        if m and method == "GET":
            return self.send_json(DEPLOYER.job(m.group(1)))
        if path == "/api/roadmap":
            if method == "GET":
                return self.send_json({"items": ROADMAP.list()})
            if method == "POST":
                return self.send_json({"items": ROADMAP.add(self.read_body())}, 201)
            raise ApiError(405, "Método no permitido")
        if path == "/api/roadmap/version" and method == "POST":
            return self.send_json({"items": ROADMAP.close_version(self.read_body().get("version"))})
        m = ROADMAP_ROUTE.fullmatch(path)
        if m:
            if method == "PUT":
                return self.send_json({"items": ROADMAP.update(m.group(1), self.read_body())})
            if method == "DELETE":
                return self.send_json({"items": ROADMAP.delete(m.group(1))})
            raise ApiError(405, "Método no permitido")
        if path == "/api/processes" and method == "GET":
            return self.send_json(TASKS.snapshot())
        m = KILL_ROUTE.fullmatch(path)
        if m and method == "POST":
            TASKS.kill(int(m.group(1)), bool(self.read_body().get("force")))
            return self.send_json({"ok": True})
        if path == "/api/power" and method == "GET":
            return self.send_json(POWER.status())
        if path == "/api/power/off" and method == "POST":
            POWER.shutdown()
            return self.send_json({"ok": True}, 202)
        if path == "/api/services":
            if method == "GET":
                return self.send_json({"services": [self.svc_out(s) for s in MANAGER.list_public() if self.can("view", s["id"])]})
            if method == "POST":
                body = self.read_body()
                extra, notice = PUBLISHER.apply(None, None, normalize_service(body), body)
                sid = MANAGER.create(body, extra)
                return self.send_json({**MANAGER.get_public(sid), "notice": notice}, 201)
            raise ApiError(405, "Método no permitido")

        m = SERVICE_ROUTE.fullmatch(path)
        if not m:
            raise ApiError(404, "No encontrado")
        sid, action = m.groups()
        if sid not in MANAGER.services:
            raise ApiError(404, "Servicio no encontrado")

        if action is None:
            if method == "GET":
                return self.send_json(self.svc_out(MANAGER.get_public(sid)))
            if method == "PUT":
                body = self.read_body()
                extra, notice = PUBLISHER.apply(sid, MANAGER.services[sid], normalize_service(body), body)
                MANAGER.update(sid, body, extra)
                return self.send_json({**MANAGER.get_public(sid), "notice": notice})
            if method == "DELETE":
                svc = dict(MANAGER.services[sid])
                MANAGER.delete(sid)
                return self.send_json({"ok": True, "notice": PUBLISHER.unpublish(svc)})
            raise ApiError(405, "Método no permitido")

        if action == "logs/stream" and method == "GET":
            return self.stream_logs(sid)
        if action == "logs/search" and method == "GET":
            return self.send_json(search_log(sid, self.query("q"), self.query("errors") == "1",
                                             self.query("regex") == "1", self.query("case") == "1"))
        if action == "logs/download" and method == "GET":
            return self.download_log(sid)
        svc = MANAGER.services[sid]
        if method == "GET" and action == "files":
            return self.send_json(list_dir(svc, self.query("path")))
        if method == "GET" and action == "file":
            return self.send_json(read_file(svc, self.query("path")))
        if method == "GET" and action == "file/download":
            return self.download_file(svc, self.query("path"))
        if action == "env" and method == "GET":
            return self.send_json(read_env(svc, self.query("file")))
        if action == "env" and method == "PUT":
            return self.send_json(write_env(sid, svc, self.query("file"), self.read_body()))
        if action == "tasks" and method == "GET":
            out = SCHEDULER.public(sid)
            if not self.can("edit"):  # los comandos de las tareas pueden llevar claves
                out["tasks"] = [{**t, "text": ""} for t in out["tasks"]]
            return self.send_json(out)
        if action == "tasks" and method == "PUT":
            return self.send_json(SCHEDULER.save(sid, self.read_body().get("tasks")))
        if action == "tasks/run" and method == "POST":
            return self.send_json(SCHEDULER.run_now(sid, str(self.read_body().get("id") or "")), 202)
        if action == "backups" and method == "GET":
            return self.send_json(BACKUPS.public(sid))
        if action == "backups" and method == "PUT":
            return self.send_json(BACKUPS.save_config(sid, self.read_body()))
        if action == "backups/run" and method == "POST":
            BACKUPS.start(sid, "manual")
            return self.send_json(BACKUPS.public(sid), 202)
        if action == "signups" and method == "POST":
            return self.send_json(CATALOG.set_signups(sid, self.read_body()))
        if action == "backups/restore" and method == "POST":
            BACKUPS.restore(sid, self.read_body().get("name"))
            return self.send_json(BACKUPS.public(sid), 202)
        if action == "backups/delete" and method == "POST":
            return self.send_json(BACKUPS.delete(sid, self.read_body().get("name")))
        if action == "backups/download" and method == "GET":
            return self.download_snapshot(sid, self.query("name"))
        if method == "PUT" and action == "file":
            return self.send_json(write_file(sid, svc, self.query("path"), self.read_body()))
        if method == "GET" and action == "git":
            return self.send_json(git_status(svc))
        if method == "POST" and action == "mode":
            DEPLOYER.set_mode(sid, str(self.read_body().get("mode") or ""))
            return self.send_json(MANAGER.get_public(sid), 202)
        if method == "POST" and action == "update":
            DEPLOYER.update(sid)
            return self.send_json(MANAGER.get_public(sid), 202)
        if method == "POST" and action in ("git/commit", "git/push", "git/pull"):
            if action == "git/commit":
                out = git_commit(svc, self.read_body().get("message"))
            else:
                out = git_push(svc) if action == "git/push" else git_pull(svc)
            return self.send_json({"output": out, "git": git_status(svc)})
        if method != "POST":
            raise ApiError(405, "Método no permitido")
        if action == "start":
            MANAGER.start(sid)
        elif action == "stop":
            MANAGER.stop(sid)
        elif action == "restart":
            MANAGER.restart(sid)
        elif action == "input":
            line = str(self.read_body().get("line") or "")
            if "\n" in line or len(line) > 2000:
                raise ApiError(400, "Comando inválido")
            MANAGER.send_input(sid, line)
        elif action == "logs/clear":
            MANAGER.clear_log(sid)
        return self.send_json(self.svc_out(MANAGER.get_public(sid)))

    def query(self, name):
        return (parse_qs(urlparse(self.path).query).get(name) or [""])[0]

    def download_file(self, svc, rel):
        root = service_root(svc)
        full = safe_path(root, rel)
        if not os.path.isfile(full):
            raise ApiError(404, "El archivo no existe")
        fname = re.sub(r'["\\\r\n]', "_", os.path.basename(full))
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
        self.send_header("Content-Length", str(os.path.getsize(full)))
        self.common_headers()
        self.end_headers()
        with open(full, "rb") as f:
            shutil.copyfileobj(f, self.wfile, 64 * 1024)

    def proxy(self, rid, rest):
        """Reenvía la petición al agente y devuelve su respuesta tal cual, a trozos (sirve para SSE y descargas)."""
        s = REMOTES.get(rid)
        if rest in ("login", "logout", "account") or rest.startswith("remote/"):
            raise ApiError(400, "Eso se hace en el panel principal")
        query = urlparse(self.path).query
        body = None
        if self.command not in ("GET", "HEAD"):
            body = json.dumps(self.read_body()).encode()
        stream = rest.endswith("logs/stream")
        try:
            conn = REMOTES.connect(s, timeout=60 if stream else 30)
            conn.request(self.command, f"/api/{rest}" + (f"?{query}" if query else ""), body=body,
                         headers={"Authorization": f"Bearer {s['token']}", "X-NovaHub": "1", "Content-Type": "application/json"})
            res = conn.getresponse()
        except (OSError, http.client.HTTPException) as e:
            raise ApiError(502, f"No se puede conectar con «{s['name']}»: {e}")
        if res.status == 401:
            raise ApiError(502, f"«{s['name']}» no acepta la llave (¿la han revocado?)")
        self.send_response(res.status)
        # Solo pasan tal cual JSON y la consola en directo. Todo lo demás sale como descarga: un servidor remoto
        # comprometido no puede colar una página o un script que este panel sirva como suyo.
        ctype = (res.getheader("Content-Type") or "").split(";")[0].strip().lower()
        if ctype in ("application/json", "text/event-stream"):
            self.send_header("Content-Type", res.getheader("Content-Type"))
        else:
            fn = re.search(r'filename="([^"]+)"', res.getheader("Content-Disposition") or "")
            name = re.sub(r"[^A-Za-z0-9._-]", "_", fn.group(1) if fn else "descarga")[:100]
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{name}"')
        self.send_header("Content-Security-Policy", "sandbox; default-src 'none'")
        for h in ("Content-Length", "Cache-Control"):
            if res.getheader(h):
                self.send_header(h, res.getheader(h))
        if self.renewed_cookie:  # mientras se usa otro servidor, la sesión de este panel también se alarga
            self.send_header("Set-Cookie", self.renewed_cookie)
        self.common_headers()
        self.end_headers()
        try:
            while True:
                chunk = res.read1(65536) if stream else res.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)
                if stream:
                    self.wfile.flush()
        except (OSError, http.client.HTTPException):
            pass
        finally:
            conn.close()

    def download_apk(self):
        """La app de Android compilada con android/build.sh (data/app/NovaHub.apk), para pasarla al móvil."""
        if not os.path.isfile(ANDROID_APK):
            raise ApiError(404, "Aún no se ha compilado la app de Android (android/build.sh)")
        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.android.package-archive")
        self.send_header("Content-Disposition", 'attachment; filename="NovaHub.apk"')
        self.send_header("Content-Length", str(os.path.getsize(ANDROID_APK)))
        self.common_headers()
        self.end_headers()
        with open(ANDROID_APK, "rb") as f:
            shutil.copyfileobj(f, self.wfile, 64 * 1024)

    def download_snapshot(self, sid, name):
        full = BACKUPS.path_of(sid, name)
        self.send_response(200)
        self.send_header("Content-Type", "application/gzip")
        self.send_header("Content-Disposition", f'attachment; filename="{sid}-{name}"')
        self.send_header("Content-Length", str(os.path.getsize(full)))
        self.common_headers()
        self.end_headers()
        with open(full, "rb") as f:
            shutil.copyfileobj(f, self.wfile, 64 * 1024)

    def download_log(self, sid):
        try:
            with open(log_path(sid), "rb") as f:
                body = f.read()
        except FileNotFoundError:
            body = b""
        body = re.sub(rb"\x1b\[[0-9;?]*[@-~]", b"", body)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{sid}.log"')
        self.send_header("Content-Length", str(len(body)))
        self.common_headers()
        self.end_headers()
        self.wfile.write(body)

    def stream_logs(self, sid):
        """Server-Sent Events: la cola del log y después todo lo que se vaya escribiendo."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("X-Accel-Buffering", "no")
        self.common_headers()
        self.end_headers()

        path = log_path(sid)
        try:
            size = os.path.getsize(path)
        except FileNotFoundError:
            size = 0
        pos = max(0, size - LOG_TAIL_BYTES)
        skip_partial_line = pos > 0
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        last_sent = time.time()

        def send(event, data):
            msg = (f"event: {event}\n" if event else "") + f"data: {json.dumps(data)}\n\n"
            self.wfile.write(msg.encode())
            self.wfile.flush()

        while sid in MANAGER.services:
            try:
                size = os.path.getsize(path)
            except FileNotFoundError:
                size = 0
            if size < pos:  # log truncado (limpiado o rotado)
                pos = 0
                decoder.reset()
                send("clear", "")
                last_sent = time.time()
            if size > pos:
                with open(path, "rb") as f:
                    f.seek(pos)
                    chunk = f.read(min(size - pos, 256 * 1024))
                pos += len(chunk)
                if skip_partial_line:
                    nl = chunk.find(b"\n")
                    chunk = chunk[nl + 1:] if nl != -1 else b""
                    skip_partial_line = False
                text = decoder.decode(chunk)
                if text:
                    send(None, text)
                    last_sent = time.time()
                continue
            if time.time() - last_sent > 15:  # evita que Cloudflare corte la conexión
                self.wfile.write(b": ping\n\n")
                self.wfile.flush()
                last_sent = time.time()
            time.sleep(0.25)


# ───────────────────────────── main ─────────────────────────────

def ask_password():
    if not sys.stdin.isatty():
        pw = sys.stdin.readline().rstrip("\n")
    else:
        pw = getpass.getpass("Nueva contraseña del panel: ")
        if pw != getpass.getpass("Repítela: "):
            sys.exit("Las contraseñas no coinciden.")
    if len(pw) < 8:
        sys.exit("La contraseña debe tener al menos 8 caracteres.")
    return pw


DEMO = {
    "id": "demo-web", "name": "Servidor web de prueba",
    "description": "Ejemplo: sirve una página de prueba en el puerto 8090. Edítalo o bórralo cuando quieras.",
    "tags": ["demo", "web"], "command": "python3 -m http.server 8090",
    "cwd": os.path.join(BASE_DIR, "demo"), "env": {}, "port": 8090, "url": "", "stop_command": "",
    "stop_timeout": 10, "autostart": False, "restart_on_crash": False,
}


def seed_example():
    if os.path.exists(SERVICES_FILE):
        return
    write_json(SERVICES_FILE, [{**DEMO, "created_at": time.time()}])


def panel_url(port):
    """https://<host> del panel según la regla del túnel que apunta a su puerto (si está publicado)."""
    if not PUBLISHER.enabled:
        return None
    try:
        entries = PUBLISHER.entries(PUBLISHER.read())[0]
    except (OSError, ApiError):
        return None
    host = next((e[2] for e in entries if e[2] and e[3] and e[3].rstrip("/").endswith(f":{port}")), None)
    return f"https://{host}" if host else None


def remote_listener():
    """Puerta solo de API para otros paneles NovaHub (NOVAHUB_REMOTE_LISTEN=IP:puerto, p. ej. la IP de Tailscale)."""
    host, _, port = REMOTE_LISTEN.rpartition(":")
    while True:
        try:
            srv = ThreadingHTTPServer((host.strip("[]"), int(port)), Handler)
            srv.daemon_threads = True
            srv.remote_only = True
            print(f"Puerta para otros paneles en http://{REMOTE_LISTEN} (solo con llave de acceso)", flush=True)
            srv.serve_forever()
        except (OSError, ValueError) as e:
            print(f"[puerta remota] no se puede escuchar en {REMOTE_LISTEN}: {e}; reintento en 30 s", flush=True)
            time.sleep(30)


def main():
    global MANAGER, AUTH, PUBLISHER, GATEWAY
    parser = argparse.ArgumentParser(description="NovaHub — gestor de servicios")
    parser.add_argument("command", nargs="?", default="serve", choices=["serve", "set-password"])
    parser.add_argument("user", nargs="?", help="con set-password: el usuario (por defecto, el primer administrador)")
    parser.add_argument("--host", default=os.environ.get("NOVAHUB_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("NOVAHUB_PORT", "8686")))
    args = parser.parse_args()

    for d in (DATA_DIR, LOG_DIR, RUN_DIR):
        os.makedirs(d, mode=0o700, exist_ok=True)

    AUTH = Auth()
    if args.command == "set-password":
        try:
            name = AUTH.set_password(ask_password(), (args.user or "").lower() or None)
        except ApiError as e:
            sys.exit(e.msg)
        print(f"Contraseña de «{name}» guardada. Sus sesiones abiertas se han cerrado.")
        return
    if not AUTH.configured():
        if not sys.stdin.isatty():
            sys.exit("No hay ningún usuario. Ejecuta primero: python3 server.py set-password")
        print("Primera ejecución: elige la contraseña del panel.")
        name = AUTH.set_password(ask_password())
        print(f"Usuario administrador: {name}")

    seed_example()
    prev = previous_run()
    mark_run("running")
    PUBLISHER = Publisher()
    MANAGER = Manager()
    MANAGER.boot()
    GATEWAY = Gateway()
    SUPERVISOR.spawn("pasarela", GATEWAY.loop.run_forever)
    SUPERVISOR.spawn("salud", HEALTH.loop)
    GATEWAY.sync()
    PUBLISHER.reconcile()
    SUPERVISOR.spawn("correo", NOTIFIER.loop)
    global PANEL_URL
    PANEL_URL = os.environ.get("NOVAHUB_PUBLIC_URL", "").rstrip("/") or panel_url(args.port)
    failed = [s["name"] for sid, s in MANAGER.services.items() if s.get("autostart") and not MANAGER.running(sid)]
    startup_notice(prev, failed)
    SUPERVISOR.spawn("vigilancia", MANAGER.monitor)
    SUPERVISOR.spawn("copias", BACKUPS.loop)
    SUPERVISOR.spawn("graficas", METRICS.loop)
    SUPERVISOR.spawn("tareas", SCHEDULER.loop)
    SUPERVISOR.spawn("actualizaciones", UPDATES.loop)
    SUPERVISOR.spawn("fuera-de-casa", OFFSITE.loop)
    SUPERVISOR.spawn("registro-de-cuentas", CATALOG.watch)
    write_json(RUNNING_FILE, {"version": VERSION, "commit": current_commit(), "pid": os.getpid(), "at": time.time()})

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.daemon_threads = True
    if REMOTE_LISTEN:
        threading.Thread(target=remote_listener, name="puerta-remota", daemon=True).start()
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown).start())
    SUPERVISOR.url = ("127.0.0.1" if args.host in ("0.0.0.0", "::", "") else args.host, args.port)
    threading.Thread(target=SUPERVISOR.loop, name="supervisor", daemon=True).start()
    sd_notify("READY=1")
    sd_notify("WATCHDOG=1")
    print(f"NovaHub escuchando en http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    METRICS.save()
    mark_run("stopped")
    print("NovaHub detenido (los servicios siguen en marcha).")


if __name__ == "__main__":
    main()
