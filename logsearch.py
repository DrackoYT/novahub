#!/usr/bin/env python3
"""Búsqueda en los logs de NovaHub (sin dependencias).

server.py la usa directamente para búsquedas de texto, y como proceso aparte (con límite de tiempo) para las
expresiones regulares: una expresión mal planteada, como (a+)+$, puede tardar minutos en una sola línea y
Python no puede interrumpirla, así que se ejecuta donde se puede matar sin afectar al panel.

    echo '{"paths": [...], "q": "...", "errors": false, "regex": true, "case": false}' | python3 logsearch.py
"""

import json
import re
import sys

ERROR_WORDS = re.compile(
    r"\b(errors?|err|fail(?:ed|s|ure)?|fallo|fallad[oa]|ha fallado|rechazad[oa]|denegad[oa]|no se pudo|"
    r"fatal|exception|traceback|panic|critical|"
    r"denied|refused|crash(?:ed)?|unhandled|uncaught|segfault|killed|timeout|timed out)\b", re.I)
RED = re.compile(r"\x1b\[(?:[0-9;]*;)?(?:31|91|1;31)m")   # lo que NovaHub (y muchos programas) pintan en rojo
ANSI = re.compile(r"\x1b\[[0-9;?]*[@-~]")
MAX_MATCHES = 500


def scan(paths, q="", errors=False, regex=False, case=False):
    """paths: [(ruta, etiqueta)] del más antiguo al más nuevo. Devuelve las últimas coincidencias con su
    número de línea y dónde resaltar. Lanza re.error si la expresión no es válida."""
    pattern = re.compile(q if regex else re.escape(q), 0 if case else re.I) if q else None
    matches, total, count = [], 0, 0
    for path, label in paths:
        try:
            with open(path, "rb") as f:
                text_all = f.read().decode("utf-8", "replace")
        except FileNotFoundError:
            continue
        for n, raw in enumerate(text_all.splitlines(), 1):
            count += 1
            text = ANSI.sub("", raw).replace("\r", "")
            if errors and not (RED.search(raw) or ERROR_WORDS.search(text)):
                continue
            if pattern:
                spans = [m.span() for m in pattern.finditer(text) if m.end() > m.start()]
                if not spans:
                    continue
            else:
                spans = [m.span() for m in ERROR_WORDS.finditer(text)]
            total += 1
            matches.append({"file": label, "n": n, "text": text[:2000], "spans": [s for s in spans if s[1] <= 2000][:20]})
            if len(matches) > MAX_MATCHES:
                matches.pop(0)  # se quedan las más recientes
    return {"matches": matches, "total": total, "shown": len(matches), "lines": count}


if __name__ == "__main__":
    args = json.load(sys.stdin)
    try:
        out = scan([tuple(p) for p in args["paths"]], args.get("q", ""), args.get("errors", False),
                   args.get("regex", False), args.get("case", False))
    except re.error as e:
        out = {"error": f"Expresión regular no válida: {e}"}
    json.dump(out, sys.stdout)
