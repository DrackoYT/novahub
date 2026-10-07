# Tu primer servicio

Un **servicio** es cualquier cosa que quieras tener en marcha en el servidor: un bot, una web, un servidor de
Minecraft, un contenedor… NovaHub lo arranca, lo vigila y te deja ver su consola.

## Crear el servicio

1. Pulsa **Nuevo servicio** (arriba a la derecha).
2. Elige qué quieres añadir:
   - **Programa**: cualquier comando, por ejemplo `python3 bot.py` o `npm start`.
   - **Contenedor**: una imagen de Docker Hub, como `nginx:alpine`.
   - **Compose**: una carpeta con su `docker-compose.yml`.
   - **Catálogo de apps**: apps ya preparadas (Vaultwarden, Immich, Nextcloud…). Ver [Catálogo de apps](catalogo.md).
   - **Desde GitHub** o una **plantilla** (web, React + Vite, API, bot de Discord, Flask, Minecraft).
3. Rellena el formulario. A la derecha ves un resumen en vivo de lo que se va a crear.
4. Guarda. El servicio aparece en **Servicios** y puedes encenderlo con su interruptor.

![Formulario de nuevo servicio](../img/nuevo-servicio.png)

## Los campos importantes

| Campo | Qué es |
|---|---|
| Comando | Lo que se ejecuta, con una shell de inicio de sesión (`bash -lc`), así coge tu PATH. Si empiezas por `exec`, el servicio es el propio programa y no una shell intermedia |
| Directorio | Dónde se ejecuta y la carpeta que entra en las copias de seguridad |
| Puerto | Si escucha en uno: sirve para la comprobación de salud y para publicarlo en internet |
| Arrancar con el servidor | Se enciende solo al arrancar NovaHub |
| Reiniciar si se cae | Si termina con error, se vuelve a lanzar (con un límite de intentos) |
| Límite de memoria | Si lo pasa, se reinicia y te avisa |

## La ficha del servicio

Al pulsar un servicio se abre su ficha:

- **Arriba**: encender o apagar, reiniciar, editar y, si es un contenedor o viene de GitHub, actualizar.
- **Cifras**: tiempo encendido, CPU, memoria y puerto, con una gráfica de las últimas horas.
- **Consola**: la salida en directo, con colores. Puedes escribirle y buscar en todo el log. Ver
  [Consola, logs y variables](consola.md).
- **Pestañas**: archivos, Git, variables (.env), copias de seguridad y tareas programadas.

![Ficha de un servicio en tema oscuro](../img/ficha-oscuro.png)

> [!NOTE]
> Los servicios siguen funcionando aunque reinicies o actualices NovaHub: el panel los vuelve a encontrar al arrancar.

## Siguiente paso

Si quieres usarlo desde fuera de casa, sigue con [Publicar en internet](publicar.md).
