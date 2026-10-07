# Solución de problemas

Lo primero, casi siempre: mira la **consola del servicio** (en su ficha). Para el propio panel:

```bash
journalctl --user -u novahub -f
```

## No puedo entrar al panel

**Olvidé la contraseña.** En el servidor, por SSH:

```bash
python3 ~/novahub/server.py set-password <usuario>
```

Se aplica al momento, sin reiniciar nada. Tiene que ser en una terminal de verdad, porque pide la contraseña sin
mostrarla.

**Perdí el móvil de la verificación en dos pasos.** Usa uno de tus códigos de recuperación en lugar del código. Si no
te queda ninguno:

```bash
python3 ~/novahub/server.py reset-totp <usuario>
```

**«Demasiados intentos».** Tras 5 intentos fallidos en 5 minutos desde la misma IP, el panel espera. Se quita solo.

## Cloudflare muestra «Bad gateway» (502)

El túnel llega al servidor pero el servicio no contesta.

1. Comprueba que el servicio está **En marcha** y que su **puerto** es el que escucha de verdad.
2. Prueba en el servidor: `curl -I http://127.0.0.1:<puerto>/`.
3. Si es un contenedor recién instalado, espera: la primera vez descarga sus imágenes (mira la consola).
4. Mira la [Vista de red](vigilancia.md#vista-de-red): estado del túnel y dominios publicados.

> [!NOTE]
> Si el servicio está parado o reiniciándose, NovaHub enseña su propia página de «Fuera de servicio» en vez del error
> de Cloudflare.

## Un servicio no arranca

- **«Address already in use»**: otro proceso usa su puerto. Busca cuál en **Procesos**, o cambia el puerto.
  Si son restos de un contenedor anterior que Podman perdió, NovaHub los cierra solo al arrancar.
- **Se reinicia en bucle**: tras varios fallos seguidos espera más entre intentos. Lee las primeras líneas de error de
  la consola: suele ser una variable que falta o un archivo que no existe.
- **Un contenedor no descarga la imagen**: comprueba el nombre (`imagen:etiqueta`) y que el servidor tiene internet.

## Las copias de seguridad fallan

- **«El disco duro de copias no está montado»**: el disco de `NOVAHUB_BACKUP_MOUNT` no está. NovaHub no escribe en el
  disco del sistema por error. Móntalo (`sudo mount -a`) y pulsa «Hacer copia ahora».
- **Copias fuera de casa: «el disco no está conectado»**: el USB no está montado. No es un error: la copia espera a la
  siguiente vez.
- **Menos de 1 GB libre**: no se empieza una copia. Libera espacio o baja el número de copias que se guardan.

## Los discos salen «Sin SMART»

Hace falta `smartmontools` y el ayudante de root. En el Resumen, la tarjeta «Discos y temperatura» muestra los
comandos exactos. Ver [Gráficas, discos y red](vigilancia.md).

## No llegan los avisos

- **Móvil (ntfy)**: en Ajustes → Avisos, pulsa «Enviar prueba». En la app ntfy, comprueba el servidor, el usuario
  `movil` y que estás suscrito al tema `novahub`.
- **Correo (Gmail)**: hace falta una *contraseña de aplicación* de Google, no la normal.
- Cada tipo de aviso se puede activar o desactivar por canal, y hay un límite para no inundarte: uno por servicio y
  tipo cada 10 minutos.
