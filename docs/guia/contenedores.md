# Contenedores (Podman)

Además de programas (un comando), un servicio puede ser un **contenedor** (una imagen de Docker Hub u otro
registro) o un proyecto **docker-compose**. Nuevo servicio → **Contenedor**, o el selector «Tipo» del formulario.

Se usa **Podman sin root**: los contenedores corren como tu usuario, sin servicio de root ni grupo `docker`
(que equivaldría a dar root a quien controle el panel). Instalación:

```bash
sudo apt install -y podman podman-compose passt uidmap
```

- **Contenedor:** imagen (p. ej. `louislam/uptime-kuma:1`), puerto del servidor y del contenedor, carpetas
  (`data:/app/data`; las relativas van dentro del directorio del servicio, que se crea solo) y variables de
  entorno, que se pasan sin aparecer en la lista de procesos. Ejemplos listos: Uptime Kuma, web estática con
  nginx y Minecraft (Paper).
- **Compose:** el directorio del servicio con su `compose.yaml` o `docker-compose.yml`. Los logs de todos los
  contenedores salen en la consola, cada uno con su nombre.
- Se vigilan como cualquier servicio: consola (también para escribirles), reinicio si se caen, comprobación
  de salud, límite de memoria, gráficas, tareas programadas, copias de seguridad y publicación en internet.
  La CPU y la memoria se leen de su cgroup, porque sus procesos no son hijos de NovaHub. La comprobación de salud no
  cuenta fallos hasta que responden por primera vez (máx. 15 min): la primera vez descargan GB de imágenes.
- **Actualizar imagen** descarga la versión nueva y reinicia solo si ha cambiado.
- Al parar, el contenedor recibe su señal de parada con el tiempo de «Espera»; después se elimina (los datos
  quedan en sus carpetas).
