# Contribuir

¡Gracias por el interés! Algunas pautas para que NovaHub siga siendo sencillo de instalar y de mantener:

- **Sin dependencias.** El backend usa solo la biblioteca estándar de Python y la interfaz es HTML, CSS y JavaScript
  sin frameworks, CDN ni paso de compilación. Si una mejora necesita una dependencia, ábrela antes como issue.
- **La interfaz está en español**, igual que los mensajes y los comentarios del código.
- **Seguridad primero.** Cualquier ruta nueva de la API tiene que pasar por `route_permission` (si no, queda solo
  para administradores), y todo dato que se pinte en la interfaz va por `esc()`.
- Antes de enviar cambios: `python3 -m pyflakes server.py` y ESLint sobre `static/app.js` sin avisos, y prueba en una
  instancia aislada (`NOVAHUB_DATA=/tmp/prueba python3 server.py --port 8797`) en vez de en tu panel de verdad.
- Pull requests pequeños y con una explicación de qué cambia y por qué.

Para dudas o ideas, abre un issue.

## Versiones

- Los commits van a `main`; **no** cada commit es una versión.
- Cada cambio para los usuarios se apunta en `CHANGELOG.md`, bajo «Sin publicar».
- Cuando hay un grupo de cambios listo y revisado: `tools/publicar-version.sh X.Y.Z` pone el número en `server.py`,
  mueve «Sin publicar» a esa versión, crea la etiqueta `vX.Y.Z` y la release de GitHub. Los paneles con el canal
  estable la ven en su Centro de actualizaciones.
- Parches (`1.0.1`) para arreglos, menores (`1.1.0`) para funciones nuevas compatibles, mayores (`2.0.0`) si hay que
  hacer algo a mano al actualizar (explícalo en el CHANGELOG).

