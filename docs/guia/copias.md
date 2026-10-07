# Copias de seguridad

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
- **Bases de datos SQLite** (Vaultwarden, Uptime Kuma, ntfy…): se copian con la API de copia de SQLite, que da una
  copia coherente aunque la app esté escribiendo, en lugar de copiar el archivo y su `-wal` a medias.
- **Retención:** se guardan las N últimas automáticas y las 3 últimas «antes de restaurar»; las manuales
  solo se borran a mano.
- **Restaurar:** para el servicio, guarda antes una copia del estado actual, deja la carpeta como en la
  copia (sin tocar lo excluido) y lo vuelve a arrancar. También se pueden descargar y borrar.
