# Tareas programadas

Pestaña **Tareas** en la ficha de cada servicio. Cada tarea es una acción a una hora, ciertos días de la semana:

- **Encender, apagar o reiniciar.** Para que un servicio solo funcione en un horario, dos tareas:
  encender a las 09:00 y apagar a las 23:00.
- **Escribir en la consola** del proceso (p. ej. `say Reinicio en 5 minutos` en Minecraft).
- **Ejecutar un comando** en la carpeta del servicio, con sus variables de entorno. Se corta a los 10 min.

Se ejecutan aunque no tengas el panel abierto; lo que pasa queda en la consola del servicio y, si una
falla, llega un aviso por correo. «Probar» la lanza en el momento. Si NovaHub estaba reiniciándose justo
a esa hora, la tarea se lanza igualmente hasta 3 minutos tarde (nunca dos veces).
