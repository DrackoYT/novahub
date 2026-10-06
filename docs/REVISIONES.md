# Registro de revisiones de código

Este documento dice **qué partes de NovaHub están revisadas, hasta qué commit y qué se comprobó**.
Sirve para que cada revisión nueva cubra solo lo que ha cambiado desde la anterior.

## Cómo saber qué hay que revisar

**Revisado hasta el commit: `72eae4a`** (se actualiza al cerrar cada revisión; editar este documento
por otros motivos no cambia este valor). Para ver lo que ha cambiado desde entonces:

```bash
BASE=72eae4a
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
| 3 | 2026-10-06 | **Incremental**: modo producción, sesiones, editor, copias, gráficas y vista de red | `92ee43d..72eae4a` | 7 corregidos |

---

## Inventario: qué está revisado

Estado de cada pieza tras la revisión 3. «R1» = revisada entera en la revisión 1 y sin cambios
desde entonces; «R2» / «R3» = cambiada o añadida después y revisada en esa revisión.

### `server.py` (backend, ~4.200 líneas)

| Pieza | Estado | Notas |
|---|---|---|
| Utilidades (`read_json`, `write_json`, `proc_*`, `group_usage`, `listening_ports`, `lan_ip`, `system_info`, `slugify`) | R1 + R3 | `write_json` escribe con permisos 600; R3: opción compacta (`indent=None`) |
| `uptime`, `wait_for_network` | R2 | |
| `normalize_service` | R1 + R2 | R2: campos de una línea sin caracteres de control (salvo `command` y `description`) |
| `Manager`: `spawn`, `start`, `stop`, `_do_stop`, `restart`, stdin, `_rotate_live`, CRUD, `public` | R1 + R3 | R3: `NOVAHUB_SERVICE_PORT`, `mode`/`can_build`/`backup` en `public`, `delete` borra `data/builds/<id>` |
| `Manager.boot`, `_autostart` | R2 | Autoarranque solo al encender el servidor; espera red; relanza los servicios que murieron con NovaHub caído |
| `Manager.monitor`, `_check_all`, `_check_memory` | R2 | Reintentos rápidos y luego lentos (nunca se abandona), avisos, aviso de recuperación |
| `Manager.status` | R2 | Estado nuevo `retrying` |
| `Auth` | R1 + R3 | Invariante de seguridad. R3: tokens `emitido:caduca.firma`, inactividad y máximo absoluto (`data/session.json`), revocación por sesión |
| `Publisher` (túnel, DNS, ingress) | R1 | |
| `Power` | R1 + R2 | R2: correo de apagado antes de programar el corte del enchufe |
| Archivos: `service_root`, `safe_path`, `list_dir`, `read_file` | R1 | Invariante de seguridad |
| Edición: `write_file`, `backup_file`, `_check_writable` | R3 | Escritura atómica, conflicto por `mtime`, bloquea `.git`, versión anterior en `data/backups/` |
| Git: `git_*` | R1 | |
| `Tasks` (procesos) | R1 | |
| `Health` | R1 + R2 | R2: latido del supervisor en cada comprobación; avisos por correo |
| `Network` (vista de red) | R3 | Métricas de cloudflared (2 s de límite), reglas del túnel, enchufe en segundo plano cada ≥60 s |
| `Metrics` (gráficas), `cpu_times` | R3 | Hilo propio que late; `data/metrics.json` cada 5 min y al cerrar |
| `Backups` y ayudantes (`backup_disk`, `disk_kind`, `snapshot_time`, `_own_rels`, `_excluded`) | R3 | Copias en el HDD, no escribe si no está montado; restauración con filtro `data` |
| `Gateway` (pasarela y página 503) | R1 + R2 | R2: su hilo lo lanza el supervisor |
| `Roadmap` | R1 | |
| Correo: `Notifier`, `email_html`, `make_orb_png`, `log_tail`, `strip_ansi` | R2 | |
| Vigilancia: `Supervisor`, `sd_notify`, `previous_run`/`mark_run`, `journal_tail`, `startup_notice`, `_boot_report` | R2 | |
| Despliegue: `gh_repos`, `detect_project`, `project_dir`, `install_steps`, `Deployer` | R1 + R3 | R3: modo producción (`set_mode`, `_to_prod`, `_build`, `_publish_build`, `prod_command`, `build_info`) |
| Plantillas (`TEMPLATES`, `template_create`, `_template_job`, `download_paper`) | R1 | |
| `Handler` (rutas, cabeceras, cookies, estáticos, SSE) | R1 + R2 + R3 | R3: renovación de sesión, `/api/session-settings`, `/api/network`, `/api/metrics`, `mode`, `file` (PUT), `backups*` |
| `main`, `panel_url` | R2 + R3 | R3: hilos `copias` y `graficas`; guarda las métricas al cerrar |

### Otros archivos

| Archivo | Estado | Notas |
|---|---|---|
| `static/app.js` | R1 + R2 + R3 | R3: sesión y bloqueo, editor con resaltado, modo producción, pestaña Copias, gráficas SVG, vista Red |
| `static/style.css` | R1 + R2 + R3 | R3: editor, copias, gráficas (`--chart`) y vista de red |
| `serve.py` | R3 | Servidor estático de producción: solo 127.0.0.1, sin salir de la carpeta, gzip y caché |
| `static/index.html`, `static/theme.js` | R1 | |
| `static/favicon.svg`, `static/fonts/*` | — | Recursos estáticos, sin lógica |
| `tapo.py` | R1 + R2 + R3 | R3: `status` devuelve consumo (W, kWh), señal, IP y encendido desde |
| `novahub.service` | R2 | `Type=notify`, `NotifyAccess=main`, `WatchdogSec=30`, `KillMode=process` |
| `README.md` | R2 + R3 | Comprobado que describe lo que hace el código |
| `demo/` | — | Página de ejemplo, sin lógica |

---

## Invariantes de seguridad comprobados

Son propiedades que se verificaron con pruebas reales. Si un cambio toca su código, hay que volver
a comprobarlas.

1. **Autenticación**: sin cookie, con token falsificado, caducado o de una sesión cerrada, toda la API responde 401. Los tokens se
   firman con HMAC-SHA256 y un secreto de `data/auth.json`. Caducan tras la inactividad (15 min) y como mucho a las 12 h; solo
   los renuevan peticiones con actividad real del usuario. Cerrar sesión invalida **todos** los tokens de esa sesión. La contraseña usa PBKDF2 con 600.000
   iteraciones. Máximo 5 intentos de login por IP cada 5 minutos.
2. **CSRF**: toda petición que no sea GET exige la cabecera `X-NovaHub: 1`, y la cookie es
   `HttpOnly` y `SameSite=Strict`. Ningún GET modifica estado.
3. **Rutas de archivos**: `safe_path` resuelve con `realpath` y rechaza todo lo que quede fuera de
   la carpeta del servicio, incluidos `../` y enlaces simbólicos. Los estáticos solo se sirven
   desde `static/`. Editar no puede tocar `.git/`. Los nombres de copia se validan con una expresión
   exacta, y restaurar usa el filtro `data` de `tarfile` (nada fuera de la carpeta). `serve.py` no sale
   de la carpeta compilada.
4. **XSS**: en `app.js`, todo dato del servidor pasa por `esc()` o se asigna con `textContent`. Las
   URL de servicio solo pueden ser `http(s)://`. En los correos, todo texto dinámico pasa por
   `html.escape`.
5. **Secretos**: los archivos de `data/` tienen permisos 600. La contraseña de aplicación de Gmail
   nunca se devuelve por la API. `tapo.json` exige 600. Las copias del HDD (pueden llevar `.env`) van en
   carpetas 700 y archivos 600.
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
- **«Pedir la contraseña al recargar» lo aplica la interfaz**: al cargar sin haber escrito la contraseña,
  cierra la sesión en el servidor. Quien tenga la cookie y no use la interfaz no se ve afectado; para eso
  están la caducidad por inactividad y Cloudflare Access.
- **Restaurar una copia borra** lo creado después en las carpetas copiadas (salvo lo excluido). Antes
  siempre se guarda una copia del estado actual.
- **Se puede encender a mano un servicio durante su restauración**: la interfaz no lo impide.
- **El modo producción y las actualizaciones ejecutan `npm run build`** del propio proyecto.
- **Clonar repositorios o usar plantillas ejecuta sus scripts de instalación** (`npm ci` y
  similares). Solo se clonan repositorios propios.

## Hallazgos y correcciones

### Revisión 3 (incremental, 2026-10-06)

| # | Problema | Riesgo | Corrección |
|---|---|---|---|
| 1 | Modo producción: `serve.py` servía `dist/` directamente y `npm run build` la vacía al empezar. Una compilación fallida (o los segundos que dura una buena) dejaba la web publicada sin archivos | Medio | Se sirve una copia en `data/builds/<id>/current`, que solo cambia (de forma atómica) cuando la compilación acaba bien |
| 2 | Cerrar sesión solo invalidaba el último token; uno anterior de la misma sesión (antes de una renovación) seguía valiendo hasta su caducidad | Bajo | La revocación es por sesión («emitido»), así caen todos sus tokens |
| 3 | Restaurar borraba según las exclusiones *actuales*: si después de la copia se quitaba `node_modules` de «Excluir», restaurar lo borraba | Medio | Cada copia guarda sus exclusiones (cabecera PAX) y la restauración usa esas |
| 4 | Una copia automática que fallaba (p. ej. disco sin montar) se reintentaba cada 30 s | Bajo | Reintento a los 30 min |
| 5 | Si el servicio estaba esperando un reintento, el gestor podía arrancarlo a mitad de una restauración | Bajo | Parar para copiar o restaurar cancela el reintento y lo arranca al acabar |
| 6 | `serve.py` marcaba como inmutables un año archivos sin huella con nombres largos (`logo-transparente.png`); una ruta con byte nulo daba un error interno | Bajo | Caché larga solo en `assets/` o `static/`; byte nulo → 404 |
| 7 | La pestaña Copias dejaba de refrescarse sola tras salir de la ficha durante una copia | Bajo | El temporizador se reinicia al cambiar de vista |

También se ordenó una cabecera de sección mal colocada y la lista de servicios que lee el hilo de
gráficas pasa a leerse con el lock.

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
- Ctrl+S del editor solo guardaba con el foco en el área de texto, y dos guardados en el mismo segundo
  pisaban la versión anterior guardada.

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
5. **Prueba de memoria** (revisión 3): un servicio que crece hasta 500 MB con límite de 300 MB se
   reinició 3 veces (a los ~30 s por encima del límite cada vez) y a la cuarta NovaHub dejó de reiniciarlo
   y lo anotó, como está previsto. La gráfica de memoria muestra la línea del límite.
6. **Regresión en el panel real**: las 18 rutas de lectura responden 200; se comprueban las
   protecciones (401 sin sesión, 403 sin cabecera, 403 con `../`); y un navegador headless recorre
   24 pasos en claro, oscuro, escritorio y móvil sin errores de JavaScript ni desbordamientos.

## Lista para la próxima revisión

- [ ] Ejecutar el diff desde el commit «revisado hasta» (arriba) y revisar solo eso.
- [ ] Si el diff toca un invariante de seguridad, revisar la pieza entera y repetir su prueba.
- [ ] `pyflakes` y ESLint sin avisos.
- [ ] Regresión: rutas, protecciones y recorrido de la interfaz.
- [ ] Añadir aquí una fila al historial, actualizar el inventario, apuntar los hallazgos y
  **actualizar «Revisado hasta el commit»** al último commit revisado.
