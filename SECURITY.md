# Seguridad

NovaHub **ejecuta comandos en tu servidor**: quien entra como administrador puede hacer casi lo mismo que tu usuario
de Linux. Por eso conviene tratarlo como un acceso SSH.

## Recomendaciones

- **No lo expongas directamente a internet.** El panel escucha solo en `127.0.0.1`. Para entrar desde fuera, usa
  Cloudflare Tunnel con **Cloudflare Access** delante (tu cuenta de Google o un código por correo), o una VPN como
  Tailscale.
- Ejecútalo con un **usuario normal**, nunca como root (el `novahub.service` incluido es un servicio de usuario).
- Usa contraseñas largas y da a cada persona su usuario con el **rol mínimo** (operador o lector) y solo los servicios
  que necesite.
- Para los contenedores se usa **Podman sin root**: no añadas tu usuario al grupo `docker`, que equivale a root.

## Qué protege NovaHub

- Contraseñas con PBKDF2-SHA256 (600.000 iteraciones); máximo 5 intentos por IP cada 5 minutos.
- Sesiones firmadas (HMAC-SHA256) que caducan por inactividad y por tiempo máximo; cerrar sesión las invalida en el
  servidor; cambiar contraseña, rol o servicios cierra las sesiones de ese usuario.
- Protección CSRF (cabecera obligatoria en todo lo que modifica) y cookie `HttpOnly` + `SameSite=Strict`.
- Permisos por rol comprobados en el servidor en cada petición, denegados por defecto.
- Rutas de archivos limitadas a la carpeta de cada servicio (sin `../` ni enlaces que salgan).
- Cabeceras de seguridad (CSP, `X-Frame-Options`, `nosniff`) y datos en `data/` con permisos 600.
- Llaves para otros paneles guardadas como huella SHA-256; la puerta remota solo acepta llaves.

El detalle, las pruebas que se hicieron y los riesgos aceptados están en [`docs/REVISIONES.md`](docs/REVISIONES.md).

## Avisar de un fallo

Si encuentras una vulnerabilidad, **no abras un issue público**: usa
[«Report a vulnerability»](https://github.com/DrackoYT/novahub/security/advisories/new) en la pestaña *Security* del
repositorio. Intentaré responder en unos días.
