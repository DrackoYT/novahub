#!/usr/bin/env python3
"""Control local del enchufe Tapo que alimenta el servidor (sin Alexa ni la nube).

Necesita python-kasa en .venv (ver README) y data/tapo.json (permisos 600):
    {"host": "192.168.0.50", "username": "email@cuenta-tapo", "password": "..."}

Uso (con .venv/bin/python):
    tapo.py status          estado del enchufe
    tapo.py test            programa una cuenta atrás inofensiva («encender» en 30 s) y la lista
    tapo.py off-in SEG      programa el corte de corriente dentro de SEG segundos
    tapo.py cancel          anula las cuentas atrás pendientes
"""

import asyncio
import json
import os
import sys

from kasa import Credentials, Discover

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tapo.json")


def load_config():
    try:
        st = os.stat(CONFIG)
    except FileNotFoundError:
        sys.exit(f"Falta {CONFIG}")
    if st.st_mode & 0o077:
        sys.exit(f"{CONFIG} tiene la contraseña: déjalo solo para tu usuario (chmod 600)")
    with open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)
    missing = [k for k in ("host", "username", "password") if not cfg.get(k)]
    if missing:
        sys.exit(f"Faltan campos en {CONFIG}: {', '.join(missing)}")
    return cfg


async def connect(cfg):
    dev = await Discover.discover_single(
        cfg["host"], credentials=Credentials(cfg["username"], cfg["password"]), timeout=10)
    await dev.update()
    return dev


async def countdown(dev, seconds, on):
    rule = {"delay": seconds, "desired_states": {"on": on}, "enable": True, "remain": seconds}
    await dev._query_helper("add_countdown_rule", rule)
    return await dev._query_helper("get_countdown_rules")


async def main(argv):
    if not argv or argv[0] not in ("status", "test", "off-in", "cancel"):
        sys.exit(__doc__)
    cfg = load_config()
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
            rules = (await dev._query_helper("get_countdown_rules")).get("rule_list", [])
            for r in rules:
                await dev._query_helper("edit_countdown_rule", {**r, "enable": False})
            print(f"{len(rules)} cuenta(s) atrás anulada(s)")
    finally:
        await dev.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main(sys.argv[1:]))
    except Exception as e:  # noqa: BLE001
        sys.exit(f"Error con el enchufe Tapo: {e}")
