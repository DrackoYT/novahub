# Gráficas, discos y red

## Gráficas de uso

En **Resumen** (todo el servidor) y en la ficha de cada servicio hay dos gráficas, CPU y memoria, con
selector **1 h / 24 h**. Al pasar el ratón (o el dedo) se ve el valor de cada momento.

- Una muestra cada 10 s para la gráfica de 1 h y una media cada 5 min para la de 24 h. Se guardan en
  `data/metrics.json` cada 5 min y al cerrar NovaHub, así que sobreviven a un reinicio.
- La CPU del servidor es el % del total; la de un servicio, % de un núcleo (como en `top`: 200 % = dos
  núcleos llenos). En la memoria de un servicio con límite se dibuja el límite como línea roja.
- Los huecos son ratos en que el servicio estaba parado (o NovaHub apagado).

## Discos y temperatura

En el **Resumen**, una tarjeta por disco (sistema, datos, USB…) y otra con las temperaturas:

- **Temperaturas** de la CPU, la gráfica y los SSD NVMe, cada minuto y sin root (`/sys/class/hwmon`). Si pasan del
  límite tres minutos seguidos, avisa (revisa ventiladores y polvo).
- **SMART** de cada disco cada 30 minutos, con `smartctl` en solo lectura a través de `novahub-sistema discos`. No
  despierta a los discos dormidos. Cada disco sale como **Bien**, **Atención** o **Peligro**, con el porqué: el disco se
  da por fallado, sectores reasignados (y si crecen), sectores pendientes o sin corregir, desgaste y reserva de los SSD,
  errores del medio, errores de cable nuevos o temperatura alta. También horas encendido, desgaste y datos escritos.
- **Avisos** (móvil y correo, tipo «Un disco da señales de fallo o algo se calienta demasiado») en cuanto un disco
  empeora, para cambiarlo antes de que falle.

Necesita `sudo apt install smartmontools` y el ayudante `tools/novahub-sistema` instalado (ver Centro de
actualizaciones); si ya lo tenías, vuelve a ejecutar la línea `sudo install …` para que tenga la orden `discos`.

## Vista de red

Pestaña **Red** (tecla `4`):

- **Túnel:** conexiones activas con Cloudflare, centros a los que está conectado (p. ej. `mad05 · mad07`),
  peticiones y errores del servidor (respuestas 5xx). Se leen del servidor de métricas de cloudflared, así que el comando del túnel debe
  llevar `--metrics 127.0.0.1:PUERTO`.
- **Servidor:** IP en la red local y dominio de publicación.
- **Enchufe Tapo:** encendido o apagado, consumo en vatios en este momento (P110/P115), kWh de hoy y del
  mes, desde cuándo está encendido y calidad del Wi-Fi. Se consulta como mucho una vez por minuto.
- **Dominios publicados:** cada regla del `config.yml` del túnel con el servicio al que lleva, su estado
  y si pasa por la pasarela de NovaHub.
