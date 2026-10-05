#!/usr/bin/env python3
"""Control local del enchufe Tapo que alimenta el servidor (sin Alexa ni la nube).

Necesita python-kasa en .venv (ver README) y data/tapo.json (permisos 600):
    {"host": "192.168.0.50", "username": "email@cuenta-tapo", "password": "..."}

Uso (con .venv/bin/python):
    tapo.py setup           pide IP, email y contraseña de Tapo y guarda data/tapo.json (bien escapado, 600)
    tapo.py check           muestra qué IP y cuenta hay guardadas (sin la contraseña)
    tapo.py status          estado del enchufe
    tapo.py test            programa una cuenta atrás inofensiva («encender» en 30 s) y la lista
    tapo.py off-in SEG      programa el corte de corriente dentro de SEG segundos
    tapo.py cancel          anula las cuentas atrás pendientes
"""

import asyncio
import getpass
import json
import logging
import os
import sys

from kasa import AuthenticationError, Credentials, Discover

# Si falla la identificación, la librería deja avisos internos («Unclosed client session») que solo confunden.
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

AUTH_HELP = """el enchufe ha rechazado el email o la contraseña. Revisa, por orden:
  1. App Tapo → Yo → Tapo Lab → «Compatibilidad con terceros» activada.
  2. Email y contraseña exactos de tu cuenta Tapo (distinguen mayúsculas). Vuelve a guardarlos con: tapo.py setup
  3. Si entras en la app con Google o Apple, tu cuenta no tiene contraseña: créala en la app (Yo → cuenta).
  4. Si cambiaste la contraseña hace poco, el enchufe guarda la antigua hasta reiniciarlo (desenchufar 10 s).
     Ojo: si alimenta al servidor, lo apagaría de golpe."""

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tapo.json")


def load_config():
    try:
        st = os.stat(CONFIG)
    except FileNotFoundError:
        sys.exit(f"Falta {CONFIG}")
    if st.st_mode & 0o077:
        sys.exit(f"{CONFIG} tiene la contraseña: déjalo solo para tu usuario (chmod 600)")
    try:
        with open(CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
    except ValueError as e:
        sys.exit(f"{CONFIG} no es un JSON válido ({e}). Vuelve a crearlo con: tapo.py setup")
    missing = [k for k in ("host", "username", "password") if not cfg.get(k)]
    if missing:
        sys.exit(f"Faltan campos en {CONFIG}: {', '.join(missing)}")
    return cfg


async def connect(cfg):
    dev = await Discover.discover_single(
        cfg["host"], credentials=Credentials(cfg["username"], cfg["password"]), timeout=10)
    await dev.update()
    return dev


async def rules(dev):
    """Cuentas atrás del enchufe. La respuesta llega envuelta en el nombre del método."""
    res = await dev._query_helper("get_countdown_rules")
    res = res.get("get_countdown_rules", res)
    return res.get("rule_list", [])


async def countdown(dev, seconds, on):
    """Programa la cuenta atrás. El P110 solo admite una: si ya hay, se modifica en vez de añadir otra."""
    rule = {"delay": seconds, "desired_states": {"on": on}, "enable": True, "remain": seconds}
    existing = await rules(dev)
    if existing:
        await dev._query_helper("edit_countdown_rule", {**rule, "id": existing[0]["id"]})
    else:
        await dev._query_helper("add_countdown_rule", rule)
    return await rules(dev)


def setup():
    """Guarda la configuración con json.dumps: comillas o barras en la contraseña no rompen el archivo."""
    host = input("IP del enchufe (app Tapo → enchufe → ⚙ → Información del dispositivo): ").strip()
    user = input("Email de tu cuenta Tapo: ").strip()
    password = getpass.getpass("Contraseña de Tapo (no se ve al escribir): ")
    if not (host and user and password):
        sys.exit("Faltan datos: no se ha guardado nada")
    fd = os.open(CONFIG, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"host": host, "username": user, "password": password}, f)
    os.chmod(CONFIG, 0o600)
    print(f"Guardado en {CONFIG}. Pruébalo con: tapo.py status")


async def main(argv):
    if not argv or argv[0] not in ("setup", "check", "status", "test", "off-in", "cancel"):
        sys.exit(__doc__)
    if argv[0] == "setup":
        return setup()
    cfg = load_config()
    if argv[0] == "check":
        pw = cfg["password"]
        print(f"IP: {cfg['host']}\nEmail: {cfg['username']}\nContraseña: {len(pw)} caracteres"
              + (" (¡ojo: empieza o acaba con espacio!)" if pw != pw.strip() else ""))
        return
    dev = await connect(cfg)
    try:
        cmd = argv[0]
        if cmd == "status":
            print(json.dumps({"model": dev.model, "alias": dev.alias, "on": dev.is_on}, ensure_ascii=False))
        elif cmd == "test":
            # «encender» con el enchufe ya encendido no hace nada: sirve para probar la API sin riesgo
            print(json.dumps(await countdown(dev, 30, True), ensure_ascii=False))
        elif cmd == "off-in":
            seconds = int(argv[1]) if len(argv) > 1 else 0
            if not 30 <= seconds <= 600:
                sys.exit("La espera debe estar entre 30 y 600 segundos")
            print(json.dumps(await countdown(dev, seconds, False), ensure_ascii=False))
        elif cmd == "cancel":
            pending = [r for r in await rules(dev) if r.get("enable")]
            for r in pending:
                await dev._query_helper("edit_countdown_rule", {**r, "enable": False})
            left = [r for r in await rules(dev) if r.get("enable")]
            if left:
                sys.exit(f"No se pudieron anular todas las cuentas atrás: {left}")
            print(f"{len(pending)} cuenta(s) atrás anulada(s)")
    finally:
        await dev.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main(sys.argv[1:]))
    except AuthenticationError:
        sys.exit(f"Error con el enchufe Tapo: {AUTH_HELP}")
    except Exception as e:  # noqa: BLE001
        sys.exit(f"Error con el enchufe Tapo: {e}")
