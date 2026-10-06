#!/usr/bin/env python3
"""Genera los iconos de la app (PWA) en static/icons/ sin dependencias: el orbe de NovaHub sobre fondo
oscuro, a sangre (sirve como icono «maskable»: el orbe cabe en la zona segura del 80 %).

    python3 tools/make_icons.py
"""

import os
import struct
import zlib

BG = (27, 24, 34)          # --screen: el mismo fondo oscuro de la consola
STOPS = [(0.0, (255, 255, 255)), (0.3, (184, 156, 255)), (0.75, (106, 53, 240)), (1.0, (74, 31, 199))]
GLOW = (123, 77, 255)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "icons")


def blend(dst, src, a):
    return tuple(round(d + (s - d) * a) for d, s in zip(dst, src))


def orb_icon(size, ss=3):
    """Orbe con luz arriba a la izquierda y halo morado; supermuestreo ss×ss para bordes suaves."""
    c, r = size / 2, size * 0.27
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            acc = [0.0, 0.0, 0.0]
            for sy in range(ss):
                for sx in range(ss):
                    px, py = x + (sx + 0.5) / ss, y + (sy + 0.5) / ss
                    d = ((px - c) ** 2 + (py - c) ** 2) ** 0.5
                    if d <= r:
                        lx, ly = px - (c - r * 0.3), py - (c - r * 0.4)
                        t = min(1.0, (lx * lx + ly * ly) ** 0.5 / (r * 1.55))
                        for (t0, c0), (t1, c1) in zip(STOPS, STOPS[1:]):
                            if t <= t1:
                                k = (t - t0) / (t1 - t0)
                                col = tuple(a + (b - a) * k for a, b in zip(c0, c1))
                                break
                    else:
                        g = max(0.0, 1 - (d - r) / (size * 0.48 - r))
                        col = blend(BG, GLOW, 0.55 * g ** 2.2)
                    for i in range(3):
                        acc[i] += col[i]
            row += bytes(round(v / (ss * ss)) for v in acc)
        rows.append(bytes(row))
    raw = zlib.compress(b"".join(rows), 9)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", raw) + chunk(b"IEND", b""))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, size in (("icon-192.png", 192), ("icon-512.png", 512), ("apple-touch-icon.png", 180)):
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(orb_icon(size))
        print(f"static/icons/{name} ({size}×{size})")
