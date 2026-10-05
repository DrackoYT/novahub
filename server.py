#!/usr/bin/env python3
"""
NovaHub — panel web para arrancar, parar y vigilar los servicios del servidor.

Sin dependencias externas: solo la librería estándar de Python 3.9+.

    python3 server.py set-password          # define o cambia la contraseña
    python3 server.py [--host H] [--port P] # arranca el panel (por defecto 127.0.0.1:8686)
"""
from __future__ import annotations

import argparse
import codecs
import getpass
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.environ.get("NOVAHUB_DATA", os.path.join(BASE_DIR, "data")))
STATIC_DIR = os.path.join(BASE_DIR, "static")
LOG_DIR = os.path.join(DATA_DIR, "logs")
RUN_DIR = os.path.join(DATA_DIR, "run")
SERVICES_FILE = os.path.join(DATA_DIR, "services.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
AUTH_FILE = os.path.join(DATA_DIR, "auth.json")

LOG_MAX_BYTES = 5 * 1024 * 1024    # al superarlo, el log se rota a <id>.log.1
LOG_TAIL_BYTES = 64 * 1024         # lo que se envía al abrir la consola
SESSION_TTL = 30 * 24 * 3600
MAX_AUTO_RESTARTS = 5              # reinicios automáticos permitidos por minuto
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


def write_json(path, data, mode=0o644):
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def log_path(sid):
    return os.path.join(LOG_DIR, f"{sid}.log")


def fifo_path(sid):
    return os.path.join(RUN_DIR, f"{sid}.stdin")


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


# ───────────────────────────── validación ─────────────────────────────

ENV_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def normalize_service(data: dict) -> dict:
    def text(key, maxlen, required=False):
        val = str(data.get(key) or "").strip()
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

    return {
        "name": text("name", 60, required=True),
        "description": text("description", 500),
        "tags": clean_tags[:12],
        "command": text("command", 4000, required=True),
        "cwd": cwd,
        "env": {str(k): str(v) for k, v in env.items()},
        "port": port,
        "url": url,
        "stop_command": text("stop_command", 200),
        "stop_timeout": max(1, min(stop_timeout, 120)),
        "autostart": bool(data.get("autostart")),
        "restart_on_crash": bool(data.get("restart_on_crash")),
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
            return "starting"
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
        with self.lock:
            for sid in list(self.state):
                if sid not in self.services:
                    del self.state[sid]
                    continue
                st = self.state[sid]
                st.pop("restart_at", None)
                if st.get("pid") and not self.running(sid):
                    st["pid"] = None
                    st["desired"] = "stopped"
            for sid, svc in self.services.items():
                if svc.get("autostart") and not self.running(sid):
                    try:
                        self.log(sid, "autoarranque al iniciar NovaHub")
                        self.spawn(sid)
                    except Exception as e:  # noqa: BLE001
                        self.log(sid, f"\x1b[31mno se pudo iniciar: {e}\x1b[0m")
            self.save_state()

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

        self.log(sid, f"iniciando \x1b[2m$ {svc['command']}\x1b[0m")
        # O_RDWR: el hijo mantiene un escritor abierto, así nunca recibe EOF
        # y el panel puede escribir en el FIFO cuando quiera.
        stdin_fd = os.open(fifo, os.O_RDWR)
        try:
            with open(path, "ab") as logf:
                proc = subprocess.Popen(
                    [SHELL, "-lc", svc["command"]],
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
            st.update(desired="stopped", crashed=False, restart_at=None)
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
            try:
                with self.lock:
                    self._check_all(rotate=tick % 30 == 0)
            except Exception:  # noqa: BLE001
                traceback.print_exc()

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

            if not st.get("pid") or self.running(sid):
                continue

            # El proceso ha terminado sin que lo pidiéramos.
            code = self._reap(sid)
            st.update(pid=None, last_exit=code, last_exit_at=now)
            color = "32" if code == 0 else "31"
            self.log(sid, f"\x1b[{color}mel proceso ha terminado"
                          + (f" (código {code})" if code is not None else "") + "\x1b[0m")
            if st.get("desired") == "running" and svc.get("restart_on_crash") and code != 0:
                recent = [t for t in st.get("restarts", []) if now - t < 60]
                if len(recent) < MAX_AUTO_RESTARTS:
                    recent.append(now)
                    st["restarts"] = recent
                    delay = 2 * len(recent)
                    st["restart_at"] = now + delay
                    self.log(sid, f"reinicio automático en {delay} s "
                                  f"(intento {len(recent)}/{MAX_AUTO_RESTARTS})")
                else:
                    st.update(crashed=True, desired="stopped")
                    self.log(sid, "\x1b[31mdemasiados fallos seguidos, se deja de reintentar\x1b[0m")
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
            self.services[sid] = svc
            self.save_services()
            return sid

    def update(self, sid, data, extra=None):
        svc = {**normalize_service(data), **(extra or {})}
        with self.lock:
            self.services[sid] = {**self.services[sid], **svc}
            self.save_services()

    def delete(self, sid):
        with self.lock:
            if self.running(sid) or sid in self.transition:
                raise ApiError(409, "Detén el servicio antes de eliminarlo")
            self.services.pop(sid, None)
            self.state.pop(sid, None)
            self.save_services()
            self.save_state()
            for path in (log_path(sid), log_path(sid) + ".1", fifo_path(sid)):
                try:
                    os.remove(path)
                except FileNotFoundError:
                    pass

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
            listening=(svc["port"] in ports) if svc.get("port") else None,
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

class Auth:
    ITERATIONS = 600_000

    def __init__(self):
        self.data = read_json(AUTH_FILE, {})
        self.fails = {}  # ip -> [timestamps]

    def configured(self):
        return bool(self.data.get("password"))

    def set_password(self, password):
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), self.ITERATIONS).hex()
        # Un secreto nuevo invalida todas las sesiones abiertas.
        self.data = {"password": f"pbkdf2_sha256${self.ITERATIONS}${salt}${digest}",
                     "secret": secrets.token_hex(32)}
        write_json(AUTH_FILE, self.data, mode=0o600)

    def check_password(self, password):
        try:
            _, iterations, salt, digest = self.data["password"].split("$")
        except (KeyError, ValueError):
            return False
        test = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return hmac.compare_digest(test, digest)

    def _sign(self, payload):
        return hmac.new(self.data["secret"].encode(), payload.encode(), hashlib.sha256).hexdigest()

    def make_token(self):
        payload = str(int(time.time()) + SESSION_TTL)
        return f"{payload}.{self._sign(payload)}"

    def valid_token(self, token):
        if not token or "." not in token or not self.configured():
            return False
        payload, sig = token.rsplit(".", 1)
        if not hmac.compare_digest(sig, self._sign(payload)):
            return False
        return payload.isdigit() and int(payload) > time.time()

    def throttled(self, ip):
        now = time.time()
        self.fails[ip] = [t for t in self.fails.get(ip, []) if now - t < 300]
        return len(self.fails[ip]) >= 5

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

        target = f"http://localhost:{new['port']}" if new_host else None
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


# ───────────────────────────── HTTP ─────────────────────────────

MANAGER: Manager
AUTH: Auth
PUBLISHER: Publisher
SERVICE_ROUTE = re.compile(r"/api/services/([a-z0-9-]+)(?:/(start|stop|restart|input|logs/stream|logs/clear|logs/download))?")


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
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        self.common_headers()
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
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

    def session_cookie(self, value, max_age):
        parts = [f"nh_session={value}", "Path=/", "HttpOnly", "SameSite=Strict", f"Max-Age={max_age}"]
        if self.is_https():
            parts.append("Secure")
        return "; ".join(parts)

    def authed(self):
        cookie = SimpleCookie(self.headers.get("Cookie") or "")
        morsel = cookie.get("nh_session")
        return AUTH.valid_token(morsel.value if morsel else None)

    # ── enrutado ──
    def route(self, method):
        path = urlparse(self.path).path
        try:
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
            if not AUTH.check_password(str(self.read_body().get("password") or "")):
                AUTH.failed(ip)
                raise ApiError(401, "Contraseña incorrecta")
            return self.send_json({"ok": True}, cookie=self.session_cookie(AUTH.make_token(), SESSION_TTL))
        if path == "/api/logout" and method == "POST":
            return self.send_json({"ok": True}, cookie=self.session_cookie("", 0))

        if not self.authed():
            raise ApiError(401, "No autorizado")

        if path == "/api/me":
            return self.send_json({"ok": True})
        if path == "/api/system":
            return self.send_json(system_info())
        if path == "/api/services":
            if method == "GET":
                return self.send_json({"services": MANAGER.list_public()})
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
                return self.send_json(MANAGER.get_public(sid))
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
        if action == "logs/download" and method == "GET":
            return self.download_log(sid)
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
        return self.send_json(MANAGER.get_public(sid))

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


def main():
    global MANAGER, AUTH, PUBLISHER
    parser = argparse.ArgumentParser(description="NovaHub — gestor de servicios")
    parser.add_argument("command", nargs="?", default="serve", choices=["serve", "set-password"])
    parser.add_argument("--host", default=os.environ.get("NOVAHUB_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("NOVAHUB_PORT", "8686")))
    args = parser.parse_args()

    for d in (DATA_DIR, LOG_DIR, RUN_DIR):
        os.makedirs(d, mode=0o700, exist_ok=True)

    AUTH = Auth()
    if args.command == "set-password":
        AUTH.set_password(ask_password())
        print("Contraseña guardada. Las sesiones abiertas se han cerrado.")
        return
    if not AUTH.configured():
        if not sys.stdin.isatty():
            sys.exit("No hay contraseña configurada. Ejecuta primero: python3 server.py set-password")
        print("Primera ejecución: elige la contraseña del panel.")
        AUTH.set_password(ask_password())

    seed_example()
    PUBLISHER = Publisher()
    MANAGER = Manager()
    MANAGER.boot()
    threading.Thread(target=MANAGER.monitor, daemon=True).start()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.daemon_threads = True
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown).start())
    print(f"NovaHub escuchando en http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    print("NovaHub detenido (los servicios siguen en marcha).")


if __name__ == "__main__":
    main()
