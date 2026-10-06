#!/usr/bin/env python3
"""Servidor estático ligero para el modo producción de NovaHub (sin dependencias).

    python3 serve.py CARPETA --port 8080 [--spa]

- Solo escucha en 127.0.0.1: desde fuera se llega por la pasarela y el túnel de NovaHub.
- --spa: las rutas que no son archivos devuelven index.html (React, Vue… con rutas en el navegador).
- Los archivos con huella en el nombre (assets/app-3f9a1c.js) se guardan en caché un año; index.html
  nunca, para que una compilación nueva se vea al momento.
- Comprime con gzip el texto (HTML, CSS, JS, JSON, SVG) si el navegador lo acepta.
"""

import argparse
import gzip
import mimetypes
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

HASHED = re.compile(r"[-.][0-9A-Za-z_]{8,}\.[a-z0-9]+$")  # app-3f9a1c2b.js, index.BcD3eF4g.css
COMPRESSIBLE = ("text/", "application/javascript", "application/json", "image/svg+xml", "application/xml")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("font/woff2", ".woff2")


class StaticHandler(BaseHTTPRequestHandler):
    server_version = "NovaHub-static"
    sys_version = ""
    root = "."
    spa = False

    def log_message(self, fmt, *args):  # una línea por petición, como un servidor normal
        sys.stdout.write(f"{self.address_string()} {self.command} {self.path} → {args[1] if len(args) > 1 else ''}\n")
        sys.stdout.flush()

    def resolve(self):
        rel = unquote(urlparse(self.path).path).lstrip("/")
        full = os.path.realpath(os.path.join(self.root, rel))
        if full != self.root and not full.startswith(self.root + os.sep):
            return None  # fuera de la carpeta (../ o enlaces): no existe
        if os.path.isdir(full):
            full = os.path.join(full, "index.html")
        if os.path.isfile(full):
            return full
        # SPA: las rutas sin extensión son del enrutador del navegador → index.html
        if self.spa and "." not in os.path.basename(rel):
            index = os.path.join(self.root, "index.html")
            return index if os.path.isfile(index) else None
        return None

    def do_HEAD(self):
        self.serve(head=True)

    def do_GET(self):
        self.serve(head=False)

    def serve(self, head):
        full = self.resolve()
        if not full:
            body = b"404 - no encontrado\n"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if not head:
                self.wfile.write(body)
            return
        with open(full, "rb") as f:
            body = f.read()
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json", "image/svg+xml"):
            ctype += "; charset=utf-8"
        gz = ("gzip" in (self.headers.get("Accept-Encoding") or "") and len(body) > 1024
              and ctype.startswith(COMPRESSIBLE))
        if gz:
            body = gzip.compress(body, 6)
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        if gz:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        name = os.path.basename(full)
        if name == "index.html" or not HASHED.search(name):
            self.send_header("Cache-Control", "no-cache")
        else:
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if not head:
            self.wfile.write(body)


def main():
    ap = argparse.ArgumentParser(description="Servidor estático de NovaHub")
    ap.add_argument("folder")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--spa", action="store_true", help="rutas desconocidas → index.html")
    args = ap.parse_args()
    root = os.path.realpath(args.folder)
    if not os.path.isfile(os.path.join(root, "index.html")):
        sys.exit(f"No hay index.html en {root}: ¿se ha compilado la web?")
    StaticHandler.root, StaticHandler.spa = root, args.spa
    server = ThreadingHTTPServer(("127.0.0.1", args.port), StaticHandler)
    server.daemon_threads = True
    print(f"Sirviendo {root} en http://127.0.0.1:{args.port}" + (" (SPA)" if args.spa else ""), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
