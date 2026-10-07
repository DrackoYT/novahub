# Variables de entorno

Casi todo se configura desde el panel. Estas variables son para lo que hay que decidir antes de arrancar: se ponen en
la unidad de systemd (`~/.config/systemd/user/novahub.service`) con líneas `Environment=`, y después:

```bash
systemctl --user daemon-reload
systemctl --user restart novahub
```

## Panel

| Variable | Por defecto | Para qué |
|---|---|---|
| `NOVAHUB_HOST` | `127.0.0.1` | Dirección en la que escucha el panel. Déjala así si lo publicas con Cloudflare Tunnel |
| `NOVAHUB_PORT` | `8686` | Puerto del panel |
| `NOVAHUB_DATA` | `data/` junto a `server.py` | Servicios, usuarios, logs, métricas y ajustes (permisos 600) |
| `NOVAHUB_PUBLIC_URL` | se deduce | Dirección pública del panel para los enlaces de los avisos, p. ej. `https://novahub.midominio.com` |
| `NOVAHUB_UNIT` | `novahub` | Nombre de la unidad de systemd, para que el actualizador sepa qué reiniciar |
| `NOVAHUB_UPDATE_REPO` | se deduce del git | `usuario/repo` de GitHub del que se actualiza NovaHub |

## Publicar en internet

| Variable | Por defecto | Para qué |
|---|---|---|
| `NOVAHUB_DOMAIN` | vacío | Dominio para publicar servicios como `<subdominio>.<dominio>` |
| `NOVAHUB_TUNNEL` | el de `tunnel:` en el config | Nombre o ID del túnel de cloudflared |
| `NOVAHUB_CLOUDFLARED_CONFIG` | `~/.cloudflared/config.yml` | Archivo de configuración del túnel que NovaHub edita |

## Copias de seguridad

| Variable | Por defecto | Para qué |
|---|---|---|
| `NOVAHUB_BACKUP_MOUNT` | vacío | Disco aparte para las copias, p. ej. `/mnt/datos`. Si no está montado, no se copia |
| `NOVAHUB_BACKUP_DIR` | `<disco o data>/novahub-copias` | Carpeta de las copias de los servicios |
| `NOVAHUB_RESTIC` | el `restic` del sistema | Ruta de restic para las copias fuera de casa |
| `NOVAHUB_RESTORE_DIR` | `~/novahub-recuperado` | Dónde se sacan las copias fuera de casa al recuperarlas |

## Servicios y apps

| Variable | Por defecto | Para qué |
|---|---|---|
| `NOVAHUB_PROJECTS` | `~/proyectos` | Dónde se clonan los repositorios de GitHub y las plantillas |
| `NOVAHUB_APPS_DIR` | `~/apps` | Carpeta de las apps del catálogo |

## Varios servidores

| Variable | Por defecto | Para qué |
|---|---|---|
| `NOVAHUB_REMOTE_LISTEN` | vacío | Puerta para que otro panel maneje este servidor, p. ej. `100.x.y.z:8687` (Tailscale) |

## Herramientas personales

| Variable | Por defecto | Para qué |
|---|---|---|
| `NOVAHUB_ROADMAP` | vacío | Con `1`, activa la página oculta de mejoras y pendientes (`#/mejoras`) |

> [!WARNING]
> Si cambias `NOVAHUB_DATA` o `NOVAHUB_BACKUP_DIR` con datos ya creados, mueve antes las carpetas: NovaHub no las
> mueve solo.
