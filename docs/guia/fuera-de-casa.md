# Copias fuera de casa

Ajustes → **Copias fuera de casa**: las copias locales de los servicios (`novahub-copias`) y la configuración de NovaHub
(`data/`: servicios, usuarios, ajustes), además de las carpetas de datos grandes de las apps (las fotos de Immich, sin
las miniaturas), van **cifradas** con [restic](https://restic.net) (libre: `sudo apt install restic`)
a uno o varios destinos tuyos, **sin servicios de terceros ni suscripciones**:

- **Disco USB o externo**: una carpeta del disco. Si no está conectado a la hora de la copia, se espera a la siguiente.
- **Otro servidor** por SSH (el de un familiar, una Raspberry…, mejor por Tailscale): NovaHub crea su propia llave SSH
  (`data/ssh/`) y la añades al `authorized_keys` de un usuario de ese servidor.

Copia diaria e incremental (solo viaja lo nuevo), retención de 7 diarias, 4 semanales y 6 mensuales, y cada 30 días se
comprueba el destino y **se restaura de verdad un archivo** para confirmar que sirve. «Recuperar» saca una copia completa a
`~/novahub-recuperado/` sin tocar nada de lo actual. La contraseña de cifrado se genera (o pones la tuya) y se enseña
una vez: **guárdala fuera del servidor**, porque sin ella no se pueden recuperar las copias. En el destino no queda nada
legible sin ella.
