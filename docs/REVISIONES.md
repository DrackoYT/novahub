# Registro de revisiones de código

Este documento dice **qué partes de NovaHub están revisadas, hasta qué commit y qué se comprobó**.
Sirve para que cada revisión nueva cubra solo lo que ha cambiado desde la anterior.

## Cómo saber qué hay que revisar

**Revisado hasta el commit: `aae4582`** (versión **1.0**, etiqueta `v1.0`) (se actualiza al cerrar cada revisión; editar este documento
por otros motivos no cambia este valor). Para ver lo que ha cambiado desde entonces:

```bash
BASE=aae4582
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
| 4 | 2026-10-06 | **Incremental**: PWA, tareas programadas, búsqueda en logs, `.env`, identidad de git, ajustes como página | `72eae4a..0d96648` | 5 corregidos |
| 5 | 2026-10-06 | **v1.0**: contenedores, páginas de servicio, usuarios y permisos, varios servidores; todos los invariantes repetidos; historial de git revisado para publicarlo | `0d96648..aae4582` | 2 corregidos |

---

## Inventario: qué está revisado

Estado de cada pieza tras la revisión 5 (v1.0). «R1» = revisada entera en la revisión 1 y sin cambios
desde entonces; «R2»…«R5» = cambiada o añadida después y revisada en esa revisión.

### `server.py` (backend, ~5.300 líneas)

| Pieza | Estado | Notas |
|---|---|---|
| Utilidades (`read_json`, `write_json`, `proc_*`, `group_usage`, `listening_ports`, `lan_ip`, `system_info`, `slugify`) | R1 + R3 | `write_json` escribe con permisos 600; R3: opción compacta (`indent=None`) |
| `uptime`, `wait_for_network` | R2 | |
| `normalize_service` | R1 + R2 + R5 | R2: campos de una línea sin caracteres de control (salvo `command` y `description`) |
| `Manager`: `spawn`, `start`, `stop`, `_do_stop`, `restart`, stdin, `_rotate_live`, CRUD, `public` | R1 + R3 | R3: `NOVAHUB_SERVICE_PORT`, `mode`/`can_build`/`backup` en `public`, `delete` borra `data/builds/<id>` |
| `Manager.boot`, `_autostart` | R2 | Autoarranque solo al encender el servidor; espera red; relanza los servicios que murieron con NovaHub caído |
| `Manager.monitor`, `_check_all`, `_check_memory` | R2 | Reintentos rápidos y luego lentos (nunca se abandona), avisos, aviso de recuperación |
| `Manager.status` | R2 | Estado nuevo `retrying` |
| `Auth` | R1 + R3 + R5 | Invariante de seguridad. R5: reescrita con usuarios (`data/users.json`) y roles; tokens `emitido:caduca:usuario:versión.firma`; la versión cambia con contraseña/rol/servicios; migración desde la contraseña única; `users.json` se relee si cambia por fuera |
| Permisos: `ROLES`, `route_permission`, `Handler.can/need/svc_out` | R5 | Invariante de seguridad (9): denegado por defecto |
| Varios servidores: `ApiTokens`, `Remotes`, `Handler.proxy`, `remote_listener` | R5 | Invariante de seguridad (10): llaves con huella SHA-256, puerta solo de API, reenvío sin HTML |
| Contenedores: `container_command`, `prepare_container`, `stop_containers`, `Containers`, `Deployer._update_container` | R5 | Podman sin root; variables sin valor en la orden; CPU/memoria por cgroup |
| `Publisher` (túnel, DNS, ingress) | R1 | |
| `Power` | R1 + R2 | R2: correo de apagado antes de programar el corte del enchufe |
| Archivos: `service_root`, `safe_path`, `list_dir`, `read_file` | R1 | Invariante de seguridad |
| Edición: `write_file`, `backup_file`, `_check_writable` | R3 | Escritura atómica, conflicto por `mtime`, bloquea `.git`, versión anterior en `data/backups/` |
| Variables: `read_env`, `write_env`, `_env_*`, `env_files` | R4 | Ruta por `safe_path`; conserva comentarios y formato; `.env` nuevo con 600; aviso si iría a git |
| Git: `git_*` | R1 + R4 | R4: `git_commit` exige identidad (ya no copia el autor del último commit); `git_identity`/`set_git_identity` | |
| `Tasks` (procesos) | R1 | |
| `Health` | R1 + R2 | R2: latido del supervisor en cada comprobación; avisos por correo |
| `Network` (vista de red) | R3 + R4 | Métricas de cloudflared (2 s de límite), reglas del túnel, enchufe en segundo plano cada ≥60 s. R4: errores = respuestas 5xx |
| `Metrics` (gráficas), `cpu_times` | R3 | Hilo propio que late; `data/metrics.json` cada 5 min y al cerrar |
| `Backups` y ayudantes (`backup_disk`, `disk_kind`, `snapshot_time`, `_own_rels`, `_excluded`) | R3 | Copias en el HDD, no escribe si no está montado; restauración con filtro `data` |
| `Scheduler` (tareas programadas) | R4 | Hilo propio que late; margen de 3 min, nunca dos veces; comandos con límite de 10 min en su propio grupo de procesos |
| Búsqueda en logs: `search_log` + `logsearch.py` | R4 | Texto en el propio proceso; expresiones regulares en un proceso aparte con límite de 5 s |
| `Gateway` (pasarela y página 503) | R1 + R2 | R2: su hilo lo lanza el supervisor |
| `Roadmap` | R1 | |
| Correo: `Notifier`, `email_html`, `make_orb_png`, `log_tail`, `strip_ansi` | R2 | |
| Vigilancia: `Supervisor`, `sd_notify`, `previous_run`/`mark_run`, `journal_tail`, `startup_notice`, `_boot_report` | R2 | |
| Despliegue: `gh_repos`, `detect_project`, `project_dir`, `install_steps`, `Deployer` | R1 + R3 | R3: modo producción (`set_mode`, `_to_prod`, `_build`, `_publish_build`, `prod_command`, `build_info`) |
| Plantillas (`TEMPLATES`, `template_create`, `_template_job`, `download_paper`) | R1 | |
| `Handler` (rutas, cabeceras, cookies, estáticos, SSE) | R1 + R2 + R3 + R4 | R3: renovación de sesión, `/api/session-settings`, `/api/network`, `/api/metrics`, `mode`, `file` (PUT), `backups*`. R4: `/api/git-identity`, `tasks*`, `logs/search`, `env`; MIME del manifiesto |
| `main`, `panel_url` | R2 + R3 + R4 | R3: hilos `copias` y `graficas`; guarda las métricas al cerrar. R4: hilo `tareas` |

### Otros archivos

| Archivo | Estado | Notas |
|---|---|---|
| `static/app.js` | R1 + R2 + R3 + R4 + R5 | R3: sesión y bloqueo, editor con resaltado, modo producción, pestaña Copias, gráficas SVG, vista Red. R4: PWA (registro, instalar, sin conexión), Tareas, búsqueda en la consola, Variables, Ajustes como página |
| `static/style.css` | R1 + R2 + R3 + R4 + R5 | R3: editor, copias, gráficas (`--chart`) y vista de red. R4: tareas, búsqueda, variables, ajustes, aviso sin conexión |
| `static/sw.js`, `static/manifest.webmanifest`, `static/icons/*` | R4 | El service worker nunca guarda `/api/` ni respuestas redirigidas (login de Access); primero la red |
| `logsearch.py` | R4 | Búsqueda en logs; se ejecuta como proceso aparte para las expresiones regulares |
| `tools/make_icons.py` | R4 | Genera los iconos; no se ejecuta en el servidor |
| `serve.py` | R3 | Servidor estático de producción: solo 127.0.0.1, sin salir de la carpeta, gzip y caché |
| `static/index.html`, `static/theme.js` | R1 + R4 | R4: manifiesto con credenciales y etiquetas de iOS | |
| `static/favicon.svg`, `static/fonts/*` | — | Recursos estáticos, sin lógica |
| `tapo.py` | R1 + R2 + R3 | R3: `status` devuelve consumo (W, kWh), señal, IP y encendido desde |
| `novahub.service` | R2 | `Type=notify`, `NotifyAccess=main`, `WatchdogSec=30`, `KillMode=process` |
| `README.md` | R2 + R3 + R4 | Comprobado que describe lo que hace el código |
| `demo/` | — | Página de ejemplo, sin lógica |

---

## Invariantes de seguridad comprobados

Son propiedades que se verificaron con pruebas reales. Si un cambio toca su código, hay que volver
a comprobarlas.

1. **Autenticación**: sin cookie, con token falsificado, caducado o de una sesión cerrada, toda la API responde 401. Los tokens se
   firman con HMAC-SHA256 y un secreto de `data/auth.json`. Caducan tras la inactividad (15 min) y como mucho a las 12 h; solo
   los renuevan peticiones con actividad real del usuario. Cerrar sesión invalida **todos** los tokens de esa sesión. La contraseña usa PBKDF2 con 600.000
   iteraciones. Máximo 5 intentos de login (o de llave de acceso) por IP cada 5 minutos. Con un usuario que no existe
   el login tarda lo mismo (no se puede averiguar qué usuarios hay). Las sesiones de un usuario caen si cambia su
   contraseña, su rol o sus servicios, o si se borra.
2. **CSRF**: toda petición que no sea GET exige la cabecera `X-NovaHub: 1`, y la cookie es
   `HttpOnly` y `SameSite=Strict`. Ningún GET modifica estado.
3. **Rutas de archivos**: `safe_path` resuelve con `realpath` y rechaza todo lo que quede fuera de
   la carpeta del servicio, incluidos `../` y enlaces simbólicos. Los estáticos solo se sirven
   desde `static/`. Editar no puede tocar `.git/`. Los nombres de copia se validan con una expresión
   exacta, y restaurar usa el filtro `data` de `tarfile` (nada fuera de la carpeta). `serve.py` no sale
   de la carpeta compilada. El editor de `.env` también pasa por `safe_path` (un `.env` enlazado fuera no se toca).
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
9. **Permisos**: cada petición pasa por `route_permission` antes de hacer nada; lo que no está permitido
   expresamente a operador o lector es solo para administradores, y operador/lector solo llegan a sus servicios.
   A quien no es administrador no se le envían comandos, rutas, variables ni comandos de tareas. Comprobado con
   28 rutas × 2 roles.
10. **Varios servidores**: la puerta remota (`NOVAHUB_REMOTE_LISTEN`) solo acepta llaves (`Bearer nh_…`, guardadas
    como huella SHA-256): ni interfaz, ni login, ni cookies. El reenvío solo deja pasar JSON y la consola en
    directo; cualquier otra respuesta sale como descarga con `CSP: sandbox`, así un servidor remoto comprometido
    no puede ejecutar código en este panel. Solo los administradores pueden usar otros servidores.

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
- **Las tareas programadas de tipo «comando» ejecutan lo que se escriba**, como el comando del propio
  servicio: es su función.
- **El `.env` se ve en texto normal en la pestaña Archivos.** En Variables los valores van ocultos, pero solo
  frente a miradas por encima del hombro: la API los devuelve a quien tenga sesión.
- **La app del móvil guarda la interfaz** (HTML, CSS, JS, fuentes) en el teléfono, nunca datos ni respuestas
  de la API.
- **Las llaves de otros servidores se guardan en claro** en `data/servers.json` (permisos 600) del panel principal:
  tiene que poder enviarlas. En el servidor remoto solo se guarda su huella.
- **Una llave actúa con los permisos de quien la creó** (administrador) y puede crear otras llaves o usuarios en
  ese servidor. Se revoca desde allí.
- **Los contenedores aceptan opciones de podman arbitrarias** («Opciones de podman»), como el comando de un
  programa: solo los administradores pueden ponerlas. Sin root, no dan acceso de root al servidor.
- **El correo del autor está en el historial de git** (44 commits). Al hacer público el repositorio será visible.
- **Clonar repositorios o usar plantillas ejecuta sus scripts de instalación** (`npm ci` y
  similares). Solo se clonan repositorios propios.

## Hallazgos y correcciones

### Revisión 5 — versión 1.0 (2026-10-06)

Además de lo cambiado, se repitieron en el panel real todas las comprobaciones de los invariantes (autenticación,
CSRF, rutas, secretos, red, peticiones malformadas, procesos), la matriz de permisos con los tres roles en el entorno
aislado, todas las pruebas de navegador (gráficas, búsqueda, tareas, ajustes, formulario, usuarios, app sin conexión)
y se revisó el historial completo de git en busca de llaves, contraseñas, IPs o direcciones privadas (ninguna).

| # | Problema | Riesgo | Corrección |
|---|---|---|---|
| 1 | El reenvío a otros servidores devolvía el `Content-Type` del remoto: uno comprometido podía servir HTML o JavaScript con el origen de este panel (XSS, y con `script-src 'self'` la CSP no lo frenaba) | Medio | Solo pasan JSON y `text/event-stream`; el resto sale como `application/octet-stream` + `attachment` + `CSP: sandbox` (probado con un servidor remoto malicioso falso) |
| 2 | Los números del estado de otros servidores se pasaban tal cual | Bajo | Se fuerzan a número; el nombre de máquina se recorta y la interfaz lo escapa |

También se quitaron del README el dominio y la carpeta personal.

### Revisión 4 (incremental, 2026-10-06)

| # | Problema | Riesgo | Corrección |
|---|---|---|---|
| 1 | Una expresión regular catastrófica en «Buscar en los logs» (p. ej. `(a+)+$`) dejaba un hilo del panel al 100 % de CPU sin fin, y la interfaz la repetía cada 5 s | Medio | Las expresiones regulares se buscan en un proceso aparte (`logsearch.py`) que se mata a los 5 s; el panel sigue respondiendo |
| 2 | El editor de `.env` no pasaba por `safe_path`: un `.env` enlazado a un archivo de fuera de la carpeta se leía, y guardar reemplazaba el enlace por un archivo | Bajo | La ruta se resuelve con `safe_path`: fuera de la carpeta → rechazado; enlazado dentro → se edita el destino y el enlace se conserva |
| 3 | `KEY='valor' # nota` se leía con las comillas y el comentario dentro del valor | Bajo | Se reconocen las comillas seguidas de un comentario |
| 4 | Si se borraba un servicio mientras una de sus tareas se ejecutaba, quedaba un estado huérfano | Bajo | Al acabar, si el servicio ya no existe, no se guarda nada |
| 5 | «Enviar correo de prueba» esperaba 600 ms a ciegas a que se guardara lo escrito; si tardaba más, la prueba usaba la configuración anterior | Bajo | Espera a que el guardado termine |

El «1 error» de la vista Red al cerrar la revisión era un 503 de cloudflared en el segundo exacto en que se
reinició NovaHub para aplicar un cambio (`connection reset by peer` en `/api/system`): no es un fallo.

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
6. **Regresión en el panel real**: las rutas de lectura (23 en la revisión 4, incluidos manifiesto, `sw.js` e iconos) responden 200; se comprueban las
   protecciones (401 sin sesión, 403 sin cabecera, 403 con `../`); y un navegador headless recorre
   24 pasos en claro, oscuro, escritorio y móvil sin errores de JavaScript ni desbordamientos.

## Lista para la próxima revisión

- [ ] Ejecutar el diff desde el commit «revisado hasta» (arriba) y revisar solo eso.
- [ ] Si el diff toca un invariante de seguridad, revisar la pieza entera y repetir su prueba.
- [ ] `pyflakes` y ESLint sin avisos.
- [ ] Regresión: rutas, protecciones y recorrido de la interfaz.
- [ ] Añadir aquí una fila al historial, actualizar el inventario, apuntar los hallazgos y
  **actualizar «Revisado hasta el commit»** al último commit revisado.
