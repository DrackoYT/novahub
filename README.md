# NovaHub

Panel web para encender, apagar y vigilar los servicios de tu servidor con un clic.

- Tarjetas con estado en vivo, etiquetas, filtro y buscador.
- Ficha de cada servicio: PID, tiempo activo, CPU, RAM, puerto (comprueba si está escuchando), última salida…
- Consola en directo con colores, y caja para **enviar comandos** al proceso (stdin).
- Reinicio automático si se cae, autoarranque al iniciar el panel y comando de parada suave (p. ej. `stop` en Minecraft).
- Los servicios **siguen funcionando aunque reinicies o actualices el panel**: al volver los recupera.
- Sin dependencias: solo Python 3.9+.

## Puesta en marcha

```bash
cd ~/novahub
python3 server.py set-password     # elige la contraseña del panel
python3 server.py                  # http://127.0.0.1:8686
```

Opciones: `--host` y `--port` (o las variables `NOVAHUB_HOST` / `NOVAHUB_PORT`).
Los datos se guardan en `data/` (servicios, estado, logs y contraseña cifrada).

### Dejarlo siempre encendido (systemd)

```bash
mkdir -p ~/.config/systemd/user
cp novahub.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now novahub
sudo loginctl enable-linger $USER    # que arranque con el servidor sin iniciar sesión
```

Logs del propio panel: `journalctl --user -u novahub -f`.

## Publicarlo con Cloudflare Tunnel

El panel escucha solo en `127.0.0.1`; Cloudflare se conecta desde dentro del servidor, así que no hace falta abrir puertos.

1. Instala `cloudflared` y autentícate: `cloudflared tunnel login`
2. Crea el túnel y el DNS:
   ```bash
   cloudflared tunnel create novahub
   cloudflared tunnel route dns novahub panel.tudominio.com
   ```
3. `~/.cloudflared/config.yml`:
   ```yaml
   tunnel: novahub
   credentials-file: /home/sergi/.cloudflared/<ID-DEL-TUNEL>.json
   ingress:
     - hostname: panel.tudominio.com
       service: http://localhost:8686
     - service: http_status:404
   ```
4. `cloudflared tunnel run novahub` (o `sudo cloudflared service install` para dejarlo como servicio).

> ⚠️ Quien entre al panel puede ejecutar comandos en tu servidor. Usa una contraseña larga y,
> si puedes, añade **Cloudflare Access** (Zero Trust → Access → Applications) delante del
> dominio para exigir tu email/Google antes de llegar siquiera al login.

## Consejos para los servicios

- **El comando** se ejecuta con `bash -lc` dentro del directorio de trabajo, así que funcionan
  `source venv/bin/activate && python bot.py`, `npm run start`, `java -Xmx4G -jar server.jar nogui`, etc.
- **No uses comandos que se vayan a segundo plano** (`&`, `nohup`, `--daemon`, `pm2 start`…):
  el panel tiene que ser el que mantenga vivo el proceso para poder vigilarlo y pararlo.
- **Si la consola tarda en mostrar la salida**, el programa está acumulando la salida en un buffer.
  Python ya va sin buffer (`PYTHONUNBUFFERED=1`); en otros casos prueba `stdbuf -oL tu-comando`.
- **Puerto**: si lo indicas, la tarjeta muestra en verde si realmente está escuchando.
  Es la forma más fiable de saber si el servicio "ha arrancado de verdad".

## Estructura

```
server.py          backend (API + gestor de procesos + consola por SSE)
static/            interfaz web (HTML/CSS/JS sin frameworks)
novahub.service    unidad de systemd
data/              se crea al arrancar (no subir a git)
```
