# Cambios

Versiones con [versionado semántico](https://semver.org/lang/es/): **MAYOR.MENOR.PARCHE**. Cada mejora o arreglo
terminado es un parche (1.0.1, 1.0.2…); un bloque grande de mejoras, tras su revisión de código, es una versión menor
(1.1.0); una mayor (2.0.0) solo si al actualizar hay que hacer algo a mano.

## Sin publicar

## 1.0.10 — 2026-10-07

- «Discos y temperatura» rediseñado: una sola tarjeta con las temperaturas arriba y una fila por disco (estado, temperatura,
  datos clave y motivos), y el botón «Leer SMART» junto a la hora de la última lectura.
- El desgaste de un SSD sano (reserva intacta, sin errores) avisa como «Atención» desde el 80 % y solo es «Peligro» al
  llegar al 100 % o si hay errores o poca reserva.

## 1.0.9 — 2026-10-07

- **Salud de los discos y temperatura** (Resumen): SMART de cada disco cada 30 min con `novahub-sistema discos` (solo
  lectura, sin despertar discos dormidos), con estado Bien / Atención / Peligro y el motivo (sectores reasignados o
  pendientes, desgaste del SSD, errores…); temperaturas de CPU, gráfica y NVMe cada minuto. Avisos al móvil y al correo
  cuando un disco empeora o algo se calienta demasiado. Hay que volver a instalar `novahub-sistema` y `smartmontools`.

## 1.0.8 — 2026-10-07

- **Pendientes** en la página de Mejoras: una lista de tareas sueltas para hacer a mano (instalar algo, conectar el
  móvil…), con nota opcional para comandos o detalles, editar, borrar y las hechas en un desplegable.

## 1.0.7 — 2026-10-07

- **Fotos propias (Immich)**: el catálogo pide la carpeta de las fotos, por defecto en el disco duro de datos
  (`/mnt/dades/immich`), con la base de datos en el SSD. Las copias fuera de casa se llevan las fotos directamente
  (incremental, sin miniaturas) y la copia de la base de datos que Immich hace cada noche; la copia local nunca copia la
  carpeta viva de PostgreSQL. Notas para el móvil, incluido el cambio de URL en casa por el límite de 100 MB de Cloudflare.
- La comprobación de salud de los contenedores no cuenta fallos hasta que responden por primera vez (máx. 15 min):
  antes podía reiniciar una app a media descarga de sus imágenes.

## 1.0.6 — 2026-10-07

- Arreglado el 502 de Cloudflare (y las comprobaciones de salud fallidas) en servicios publicados cuyo programa solo
  escucha en IPv4 dentro del contenedor, como Vaultwarden: la pasarela y la salud usaban «localhost», que da primero
  ::1. Ahora prueban 127.0.0.1 y, si no, ::1.

## 1.0.5 — 2026-10-07

- **Gestor de contraseñas propio (Vaultwarden)**: se instala desde el catálogo proponiendo publicarlo con HTTPS
  (`vault.<dominio>`), con copias diarias activadas desde el primer día y el registro de cuentas controlado: NovaHub lo
  cierra solo en cuanto se crea tu cuenta y la ficha permite abrirlo para una cuenta más. Panel /admin desactivado.
- Las copias de seguridad copian las bases de datos SQLite con la API de SQLite (copia coherente aunque la app esté
  escribiendo) en lugar del archivo y su `-wal` a medias. Sirve para todas las apps que usan SQLite.

## 1.0.4 — 2026-10-07

- **Avisos al móvil con ntfy** (Ajustes → Avisos): ntfy como canal de avisos junto al correo, eligiendo qué avisos van
  por cada uno. «Proteger y conectar» deja el ntfy del catálogo con todo denegado por defecto, un usuario `movil` de solo
  lectura y una llave de solo escritura para NovaHub, que publica por dentro del servidor. Prioridad máxima para los
  problemas graves, botón de prueba y cambio de contraseña del móvil. Gmail pasa a ser opcional.
- El ntfy del catálogo se instala ya protegido (sin usuario no se puede leer ni publicar).
- Si un contenedor anterior se queda a medias (Podman lo pierde pero sus procesos siguen ocupando el puerto), al arrancar
  el servicio se cierran esos restos en vez de fallar con «Address already in use».

## 1.0.3 — 2026-10-07

- **Catálogo de apps** (Nuevo servicio → Catálogo de apps): 20 apps autoalojadas ya configuradas (Vaultwarden, Immich,
  Nextcloud, Radicale, ntfy, SearXNG, Jellyfin, Navidrome, Calibre-Web, Paperless-ngx, Mealie, Actual Budget, FreshRSS,
  Stirling-PDF, File Browser, Syncthing, Forgejo, Home Assistant, Uptime Kuma y Minecraft), con búsqueda y categorías.
  Instalar elige un puerto libre, genera las claves, descarga el compose oficial si hace falta, lo publica si quieres y lo
  arranca; la ficha muestra los primeros pasos. Definido en `catalogo.json`.

## 1.0.2 — 2026-10-06

- **Copias fuera de casa** (Ajustes → Copias fuera de casa): copias cifradas con restic de las copias locales y de la
  configuración de NovaHub a un disco USB o a otro servidor por SSH, sin servicios de terceros. Copia diaria incremental
  con retención, comprobación mensual con restauración real de un archivo, lista de copias y recuperación a una carpeta
  aparte. Si el disco USB no está conectado, se espera a la siguiente copia.

## 1.0.1 — 2026-10-06

- **Centro de actualizaciones** (Ajustes → Actualizaciones): NovaHub (versiones de GitHub o canal de desarrollo, con
  copia previa y vuelta atrás automática si la versión nueva no arranca), el sistema con apt (solo seguridad o todo,
  y de seguridad automáticas cada noche si quieres), reinicio pendiente con reinicio ordenado del servidor, imágenes de
  contenedores, servicios con git y dependencias de cada proyecto (npm, pip) con copia de seguridad previa. Se comprueba
  cada 6 horas, avisa por correo y guarda un historial.
- Lo que necesita root pasa por un único script con órdenes fijas, `tools/novahub-sistema`.
- La versión de NovaHub se ve en Ajustes → Actualizaciones.
- Mejoras: «Cerrar versión…» agrupa las hechas en un desplegable por versión.
- La página oculta de mejoras solo existe en paneles que ya tienen una lista.
- En el móvil, el menú del selector de servidor ya no se sale de la pantalla.

## 1.0.0 — 2026-10-06

Primera versión pública: servicios (programas, contenedores con Podman y docker-compose), consola en directo con
búsqueda, salud y límite de memoria, gráficas, avisos por correo, editor de archivos, Git, editor de `.env`, copias de
seguridad, tareas programadas, publicación con Cloudflare Tunnel, despliegue desde GitHub y plantillas, modo
producción, usuarios y roles, varios servidores por Tailscale, procesos, red y enchufe Tapo, apagado ordenado y app para
el móvil (PWA y APK de Android).
