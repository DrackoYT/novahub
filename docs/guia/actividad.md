# Registro de actividad

Ajustes → **Actividad** muestra quién hizo qué y cuándo en el panel: encender, apagar, reiniciar, editar, borrar,
restaurar copias, instalar apps, cambiar usuarios o ajustes, y las entradas al panel (también los intentos fallidos).
Solo lo ven los administradores.

## Buscar y filtrar

- **Buscador**: busca en el texto, el usuario y la IP, sin importar tildes ni mayúsculas. Por ejemplo «restauró»,
  «vaultwarden» o una dirección IP.
- **Usuario**: solo lo que hizo una persona.
- **Tipo**: Servicios, Configuración, Copias, Acceso, Usuarios, Sistema o Apps.
- **Cargar más**: se muestran las 100 más recientes; el botón trae las anteriores.

En la ficha de cada servicio, el apartado **Actividad reciente** enseña lo último que se ha hecho con él.

## Qué se apunta y qué no

Se apunta cada acción que **sale bien** (lo que falla no cambia nada) y cada intento de entrar:

| Se guarda | No se guarda nunca |
|---|---|
| Quién, cuándo y desde qué IP | Contraseñas ni códigos de verificación |
| Qué hizo y sobre qué servicio, usuario o copia | Los valores de las variables (.env) |
| Si fue desde otro panel (llave de acceso remoto) | Lo que se escribe en las consolas |
| | El contenido de los archivos que se editan |

Las consultas (mirar estado, gráficas o logs) y las pruebas (como «Enviar prueba» de los avisos) no se apuntan.

> [!NOTE]
> El registro está en `data/activity.jsonl`, con permisos 600: una línea por acción. Al pasar de 5 MB se guarda como
> `activity.jsonl.1` y se empieza otro, así que siempre quedan entre 5 y 10 MB de historia.
