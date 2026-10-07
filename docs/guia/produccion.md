# Modo producción para webs

En la ficha de un servicio con `npm run build` (Vite, React, Vue…), **Modo → Pasar a producción**:
NovaHub compila la web y la sirve con `serve.py`, un servidor estático propio (sin dependencias) con
soporte para rutas de SPA, caché larga para los archivos con huella y compresión gzip. Gasta una
fracción de la memoria del modo desarrollo (≈20 MB frente a ≈300 MB en una web Vite). «Recompilar»
aplica los cambios del código; «Actualizar» desde GitHub recompila solo; «Volver a desarrollo»
recupera el comando original. El puerto llega por la variable `NOVAHUB_SERVICE_PORT`.
Se sirve una copia de la compilación (`data/builds/<servicio>/current`), no la carpeta `dist/`: mientras se
recompila, o si la compilación falla, la web publicada sigue funcionando con la versión anterior.

## Consejos para los servicios

- **El comando** se ejecuta con `bash -lc` dentro del directorio de trabajo, así que funcionan
  `source venv/bin/activate && python bot.py`, `npm run start`, `java -Xmx4G -jar server.jar nogui`, etc.
- **No uses comandos que se vayan a segundo plano** (`&`, `nohup`, `--daemon`, `pm2 start`…):
  el panel tiene que ser el que mantenga vivo el proceso para poder vigilarlo y pararlo.
- **Si la consola tarda en mostrar la salida**, el programa está acumulando la salida en un buffer.
  Python ya va sin buffer (`PYTHONUNBUFFERED=1`); en otros casos prueba `stdbuf -oL tu-comando`.
- **Puerto**: si lo indicas, la tarjeta muestra en verde si realmente está escuchando.
  Es la forma más fiable de saber si el servicio "ha arrancado de verdad".
