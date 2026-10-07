# App para el móvil

NovaHub se instala como app (PWA): icono en la pantalla de inicio y se abre a pantalla completa, sin la barra
del navegador. Sigue yendo por el túnel (tu dominio publicado), con Cloudflare Access y la contraseña.

- **Android (Chrome):** Ajustes → «Instalar NovaHub», o menú ⋮ → «Instalar aplicación».
- **iPhone (Safari):** Compartir → «Añadir a pantalla de inicio».

La interfaz queda guardada en el móvil (`static/sw.js`), así que abre aunque no haya conexión y avisa de que
no puede hablar con el servidor; reintenta sola. Los datos (la API) nunca se guardan: siempre vienen del
servidor. Con «Pedir la contraseña al recargar» activado, la app la pide cada vez que se abre.
Los iconos se generan con `python3 tools/make_icons.py`.

## App de Android (APK), para móviles sin navegador ni Google Play

`android/` es una app mínima (una WebView a pantalla completa, sin Gradle) que abre tu panel. Todo se abre dentro,
también el inicio de sesión de Cloudflare Access; las descargas van a «Descargas».

```bash
# una vez: JDK 17 y las herramientas de Android en ~/android (sin sudo, ~750 MB)
#   JAVA_HOME=~/android/jdk  ANDROID_HOME=~/android/sdk  con «build-tools;34.0.0» y «platforms;android-34»
JAVA_HOME=~/android/jdk ANDROID_HOME=~/android/sdk NOVAHUB_APK_OUT=data/app/NovaHub.apk \
  android/build.sh https://tu-panel.ejemplo.com
```

La firma se crea la primera vez en `~/.novahub-android/` (fuera del repositorio): guárdala, porque para instalar una
versión nueva encima de la anterior hace falta la misma. Con el APK en `data/app/NovaHub.apk`, sale el botón
**Descargar la app para Android** en Ajustes → App para el móvil: descárgalo en el PC, pásalo al móvil y ábrelo con
el gestor de archivos.

Google no deja iniciar sesión con su cuenta dentro de una app (WebView), así que para Cloudflare Access añade el
método **One-time PIN** (te manda un código por correo): Zero Trust → Settings → Authentication → Login methods.
