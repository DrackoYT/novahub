# Escribir esta documentación

Esta guía son archivos Markdown en `docs/guia/` del repositorio de NovaHub. El panel los muestra en la pestaña
**Docs** y también se leen en GitHub. Van con el código: cada versión de NovaHub trae su documentación al día.

## Añadir una página

1. Crea el archivo en `docs/guia/`, por ejemplo `docs/guia/mi-tema.md`. Empieza con un título `#`.
2. Añádelo al índice, `docs/guia/SUMMARY.md`, en la sección que le toque:

   ```markdown
   ## Servicios
   * [Mi tema](mi-tema.md)
     * [Un subapartado](mi-subtema.md)
   ```

3. Recarga la pestaña **Docs**. La página aparece en el índice, en el buscador y en los botones de anterior y
   siguiente.

El índice usa el mismo formato que GitBook: `# Título` de la guía, `## Sección` para cada grupo y una lista de
enlaces. Las subpáginas van con dos espacios más de sangría. Solo cuentan los archivos de `docs/guia/` que existen.

## Qué se puede usar

| Escribes | Sale |
|---|---|
| `# Título`, `## Apartado`, `### Subapartado` | Títulos. Los `##` y `###` salen en «En esta página» |
| `**negrita**`, `*cursiva*`, `` `código` `` | Formato dentro del texto |
| `- punto` o `1. punto` | Listas; con sangría, listas dentro de listas |
| `` ``` `` al principio y al final | Bloque de código con botón de copiar |
| `\| a \| b \|` y una línea `\|---\|---\|` | Tabla |
| `> texto` | Cita |
| `> [!TIP]`, `> [!NOTE]`, `> [!WARNING]`, `> [!CAUTION]` | Aviso de color (la primera línea de la cita) |
| `[texto](otra-pagina.md)` | Enlace a otra página de la guía; con `#apartado`, a un apartado |
| `[texto](https://…)` | Enlace externo, en una pestaña nueva |
| `![descripción](../img/captura.png)` | Imagen (de la carpeta `docs/`) |

> [!NOTE]
> Por seguridad, el HTML escrito en el Markdown se muestra como texto: no se ejecuta.

## Ejemplo de aviso

```markdown
> [!WARNING]
> Esto borra el disco. Comprueba antes que es el correcto.
```

> [!WARNING]
> Esto borra el disco. Comprueba antes que es el correcto.

## Estilo

- En castellano, de tú, con frases cortas.
- Primero lo que hace la persona y luego el porqué.
- Los nombres de botones y menús, como se ven en el panel: **Ajustes → Copias fuera de casa**.
- Los comandos, en bloques de código listos para copiar.
