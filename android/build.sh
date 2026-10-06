#!/usr/bin/env bash
# Compila la app de Android de NovaHub sin Gradle (JDK + build-tools de Android).
#
#   android/build.sh https://tu-panel.ejemplo.com
#
# Necesita JAVA_HOME (JDK 17) y ANDROID_HOME con «build-tools;34.0.0» y «platforms;android-34».
# La firma va en ~/.novahub-android/ (fuera del repositorio): guárdala, las actualizaciones necesitan la misma.
set -euo pipefail
URL="${1:?Uso: android/build.sh https://tu-panel.ejemplo.com}"
[[ "$URL" =~ ^https://[A-Za-z0-9.-]+(:[0-9]+)?/?$ ]] || { echo "La dirección debe ser https://dominio (sin rutas)"; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
: "${JAVA_HOME:?Define JAVA_HOME (JDK 17)}"; : "${ANDROID_HOME:?Define ANDROID_HOME}"
BT="$ANDROID_HOME/build-tools/34.0.0"; JAR="$ANDROID_HOME/platforms/android-34/android.jar"
KEYDIR="${NOVAHUB_ANDROID_KEYS:-$HOME/.novahub-android}"
OUT="${NOVAHUB_APK_OUT:-$HERE/build/NovaHub.apk}"
VERSION_CODE="${VERSION_CODE:-$(date +%y%m%d%H)}"
B="$HERE/build"; rm -rf "$B"; mkdir -p "$B/res/values" "$B/gen" "$B/classes" "$B/dex"
export PATH="$JAVA_HOME/bin:$PATH"

echo "· recursos"
cp -r "$HERE/res/." "$B/res/"
python3 - "$B/res/values/strings.xml" "${URL%/}" <<'PY'
import sys, re
from xml.sax.saxutils import escape
p, url = sys.argv[1], sys.argv[2]
s = open(p).read()
open(p, "w").write(re.sub(r'(<string name="panel_url">)[^<]*(</string>)', lambda m: m.group(1) + escape(url) + m.group(2), s))
PY
python3 - "$B/res" <<'PY'  # iconos a partir del generador del repositorio (el orbe de NovaHub)
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "..", "..", "tools"))
from make_icons import orb_icon
for d, px in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
    os.makedirs(f"{sys.argv[1]}/mipmap-{d}", exist_ok=True)
    open(f"{sys.argv[1]}/mipmap-{d}/ic_launcher.png", "wb").write(orb_icon(px, ss=2))
PY
"$BT/aapt2" compile --dir "$B/res" -o "$B/res.zip"
"$BT/aapt2" link -o "$B/base.apk" -I "$JAR" --manifest "$HERE/AndroidManifest.xml" --java "$B/gen" "$B/res.zip" \
  --min-sdk-version 24 --target-sdk-version 34 --version-code "$VERSION_CODE" --version-name 1.0 --auto-add-overlay

echo "· código"
javac -nowarn -source 11 -target 11 -encoding UTF-8 -classpath "$JAR" -d "$B/classes" \
  $(find "$B/gen" "$HERE/src" -name '*.java') 2>&1 | grep -v "^warning\|^Note\|^1 warning" || true
"$BT/d8" --release --min-api 24 --lib "$JAR" --output "$B/dex" $(find "$B/classes" -name '*.class')

echo "· empaquetar y firmar"
python3 - "$B/base.apk" "$B/dex/classes.dex" "$B/unsigned.apk" <<'PY'
import shutil, sys, zipfile
shutil.copy(sys.argv[1], sys.argv[3])
with zipfile.ZipFile(sys.argv[3], "a", zipfile.ZIP_DEFLATED) as z:
    z.write(sys.argv[2], "classes.dex")
PY
"$BT/zipalign" -f -p 4 "$B/unsigned.apk" "$B/aligned.apk"
mkdir -p "$KEYDIR"; chmod 700 "$KEYDIR"
if [ ! -f "$KEYDIR/novahub.keystore" ]; then
  python3 -c "import secrets; print(secrets.token_urlsafe(24))" > "$KEYDIR/clave"; chmod 600 "$KEYDIR/clave"
  keytool -genkeypair -keystore "$KEYDIR/novahub.keystore" -alias novahub -keyalg RSA -keysize 2048 -validity 10000 \
    -storepass "$(cat "$KEYDIR/clave")" -keypass "$(cat "$KEYDIR/clave")" -dname "CN=NovaHub" >/dev/null 2>&1
  chmod 600 "$KEYDIR/novahub.keystore"
  echo "  firma nueva en $KEYDIR (guárdala: las actualizaciones de la app necesitan la misma)"
fi
mkdir -p "$(dirname "$OUT")"
NH_KS_PASS="$(cat "$KEYDIR/clave")" "$BT/apksigner" sign --ks "$KEYDIR/novahub.keystore" --ks-pass env:NH_KS_PASS --key-pass env:NH_KS_PASS --out "$OUT" "$B/aligned.apk"
"$BT/apksigner" verify "$OUT"
echo "Listo: $OUT ($(du -h "$OUT" | cut -f1)) → abre $URL"
