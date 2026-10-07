# Catálogo de apps

Nuevo servicio → **Catálogo de apps**: alternativas propias a servicios de empresas, ya configuradas (puertos, carpetas,
variables y claves generadas). Un clic las instala como un servicio más (contenedor o compose), con copias de seguridad,
salud, gráficas y publicación como cualquier otro, y en su ficha salen los **primeros pasos**.

| Categoría | Apps |
|---|---|
| Privacidad | Vaultwarden (contraseñas), Immich (fotos), Nextcloud (archivos), Radicale (calendario y contactos), ntfy (avisos al móvil), SearXNG (buscador) |
| Multimedia | Jellyfin (películas y series), Navidrome (música), Calibre-Web (libros) |
| Productividad | Paperless-ngx (documentos), Mealie (recetas), Actual Budget (finanzas), FreshRSS (noticias) |
| Herramientas | Stirling-PDF, File Browser, Syncthing, Forgejo (git propio) |
| Otras | Home Assistant (domótica), Uptime Kuma (vigilancia), Minecraft |

El catálogo es [`catalogo.json`](../../catalogo.json): añadir una app es añadir una entrada (imagen, puertos, carpetas, variables
con marcadores como `{secret}` o `{url}`, y notas). Las apps de varios contenedores descargan su compose oficial.
Las carpetas van por defecto a `~/apps/<app>` (`NOVAHUB_APPS_DIR`).

## Gestor de contraseñas (Vaultwarden)

Vaultwarden es compatible con las apps y extensiones de Bitwarden (Android, iPhone, Chrome, Firefox…). Al instalarlo:

- **HTTPS obligatorio:** el navegador y las apps lo exigen, así que el formulario propone publicarlo en
  `vault.<tu dominio>`. No lo pongas detrás de Cloudflare Access: las apps de Bitwarden no pueden pasar ese login.
- **Registro controlado:** entra en su dirección y crea tu cuenta. En cuanto existe, NovaHub cierra el registro solo
  (`SIGNUPS_ALLOWED=false`) y reinicia el contenedor, así que nadie más puede crear cuentas aunque esté en internet.
  En la ficha, «Registro de cuentas» muestra cuántas hay y permite **abrirlo para una cuenta más** (familia); se vuelve
  a cerrar tras ella. El panel `/admin` queda desactivado y las pistas de contraseña ocultas.
- **Copias diarias desde el primer día** (03:30, 14 días), con la base de datos copiada sin cortes. Las contraseñas ya
  van cifradas con tu contraseña maestra; para tenerlas también fuera de casa, añade un destino en **Copias fuera de
  casa** (restic, cifrado).
- En las apps de Bitwarden: «Autoalojado» (self-hosted) → `https://vault.<tu dominio>`.

## Fotos (Immich)

Alternativa a Google Fotos: copia automática desde el móvil, caras, mapas y álbumes compartidos.

- **Fotos en el disco duro:** el formulario pide la «Carpeta de las fotos», por defecto en el disco de datos
  (`/mnt/dades/immich`), y la base de datos se queda en la carpeta de la app (SSD, más rápida).
- **Copias:** Immich guarda cada noche una copia de su base de datos en `<fotos>/backups`. Las **Copias fuera de casa**
  se llevan la carpeta de fotos directamente (restic: incremental, sin duplicarla en un .tar.gz), sin miniaturas ni
  vídeos recodificados, que se regeneran. La copia local del servicio guarda su configuración (`.env`), nunca la carpeta
  viva de PostgreSQL, que copiada en marcha no sirve.
- **Móvil:** app «Immich» (F-Droid, Google Play o el APK de sus releases). Cloudflare corta las subidas de más de 100 MB,
  así que en la app activa el **cambio automático de URL**: con el Wi-Fi de casa usa la dirección local
  (`http://<ip>:2283`) y fuera, la publicada.
