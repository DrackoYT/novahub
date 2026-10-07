# Varios servidores

Un panel puede manejar otros servidores que tengan NovaHub. Con el **selector de arriba** eliges cuál ves: todo el
panel (servicios, consolas, gráficas, copias…) pasa a ser el de ese servidor, con la cabecera en morado para que
se note. En **Resumen** salen los demás con su estado.

Las peticiones viajan por **Tailscale** (red privada y cifrada, sin abrir puertos en el router):

1. En el otro servidor (Linux): instala NovaHub y Tailscale con tu misma cuenta.
2. En su `novahub.service`, abre la puerta para otros paneles en su IP de Tailscale y reinícialo:
   ```ini
   Environment=NOVAHUB_REMOTE_LISTEN=100.x.y.z:8687
   ```
   Esa puerta **solo** acepta llaves de acceso: no tiene interfaz ni inicio de sesión. Si la IP aún no existe al
   arrancar, lo reintenta cada 30 s.
3. En el NovaHub de ese servidor: Ajustes → **Acceso remoto** → crea una llave (`nh_…`). Se muestra una vez; allí
   se guarda solo su huella, y se puede revocar cuando quieras.
4. En tu panel: Ajustes → **Servidores** → nombre, `http://100.x.y.z:8687` y la llave. Antes de guardarlo comprueba
   que conecta y que la llave es de un administrador.

Solo los administradores de este panel pueden usar otros servidores. La llave queda en `data/servers.json`
(permisos 600); la sesión de este panel se alarga mientras trabajas en otro servidor.
