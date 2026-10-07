# Fiabilidad de NovaHub

- **Watchdog de systemd** (`Type=notify`, `WatchdogSec=30` en `novahub.service`): NovaHub avisa a systemd
  cada 10 s mientras su web, su pasarela y sus bucles internos responden; si algo se queda colgado,
  systemd lo reinicia. Tus servicios no se tocan (`KillMode=process`).
- **Hilos vigilados**: si muere el de correo, salud, pasarela o vigilancia, se relanza y se avisa.
- **Reinicios tras un fallo**: NovaHub sabe si la vez anterior se cerró bien; si no, te escribe
  («se ha reiniciado tras un fallo», o «el servidor se ha encendido tras un apagado inesperado»).
- **Autoarranque** = al encender el servidor. Si solo se reinicia NovaHub, lo que apagaste sigue apagado.
- **Vigilante externo** (healthchecks.io u otro servicio con dirección de ping): en ⚙ Ajustes. NovaHub
  manda una señal de vida cada minuto solo si todo responde; si dejan de llegar (corte de luz, sin
  internet, servidor colgado), el servicio externo te avisa. Configura allí 1 min de periodo y 3 de gracia.
- **Túnel**: arranca con `--metrics 127.0.0.1:20241` y su comprobación de salud usa `/ready`, que solo
  responde 200 si hay conexión con Cloudflare.
