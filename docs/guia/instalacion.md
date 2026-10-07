# Instalación

Necesitas Linux con **systemd** y **Python 3.11.4 o superior** (Debian 12/13, Ubuntu 24.04, Raspberry Pi OS…).

```bash
git clone https://github.com/DrackoYT/novahub ~/novahub
cd ~/novahub
python3 server.py set-password     # crea el usuario administrador
python3 server.py                  # → http://127.0.0.1:8686
```

Para que arranque solo con el servidor (como servicio de usuario, sin root):

```bash
mkdir -p ~/.config/systemd/user
cp novahub.service ~/.config/systemd/user/     # revisa las rutas si no lo clonaste en ~/novahub
systemctl --user daemon-reload
systemctl --user enable --now novahub
sudo loginctl enable-linger $USER             # que arranque aunque no inicies sesión
journalctl --user -u novahub -f               # logs del panel
```

El panel escucha solo en `127.0.0.1`. Para entrar desde otros equipos, publícalo con Cloudflare Tunnel (abajo) o
pon `NOVAHUB_HOST` a la IP de la red local. Los datos (servicios, usuarios, logs, métricas) quedan en `data/`, con
permisos 600.

## Configuración

Todo se configura desde el panel salvo estas variables (en `novahub.service`):

| Variable | Para qué |
|---|---|
| `NOVAHUB_HOST`, `NOVAHUB_PORT` | Dónde escucha el panel (por defecto `127.0.0.1:8686`) |
| `NOVAHUB_DATA` | Carpeta de datos (por defecto `data/` junto a `server.py`) |
| `NOVAHUB_DOMAIN` | Dominio para «Publicar en internet» con Cloudflare Tunnel |
| `NOVAHUB_BACKUP_MOUNT` | Disco aparte para las copias (p. ej. `/mnt/datos`); si no está montado, no se copia |
| `NOVAHUB_BACKUP_DIR` | Carpeta de las copias (por defecto `<disco o data>/novahub-copias`) |
| `NOVAHUB_REMOTE_LISTEN` | Puerta para que otro panel maneje este servidor, p. ej. `100.x.y.z:8687` (Tailscale) |
| `NOVAHUB_PROJECTS` | Dónde se clonan los repositorios y las plantillas (por defecto `~/proyectos`) |

## Seguridad

El panel puede ejecutar comandos en el servidor, así que está pensado para estar detrás de algo más que una
contraseña: lo recomendado es **Cloudflare Access** (tu cuenta de Google) delante del túnel. Además: contraseñas con
PBKDF2, **verificación en dos pasos** opcional, sesiones firmadas que caducan por inactividad, protección CSRF,
permisos por rol comprobados en el servidor y nada escuchando fuera de `127.0.0.1`. El modelo completo y las revisiones de código están en
[`SECURITY.md`](../../SECURITY.md) y [`docs/REVISIONES.md`](../REVISIONES.md).
