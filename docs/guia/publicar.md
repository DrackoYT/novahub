# Publicar en internet

El panel escucha solo en `127.0.0.1`; Cloudflare se conecta desde dentro del servidor, así que no hace falta abrir puertos.

1. Instala `cloudflared` y autentícate: `cloudflared tunnel login`
2. Crea el túnel y el DNS:
   ```bash
   cloudflared tunnel create novahub
   cloudflared tunnel route dns novahub panel.tudominio.com
   ```
3. `~/.cloudflared/config.yml`:
   ```yaml
   tunnel: novahub
   credentials-file: /home/<usuario>/.cloudflared/<ID-DEL-TUNEL>.json
   ingress:
     - hostname: panel.tudominio.com
       service: http://localhost:8686
     - service: http_status:404
   ```
4. `cloudflared tunnel run novahub` (o `sudo cloudflared service install` para dejarlo como servicio).

> ⚠️ Quien entre al panel puede ejecutar comandos en tu servidor. Usa una contraseña larga y,
> si puedes, añade **Cloudflare Access** (Zero Trust → Access → Applications) delante del
> dominio para exigir tu email/Google antes de llegar siquiera al login.

## Publicar servicios desde el panel

Con el túnel funcionando, el panel puede dar a cada servicio su propia dirección pública:

1. Añade tu dominio a la unidad de systemd (`~/.config/systemd/user/novahub.service`):
   ```ini
   Environment=NOVAHUB_DOMAIN=tudominio.com
   ```
   y recarga: `systemctl --user daemon-reload && systemctl --user restart novahub`.
2. Crea en el panel un servicio para el túnel con el comando `cloudflared tunnel run novahub`
   (autoarranque + reiniciar si se cae).
3. En cada servicio con puerto aparece el campo **Publicar en internet**: escribe un subdominio
   (p. ej. `mi-app`) y al guardar el panel crea el CNAME `mi-app.tudominio.com`, añade la regla al
   `config.yml` del túnel, rellena la URL del servicio y reinicia el túnel.

Opcionales: `NOVAHUB_TUNNEL` (si no, se usa el `tunnel:` del config) y `NOVAHUB_CLOUDFLARED_CONFIG`
(por defecto `~/.cloudflared/config.yml`). Al despublicar o eliminar un servicio se quita su regla
del túnel, pero **el registro DNS se queda** en Cloudflare (cloudflared no puede borrarlo): bórralo
a mano en *DNS → Records* si ya no lo quieres.
