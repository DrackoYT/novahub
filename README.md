# NovaHub

Panel web para encender, apagar y vigilar los servicios de tu servidor con un clic.

- Tarjetas con estado en vivo, etiquetas, filtro y buscador.
- Ficha de cada servicio: PID, tiempo activo, CPU, RAM, puerto (comprueba si está escuchando), última salida…
- Consola en directo con colores, y caja para **enviar comandos** al proceso (stdin).
- Reinicio automático si se cae, autoarranque al iniciar el panel y comando de parada suave (p. ej. `stop` en Minecraft).
- Los servicios **siguen funcionando aunque reinicies o actualices el panel**: al volver los recupera.
- **Vigilancia**: comprobación de salud (HTTP o puerto) y límite de memoria con reinicio automático.
- **Publicar en internet** con un subdominio a través de Cloudflare Tunnel, con página «Reiniciando…»
  (503) mientras el servicio no responde.
- **Desplegar desde GitHub** (clonar, instalar dependencias, «Actualizar» con un botón) y **plantillas**
  para empezar proyectos nuevos (web, React + Vite, API, bot de Discord, Flask, Minecraft).
- Por servicio: **explorador y editor de archivos** (resaltado de código, Ctrl+S, aviso de conflictos y
  copia de seguridad automática en `data/backups/`) y **Git** (commit, subir y traer cambios).
- **Procesos**: qué usa la memoria y la CPU del servidor, agrupado por aplicación.
- Tema claro y oscuro. Sin dependencias: solo Python 3.9+.

## Puesta en marcha

```bash
cd ~/projectes/novahub            # o donde lo hayas clonado (ajusta también novahub.service)
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

### Publicar servicios desde el panel

Con el túnel funcionando, el panel puede dar a cada servicio su propia dirección pública:

1. Añade tu dominio a la unidad de systemd (`~/.config/systemd/user/novahub.service`):
   ```ini
   Environment=NOVAHUB_DOMAIN=tudominio.com
   ```
   y recarga: `systemctl --user daemon-reload && systemctl --user restart novahub`.
2. Crea en el panel un servicio para el túnel con el comando `cloudflared tunnel run novahub`
   (autoarranque + reiniciar si se cae).
3. En cada servicio con puerto aparece el campo **Publicar en internet**: escribe un subdominio
   (p. ej. `mi-app`) y al guardar el panel crea el CNAME `mi-app.tudominio.com`, añade la regla al
   `config.yml` del túnel, rellena la URL del servicio y reinicia el túnel.

Opcionales: `NOVAHUB_TUNNEL` (si no, se usa el `tunnel:` del config) y `NOVAHUB_CLOUDFLARED_CONFIG`
(por defecto `~/.cloudflared/config.yml`). Al despublicar o eliminar un servicio se quita su regla
del túnel, pero **el registro DNS se queda** en Cloudflare (cloudflared no puede borrarlo): bórralo
a mano en *DNS → Records* si ya no lo quieres.

## Sesión

En **⚙ Ajustes → Sesión**: pedir la contraseña al recargar la página (activado por defecto), cerrar la
sesión tras X minutos sin usar el panel (15 por defecto; las actualizaciones automáticas de la pantalla
no cuentan como uso) y una duración máxima (12 h). La cookie es de sesión del navegador y cerrar sesión
invalida el token en el servidor.

## Modo producción para webs

En la ficha de un servicio con `npm run build` (Vite, React, Vue…), **Modo → Pasar a producción**:
NovaHub compila la web y la sirve con `serve.py`, un servidor estático propio (sin dependencias) con
soporte para rutas de SPA, caché larga para los archivos con huella y compresión gzip. Gasta una
fracción de la memoria del modo desarrollo (≈20 MB frente a ≈300 MB en una web Vite). «Recompilar»
aplica los cambios del código; «Actualizar» desde GitHub recompila solo; «Volver a desarrollo»
recupera el comando original. El puerto llega por la variable `NOVAHUB_SERVICE_PORT`.

## Gráficas de uso

En **Resumen** (todo el servidor) y en la ficha de cada servicio hay dos gráficas, CPU y memoria, con
selector **1 h / 24 h**. Al pasar el ratón (o el dedo) se ve el valor de cada momento.

- Una muestra cada 10 s para la gráfica de 1 h y una media cada 5 min para la de 24 h. Se guardan en
  `data/metrics.json` cada 5 min y al cerrar NovaHub, así que sobreviven a un reinicio.
- La CPU del servidor es el % del total; la de un servicio, % de un núcleo (como en `top`: 200 % = dos
  núcleos llenos). En la memoria de un servicio con límite se dibuja el límite como línea roja.
- Los huecos son ratos en que el servicio estaba parado (o NovaHub apagado).

## Copias de seguridad

Pestaña **Copias** en la ficha de cada servicio:

- **Dónde:** en el disco duro de datos (HDD, `/mnt/dades/novahub-copias/<servicio>/`), no en el SSD
  del sistema, para que un fallo del SSD no se lleve también las copias. Si el disco no está montado,
  NovaHub no hace la copia (no escribe en el SSD por error) y avisa. Se puede cambiar con
  `NOVAHUB_BACKUP_DIR` y `NOVAHUB_BACKUP_MOUNT`.
- **Nombre:** `bk_DDMMAA_HHMMSS_tipo.tar.gz`, p. ej. `bk_061026_040000_auto.tar.gz` (copia del 6/10/26).
  El panel muestra la fecha corta (`bk_061026`) en la lista y en la tarjeta del servicio («Copia»).
- **Cuándo:** a mano («Hacer copia ahora») o automáticas cada día a una hora o cada X horas.
- **Qué:** toda la carpeta o solo algunas subcarpetas, sin lo que se regenera (`node_modules`, `.git`,
  `.venv`…). Opción de parar el servicio durante la copia (juegos, bases de datos).
- **Retención:** se guardan las N últimas automáticas y las 3 últimas «antes de restaurar»; las manuales
  solo se borran a mano.
- **Restaurar:** para el servicio, guarda antes una copia del estado actual, deja la carpeta como en la
  copia (sin tocar lo excluido) y lo vuelve a arrancar. También se pueden descargar y borrar.

## Fiabilidad de NovaHub

- **Watchdog de systemd** (`Type=notify`, `WatchdogSec=30` en `novahub.service`): NovaHub avisa a systemd
  cada 10 s mientras su web, su pasarela y sus bucles internos responden; si algo se queda colgado,
  systemd lo reinicia. Tus servicios no se tocan (`KillMode=process`).
- **Hilos vigilados**: si muere el de correo, salud, pasarela o vigilancia, se relanza y se avisa.
- **Reinicios tras un fallo**: NovaHub sabe si la vez anterior se cerró bien; si no, te escribe
  («se ha reiniciado tras un fallo», o «el servidor se ha encendido tras un apagado inesperado»).
- **Autoarranque** = al encender el servidor. Si solo se reinicia NovaHub, lo que apagaste sigue apagado.
- **Vigilante externo** (healthchecks.io u otro servicio con dirección de ping): en ⚙ Ajustes. NovaHub
  manda una señal de vida cada minuto solo si todo responde; si dejan de llegar (corte de luz, sin
  internet, servidor colgado), el servicio externo te avisa. Configura allí 1 min de periodo y 3 de gracia.
- **Túnel**: arranca con `--metrics 127.0.0.1:20241` y su comprobación de salud usa `/ready`, que solo
  responde 200 si hay conexión con Cloudflare.

## Avisos por correo (Gmail)

En **⚙ Ajustes** de la cabecera: tu Gmail, una *contraseña de aplicación* (créala en
<https://myaccount.google.com/apppasswords>; necesita la verificación en dos pasos) y qué avisos quieres:
caídas, servicios que no responden, exceso de memoria, encendido/apagado del servidor y actualizaciones
fallidas. Cada correo incluye las últimas líneas de la consola y un enlace a la ficha del servicio.
Como mucho un correo por servicio y tipo de aviso cada 10 minutos (y 30 por hora en total).
La configuración se guarda en `data/notify.json` (permisos 600). Para los enlaces se usa la dirección
pública del panel según el túnel, o `NOVAHUB_PUBLIC_URL` si la defines.

## Apagar el servidor (y el enchufe Tapo)

El botón ⏻ de la barra superior para todos los servicios (con su comando de parada), programa en el
enchufe Tapo un corte de corriente dentro de 90 s y apaga el servidor con `systemctl poweroff`.
Se habla con el enchufe por la red local: no hace falta Alexa ni la nube.

1. **Permiso para apagar** (una vez):
   ```bash
   echo "$USER ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff" | sudo tee /etc/sudoers.d/novahub-poweroff
   sudo chmod 440 /etc/sudoers.d/novahub-poweroff && sudo visudo -c
   ```
2. **Enchufe Tapo** (opcional; sin él el servidor se apaga igual pero el enchufe sigue encendido):
   ```bash
   python3 -m venv --without-pip .venv
   curl -fsSL https://bootstrap.pypa.io/get-pip.py | .venv/bin/python
   .venv/bin/pip install python-kasa
   ```
   Crea `data/tapo.json` con la IP del enchufe (fíjala en el router) y tu cuenta Tapo, y protégelo:
   ```json
   {"host": "192.168.0.50", "username": "email@cuenta-tapo", "password": "..."}
   ```
   `chmod 600 data/tapo.json`, y comprueba: `.venv/bin/python tapo.py status` y `.venv/bin/python tapo.py test`
   (programa un «encender» inofensivo en 30 s para verificar que el enchufe acepta cuentas atrás).
3. **Encendido automático**: en la BIOS activa *Restore on AC Power Loss → Power On*. Así, al encender el
   enchufe (app Tapo, Alexa o botón) el servidor arranca solo, y NovaHub levanta los servicios con autoarranque.

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
