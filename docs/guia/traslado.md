# Exportar e importar la configuración

Ajustes → **Traslado** guarda la configuración de NovaHub en un archivo (`.nhcfg`) para llevarla a otro servidor o
recuperarla tras una avería.

## Qué lleva

Eliges qué partes exportar:

| Parte | Contenido |
|---|---|
| Servicios | Cada servicio con sus ajustes, copias programadas y tareas |
| Usuarios | Usuarios con su contraseña (cifrada) y su verificación en dos pasos |
| Avisos | ntfy, correo y vigilante externo |
| Sesión, actualizaciones, Tapo | Sus ajustes |
| Copias fuera de casa | Destinos, contraseñas de cifrado y la llave SSH de NovaHub |
| Otros servidores | Servidores del panel y llaves de acceso remoto |
| Mejoras | Lista de mejoras y pendientes |
| Git | Nombre y correo con los que se firman los commits |

**No lleva los datos de los servicios** (sus carpetas, bases de datos, fotos…): eso va en las
[copias de seguridad](copias.md) y en las [copias fuera de casa](fuera-de-casa.md).

> [!IMPORTANT]
> El archivo va **siempre cifrado** con una contraseña que eliges (mínimo 12 caracteres): lleva secretos, como las
> contraseñas de las copias fuera de casa. Sin esa contraseña no se puede abrir ni recuperar: guárdala en tu gestor de
> contraseñas. Para exportar se pide también tu contraseña de NovaHub.

## Importar

1. En el servidor nuevo, instala NovaHub y entra (Ajustes → **Traslado** → Importar).
2. Elige el archivo y escribe su contraseña: verás de qué servidor viene y qué trae, con avisos de lo que ya existe,
   de las carpetas que faltan en este servidor y de los ajustes que se sustituyen.
3. Marca lo que quieras importar y pulsa **Importar lo marcado**.

- Los **servicios y usuarios que ya existen se dejan como están**, salvo que marques «Reemplazar».
- Antes de tocar nada se guarda una copia de la configuración actual en `data/import-backups/` (las 5 últimas).
- Si importas ajustes, NovaHub se reinicia solo unos segundos para aplicarlos; los servicios siguen funcionando.
- Las carpetas de los servicios tienen que existir en el servidor nuevo: restaura antes sus copias.
- La publicación en internet (el túnel de Cloudflare) se configura aparte en cada servidor.

## Desde la terminal

Para recuperar un servidor antes de arrancar el panel:

```bash
python3 server.py export [archivo.nhcfg]     # pide la contraseña del archivo dos veces
python3 server.py import archivo.nhcfg       # con NovaHub parado: systemctl --user stop novahub
```

## Cómo se cifra

Solo con la biblioteca estándar de Python: la clave sale de la contraseña con PBKDF2-SHA256 (600.000 vueltas y sal
aleatoria), los datos se cifran con HMAC-SHA256 en modo contador y todo se firma con HMAC-SHA256 y una clave aparte.
Una contraseña equivocada o un archivo modificado se detectan antes de descifrar nada.
