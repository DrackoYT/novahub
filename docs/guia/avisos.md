# Avisos al móvil y por correo

Ajustes → **Avisos**: NovaHub te avisa cuando un servicio se cae, deja de responder o se pasa de memoria, cuando el
servidor se enciende o se apaga, si falla una copia, una tarea o una actualización, y cuando hay actualizaciones. Como
mucho un aviso por servicio y tipo cada 10 minutos. Para cada tipo eliges si va al móvil, al correo o a los dos.

- **Móvil con ntfy** (recomendado, sin terceros): instala **ntfy** desde el catálogo y pulsa **«Proteger y conectar»**.
  ntfy queda con todo denegado por defecto, un usuario `movil` que solo puede leer y una llave para NovaHub que solo
  puede publicar en su tema. NovaHub le envía los avisos por dentro del servidor (no depende del túnel), con prioridad
  máxima para los problemas graves. En el móvil, la app **ntfy** (Google Play o F-Droid; en iPhone, App Store) con la
  dirección pública, el usuario `movil` y el tema `novahub`. También vale cualquier otro servidor ntfy (dirección, tema
  y llave a mano).
- **Correo con Gmail** (opcional): una [contraseña de aplicación](https://myaccount.google.com/apppasswords) de Google
  (no tu contraseña normal). Correos en HTML con las últimas líneas de la consola. Sin cuenta, desactivado.
