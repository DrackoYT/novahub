"use strict";

// ───────────────────────── utilidades ─────────────────────────

const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const ICON = {
  power: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 3v8M6.3 7.2a8 8 0 1 0 11.4 0"/></svg>',
  plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
  logout: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/></svg>',
  home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/></svg>',
  grid: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><rect x="3" y="3" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="2"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="2"/></svg>',
  globe: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/></svg>',
  search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
  back: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>',
  restart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 15.5-6.2L21 8M21 3v5h-5M21 12a9 9 0 0 1-15.5 6.2L3 16M3 21v-5h5"/></svg>',
  edit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg>',
  download: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></svg>',
  expand: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>',
  close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>',
  activity: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h4l3-8 4 16 3-8h4"/></svg>',
  folder: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 6.5A2.5 2.5 0 0 1 5.5 4h3.6a2 2 0 0 1 1.5.7L12 6.3h6.5A2.5 2.5 0 0 1 21 8.8v8.7a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17.5z"/></svg>',
  file: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>',
  git: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="6" cy="6" r="2.5"/><circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="8" r="2.5"/><path d="M6 8.5v7M18 10.5c0 4-6 3-11 6"/></svg>',
  upload: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21V9M7 14l5-5 5 5M5 3h14"/></svg>',
  sun: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
  box: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5M12 13v8"/></svg>',
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
  users: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6.5 6.5 0 0 1 4 6"/></svg>',
  server: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 7.5h.01M7 16.5h.01"/></svg>',
  mail: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
  lock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>',
  phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="2" width="12" height="20" rx="2.5"/><path d="M11 18h2"/></svg>',
  settings: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>',
  key: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="15" r="4"/><path d="m10.8 12.2 8.7-8.7M17 6l2.5 2.5M14.5 8.5 17 11"/></svg>',
  eye: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
  eyeOff: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.6 5.1A9.6 9.6 0 0 1 12 5c6.4 0 10 7 10 7a17 17 0 0 1-3 3.9M6.6 6.6A17 17 0 0 0 2 12s3.6 7 10 7a9.4 9.4 0 0 0 5.4-1.6M9.9 9.9a3 3 0 0 0 4.2 4.2M3 3l18 18"/></svg>',
  clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  archive: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="5" rx="1.5"/><path d="M5 9v9a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9M10 13h4"/></svg>',
  moon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>',
};

// Marca: el orbe de «Nebulosa» con el nombre en Unbounded.
const BRAND = `<span class="orb" aria-hidden="true"></span><span class="wordmark">NovaHub</span>`;

const STATUS_LABEL = {
  running: "En marcha",
  stopped: "Detenido",
  starting: "Iniciando…",
  stopping: "Deteniendo…",
  crashed: "Error",
  retrying: "Reintentando",
};
const isOn = (s) => s.status === "running" || s.status === "starting" || s.status === "retrying";
const statusHTML = (s) => `<span class="status">${STATUS_LABEL[s.status]}</span>`;
// Tecla de encendido: hundida y morada mientras el servicio está en marcha.
function keyHTML(s) {
  const busy = s.status === "starting" || s.status === "stopping";
  return `<button class="key${busy ? " busy" : ""}" role="switch" aria-checked="${isOn(s)}" data-act="toggle" data-perm="operate" data-id="${esc(s.id)}"
    title="${isOn(s) ? "Apagar" : "Encender"}" aria-label="${isOn(s) ? "Apagar" : "Encender"} ${esc(s.name)}">${ICON.power}</button>`;
}
const pct = (a, b) => (b ? (a / b) * 100 : 0);
// Estado de la comprobación de salud en palabras; null si no aplica.
function healthText(s) {
  if (s.health_mode === "off") return { text: "Desactivada", cls: "dim-text" };
  const h = s.health;
  if (s.status !== "running" || !h) return null;
  if (h.state === "starting") return { text: "Esperando a que arranque", cls: "dim-text" };
  if (h.state === "ok") return { text: `Responde · ${h.ms} ms · ${fmtAgo(h.at)}`, cls: "ok-text" };
  return { text: `No responde (${h.fails}/3) · ${h.detail}`, cls: "bad-text" };
}
// medidor de uso; ámbar desde el 75 %, rojo desde el 90 %
const meterHTML = (p) => `<div class="meter${p >= 90 ? " crit" : p >= 75 ? " hot" : ""}"><i style="width:${Math.min(100, Math.max(0, p)).toFixed(1)}%"></i></div>`;

// Tema: claro/oscuro según el sistema, o el elegido con el botón (se recuerda en este navegador).
function currentTheme() {
  return document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}
function toggleTheme() {
  const next = currentTheme() === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem("nh-theme", next); } catch { /* sin almacenamiento: solo esta visita */ }
  const btn = $("[data-act=theme]");
  if (btn) btn.innerHTML = next === "dark" ? ICON.sun : ICON.moon;
}

function fmtDuration(sec) {
  if (sec == null) return "—";
  sec = Math.floor(sec);
  if (sec < 60) return `${sec}s`;
  const m = Math.floor(sec / 60), h = Math.floor(m / 60), d = Math.floor(h / 24);
  if (d) return `${d}d ${h % 24}h`;
  if (h) return `${h}h ${String(m % 60).padStart(2, "0")}m`;
  return `${m}m`;
}

// Cada etiqueta tiene siempre el mismo color (8 colores, elegido por hash del nombre).
function tapeClass(tag) {
  let h = 0;
  for (const ch of tag.toLowerCase()) h = (h * 31 + ch.codePointAt(0)) >>> 0;
  return `t${h % 8}`;
}
const tagsHTML = (tags) => tags.length
  ? `<div class="tags">${tags.map((t) => `<span class="tag ${tapeClass(t)}">${esc(t)}</span>`).join("")}</div>`
  : "";

// Enlace para abrir el servicio: su URL, o la IP del servidor + el puerto.
function openUrl(s) {
  if (s.url) return s.url;
  if (!s.port) return null;
  let host = location.hostname;
  const loopback = ["localhost", "127.0.0.1", "::1", "[::1]"].includes(host);
  if (loopback && ui.lanIp) host = ui.lanIp; // panel abierto por un túnel/redirección local
  else if (!/^[\d.]+$|^\[/.test(host) && ui.lanIp) host = ui.lanIp; // panel abierto por dominio (Cloudflare)
  return `http://${host}:${s.port}`;
}
function fmtBytes(b) {
  if (b == null) return "—";
  const u = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
  return `${b.toFixed(b < 10 && i ? 1 : 0)} ${u[i]}`;
}
function fmtAgo(epoch) {
  if (!epoch) return "—";
  const s = Math.max(0, Date.now() / 1000 - epoch);
  if (s < 60) return "hace un momento";
  if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
  if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
  if (s < 86400 * 30) return `hace ${Math.floor(s / 86400)} días`;
  return new Date(epoch * 1000).toLocaleDateString("es-ES");
}
function fmtTime(epoch) {
  if (!epoch) return "—";
  return new Date(epoch * 1000).toLocaleString("es-ES", { dateStyle: "short", timeStyle: "medium" });
}

function toast(msg, kind = "") {
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = msg;
  $("#toasts").appendChild(el);
  setTimeout(() => el.remove(), 3800);
}

// Con Cloudflare Access delante, al caducar la sesión de Google las peticiones se redirigen a su
// login (otro dominio) y el navegador las bloquea. Si es eso, se recarga para ir a identificarse.
async function checkAccessSession() {
  try {
    const probe = await fetch("/", { redirect: "manual", cache: "no-store" });
    if (probe.type === "opaqueredirect") location.reload();
  } catch { /* sin conexión de verdad */ }
}

async function api(method, url, body) {
  const headers = { "X-NovaHub": "1" };
  if (Date.now() - ui.lastActivity < 60000) headers["X-NovaHub-Activity"] = "1";
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch(apiUrl(url), { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined, credentials: "same-origin" });
  } catch {
    setOffline(true);
    await checkAccessSession();
    throw new Error("Sin conexión con el servidor");
  }
  if ($("#offline") && !$("#offline").hidden) setOffline(false);
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && url !== "/api/login") {
    if (!ui.locked) showLogin(ui.unlocked ? "La sesión se ha cerrado por inactividad. Vuelve a entrar." : "");
    throw new Error("Sesión caducada");
  }
  if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
  return data;
}

// ───────────────────────── estado global ─────────────────────────

const app = $("#app");
const ui = {
  lastActivity: 0,   // último clic o tecla del usuario
  unlocked: false,   // contraseña introducida en esta carga de la página
  locked: false,     // pantalla de contraseña a la vista
  services: [],
  tag: null,
  q: "",
  current: null,     // servicio abierto en la vista de detalle
  timers: [],
  es: null,          // EventSource de la consola
  cards: new Map(),  // id -> elemento de tarjeta
  history: [],       // historial de comandos enviados
};

function clearView() {
  ui.timers.forEach(clearInterval);
  ui.timers = [];
  ui.backupPoll = null;
  if (ui.es) { ui.es.close(); ui.es = null; }
  ui.term = null;
  ui.current = null;
  ui.cards.clear();
}
function every(ms, fn) { ui.timers.push(setInterval(fn, ms)); }

// ───────────────────────── login ─────────────────────────

// Sin red al abrir (sobre todo en la app): pantalla de espera que reintenta sola al volver la conexión.
function showOffline() {
  clearView();
  app.innerHTML = `
    <div class="login-wrap">
      <div class="login module">
        <div class="brand">${BRAND}</div>
        <p class="sub">No hay conexión con el servidor</p>
        <p class="offline-text">Comprueba que tienes internet. Si el servidor está apagado o sin red, NovaHub no puede responder.</p>
        <button class="btn primary" type="button" id="retry">Reintentar</button>
      </div>
    </div>`;
  $("#retry").addEventListener("click", () => start());
  every(15000, () => navigator.onLine && start());
}
window.addEventListener("online", () => { if ($("#retry")) start(); });

function showLogin(reason = "") {
  clearView();
  ui.locked = true;
  app.innerHTML = `
    <div class="login-wrap">
      <div class="login module">
        <div class="brand">${BRAND}</div>
        <p class="sub">Panel de servicios de tu servidor</p>
        <form id="login-form">
          ${reason ? `<p class="nt-ok login-note">${esc(reason)}</p>` : ""}
          <div class="form-error" id="login-error"></div>
          <label class="field"><span>Usuario</span><input id="user" name="username" autocomplete="username" autocapitalize="off" spellcheck="false" required></label>
          <label class="field"><span>Contraseña</span><input id="pw" type="password" name="password" autocomplete="current-password" required></label>
          <button class="btn primary" type="submit">Entrar</button>
        </form>
      </div>
    </div>`;
  let last = "";
  try { last = localStorage.getItem("nh-user") || ""; } catch { /* sin almacenamiento */ }
  $("#user").value = last;
  (last ? $("#pw") : $("#user")).focus();
  $("#login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector("button");
    btn.disabled = true;
    try {
      const username = e.target.username.value.trim().toLowerCase();
      await api("POST", "/api/login", { username, password: e.target.password.value });
      try { localStorage.setItem("nh-user", username); } catch { /* sin almacenamiento */ }
      ui.unlocked = true;
      ui.locked = false;
      ui.lastActivity = Date.now();
      start();
    } catch (err) {
      $("#login-error").textContent = err.message;
      btn.disabled = false;
    }
  });
}

// ───────────────────────── esqueleto ─────────────────────────

const NAV = [
  ["overview", "#/", "Resumen", "1", ICON.home],
  ["services", "#/servicios", "Servicios", "2", ICON.grid],
  ["tasks", "#/procesos", "Procesos", "3", ICON.activity, "admin"],
  ["network", "#/red", "Red", "4", ICON.globe, "admin"],
];

// Permisos del usuario (los decide el servidor, que rechaza lo demás; aquí solo se esconde lo que no puede usar)
const can = (perm) => !!ui.me?.perms?.includes(perm);
function applyPerms() {
  for (const p of ["view", "operate", "console", "edit", "admin"]) document.body.classList.toggle(`p-${p}`, can(p));
}

function shell() {
  app.innerHTML = `
    <header class="topbar">
      <a class="brand" href="#/" aria-label="NovaHub · inicio">${BRAND}</a>
      <nav class="nav" aria-label="Secciones">
        ${NAV.filter((n) => !n[5] || can(n[5])).map(([key, href, label, k, icon]) => `<a href="${href}" data-nav="${key}" title="${label} (${k})">${icon}<span>${label}</span></a>`).join("")}
      </nav>
      <div class="top-actions">
        <div class="srv-pick" id="srv-pick" hidden></div>
        <span class="lcd host-chip" id="host-chip"></span>
        <button class="btn primary" data-act="new" data-perm="admin">${ICON.plus}<span>Nuevo servicio</span></button>
        <a class="btn icon" href="#/ajustes" data-nav="settings" title="Ajustes" aria-label="Ajustes">${ICON.settings}</a>
        <button class="btn icon" data-act="theme" title="Cambiar tema claro/oscuro" aria-label="Cambiar tema">${currentTheme() === "dark" ? ICON.sun : ICON.moon}</button>
        <button class="btn icon" data-act="poweroff" data-perm="admin" title="Apagar el servidor" aria-label="Apagar el servidor">${ICON.power}</button>
        <button class="btn icon ghost" data-act="logout" title="Cerrar sesión" aria-label="Cerrar sesión">${ICON.logout}</button>
      </div>
    </header>
    <main id="main"></main>`;
  $(".topbar .brand").addEventListener("dblclick", (e) => { e.preventDefault(); if (ui.hasRoadmap) location.hash = "#/mejoras"; });
}

async function refreshSystem() {
  try {
    const s = await api("GET", "/api/system");
    ui.sys = s;
    ui.lanIp = s.lan_ip;
    ui.publishDomain = s.publish_domain;
    ui.user = s.user;
    ui.host = s.hostname;
    if (ui.server === "local" && ui.localHost !== s.hostname) { ui.localHost = s.hostname; drawServerPicker(); }
    const chip = $("#host-chip");
    if (chip) chip.textContent = `${ui.me?.username || s.user}@${s.hostname}`;
    drawKpis();
    drawUpdatesBanner();
    if (!ui.current && ui.services.length) { drawList(); drawOverview(); } // los enlaces «Abrir» dependen de la IP del servidor
  } catch { /* silencioso */ }
}

// ───────────────────────── gráficas de uso ─────────────────────────
// SVG a mano: una serie por gráfica (CPU o memoria), un solo eje, huecos donde no hay datos
// (servicio parado o NovaHub apagado) y una línea con la lectura al pasar el ratón o el dedo.

const CHART_H = 150, CHART_PAD = { r: 10, t: 10, b: 22 };
// Techo «redondo» para el eje: 1, 2, 2,5, 5 o 10 × 10ⁿ (300 MB, 500 MB… en lugar de 324 MB)
const niceCeil = (v) => { const e = 10 ** Math.floor(Math.log10(v)); return [1, 2, 2.5, 5, 10].find((m) => m * e >= v) * e; };

function usageRange() {
  try { return localStorage.getItem("nh-range") === "24h" ? "24h" : "1h"; } catch { return "1h"; }
}

// Bloque con las dos gráficas; `key` es «system» o el id de un servicio.
function usageHTML(key) {
  const r = usageRange();
  return `
    <div class="section-title usage-head">
      <h2>${key === "system" ? "Uso del servidor" : "Uso"}</h2>
      <div class="seg" role="group" aria-label="Periodo">
        <button type="button" class="chip ${r === "1h" ? "active" : ""}" data-range="1h" aria-pressed="${r === "1h"}">1 h</button>
        <button type="button" class="chip ${r === "24h" ? "active" : ""}" data-range="24h" aria-pressed="${r === "24h"}">24 h</button>
      </div>
    </div>
    <section class="charts" id="charts" data-key="${esc(key)}">
      <div class="module chart" data-metric="cpu"><div class="chart-head"><span class="label">CPU</span><span class="chart-now"></span></div><div class="chart-plot"></div></div>
      <div class="module chart" data-metric="mem"><div class="chart-head"><span class="label">Memoria</span><span class="chart-now"></span></div><div class="chart-plot"></div></div>
    </section>`;
}

function setupUsage() {
  const box = $("#charts");
  if (!box) return;
  ui.usage = null;
  box.parentElement.querySelector(".usage-head .seg").addEventListener("click", (e) => {
    const r = e.target.closest("[data-range]")?.dataset.range;
    if (!r) return;
    try { localStorage.setItem("nh-range", r); } catch { /* sin almacenamiento: solo esta vez */ }
    e.currentTarget.querySelectorAll("[data-range]").forEach((b) => {
      b.classList.toggle("active", b.dataset.range === r);
      b.setAttribute("aria-pressed", String(b.dataset.range === r));
    });
    refreshUsage();
  });
  refreshUsage();
  every(10000, refreshUsage);
  window.addEventListener("resize", ui.onResize = ui.onResize || (() => ui.usage && drawUsage(ui.usage)));
}

async function refreshUsage() {
  const box = $("#charts");
  if (!box) return;
  try {
    const d = await api("GET", `/api/metrics?range=${usageRange()}&service=${encodeURIComponent(box.dataset.key)}`);
    if ($("#charts") !== box) return;
    ui.usage = d;
    drawUsage(d);
  } catch { /* silencioso: se reintenta en 10 s */ }
}

function drawUsage(d) {
  const box = $("#charts");
  if (!box) return;
  const sys = box.dataset.key === "system";
  const last = d.points[d.points.length - 1];
  const fresh = last && d.to - last[0] < d.step * 2.5;
  const memMax = sys ? d.mem_total : niceCeil(Math.max(2 ** 20, (d.memory_limit || 0) * 2 ** 20 * 1.05, ...d.points.map((p) => p[2] * 1.15)) / 2 ** 20) * 2 ** 20;
  const cpuMax = sys ? 100 : Math.max(100, Math.ceil(Math.max(0, ...d.points.map((p) => p[1])) / 50) * 50);
  const specs = {
    cpu: { i: 1, max: cpuMax, fmt: (v) => `${v.toFixed(v < 10 ? 1 : 0)} %`, axis: (v) => `${Math.round(v)}%`,
      now: fresh ? `${last[1].toFixed(1)} %` : "—", note: sys ? `de ${d.cpus} núcleos` : "100 % = 1 núcleo" },
    mem: { i: 2, max: memMax || 1, fmt: fmtBytes, axis: fmtBytes, limit: !sys && d.memory_limit ? d.memory_limit * 2 ** 20 : null,
      now: fresh ? fmtBytes(last[2]) : "—", note: sys ? `de ${fmtBytes(d.mem_total)}` : (d.memory_limit ? `límite ${fmtBytes(d.memory_limit * 2 ** 20)}` : "") },
  };
  box.querySelectorAll(".chart").forEach((el) => {
    const sp = specs[el.dataset.metric];
    el.querySelector(".chart-now").innerHTML = `<b>${sp.now}</b>${sp.note ? ` <span class="dim-text">${esc(sp.note)}</span>` : ""}`;
    drawChart(el.querySelector(".chart-plot"), d, sp);
  });
}

function drawChart(plot, d, sp) {
  const labels = [0, 0.5, 1].map((f) => sp.axis(sp.max * f));
  const P = { ...CHART_PAD, l: Math.max(30, Math.max(...labels.map((t) => t.length)) * 6.6 + 12) };  // sitio para el rótulo más largo
  const W = Math.max(240, plot.clientWidth), H = CHART_H;
  const iw = W - P.l - P.r, ih = H - P.t - P.b;
  const x = (t) => P.l + ((t - d.from) / (d.to - d.from)) * iw;
  const y = (v) => P.t + ih - (Math.min(v, sp.max) / sp.max) * ih;
  const pts = d.points;
  // tramos continuos: un salto de más de 2,5 pasos es un hueco (parado o sin datos)
  const segs = [];
  pts.forEach((p, k) => {
    if (!k || p[0] - pts[k - 1][0] > d.step * 2.5) segs.push([]);
    segs[segs.length - 1].push(p);
  });
  const line = (s) => s.map((p, k) => `${k ? "L" : "M"}${x(p[0]).toFixed(1)},${y(p[sp.i]).toFixed(1)}`).join("");
  const area = (s) => `${line(s)}L${x(s[s.length - 1][0]).toFixed(1)},${P.t + ih}L${x(s[0][0]).toFixed(1)},${P.t + ih}Z`;
  const grid = [0, 0.5, 1].map((f, k) => {
    const gy = P.t + ih - f * ih;
    return `<line x1="${P.l}" x2="${W - P.r}" y1="${gy}" y2="${gy}" class="ch-grid"/>` +
      `<text x="${P.l - 8}" y="${gy + 4}" class="ch-axis" text-anchor="end">${esc(labels[k])}</text>`;
  }).join("");
  const span = d.to - d.from, ticks = [];
  for (let k = 0; k <= 4; k++) ticks.push(d.from + (span * k) / 4);
  const hhmm = (t) => new Date(t * 1000).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
  const xAxis = ticks.map((t, k) => `<text x="${x(t)}" y="${H - 5}" class="ch-axis" text-anchor="${k === 0 ? "start" : k === 4 ? "end" : "middle"}">${k === 4 ? "ahora" : hhmm(t)}</text>`).join("");
  const limit = sp.limit ? `<line x1="${P.l}" x2="${W - P.r}" y1="${y(sp.limit)}" y2="${y(sp.limit)}" class="ch-limit"/>` +
    `<text x="${P.l + 6}" y="${y(sp.limit) - 5}" class="ch-axis ch-limit-text">límite</text>` : "";
  const vals = pts.map((p) => p[sp.i]);
  const summary = vals.length
    ? `mínimo ${sp.fmt(Math.min(...vals))}, media ${sp.fmt(vals.reduce((a, b) => a + b, 0) / vals.length)}, máximo ${sp.fmt(Math.max(...vals))}`
    : "sin datos";
  plot.innerHTML = `
    <svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(summary)}">
      ${grid}${limit}
      ${segs.map((s) => `<path d="${area(s)}" class="ch-area"/><path d="${line(s)}" class="ch-line"/>`).join("")}
      ${segs.filter((s) => s.length === 1).map((s) => `<circle cx="${x(s[0][0])}" cy="${y(s[0][sp.i])}" r="2.5" class="ch-dot"/>`).join("")}
      ${xAxis}
      <g class="ch-hover" hidden><line y1="${P.t}" y2="${P.t + ih}" class="ch-cross"/><circle r="4.5" class="ch-mark"/></g>
    </svg>
    ${pts.length ? "" : `<div class="chart-empty">Recogiendo datos: una muestra cada 10 s${d.range === "24h" ? " (la de 24 h es una media cada 5 min)" : ""}</div>`}
    <div class="ch-tip" hidden></div>`;
  if (!pts.length) return;
  const svg = plot.querySelector("svg"), hover = svg.querySelector(".ch-hover"), tip = plot.querySelector(".ch-tip");
  const move = (e) => {
    const r = svg.getBoundingClientRect(), mx = e.clientX - r.left;
    let best = pts[0];
    for (const p of pts) if (Math.abs(x(p[0]) - mx) < Math.abs(x(best[0]) - mx)) best = p;
    if (Math.abs(x(best[0]) - mx) > Math.max(24, (iw / (span / d.step)) * 3)) { hover.hidden = tip.hidden = true; return; }  // en un hueco
    const px = x(best[0]), py = y(best[sp.i]);
    hover.hidden = tip.hidden = false;
    hover.querySelector("line").setAttribute("x1", px); hover.querySelector("line").setAttribute("x2", px);
    hover.querySelector("circle").setAttribute("cx", px); hover.querySelector("circle").setAttribute("cy", py);
    tip.innerHTML = `<b>${esc(sp.fmt(best[sp.i]))}</b><span>${new Date(best[0] * 1000).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" })}</span>`;
    tip.style.left = `${Math.min(Math.max(px, 50), W - 50)}px`;
    tip.style.top = `${Math.max(py - 12, 0)}px`;
  };
  svg.addEventListener("pointermove", move);
  svg.addEventListener("pointerdown", move);
  svg.addEventListener("pointerleave", () => { hover.hidden = tip.hidden = true; });
}

// Aviso en el resumen si hay actualizaciones (solo administradores, solo este servidor)
function drawUpdatesBanner() {
  const el = $("#ov-updates"), u = ui.sys?.updates;
  if (!el) return;
  const parts = !u ? [] : [u.novahub ? "versión nueva de NovaHub" : "", u.security ? `${u.security} de seguridad` : u.system ? `${u.system} del sistema` : "",
    u.reboot ? "reinicio pendiente" : ""].filter(Boolean);
  const html = parts.length ? `<a class="upd-banner ${u.security || u.reboot ? "warn" : ""}" href="#/ajustes/actualizaciones">${ICON.download}
    <span><b>Actualizaciones:</b> ${parts.join(" · ")}</span><span class="grow"></span><span>Ver →</span></a>` : "";
  if (el._html !== html) { el.innerHTML = html; el._html = html; }
}

function viewNoAccess() {
  $("#main").innerHTML = `<div class="empty"><h2>Sin permiso</h2>
    <p>Tu usuario (${esc(ui.me?.role_label || "")}) no puede abrir esta página. Pídele acceso a un administrador.</p>
    <a class="btn" href="#/">Volver al resumen</a></div>`;
}

// ───────────────────────── varios servidores ─────────────────────────
// Con otro servidor elegido arriba, las peticiones van a /api/remote/<id>/… y este panel las reenvía.

const HUB_ONLY = /^\/api\/(me|login|logout|account|servers|remote)(\/|$|\?)/;
function apiUrl(url) {
  if (!ui.server || ui.server === "local" || !url.startsWith("/api/") || HUB_ONLY.test(url)) return url;
  return `/api/remote/${encodeURIComponent(ui.server)}/${url.slice(5)}`;
}

async function loadServers() {
  if (!can("admin")) { ui.servers = []; return; }
  try { ui.servers = (await api("GET", "/api/servers")).servers; } catch { ui.servers = ui.servers || []; }
  if (ui.server !== "local" && !ui.servers.some((s) => s.id === ui.server)) ui.server = "local";
  drawServerPicker();
}

// En el resumen de este servidor: los demás, con su estado (clic para cambiar a ese)
function drawServerCards() {
  const el = $("#ov-servers");
  if (!el || ui.server !== "local" || !ui.servers?.length) { if (el) el.innerHTML = ""; return; }
  el.innerHTML = `<div class="section-title"><h2>Otros servidores</h2><a href="#/ajustes/servidores">Gestionar →</a></div>
    <div class="srv-cards">${ui.servers.map((x) => {
      const st = x.status || {};
      return `<button type="button" class="module srv-card" data-srv="${esc(x.id)}" ${st.online ? "" : "disabled"}>
        <span class="srv-head"><span class="srv-dot ${st.online ? "on" : "off"}"></span><b>${esc(x.name)}</b></span>
        <small>${st.online ? `${st.running} de ${st.services} en marcha${st.crashed ? ` · <span class="bad-text">${st.crashed} con error</span>` : ""}
          · RAM ${Math.round(pct(st.mem_used, st.mem_total))} % · encendido ${fmtDuration(st.uptime)}` : `<span class="bad-text">${esc(st.error || "Sin conexión")}</span>`}</small>
      </button>`;
    }).join("")}</div>`;
}

function serverName() {
  return ui.server === "local" ? ui.localHost || "Este servidor" : ui.servers.find((s) => s.id === ui.server)?.name || ui.server;
}

function drawServerPicker() {
  const el = $("#srv-pick");
  if (!el) return;
  el.hidden = !can("admin");  // siempre visible para administradores: así se descubre que se pueden añadir servidores
  document.body.classList.toggle("remote-mode", ui.server !== "local");
  if (el.hidden) return;
  const dot = (s) => `<span class="srv-dot ${s.status?.online === false ? "off" : "on"}"></span>`;
  el.innerHTML = `
    <button type="button" class="btn srv-btn" data-srv="menu" aria-haspopup="true">${ICON.server}<span>${esc(serverName())}</span></button>
    <div class="srv-menu module" hidden>
      <button type="button" data-srv="local" class="${ui.server === "local" ? "active" : ""}"><span class="srv-dot on"></span>Este servidor${ui.localHost ? ` <span class="dim-text">· ${esc(ui.localHost)}</span>` : ""}</button>
      ${ui.servers.map((s) => `<button type="button" data-srv="${esc(s.id)}" class="${ui.server === s.id ? "active" : ""}" ${s.status?.online === false ? 'title="Sin conexión"' : ""}>
        ${dot(s)}${esc(s.name)}</button>`).join("")}
      <a href="#/ajustes/servidores">${ui.servers.length ? "Gestionar servidores…" : `${ICON.plus}Añadir otro servidor…`}</a>
    </div>`;
}

function switchServer(id) {
  ui.server = id;
  try { localStorage.setItem("nh-server", id); } catch { /* sin almacenamiento */ }
  ui.services = [];
  ui.gitRepo = null;
  drawServerPicker();
  toast(`Ahora ves: ${serverName()}`, "ok");
  if (location.hash === "#/" || location.hash === "") route(); else location.hash = "#/";
}

document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-srv]");
  const menu = $("#srv-pick .srv-menu");
  if (!b) { if (menu && !e.target.closest("#srv-pick")) menu.hidden = true; return; }
  if (b.dataset.srv === "menu") { menu.hidden = !menu.hidden; return; }
  menu.hidden = true;
  if (b.dataset.srv !== ui.server) switchServer(b.dataset.srv);
});

// ───────────────────────── vista: resumen ─────────────────────────

function viewOverview() {
  $("#main").innerHTML = `
    <section class="page-head">
      <div>
        <h1 class="page-title">Resumen</h1>
        <p class="page-sub" id="ov-sub">Estado del servidor y de tus servicios</p>
      </div>
    </section>
    <div id="ov-updates"></div>
    <section class="kpis" id="kpis"></section>
    <div id="ov-servers"></div>
    ${usageHTML("system")}
    <div class="section-title"><h2>Servicios</h2><a href="#/servicios">Ver todos →</a></div>
    <section class="module rows" id="ov-rows"></section>`;
  drawKpis();
  drawServerCards();
  setupUsage();
  refreshOverview();
  every(3000, refreshOverview);
}

async function refreshOverview() {
  try {
    ui.services = (await api("GET", "/api/services")).services;
    drawOverview();
  } catch { /* el 401 ya redirige */ }
}

// Módulo de cifra: rótulo, valor grande, medidor opcional y lectura en LCD.
function kpiHTML(label, value, lcd, p) {
  return `<div class="module kpi">
    <span class="label">${label}</span>
    <span class="kpi-value">${value}</span>
    ${p != null ? meterHTML(p) : ""}
    ${lcd ? `<span class="lcd">${lcd}</span>` : ""}
  </div>`;
}

function drawKpis() {
  const el = $("#kpis"), s = ui.sys;
  if (!el || !s) return;
  const cpu = pct(s.load[0], s.cpus), mem = pct(s.mem_used, s.mem_total), disk = pct(s.disk_used, s.disk_total);
  const html =
    kpiHTML("CPU", `${cpu.toFixed(0)}<small>%</small>`, `carga ${s.load[0].toFixed(2)} · ${s.cpus} núcleos`, cpu) +
    kpiHTML("Memoria", fmtBytes(s.mem_used), `de ${fmtBytes(s.mem_total)}`, mem) +
    kpiHTML("Disco", `${disk.toFixed(0)}<small>%</small>`, `${fmtBytes(s.disk_used)} / ${fmtBytes(s.disk_total)}`, disk) +
    kpiHTML("Encendido", fmtDuration(s.uptime), esc(s.hostname), null);
  if (el._html !== html) { el.innerHTML = html; el._html = html; }
}

function drawOverview() {
  const el = $("#ov-rows");
  if (!el) return;
  const all = ui.services;
  const running = all.filter((s) => s.status === "running").length;
  const crashed = all.filter((s) => s.status === "crashed").length;
  const sub = $("#ov-sub");
  if (sub) sub.innerHTML = all.length
    ? `<b>${running} de ${all.length}</b> servicios en marcha${crashed ? ` · <span class="bad-text">${crashed} con error</span>` : ""}`
    : "Aún no hay servicios";
  // primero los que tienen error, luego los encendidos
  const order = { crashed: 0, retrying: 0, starting: 1, stopping: 1, running: 2, stopped: 3 };
  const list = [...all].sort((a, b) => order[a.status] - order[b.status]);
  const html = list.length ? list.map((s) => {
    const url = s.status === "running" ? openUrl(s) : null;
    return `<a class="row" href="#/s/${esc(s.id)}" data-status="${s.status}">
      ${statusHTML(s)}
      <span class="row-name">${esc(s.name)}</span>
      <span class="row-meta">
        ${s.subdomain && url ? `<span class="opt url">${esc(url.replace(/^https?:\/\//, ""))}</span>` : ""}
        ${s.status === "running" ? `<span class="num">${fmtDuration(s.uptime)}</span>` : ""}
      </span>
    </a>`;
  }).join("") : `<div class="row-empty">Añade tu primer servicio con «Nuevo servicio».</div>`;
  if (el._html !== html) { el.innerHTML = html; el._html = html; }
}

// ───────────────────────── vista: red ─────────────────────────

function viewNetwork() {
  $("#main").innerHTML = `
    <section class="page-head">
      <div>
        <h1 class="page-title">Red</h1>
        <p class="page-sub" id="net-sub">Túnel de Cloudflare, dominios publicados y enchufe</p>
      </div>
    </section>
    <section class="net-grid" id="net-cards"></section>
    <div class="section-title"><h2>Dominios publicados</h2></div>
    <section class="module rows" id="net-hosts"></section>`;
  refreshNetwork();
  every(10000, refreshNetwork);
}

async function refreshNetwork() {
  try {
    const d = await api("GET", "/api/network");
    drawNetwork(d);
    if (d.tapo.loading) setTimeout(() => $("#net-cards") && refreshNetwork(), 4000);  // el enchufe tarda unos segundos
  } catch { /* el 401 ya redirige */ }
}

const wifiText = (rssi) => (rssi == null ? null : rssi >= -50 ? "Excelente" : rssi >= -60 ? "Buena" : rssi >= -70 ? "Regular" : "Débil");
const kwh = (v) => `${v.toLocaleString("es-ES", { maximumFractionDigits: v < 10 ? 2 : 1 })} kWh`;

function drawNetwork(d) {
  const cards = $("#net-cards"), hostsEl = $("#net-hosts");
  if (!cards) return;
  const cell = (k, v) => `<div><dt>${k}</dt><dd>${v}</dd></div>`;
  const dash = '<span class="dim-text">—</span>';

  const t = d.tunnel;
  let tunnel;
  if (!t) {
    tunnel = `<div class="module net-card"><span class="label">Túnel</span><p class="dim-text">No hay ningún servicio con <code>cloudflared tunnel run</code>.</p></div>`;
  } else {
    const on = t.status === "running";
    const conn = t.connections;
    const state = !on ? t.status : conn == null ? "starting" : conn > 0 ? "running" : "crashed";
    const big = !on ? STATUS_LABEL[t.status] : conn == null ? (t.metrics_error ? "Sin métricas" : "—") : `${conn}<small> de 4</small>`;
    tunnel = `<a class="module net-card" href="#/s/${esc(t.sid)}" data-status="${state}">
      <div class="net-top"><span class="label">Túnel · conexiones</span>${statusHTML({ status: state })}</div>
      <span class="kpi-value">${big}</span>
      <dl class="readout">
        ${cell("Centros de Cloudflare", t.locations.length ? esc(t.locations.join(" · ")) : dash)}
        ${cell("Peticiones", t.requests != null ? t.requests.toLocaleString("es-ES") : dash)}
        ${cell('<span title="Respuestas 5xx: un servicio publicado caído o que falla. Cerrar una consola en directo no cuenta.">Errores del servidor (5xx)</span>', t.errors != null ? `<span class="${t.errors ? "warn-text" : ""}">${t.errors.toLocaleString("es-ES")}</span>` : dash)}
      </dl>
    </a>`;
  }

  const p = d.tapo;
  let plug;
  if (!p.configured) {
    plug = `<div class="module net-card"><span class="label">Enchufe</span>
      <p class="dim-text">Sin configurar. Ejecuta <code>.venv/bin/python tapo.py setup</code> (ver README).</p></div>`;
  } else if (p.loading) {
    plug = `<div class="module net-card"><span class="label">Enchufe</span><p class="dim-text">Consultando el enchufe…</p></div>`;
  } else if (p.error) {
    plug = `<div class="module net-card" data-status="crashed"><div class="net-top"><span class="label">Enchufe</span>${statusHTML({ status: "crashed" })}</div>
      <p class="bad-text">${esc(p.error)}</p></div>`;
  } else {
    const wifi = wifiText(p.rssi);
    plug = `<div class="module net-card" data-status="${p.on ? "running" : "stopped"}">
      <div class="net-top"><span class="label">Enchufe · ${esc(p.alias || p.model)}</span><span class="status">${p.on ? "Encendido" : "Apagado"}</span></div>
      <span class="kpi-value">${p.watts != null ? `${p.watts.toLocaleString("es-ES", { maximumFractionDigits: 1 })}<small> W</small>` : esc(p.model)}</span>
      <dl class="readout">
        ${p.today_kwh != null ? cell("Consumo hoy · este mes", `${kwh(p.today_kwh)} · ${kwh(p.month_kwh)}`) : ""}
        ${cell("Encendido desde", p.on_since ? `${fmtTime(p.on_since)}` : dash)}
        ${cell("Wi-Fi", wifi ? `${wifi} <span class="dim-text">· ${p.rssi} dBm</span>` : dash)}
        ${cell("Modelo · IP", `${esc(p.model)} · <span class="mono">${esc(p.host || "")}</span>`)}
      </dl>
      <span class="net-foot dim-text">Leído ${fmtAgo(p.at)}</span>
    </div>`;
  }

  const lan = `<div class="module net-card">
      <span class="label">Servidor</span>
      <span class="kpi-value mono-value">${esc(d.lan_ip || "—")}</span>
      <dl class="readout">
        ${cell("Dominio", d.domain ? esc(d.domain) : '<span class="dim-text">sin publicar (NOVAHUB_DOMAIN)</span>')}
        ${cell("Dominios activos", d.hosts.length)}
      </dl>
    </div>`;

  const html = tunnel + lan + plug;
  if (cards._html !== html) { cards.innerHTML = html; cards._html = html; }

  const sub = $("#net-sub");
  if (sub && t) {
    const ok = t.status === "running" && t.connections > 0;
    sub.innerHTML = ok ? `Túnel <b>conectado</b> con ${t.connections} conexiones a Cloudflare` : '<span class="bad-text">El túnel no está conectado: las webs publicadas no se ven desde fuera</span>';
  }

  const rows = d.hosts.length ? d.hosts.map((h) => `
    <div class="row net-host" data-status="${h.status || "stopped"}">
      ${h.status ? statusHTML({ status: h.status }) : '<span class="status">Sin servicio</span>'}
      <a class="row-name url" href="https://${esc(h.host)}" target="_blank" rel="noopener">${esc(h.host)} ↗</a>
      <span class="row-meta">
        ${h.sid ? `<a href="#/s/${esc(h.sid)}" class="net-svc">${esc(h.name)}</a>` : h.name ? `<span class="net-svc">${esc(h.name)}</span>` : ""}
        <span class="opt" title="${h.gateway ? "Pasa por la pasarela de NovaHub (página de aviso si el servicio está caído)" : ""}">${esc(h.target)}${h.gateway ? " · pasarela" : ""}</span>
      </span>
    </div>`).join("") : `<div class="row-empty">Aún no hay nada publicado. Pon un subdominio al editar un servicio.</div>`;
  if (hostsEl._html !== rows) { hostsEl.innerHTML = rows; hostsEl._html = rows; }
}

// ───────────────────────── vista: mejoras (oculta) ─────────────────────────
// No está en las pestañas: se abre con doble clic en el logo, la tecla «m» o #/mejoras.

function viewRoadmap() {
  $("#main").innerHTML = `
    <section class="page-head">
      <div>
        <h1 class="page-title">Mejoras</h1>
        <p class="page-sub">Lista de lo que queda por hacer en NovaHub, de más a menos importante. Marca cada una al terminarla.</p>
      </div>
      <div class="rm-head-actions"><div id="rm-progress"></div>
        <button type="button" class="btn sm" id="rm-close" hidden title="Guardar las hechas bajo una versión para que no se vean">Cerrar versión…</button></div>
    </section>
    <section class="module rm-list" id="rm-todo"></section>
    <form class="module rm-add" id="rm-add">
      <label class="field"><span>Apuntar una idea nueva</span>
        <input id="rm-title" maxlength="120" placeholder="p. ej. «Modo oscuro automático por horario»" autocomplete="off"></label>
      <button class="btn primary" type="submit">${ICON.plus}Añadir</button>
    </form>
    <div class="section-title" id="rm-done-title"></div>
    <section class="module rm-list done" id="rm-done"></section>
    <div id="rm-versions"></div>`;
  const handler = async (e) => {
    const box = e.target.closest("[data-done]");
    const del = e.target.closest("[data-del]");
    try {
      if (box) ui.roadmapItems = (await api("PUT", `/api/roadmap/${box.dataset.done}`, { done: box.checked })).items;
      else if (del && await confirmDialog("Borrar mejora", "Se quitará de la lista.", "Borrar")) {
        ui.roadmapItems = (await api("DELETE", `/api/roadmap/${del.dataset.del}`)).items;
      } else return;
      drawRoadmap();
    } catch (err) { toast(err.message, "error"); }
  };
  $("#rm-todo").addEventListener("change", handler);
  $("#rm-done").addEventListener("change", handler);
  $("#rm-todo").addEventListener("click", (e) => { if (e.target.closest("[data-del]")) handler(e); });
  $("#rm-done").addEventListener("click", (e) => { if (e.target.closest("[data-del]")) handler(e); });
  $("#rm-versions").addEventListener("change", handler);
  $("#rm-close").addEventListener("click", async () => {
    const dlg = modal(`<form method="dialog" id="rmv-form"><header><h2>Cerrar versión</h2></header>
      <div class="body"><p>Las mejoras hechas se guardan bajo esta versión, en un desplegable cerrado, y dejan de verse en la lista.</p>
        <label class="field"><span>Versión</span><input id="rmv-name" placeholder="1.1" autocomplete="off"></label></div>
      <footer><button class="btn ghost" value="no">Cancelar</button><button class="btn primary" value="yes">Guardar</button></footer></form>`, "small");
    $("#rmv-name", dlg).focus();
    dlg.addEventListener("close", async () => {
      if (dlg.returnValue !== "yes") return;
      try { ui.roadmapItems = (await api("POST", "/api/roadmap/version", { version: $("#rmv-name", dlg).value })).items; drawRoadmap(); toast("Versión cerrada", "ok"); }
      catch (err) { toast(err.message, "error"); }
    });
  });
  $("#rm-add").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = $("#rm-title");
    try {
      ui.roadmapItems = (await api("POST", "/api/roadmap", { title: input.value })).items;
      input.value = "";
      drawRoadmap();
      toast("Mejora apuntada al final de la lista", "ok");
    } catch (err) { toast(err.message, "error"); }
  });
  api("GET", "/api/roadmap").then((d) => { ui.roadmapItems = d.items; drawRoadmap(); }).catch((e) => toast(e.message, "error"));
}

function drawRoadmap() {
  const all = ui.roadmapItems || [];
  const items = all.filter((i) => !i.version);  // lo de versiones cerradas va aparte, en desplegables
  const todo = items.filter((i) => !i.done);
  const done = items.filter((i) => i.done).sort((a, b) => (b.done_at || 0) - (a.done_at || 0));
  const versions = [...new Set(all.filter((i) => i.version).map((i) => i.version))]
    .sort((a, b) => b.localeCompare(a, "es", { numeric: true }));
  const row = (i, n) => `
    <label class="rm-item" data-tag="${esc(i.tag)}">
      <input type="checkbox" data-done="${esc(i.id)}" ${i.done ? "checked" : ""} aria-label="Marcar «${esc(i.title)}» como hecha">
      <span class="rm-check" aria-hidden="true"></span>
      ${n != null ? `<span class="rm-rank num">${String(n).padStart(2, "0")}</span>` : ""}
      <span class="rm-text">
        <span class="rm-title">${esc(i.title)}</span>
        ${i.desc ? `<span class="rm-desc">${esc(i.desc)}</span>` : ""}
        ${i.done && i.done_at ? `<span class="rm-desc">Hecha ${fmtAgo(i.done_at)}</span>` : ""}
      </span>
      <span class="tag ${tapeClass(i.tag)}">${esc(i.tag)}</span>
      ${i.custom ? `<button type="button" class="btn sm icon ghost" data-del="${esc(i.id)}" title="Borrar" aria-label="Borrar «${esc(i.title)}»">${ICON.trash}</button>` : ""}
    </label>`;
  $("#rm-progress").innerHTML = `<span class="lcd">${done.length}/${items.length} hechas</span>`;
  $("#rm-todo").innerHTML = todo.length ? todo.map((i, k) => row(i, k + 1)).join("") : '<div class="row-empty">No queda nada pendiente.</div>';
  $("#rm-done-title").innerHTML = done.length ? `<h2>Hechas · ${done.length}</h2>` : "";
  $("#rm-done").hidden = !done.length;
  $("#rm-done").innerHTML = done.map((i) => row(i, null)).join("");
  $("#rm-close").hidden = !done.length;
  $("#rm-versions").innerHTML = versions.map((v) => {
    const list = all.filter((i) => i.version === v).sort((a, b) => (b.done_at || 0) - (a.done_at || 0));
    return `<details class="module rm-version"><summary><b>${esc(v)}v</b> <span class="dim-text">· ${list.length} mejora${list.length === 1 ? "" : "s"} hecha${list.length === 1 ? "" : "s"}</span></summary>
      <div class="rm-list done">${list.map((i) => row(i, null)).join("")}</div></details>`;
  }).join("");
}

// ───────────────────────── vista: procesos ─────────────────────────

function viewTasks() {
  ui.tasks = ui.tasks || { sort: "rss", q: "" };
  $("#main").innerHTML = `
    <section class="page-head">
      <div>
        <h1 class="page-title">Procesos</h1>
        <p class="page-sub">Qué está usando la memoria y la CPU del servidor</p>
      </div>
    </section>
    <section class="module mem" id="mem"></section>
    <div class="section-title"><h2>Por aplicación</h2></div>
    <section class="module rows" id="groups"></section>
    <div class="section-title"><h2>Todos los procesos</h2></div>
    <section class="toolbar">
      <label class="search">${ICON.search}<input id="pq" type="search" placeholder="Buscar proceso…" aria-label="Buscar proceso"></label>
      <div class="filters" id="psort">
        <button class="chip" data-sort="rss">Más memoria</button>
        <button class="chip" data-sort="cpu">Más CPU</button>
      </div>
    </section>
    <section class="module ptable" id="procs"></section>`;
  const q = $("#pq");
  q.value = ui.tasks.q;
  q.addEventListener("input", () => { ui.tasks.q = q.value; drawTasks(); });
  $("#psort").addEventListener("click", (e) => {
    const b = e.target.closest("[data-sort]");
    if (b) { ui.tasks.sort = b.dataset.sort; drawTasks(); }
  });
  $("#procs").addEventListener("click", (e) => {
    const b = e.target.closest("[data-kill]");
    if (b) killProcess(+b.dataset.kill);
  });
  refreshTasks();
  every(3000, refreshTasks);
}

async function refreshTasks() {
  try {
    ui.tasks.data = await api("GET", "/api/processes");
    drawTasks();
  } catch { /* el 401 ya redirige */ }
}

function drawTasks() {
  const d = ui.tasks?.data, memEl = $("#mem");
  if (!d || !memEl) return;
  const m = d.mem;
  const w = (x) => `${Math.max(0, (x / m.total) * 100).toFixed(2)}%`;
  memEl.innerHTML = `
    <div class="mem-head">
      <div><span class="label">Memoria</span><div class="kpi-value">${fmtBytes(m.used)} <small>en uso de ${fmtBytes(m.total)}</small></div></div>
      <span class="lcd">CPU ${pct(d.load[0], d.cpus).toFixed(0)}% · carga ${d.load[0].toFixed(2)}</span>
    </div>
    <div class="membar" role="img" aria-label="Memoria: ${fmtBytes(m.used)} en uso, ${fmtBytes(m.cache)} en caché, ${fmtBytes(m.free)} libre">
      <i class="used" style="width:${w(m.used)}"></i><i class="cache" style="width:${w(m.cache)}"></i>
    </div>
    <div class="legend">
      <span><i class="used"></i>En uso <b>${fmtBytes(m.used)}</b></span>
      <span><i class="cache"></i>Caché <b>${fmtBytes(m.cache)}</b></span>
      <span><i class="free"></i>Libre <b>${fmtBytes(m.free)}</b></span>
      ${m.swap_total ? `<span>Swap <b>${fmtBytes(m.swap_used)}</b> de ${fmtBytes(m.swap_total)}</span>` : ""}
    </div>
    <p class="mem-note">La caché es memoria que Linux usa para acelerar el disco y libera en cuanto un programa la necesita: no cuenta como «en uso».</p>`;

  const top = d.groups[0]?.rss || 1;
  $("#groups").innerHTML = d.groups.slice(0, 12).map((g) => `
    <div class="row grow-row">
      <span class="row-name">${esc(g.name)}</span>
      ${g.kind === "service" ? '<span class="status svc">Servicio</span>' : ""}
      <span class="dim-text gcount">${g.count} proceso${g.count > 1 ? "s" : ""}</span>
      <span class="gbar"><i style="width:${((g.rss / top) * 100).toFixed(1)}%"></i></span>
      <span class="row-meta"><span>CPU ${g.cpu.toFixed(1)}%</span><b class="num">${fmtBytes(g.rss)}</b></span>
    </div>`).join("");

  document.querySelectorAll("#psort [data-sort]").forEach((b) => b.classList.toggle("active", b.dataset.sort === ui.tasks.sort));
  const q = ui.tasks.q.trim().toLowerCase();
  let list = d.processes.filter((p) => !q || `${p.pid} ${p.app} ${p.name} ${p.user} ${p.cmd}`.toLowerCase().includes(q));
  list = [...list].sort((a, b) => (ui.tasks.sort === "cpu" ? (b.cpu || 0) - (a.cpu || 0) : b.rss - a.rss));
  const shown = list.slice(0, q ? 300 : 60);
  $("#procs").innerHTML = `
    <div class="prow phead"><span>PID</span><span>Proceso</span><span>Usuario</span><span class="r">CPU</span><span class="r">Memoria</span><span></span></div>
    ${shown.map((p) => `
      <div class="prow">
        <span class="num dim-text">${p.pid}</span>
        <span class="pname"><b>${esc(p.app)}</b><small class="mono" title="${esc(p.cmd)}">${esc(p.cmd)}</small></span>
        <span class="dim-text">${esc(p.user)}</span>
        <span class="r num">${p.cpu == null ? "…" : `${p.cpu.toFixed(1)}%`}</span>
        <span class="r num"><b>${fmtBytes(p.rss)}</b></span>
        <span class="r">${p.own && p.kind !== "service" ? `<button class="btn sm" data-kill="${p.pid}" title="Cerrar este proceso">Cerrar</button>` : ""}</span>
      </div>`).join("")}
    ${list.length > shown.length ? `<div class="row-empty">Se muestran ${shown.length} de ${list.length}. Usa el buscador para encontrar el resto.</div>` : ""}
    ${!list.length ? '<div class="row-empty">Ningún proceso coincide con la búsqueda.</div>' : ""}`;
}

async function killProcess(pid) {
  const p = ui.tasks?.data?.processes.find((x) => x.pid === pid);
  if (!p) return;
  const ok = await confirmDialog("Cerrar proceso",
    `Se pedirá a «${p.app}» (PID ${pid}) que se cierre. Si es parte de otro programa, como VS Code, ese programa puede dejar de funcionar.`, "Cerrar proceso");
  if (!ok) return;
  try {
    await api("POST", `/api/processes/${pid}/kill`, {});
    toast(`Señal de cierre enviada a ${p.app} (PID ${pid})`, "ok");
    setTimeout(refreshTasks, 800);
  } catch (e) { toast(e.message, "error"); }
}

// ───────────────────────── vista: lista ─────────────────────────

function viewList() {
  $("#main").innerHTML = `
    <section class="page-head">
      <div>
        <h1 class="page-title">Servicios</h1>
        <p class="page-sub">Enciende, apaga y vigila cada servicio</p>
      </div>
      <div id="summary"></div>
    </section>
    <section class="toolbar">
      <label class="search">${ICON.search}<input id="q" type="search" placeholder="Buscar…" aria-label="Buscar"></label>
      <div class="filters" id="filters"></div>
    </section>
    <section class="grid" id="grid"></section>`;
  const q = $("#q");
  q.value = ui.q;
  q.addEventListener("input", () => { ui.q = q.value; drawList(); });

  $("#filters").addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    ui.tag = chip.dataset.tag || null;
    drawList();
  });

  const grid = $("#grid");
  grid.addEventListener("click", (e) => {
    if (e.target.closest("[data-act], a")) return; // interruptor y enlaces van por su cuenta
    const card = e.target.closest(".card");
    if (card) location.hash = `#/s/${card.dataset.id}`;
  });
  grid.addEventListener("keydown", (e) => {
    const card = e.target.closest(".card");
    if (card && e.target === card && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      location.hash = `#/s/${card.dataset.id}`;
    }
  });

  refreshList();
  every(3000, refreshList);
}

async function refreshList() {
  try {
    ui.services = (await api("GET", "/api/services")).services;
    drawList();
  } catch { /* el 401 ya redirige */ }
}

function cardHTML(s) {
  const foot = [];
  if (s.status === "running") foot.push(`<span><span class="k">Activo</span><span class="v">${fmtDuration(s.uptime)}</span></span>`);
  else if (s.status === "crashed" && s.last_exit != null) foot.push(`<span><span class="k">Salida</span><span class="v bad-text">${s.last_exit}</span></span>`);
  if (s.status === "running" && s.memory != null) foot.push(`<span><span class="k">RAM</span><span class="v">${fmtBytes(s.memory)}</span></span>`);
  if (s.port) {
    foot.push(`<span title="${s.listening ? "El puerto está escuchando" : "El puerto no está escuchando"}"><span class="k">Puerto</span>` +
      `<span class="v ${s.listening ? "ok-text" : "dim-text"}">${s.port}</span></span>`);
  }
  if (!foot.length) foot.push(`<span class="dim-text">Detenido</span>`);
  if (s.mode === "prod") foot.push(`<span><span class="k">Modo</span><span class="v">producción</span></span>`);
  if (s.backup?.last_name) {
    foot.push(`<span title="Última copia de seguridad · ${esc(fmtTime(s.backup.last_ok_at))}"><span class="k">Copia</span>` +
      `<span class="v">${esc(s.backup.last_name.split("_").slice(0, 2).join("_"))}</span></span>`);
  }
  if (s.status === "running" && s.health?.state === "failing") foot.unshift(`<span class="bad-text"><b>No responde</b></span>`);
  const url = s.status === "running" ? openUrl(s) : null;
  const link = url
    ? `<a class="card-link" href="${esc(url)}" target="_blank" rel="noopener">${s.subdomain ? ICON.globe : ""}<span>${esc(url.replace(/^https?:\/\//, ""))}</span> ↗</a>`
    : "";
  return `
    <div class="card-top">
      <div class="grow">
        ${statusHTML(s)}
        <h3 class="card-name">${esc(s.name)}</h3>
      </div>
      ${keyHTML(s)}
    </div>
    ${s.description ? `<p class="card-desc">${esc(s.description)}</p>` : ""}
    ${link}
    ${tagsHTML(s.tags)}
    <footer class="card-foot">${foot.join("")}</footer>`;
}

function drawList() {
  const grid = $("#grid");
  if (!grid) return;
  const all = ui.services;

  // filtros por etiqueta
  const tags = [...new Set(all.flatMap((s) => s.tags))].sort((a, b) => a.localeCompare(b, "es"));
  if (ui.tag && !tags.includes(ui.tag)) ui.tag = null;
  const filtersHTML = tags.length
    ? `<button class="chip${ui.tag ? "" : " active"}" data-tag="">Todos</button>` +
      tags.map((t) => `<button class="chip${ui.tag === t ? " active" : ""}" data-tag="${esc(t)}"><span class="swatch ${tapeClass(t)}"></span>${esc(t)}</button>`).join("")
    : "";
  const filters = $("#filters");
  if (filters._html !== filtersHTML) { filters.innerHTML = filtersHTML; filters._html = filtersHTML; }

  const running = all.filter((s) => s.status === "running").length;
  $("#summary").innerHTML = all.length ? `<span class="lcd">${running}/${all.length} en marcha</span>` : "";

  const q = ui.q.trim().toLowerCase();
  const list = all.filter((s) =>
    (!ui.tag || s.tags.includes(ui.tag)) &&
    (!q || [s.name, s.description, ...s.tags].join(" ").toLowerCase().includes(q)));

  grid.querySelectorAll(":scope > :not(.card)").forEach((el) => el.remove());
  if (!all.length) {
    ui.cards.forEach((el) => el.remove());
    grid.insertAdjacentHTML("beforeend", `
      <div class="empty">
        <h2>Aún no hay servicios</h2>
        <p>Añade tu primer servicio: un bot, una web, un servidor de juegos…</p>
        <button class="btn primary" data-act="new" data-perm="admin">${ICON.plus}Crear servicio</button>
      </div>`);
    return;
  }

  const visible = new Set(list.map((s) => s.id));
  for (const [id, el] of ui.cards) if (!visible.has(id)) el.remove();

  for (const s of list) {
    let el = ui.cards.get(s.id);
    if (!el) {
      el = document.createElement("article");
      el.className = "card module";
      el.tabIndex = 0;
      el.dataset.id = s.id;
      ui.cards.set(s.id, el);
    }
    const html = cardHTML(s);
    if (el._html !== html) { el.innerHTML = html; el._html = html; }
    el.dataset.status = s.status;
    grid.appendChild(el); // mantiene el orden
  }
  if (!list.length) grid.insertAdjacentHTML("beforeend", `<div class="empty"><p>Ningún servicio coincide con el filtro.</p></div>`);
}

// ───────────────────────── acciones ─────────────────────────

async function toggle(id) {
  const s = ui.current?.id === id && ui.current.status ? ui.current : ui.services.find((x) => x.id === id);
  if (!s) return;
  const turnOn = !isOn(s);
  if (!turnOn) {
    const ok = await confirmDialog("Apagar servicio",
      `¿Seguro que quieres apagar «${s.name}»? Dejará de funcionar hasta que lo vuelvas a encender.`, "Apagar");
    if (!ok) return;
  }
  try {
    await api("POST", `/api/services/${id}/${turnOn ? "start" : "stop"}`);
    toast(turnOn ? `«${s.name}» iniciado` : `Deteniendo «${s.name}»…`, "ok");
  } catch (e) {
    toast(e.message, "error");
  }
  refreshCurrent();
}

async function restart(id) {
  try {
    await api("POST", `/api/services/${id}/restart`);
    toast("Reiniciando…", "ok");
  } catch (e) { toast(e.message, "error"); }
  refreshCurrent();
}

async function removeService(s) {
  const ok = await confirmDialog("Eliminar servicio",
    `Se eliminará «${s.name}» y su historial de consola. Esta acción no se puede deshacer.`, "Eliminar");
  if (!ok) return;
  try {
    const res = await api("DELETE", `/api/services/${s.id}`);
    toast(res.notice ? `Servicio eliminado. ${res.notice}` : "Servicio eliminado", "ok");
    location.hash = "#/servicios";
  } catch (e) { toast(e.message, "error"); }
}

// Modo de una web: desarrollo (npm run dev) o producción (compilada y servida por serve.py).
function modeHTML(s) {
  const busy = s.updating ? "disabled" : "";
  if (s.mode === "prod") {
    return `<div class="mode-row"><span class="status prod">Producción</span>
      <span class="mode-btns"><button class="btn sm" data-act="mode-prod" ${busy}>${s.updating ? "Compilando…" : "Recompilar"}</button>
      <button class="btn sm" data-act="mode-dev" ${busy}>Volver a desarrollo</button></span></div>
      <small class="dim-text">Versión compilada: ligera y estable. Los cambios en el código no se ven hasta recompilar.</small>`;
  }
  return `<div class="mode-row"><span class="status">Desarrollo</span>
    <span class="mode-btns"><button class="btn sm primary" data-act="mode-prod" ${busy}>${s.updating ? "Compilando…" : "Pasar a producción"}</button></span></div>
    <small class="dim-text">Recarga al instante mientras programas, pero gasta más memoria. Para una web publicada, mejor producción.</small>`;
}

async function setMode(s, mode) {
  if (mode === "prod" && s.mode !== "prod") {
    const ok = await confirmDialog("Pasar a producción",
      `Se compilará «${s.name}» (npm run build) y se servirá la versión compilada. Tardará unos segundos y el progreso sale en la consola. Podrás volver a desarrollo cuando quieras.`,
      "Compilar y pasar");
    if (!ok) return;
  }
  try {
    await api("POST", `/api/services/${s.id}/mode`, { mode });
    toast(mode === "prod" ? "Compilando: el progreso sale en la consola" : "Vuelve a modo desarrollo", "ok");
    $('[data-tab="console"]')?.click();
    refreshDetail(s.id);
  } catch (e) { toast(e.message, "error"); }
}

async function updateService(id) {
  try {
    await api("POST", `/api/services/${id}/update`);
    toast("Actualizando desde GitHub: el progreso sale en la consola", "ok");
    $('[data-tab="console"]')?.click();
    refreshDetail(id);
  } catch (e) { toast(e.message, "error"); }
}

// «Nuevo servicio»: desde un repositorio de GitHub o en blanco.
// Galería de plantillas → formulario corto → progreso en vivo → ficha del servicio creado.
async function openTemplates() {
  const dlg = modal(`
    <form id="tpl-form" novalidate>
      <header><h2>Desde una plantilla</h2><button type="button" class="btn ghost icon" data-close aria-label="Cerrar">${ICON.close}</button></header>
      <div class="body" id="tpl-body"><div class="pane-msg">Cargando plantillas…</div></div>
      <footer>
        <button type="button" class="btn ghost" data-close>Cancelar</button>
        <button type="submit" class="btn primary" id="tpl-go" hidden>${ICON.plus}Crear servicio</button>
      </footer>
    </form>`);
  const body = $("#tpl-body", dlg), go = $("#tpl-go", dlg);
  let data, chosen;
  const slug = (t) => t.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 32);

  const gallery = () => {
    go.hidden = true;
    body.innerHTML = `<div class="tpl-grid">${data.templates.map((t) => `
      <button type="button" class="tpl${t.missing.length ? " blocked" : ""}" data-tpl="${t.id}">
        <strong>${esc(t.name)}</strong>
        <small>${esc(t.desc)}</small>
        <span class="tpl-meta">${t.port ? `<span class="lcd">:${t.port}</span>` : ""}${t.publishable ? '<span class="status svc">Publicable</span>' : ""}</span>
        ${t.missing.map((m) => `<span class="tpl-missing">Falta ${esc(m.what)}: <code>${esc(m.install)}</code></span>`).join("")}
      </button>`).join("")}</div>`;
  };

  const form = (t) => {
    chosen = t;
    go.hidden = false;
    go.disabled = false;
    body.innerHTML = `
      <button type="button" class="btn sm" data-back>${ICON.back}Plantillas</button>
      <div class="tpl-head"><strong>${esc(t.name)}</strong><small>${esc(t.desc)}</small></div>
      <div class="form-error" id="tpl-error"></div>
      <label class="field"><span>Nombre *</span><input id="tpl-name" maxlength="60" placeholder="Mi proyecto" autocomplete="off"></label>
      <div class="row2">
        <label class="field"><span>Carpeta</span><input id="tpl-dest" class="mono" spellcheck="false" autocomplete="off"></label>
        ${t.port ? `<label class="field"><span>Puerto</span><input id="tpl-port" inputmode="numeric" value="${t.port}"></label>` : ""}
      </div>
      ${t.publishable && ui.publishDomain ? `<label class="field"><span>Publicar en internet</span>
        <div class="affix"><input id="tpl-sub" class="mono" spellcheck="false" autocapitalize="off" placeholder="opcional"><span>.${esc(ui.publishDomain)}</span></div>
        <small>Déjalo vacío para que solo funcione en tu red local.</small></label>` : ""}
      ${t.fields.map((f) => `<label class="field"><span>${esc(f.label)}${f.required ? " *" : ""}</span>
        <input data-field="${esc(f.key)}" type="${f.secret ? "password" : "text"}" value="${esc(f.default || "")}" autocomplete="off" spellcheck="false">
        ${f.help ? `<small>${esc(f.help)}</small>` : ""}</label>`).join("")}
      ${t.note ? `<p class="git-note">${esc(t.note)}</p>` : ""}
      <label class="chk tpl-start"><input type="checkbox" id="tpl-start" checked><span>Arrancarlo al crearlo</span></label>`;
    const name = $("#tpl-name", dlg), dest = $("#tpl-dest", dlg);
    let touched = false;
    dest.addEventListener("input", () => { touched = true; });
    const sync = () => { if (!touched) dest.value = `${data.projects_dir}/${slug(name.value) || "mi-proyecto"}`; };
    name.addEventListener("input", sync);
    sync();
    name.focus();
  };

  body.addEventListener("click", (e) => {
    if (e.target.closest("[data-back]")) return gallery();
    const b = e.target.closest("[data-tpl]");
    if (!b) return;
    const t = data.templates.find((x) => x.id === b.dataset.tpl);
    if (t.missing.length) return toast(`Falta instalar ${t.missing[0].what}: ${t.missing[0].install}`, "error");
    form(t);
  });

  $("#tpl-form", dlg).addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!chosen) return;
    const fields = {};
    body.querySelectorAll("[data-field]").forEach((i) => { fields[i.dataset.field] = i.value; });
    go.disabled = true;
    try {
      const { job } = await api("POST", "/api/templates/create", {
        template: chosen.id, name: $("#tpl-name", dlg).value, dest: $("#tpl-dest", dlg).value,
        port: $("#tpl-port", dlg)?.value, subdomain: $("#tpl-sub", dlg)?.value || "", fields, start: $("#tpl-start", dlg).checked,
      });
      body.innerHTML = `<p class="label">Creando «${esc(chosen.name)}»</p><pre class="git-out gh-log" id="tpl-log">Empezando…</pre>`;
      go.textContent = "Creando…";
      const poll = async () => {
        if (!dlg.open) return;
        const j = await api("GET", `/api/deploy/jobs/${job}`);
        const log = $("#tpl-log", dlg);
        log.textContent = j.log.join("\n");
        log.scrollTop = log.scrollHeight;
        if (j.status === "running") return setTimeout(poll, 1000);
        if (j.status === "error") { go.textContent = "Error"; return toast(`No se pudo crear: ${j.error}`, "error"); }
        dlg.close();
        toast("Servicio creado desde la plantilla", "ok");
        location.hash = `#/s/${j.result.sid}`;
      };
      poll();
    } catch (err) {
      $("#tpl-error", dlg).textContent = err.message;
      go.disabled = false;
    }
  });

  try {
    data = await api("GET", "/api/templates");
    gallery();
  } catch (err) {
    body.innerHTML = `<div class="pane-msg bad-text">${esc(err.message)}</div>`;
  }
}

async function openGithub() {
  const dlg = modal(`
    <form id="gh-form" novalidate>
      <header><h2>Desplegar desde GitHub</h2><button type="button" class="btn ghost icon" data-close aria-label="Cerrar">${ICON.close}</button></header>
      <div class="body" id="gh-body">
        <div class="form-error" id="gh-error"></div>
        <label class="search gh-search">${ICON.search}<input id="gh-q" type="search" placeholder="Buscar en tus repositorios…" aria-label="Buscar repositorio"></label>
        <div class="gh-list" id="gh-list"><div class="pane-msg">Cargando tus repositorios…</div></div>
        <label class="field"><span>Repositorio</span><input id="gh-repo" class="mono" placeholder="usuario/repositorio o https://github.com/…" autocomplete="off" spellcheck="false"></label>
        <label class="field"><span>Carpeta de destino</span><input id="gh-dest" class="mono" placeholder="se crea dentro de ~/projectes" autocomplete="off" spellcheck="false">
          <small>Se clona aquí y se instalan sus dependencias (npm). La carpeta no debe existir.</small></label>
      </div>
      <footer>
        <button type="button" class="btn ghost" data-close>Cancelar</button>
        <button type="submit" class="btn primary" id="gh-go">${ICON.download}Clonar e instalar</button>
      </footer>
    </form>`);
  let repos = [], projectsDir = "~/projectes", info = {};
  const list = $("#gh-list", dlg), repoIn = $("#gh-repo", dlg), destIn = $("#gh-dest", dlg);
  const draw = () => {
    const q = $("#gh-q", dlg).value.trim().toLowerCase();
    const shown = repos.filter((r) => !q || `${r.nameWithOwner} ${r.description || ""}`.toLowerCase().includes(q));
    list.innerHTML = shown.length ? shown.map((r) => `
      <button type="button" class="gh-repo${repoIn.value === r.nameWithOwner ? " selected" : ""}" data-repo="${esc(r.nameWithOwner)}" ${r.cloned ? 'title="Ya hay una carpeta con este nombre en ~/projectes"' : ""}>
        <span class="gh-name">${esc(r.name)}</span>
        <span class="status ${r.isPrivate ? "" : "svc"}">${r.isPrivate ? "Privado" : "Público"}</span>
        ${r.cloned ? '<span class="dim-text">ya clonado</span>' : ""}
        <span class="gh-date">${fmtAgo(Date.parse(r.updatedAt) / 1000)}</span>
        ${r.description ? `<span class="gh-desc">${esc(r.description)}</span>` : ""}
      </button>`).join("") : '<div class="pane-msg">Ningún repositorio coincide.</div>';
  };
  const pick = (name) => {
    const r = repos.find((x) => x.nameWithOwner === name);
    repoIn.value = name;
    info = r || {};
    destIn.value = `${projectsDir}/${name.split("/").pop()}`;
    draw();
  };
  $("#gh-q", dlg).addEventListener("input", draw);
  list.addEventListener("click", (e) => { const b = e.target.closest("[data-repo]"); if (b) pick(b.dataset.repo); });
  repoIn.addEventListener("change", () => {
    const name = repoIn.value.trim().replace(/\.git$/, "").split(/[/:]/).pop();
    if (name && !destIn.value) destIn.value = `${projectsDir}/${name}`;
  });
  try {
    const d = await api("GET", "/api/github/repos");
    repos = d.repos; projectsDir = d.projects_dir;
    draw();
  } catch (err) {
    list.innerHTML = `<div class="pane-msg bad-text">${esc(err.message)}</div>`;
  }

  $("#gh-form", dlg).addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = $("#gh-go", dlg);
    btn.disabled = true;
    try {
      const { job } = await api("POST", "/api/deploy/clone", { repo: repoIn.value, dest: destIn.value });
      $("#gh-body", dlg).innerHTML = `<p class="label">Progreso</p><pre class="git-out gh-log" id="gh-log">Empezando…</pre>`;
      btn.textContent = "Clonando…";
      const poll = async () => {
        if (!dlg.open) return;
        const j = await api("GET", `/api/deploy/jobs/${job}`);
        const log = $("#gh-log", dlg);
        log.textContent = j.log.join("\n");
        log.scrollTop = log.scrollHeight;
        if (j.status === "running") return setTimeout(poll, 1000);
        if (j.status === "error") {
          btn.textContent = "Error";
          toast(`No se pudo clonar: ${j.error}`, "error");
          return;
        }
        const r = j.result;
        dlg.close();
        toast(`Clonado: proyecto ${r.kind}. Revisa los datos y crea el servicio.`, "ok");
        const pretty = r.name.replace(/[-_]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
        ui.formPrefill = {
          kind: "process", name: pretty, description: info.description || "", tags: r.tags, command: r.command,
          cwd: r.path, port: r.port, env: r.env || {}, autostart: true, restart_on_crash: true,
        };
        location.hash = "#/nuevo/programa";
      };
      poll();
    } catch (err) {
      $("#gh-error", dlg).textContent = err.message;
      btn.disabled = false;
    }
  });
}

// ───────────────────────── vista: ajustes ─────────────────────────
// Página propia (#/ajustes/<categoría>): lista de categorías a la izquierda y la elegida a la derecha.
// Cada categoría se guarda por separado.

const SETTINGS = [
  ["cuenta", "Mi cuenta", "Tu contraseña", ICON.user, null],
  ["actualizaciones", "Actualizaciones", "NovaHub, sistema y servicios", ICON.download, "admin"],
  ["fuera", "Copias fuera de casa", "Cifradas, en un USB u otro servidor", ICON.archive, "admin"],
  ["usuarios", "Usuarios", "Quién entra y qué puede hacer", ICON.users, "admin"],
  ["servidores", "Servidores", "Otros servidores en este panel", ICON.server, "admin"],
  ["remoto", "Acceso remoto", "Llaves para otros paneles", ICON.key, "admin"],
  ["avisos", "Avisos por correo", "Gmail y qué avisar", ICON.mail, "admin"],
  ["vigilante", "Vigilante externo", "Si el servidor cae del todo", ICON.activity, "admin"],
  ["sesion", "Sesión", "Contraseña e inactividad", ICON.lock, "admin"],
  ["git", "Git", "Autor de los commits", ICON.git, "admin"],
  ["app", "App para el móvil", "Instalar NovaHub", ICON.phone, null],
];

function viewSettings(cat) {
  const cats = SETTINGS.filter((c) => !c[4] || can(c[4]));
  if (!cats.some(([k]) => k === cat)) cat = can("admin") ? "avisos" : "cuenta";
  $("#main").innerHTML = `
    <section class="page-head"><div><h1 class="page-title">Ajustes</h1><p class="page-sub">Cada apartado se guarda por separado</p></div></section>
    <div class="settings">
      <nav class="set-nav" aria-label="Categorías de ajustes">
        ${cats.map(([k, label, sub, icon]) => `<a href="#/ajustes/${k}" class="${k === cat ? "active" : ""}" ${k === cat ? 'aria-current="page"' : ""}>
          ${icon}<span><b>${label}</b><small>${sub}</small></span></a>`).join("")}
      </nav>
      <section class="module set-body" id="set-body"><div class="pane-msg">Cargando…</div></section>
    </div>`;
  $(".set-nav a.active").scrollIntoView({ block: "nearest", inline: "center" });  // en el móvil la lista se desliza
  ({ cuenta: setAccount, actualizaciones: setUpdates, fuera: setOffsite, usuarios: setUsers, servidores: setServers, remoto: setTokens, avisos: setNotify, vigilante: setHeartbeat, sesion: setSession, git: setGit, app: setApp })[cat]($("#set-body"));
}

// Pie con «Guardar» y el error, común a todas las categorías
const setFoot = (extra = "") => `<div class="form-error" id="set-error"></div>
  <footer class="set-foot">${extra}<span class="grow"></span><button type="submit" class="btn primary" id="set-save">Guardar</button></footer>`;

// Devuelve una función que guarda (y lanza el error si falla), para quien necesite guardar antes de otra cosa
function setForm(body, html, save, extra) {
  body.innerHTML = `<form id="set-form" novalidate>${html}${setFoot(extra)}</form>`;
  const form = $("#set-form", body);
  const submit = async () => {
    $("#set-error", body).textContent = "";
    const btn = $("#set-save", body);
    btn.disabled = true;
    try { await save(form); } finally { btn.disabled = false; }
  };
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try { await submit(); toast("Guardado", "ok"); } catch (err) { $("#set-error", body).textContent = err.message; }
  });
  return submit;
}

async function setNotify(body) {
  const n = await api("GET", "/api/notify");
  const status = n.last_error ? `<p class="git-note bad">Último error: ${esc(n.last_error)}</p>`
    : n.last_sent ? `<p class="nt-ok">Último correo enviado ${fmtAgo(n.last_sent)}.</p>`
    : n.configured ? '<p class="nt-ok">Configurado. Pulsa «Enviar correo de prueba» para comprobarlo.</p>' : "";
  const submit = setForm(body, `
    <h2 class="set-title">Avisos por correo</h2>
    <p class="set-sub">NovaHub te escribe cuando algo va mal. Como mucho un correo por servicio y tipo de aviso cada 10 minutos.</p>
    ${status}
    <h3 class="set-h">Cuenta de Gmail</h3>
    <div class="set-grid">
      <label class="field"><span>Tu Gmail</span><input name="user" type="email" autocomplete="off" placeholder="tu.cuenta@gmail.com" value="${esc(n.user)}"></label>
      <label class="field"><span>Enviar a</span><input name="to" autocomplete="off" placeholder="${esc(n.user || "el mismo Gmail")}" value="${esc(n.to)}">
        <small>Opcional. Varias direcciones separadas por comas.</small></label>
    </div>
    <label class="field"><span>Contraseña de aplicación</span>
      <input name="app_password" type="password" autocomplete="new-password" spellcheck="false" placeholder="${n.configured ? "guardada · déjala vacía para mantenerla" : "16 letras"}">
      <small>No es tu contraseña de Google: créala en <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener">myaccount.google.com/apppasswords</a>
        (hace falta la verificación en dos pasos). Se guarda en el servidor y no se vuelve a mostrar.</small></label>
    <h3 class="set-h">Avisarme cuando…</h3>
    <div class="checks">${n.events.map((e) => `
      <label><input type="checkbox" data-event="${esc(e.key)}" ${e.on ? "checked" : ""}><span><strong>${esc(e.label)}</strong></span></label>`).join("")}
    </div>`, async (f) => {
    const events = {};
    f.querySelectorAll("[data-event]").forEach((c) => { events[c.dataset.event] = c.checked; });
    await api("PUT", "/api/notify", { user: f.user.value.trim(), to: f.to.value.trim(), app_password: f.app_password.value, events });
  }, '<button type="button" class="btn" id="set-test">Enviar correo de prueba</button>');
  $("#set-test", body).addEventListener("click", async (e) => {
    e.target.disabled = true;
    try {
      await submit();  // primero se guarda lo escrito
      await api("POST", "/api/notify/test");
      toast("Correo de prueba enviado: mira tu bandeja de entrada", "ok");
      setNotify(body);
    } catch (err) { const el = $("#set-error", body); if (el) el.textContent = err.message; }
    e.target.disabled = false;
  });
}

async function setHeartbeat(body) {
  const n = await api("GET", "/api/notify");
  setForm(body, `
    <h2 class="set-title">Vigilante externo</h2>
    <p class="set-sub">NovaHub manda una señal de vida cada minuto mientras todo funciona. Si deja de llegar (corte de luz, sin internet,
      servidor colgado), <a href="https://healthchecks.io" target="_blank" rel="noopener">healthchecks.io</a> te avisa: es lo único que avisa
      cuando el propio servidor no puede hacerlo.</p>
    ${n.heartbeat_error ? `<p class="git-note bad">Señal de vida: ${esc(n.heartbeat_error)}</p>`
      : n.heartbeat_last ? `<p class="nt-ok">Última señal de vida ${fmtAgo(n.heartbeat_last)}.</p>` : ""}
    <label class="field"><span>Dirección de ping</span>
      <input name="hb" class="mono" spellcheck="false" autocomplete="off" placeholder="https://hc-ping.com/…" value="${esc(n.heartbeat_url)}">
      <small>Configura allí el check con periodo de 1 minuto y 3 de gracia. Vacío = desactivado.</small></label>`, async (f) => {
    await api("PUT", "/api/notify", { heartbeat_url: f.hb.value.trim() });
    setTimeout(() => setHeartbeat(body), 1500);  // el primer ping sale enseguida
  });
}

async function setSession(body) {
  const s = await api("GET", "/api/session-settings");
  setForm(body, `
    <h2 class="set-title">Sesión</h2>
    <p class="set-sub">Cuándo vuelve a pedir la contraseña. Antes del panel está además tu cuenta de Google (Cloudflare Access).</p>
    <div class="checks one"><label><input type="checkbox" name="reload" ${s.lock_on_reload ? "checked" : ""}>
      <span><strong>Pedir la contraseña al recargar la página</strong><small>También al abrir el panel en una pestaña nueva o abrir la app del móvil.</small></span></label></div>
    <div class="set-grid">
      <label class="field"><span>Cerrar tras… sin usarlo (minutos)</span><input name="idle" inputmode="numeric" value="${s.idle_minutes}">
        <small>Sin clics ni teclas en el panel. Las actualizaciones automáticas de la pantalla no cuentan.</small></label>
      <label class="field"><span>Duración máxima (horas)</span><input name="max" inputmode="numeric" value="${s.max_hours}">
        <small>Aunque lo estés usando, pasado este tiempo vuelve a pedirla.</small></label>
    </div>`, async (f) => {
    await api("PUT", "/api/session-settings", { lock_on_reload: f.reload.checked, idle_minutes: f.idle.value.trim(), max_hours: f.max.value.trim() });
  });
}

async function setGit(body) {
  const g = await api("GET", "/api/git-identity");
  setForm(body, `
    <h2 class="set-title">Git</h2>
    <p class="set-sub">Con este nombre y correo se firman los commits que hagas desde el panel (pestaña Git de cada servicio).
      Es la configuración global de git del servidor.</p>
    <div class="set-grid git-id">
      <label class="field"><span>Nombre</span><input name="name" autocomplete="off" spellcheck="false" placeholder="tu usuario de GitHub" value="${esc(g.name)}"></label>
      <label class="field"><span>Correo</span><input name="email" type="email" autocomplete="off" spellcheck="false" placeholder="el de tu cuenta de GitHub" value="${esc(g.email)}">
        <small>Usa el de tu cuenta de GitHub para que los commits aparezcan como tuyos.</small></label>
    </div>`, async (f) => {
    await api("PUT", "/api/git-identity", { name: f.name.value.trim(), email: f.email.value.trim() });
  });
}

async function setOffsite(body) {
  let shown = null;  // contraseña generada que se enseña una sola vez
  const draw = (o) => {
    const busy = !!o.job, c = o.config;
    const st = (r) => !r ? '<span class="dim-text">todavía no</span>'
      : `<span class="${r.ok ? "ok-text" : r.ok === false ? "bad-text" : "dim-text"}">${r.ok ? "✓" : r.ok === false ? "✗" : "·"}</span> ${esc(r.msg)} <span class="dim-text">· ${fmtAgo(r.at)}</span>`;
    const dest = (d) => `
      <section class="upd-card" data-dest="${esc(d.id)}">
        <header><h3>${d.type === "local" ? ICON.archive : ICON.server}${esc(d.name)}</h3>
          <span class="${d.available ? "ok-text" : "dim-text"}">${d.available ? "disponible" : esc(d.why)}</span></header>
        <p class="dim-text mono off-repo">${esc(d.repo)}</p>
        ${d.same_disk ? '<p class="git-note">Está en el mismo disco que el servidor o que las copias locales: si ese disco falla, también se pierde. Usa un disco aparte.</p>' : ""}
        <dl class="readout"><div><dt>Última copia</dt><dd>${st(d.last_backup)}</dd></div><div><dt>Última comprobación</dt><dd>${st(d.last_check)}</dd></div></dl>
        <div class="upd-actions">
          <button type="button" class="btn sm primary" data-off="run" ${busy || !o.restic ? "disabled" : ""}>Copiar ahora</button>
          <button type="button" class="btn sm" data-off="check" ${busy || !o.restic ? "disabled" : ""}>Comprobar</button>
          <button type="button" class="btn sm" data-off="list" ${!o.restic ? "disabled" : ""}>Ver copias</button>
          <span class="grow"></span>
          <button type="button" class="btn sm icon ghost" data-off="del" title="Quitar destino" aria-label="Quitar destino">${ICON.trash}</button>
        </div>
        <div class="off-snaps" hidden></div>
      </section>`;
    body.innerHTML = `
      <h2 class="set-title">Copias fuera de casa</h2>
      <p class="set-sub">Las copias de tus servicios y la configuración de NovaHub, <b>cifradas</b>, en un disco USB o en otro servidor tuyo
        (por SSH, p. ej. por Tailscale). Sin servicios de terceros ni suscripciones. Si el servidor se estropea o se pierde, desde ahí
        se recupera todo.</p>
      ${o.restic ? "" : `<div class="git-note"><b>Falta restic</b> (libre, se instala con apt): <pre class="upd-cmd">sudo apt install restic</pre></div>`}
      ${shown ? `<div class="nt-ok tok-show"><b>Contraseña de cifrado de «${esc(shown.name)}». Guárdala ahora fuera del servidor (gestor de contraseñas o papel):
        sin ella no se pueden recuperar las copias si este servidor muere.</b><code id="off-pass">${esc(shown.password)}</code>
        <button type="button" class="btn sm" data-off="copy">Copiar</button></div>` : ""}
      ${busy ? `<p class="nt-ok upd-busy">En curso: ${esc(o.job)}…</p>` : ""}
      ${o.destinations.map(dest).join("") || '<p class="dim-text">Aún no hay destinos.</p>'}
      <details class="adv" ${o.destinations.length ? "" : "open"}><summary>Añadir destino</summary><div class="inner">
        <form id="off-form" novalidate class="off-form">
          <div class="field"><span>Tipo</span><div class="kind-pick">
            <label><input type="radio" name="type" value="local" checked><span><strong>Disco USB o externo</strong><small>Una carpeta en un disco conectado al servidor</small></span></label>
            <label><input type="radio" name="type" value="sftp"><span><strong>Otro servidor</strong><small>Por SSH: el de un familiar, una Raspberry…</small></span></label>
          </div></div>
          <label class="field"><span>Nombre</span><input name="name" placeholder="Disco USB"></label>
          <label class="field" data-off-kind="local"><span>Carpeta en el disco</span><input name="path" class="mono" spellcheck="false" placeholder="/media/usb/novahub-copias">
            <small>Si el disco no está conectado a la hora de la copia, se espera a la siguiente sin dar error.</small></label>
          <div data-off-kind="sftp" class="kind-block" hidden>
            <div class="set-grid"><label class="field"><span>Usuario</span><input name="user" class="mono" placeholder="copias"></label>
              <label class="field"><span>Servidor</span><input name="host" class="mono" placeholder="100.64.0.5 (IP de Tailscale)"></label></div>
            <div class="set-grid"><label class="field"><span>Carpeta allí</span><input name="rpath" class="mono" placeholder="/srv/copias/novahub"></label>
              <label class="field"><span>Puerto SSH</span><input name="port" inputmode="numeric" placeholder="22"></label></div>
            <div class="git-note off-key">En el otro servidor, añade esta llave de NovaHub a <code>~/.ssh/authorized_keys</code> del usuario (mejor uno solo para copias):
              ${o.pubkey ? `<code id="off-key">${esc(o.pubkey)}</code><button type="button" class="btn sm" data-off="copykey">Copiar llave</button>`
                : '<button type="button" class="btn sm" data-off="mkkey">Crear la llave de NovaHub</button>'}</div>
          </div>
          <label class="field"><span>Contraseña de cifrado</span><input name="password" type="password" autocomplete="new-password" placeholder="vacía = se genera una segura">
            <small>Si el destino ya tiene copias de NovaHub (p. ej. tras reinstalar), pon su contraseña y se usan.</small></label>
          <div class="form-error" id="off-error"></div>
          <button type="submit" class="btn primary" ${!o.restic || busy ? "disabled" : ""}>Añadir destino</button>
        </form></div></details>
      <h3 class="set-h">Cuándo y cuántas</h3>
      <div class="off-cfg">
        <label class="chk-line"><input type="checkbox" id="off-enabled" ${c.enabled ? "checked" : ""}> Copia cada día a las <input id="off-hour" class="upd-hour" inputmode="numeric" value="${c.hour}">:00</label>
        <span>Conservar <input id="off-d" class="upd-hour" value="${c.keep_daily}"> diarias, <input id="off-w" class="upd-hour" value="${c.keep_weekly}"> semanales
          y <input id="off-m" class="upd-hour" value="${c.keep_monthly}"> mensuales</span>
      </div>
      <p class="dim-text upd-help">Se copian ${o.sources.map((x) => `<code>${esc(x)}</code>`).join(" y ")}. Cada ${c.verify_days} días se comprueba el destino y se restaura
        de verdad un archivo para confirmar que la copia sirve. «Recuperar» saca una copia completa a <code>${esc(o.restore_dir)}</code> sin tocar nada de lo actual.</p>
      ${o.log ? `<details class="adv" ${busy ? "open" : ""}><summary>Registro</summary><pre class="upd-log" id="off-log">${esc(o.log)}</pre></details>` : ""}`;
    const f = $("#off-form", body);
    const sync = () => f.querySelectorAll("[data-off-kind]").forEach((el) => { el.hidden = el.dataset.offKind !== f.type.value; });
    f.addEventListener("change", (e) => { if (e.target.name === "type") sync(); });
    sync();
    f.addEventListener("submit", async (e) => {
      e.preventDefault();
      const v = Object.fromEntries(new FormData(f));
      try {
        const r = await api("POST", "/api/offsite/destinations", v);
        shown = r.password ? { name: v.name, password: r.password } : null;
        draw(r); toast("Destino añadido", "ok");
      } catch (err) { $("#off-error", body).textContent = err.message; }
    });
    const log = $("#off-log", body); if (log) log.scrollTop = log.scrollHeight;
    ui.offBusy = busy;
  };
  const load = async () => { try { draw(await api("GET", "/api/offsite")); } catch (e) { body.innerHTML = `<div class="pane-msg bad-text">${esc(e.message)}</div>`; } };
  body.onchange = async (e) => {
    if (!["off-enabled", "off-hour", "off-d", "off-w", "off-m"].includes(e.target.id)) return;
    try {
      draw(await api("PUT", "/api/offsite", { enabled: $("#off-enabled", body).checked, hour: $("#off-hour", body).value,
        keep_daily: $("#off-d", body).value, keep_weekly: $("#off-w", body).value, keep_monthly: $("#off-m", body).value }));
      toast("Guardado", "ok");
    } catch (err) { toast(err.message, "error"); }
  };
  body.onclick = async (e) => {
    const b = e.target.closest("[data-off]");
    if (!b) return;
    const act = b.dataset.off, card = b.closest("[data-dest]"), id = card?.dataset.dest;
    const copy = (sel, what) => navigator.clipboard?.writeText($(sel, body).textContent).then(() => toast(`${what} copiada`, "ok"), () => {});
    try {
      if (act === "copy") copy("#off-pass", "Contraseña");
      else if (act === "copykey") copy("#off-key", "Llave");
      else if (act === "mkkey") { await api("POST", "/api/offsite/key"); await load(); }
      else if (act === "run") draw(await api("POST", `/api/offsite/destinations/${id}/run`, {}));
      else if (act === "check") draw(await api("POST", `/api/offsite/destinations/${id}/check`, {}));
      else if (act === "del") {
        if (!(await confirmDialog("Quitar destino", "NovaHub dejará de copiar ahí. Las copias que ya hay en el destino no se borran.", "Quitar"))) return;
        shown = null; draw(await api("DELETE", `/api/offsite/destinations/${id}`));
      } else if (act === "list") {
        const box = $(".off-snaps", card);
        box.hidden = !box.hidden;
        if (box.hidden) return;
        box.innerHTML = '<p class="dim-text">Leyendo las copias…</p>';
        const { snapshots } = await api("GET", `/api/offsite/destinations/${id}/snapshots`);
        box.innerHTML = snapshots.length ? `<ul class="upd-rows">${snapshots.map((s) => `<li><span><b>${esc(new Date(s.time).toLocaleString("es-ES"))}</b>
          <small class="mono">${esc(s.id)}${s.size ? ` · ${fmtBytes(s.size)}` : ""}${s.files ? ` · ${s.files} archivos` : ""}</small></span>
          <button type="button" class="btn sm" data-off="restore" data-snap="${esc(s.id)}">Recuperar</button></li>`).join("")}</ul>` : '<p class="dim-text">Aún no hay copias.</p>';
      } else if (act === "restore") {
        if (!(await confirmDialog("Recuperar copia", "Se sacará esta copia completa a una carpeta aparte, sin tocar nada de lo actual. Desde ahí puedes recuperar lo que necesites.", "Recuperar"))) return;
        const r = await api("POST", `/api/offsite/destinations/${id}/restore`, { snapshot: b.dataset.snap });
        draw(r); toast(`Recuperando en ${r.target}`, "ok");
      }
    } catch (err) { toast(err.message, "error"); }
  };
  await load();
  every(3000, () => { if (ui.offBusy && $("#set-body") === body) load(); });
}

async function setUpdates(body) {
  const draw = (u) => {
    const nh = u.novahub || {}, apt = u.apt || {}, pk = apt.packages || [];
    const sec = pk.filter((p) => p.security), busy = !!u.job;
    const svcName = (id) => ui.services.find((s) => s.id === id)?.name || id;
    const pkgRow = (p) => `<li><b class="mono">${esc(p.name)}</b> <span class="dim-text mono">${esc(p.from)} → ${esc(p.to)}</span>${p.security ? ' <span class="status bad">seguridad</span>' : ""}</li>`;
    const card = (title, sub, inner, cls = "") => `<section class="upd-card ${cls}"><header><h3>${title}</h3>${sub ? `<span>${sub}</span>` : ""}</header>${inner}</section>`;
    const novahub = nh.error ? `<p class="git-note">${esc(nh.error)}</p>`
      : nh.available ? `<p class="nt-ok"><b>Versión nueva: ${esc(nh.channel === "dev" ? `${nh.behind} commit(s) nuevos (${nh.latest})` : nh.name || nh.latest)}</b></p>
          ${nh.notes ? `<details class="adv"><summary>Novedades</summary><pre class="upd-notes">${esc(nh.notes)}</pre></details>` : ""}
          ${nh.dirty ? '<p class="git-note">Hay cambios sin guardar en los archivos de NovaHub: no se puede actualizar hasta resolverlos.</p>' : ""}
          ${!nh.systemd ? '<p class="git-note">NovaHub no funciona como servicio de systemd: actualízalo a mano.</p>' : ""}
          <button type="button" class="btn primary" data-up="novahub" ${busy || nh.dirty || !nh.systemd ? "disabled" : ""}>${ICON.download}Actualizar NovaHub</button>
          <small class="dim-text upd-help">Guarda una copia de los datos, instala la versión, reinicia el panel (unos segundos) y comprueba que responde. Si no, vuelve sola a la versión anterior. Los servicios no se paran.</small>`
      : `<p class="dim-text">Tienes la última ${nh.channel === "dev" ? "versión de desarrollo" : "versión"}.</p>`;
    const system = apt.error ? `<p class="git-note">${esc(apt.error)}</p>` : `
      <p>${pk.length ? `<b>${pk.length}</b> paquete${pk.length === 1 ? "" : "s"} por actualizar${sec.length ? ` · <b class="bad-text">${sec.length} de seguridad</b>` : ""}` : "El sistema está al día."}</p>
      ${pk.length ? `<details class="adv"><summary>Ver paquetes</summary><ul class="upd-list">${[...sec, ...pk.filter((p) => !p.security)].map(pkgRow).join("")}</ul></details>` : ""}
      ${u.sudo ? `<div class="upd-actions">
          <button type="button" class="btn" data-up="security" ${busy || !sec.length ? "disabled" : ""}>Solo seguridad</button>
          <button type="button" class="btn primary" data-up="upgrade" ${busy || !pk.length ? "disabled" : ""}>Actualizar todo</button></div>
          <label class="chk-line upd-auto"><input type="checkbox" id="up-auto" ${u.config.auto_security ? "checked" : ""}> Instalar solas las de seguridad cada noche a las
            <input id="up-hour" class="upd-hour" inputmode="numeric" value="${u.config.auto_hour}">:00</label>`
        : `<div class="git-note"><b>Falta un permiso de una sola vez.</b> NovaHub no es root; para actualizar el sistema usa un script con
          órdenes fijas que solo puede ejecutar como root. Ejecuta en el servidor (desde la carpeta de NovaHub):
          <pre class="upd-cmd">sudo install -o root -g root -m 755 tools/novahub-sistema /usr/local/sbin/novahub-sistema
echo "$USER ALL=(root) NOPASSWD: /usr/local/sbin/novahub-sistema" | sudo tee /etc/sudoers.d/novahub-sistema
sudo chmod 440 /etc/sudoers.d/novahub-sistema</pre></div>`}`;
    const reboot = u.reboot ? card("Reinicio pendiente", fmtAgo(u.reboot.since), `
      <p>Se ha actualizado el núcleo u otra pieza básica${u.reboot.packages.length ? ` (${u.reboot.packages.slice(0, 4).map(esc).join(", ")})` : ""}: no se usa hasta reiniciar el servidor.</p>
      <button type="button" class="btn" data-up="reboot" ${busy || !u.sudo ? "disabled" : ""}>${ICON.restart}Reiniciar el servidor</button>
      <small class="dim-text upd-help">Para los servicios en orden y reinicia. Al volver, se encienden solos los que tienen autoarranque.</small>`, "warn") : "";
    const svcs = Object.entries(u.services || {}).filter(([, s]) => s.available);
    const deps = Object.entries(u.deps || {}).filter(([, d]) => d.count);
    const services = (svcs.length || deps.length) ? `<ul class="upd-rows">
        ${svcs.map(([id, s]) => `<li><span><b>${esc(svcName(id))}</b><small>${esc(s.msg)}</small></span>
          <button type="button" class="btn sm" data-up="service" data-id="${esc(id)}" data-what="${esc(s.kind)}" ${busy ? "disabled" : ""}>Actualizar</button></li>`).join("")}
        ${deps.map(([id, d]) => `<li><span><b>${esc(svcName(id))}</b><small>${d.count} dependencia${d.count === 1 ? "" : "s"} con versión nueva
            (${d.safe} sin cambios grandes)</small>
            <details class="adv"><summary>Ver</summary><ul class="upd-list">${d.items.map((i) => `<li><b class="mono">${esc(i.name)}</b>
              <span class="dim-text mono">${esc(i.current)} → ${esc(i.safe ? i.wanted : i.latest)}</span> <span class="dim-text">${esc(i.tool)}${i.safe ? "" : " · versión mayor, a mano"}</span></li>`).join("")}</ul></details></span>
          <button type="button" class="btn sm" data-up="service" data-id="${esc(id)}" data-what="deps" ${busy || !d.safe ? "disabled" : ""}>Actualizar</button></li>`).join("")}
      </ul><small class="dim-text upd-help">Antes de actualizar las dependencias de un proyecto se hace una copia de seguridad del servicio. Solo se instalan las versiones compatibles (npm update, pip sin saltos de versión mayor); los cambios grandes, a mano.</small>`
      : '<p class="dim-text">Los servicios están al día (imágenes de contenedores, repositorios de git y dependencias).</p>';
    body.innerHTML = `
      <div class="upd-top">
        <div><h2 class="set-title">Actualizaciones</h2>
          <p class="set-sub">NovaHub <b>${esc(u.version)}</b>${u.commit ? ` <span class="dim-text mono">· ${esc(u.commit)}</span>` : ""} ·
            ${u.checking ? "comprobando…" : u.last_check ? `comprobado ${fmtAgo(u.last_check)}` : "sin comprobar todavía"}</p></div>
        <button type="button" class="btn" data-up="check" ${u.checking ? "disabled" : ""}>${ICON.restart}Comprobar ahora</button>
      </div>
      ${busy ? `<p class="nt-ok upd-busy">Actualizando: ${esc(u.job)}…</p>` : ""}
      ${reboot}
      ${card("NovaHub", `<label class="upd-channel">Canal <select id="up-channel"><option value="stable" ${u.config.channel === "stable" ? "selected" : ""}>Estable (versiones)</option>
        <option value="dev" ${u.config.channel === "dev" ? "selected" : ""}>Desarrollo (cada cambio)</option></select></label>`, novahub)}
      ${card("Sistema", "apt · Python, Node, núcleo, librerías…", system)}
      ${card("Servicios", "contenedores, git y dependencias", services)}
      ${u.log ? `<details class="adv" ${busy ? "open" : ""}><summary>Registro</summary><pre class="upd-log" id="upd-log">${esc(u.log)}</pre></details>` : ""}
      ${u.history.length ? `<h3 class="set-h">Historial</h3><ul class="upd-hist">${u.history.map((h) => `<li><span class="${h.ok ? "ok-text" : "bad-text"}">${h.ok ? "✓" : "✗"}</span>
        <b>${esc(h.what)}</b> ${esc(h.msg)} <span class="dim-text">· ${fmtAgo(h.at)}</span></li>`).join("")}</ul>` : ""}
      <label class="chk-line upd-auto"><input type="checkbox" id="up-notify" ${u.config.notify ? "checked" : ""}> Avisarme por correo cuando haya actualizaciones</label>`;
    const log = $("#upd-log", body); if (log) log.scrollTop = log.scrollHeight;
    ui.updBusy = busy || u.checking;
  };
  const load = async () => { try { draw(await api("GET", "/api/updates")); } catch (e) { body.innerHTML = `<div class="pane-msg bad-text">${esc(e.message)}</div>`; } };
  const saveCfg = async () => {
    try { draw(await api("PUT", "/api/updates", { channel: $("#up-channel", body).value, auto_security: !!$("#up-auto", body)?.checked,
      auto_hour: $("#up-hour", body)?.value ?? 4, notify: $("#up-notify", body).checked })); toast("Guardado", "ok"); }
    catch (e) { toast(e.message, "error"); }
  };
  body.onchange = (e) => { if (["up-channel", "up-auto", "up-hour", "up-notify"].includes(e.target.id)) saveCfg(); };
  body.onclick = async (e) => {
    const b = e.target.closest("[data-up]");
    if (!b) return;
    const act = b.dataset.up;
    try {
      if (act === "check") draw(await api("POST", "/api/updates/check"));
      else if (act === "novahub") {
        if (!(await confirmDialog("Actualizar NovaHub", "El panel se reiniciará unos segundos (tus servicios siguen funcionando). Si la versión nueva no arranca, se vuelve sola a la anterior.", "Actualizar"))) return;
        draw(await api("POST", "/api/updates/novahub"));
        toast("Actualizando NovaHub: el panel volverá en unos segundos", "ok");
      } else if (act === "security" || act === "upgrade") {
        if (!(await confirmDialog("Actualizar el sistema", act === "security" ? "Se instalarán solo las actualizaciones de seguridad." : "Se instalarán todas las actualizaciones pendientes del sistema. Puede tardar unos minutos.", "Actualizar"))) return;
        draw(await api("POST", "/api/updates/system", { mode: act }));
      } else if (act === "reboot") {
        if (!(await confirmDialog("Reiniciar el servidor", "Se pararán los servicios en orden y el servidor se reiniciará. El panel volverá en uno o dos minutos.", "Reiniciar"))) return;
        await api("POST", "/api/updates/reboot");
        toast("Reiniciando el servidor…", "ok");
      } else if (act === "service") {
        draw(await api("POST", "/api/updates/service", { id: b.dataset.id, what: b.dataset.what }));
      }
    } catch (err) { toast(err.message, "error"); }
  };
  await load();
  every(4000, () => { if (ui.updBusy && $("#set-body") === body) load(); });
}

async function setAccount(body) {
  const u = ui.me;
  setForm(body, `
    <h2 class="set-title">Mi cuenta</h2>
    <p class="set-sub">Has entrado como <b>${esc(u.username)}</b> · ${esc(u.role_label)}${u.role !== "admin"
      ? ` · ${u.services === "*" ? "todos los servicios" : `${u.services.length} servicio${u.services.length === 1 ? "" : "s"}`}` : ""}.</p>
    <h3 class="set-h">Cambiar la contraseña</h3>
    <label class="field"><span>Contraseña actual</span><input name="current" type="password" autocomplete="current-password"></label>
    <div class="set-grid">
      <label class="field"><span>Nueva contraseña</span><input name="password" type="password" autocomplete="new-password"><small>Al menos 8 caracteres.</small></label>
      <label class="field"><span>Repítela</span><input name="again" type="password" autocomplete="new-password"></label>
    </div>
    <p class="dim-text task-help">Al cambiarla se cierran tus sesiones en otros dispositivos; en este sigues dentro.</p>`, async (f) => {
    if (f.password.value !== f.again.value) throw new Error("Las dos contraseñas nuevas no coinciden");
    await api("PUT", "/api/account", { current: f.current.value, password: f.password.value });
    f.reset();
  });
}

async function setUsers(body) {
  const [{ users, roles }, svcs] = await Promise.all([api("GET", "/api/users"), api("GET", "/api/services")]);
  const services = svcs.services;
  const svcName = (id) => services.find((s) => s.id === id)?.name || id;
  const row = (u) => `
    <div class="user-row" data-user="${esc(u.username)}">
      <div class="user-main"><b>${esc(u.name)}</b> <span class="dim-text mono">${esc(u.username)}</span>${u.username === ui.me.username ? ' <span class="status svc">tú</span>' : ""}
        <small>${esc(u.role_label)}${u.role === "admin" ? " · todo" : ` · ${u.services === "*" ? "todos los servicios" : u.services.map(svcName).map(esc).join(", ") || "ningún servicio"}`}
          · ${u.last_login ? `entró ${fmtAgo(u.last_login)}` : "aún no ha entrado"}</small></div>
      <button type="button" class="btn sm" data-uact="edit">${ICON.edit}Editar</button>
      ${u.username === ui.me.username ? "" : `<button type="button" class="btn sm icon ghost" data-uact="del" title="Borrar usuario" aria-label="Borrar usuario">${ICON.trash}</button>`}
    </div>`;
  const editor = (u = null) => `
    <form class="user-edit" id="user-form" novalidate>
      <h3 class="set-h">${u ? `Editar ${esc(u.username)}` : "Nuevo usuario"}</h3>
      <div class="set-grid">
        <label class="field"><span>Usuario</span><input name="username" class="mono" autocapitalize="off" spellcheck="false" value="${esc(u?.username || "")}" ${u ? "disabled" : ""}
          placeholder="amigo"><small>Minúsculas, números, punto o guion. Es con lo que entra.</small></label>
        <label class="field"><span>Nombre</span><input name="name" value="${esc(u?.name || "")}" placeholder="Nombre para mostrar"></label>
      </div>
      <div class="field"><span>Rol</span><div class="kind-pick">
        ${Object.entries({ admin: "Todo: servicios, archivos, ajustes y usuarios", operator: "Ver, encender, apagar, reiniciar y escribir en la consola", viewer: "Solo ver estado, gráficas y logs" })
          .map(([k, d]) => `<label><input type="radio" name="role" value="${k}" ${(u?.role || "viewer") === k ? "checked" : ""}><span><strong>${esc(roles[k])}</strong><small>${d}</small></span></label>`).join("")}
      </div></div>
      <div class="field" id="svc-pick"><span>Servicios a los que tiene acceso</span>
        <label class="chk-line"><input type="checkbox" name="all" ${!u || u.services === "*" ? "checked" : ""}> Todos (también los que crees después)</label>
        <div class="svc-checks">${services.map((s) => `<label class="chk-line"><input type="checkbox" name="svc" value="${esc(s.id)}"
          ${u && Array.isArray(u.services) && u.services.includes(s.id) ? "checked" : ""}> ${esc(s.name)}</label>`).join("")}</div>
      </div>
      <label class="field"><span>${u ? "Nueva contraseña" : "Contraseña"}</span><input name="password" type="password" autocomplete="new-password"
        placeholder="${u ? "vacía = no cambiarla" : "al menos 8 caracteres"}"><small>${u ? "Si la cambias, o cambias su rol o servicios, sus sesiones abiertas se cierran." : "Pásasela por un canal seguro; podrá cambiarla en Ajustes → Mi cuenta."}</small></label>
      <div class="form-error" id="user-error"></div>
      <footer class="set-foot"><button type="button" class="btn ghost" data-uact="cancel">Cancelar</button><span class="grow"></span>
        <button type="submit" class="btn primary">${u ? "Guardar" : "Crear usuario"}</button></footer>
    </form>`;
  body.innerHTML = `
    <h2 class="set-title">Usuarios</h2>
    <p class="set-sub">Quién puede entrar al panel y qué puede hacer. Para que alguien llegue desde internet, añade también su correo
      a la regla de Cloudflare Access (Zero Trust → Access → Applications → la de NovaHub → Policies).</p>
    <div class="user-list">${users.map(row).join("")}</div>
    <div id="user-editor"><button type="button" class="btn" data-uact="new">${ICON.plus}Añadir usuario</button></div>`;
  const openEditor = (u) => {
    $("#user-editor", body).innerHTML = editor(u);
    const f = $("#user-form", body);
    const sync = () => {
      const admin = f.querySelector('[name="role"]:checked').value === "admin";
      $("#svc-pick", body).hidden = admin;
      f.querySelectorAll('[name="svc"]').forEach((c) => { c.disabled = f.all.checked; });
    };
    f.addEventListener("change", sync);
    sync();
    (u ? f.name : f.username).focus();
    f.addEventListener("submit", async (e) => {
      e.preventDefault();
      const data = { name: f.name.value.trim(), role: f.querySelector('[name="role"]:checked').value,
        services: f.all.checked ? "*" : [...f.querySelectorAll('[name="svc"]:checked')].map((c) => c.value) };
      if (f.password.value) data.password = f.password.value;
      try {
        if (u) await api("PUT", `/api/users/${encodeURIComponent(u.username)}`, data);
        else await api("POST", "/api/users", { ...data, username: f.username.value.trim().toLowerCase() });
        toast(u ? "Usuario guardado" : "Usuario creado", "ok");
        setUsers(body);
      } catch (err) { $("#user-error", body).textContent = err.message; }
    });
  };
  body.onclick = async (e) => {
    const act = e.target.closest("[data-uact]")?.dataset.uact;
    const name = e.target.closest("[data-user]")?.dataset.user;
    const u = users.find((x) => x.username === name);
    if (act === "new") openEditor(null);
    else if (act === "edit") { openEditor(u); $("#user-editor", body).scrollIntoView({ block: "nearest", behavior: "smooth" }); }
    else if (act === "cancel") setUsers(body);
    else if (act === "del" && await confirmDialog("Borrar usuario", `«${u.name}» (${u.username}) no podrá volver a entrar. Sus sesiones se cierran al momento.`, "Borrar")) {
      try { await api("DELETE", `/api/users/${encodeURIComponent(name)}`); toast("Usuario borrado", "ok"); setUsers(body); }
      catch (err) { toast(err.message, "error"); }
    }
  };
}

async function setServers(body) {
  const { servers } = await api("GET", "/api/servers");
  const row = (s) => {
    const st = s.status || {};
    return `<div class="user-row" data-server="${esc(s.id)}">
      <span class="srv-dot ${st.online ? "on" : "off"}" title="${st.online ? "En línea" : esc(st.error || "Sin conexión")}"></span>
      <div class="user-main"><b>${esc(s.name)}</b> <span class="dim-text mono">${esc(s.url)}</span>
        <small>${st.online ? `${esc(st.hostname)} · ${st.running} de ${st.services} servicios en marcha${st.crashed ? ` · <span class="bad-text">${st.crashed} con error</span>` : ""} · RAM ${fmtBytes(st.mem_used)} de ${fmtBytes(st.mem_total)}`
          : `<span class="bad-text">${esc(st.error || "Sin conexión")}</span>`}</small></div>
      <button type="button" class="btn sm" data-sact="open" ${st.online ? "" : "disabled"}>Abrir</button>
      <button type="button" class="btn sm icon ghost" data-sact="del" title="Quitar del panel" aria-label="Quitar del panel">${ICON.trash}</button>
    </div>`;
  };
  setForm(body, `
    <h2 class="set-title">Servidores</h2>
    <p class="set-sub">Otros servidores con NovaHub que puedes manejar desde este panel con el selector de arriba. Las peticiones van
      por <b>Tailscale</b> (red privada y cifrada, sin abrir puertos).</p>
    <div class="user-list">${servers.length ? servers.map(row).join("") : '<p class="dim-text">Aún no hay otros servidores.</p>'}</div>
    <details class="adv" ${servers.length ? "" : "open"}><summary>Cómo preparar otro servidor</summary><div class="inner set-steps">
      <ol>
        <li>Instala NovaHub en el otro servidor (Linux) y Tailscale con tu misma cuenta.</li>
        <li>En su <code>novahub.service</code>, añade <code>Environment=NOVAHUB_REMOTE_LISTEN=&lt;su IP de Tailscale&gt;:8687</code> y reinícialo.
          Es una puerta solo para paneles: no tiene interfaz ni inicio de sesión, solo acepta llaves.</li>
        <li>En el NovaHub de ese servidor: Ajustes → <b>Acceso remoto</b> → crea una llave y cópiala.</li>
        <li>Aquí abajo: nombre, <code>http://&lt;su IP de Tailscale&gt;:8687</code> y la llave.</li>
      </ol></div></details>
    <h3 class="set-h">Añadir servidor</h3>
    <div class="set-grid">
      <label class="field"><span>Nombre</span><input name="name" placeholder="Raspberry del salón"></label>
      <label class="field"><span>Dirección</span><input name="url" class="mono" spellcheck="false" placeholder="http://100.64.0.2:8687"></label>
    </div>
    <label class="field"><span>Llave de acceso</span><input name="token" type="password" class="mono" spellcheck="false" autocomplete="off" placeholder="nh_…">
      <small>Se comprueba la conexión antes de guardarlo.</small></label>`, async (f) => {
    await api("POST", "/api/servers", { name: f.name.value.trim(), url: f.url.value.trim(), token: f.token.value.trim() });
    await loadServers();
    setServers(body);
  });
  $("#set-save", body).textContent = "Añadir servidor";
  body.onclick = async (e) => {
    const act = e.target.closest("[data-sact]")?.dataset.sact, id = e.target.closest("[data-server]")?.dataset.server;
    if (act === "open") switchServer(id);
    if (act === "del" && await confirmDialog("Quitar servidor", "Deja de verse en este panel. El otro servidor y sus servicios siguen funcionando; revoca también la llave allí si ya no la vas a usar.", "Quitar")) {
      try { await api("DELETE", `/api/servers/${id}`); await loadServers(); setServers(body); } catch (err) { toast(err.message, "error"); }
    }
  };
}

async function setTokens(body) {
  const d = await api("GET", "/api/tokens");
  const list = () => d.tokens.length ? d.tokens.map((t) => `<div class="user-row" data-token="${esc(t.id)}">
      <div class="user-main"><b>${esc(t.name)}</b> <span class="dim-text">de ${esc(t.user)}</span>
        <small>creada ${fmtAgo(t.created)} · ${t.last_used ? `usada ${fmtAgo(t.last_used)}` : "sin usar"}</small></div>
      <button type="button" class="btn sm" data-tact="del">Revocar</button></div>`).join("") : '<p class="dim-text">No hay llaves.</p>';
  setForm(body, `
    <h2 class="set-title">Acceso remoto</h2>
    <p class="set-sub">Llaves para que <b>otro</b> panel NovaHub maneje ${ui.server !== "local" ? "este servidor" : "este servidor"} (Ajustes → Servidores, allí).
      Cada llave actúa con tus permisos; revócala y deja de valer al momento.</p>
    ${d.listen ? `<p class="nt-ok">Puerta para otros paneles activa en <code>http://${esc(d.listen)}</code>.</p>`
      : '<p class="git-note">La puerta para otros paneles está cerrada. Para abrirla, añade <code>Environment=NOVAHUB_REMOTE_LISTEN=&lt;IP de Tailscale&gt;:8687</code> a novahub.service y reinicia NovaHub.</p>'}
    <div class="user-list" id="tok-list">${list()}</div>
    <div id="tok-new"></div>
    <h3 class="set-h">Nueva llave</h3>
    <label class="field"><span>Para qué panel es</span><input name="name" placeholder="Panel principal"></label>`, async (f) => {
    const r = await api("POST", "/api/tokens", { name: f.name.value.trim() });
    d.tokens = r.tokens;
    $("#tok-list", body).innerHTML = list();
    $("#tok-new", body).innerHTML = `<div class="nt-ok tok-show"><b>Copia la llave ahora: no se vuelve a mostrar.</b>
      <code id="tok-raw">${esc(r.token)}</code><button type="button" class="btn sm" data-tact="copy">Copiar</button></div>`;
    f.reset();
  });
  $("#set-save", body).textContent = "Crear llave";
  body.onclick = async (e) => {
    const act = e.target.closest("[data-tact]")?.dataset.tact;
    if (act === "copy") { navigator.clipboard?.writeText($("#tok-raw", body).textContent).then(() => toast("Llave copiada", "ok"), () => {}); }
    if (act === "del") {
      const id = e.target.closest("[data-token]").dataset.token;
      if (!(await confirmDialog("Revocar llave", "El panel que la usa dejará de poder manejar este servidor al momento.", "Revocar"))) return;
      try { d.tokens = (await api("DELETE", `/api/tokens/${id}`)).tokens; $("#tok-list", body).innerHTML = list(); } catch (err) { toast(err.message, "error"); }
    }
  };
}

function setApp(body) {
  body.innerHTML = `
    <h2 class="set-title">App para el móvil</h2>
    <p class="set-sub">NovaHub se instala como app: icono en la pantalla de inicio y se abre a pantalla completa, sin la barra del navegador.
      Sigue pasando por el túnel, con tu cuenta de Google y la contraseña.</p>
    ${appInstallHTML()}`;
  if (body.dataset.bound) return;
  body.dataset.bound = "1";
  body.addEventListener("click", async (e) => {
    if (!e.target.closest("#app-install") || !ui.installPrompt) return;
    ui.installPrompt.prompt();
    const { outcome } = await ui.installPrompt.userChoice;
    if (outcome === "accepted") { ui.installPrompt = null; toast("NovaHub instalada: ábrela desde la pantalla de inicio", "ok"); setApp(body); }
  });
}

// ───────────────────────── app para el móvil (PWA) ─────────────────────────

const standalone = () => matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;

function appInstallHTML() {
  const apk = ui.sys?.android_apk ? `<h3 class="set-h">Android sin navegador ni Google Play</h3>
    <p>App propia de NovaHub (APK). Descárgala aquí, pásala al móvil (cable USB, Bluetooth…) y ábrela con el gestor de archivos;
      Android pedirá permitir «instalar apps de origen desconocido» para ese gestor.</p>
    <a class="btn" href="/api/app/android" download>${ICON.download}Descargar la app para Android (APK)</a>` : "";
  return appInstallHTMLWeb() + apk;
}

function appInstallHTMLWeb() {
  if (standalone()) return '<p class="nt-ok">Ya estás usando NovaHub como app.</p>';
  if (ui.installPrompt) {
    return `<p>Ábrela desde la pantalla de inicio, a pantalla completa y sin la barra del navegador.</p>
      <button type="button" class="btn" id="app-install">${ICON.download}Instalar NovaHub</button>`;
  }
  const ios = /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  return ios
    ? "<p>En el iPhone, desde <strong>Safari</strong>: botón <strong>Compartir</strong> → <strong>Añadir a pantalla de inicio</strong>.</p>"
    : "<p>En Android, desde <strong>Chrome</strong>: menú <strong>⋮</strong> → <strong>Instalar aplicación</strong> (o «Añadir a pantalla de inicio»).</p>";
}

window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); ui.installPrompt = e; });  // se ofrece en Ajustes
window.addEventListener("appinstalled", () => { ui.installPrompt = null; });
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}

// Aviso de «sin conexión» (útil sobre todo en la app: la interfaz abre aunque no haya red)
function setOffline(off) {
  let bar = $("#offline");
  if (!bar) {
    bar = document.createElement("div");
    bar.id = "offline";
    bar.setAttribute("role", "status");
    bar.textContent = "Sin conexión con el servidor: los datos no se actualizan";
    document.body.appendChild(bar);
  }
  bar.hidden = !off;
}
window.addEventListener("offline", () => setOffline(true));
window.addEventListener("online", () => setOffline(false));

async function powerOff() {
  try {
    const p = await api("GET", "/api/power");
    if (p.phase) return toast("El servidor ya se está apagando", "ok");
    if (!p.sudo) return toast("NovaHub aún no tiene permiso para apagar el servidor (regla de sudoers, ver README).", "error");
    const plug = p.tapo
      ? "Después, el enchufe Tapo cortará la corriente."
      : "El enchufe Tapo no está configurado: se quedará encendido.";
    const ok = await confirmDialog("Apagar servidor",
      `Se pararán todos los servicios y se apagará el servidor. ${plug} Para volver a encenderlo tendrás que usar el enchufe (app Tapo, Alexa o el botón).`,
      "Apagar");
    if (!ok) return;
    await api("POST", "/api/power/off");
    toast("Apagando: parando servicios…", "ok");
  } catch (e) { toast(e.message, "error"); }
}

function refreshCurrent() {
  if (ui.current) refreshDetail(ui.current.id);
  else if ($("#ov-rows")) refreshOverview();
  else refreshList();
}

document.addEventListener("click", async (e) => {
  const el = e.target.closest("[data-act]");
  if (!el) return;
  const act = el.dataset.act;
  const s = ui.current;
  if (act === "toggle") { e.stopPropagation(); toggle(el.dataset.id || s?.id); }
  else if (act === "new") location.hash = "#/nuevo";
  else if (act === "poweroff") powerOff();
  else if (act === "theme") toggleTheme();
  else if (act === "logout") {
    await api("POST", "/api/logout").catch(() => {});
    ui.unlocked = false;
    showLogin("Has cerrado la sesión.");
  }
  else if (!s) return;
  else if (act === "restart") restart(s.id);
  else if (act === "update") updateService(s.id);
  else if (act === "mode-prod" || act === "mode-dev") setMode(s, act === "mode-prod" ? "prod" : "dev");
  else if (act === "edit") location.hash = `#/s/${s.id}/editar`;
  else if (act === "delete") removeService(s);
  else if (act === "clear-log") {
    if (await confirmDialog("Limpiar consola", "Se borrará el historial guardado de la consola.", "Limpiar")) {
      api("POST", `/api/services/${s.id}/logs/clear`).catch((err) => toast(err.message, "error"));
    }
  }
});

// ───────────────────────── vista: detalle ─────────────────────────

function viewDetail(id) {
  $("#main").innerHTML = `
    <a class="back" href="#/servicios">${ICON.back}Servicios</a>
    <div id="d-head"></div>
    <section class="kpis d-kpis" id="d-kpis"></section>
    ${usageHTML(id)}
    <div class="d-body">
      <section class="term module" id="term">
        <div class="term-bar">
          <div class="tabs" role="tablist" aria-label="Vistas del servicio">
            <button type="button" role="tab" class="tab term-title" id="live" data-tab="console" aria-selected="true">Consola</button>
            <button type="button" role="tab" class="tab" data-tab="files" data-perm="edit" aria-selected="false">${ICON.folder}Archivos</button>
            <button type="button" role="tab" class="tab" data-tab="git" data-perm="edit" aria-selected="false">${ICON.git}Git<span class="count" id="git-count" hidden></span></button>
            <button type="button" role="tab" class="tab" data-tab="backups" data-perm="edit" aria-selected="false">${ICON.archive}Copias</button>
            <button type="button" role="tab" class="tab" data-tab="tasks" data-perm="edit" aria-selected="false">${ICON.clock}Tareas</button>
            <button type="button" role="tab" class="tab" data-tab="env" data-perm="edit" aria-selected="false">${ICON.key}Variables</button>
          </div>
          <div class="term-tools" data-for="console">
            <label class="chk" title="Auto-scroll"><input type="checkbox" id="autoscroll" checked><span>Auto-scroll</span></label>
            <a class="btn sm icon" href="${esc(apiUrl(`/api/services/${id}/logs/download`))}" download title="Descargar log" aria-label="Descargar log">${ICON.download}</a>
            <button class="btn sm icon" data-act="clear-log" data-perm="edit" title="Limpiar consola" aria-label="Limpiar consola">${ICON.trash}</button>
            <button class="btn sm icon" data-term="max" title="Pantalla completa (Esc para salir)" aria-label="Pantalla completa">${ICON.expand}</button>
          </div>
        </div>
        <div class="screen" data-pane="console">
          <div class="lsearch" id="lsearch">
            ${ICON.search}
            <input id="lq" type="search" placeholder="Buscar en todo el log…  ( / )" autocomplete="off" spellcheck="false" aria-label="Buscar en el log">
            <button type="button" class="ls-chip" data-ls="errors" aria-pressed="false" title="Mostrar solo las líneas con errores">Solo errores</button>
            <button type="button" class="ls-chip mono" data-ls="regex" aria-pressed="false" title="Expresión regular">.*</button>
            <button type="button" class="ls-chip" data-ls="case" aria-pressed="false" title="Distinguir mayúsculas y minúsculas">Aa</button>
            <button type="button" class="ls-chip ls-x" data-lsclear title="Quitar la búsqueda (Esc)" aria-label="Quitar la búsqueda">✕</button>
          </div>
          <pre class="term-out" id="out"></pre>
          <div class="term-out found" id="found" hidden></div>
          <form class="term-in" id="cin" data-perm="console">
            <span class="prompt" id="prompt"></span>
            <input id="cmd" placeholder="enviar un comando al proceso…" autocomplete="off" spellcheck="false" aria-label="Comando">
            <button class="btn sm" type="submit">↵</button>
          </form>
        </div>
        <div class="pane" data-pane="files" id="files" hidden></div>
        <div class="pane" data-pane="git" id="git" hidden></div>
        <div class="pane" data-pane="backups" id="backups" hidden></div>
        <div class="pane" data-pane="tasks" id="tasks" hidden></div>
        <div class="pane" data-pane="env" id="envpane" hidden></div>
      </section>
      <aside class="side" id="d-info"></aside>
    </div>`;

  const term = $("#term");
  term.querySelector("[data-term=max]").addEventListener("click", () => {
    term.classList.toggle("max");
    $("#out").scrollTop = $("#out").scrollHeight;
  });

  ui.current = { id };
  refreshDetail(id);
  every(2000, () => refreshDetail(id));
  openConsole(id);
  setupLogSearch(id);
  setupInput(id);
  setupTabs(id);
  setupUsage();
}

// ───────────────────────── ficha: pestañas ─────────────────────────

function setupTabs(id) {
  const term = $("#term");
  const loaded = new Set();
  term.querySelector(".tabs").addEventListener("click", async (e) => {
    const tab = e.target.closest("[data-tab]")?.dataset.tab;
    if (!tab) return;
    if (tab !== "files" && !(await leaveEditor())) return;
    term.querySelectorAll("[data-tab]").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === tab)));
    term.querySelectorAll("[data-pane]").forEach((p) => { p.hidden = p.dataset.pane !== tab; });
    term.querySelector("[data-for=console]").hidden = tab !== "console";
    if (tab === "console") $("#out").scrollTop = $("#out").scrollHeight;
    if (!loaded.has(tab)) {
      loaded.add(tab);
      if (tab === "files") loadFiles(id, "");
      if (tab === "git") loadGit(id);
      if (tab === "backups") loadBackups(id);
      if (tab === "tasks") loadTasks(id);
      if (tab === "env") loadEnv(id);
    }
  });
  $("#files").addEventListener("click", async (e) => {
    const act = e.target.closest("[data-fact]")?.dataset.fact;
    if (act === "edit") return editFile(id, ui.file);
    if (act === "save") return saveFile(id);
    if (act === "new") return newFile(id, e.target.closest("[data-fact]").dataset.dir);
    const el = e.target.closest("[data-path]");
    if (!el) return;
    e.preventDefault();
    if (!(await leaveEditor())) return;
    if (el.dataset.kind === "file") openFile(id, el.dataset.path);
    else loadFiles(id, el.dataset.path);
  });
  $("#backups").addEventListener("click", (e) => {
    const b = e.target.closest("[data-bk]");
    if (b) backupAction(id, b.dataset.bk, b.dataset.name);
  });
  $("#backups").addEventListener("submit", (e) => { e.preventDefault(); saveBackupConfig(id, e.target); });
  $("#tasks").addEventListener("click", (e) => taskEdit(id, e));
  $("#tasks").addEventListener("input", (e) => taskField(id, e));
  $("#tasks").addEventListener("change", (e) => taskField(id, e));
  every(5000, () => refreshTaskStatus(id));
  $("#envpane").addEventListener("click", (e) => envClick(id, e));
  $("#envpane").addEventListener("input", (e) => {
    const row = e.target.closest(".env-row");
    if (!row || !e.target.dataset.f) return;
    ui.envDraft[+row.dataset.i][e.target.dataset.f] = e.target.value;
    envMark();
  });
  $("#envpane").addEventListener("change", async (e) => {
    if (e.target.id !== "env-file") return;
    if (ui.envDirty && !(await confirmDialog("Cambios sin guardar", `Hay cambios sin guardar en ${ui.envFile}. ¿Descartarlos y abrir ${e.target.value}?`, "Descartar"))) {
      e.target.value = ui.envFile;
      return;
    }
    loadEnv(id, e.target.value);
  });
  $("#git").addEventListener("click", (e) => {
    const act = e.target.closest("[data-git]")?.dataset.git;
    if (act) gitAction(id, act);
  });
  // el número de cambios pendientes se ve en la pestaña aunque no esté abierta
  api("GET", `/api/services/${id}/git`).then(drawGitCount).catch(() => {});
}

// ───────────────────────── ficha: archivos ─────────────────────────

const fileUrl = (id, path, action = "file") => apiUrl(`/api/services/${encodeURIComponent(id)}/${action}?path=${encodeURIComponent(path)}`);

function crumbsHTML(root, path) {
  const parts = path ? path.split("/") : [];
  const rootName = root.split("/").pop() || "/";
  let acc = "";
  const items = [`<button type="button" data-path="" data-kind="dir">${esc(rootName)}</button>`];
  parts.forEach((part, i) => {
    acc = acc ? `${acc}/${part}` : part;
    const last = i === parts.length - 1;
    items.push(last
      ? `<span class="here">${esc(part)}</span>`
      : `<button type="button" data-path="${esc(acc)}" data-kind="dir">${esc(part)}</button>`);
  });
  return `<nav class="crumbs" aria-label="Ruta">${ICON.folder}${items.join('<span class="sep">/</span>')}</nav>`;
}

async function loadFiles(id, path) {
  const pane = $("#files");
  pane.innerHTML = `<div class="pane-msg">Cargando…</div>`;
  try {
    const d = await api("GET", fileUrl(id, path, "files"));
    const parent = d.path.includes("/") ? d.path.slice(0, d.path.lastIndexOf("/")) : "";
    const rows = d.entries.map((e) => {
      const p = d.path ? `${d.path}/${e.name}` : e.name;
      return `<button type="button" class="frow${e.name.startsWith(".") ? " hidden-file" : ""}" data-path="${esc(p)}" data-kind="${e.dir ? "dir" : "file"}">
        <span class="ficon ${e.dir ? "dir" : ""}">${e.dir ? ICON.folder : ICON.file}</span>
        <span class="fname">${esc(e.name)}${e.link ? ' <span class="dim-text">↪</span>' : ""}</span>
        <span class="fsize num">${e.dir ? "" : fmtBytes(e.size)}</span>
        <span class="fdate">${fmtAgo(e.mtime)}</span>
      </button>`;
    }).join("");
    pane.innerHTML = `
      <div class="pane-bar">${crumbsHTML(d.root, d.path)}<span class="lcd">${d.total} elemento${d.total === 1 ? "" : "s"}</span>
        <button type="button" class="btn sm" data-fact="new" data-dir="${esc(d.path)}">${ICON.plus}Nuevo archivo</button></div>
      <div class="flist">
        ${d.path ? `<button type="button" class="frow up" data-path="${esc(parent)}" data-kind="dir"><span class="ficon">${ICON.back}</span><span class="fname">Subir un nivel</span></button>` : ""}
        ${rows || '<div class="pane-msg">Carpeta vacía.</div>'}
        ${d.total > d.entries.length ? `<div class="pane-msg">Se muestran ${d.entries.length} de ${d.total} elementos.</div>` : ""}
      </div>`;
  } catch (e) {
    pane.innerHTML = `<div class="pane-msg bad-text">${esc(e.message)}</div>`;
  }
}

// ───────────────────────── resaltado de código (sin dependencias) ─────────────────────────

const HL_KEYWORDS = {
  js: "const|let|var|function|return|if|else|for|while|do|switch|case|break|continue|new|class|extends|import|from|export|default|async|await|try|catch|finally|throw|typeof|instanceof|in|of|this|super|null|undefined|true|false|yield|static|get|set|as|interface|type|enum|implements",
  py: "def|class|return|if|elif|else|for|while|break|continue|import|from|as|with|try|except|finally|raise|pass|lambda|yield|global|nonlocal|in|is|not|and|or|None|True|False|async|await|self",
  sh: "if|then|else|elif|fi|for|while|do|done|case|esac|function|return|in|export|local|echo|exit",
};
const HL_RULES = (() => {
  const str = String.raw`"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'`;
  const num = String.raw`\b\d+(?:\.\d+)?\b`;
  const kw = (k) => String.raw`\b(?:${HL_KEYWORDS[k]})\b`;
  const tq = '"""[\\s\\S]*?"""|' + "'''[\\s\\S]*?'''";  // cadenas de triple comilla de Python
  return {
    js: [["c", String.raw`\/\/[^\n]*|\/\*[\s\S]*?\*\/`], ["s", `${str}|` + "`(?:\\\\.|[^`\\\\])*`"], ["t", String.raw`<\/?[A-Za-z][\w.-]*|\/?>`],
         ["k", kw("js")], ["n", num], ["f", String.raw`\b[A-Za-z_$][\w$]*(?=\s*\()`]],
    css: [["c", String.raw`\/\*[\s\S]*?\*\/`], ["s", str], ["k", String.raw`@[\w-]+|!important`],
          ["n", String.raw`#[0-9a-fA-F]{3,8}\b|-?\b\d+(?:\.\d+)?(?:px|rem|em|%|vh|vw|s|ms|deg|fr)?\b`], ["a", String.raw`[\w-]+(?=\s*:[^;{]*[;}])`]],
    html: [["c", String.raw`<!--[\s\S]*?-->`], ["t", String.raw`<\/?[\w-]+|\/?>`], ["a", String.raw`\b[\w:-]+(?==)`], ["s", str]],
    json: [["a", String.raw`"(?:\\.|[^"\\])*"(?=\s*:)`], ["s", str], ["k", String.raw`\b(?:true|false|null)\b`], ["n", String.raw`-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b`]],
    py: [["c", String.raw`#[^\n]*`], ["s", `${tq}|[rbfu]?(?:${str})`], ["k", kw("py") + String.raw`|@[\w.]+`], ["n", num], ["f", String.raw`\b[A-Za-z_]\w*(?=\s*\()`]],
    sh: [["c", String.raw`#[^\n]*`], ["s", str], ["k", kw("sh")], ["a", String.raw`\$\{?[\w@#?*]+\}?`]],
    yaml: [["c", String.raw`#[^\n]*`], ["a", String.raw`^[ \t-]*[\w.-]+(?=:)`], ["s", str], ["k", String.raw`\b(?:true|false|null|yes|no)\b`], ["n", num]],
    md: [["k", String.raw`^#{1,6} [^\n]*`], ["s", "`[^`\\n]+`|```[\\s\\S]*?```"], ["f", String.raw`\*\*[^*\n]+\*\*|\[[^\]\n]+\]\([^)\n]+\)`], ["c", String.raw`^>[^\n]*`]],
  };
})();
const HL_RE = {};
function langOf(path) {
  const ext = path.split(".").pop().toLowerCase();
  const map = { js: "js", jsx: "js", mjs: "js", cjs: "js", ts: "js", tsx: "js", css: "css", scss: "css", html: "html", htm: "html", svg: "html", xml: "html",
    vue: "html", json: "json", py: "py", sh: "sh", bash: "sh", env: "sh", yml: "yaml", yaml: "yaml", toml: "yaml", md: "md", markdown: "md" };
  if (/(^|\/)\.env(\.|$)/.test(path) || /(^|\/)(Dockerfile|Makefile)$/.test(path)) return "sh";
  return map[ext] || null;
}
// HTML coloreado: cada token en un <span class="tk-…">; todo el texto se escapa.
function highlight(code, lang) {
  const rules = HL_RULES[lang];
  if (!rules) return esc(code);
  const re = HL_RE[lang] ||= new RegExp(rules.map(([, r]) => `(${r})`).join("|"), "gm");
  let out = "", last = 0, m;
  re.lastIndex = 0;
  while ((m = re.exec(code))) {
    if (!m[0]) { re.lastIndex++; continue; }
    const i = m.slice(1).findIndex((g) => g !== undefined);
    out += esc(code.slice(last, m.index)) + `<span class="tk-${rules[i][0]}">${esc(m[0])}</span>`;
    last = re.lastIndex;
  }
  return out + esc(code.slice(last));
}
const gutter = (text) => Array.from({ length: (text.match(/\n/g) || []).length + 1 }, (_, i) => i + 1).join("\n");

// ───────────────────────── ficha: ver y editar archivos ─────────────────────────

async function openFile(id, path) {
  const pane = $("#files");
  pane.innerHTML = `<div class="pane-msg">Abriendo…</div>`;
  ui.editing = false;
  try {
    const f = await api("GET", fileUrl(id, path));
    ui.file = f;
    const dir = path.includes("/") ? path.slice(0, path.lastIndexOf("/")) : "";
    const editable = !f.binary && !f.truncated;
    let body;
    if (f.binary) {
      body = `<div class="pane-msg">Es un archivo binario (${fmtBytes(f.size)}): no se puede mostrar como texto. Puedes descargarlo.</div>`;
    } else {
      const text = f.text.endsWith("\n") ? f.text.slice(0, -1) : f.text;
      body = `<div class="editor readonly"><pre class="ed-gutter" aria-hidden="true">${gutter(text)}</pre>
        <pre class="ed-view">${highlight(text, langOf(f.path))}\n</pre></div>
        ${f.truncated ? `<div class="pane-msg">Se muestran los primeros ${fmtBytes(f.text.length)} de ${fmtBytes(f.size)}. Es demasiado grande para editarlo aquí; descárgalo para verlo entero.</div>` : ""}`;
    }
    pane.innerHTML = `
      <div class="pane-bar">
        <button type="button" class="btn sm" data-path="${esc(dir)}" data-kind="dir">${ICON.back}Volver</button>
        <span class="fpath mono">${esc(f.path)}</span>
        <span class="lcd">${fmtBytes(f.size)} · ${fmtAgo(f.mtime)}</span>
        ${editable ? `<button type="button" class="btn sm primary" data-fact="edit">${ICON.edit}Editar</button>` : ""}
        <a class="btn sm icon" href="${fileUrl(id, path, "file/download")}" download title="Descargar" aria-label="Descargar">${ICON.download}</a>
      </div>
      ${body}`;
  } catch (e) {
    pane.innerHTML = `<div class="pane-msg bad-text">${esc(e.message)}</div>`;
  }
}

function editFile(id, f) {
  const pane = $("#files");
  const lang = langOf(f.path);
  pane.innerHTML = `
    <div class="pane-bar">
      <button type="button" class="btn sm" data-path="${esc(f.path)}" data-kind="file">${ICON.back}Salir del editor</button>
      <span class="fpath mono">${esc(f.path)}</span>
      <span class="ed-state" id="ed-state">Sin cambios</span>
      <button type="button" class="btn sm primary" data-fact="save" id="ed-save" disabled>Guardar <kbd>Ctrl+S</kbd></button>
    </div>
    <div class="editor">
      <pre class="ed-gutter" aria-hidden="true"></pre>
      <div class="ed-main">
        <pre class="ed-hl" aria-hidden="true"></pre>
        <textarea class="ed-input" id="ed-input" spellcheck="false" autocapitalize="off" autocomplete="off" wrap="off" aria-label="Contenido de ${esc(f.path)}"></textarea>
      </div>
    </div>`;
  const ta = $("#ed-input"), hl = pane.querySelector(".ed-hl"), gut = pane.querySelector(".ed-gutter");
  ta.value = f.text;
  ui.editing = true;
  ui.editOriginal = f.text;
  let queued = false;
  const sync = () => { hl.scrollTop = gut.scrollTop = ta.scrollTop; hl.scrollLeft = ta.scrollLeft; };
  const paint = () => {
    queued = false;
    hl.innerHTML = highlight(ta.value, lang) + "\n ";  // el espacio final iguala la altura con el textarea
    gut.textContent = gutter(ta.value);
    const dirty = ta.value !== ui.editOriginal;
    $("#ed-save").disabled = !dirty;
    $("#ed-state").textContent = dirty ? "● Cambios sin guardar" : "Sin cambios";
    $("#ed-state").classList.toggle("dirty", dirty);
    sync();
  };
  ta.addEventListener("input", () => { if (!queued) { queued = true; requestAnimationFrame(paint); } });
  ta.addEventListener("scroll", sync);
  ui.editingId = id;
  ta.addEventListener("keydown", (e) => {
    if (e.key === "Tab" && !e.ctrlKey && !e.altKey) {  // el tabulador sangra en vez de saltar de campo
      e.preventDefault();
      const indent = lang === "py" ? "    " : "  ";
      const { selectionStart: a, selectionEnd: b } = ta;
      if (a === b && !e.shiftKey) ta.setRangeText(indent, a, b, "end");
      else {
        const lineStart = ta.value.lastIndexOf("\n", a - 1) + 1;
        const block = ta.value.slice(lineStart, b);
        const changed = e.shiftKey ? block.replace(new RegExp(`^(\\t| {1,${indent.length}})`, "gm"), "")
                                   : block.replace(/^/gm, indent);
        ta.setRangeText(changed, lineStart, b, "select");
      }
      ta.dispatchEvent(new Event("input"));
    }
  });
  paint();
  ta.focus();
  ta.setSelectionRange(0, 0);
}

async function saveFile(id, force = false) {
  const ta = $("#ed-input");
  if (!ta || !ui.file) return;
  const btn = $("#ed-save");
  if (btn) btn.disabled = true;
  try {
    const f = await api("PUT", fileUrl(id, ui.file.path), { content: ta.value, mtime: ui.file.mtime, force });
    ui.file = f;
    ui.editOriginal = ta.value;
    ta.dispatchEvent(new Event("input"));
    const svc = ui.current;
    toast(svc?.status === "running" && svc.mode !== "prod" ? "Guardado" : "Guardado. Reinicia o recompila el servicio para aplicar el cambio.", "ok");
  } catch (e) {
    if (/ha cambiado desde que lo abriste/.test(e.message)) {
      const ok = await confirmDialog("El archivo ha cambiado",
        "Alguien (u otro editor) ha modificado este archivo desde que lo abriste. Si lo guardas, sus cambios se perderán. La versión actual se guardará como copia de seguridad.",
        "Sobrescribir");
      if (ok) return saveFile(id, true);
    } else toast(e.message, "error");
    if (btn) btn.disabled = false;
  }
}

async function newFile(id, dir) {
  const dlg = modal(`
    <form id="nf-form" novalidate>
      <header><h2>Nuevo archivo</h2><button type="button" class="btn ghost icon" data-close aria-label="Cerrar">${ICON.close}</button></header>
      <div class="body">
        <div class="form-error" id="nf-error"></div>
        <label class="field"><span>Nombre</span>
          <div class="affix rev"><span>${esc(dir ? dir + "/" : "./")}</span><input id="nf-name" class="mono" spellcheck="false" autocomplete="off" placeholder="componente.jsx"></div>
          <small>Se crea vacío en esta carpeta y se abre en el editor.</small></label>
      </div>
      <footer><button type="button" class="btn ghost" data-close>Cancelar</button><button type="submit" class="btn primary">Crear</button></footer>
    </form>`, "small");
  $("#nf-name", dlg).focus();
  $("#nf-form", dlg).addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = $("#nf-name", dlg).value.trim();
    if (!name || /(^|\/)\.\.(\/|$)/.test(name) || name.startsWith("/")) {
      $("#nf-error", dlg).textContent = "Escribe un nombre de archivo válido";
      return;
    }
    const path = dir ? `${dir}/${name}` : name;
    try {
      const f = await api("PUT", fileUrl(id, path), { content: "", create: true });
      dlg.close();
      toast(`Creado ${f.path}`, "ok");
      ui.file = f;
      editFile(id, f);
    } catch (err) { $("#nf-error", dlg).textContent = err.message; }
  });
}

// Con cambios sin guardar en el editor, pregunta antes de salir. true = se puede salir.
async function leaveEditor() {
  const ta = $("#ed-input");
  if (!ui.editing || !ta || ta.value === ui.editOriginal) { ui.editing = false; return true; }
  const ok = await confirmDialog("Cambios sin guardar", "Si sales del editor, perderás los cambios que no has guardado.", "Salir sin guardar");
  if (ok) ui.editing = false;
  return ok;
}

// ───────────────────────── ficha: copias de seguridad ─────────────────────────

const BACKUP_KIND = { auto: "Automática", manual: "Manual", "antes-de-restaurar": "Antes de restaurar" };

async function loadBackups(id) {
  const pane = $("#backups");
  if (!pane.innerHTML) pane.innerHTML = `<div class="pane-msg">Cargando…</div>`;
  try {
    drawBackups(id, await api("GET", `/api/services/${id}/backups`));
  } catch (e) {
    pane.innerHTML = `<div class="pane-msg bad-text">${esc(e.message)}</div>`;
  }
}

function drawBackups(id, b) {
  const pane = $("#backups");
  const c = b.config;
  const newest = b.copies[0];
  const last = b.last?.at && !b.last.ok
    ? `<span class="bad-text">${esc(b.last.msg)}</span> · ${fmtAgo(b.last.at)}`
    : newest ? `Última copia <b class="mono">${esc(newest.label)}</b> · ${fmtAgo(newest.created)}` : "Todavía no hay copias";
  const d = b.disk;
  const where = d.mounted
    ? `<span class="bk-disk">${ICON.archive}<span>Se guardan en el <b>disco ${esc(d.kind || "de datos")}</b> · <code>${esc(d.path)}</code>` +
      (d.free != null ? ` · ${fmtBytes(d.free)} libres de ${fmtBytes(d.total)}` : "") + "</span></span>"
    : `<span class="bk-disk bad-text">${ICON.archive}<span>El disco de copias no está montado (<code>${esc(d.path)}</code>): no se pueden hacer copias hasta que vuelva.</span></span>`;
  const next = b.next ? `Próxima: ${new Date(b.next * 1000).toLocaleString("es-ES", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}` : "Sin copias programadas";
  const editing = pane.querySelector("#bk-form") && pane.contains(document.activeElement) && document.activeElement.closest("#bk-form");
  if (editing) {  // no pisar el formulario mientras se escribe: solo se refresca la lista y el estado
    pane.querySelector("#bk-status").innerHTML = `${last} · ${next}`;
    pane.querySelector("#bk-list").innerHTML = backupRows(id, b);
    return;
  }
  pane.innerHTML = `
    <div class="pane-bar">
      <span class="bk-status" id="bk-status">${last} · ${next}</span>
      <span class="grow"></span>
      <button type="button" class="btn sm primary" data-bk="run" ${b.running ? "disabled" : ""}>${ICON.archive}${b.running ? "Copiando…" : "Hacer copia ahora"}</button>
    </div>
    <div class="git-body">
      <form class="git-commit" id="bk-form" novalidate>
        <label class="chk bk-auto"><input type="checkbox" name="enabled" ${c.enabled ? "checked" : ""}><span><strong>Copias automáticas</strong></span></label>
        <div class="bk-grid">
          <label class="field"><span>Frecuencia</span>
            <select name="every"><option value="daily" ${c.every === "daily" ? "selected" : ""}>Cada día a una hora</option>
              <option value="hours" ${c.every === "hours" ? "selected" : ""}>Cada X horas</option></select></label>
          <label class="field" data-show="daily"><span>Hora</span><input name="at" value="${esc(c.at)}" placeholder="04:00" inputmode="numeric"></label>
          <label class="field" data-show="hours"><span>Cada (horas)</span><input name="hours" value="${c.hours}" inputmode="numeric"></label>
          <label class="field"><span>Conservar</span><input name="keep" value="${c.keep}" inputmode="numeric"><small>copias automáticas</small></label>
        </div>
        <label class="field"><span>Qué copiar</span><input name="paths" class="mono" value="${esc(c.paths.join(", "))}" placeholder="toda la carpeta del servicio" spellcheck="false">
          <small>Vacío = toda la carpeta. O subcarpetas separadas por comas, p. ej. <code>world, config</code>.</small></label>
        <label class="field"><span>Excluir</span><input name="exclude" class="mono" value="${esc(c.exclude.join(", "))}" spellcheck="false">
          <small>Nombres de carpetas o archivos que no se copian (se pueden regenerar). Admite comodines: <code>*.log</code>.</small></label>
        <label class="chk"><input type="checkbox" name="stop" ${c.stop ? "checked" : ""}><span>Parar el servicio durante la copia (juegos y bases de datos: así no se copia nada a medio escribir)</span></label>
        <button type="submit" class="btn">Guardar ajustes</button>
      </form>
      <p class="label">Copias guardadas · ${b.copies.length}</p>
      ${where}
      <div class="bk-list" id="bk-list">${backupRows(id, b)}</div>
    </div>`;
  const form = pane.querySelector("#bk-form");
  const toggle = () => form.querySelectorAll("[data-show]").forEach((el) => { el.hidden = el.dataset.show !== form.every.value; });
  form.every.addEventListener("change", toggle);
  toggle();
  if (b.running && !ui.backupPoll) {  // mientras copia o restaura, se refresca solo
    ui.backupPoll = setInterval(async () => {
      if (!$("#backups") || $("#backups").hidden) return;
      const fresh = await api("GET", `/api/services/${id}/backups`).catch(() => null);
      if (!fresh) return;
      if (!fresh.running) { clearInterval(ui.backupPoll); ui.backupPoll = null; }
      drawBackups(id, fresh);
    }, 2000);
    ui.timers.push(ui.backupPoll);
  }
}

function backupRows(id, b) {
  if (!b.copies.length) return '<p class="dim-text">Aún no hay copias. Pulsa «Hacer copia ahora» o activa las automáticas.</p>';
  return b.copies.map((x) => `
    <div class="bk-row">
      <span class="status ${x.kind === "manual" ? "svc" : ""}">${BACKUP_KIND[x.kind]}</span>
      <span class="bk-name mono" title="${esc(x.name)}">${esc(x.label)}</span>
      <span class="bk-date">${esc(fmtTime(x.created))}</span>
      <span class="bk-size num">${fmtBytes(x.size)}</span>
      <span class="bk-actions">
        <a class="btn sm icon" href="${esc(apiUrl(`/api/services/${encodeURIComponent(id)}/backups/download?name=${encodeURIComponent(x.name)}`))}" download title="Descargar" aria-label="Descargar">${ICON.download}</a>
        <button type="button" class="btn sm" data-bk="restore" data-name="${esc(x.name)}" ${b.running ? "disabled" : ""}>Restaurar</button>
        <button type="button" class="btn sm icon ghost" data-bk="delete" data-name="${esc(x.name)}" title="Borrar" aria-label="Borrar">${ICON.trash}</button>
      </span>
    </div>`).join("");
}

async function backupAction(id, act, name) {
  try {
    if (act === "run") {
      drawBackups(id, await api("POST", `/api/services/${id}/backups/run`));
      toast("Haciendo la copia: el progreso sale en la consola", "ok");
    } else if (act === "restore") {
      const svc = ui.current;
      const ok = await confirmDialog("Restaurar copia",
        `La carpeta de «${svc?.name || id}» quedará exactamente como en esta copia (lo que se haya creado después se borra; lo excluido, como node_modules, no se toca). ` +
        "Antes se guarda una copia del estado actual por si te arrepientes." + (isOn(svc || {}) ? " El servicio se parará y volverá a arrancar." : ""),
        "Restaurar");
      if (!ok) return;
      drawBackups(id, await api("POST", `/api/services/${id}/backups/restore`, { name }));
      toast("Restaurando: el progreso sale en la consola", "ok");
      $('[data-tab="console"]')?.click();
    } else if (act === "delete") {
      if (!(await confirmDialog("Borrar copia", "Esta copia se borrará del disco. No se puede deshacer.", "Borrar"))) return;
      drawBackups(id, await api("POST", `/api/services/${id}/backups/delete`, { name }));
      toast("Copia borrada", "ok");
    }
  } catch (e) { toast(e.message, "error"); }
}

async function saveBackupConfig(id, form) {
  const f = form.elements;
  try {
    const b = await api("PUT", `/api/services/${id}/backups`, {
      enabled: f.enabled.checked, every: f.every.value, at: f.at.value.trim(), hours: f.hours.value.trim(),
      keep: f.keep.value.trim(), paths: f.paths.value, exclude: f.exclude.value, stop: f.stop.checked,
    });
    document.activeElement?.blur();
    drawBackups(id, b);
    toast("Ajustes de copias guardados", "ok");
  } catch (e) { toast(e.message, "error"); }
}

// ───────────────────────── ficha: tareas programadas ─────────────────────────

const TASK_DAYS = ["L", "M", "X", "J", "V", "S", "D"];   // 0 = lunes, como en el servidor
const TASK_DAY_NAMES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"];

async function loadTasks(id) {
  const pane = $("#tasks");
  if (!pane.innerHTML) pane.innerHTML = `<div class="pane-msg">Cargando…</div>`;
  try {
    const d = await api("GET", `/api/services/${id}/tasks`);
    ui.taskActions = d.actions;
    ui.taskDraft = d.tasks.map((t) => ({ ...t }));
    ui.taskDirty = false;
    drawTasksPane(id, d);
  } catch (e) {
    pane.innerHTML = `<div class="pane-msg bad-text">${esc(e.message)}</div>`;
  }
}

// Refresco del estado (última vez, próxima, en curso) sin pisar lo que se está editando
async function refreshTaskStatus(id) {
  if (!$("#tasks") || $("#tasks").hidden || ui.taskDirty) return;
  const d = await api("GET", `/api/services/${id}/tasks`).catch(() => null);
  if (!d || ui.taskDirty || $("#tasks").contains(document.activeElement)) return;
  ui.taskDraft = d.tasks.map((t) => ({ ...t }));
  drawTasksPane(id, d);
}

const daysText = (days) => days.length === 7 ? "todos los días"
  : days.join() === "0,1,2,3,4" ? "de lunes a viernes"
  : days.join() === "5,6" ? "fines de semana"
  : days.map((d) => TASK_DAY_NAMES[d]).join(", ");

function drawTasksPane() {
  const pane = $("#tasks");
  const acts = ui.taskActions || {};
  const rows = ui.taskDraft.map((t, i) => {
    const last = t.last && t.last.ok !== null && t.last.ok !== undefined
      ? `<span class="${t.last.ok ? "ok-text" : "bad-text"}">${esc(t.last.msg)}</span> · ${fmtAgo(t.last.at)}` : "Aún no se ha ejecutado";
    const next = t.enabled && t.next ? `Próxima: ${new Date(t.next * 1000).toLocaleString("es-ES", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}` : "Desactivada";
    return `
    <div class="task" data-i="${i}">
      <div class="task-main">
        <label class="switch" title="Activar o desactivar"><input type="checkbox" data-f="enabled" ${t.enabled ? "checked" : ""}><span></span></label>
        <select data-f="action" aria-label="Acción">${Object.entries(acts).map(([k, v]) => `<option value="${k}" ${t.action === k ? "selected" : ""}>${esc(v)}</option>`).join("")}</select>
        <span class="task-at">a las <input data-f="at" value="${esc(t.at)}" inputmode="numeric" maxlength="5" aria-label="Hora (HH:MM)"></span>
        <div class="task-days" role="group" aria-label="Días">${TASK_DAYS.map((d, k) =>
          `<button type="button" class="day ${t.days.includes(k) ? "on" : ""}" data-day="${k}" aria-pressed="${t.days.includes(k)}" title="${TASK_DAY_NAMES[k]}">${d}</button>`).join("")}</div>
        <span class="grow"></span>
        <button type="button" class="btn sm" data-tk="run" ${t.id && !t.busy ? "" : "disabled"} title="${t.id ? "Ejecutarla ahora para probarla" : "Guarda primero"}">${t.busy ? "En marcha…" : "Probar"}</button>
        <button type="button" class="btn sm icon ghost" data-tk="del" title="Borrar tarea" aria-label="Borrar tarea">${ICON.trash}</button>
      </div>
      ${t.action === "input" || t.action === "command" ? `<input class="mono task-text" data-f="text" value="${esc(t.text)}" spellcheck="false"
        placeholder="${t.action === "input" ? "texto para la consola, p. ej. say Reinicio en 5 minutos" : "comando, p. ej. ./limpiar.sh"}">` : ""}
      <p class="task-meta">${esc(acts[t.action] || "")} ${esc(daysText(t.days))} a las ${esc(t.at)} · ${last} · ${next}</p>
    </div>`;
  }).join("");
  pane.innerHTML = `
    <div class="pane-bar">
      <span class="bk-status">${ui.taskDirty ? '<b class="warn-text">Cambios sin guardar</b>' : `${ui.taskDraft.length} tarea${ui.taskDraft.length === 1 ? "" : "s"}`}</span>
      <span class="grow"></span>
      <button type="button" class="btn sm" data-tk="add">${ICON.plus}Añadir tarea</button>
      <button type="button" class="btn sm primary" data-tk="save" ${ui.taskDirty ? "" : "disabled"}>Guardar</button>
    </div>
    <div class="git-body">
      ${rows || `<p class="dim-text">No hay tareas. Ejemplos: reiniciar cada noche a las 05:00, o encenderlo a las 09:00 y apagarlo a las 23:00
        de lunes a viernes para que solo funcione en ese horario.</p>`}
      <p class="dim-text task-help">Se ejecutan a su hora aunque no tengas el panel abierto, y lo que pasa queda en la consola.
        Los comandos se ejecutan en la carpeta del servicio y se cortan a los 10 minutos. Las copias de seguridad tienen su propio horario en «Copias».</p>
    </div>`;
}

function taskEdit(id, e) {
  const row = e.target.closest(".task");
  const t = row && ui.taskDraft[+row.dataset.i];
  const act = e.target.closest("[data-tk]")?.dataset.tk;
  if (act === "add") {
    ui.taskDraft.push({ id: "", action: "restart", at: "05:00", days: [0, 1, 2, 3, 4, 5, 6], text: "", enabled: true });
  } else if (act === "del" && t) {
    ui.taskDraft.splice(+row.dataset.i, 1);
  } else if (act === "save") {
    return saveTasks(id);
  } else if (act === "run" && t) {
    return api("POST", `/api/services/${id}/tasks/run`, { id: t.id })
      .then((d) => { ui.taskDraft = d.tasks.map((x) => ({ ...x })); drawTasksPane(id); toast("Tarea lanzada: el resultado sale en la consola", "ok"); })
      .catch((err) => toast(err.message, "error"));
  } else if (e.target.closest("[data-day]") && t) {
    const k = +e.target.closest("[data-day]").dataset.day;
    t.days = t.days.includes(k) ? t.days.filter((d) => d !== k) : [...t.days, k].sort();
  } else {
    return;
  }
  ui.taskDirty = true;
  drawTasksPane(id);
}

function taskField(id, e) {
  const row = e.target.closest(".task");
  const f = e.target.dataset.f;
  if (!row || !f) return;
  const t = ui.taskDraft[+row.dataset.i];
  t[f] = e.target.type === "checkbox" ? e.target.checked : e.target.value;
  ui.taskDirty = true;
  // solo al cambiar la acción se redibuja (aparece o desaparece el campo de texto); en el resto no,
  // porque redibujar al salir de un campo le quitaría el foco al siguiente que se ha pulsado
  if (e.type === "change" && f === "action") return drawTasksPane(id);
  $("#tasks .bk-status").innerHTML = '<b class="warn-text">Cambios sin guardar</b>';  // al escribir no se redibuja (perdería el foco)
  $("#tasks [data-tk=save]").disabled = false;
}

async function saveTasks(id) {
  try {
    const d = await api("PUT", `/api/services/${id}/tasks`, { tasks: ui.taskDraft });
    ui.taskDraft = d.tasks.map((t) => ({ ...t }));
    ui.taskDirty = false;
    drawTasksPane(id);
    toast("Tareas guardadas", "ok");
  } catch (err) { toast(err.message, "error"); }
}

// ───────────────────────── ficha: variables (.env) ─────────────────────────

async function loadEnv(id, file = ui.envFile || ".env") {
  const pane = $("#envpane");
  if (!pane.innerHTML) pane.innerHTML = `<div class="pane-msg">Cargando…</div>`;
  try {
    const d = await api("GET", `/api/services/${id}/env?file=${encodeURIComponent(file)}`);
    ui.envFile = d.file;
    ui.env = d;
    ui.envDraft = d.vars.map((v) => ({ ...v }));
    ui.envDirty = false;
    ui.envShow = new Set();
    drawEnv();
  } catch (e) {
    pane.innerHTML = `<div class="pane-msg bad-text">${esc(e.message)}</div>`;
  }
}

function drawEnv(saved = false) {
  const pane = $("#envpane"), d = ui.env;
  const files = [...new Set([...d.files, ".env", d.file])].sort();
  const warn = {
    "not-ignored": `<b>Este archivo no está en .gitignore.</b> Si haces commit, tus claves acabarían en GitHub.
      Añade <code>${esc(d.file)}</code> (o <code>.env*</code>) al archivo <code>.gitignore</code>.`,
    tracked: `<b>Este archivo ya está en el repositorio de git</b>, así que sus valores están (o estarán) en GitHub.
      Quítalo con <code>git rm --cached ${esc(d.file)}</code>, añádelo a <code>.gitignore</code> y cambia las claves que tuviera.`,
  }[d.git];
  const rows = ui.envDraft.map((v, i) => {
    const show = ui.envShow.has(i);
    return `<div class="env-row" data-i="${i}">
      <input class="mono env-key" data-f="key" value="${esc(v.key)}" placeholder="NOMBRE" spellcheck="false" autocomplete="off" aria-label="Nombre">
      <span class="env-eq">=</span>
      <input class="mono env-val" data-f="value" type="${show ? "text" : "password"}" value="${esc(v.value)}" placeholder="valor"
        spellcheck="false" autocomplete="new-password" aria-label="Valor de ${esc(v.key)}">
      <button type="button" class="btn sm icon ghost" data-env="eye" title="${show ? "Ocultar" : "Mostrar"} el valor" aria-label="${show ? "Ocultar" : "Mostrar"} el valor">${show ? ICON.eyeOff : ICON.eye}</button>
      <button type="button" class="btn sm icon ghost" data-env="del" title="Borrar variable" aria-label="Borrar variable">${ICON.trash}</button>
    </div>`;
  }).join("");
  const running = ui.current?.status === "running";
  pane.innerHTML = `
    <div class="pane-bar">
      <select id="env-file" aria-label="Archivo">${files.map((f) => `<option ${f === d.file ? "selected" : ""}>${esc(f)}</option>`).join("")}</select>
      <span class="bk-status" id="env-status">${ui.envDirty ? '<b class="warn-text">Cambios sin guardar</b>'
        : d.exists ? `${d.vars.length} variable${d.vars.length === 1 ? "" : "s"}` : "El archivo no existe: se creará al guardar"}</span>
      <span class="grow"></span>
      ${saved && running ? `<button type="button" class="btn sm" data-env="restart">${ICON.restart}Reiniciar para aplicar</button>` : ""}
      <button type="button" class="btn sm" data-env="toggle">${ui.envShow.size ? ICON.eyeOff : ICON.eye}${ui.envShow.size ? "Ocultar" : "Mostrar"} valores</button>
      <button type="button" class="btn sm" data-env="add">${ICON.plus}Añadir</button>
      <button type="button" class="btn sm primary" data-env="save" ${ui.envDirty ? "" : "disabled"}>Guardar</button>
    </div>
    <div class="git-body">
      ${warn ? `<p class="git-note bad">${warn}</p>` : ""}
      ${d.dupes?.length ? `<p class="git-note">Repetidas en el archivo: <code>${d.dupes.map(esc).join(", ")}</code>. Se muestra el valor que cuenta (el último); al guardar queda una sola.</p>` : ""}
      <div class="env-list">${rows || '<p class="dim-text">No hay variables. Pulsa «Añadir».</p>'}</div>
      <p class="dim-text task-help">Los valores van ocultos para que no se vean por encima del hombro. Los comentarios y el orden del
        archivo se conservan, y la versión anterior se guarda por si acaso. Casi todos los programas leen el .env solo al arrancar:
        reinicia el servicio para aplicar los cambios.</p>
    </div>`;
}

function envMark() {
  ui.envDirty = true;
  $("#env-status").innerHTML = '<b class="warn-text">Cambios sin guardar</b>';
  $('#envpane [data-env="save"]').disabled = false;
}

async function envClick(id, e) {
  const act = e.target.closest("[data-env]")?.dataset.env;
  if (!act) return;
  const row = e.target.closest(".env-row"), i = row ? +row.dataset.i : -1;
  if (act === "eye") { ui.envShow.has(i) ? ui.envShow.delete(i) : ui.envShow.add(i); return drawEnv(); }
  if (act === "toggle") { ui.envShow = ui.envShow.size ? new Set() : new Set(ui.envDraft.map((_, k) => k)); return drawEnv(); }
  if (act === "add") {
    ui.envDraft.push({ key: "", value: "" });
    ui.envShow.add(ui.envDraft.length - 1);  // al escribir un valor nuevo, mejor verlo
    ui.envDirty = true;
    drawEnv();
    return $("#envpane .env-row:last-child .env-key")?.focus();
  }
  if (act === "del") {
    ui.envDraft.splice(i, 1);
    ui.envShow = new Set([...ui.envShow].filter((k) => k !== i).map((k) => (k > i ? k - 1 : k)));
    ui.envDirty = true;
    return drawEnv();
  }
  if (act === "restart") {
    try { await api("POST", `/api/services/${id}/restart`); toast("Reiniciando con las variables nuevas", "ok"); $('[data-tab="console"]')?.click(); }
    catch (err) { toast(err.message, "error"); }
    return;
  }
  if (act === "save") return saveEnv(id);
}

async function saveEnv(id, force = false) {
  const vars = ui.envDraft.filter((v) => v.key.trim() || v.value);  // las filas vacías del todo no cuentan
  try {
    const d = await api("PUT", `/api/services/${id}/env?file=${encodeURIComponent(ui.envFile)}`,
      { vars: vars.map((v) => ({ key: v.key.trim(), value: v.value })), mtime: ui.env.mtime, force });
    ui.env = d;
    ui.envDraft = d.vars.map((v) => ({ ...v }));
    ui.envDirty = false;
    ui.envShow = new Set();
    drawEnv(true);
    toast(`${d.file} guardado`, "ok");
  } catch (err) {
    if (err.message.startsWith("El archivo ha cambiado")) {
      if (await confirmDialog("El archivo ha cambiado", `${ui.envFile} se ha modificado fuera del panel desde que lo abriste. ¿Guardar igualmente y sustituir esos cambios?`, "Guardar igualmente")) {
        return saveEnv(id, true);
      }
      return;
    }
    toast(err.message, "error");
  }
}

// ───────────────────────── ficha: git ─────────────────────────

const GIT_CODES = { M: "Modificado", A: "Nuevo", D: "Borrado", R: "Renombrado", C: "Copiado", U: "En conflicto", "?": "Sin seguimiento" };

function drawGitCount(g) {
  if (g?.repo && ui.current) ui.gitRepo = ui.current.id;
  const c = $("#git-count");
  if (!c) return;
  const n = g?.repo ? g.total_changes : 0;
  c.hidden = !n;
  c.textContent = n;
}

function githubUrl(remote) {
  if (!remote) return null;
  const m = remote.match(/github\.com[:/](.+?)(\.git)?$/);
  return m ? `https://github.com/${m[1]}` : null;
}

async function loadGit(id) {
  const pane = $("#git");
  pane.innerHTML = `<div class="pane-msg">Leyendo el repositorio…</div>`;
  try {
    drawGit(id, await api("GET", `/api/services/${id}/git`));
  } catch (e) {
    pane.innerHTML = `<div class="pane-msg bad-text">${esc(e.message)}</div>`;
  }
}

function drawGit(id, g, output = "") {
  drawGitCount(g);
  const pane = $("#git");
  if (!g.repo) {
    pane.innerHTML = `<div class="pane-msg"><strong>Esta carpeta no es un repositorio de git.</strong><br>
      Para usarlo aquí, clona el proyecto desde GitHub en <code>${esc(g.root)}</code> o ejecuta <code>git init</code> en esa carpeta.</div>`;
    return;
  }
  const web = githubUrl(g.remote);
  const n = g.total_changes;
  const sync = !g.upstream ? "Rama sin conectar con GitHub"
    : g.ahead && g.behind ? `${g.ahead} commit${g.ahead > 1 ? "s" : ""} por subir · ${g.behind} por traer`
    : g.ahead ? `${g.ahead} commit${g.ahead > 1 ? "s" : ""} sin subir a GitHub`
    : g.behind ? `${g.behind} commit${g.behind > 1 ? "s" : ""} nuevo${g.behind > 1 ? "s" : ""} en GitHub`
    : "Al día con GitHub";
  const msg = $("#git-msg")?.value || "";
  pane.innerHTML = `
    <div class="pane-bar">
      <span class="lcd">${esc(g.branch)}${g.upstream ? ` → ${esc(g.upstream)}` : ""}</span>
      <span class="git-sync ${g.ahead || g.behind ? "warn" : ""}">${sync}</span>
      <span class="grow"></span>
      ${web ? `<a class="btn sm" href="${esc(web)}" target="_blank" rel="noopener">Ver en GitHub ↗</a>` : ""}
      <button type="button" class="btn sm" data-git="pull" title="Solo git pull, sin reiniciar">Traer cambios</button>
      <button type="button" class="btn sm" data-git="update" title="Pull, dependencias y reinicio">${ICON.download}Actualizar y reiniciar</button>
      <button type="button" class="btn sm ${g.ahead || !g.upstream ? "primary" : ""}" data-git="push" ${g.ahead || !g.upstream ? "" : "disabled"}>${ICON.upload}Subir a GitHub</button>
    </div>
    <div class="git-body">
      ${g.top !== g.root ? `<p class="git-note">Esta carpeta está dentro del repositorio <code>${esc(g.top)}</code>: el commit incluirá todos los cambios de ese repositorio.</p>` : ""}
      <div class="git-commit">
        <label class="field"><span>Mensaje del commit</span>
          <textarea id="git-msg" rows="2" placeholder="Qué has cambiado, p. ej. «Editar tareas: guardar cambios»">${esc(msg)}</textarea></label>
        <button type="button" class="btn primary" data-git="commit" ${n ? "" : "disabled"}>Hacer commit${n ? ` (${n} archivo${n > 1 ? "s" : ""})` : ""}</button>
      </div>
      <p class="label">Cambios sin guardar · ${n}</p>
      ${n ? `<ul class="changes">${g.changes.map((c) => {
        const code = (c.code.trim()[0] || "?");
        return `<li><span class="gcode g${code === "?" ? "N" : code}" title="${GIT_CODES[code] || c.code}">${code === "?" ? "+" : code}</span><span class="mono">${esc(c.path)}</span></li>`;
      }).join("")}${g.total_changes > g.changes.length ? `<li class="dim-text">… y ${g.total_changes - g.changes.length} más</li>` : ""}</ul>`
        : '<p class="dim-text">No hay cambios: todo está guardado en el último commit.</p>'}
      ${g.last ? `<p class="label">Último commit</p>
        <p class="git-last"><span class="lcd">${esc(g.last.hash)}</span> ${esc(g.last.subject)} <span class="dim-text">· ${esc(g.last.author)} · ${fmtAgo(+g.last.time)}</span></p>` : ""}
      ${output ? `<p class="label">Salida de git</p><pre class="git-out">${esc(output)}</pre>` : ""}
    </div>`;
}

async function gitAction(id, act) {
  if (act === "update") return updateService(id);
  const body = {};
  if (act === "commit") {
    body.message = $("#git-msg")?.value || "";
    if (!body.message.trim()) { toast("Escribe un mensaje que explique los cambios", "error"); $("#git-msg")?.focus(); return; }
  }
  $("#git").querySelectorAll("button").forEach((b) => { b.disabled = true; });
  try {
    const res = await api("POST", `/api/services/${id}/git/${act}`, body);
    if (act === "commit") { const m = $("#git-msg"); if (m) m.value = ""; }
    drawGit(id, res.git, res.output);
    toast(act === "commit" ? "Commit guardado. Pulsa «Subir a GitHub» para publicarlo."
      : act === "push" ? "Cambios subidos a GitHub" : "Cambios traídos de GitHub", "ok");
  } catch (e) {
    toast(e.message, "error");
    loadGit(id);
  }
}

async function refreshDetail(id) {
  let s;
  try {
    s = await api("GET", `/api/services/${id}`);
  } catch (e) {
    if (e.message === "Servicio no encontrado" || e.message.startsWith("No tienes")) { toast(e.message, "error"); location.hash = "#/servicios"; }
    return;
  }
  if (!ui.current || ui.current.id !== id) return;
  ui.current = s;
  drawDetail(s);
}

function drawDetail(s) {
  const busy = s.status === "starting" || s.status === "stopping";
  const url = s.status === "running" ? openUrl(s) : null;
  const head = `
    <div class="d-head" data-status="${s.status}">
      <div class="d-title">
        <div class="d-status">${statusHTML(s)}<span class="sid">${esc(s.id)}</span></div>
        <h1>${esc(s.name)}</h1>
        ${s.description ? `<p class="d-desc">${esc(s.description)}</p>` : ""}
        ${tagsHTML(s.tags)}
      </div>
      <div class="d-actions">
        ${url ? `<a class="btn" href="${esc(url)}" target="_blank" rel="noopener">Abrir ↗</a>` : ""}
        ${s.kind === "container" || s.kind === "compose"
    ? `<button class="btn" data-act="update" data-perm="edit" ${s.updating ? "disabled" : ""} title="Descargar la versión nueva de la imagen y reiniciar si ha cambiado">${ICON.download}${s.updating ? "Actualizando…" : "Actualizar imagen"}</button>`
    : ui.gitRepo === s.id ? `<button class="btn" data-act="update" data-perm="edit" ${s.updating ? "disabled" : ""} title="Traer cambios de GitHub, instalar dependencias y reiniciar">${ICON.download}${s.updating ? "Actualizando…" : "Actualizar"}</button>` : ""}
        <button class="btn" data-act="restart" data-perm="operate" ${s.status === "running" ? "" : "disabled"}>${ICON.restart}Reiniciar</button>
        <button class="btn" data-act="edit" data-perm="edit">${ICON.edit}Editar</button>
        <button class="btn danger" data-act="delete" data-perm="edit" ${isOn(s) || busy ? "disabled title=\"Detén el servicio para eliminarlo\"" : ""}>${ICON.trash}Eliminar</button>
        <button class="btn power ${isOn(s) ? "off" : "on"}" data-act="toggle" data-perm="operate" ${s.status === "stopping" ? "disabled" : ""}>
          ${ICON.power}${isOn(s) ? "Apagar" : "Encender"}</button>
      </div>
    </div>`;
  const headEl = $("#d-head");
  if (headEl && headEl._html !== head) { headEl.innerHTML = head; headEl._html = head; }

  const cell = (k, v, cls = "") => `<div class="${cls}"><dt>${k}</dt><dd>${v}</dd></div>`;
  const dash = '<span class="dim-text">—</span>';
  const on = s.status === "running";
  const kpis =
    kpiHTML("Activo", on ? fmtDuration(s.uptime) : "—", on ? `desde ${fmtTime(s.started_at)}` : STATUS_LABEL[s.status].toLowerCase()) +
    kpiHTML("CPU", s.cpu != null ? `${s.cpu.toFixed(1)}<small>%</small>` : "—", s.processes ? `${s.processes} proceso${s.processes > 1 ? "s" : ""}` : "sin procesos") +
    kpiHTML("Memoria", s.memory != null ? fmtBytes(s.memory) : "—",
      s.memory_limit ? `límite ${fmtBytes(s.memory_limit * 2 ** 20)}` : (s.pid ? `PID ${s.pid}` : "sin proceso"),
      s.memory_limit && s.memory != null ? pct(s.memory, s.memory_limit * 2 ** 20) : null) +
    kpiHTML("Puerto", s.port ?? "—", s.port ? (s.listening ? "escuchando" : "no escucha") : "sin puerto");
  const kpiEl = $("#d-kpis");
  if (kpiEl && kpiEl._html !== kpis) { kpiEl.innerHTML = kpis; kpiEl._html = kpis; }

  const envKeys = Object.keys(s.env || {});
  const info = `
    <div class="module">
      <span class="label">Estado</span>
      <dl class="readout">
        ${s.url ? cell("URL", `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url.replace(/^https?:\/\//, ""))}</a>`) : ""}
        ${cell("Última salida", s.last_exit_at ? `${s.last_exit ?? "?"} <span class="dim-text">· ${fmtTime(s.last_exit_at)}</span>` : dash)}
        ${cell("Reinicios auto · 1 h", s.auto_restarts)}
        ${s.mem_restarts ? cell("Reinicios por memoria · 1 h", `<span class="bad-text">${s.mem_restarts}</span>`) : ""}
        ${(() => { const h = healthText(s); return h ? cell("Salud", `<span class="${h.cls}">${esc(h.text)}</span>`) : ""; })()}
        ${s.last_update ? cell("Última actualización", `<span class="${s.last_update.ok ? "" : "bad-text"}">${esc(s.last_update.msg)}</span> <span class="dim-text">· ${fmtAgo(s.last_update.at)}</span>`) : ""}
      </dl>
    </div>
    <div class="module" data-perm="edit">
      <span class="label">Configuración</span>
      <dl class="readout">
        ${cell("Comando", `<code>${esc(s.command)}</code>`, "wide")}
        ${cell("Directorio", `<code>${esc(s.cwd || "~")}</code>`, "wide")}
        ${envKeys.length ? cell("Variables", `<code>${envKeys.map(esc).join("\n")}</code>`, "wide") : ""}
        ${cell("Autoarranque", s.autostart ? "Sí" : "No")}
        ${cell("Si falla", s.restart_on_crash ? "Reinicia" : "Se para")}
        ${cell("Parada", s.stop_command ? `<code>${esc(s.stop_command)}</code>` : "SIGTERM")}
        ${s.can_build || s.mode === "prod" ? cell("Modo", modeHTML(s), "wide") : ""}
        ${cell("Límite de memoria", s.memory_limit ? `${fmtBytes(s.memory_limit * 2 ** 20)} · reinicia si lo pasa` : "Sin límite")}
        ${cell("Comprobación de salud", { http: `Web · GET ${esc(s.health_path || "/")}`, tcp: "Puerto abierto", off: "Desactivada" }[s.health_mode])}
      </dl>
    </div>`;
  const infoEl = $("#d-info");
  if (infoEl && infoEl._html !== info) { infoEl.innerHTML = info; infoEl._html = info; }

  const prompt = $("#prompt");
  if (prompt) {
    const html = `<b>${esc(ui.user || "user")}@${esc(ui.host || "server")}</b> <i>${esc(s.id)}</i> %`;
    if (prompt.innerHTML !== html) prompt.innerHTML = html;
  }

  const cmd = $("#cmd");
  if (cmd) {
    cmd.placeholder = s.status === "running"
      ? "comando para el proceso · !help para los del panel"
      : "servicio parado · escribe !start para encenderlo";
  }
}

// Comandos que entiende el propio panel (con «!»); todo lo demás va a la entrada del proceso.
const PANEL_COMMANDS = {
  start: ["Encender el servicio", (id) => api("POST", `/api/services/${id}/start`)],
  stop: ["Apagar el servicio", (id) => api("POST", `/api/services/${id}/stop`)],
  restart: ["Reiniciar el servicio", (id) => api("POST", `/api/services/${id}/restart`)],
  clear: ["Borrar el historial de la consola", (id) => api("POST", `/api/services/${id}/logs/clear`)],
  help: ["Mostrar esta ayuda", () => printHelp()],
};
const NOTE = (msg) => `\x1b[1;38;5;141m▌NovaHub\x1b[0m ${msg}\n`;

function printHelp() {
  const rows = Object.entries(PANEL_COMMANDS).map(([k, [desc]]) => `  \x1b[38;5;141m!${k.padEnd(9)}\x1b[0m${desc}`);
  ui.term?.write(NOTE("comandos del panel:") + rows.join("\n") +
    "\n  \x1b[2mSin «!», el texto se envía al programa (p. ej. «stop» en Minecraft).\x1b[0m\n");
}

async function runPanelCommand(id, line) {
  const name = line.slice(1).trim().toLowerCase();
  ui.term?.write(`\x1b[38;5;141m› ${line}\x1b[0m\n`);
  const cmd = PANEL_COMMANDS[name];
  if (!cmd) {
    ui.term?.write(NOTE(`\x1b[31mcomando desconocido: !${name}\x1b[0m`));
    printHelp();
    return;
  }
  await cmd[1](id);
  refreshDetail(id);
}

function setupInput(id) {
  const form = $("#cin"), input = $("#cmd");
  let idx = -1;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const line = input.value;
    if (!line.trim()) return;
    try {
      if (line.trim().startsWith("!")) {
        await runPanelCommand(id, line.trim());
      } else if (ui.current?.status !== "running") {
        ui.term?.write(NOTE("el servicio no está en marcha · usa \x1b[38;5;141m!start\x1b[0m para encenderlo"));
      } else {
        await api("POST", `/api/services/${id}/input`, { line });
      }
      if (ui.history[0] !== line) ui.history.unshift(line);
      ui.history.length = Math.min(ui.history.length, 50);
      input.value = "";
      idx = -1;
    } catch (err) {
      ui.term?.write(NOTE(`\x1b[31m${err.message}\x1b[0m`));
    }
    const out = $("#out");
    if (out && $("#autoscroll")?.checked) out.scrollTop = out.scrollHeight;
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowUp" && idx < ui.history.length - 1) { idx++; input.value = ui.history[idx]; e.preventDefault(); }
    else if (e.key === "ArrowDown") { idx = Math.max(-1, idx - 1); input.value = idx < 0 ? "" : ui.history[idx]; e.preventDefault(); }
  });
}

// ───────────────────────── consola (ANSI) ─────────────────────────

const ANSI16 = ["#3b4252", "#f87171", "#4ade80", "#facc15", "#60a5fa", "#c084fc", "#22d3ee", "#d6dae4",
                "#6b7280", "#fca5a5", "#86efac", "#fde047", "#93c5fd", "#d8b4fe", "#67e8f9", "#ffffff"];
function ansi256(n) {
  if (n < 16) return ANSI16[n];
  if (n >= 232) { const v = 8 + (n - 232) * 10; return `rgb(${v},${v},${v})`; }
  n -= 16;
  const c = (x) => (x ? 55 + x * 40 : 0);
  return `rgb(${c(Math.floor(n / 36))},${c(Math.floor(n / 6) % 6)},${c(n % 6)})`;
}

class AnsiRenderer {
  constructor(el) { this.el = el; this.carry = ""; this.reset(); }
  reset() { this.fg = null; this.bg = null; this.bold = false; this.dim = false; this.italic = false; this.underline = false; }
  clear() { this.el.textContent = ""; this.carry = ""; this.reset(); }

  write(chunk) {
    let text = this.carry + chunk;
    this.carry = "";
    // guarda una secuencia de escape incompleta para el siguiente trozo
    const tail = text.slice(text.lastIndexOf("\x1b"));
    if (tail.startsWith("\x1b") && (/^\x1b(\[[0-9;?]*)?$/.test(tail) || /^\x1b\][^\x07]*$/.test(tail))) {
      this.carry = tail;
      text = text.slice(0, -tail.length);
    }
    text = text.replace(/\x1b\][^\x07\x1b]*(\x07|\x1b\\)/g, "").replace(/\r\n/g, "\n").replace(/\r/g, "");

    const frag = document.createDocumentFragment();
    const re = /\x1b\[([0-9;?]*)([@-~])/g;
    let last = 0, m;
    while ((m = re.exec(text))) {
      this.emit(frag, text.slice(last, m.index));
      if (m[2] === "m") this.sgr(m[1]);
      last = re.lastIndex;
    }
    this.emit(frag, text.slice(last));
    this.el.appendChild(frag);
    while (this.el.childNodes.length > 6000) this.el.removeChild(this.el.firstChild);
  }

  emit(frag, s) {
    s = s.replace(/[\x00-\x08\x0b-\x1f\x7f]/g, "");
    if (!s) return;
    if (!this.fg && !this.bg && !this.bold && !this.dim && !this.italic && !this.underline) {
      frag.appendChild(document.createTextNode(s));
      return;
    }
    const span = document.createElement("span");
    span.textContent = s;
    if (this.fg) span.style.color = this.fg;
    if (this.bg) span.style.background = this.bg;
    if (this.bold) span.style.fontWeight = "700";
    if (this.dim) span.style.opacity = "0.6";
    if (this.italic) span.style.fontStyle = "italic";
    if (this.underline) span.style.textDecoration = "underline";
    frag.appendChild(span);
  }

  sgr(params) {
    const a = params === "" ? [0] : params.split(";").map((x) => parseInt(x || "0", 10));
    for (let i = 0; i < a.length; i++) {
      const n = a[i];
      if (n === 0) this.reset();
      else if (n === 1) this.bold = true;
      else if (n === 2) this.dim = true;
      else if (n === 3) this.italic = true;
      else if (n === 4) this.underline = true;
      else if (n === 22) { this.bold = false; this.dim = false; }
      else if (n === 23) this.italic = false;
      else if (n === 24) this.underline = false;
      else if (n >= 30 && n <= 37) this.fg = ANSI16[n - 30];
      else if (n >= 90 && n <= 97) this.fg = ANSI16[n - 82];
      else if (n === 39) this.fg = null;
      else if (n >= 40 && n <= 47) this.bg = ANSI16[n - 40];
      else if (n >= 100 && n <= 107) this.bg = ANSI16[n - 92];
      else if (n === 49) this.bg = null;
      else if (n === 38 || n === 48) {
        let color = null;
        if (a[i + 1] === 5) { color = ansi256(a[i + 2]); i += 2; }
        else if (a[i + 1] === 2) { color = `rgb(${a[i + 2]},${a[i + 3]},${a[i + 4]})`; i += 4; }
        if (n === 38) this.fg = color; else this.bg = color;
      }
    }
  }
}

function openConsole(id) {
  const out = $("#out"), live = $("#live"), auto = $("#autoscroll");
  const term = new AnsiRenderer(out);
  ui.term = term;
  const scroll = () => { if (auto.checked) out.scrollTop = out.scrollHeight; };

  out.addEventListener("scroll", () => {
    auto.checked = out.scrollTop + out.clientHeight >= out.scrollHeight - 30;
  });
  auto.addEventListener("change", scroll);

  const es = new EventSource(apiUrl(`/api/services/${encodeURIComponent(id)}/logs/stream`));
  // al (re)conectar el servidor vuelve a mandar la cola del log: se empieza de cero
  es.onopen = () => { term.clear(); live.classList.add("on"); };
  es.onmessage = (e) => { term.write(JSON.parse(e.data)); scroll(); };
  es.addEventListener("clear", () => term.clear());
  es.onerror = () => live.classList.remove("on");
  ui.es = es;
}

// ───────────────────────── consola: buscar en el log ─────────────────────────
// Busca en todo el log del servidor (no solo lo que hay en pantalla). Mientras hay búsqueda, la consola
// en directo se oculta y se ven los resultados; al vaciarla, vuelve.

function setupLogSearch(id) {
  const box = $("#lsearch"), q = $("#lq"), out = $("#out"), found = $("#found"), cin = $("#cin");
  const st = { errors: false, regex: false, case: false, timer: null, seq: 0 };
  const active = () => q.value.trim() !== "" || st.errors;

  const run = async () => {
    const on = active();
    out.hidden = cin.hidden = on;
    found.hidden = !on;
    box.classList.toggle("on", on);
    if (!on) { out.scrollTop = out.scrollHeight; return; }
    const seq = ++st.seq;
    const params = new URLSearchParams({ q: q.value.trim(), errors: st.errors ? "1" : "", regex: st.regex ? "1" : "", case: st.case ? "1" : "" });
    try {
      const d = await api("GET", `/api/services/${encodeURIComponent(id)}/logs/search?${params}`);
      if (seq !== st.seq) return;  // ya hay una búsqueda más nueva
      drawLogHits(found, d, q.value.trim() ? "" : "errores");
    } catch (e) {
      if (seq === st.seq) found.innerHTML = `<p class="hits-head bad">${esc(e.message)}</p>`;
    }
  };
  const later = () => { clearTimeout(st.timer); st.timer = setTimeout(run, 280); };

  q.addEventListener("input", later);
  q.addEventListener("keydown", (e) => { if (e.key === "Escape") { q.value = ""; st.errors = false; syncChips(); run(); q.blur(); } });
  const syncChips = () => box.querySelectorAll("[data-ls]").forEach((b) => {
    b.classList.toggle("on", !!st[b.dataset.ls]);
    b.setAttribute("aria-pressed", String(!!st[b.dataset.ls]));
  });
  box.addEventListener("click", (e) => {
    const b = e.target.closest("[data-ls]");
    if (b) { st[b.dataset.ls] = !st[b.dataset.ls]; syncChips(); run(); }
    if (e.target.closest("[data-lsclear]")) { q.value = ""; st.errors = false; syncChips(); run(); }
  });
  every(5000, () => { if (active() && !$("#found").hidden && document.activeElement !== q) run(); });  // lo nuevo también aparece
  // «/» abre la búsqueda, como en muchas herramientas (salvo escribiendo en otro campo)
  document.addEventListener("keydown", ui.onSlash = ui.onSlash || ((e) => {
    if (e.key === "/" && $("#lq") && !e.target.closest("input, textarea, select, dialog") && !$('[data-pane="console"]').hidden) {
      e.preventDefault();
      $("#lq").focus();
    }
  }));
}

function drawLogHits(el, d, mode) {
  const mark = (h) => {
    let html = "", last = 0;
    for (const [a, b] of h.spans) {
      if (a < last) continue;
      html += esc(h.text.slice(last, a)) + `<mark>${esc(h.text.slice(a, b))}</mark>`;
      last = b;
    }
    return html + esc(h.text.slice(last));
  };
  const head = d.total
    ? `${d.total.toLocaleString("es-ES")} ${mode ? "líneas con errores" : `coincidencia${d.total === 1 ? "" : "s"}`}` +
      (d.total > d.shown ? ` · se ven las ${d.shown} más recientes` : "") + ` · en ${d.lines.toLocaleString("es-ES")} líneas de log`
    : `Nada${mode ? " que parezca un error" : ""} en ${d.lines.toLocaleString("es-ES")} líneas de log`;
  let prev = null;
  const rows = d.matches.map((h) => {
    const sep = prev && prev !== h.file ? '<div class="hit-sep">— log actual —</div>' : "";
    prev = h.file;
    return `${sep}<div class="hit"><span class="ln" title="Línea ${h.n} del log ${h.file}">${h.n}</span><span class="tx">${mark(h)}</span></div>`;
  }).join("");
  const stick = el.scrollTop + el.clientHeight >= el.scrollHeight - 30;
  el.innerHTML = `<p class="hits-head">${head}</p>${d.matches[0]?.file === "anterior" ? '<div class="hit-sep">— log anterior —</div>' : ""}${rows}`;
  if (stick || !el._shown) el.scrollTop = el.scrollHeight;  // como la consola: lo más reciente abajo
  el._shown = true;
}

// ───────────────────────── modales ─────────────────────────

function modal(html, cls = "") {
  const dlg = document.createElement("dialog");
  dlg.className = `modal ${cls}`;
  dlg.innerHTML = html;
  document.body.appendChild(dlg);
  dlg.addEventListener("close", () => dlg.remove());
  dlg.addEventListener("click", (e) => {
    if (e.target === dlg || e.target.closest("[data-close]")) dlg.close();
  });
  dlg.showModal();
  return dlg;
}

function confirmDialog(title, text, okLabel) {
  return new Promise((resolve) => {
    const dlg = modal(`
      <form method="dialog">
        <header><h2>${esc(title)}</h2></header>
        <div class="body"><p>${esc(text)}</p></div>
        <footer>
          <button class="btn ghost" value="no">Cancelar</button>
          <button class="btn primary" value="yes" autofocus>${esc(okLabel)}</button>
        </footer>
      </form>`, "small");
    dlg.addEventListener("close", () => resolve(dlg.returnValue === "yes"));
  });
}

// ───────────────────────── vista: nuevo servicio ─────────────────────────
// #/nuevo: qué añadir. #/nuevo/<tipo> y #/s/<id>/editar: el formulario a página completa, con un resumen en vivo.

const KIND_SLUG = { programa: "process", contenedor: "container", compose: "compose" };
const CONTAINER_PRESETS = {
  kuma: { label: "Uptime Kuma", sub: "Vigila tus webs y te avisa si caen", name: "Uptime Kuma", image: "louislam/uptime-kuma:1", port: 3001, cport: 3001,
    volumes: "data:/app/data", cwd: "~/contenedores/uptime-kuma" },
  nginx: { label: "Web estática", sub: "nginx sirviendo una carpeta", name: "Web estática", image: "nginx:alpine", port: 8080, cport: 80,
    volumes: "html:/usr/share/nginx/html:ro", cwd: "~/contenedores/web" },
  minecraft: { label: "Minecraft (Paper)", sub: "Servidor de Minecraft Java", name: "Minecraft", image: "itzg/minecraft-server", port: 25565, cport: 25565,
    volumes: "data:/data", cwd: "~/contenedores/minecraft", env: { EULA: "TRUE", TYPE: "PAPER", MEMORY: "2G" }, stop_timeout: 60, health_check: "tcp" },
};

function viewNew() {
  $("#main").innerHTML = `
    <a class="back" href="#/servicios">${ICON.back}Servicios</a>
    <section class="page-head"><div><h1 class="page-title">Nuevo servicio</h1><p class="page-sub">¿Qué quieres añadir al servidor?</p></div></section>
    <div id="new-page"><div class="new-grid">
      <button type="button" class="module new-card" data-new="github">${ICON.git}<strong>Desde GitHub</strong>
        <small>Clona uno de tus repositorios, instala sus dependencias y te propone el comando y el puerto.</small></button>
      <button type="button" class="module new-card" data-new="template">${ICON.grid}<strong>Desde una plantilla</strong>
        <small>Empieza un proyecto nuevo (web, API, bot…) con los archivos de inicio ya creados y funcionando.</small></button>
      <a class="module new-card" href="#/nuevo/contenedor">${ICON.box}<strong>Contenedor</strong>
        <small>Una app ya empaquetada de Docker Hub o un proyecto con docker-compose, con Podman.</small></a>
      <a class="module new-card" href="#/nuevo/programa">${ICON.plus}<strong>Programa</strong>
        <small>Un comando de algo que ya está en el servidor: npm start, python bot.py, java -jar…</small></a>
    </div>
    <div class="section-title"><h2>Contenedores listos para usar</h2></div>
    <div class="new-presets">${Object.entries(CONTAINER_PRESETS).map(([k, p]) => `
      <button type="button" class="module preset-card" data-preset="${k}"><strong>${esc(p.label)}</strong><small>${esc(p.sub)}</small>
        <code>${esc(p.image)}</code></button>`).join("")}
    </div></div>`;
  $("#new-page").addEventListener("click", (e) => {
    const n = e.target.closest("[data-new]")?.dataset.new;
    if (n === "github") openGithub();
    if (n === "template") openTemplates();
    const p = e.target.closest("[data-preset]")?.dataset.preset;
    if (p) { ui.formPrefill = { kind: "container", ...CONTAINER_PRESETS[p] }; location.hash = "#/nuevo/contenedor"; }
  });
}

// Formulario de servicio. kind: tipo inicial al crear; id: servicio a editar.
async function viewServiceForm({ kind = "process", id = null } = {}) {
  let svc = null;
  if (id) {
    try { svc = await api("GET", `/api/services/${id}`); } catch (e) { toast(e.message, "error"); location.hash = "#/servicios"; return; }
  }
  const src = svc || ui.formPrefill || {};
  ui.formPrefill = null;
  if (!ui.services.length) ui.services = (await api("GET", "/api/services").catch(() => ({ services: [] }))).services;
  const k0 = src.kind || kind;
  const sect = (title, sub, body, attrs = "") => `<section class="module sf-sect" ${attrs}><header><h2>${title}</h2>${sub ? `<p>${sub}</p>` : ""}</header>${body}</section>`;
  $("#main").innerHTML = `
    <a class="back" href="${svc ? `#/s/${esc(svc.id)}` : "#/nuevo"}">${ICON.back}${svc ? esc(svc.name) : "Nuevo servicio"}</a>
    <section class="page-head"><div><h1 class="page-title">${svc ? "Editar servicio" : "Crear servicio"}</h1>
      <p class="page-sub">${svc ? "Los cambios se aplican al reiniciar el servicio" : "Los campos con * son obligatorios"}</p></div></section>
    <form id="svc-form" class="sf-layout" novalidate>
      <div class="sf-main">
        <div class="form-error" id="form-error"></div>
        ${sect("Tipo", "Cambia los campos de abajo", `
          <div class="kind-pick" role="radiogroup" aria-label="Tipo de servicio">
            <label><input type="radio" name="kind" value="process"><span><strong>Programa</strong><small>Un comando: npm, python, java…</small></span></label>
            <label><input type="radio" name="kind" value="container"><span><strong>Contenedor</strong><small>Una imagen de Docker Hub</small></span></label>
            <label><input type="radio" name="kind" value="compose"><span><strong>Compose</strong><small>Un docker-compose.yml</small></span></label>
          </div>`)}
        ${sect("Qué es", "", `
          <label class="field"><span>Nombre *</span><input name="name" maxlength="60" placeholder="Bot de Discord"></label>
          <label class="field"><span>Descripción</span><input name="description" maxlength="500" placeholder="Para qué sirve este servicio"></label>
          <label class="field"><span>Etiquetas</span><input name="tags" placeholder="bot, discord, producción"><small>Separadas por comas. Sirven para filtrar la lista de servicios.</small></label>`)}
        ${sect("Cómo se ejecuta", "", `
          <label class="field" data-kind="process"><span>Comando *</span><textarea name="command" rows="3" class="mono" spellcheck="false" placeholder="npm start"></textarea>
            <small>Se ejecuta con bash: puedes usar <code>&amp;&amp;</code>, variables, activar un venv, etc.</small></label>
          <div data-kind="container" class="kind-block">
            <label class="field"><span>Imagen *</span><input name="image" class="mono" spellcheck="false" autocapitalize="off" placeholder="louislam/uptime-kuma:1">
              <small>Como en Docker Hub. Se descarga sola la primera vez (puede tardar unos minutos).</small></label>
            <label class="field"><span>Carpetas</span><textarea name="volumes" rows="2" class="mono" spellcheck="false" placeholder="data:/app/data"></textarea>
              <small>Una por línea: <code>carpeta:/ruta/en/el/contenedor</code> (añade <code>:ro</code> para solo lectura). Las relativas van dentro de la carpeta de datos.</small></label>
          </div>
          <label class="field" data-kind="compose"><span>Archivo compose</span><input name="compose_file" class="mono" spellcheck="false" placeholder="compose.yaml (se busca solo)">
            <small>Vacío = busca <code>compose.yaml</code> o <code>docker-compose.yml</code> en la carpeta del proyecto.</small></label>
          <label class="field"><span id="cwd-label">Directorio de trabajo</span><input name="cwd" class="mono" spellcheck="false" placeholder="~/mi-proyecto">
            <small id="cwd-help"></small></label>
          <label class="field"><span>Variables de entorno</span><textarea name="env" rows="3" class="mono" spellcheck="false" placeholder="NODE_ENV=production&#10;TOKEN=..."></textarea>
            <small>Una por línea: CLAVE=valor. Para el .env del proyecto, usa la pestaña Variables de la ficha.</small></label>`)}
        ${sect("Red", "", `
          <div class="row2 even">
            <label class="field"><span>Puerto</span><input name="port" inputmode="numeric" placeholder="3000"><small>El del servidor.</small></label>
            <label class="field" data-kind="container"><span>Puerto del contenedor</span><input name="cport" inputmode="numeric" placeholder="igual"><small>El de la app dentro de la imagen.</small></label>
          </div>
          ${ui.publishDomain ? `<label class="field"><span>Publicar en internet</span>
            <div class="affix"><input name="subdomain" class="mono" spellcheck="false" autocapitalize="off" placeholder="mi-app"><span>.${esc(ui.publishDomain)}</span></div>
            <small>Crea el DNS en Cloudflare y la ruta del túnel hacia el puerto. Vacío = solo en la red local.</small></label>` : ""}
          <label class="field"><span>URL</span><input name="url" placeholder="https://mi-app.ejemplo.com"><small>Enlace de acceso rápido desde la ficha.${ui.publishDomain ? " Si lo publicas, se rellena sola." : ""}</small></label>`)}
        ${sect("Comportamiento", "", `
          <div class="checks">
            <label><input type="checkbox" name="autostart"><span><strong>Arrancar al encender el servidor</strong><small>Se inicia solo tras un corte de luz o un reinicio.</small></span></label>
            <label><input type="checkbox" name="restart_on_crash"><span><strong>Reiniciar si se cae</strong><small>Reintentos rápidos y, si sigue fallando, uno cada 5 minutos.</small></span></label>
          </div>
          <div class="row2">
            <label class="field"><span>Comprobación de salud</span>
              <select name="health_check">
                <option value="auto">Automática (web si tiene puerto)</option>
                <option value="http">Web (HTTP)</option>
                <option value="tcp">Solo que el puerto acepte conexiones</option>
                <option value="off">Desactivada</option>
              </select>
              <small>Cada 30 s; si falla 3 veces seguidas, se reinicia (máximo 3 veces por hora).</small></label>
            <label class="field"><span>Ruta</span><input name="health_path" class="mono" placeholder="/" spellcheck="false"></label>
          </div>
          <label class="field"><span>Límite de memoria (MB)</span><input name="memory_limit" inputmode="numeric" placeholder="sin límite">
            <small>Si usa más durante 30 s seguidos, se reinicia solo (máximo 3 veces por hora). 1024 = 1 GB.</small></label>
          <div class="row2">
            <label class="field"><span>Comando de parada</span><input name="stop_command" class="mono" placeholder="stop"><small>Se escribe en su consola antes de cerrarlo (p. ej. <code>stop</code> en Minecraft).</small></label>
            <label class="field"><span>Espera (s)</span><input name="stop_timeout" inputmode="numeric" placeholder="15"></label>
          </div>
          <div data-kind="container" class="kind-block">
            <label class="field"><span>Opciones de podman</span><input name="cargs" class="mono" spellcheck="false" placeholder="--device /dev/dri --shm-size 1g">
              <small>Se añaden tal cual a <code>podman run</code>.</small></label>
            <label class="field"><span>Comando del contenedor</span><input name="ccmd" class="mono" spellcheck="false" placeholder="(el de la imagen)"></label>
          </div>`)}
        <div class="sf-actions">
          <a class="btn ghost" href="${svc ? `#/s/${esc(svc.id)}` : "#/nuevo"}">Cancelar</a>
          <span class="grow"></span>
          <button type="submit" class="btn primary">${svc ? "Guardar cambios" : "Crear servicio"}</button>
        </div>
      </div>
      <aside class="module sf-summary" id="sf-summary" aria-live="polite"></aside>
    </form>`;

  const form = $("#svc-form"), f = form.elements;
  f.kind.value = k0;
  f.name.value = src.name || "";
  f.description.value = src.description || "";
  f.tags.value = (src.tags || []).join(", ");
  f.command.value = !src.kind || src.kind === "process" ? src.command || "" : "";
  f.image.value = src.image || "";
  f.volumes.value = src.volumes || "";
  f.compose_file.value = src.compose_file || "";
  f.cwd.value = src.cwd || "";
  f.env.value = Object.entries(src.env || {}).map(([a, b]) => `${a}=${b}`).join("\n");
  f.port.value = src.port ?? "";
  f.cport.value = src.cport ?? "";
  if (f.subdomain) f.subdomain.value = src.subdomain || "";
  f.url.value = src.url || "";
  f.autostart.checked = svc ? !!src.autostart : src.autostart ?? true;
  f.restart_on_crash.checked = svc ? !!src.restart_on_crash : src.restart_on_crash ?? true;
  f.health_check.value = src.health_check || "auto";
  f.health_path.value = src.health_path && src.health_path !== "/" ? src.health_path : "";
  f.memory_limit.value = src.memory_limit ?? "";
  f.stop_command.value = src.stop_command || "";
  f.stop_timeout.value = src.stop_timeout ?? "";
  f.cargs.value = src.cargs || "";
  f.ccmd.value = src.ccmd || "";

  const CWD = {
    process: ["Directorio de trabajo", "~/mi-proyecto", "Donde se ejecuta el comando. Vacío = tu carpeta personal."],
    container: ["Carpeta de datos *", "~/contenedores/mi-app", "Ahí quedan los datos del contenedor (y entran en las copias de seguridad). Se crea sola."],
    compose: ["Carpeta del proyecto *", "~/mi-proyecto", "La que tiene el compose.yaml."],
  };
  const sync = () => {
    const k = f.kind.value;
    form.querySelectorAll("[data-kind]").forEach((el) => { el.hidden = el.dataset.kind !== k; });
    $("#cwd-label").textContent = CWD[k][0];
    f.cwd.placeholder = CWD[k][1];
    $("#cwd-help").textContent = CWD[k][2];
    drawFormSummary(f, svc);
  };
  ui.formDirty = false;
  form.addEventListener("input", () => { ui.formDirty = true; drawFormSummary(f, svc); });
  form.addEventListener("change", (e) => { if (e.target.name === "kind") sync(); });
  sync();
  (svc ? f.name : k0 === "container" && !f.image.value ? f.image : f.name).focus();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      name: f.name.value, description: f.description.value, tags: f.tags.value,
      command: f.command.value, cwd: f.cwd.value, port: f.port.value.trim(), url: f.url.value.trim(),
      autostart: f.autostart.checked, restart_on_crash: f.restart_on_crash.checked,
      env: f.env.value, stop_command: f.stop_command.value, stop_timeout: f.stop_timeout.value.trim(),
      memory_limit: f.memory_limit.value.trim(), health_check: f.health_check.value, health_path: f.health_path.value.trim(),
      kind: f.kind.value, image: f.image.value.trim(), cport: f.cport.value.trim(), volumes: f.volumes.value,
      cargs: f.cargs.value.trim(), ccmd: f.ccmd.value.trim(), compose_file: f.compose_file.value.trim(),
    };
    if (f.subdomain) body.subdomain = f.subdomain.value.trim();
    const btn = form.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      const saved = svc ? await api("PUT", `/api/services/${svc.id}`, body) : await api("POST", "/api/services", body);
      ui.formDirty = false;
      if (svc) toast(isOn(saved) ? "Guardado. Reinicia el servicio para aplicar los cambios." : "Cambios guardados", "ok");
      else toast("Servicio creado", "ok");
      if (saved.notice) toast(saved.notice, "ok");
      location.hash = `#/s/${saved.id}`;
    } catch (err) {
      $("#form-error").textContent = err.message;
      $("#form-error").scrollIntoView({ block: "center", behavior: "smooth" });
      btn.disabled = false;
    }
  });
}

// Resumen en vivo: qué se va a ejecutar, dónde se verá y avisos antes de guardar
function drawFormSummary(f, svc) {
  const el = $("#sf-summary");
  if (!el) return;
  const k = f.kind.value, port = parseInt(f.port.value, 10) || null, name = f.name.value.trim();
  const id = svc?.id || (name ? name.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") : "servicio");
  let cmd;
  if (k === "process") cmd = f.command.value.trim() || "(escribe el comando)";
  else if (k === "container") {
    const vols = f.volumes.value.split("\n").map((v) => v.trim()).filter(Boolean).map((v) => `-v ${v}`);
    const envs = f.env.value.split("\n").map((v) => v.split("=")[0].trim()).filter((v) => v && !v.startsWith("#")).map((v) => `-e ${v}`);
    cmd = ["podman run", `--name novahub-${id}`, port ? `-p ${port}:${parseInt(f.cport.value, 10) || port}` : "", ...vols, ...envs,
      f.cargs.value.trim(), f.image.value.trim() || "(imagen)", f.ccmd.value.trim()].filter(Boolean).join(" \\\n  ");
  } else cmd = `podman-compose -p novahub-${id}${f.compose_file.value.trim() ? ` -f ${f.compose_file.value.trim()}` : ""} up`;
  const sub = f.subdomain?.value.trim().toLowerCase();
  const where = [];
  if (port && ui.lanIp) where.push(`<li><span>En casa</span><b class="mono">http://${esc(ui.lanIp)}:${port}</b></li>`);
  if (sub && ui.publishDomain) where.push(`<li><span>En internet</span><b class="mono">https://${esc(sub)}.${esc(ui.publishDomain)}</b></li>`);
  const warn = [];
  const clash = port && ui.services.find((s) => s.port === port && s.id !== svc?.id);
  if (clash) warn.push(`El puerto ${port} ya lo usa «${esc(clash.name)}»: no podrán estar encendidos a la vez.`);
  if (sub && !port) warn.push("Para publicarlo en internet hace falta un puerto.");
  if (sub && ui.services.find((s) => s.subdomain === sub && s.id !== svc?.id)) warn.push(`El subdominio «${esc(sub)}» ya lo usa otro servicio.`);
  if (k !== "process" && !f.cwd.value.trim()) warn.push(k === "container" ? "Falta la carpeta de datos." : "Falta la carpeta del proyecto.");
  if (k === "container" && !f.image.value.trim()) warn.push("Falta la imagen.");
  if (k === "process" && !f.command.value.trim()) warn.push("Falta el comando.");
  if (!name) warn.push("Falta el nombre.");
  const kindName = { process: "Programa", container: "Contenedor", compose: "Compose" }[k];
  el.innerHTML = `
    <span class="label">Resumen</span>
    <h3>${esc(name || "Sin nombre")} <span class="status svc">${kindName}</span></h3>
    <p class="sf-k">Se ejecutará</p>
    <pre class="sf-cmd">${esc(cmd)}</pre>
    ${where.length ? `<p class="sf-k">Dónde se verá</p><ul class="sf-where">${where.join("")}</ul>` : '<p class="dim-text sf-note">Sin puerto: no tendrá dirección web (bots, tareas, servidores de juego por otro protocolo…).</p>'}
    <p class="sf-k">Al arrancar el servidor</p><p class="sf-note">${f.autostart.checked ? "Se enciende solo" : "Se queda apagado hasta que lo enciendas"}${f.restart_on_crash.checked ? " · se reinicia si se cae" : ""}</p>
    ${warn.length ? `<ul class="sf-warn">${warn.map((w) => `<li>${w}</li>`).join("")}</ul>` : '<p class="nt-ok sf-ok">Todo listo para guardar</p>'}`;
}

async function leaveForm() {
  if (!ui.formDirty || !$("#svc-form")) { ui.formDirty = false; return true; }
  const ok = await confirmDialog("Cambios sin guardar", "Has cambiado el formulario y no lo has guardado. ¿Salir y perder los cambios?", "Salir sin guardar");
  if (ok) ui.formDirty = false;
  return ok;
}

// ───────────────────────── enrutado ─────────────────────────

function route() {
  if (!$("#main")) shell();
  clearView();
  const hash = location.hash;
  const m = hash.match(/^#\/s\/([a-z0-9-]+)(\/editar)?$/);
  const nm = hash.match(/^#\/nuevo(?:\/(programa|contenedor|compose))?$/);
  let section = "overview";
  const adminOnly = (m && m[2]) || nm || ["#/procesos", "#/red", "#/mejoras"].includes(hash);
  if ((adminOnly && !can("admin")) || (hash === "#/mejoras" && !ui.hasRoadmap)) { viewNoAccess(); section = ""; }
  else if (m && m[2]) { viewServiceForm({ id: m[1] }); section = "services"; }
  else if (m) { viewDetail(m[1]); section = "services"; }
  else if (nm && nm[1]) { viewServiceForm({ kind: KIND_SLUG[nm[1]] }); section = "services"; }
  else if (nm) { viewNew(); section = "services"; }
  else if (hash === "#/servicios") { viewList(); section = "services"; }
  else if (hash === "#/procesos") { viewTasks(); section = "tasks"; }
  else if (hash === "#/red") { viewNetwork(); section = "network"; }
  else if (hash.startsWith("#/ajustes")) { viewSettings(hash.split("/")[2]); section = "settings"; }
  else if (hash === "#/mejoras") { viewRoadmap(); section = "roadmap"; }
  else viewOverview();
  document.querySelectorAll("[data-nav]").forEach((a) => a.classList.toggle("active", a.dataset.nav === section));
  window.scrollTo(0, 0);
  refreshSystem();
  every(5000, refreshSystem);
}

async function start() {
  let me;
  try {
    me = await api("GET", "/api/me");
  } catch (e) {
    if (e.message === "Sin conexión con el servidor") showOffline();
    return; // si no, es un 401 y showLogin ya se ha mostrado
  }
  ui.me = me.user;
  ui.hasRoadmap = !!me.roadmap;  // página oculta de mejoras: solo administradores y solo si existe la lista
  applyPerms();
  try { ui.server = localStorage.getItem("nh-server") || "local"; } catch { ui.server = "local"; }
  if (me.lock_on_reload && !ui.unlocked) {
    // «pedir la contraseña al recargar»: se cierra la sesión que quedara de la carga anterior
    await api("POST", "/api/logout").catch(() => {});
    showLogin();
    return;
  }
  ui.locked = false;
  shell();
  await loadServers();
  route();
}

for (const ev of ["pointerdown", "keydown", "wheel", "touchstart"]) {
  document.addEventListener(ev, () => { ui.lastActivity = Date.now(); }, { passive: true, capture: true });
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") $("#term.max")?.classList.remove("max");
  // 1, 2… cambian de pestaña (salvo escribiendo o con un diálogo abierto)
  if (e.ctrlKey || e.metaKey || e.altKey || e.target.closest("input, textarea, select, dialog") || !$("#main")) return;
  const nav = NAV.find(([, , , k, , perm]) => k === e.key && (!perm || can(perm)));
  if (nav) location.hash = nav[1];
  else if (e.key === "m" && ui.hasRoadmap) location.hash = "#/mejoras";
});
let currentHash = location.hash;
window.addEventListener("hashchange", async () => {
  if (!$("#main")) return;
  if (ui.skipHash) { ui.skipHash = false; return; }
  if (!(await leaveEditor()) || !(await leaveForm())) {  // se queda donde estaba: deshace el cambio de dirección
    ui.skipHash = true;
    location.hash = currentHash;
    return;
  }
  currentHash = location.hash;
  route();
});
// Ctrl+S guarda mientras el editor está abierto, tenga el foco o no (p. ej. tras cerrar un diálogo)
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s" && ui.editing && $("#ed-input")) {
    e.preventDefault();
    if (!document.querySelector("dialog[open]")) saveFile(ui.editingId);
  }
});
window.addEventListener("beforeunload", (e) => {
  const ta = $("#ed-input");
  if ((ui.editing && ta && ta.value !== ui.editOriginal) || (ui.formDirty && $("#svc-form"))) { e.preventDefault(); e.returnValue = ""; }
});
start();
