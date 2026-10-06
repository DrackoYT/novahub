# Registro de revisiones de código

Este documento dice **qué partes de NovaHub están revisadas, hasta qué commit y qué se comprobó**.
Sirve para que cada revisión nueva cubra solo lo que ha cambiado desde la anterior.

## Cómo saber qué hay que revisar

**Revisado hasta el commit: `92ee43d`** (se actualiza al cerrar cada revisión; editar este documento
por otros motivos no cambia este valor). Para ver lo que ha cambiado desde entonces:

```bash
BASE=92ee43d
git diff --stat "$BASE"..HEAD        # qué archivos han cambiado
git diff "$BASE"..HEAD -- server.py  # el detalle de un archivo
```

Todo lo que **no** aparezca en ese diff está revisado (ver el inventario). Si un cambio toca una
pieza marcada como *invariante de seguridad*, hay que revisar esa pieza entera, no solo el diff.

## Historial

| # | Fecha | Alcance | Commits cubiertos | Hallazgos |
|---|---|---|---|---|
| 1 | 2026-10-05 | **Completa**: todo el código | hasta `cad7b13` (incluido) | 9 corregidos |
| 2 | 2026-10-06 | **Incremental**: solo lo cambiado | `cad7b13..92ee43d` | 5 corregidos |

---

## Inventario: qué está revisado

Estado de cada pieza tras la revisión 2. Lo añadido después de `92ee43d` (modo producción, `serve.py`,
sesiones con caducidad por inactividad) está **pendiente de revisar**. «R1» = revisada entera en la revisión 1 y sin cambios
desde entonces; «R2» = cambiada después de R1 y revisada en la revisión 2.

### `server.py` (backend, ~3.200 líneas)

| Pieza | Estado | Notas |
|---|---|---|
| Utilidades (`read_json`, `write_json`, `proc_*`, `group_usage`, `listening_ports`, `lan_ip`, `system_info`, `slugify`) | R1 | `write_json` escribe con permisos 600 |
| `uptime`, `wait_for_network` | R2 | |
| `normalize_service` | R1 + R2 | R2: campos de una línea sin caracteres de control (salvo `command` y `description`) |
| `Manager`: `spawn`, `start`, `stop`, `_do_stop`, `restart`, stdin, `_rotate_live`, CRUD, `public` | R1 | `stop` cambia en R2: limpia `down_notified` |
| `Manager.boot`, `_autostart` | R2 | Autoarranque solo al encender el servidor; espera red; relanza los servicios que murieron con NovaHub caído |
| `Manager.monitor`, `_check_all`, `_check_memory` | R2 | Reintentos rápidos y luego lentos (nunca se abandona), avisos, aviso de recuperación |
| `Manager.status` | R2 | Estado nuevo `retrying` |
| `Auth` | R1 | Invariante de seguridad |
| `Publisher` (túnel, DNS, ingress) | R1 | |
| `Power` | R1 + R2 | R2: correo de apagado antes de programar el corte del enchufe |
| Archivos: `service_root`, `safe_path`, `list_dir`, `read_file` | R1 | Invariante de seguridad |
| Git: `git_*` | R1 | |
| `Tasks` (procesos) | R1 | |
| `Health` | R1 + R2 | R2: latido del supervisor en cada comprobación; avisos por correo |
| `Gateway` (pasarela y página 503) | R1 + R2 | R2: su hilo lo lanza el supervisor |
| `Roadmap` | R1 | |
| Correo: `Notifier`, `email_html`, `make_orb_png`, `log_tail`, `strip_ansi` | R2 | |
| Vigilancia: `Supervisor`, `sd_notify`, `previous_run`/`mark_run`, `journal_tail`, `startup_notice`, `_boot_report` | R2 | |
| Despliegue: `gh_repos`, `detect_project`, `project_dir`, `install_steps`, `Deployer` | R1 | `Deployer._update` cambia en R2 solo para avisar |
| Plantillas (`TEMPLATES`, `template_create`, `_template_job`, `download_paper`) | R1 | |
| `Handler` (rutas, cabeceras, cookies, estáticos, SSE) | R1 + R2 | R2: rutas `/api/notify` y `/api/notify/test` |
| `main`, `panel_url` | R2 | Orden de arranque con supervisor, `READY=1` y watchdog |

### Otros archivos

| Archivo | Estado | Notas |
|---|---|---|
| `static/app.js` | R1 + R2 | R2: ventana de ajustes (avisos y vigilante externo), estado `retrying` |
| `static/style.css` | R1 + R2 | R2: solo estilos de ajustes y del estado `retrying` |
| `static/index.html`, `static/theme.js` | R1 | |
| `static/favicon.svg`, `static/fonts/*` | — | Recursos estáticos, sin lógica |
| `tapo.py` | R1 + R2 | R2: `rules`, `countdown` con una sola cuenta atrás, `cancel` que verifica, `setup`, `check` |
| `novahub.service` | R2 | `Type=notify`, `NotifyAccess=main`, `WatchdogSec=30`, `KillMode=process` |
| `README.md` | R2 | Comprobado que describe lo que hace el código |
| `demo/` | — | Página de ejemplo, sin lógica |

---

## Invariantes de seguridad comprobados

Son propiedades que se verificaron con pruebas reales. Si un cambio toca su código, hay que volver
a comprobarlas.

1. **Autenticación**: sin cookie, con token falsificado, caducado o de una sesión cerrada, toda la API responde 401. Los tokens se
   firman con HMAC-SHA256 y un secreto de `data/auth.json`. La contraseña usa PBKDF2 con 600.000
   iteraciones. Máximo 5 intentos de login por IP cada 5 minutos.
2. **CSRF**: toda petición que no sea GET exige la cabecera `X-NovaHub: 1`, y la cookie es
   `HttpOnly` y `SameSite=Strict`. Ningún GET modifica estado.
3. **Rutas de archivos**: `safe_path` resuelve con `realpath` y rechaza todo lo que quede fuera de
   la carpeta del servicio, incluidos `../` y enlaces simbólicos. Los estáticos solo se sirven
   desde `static/`.
4. **XSS**: en `app.js`, todo dato del servidor pasa por `esc()` o se asigna con `textContent`. Las
   URL de servicio solo pueden ser `http(s)://`. En los correos, todo texto dinámico pasa por
   `html.escape`.
5. **Secretos**: los archivos de `data/` tienen permisos 600. La contraseña de aplicación de Gmail
   nunca se devuelve por la API. `tapo.json` exige 600.
6. **Superficie de red**: el panel y las pasarelas escuchan solo en `127.0.0.1`. Desde fuera se
   llega únicamente por el túnel, con Cloudflare Access (Google) delante.
7. **Peticiones malformadas**: si `Content-Length` es negativo o no numérico, la respuesta es 400 sin
   esperar más datos. El cuerpo admite como máximo 1 MB.
8. **Procesos**: desde el panel solo se pueden cerrar procesos del propio usuario. Los de un servicio
   se paran desde su ficha.

## Riesgos aceptados (decisiones conscientes)

- **Las sesiones cerradas solo se recuerdan en memoria**: si NovaHub se reinicia, un token cerrado
  antes de caducar volvería a valer hasta su caducidad (como mucho, el tiempo de inactividad: 15 min
  por defecto). Para llegar al panel hace falta además la cuenta de Google de Cloudflare Access.
- **El panel ejecuta comandos arbitrarios** y deja ver cualquier carpeta que se ponga como carpeta
  de un servicio. Es su función: la protección está en la entrada (Access y contraseña).
- **Los correos incluyen las últimas líneas de la consola**: si un servicio imprime secretos en su
  salida, viajarían a Gmail.
- **La dirección de healthchecks.io funciona como un token**: quien la conozca podría enviar señales
  falsas. Solo se muestra a usuarios autenticados.
- **Las webs publicadas dependen de NovaHub**, que hace de pasarela: si NovaHub se reinicia, se
  cortan 2 o 3 segundos. Los servicios no se ven afectados.
- **Clonar repositorios o usar plantillas ejecuta sus scripts de instalación** (`npm ci` y
  similares). Solo se clonan repositorios propios.

## Hallazgos y correcciones

### Revisión 2 (incremental, 2026-10-06)

| # | Problema | Riesgo | Corrección |
|---|---|---|---|
| 1 | El hilo de salud solo latía al empezar cada vuelta. Con varios servicios lentos (8 s cada uno) pasaba de 60 s sin latir, y el watchdog habría reiniciado NovaHub sin motivo | Medio | Latido antes de cada comprobación |
| 2 | Un error al generar un aviso rompía la vuelta de vigilancia que lo llamaba | Medio | `notify()` nunca lanza excepciones: las registra |
| 3 | Un nombre de servicio con saltos de línea rompía el asunto del correo | Bajo | Asunto en una línea; los campos de una línea se limpian de caracteres de control |
| 4 | Un servicio que murió con NovaHub caído quedaba parado sin relanzarse ni avisar | Medio | Si tiene «Reiniciar si se cae», se relanza y se avisa (salvo al encender el servidor, donde es lo normal) |
| 5 | El correo de apagado salía después de programar el corte del enchufe y podía comerse el margen de 90 s | Bajo | El correo se envía antes de programar el corte |

### Revisión 1 (completa, 2026-10-05)

| # | Problema | Riesgo | Corrección |
|---|---|---|---|
| 1 | `Content-Length` negativo dejaba el hilo colgado | Medio | Respuesta 400 |
| 2 | `services.json` (con secretos) tenía permisos 644 | Bajo | Todos los archivos de datos con permisos 600 |
| 3 | Plantillas: un nombre con comillas o `<>` generaba código roto | Medio | Escapado según el lenguaje del archivo |
| 4 | El límite de tiempo de clonados e instalaciones no se cumplía si el proceso no escribía nada | Bajo | Temporizador que mata el proceso |
| 5 | La pasarela no reintentaba un puerto ocupado | Medio | Reintento cada minuto |
| 6 | «Reinicios auto · 1 h» contaba solo el último minuto | Bajo | Historial de una hora |
| 7 | Se podía borrar un servicio mientras se actualizaba | Bajo | Respuesta 409 |
| 8 | El registro de intentos de login crecía sin límite | Bajo | Limpieza periódica |
| 9 | `novahub.service` y el README apuntaban a una ruta que no existe | Bajo | Rutas corregidas |

### Fallos encontrados fuera de las revisiones (durante el desarrollo o al probar)

Los anoto para no buscarlos otra vez: ya están corregidos.

- `tapo.py cancel` no anulaba nada porque la respuesta del enchufe llega envuelta en el nombre del método.
- El P110 solo admite una cuenta atrás: había que editar la existente en vez de añadir otra.
- Guardar los avisos sin `events` los reactivaba todos, y un guardado parcial borraba la cuenta de Gmail.
- Reiniciar NovaHub volvía a encender servicios que se habían apagado a propósito.
- Al encender el servidor, el túnel arrancaba antes que el DNS y casi agotaba los reintentos.
- Gmail corta la conexión, en vez de responder 535, cuando la contraseña de aplicación es incorrecta.

---

## Cómo se revisó (para repetirlo)

1. **Análisis estático**: `pyflakes server.py tapo.py` y ESLint 9 sobre `static/*.js` con las reglas
   `no-undef`, `no-unused-vars`, `no-redeclare`, `no-dupe-keys` y `no-unreachable`. Los dos sin
   avisos al cerrar la revisión 2.
2. **Lectura del código** cambiado, con atención a hilos y locks, excepciones en bucles de fondo,
   escapado de datos, permisos y límites de tiempo.
3. **Pruebas aisladas**: una instancia con `NOVAHUB_DATA` en una carpeta temporal y el envío de
   correo sustituido por un buzón falso. Se simularon caídas en bucle, arranques sin red,
   recuperaciones, hilos muertos, bucles colgados y comprobaciones de salud lentas.
4. **Watchdog real**: una copia en un servicio temporal de systemd (`systemd-run --user` con
   `Type=notify` y `WatchdogSec=30`). Se congeló con `SIGSTOP` y se comprobó que systemd la
   reiniciaba.
5. **Regresión en el panel real**: las 16 rutas de lectura responden 200; se comprueban las
   protecciones (401 sin sesión, 403 sin cabecera, 403 con `../`); y un navegador headless recorre
   24 pasos en claro, oscuro, escritorio y móvil sin errores de JavaScript ni desbordamientos.

## Lista para la próxima revisión

- [ ] Ejecutar el diff desde el commit «revisado hasta» (arriba) y revisar solo eso.
- [ ] Si el diff toca un invariante de seguridad, revisar la pieza entera y repetir su prueba.
- [ ] `pyflakes` y ESLint sin avisos.
- [ ] Regresión: rutas, protecciones y recorrido de la interfaz.
- [ ] Añadir aquí una fila al historial, actualizar el inventario, apuntar los hallazgos y
  **actualizar «Revisado hasta el commit»** al último commit revisado.
