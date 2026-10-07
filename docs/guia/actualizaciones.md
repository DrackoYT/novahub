# Centro de actualizaciones

Ajustes → **Actualizaciones** reúne todo lo que se puede actualizar en el servidor. Se comprueba solo cada 6 horas
(y con «Comprobar ahora»), avisa por correo y en el Resumen, y guarda un historial.

| Qué | Cómo |
|---|---|
| **NovaHub** | Canal **estable** (versiones publicadas en GitHub) o **desarrollo** (cada cambio). «Actualizar» hace una copia de `data/`, instala la versión, reinicia el panel y comprueba que responde; si no arranca, **vuelve sola a la anterior** (`updater.py`). Los servicios no se paran. |
| **Sistema** | Paquetes de apt pendientes (Python, Node, núcleo, librerías…), marcando los de **seguridad**. «Solo seguridad» o «Actualizar todo», y opción de instalar solas las de seguridad cada noche. |
| **Reinicio pendiente** | Tras actualizar el núcleo: reinicio ordenado del servidor (para los servicios y reinicia). |
| **Servicios** | Imágenes de contenedores nuevas (se descargan una vez por semana; aplicar es reiniciar), servicios con git con cambios en GitHub y dependencias de cada proyecto (`npm update`, `pip` sin saltos de versión mayor) con copia de seguridad previa. |

NovaHub no es root. Para el sistema usa **un único script con órdenes fijas** (`update`, `upgrade`, `security`, `reboot`),
sin parámetros que lleguen del panel. Se instala una vez:

```bash
sudo install -o root -g root -m 755 tools/novahub-sistema /usr/local/sbin/novahub-sistema
echo "$USER ALL=(root) NOPASSWD: /usr/local/sbin/novahub-sistema" | sudo tee /etc/sudoers.d/novahub-sistema
sudo chmod 440 /etc/sudoers.d/novahub-sistema
```

Las versiones siguen el [versionado semántico](https://semver.org/lang/es/) y los cambios de cada una están en
[`CHANGELOG.md`](../../CHANGELOG.md).
