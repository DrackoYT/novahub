# Estructura del código

```
server.py          backend (API + gestor de procesos + consola por SSE)
static/            interfaz web (HTML/CSS/JS sin frameworks) y app para el móvil (manifiesto, sw.js, iconos)
serve.py           servidor estático del modo producción
catalogo.json      catálogo de apps autoalojadas (imagen, puertos, carpetas, variables y notas)
updater.py         actualiza NovaHub desde fuera y vuelve atrás si la versión nueva no arranca
logsearch.py       búsqueda en los logs (las expresiones regulares van en un proceso aparte con límite de tiempo)
tapo.py            control del enchufe Tapo
tools/             utilidades (generar los iconos de la app)
novahub.service    unidad de systemd
data/              se crea al arrancar (no subir a git)
```
