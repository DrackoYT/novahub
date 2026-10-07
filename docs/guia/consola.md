# Consola, logs y variables

## Buscar en los logs

En la consola de cada servicio, el campo **Buscar en todo el log** (o la tecla `/`) busca en el log entero,
el actual y el anterior rotado, no solo en lo que hay en pantalla. Muestra las coincidencias con su número de
línea y resaltadas (las 500 más recientes), y se actualiza solo mientras está abierta.

- **Solo errores:** líneas con palabras de error (error, failed, exception, traceback, rechazada…) o que el
  programa pinta en rojo, como los fallos que anota NovaHub.
- **`.*`** para expresiones regulares y **Aa** para distinguir mayúsculas.
- `Esc` o ✕ vuelven a la consola en directo.

## Variables (.env)

Pestaña **Variables** en la ficha: el `.env` del proyecto como tabla nombre → valor, con los valores ocultos
(el ojo muestra cada uno). Se puede elegir otro archivo (`.env.local`, `.env.production`…) y crear el `.env` si
no existe.

- Conserva comentarios, líneas en blanco y el formato de lo que no cambia; lo nuevo va al final. Pone comillas
  cuando hace falta (espacios, `#`, comillas…).
- Guarda la versión anterior (como el editor) y avisa si el archivo cambió desde que lo abriste.
- Un `.env` nuevo se crea con permisos 600 (solo tu usuario).
- **Aviso si el archivo iría a GitHub**: si no está en `.gitignore` o ya está en el repositorio.
- Si una variable está repetida, cuenta la última (como en dotenv y en el shell) y al guardar queda una.
- Casi todos los programas leen el `.env` al arrancar: tras guardar sale «Reiniciar para aplicar».

Las variables que se ponen en «Editar» del servicio son otra cosa: las pasa NovaHub al arrancarlo y se guardan
en `data/services.json`.

## Identidad de git

Los commits que se hacen desde el panel (pestaña Git) se firman con el nombre y el correo de
**Ajustes → Git**, que es la configuración global de git del usuario (`git config --global user.name/user.email`).
Si no están puestos, el commit avisa en vez de inventarse un autor.
