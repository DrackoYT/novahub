#!/usr/bin/env python3
"""Actualiza NovaHub desde fuera de NovaHub (NovaHub lo lanza y se reinicia).

1. Copia de los datos (data/*.json).   2. git: la versión nueva.   3. Comprueba que el código nuevo compila.
4. Reinicia el servicio de systemd.     5. Espera a que la versión nueva responda.
Si algo falla, vuelve a la versión anterior (código y datos), la reinicia y lo deja anotado.

NovaHub copia este archivo fuera del repositorio antes de ejecutarlo: así git puede cambiarlo sin problema.
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def git(base, *args, check=True):
    res = subprocess.run(["git", "-C", base, *args], capture_output=True, text=True, timeout=180,
                         env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"})
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {(res.stderr or res.stdout).strip()}")
    return res.stdout.strip()


def healthy(port, run_file, commit, timeout):
    """La versión nueva está en marcha: el panel responde y ha anotado que arrancó con ese commit."""
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(2)
        try:
            with open(run_file) as f:
                running = json.load(f)
            if running.get("commit") != commit:
                continue
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/me", timeout=5)
        except urllib.error.HTTPError as e:
            if e.code == 401:  # responde (sin sesión): está viva
                return True
        except (OSError, ValueError):
            continue
        else:
            return True
    return False


def restart(unit):
    subprocess.run(["systemctl", "--user", "restart", unit], capture_output=True, timeout=60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--target", required=True, help="commit al que actualizar")
    ap.add_argument("--branch", default="", help="rama si es el canal de desarrollo (vacío = versión estable)")
    ap.add_argument("--label", default="")
    ap.add_argument("--port", type=int, default=8686)
    ap.add_argument("--unit", default="novahub")
    a = ap.parse_args()
    result_file = os.path.join(a.data, "update-result.json")
    run_file = os.path.join(a.data, "running.json")
    prev = git(a.base, "rev-parse", "HEAD")
    prev_branch = git(a.base, "symbolic-ref", "--short", "-q", "HEAD", check=False)
    started = time.time()

    def finish(ok, msg):
        with open(result_file, "w") as f:
            json.dump({"ok": ok, "msg": msg, "from": prev[:7], "to": a.target[:7], "label": a.label,
                       "started": started, "finished": time.time()}, f)
        log(msg)
        sys.exit(0 if ok else 1)

    # 1. copia de los datos (sin logs ni copias)
    backups = os.path.join(a.data, "update-backups")
    os.makedirs(backups, mode=0o700, exist_ok=True)
    backup = os.path.join(backups, f"{time.strftime('%Y%m%d-%H%M%S')}-{prev[:7]}.tar.gz")
    with tarfile.open(backup, "w:gz") as tar:
        for f in glob.glob(os.path.join(a.data, "*.json")):
            tar.add(f, arcname=os.path.basename(f))
    os.chmod(backup, 0o600)
    for old in sorted(glob.glob(os.path.join(backups, "*.tar.gz")))[:-5]:
        os.remove(old)
    log(f"copia de los datos: {backup}")

    def rollback(reason):
        log(f"falla ({reason}): vuelvo a la versión anterior")
        try:
            if prev_branch:
                git(a.base, "checkout", "-q", prev_branch)
                git(a.base, "reset", "-q", "--keep", prev)
            else:
                git(a.base, "checkout", "-q", "--detach", prev)
            with tarfile.open(backup) as tar:
                tar.extractall(a.data, filter="data")
            restart(a.unit)
            if healthy(a.port, run_file, prev, 90):
                finish(False, f"La actualización falló ({reason}). Se ha vuelto a la versión anterior.")
            finish(False, f"La actualización falló ({reason}) y la versión anterior tampoco responde: revisa journalctl --user -u {a.unit}")
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            finish(False, f"La actualización falló ({reason}) y no se pudo volver atrás: {e}")

    # 2. la versión nueva
    try:
        if a.branch:
            if prev_branch != a.branch:
                git(a.base, "checkout", "-q", a.branch)
            git(a.base, "merge", "-q", "--ff-only", a.target)
        else:
            git(a.base, "checkout", "-q", "--detach", a.target)
        log(f"código en {a.label or a.target[:7]}")
    except Exception as e:  # noqa: BLE001
        rollback(str(e))

    # 3. que el código nuevo al menos compile antes de reiniciar
    res = subprocess.run([sys.executable, "-m", "py_compile", os.path.join(a.base, "server.py")], capture_output=True, text=True)
    if res.returncode != 0:
        rollback("el código nuevo no compila")

    # 4 y 5. reiniciar y comprobar
    log("reiniciando NovaHub…")
    restart(a.unit)
    if healthy(a.port, run_file, git(a.base, "rev-parse", "HEAD"), 90):
        finish(True, f"NovaHub actualizado a {a.label or a.target[:7]}")
    rollback("la versión nueva no responde en 90 s")


if __name__ == "__main__":
    main()
