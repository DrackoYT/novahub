# Verificación en dos pasos

Ajustes → **Mi cuenta** → «Activar»: escaneas el código QR con una app de códigos (Aegis, Google Authenticator,
Bitwarden, 2FAS…) y confirmas con un primer código. Desde entonces, al entrar se pide también el código de 6 cifras
(TOTP, RFC 6238; se acepta el de 30 s antes o después y ninguno sirve dos veces).

- **Códigos de recuperación:** 8, de un solo uso, que se muestran una vez (cópialos o descárgalos). Sirven en lugar del
  código si pierdes el móvil; se pueden generar otros nuevos.
- **Obligatoria para administradores** (Ajustes → Sesión): quien no la tenga solo puede mirar hasta activarla. Para
  marcarla hay que tenerla activada antes.
- **Móvil perdido:** un administrador se la quita a otro usuario en Usuarios → Editar. Si eres tú y no te quedan
  códigos: `python3 server.py reset-totp <usuario>` en el servidor.
- Las llaves de acceso entre paneles (Acceso remoto) no la piden: ya son secretos largos.
