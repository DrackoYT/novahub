// Service worker de la app (PWA). Guarda la interfaz para poder abrirla sin conexión; nunca guarda la API:
// los datos siempre vienen del servidor. Primero la red (así cada cambio del panel se ve al momento) y,
// si no hay red, lo guardado. Las respuestas redirigidas (p. ej. al login de Cloudflare Access) no se guardan.

const CACHE = "novahub-v1";
const SHELL = [
  "/", "/style.css", "/app.js", "/theme.js", "/favicon.svg", "/manifest.webmanifest",
  "/icons/icon-192.png", "/icons/apple-touch-icon.png",
  "/fonts/bricolage.woff2", "/fonts/unbounded.woff2", "/fonts/plexmono-400.woff2", "/fonts/plexmono-500.woff2", "/fonts/plexmono-600.woff2",
];

self.addEventListener("install", (e) => {
  // uno a uno: si alguno falla (sesión de Access caducada…), los demás se guardan igual
  e.waitUntil(caches.open(CACHE).then((c) => Promise.all(SHELL.map((u) => c.add(u).catch(() => {})))).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/api/")) return;  // lo hace el navegador
  e.respondWith((async () => {
    try {
      const res = await fetch(req);
      if (res.ok && res.type === "basic" && !res.redirected) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req.mode === "navigate" ? "/" : req, copy)).catch(() => {});
      }
      return res;
    } catch {
      const hit = await caches.match(req.mode === "navigate" ? "/" : req);
      return hit || new Response("Sin conexión con el servidor", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
    }
  })());
});
