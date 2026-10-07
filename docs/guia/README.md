# NovaHub

NovaHub es un panel web para **encender, apagar y vigilar los servicios de tu servidor casero**: bots, webs,
servidores de juegos, contenedores y apps autoalojadas. Es un solo archivo de Python, sin dependencias ni base de datos,
y funciona en cualquier Linux con systemd.

![Resumen del panel](../img/resumen.png)

## Qué puedes hacer

- **Servicios**: programas (cualquier comando), contenedores de Docker Hub con Podman sin root y proyectos
  docker-compose. Encender, apagar, reiniciar, arrancar con el servidor y reiniciar si se caen.
- **Consola en directo** de cada servicio, con búsqueda en todo el log y entrada para escribirle.
- **Vigilancia**: comprobaciones de salud, límite de memoria, gráficas de CPU y RAM, salud de los discos (SMART) y
  temperaturas.
- **Avisos** al móvil (ntfy, sin servicios de terceros) y por correo cuando algo falla.
- **Copias de seguridad** programadas en otro disco y **copias cifradas fuera de casa** con restic.
- **Catálogo de apps** para sustituir servicios de empresas: Vaultwarden (contraseñas), Immich (fotos), Nextcloud…
- **Publicar en internet** con un subdominio a través de Cloudflare Tunnel, sin abrir puertos.
- **Usuarios y roles**, verificación en dos pasos y varios servidores en un mismo panel.
- **Centro de actualizaciones** de NovaHub, del sistema y de los servicios.

## Cómo está organizada esta guía

| Sección | Para qué |
|---|---|
| [Primeros pasos](instalacion.md) | Instalarlo, crear tu primer servicio y publicarlo |
| [Servicios](servicios.md) | Programas, contenedores, el catálogo, la consola y las tareas |
| [Datos y copias](copias.md) | Copias locales y fuera de casa |
| [Vigilancia](vigilancia.md) | Gráficas, discos, red y avisos |
| [Seguridad y acceso](usuarios.md) | Usuarios, verificación en dos pasos y sesión |
| [Mantenimiento](actualizaciones.md) | Actualizaciones, varios servidores, apagado y solución de problemas |
| [Referencia](variables-entorno.md) | Variables de entorno, estructura del código y cómo escribir esta guía |

> [!TIP]
> Usa el buscador de la izquierda: encuentra palabras en todas las páginas, sin importar tildes ni mayúsculas.
