# Usuarios y permisos

Cada persona entra con su **usuario y contraseña**. Ajustes → **Usuarios** (solo administradores) para crearlos,
cambiarles el rol o los servicios y borrarlos; cada uno cambia su contraseña en Ajustes → **Mi cuenta**.

| Rol | Puede |
|---|---|
| **Administrador** | Todo: servicios, archivos, git, variables, copias, tareas, ajustes, usuarios, apagar el servidor |
| **Operador** | Ver, encender, apagar y reiniciar, escribir en la consola, lanzar una copia o una tarea |
| **Lector** | Ver estado, gráficas y logs |

- A un operador o lector se le pueden dar **todos los servicios o solo algunos**: los demás ni los ve.
- Los permisos los comprueba el servidor en cada petición, con «denegado por defecto»: lo que no está permitido
  expresamente para un rol es solo para administradores. A quien no es administrador tampoco le llegan comandos,
  rutas, variables ni los comandos de las tareas.
- Cambiar la contraseña, el rol o los servicios de alguien cierra sus sesiones abiertas.
- Siempre queda al menos un administrador, y nadie puede borrarse ni quitarse el rol a sí mismo.
- Desde la terminal: `python3 server.py set-password [usuario]` (crea un administrador si no existe).
- Para que alguien llegue desde internet, añade también su correo a la regla de **Cloudflare Access**.
- La primera vez, la contraseña única de antes pasa a ser la del usuario administrador con el nombre del usuario
  del sistema.
