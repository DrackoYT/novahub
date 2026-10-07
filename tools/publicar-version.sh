#!/usr/bin/env bash
# Publica una versión de NovaHub: pone el número en server.py, pasa «Sin publicar» del CHANGELOG a esa versión,
# hace el commit y la etiqueta vX.Y.Z, lo sube y crea la release en GitHub con esas notas (gh).
#
#   tools/publicar-version.sh 1.1.0
#
# Los paneles con el canal estable la verán en su Centro de actualizaciones.
set -euo pipefail
V="${1:?Uso: tools/publicar-version.sh X.Y.Z}"
[[ "$V" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "La versión debe ser X.Y.Z (p. ej. 1.1.0)"; exit 1; }
cd "$(dirname "$0")/.."
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "Hay cambios sin guardar: haz commit antes"; exit 1; }
git rev-parse -q --verify "refs/tags/v$V" >/dev/null && { echo "La versión v$V ya existe"; exit 1; }
NOTES="$(python3 - "$V" <<'PY'
import re, sys, datetime
v = sys.argv[1]
s = open("CHANGELOG.md").read()
m = re.search(r"## Sin publicar\n(.*?)(?=\n## )", s, re.S)
notes = (m.group(1).strip() if m else "")
if not notes:
    sys.exit("No hay nada en «Sin publicar» del CHANGELOG")
s = s.replace(m.group(0), f"## Sin publicar\n\n## {v} — {datetime.date.today()}\n\n{notes}\n", 1)
open("CHANGELOG.md", "w").write(s)
print(notes)
PY
)"
sed -i "s/^VERSION = \"[0-9.]*\"/VERSION = \"$V\"/" server.py
python3 -m py_compile server.py
git add CHANGELOG.md server.py
git commit -qm "Versión $V"
git tag -a "v$V" -m "NovaHub $V"
git push -q                 # en líneas separadas: con «a && b», set -e no se para si falla «a»
git push -q origin "v$V"
gh release create "v$V" --verify-tag --title "NovaHub $V" --notes "$NOTES"
echo "Publicada NovaHub $V"
