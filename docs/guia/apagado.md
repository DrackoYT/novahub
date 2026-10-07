# Apagar el servidor y el enchufe Tapo

El botón ⏻ de la barra superior para todos los servicios (con su comando de parada), programa en el
enchufe Tapo un corte de corriente dentro de 90 s y apaga el servidor con `systemctl poweroff`.
Se habla con el enchufe por la red local: no hace falta Alexa ni la nube.

1. **Permiso para apagar** (una vez):
   ```bash
   echo "$USER ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff" | sudo tee /etc/sudoers.d/novahub-poweroff
   sudo chmod 440 /etc/sudoers.d/novahub-poweroff && sudo visudo -c
   ```
2. **Enchufe Tapo** (opcional; sin él el servidor se apaga igual pero el enchufe sigue encendido):
   ```bash
   python3 -m venv --without-pip .venv
   curl -fsSL https://bootstrap.pypa.io/get-pip.py | .venv/bin/python
   .venv/bin/pip install python-kasa
   ```
   Crea `data/tapo.json` con la IP del enchufe (fíjala en el router) y tu cuenta Tapo, y protégelo:
   ```json
   {"host": "192.168.0.50", "username": "email@cuenta-tapo", "password": "..."}
   ```
   `chmod 600 data/tapo.json`, y comprueba: `.venv/bin/python tapo.py status` y `.venv/bin/python tapo.py test`
   (programa un «encender» inofensivo en 30 s para verificar que el enchufe acepta cuentas atrás).
3. **Encendido automático**: en la BIOS activa *Restore on AC Power Loss → Power On*. Así, al encender el
   enchufe (app Tapo, Alexa o botón) el servidor arranca solo, y NovaHub levanta los servicios con autoarranque.
