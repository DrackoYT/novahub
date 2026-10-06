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
Se sirve una copia de la compilación (`data/builds/<servicio>/current`), no la carpeta `dist/`: mientras se
recompila, o si la compilación falla, la web publicada sigue funcionando con la versión anterior.

## App para el móvil

NovaHub se instala como app (PWA): icono en la pantalla de inicio y se abre a pantalla completa, sin la barra
del navegador. Sigue yendo por el túnel (https://novahub.novaasist.dev), con Cloudflare Access y la contraseña.

- **Android (Chrome):** Ajustes → «Instalar NovaHub», o menú ⋮ → «Instalar aplicación».
- **iPhone (Safari):** Compartir → «Añadir a pantalla de inicio».

La interfaz queda guardada en el móvil (`static/sw.js`), así que abre aunque no haya conexión y avisa de que
no puede hablar con el servidor; reintenta sola. Los datos (la API) nunca se guardan: siempre vienen del
servidor. Con «Pedir la contraseña al recargar» activado, la app la pide cada vez que se abre.
Los iconos se generan con `python3 tools/make_icons.py`.

## Vista de red

Pestaña **Red** (tecla `4`):

- **Túnel:** conexiones activas con Cloudflare, centros a los que está conectado (p. ej. `mad05 · mad07`),
  peticiones y errores del servidor (respuestas 5xx). Se leen del servidor de métricas de cloudflared, así que el comando del túnel debe
  llevar `--metrics 127.0.0.1:PUERTO`.
- **Servidor:** IP en la red local y dominio de publicación.
- **Enchufe Tapo:** encendido o apagado, consumo en vatios en este momento (P110/P115), kWh de hoy y del
  mes, desde cuándo está encendido y calidad del Wi-Fi. Se consulta como mucho una vez por minuto.
- **Dominios publicados:** cada regla del `config.yml` del túnel con el servicio al que lleva, su estado
  y si pasa por la pasarela de NovaHub.

## Gráficas de uso

En **Resumen** (todo el servidor) y en la ficha de cada servicio hay dos gráficas, CPU y memoria, con
selector **1 h / 24 h**. Al pasar el ratón (o el dedo) se ve el valor de cada momento.

- Una muestra cada 10 s para la gráfica de 1 h y una media cada 5 min para la de 24 h. Se guardan en
  `data/metrics.json` cada 5 min y al cerrar NovaHub, así que sobreviven a un reinicio.
- La CPU del servidor es el % del total; la de un servicio, % de un núcleo (como en `top`: 200 % = dos
  núcleos llenos). En la memoria de un servicio con límite se dibuja el límite como línea roja.
- Los huecos son ratos en que el servicio estaba parado (o NovaHub apagado).

## Contenedores (Podman)

Además de programas (un comando), un servicio puede ser un **contenedor** (una imagen de Docker Hub u otro
registro) o un proyecto **docker-compose**. Nuevo servicio → **Contenedor**, o el selector «Tipo» del formulario.

Se usa **Podman sin root**: los contenedores corren como tu usuario, sin servicio de root ni grupo `docker`
(que equivaldría a dar root a quien controle el panel). Instalación:

```bash
sudo apt install -y podman podman-compose passt uidmap
```

- **Contenedor:** imagen (p. ej. `louislam/uptime-kuma:1`), puerto del servidor y del contenedor, carpetas
  (`data:/app/data`; las relativas van dentro del directorio del servicio, que se crea solo) y variables de
  entorno, que se pasan sin aparecer en la lista de procesos. Ejemplos listos: Uptime Kuma, web estática con
  nginx y Minecraft (Paper).
- **Compose:** el directorio del servicio con su `compose.yaml` o `docker-compose.yml`. Los logs de todos los
  contenedores salen en la consola, cada uno con su nombre.
- Se vigilan como cualquier servicio: consola (también para escribirles), reinicio si se caen, comprobación
  de salud, límite de memoria, gráficas, tareas programadas, copias de seguridad y publicación en internet.
  La CPU y la memoria se leen de su cgroup, porque sus procesos no son hijos de NovaHub.
- **Actualizar imagen** descarga la versión nueva y reinicia solo si ha cambiado.
- Al parar, el contenedor recibe su señal de parada con el tiempo de «Espera»; después se elimina (los datos
  quedan en sus carpetas).

## Identidad de git

Los commits que se hacen desde el panel (pestaña Git) se firman con el nombre y el correo de
**Ajustes → Git**, que es la configuración global de git del usuario (`git config --global user.name/user.email`).
Si no están puestos, el commit avisa en vez de inventarse un autor.

## Variables (.env)

Pestaña **Variables** en la ficha: el `.env` del proyecto como tabla nombre → valor, con los valores ocultos
(el ojo muestra cada uno). Se puede elegir otro archivo (`.env.local`, `.env.production`…) y crear el `.env` si
no existe.

- Conserva comentarios, líneas en blanco y el formato de lo que no cambia; lo nuevo va al final. Pone comillas
  cuando hace falta (espacios, `#`, comillas…).
- Guarda la versión anterior (como el editor) y avisa si el archivo cambió desde que lo abriste.
- Un `.env` nuevo se crea con permisos 600 (solo tu usuario).
- **Aviso si el archivo iría a GitHub**: si no está en `.gitignore` o ya está en el repositorio.
- Si una variable está repetida, cuenta la última (como en dotenv y en el shell) y al guardar queda una.
- Casi todos los programas leen el `.env` al arrancar: tras guardar sale «Reiniciar para aplicar».

Las variables que se ponen en «Editar» del servicio son otra cosa: las pasa NovaHub al arrancarlo y se guardan
en `data/services.json`.

## Buscar en los logs

En la consola de cada servicio, el campo **Buscar en todo el log** (o la tecla `/`) busca en el log entero,
el actual y el anterior rotado, no solo en lo que hay en pantalla. Muestra las coincidencias con su número de
línea y resaltadas (las 500 más recientes), y se actualiza solo mientras está abierta.

- **Solo errores:** líneas con palabras de error (error, failed, exception, traceback, rechazada…) o que el
  programa pinta en rojo, como los fallos que anota NovaHub.
- **`.*`** para expresiones regulares y **Aa** para distinguir mayúsculas.
- `Esc` o ✕ vuelven a la consola en directo.

## Tareas programadas

Pestaña **Tareas** en la ficha de cada servicio. Cada tarea es una acción a una hora, ciertos días de la semana:

- **Encender, apagar o reiniciar.** Para que un servicio solo funcione en un horario, dos tareas:
  encender a las 09:00 y apagar a las 23:00.
- **Escribir en la consola** del proceso (p. ej. `say Reinicio en 5 minutos` en Minecraft).
- **Ejecutar un comando** en la carpeta del servicio, con sus variables de entorno. Se corta a los 10 min.

Se ejecutan aunque no tengas el panel abierto; lo que pasa queda en la consola del servicio y, si una
falla, llega un aviso por correo. «Probar» la lanza en el momento. Si NovaHub estaba reiniciándose justo
a esa hora, la tarea se lanza igualmente hasta 3 minutos tarde (nunca dos veces).

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
static/            interfaz web (HTML/CSS/JS sin frameworks) y app para el móvil (manifiesto, sw.js, iconos)
serve.py           servidor estático del modo producción
logsearch.py       búsqueda en los logs (las expresiones regulares van en un proceso aparte con límite de tiempo)
tapo.py            control del enchufe Tapo
tools/             utilidades (generar los iconos de la app)
novahub.service    unidad de systemd
data/              se crea al arrancar (no subir a git)
```
