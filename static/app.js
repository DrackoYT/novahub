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
  settings: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>',
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
};
const isOn = (s) => s.status === "running" || s.status === "starting";
const statusHTML = (s) => `<span class="status">${STATUS_LABEL[s.status]}</span>`;
// Tecla de encendido: hundida y morada mientras el servicio está en marcha.
function keyHTML(s) {
  const busy = s.status === "starting" || s.status === "stopping";
  return `<button class="key${busy ? " busy" : ""}" role="switch" aria-checked="${isOn(s)}" data-act="toggle" data-id="${esc(s.id)}"
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
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch(url, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined, credentials: "same-origin" });
  } catch {
    await checkAccessSession();
    throw new Error("Sin conexión con el servidor");
  }
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && url !== "/api/login") {
    showLogin();
    throw new Error("Sesión caducada");
  }
  if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
  return data;
}

// ───────────────────────── estado global ─────────────────────────

const app = $("#app");
const ui = {
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
  if (ui.es) { ui.es.close(); ui.es = null; }
  ui.term = null;
  ui.current = null;
  ui.cards.clear();
}
function every(ms, fn) { ui.timers.push(setInterval(fn, ms)); }

// ───────────────────────── login ─────────────────────────

function showLogin() {
  clearView();
  app.innerHTML = `
    <div class="login-wrap">
      <div class="login module">
        <div class="brand">${BRAND}</div>
        <p class="sub">Panel de servicios de tu servidor</p>
        <form id="login-form">
          <div class="form-error" id="login-error"></div>
          <label class="field"><span>Contraseña</span><input id="pw" type="password" name="password" autocomplete="current-password" required autofocus></label>
          <button class="btn primary" type="submit">Entrar</button>
        </form>
      </div>
    </div>`;
  $("#login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector("button");
    btn.disabled = true;
    try {
      await api("POST", "/api/login", { password: e.target.password.value });
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
  ["tasks", "#/procesos", "Procesos", "3", ICON.activity],
];

function shell() {
  app.innerHTML = `
    <header class="topbar">
      <a class="brand" href="#/" aria-label="NovaHub · inicio">${BRAND}</a>
      <nav class="nav" aria-label="Secciones">
        ${NAV.map(([key, href, label, k, icon]) => `<a href="${href}" data-nav="${key}" title="${label} (${k})">${icon}<span>${label}</span></a>`).join("")}
      </nav>
      <div class="top-actions">
        <span class="lcd host-chip" id="host-chip"></span>
        <button class="btn primary" data-act="new">${ICON.plus}<span>Nuevo servicio</span></button>
        <button class="btn icon" data-act="settings" title="Ajustes: avisos por correo" aria-label="Ajustes">${ICON.settings}</button>
        <button class="btn icon" data-act="theme" title="Cambiar tema claro/oscuro" aria-label="Cambiar tema">${currentTheme() === "dark" ? ICON.sun : ICON.moon}</button>
        <button class="btn icon" data-act="poweroff" title="Apagar el servidor" aria-label="Apagar el servidor">${ICON.power}</button>
        <button class="btn icon ghost" data-act="logout" title="Cerrar sesión" aria-label="Cerrar sesión">${ICON.logout}</button>
      </div>
    </header>
    <main id="main"></main>`;
  $(".topbar .brand").addEventListener("dblclick", (e) => { e.preventDefault(); location.hash = "#/mejoras"; });
}

async function refreshSystem() {
  try {
    const s = await api("GET", "/api/system");
    ui.sys = s;
    ui.lanIp = s.lan_ip;
    ui.publishDomain = s.publish_domain;
    ui.user = s.user;
    ui.host = s.hostname;
    const chip = $("#host-chip");
    if (chip) chip.textContent = `${s.user}@${s.hostname}`;
    drawKpis();
    if (!ui.current && ui.services.length) { drawList(); drawOverview(); } // los enlaces «Abrir» dependen de la IP del servidor
  } catch { /* silencioso */ }
}

// ───────────────────────── vista: resumen ─────────────────────────

function viewOverview() {
  $("#main").innerHTML = `
    <section class="page-head">
      <div>
        <h1 class="page-title">Resumen</h1>
        <p class="page-sub" id="ov-sub">Estado del servidor y de tus servicios</p>
      </div>
    </section>
    <section class="kpis" id="kpis"></section>
    <div class="section-title"><h2>Servicios</h2><a href="#/servicios">Ver todos →</a></div>
    <section class="module rows" id="ov-rows"></section>`;
  drawKpis();
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
  const order = { crashed: 0, starting: 1, stopping: 1, running: 2, stopped: 3 };
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

// ───────────────────────── vista: mejoras (oculta) ─────────────────────────
// No está en las pestañas: se abre con doble clic en el logo, la tecla «m» o #/mejoras.

function viewRoadmap() {
  $("#main").innerHTML = `
    <section class="page-head">
      <div>
        <h1 class="page-title">Mejoras</h1>
        <p class="page-sub">Lista de lo que queda por hacer en NovaHub, de más a menos importante. Marca cada una al terminarla.</p>
      </div>
      <div id="rm-progress"></div>
    </section>
    <section class="module rm-list" id="rm-todo"></section>
    <form class="module rm-add" id="rm-add">
      <label class="field"><span>Apuntar una idea nueva</span>
        <input id="rm-title" maxlength="120" placeholder="p. ej. «Modo oscuro automático por horario»" autocomplete="off"></label>
      <button class="btn primary" type="submit">${ICON.plus}Añadir</button>
    </form>
    <div class="section-title" id="rm-done-title"></div>
    <section class="module rm-list done" id="rm-done"></section>`;
  const handler = async (e) => {
    const box = e.target.closest("[data-done]");
    const del = e.target.closest("[data-del]");
    try {
      if (box) ui.roadmap = (await api("PUT", `/api/roadmap/${box.dataset.done}`, { done: box.checked })).items;
      else if (del && await confirmDialog("Borrar mejora", "Se quitará de la lista.", "Borrar")) {
        ui.roadmap = (await api("DELETE", `/api/roadmap/${del.dataset.del}`)).items;
      } else return;
      drawRoadmap();
    } catch (err) { toast(err.message, "error"); }
  };
  $("#rm-todo").addEventListener("change", handler);
  $("#rm-done").addEventListener("change", handler);
  $("#rm-todo").addEventListener("click", (e) => { if (e.target.closest("[data-del]")) handler(e); });
  $("#rm-done").addEventListener("click", (e) => { if (e.target.closest("[data-del]")) handler(e); });
  $("#rm-add").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = $("#rm-title");
    try {
      ui.roadmap = (await api("POST", "/api/roadmap", { title: input.value })).items;
      input.value = "";
      drawRoadmap();
      toast("Mejora apuntada al final de la lista", "ok");
    } catch (err) { toast(err.message, "error"); }
  });
  api("GET", "/api/roadmap").then((d) => { ui.roadmap = d.items; drawRoadmap(); }).catch((e) => toast(e.message, "error"));
}

function drawRoadmap() {
  const items = ui.roadmap || [];
  const todo = items.filter((i) => !i.done);
  const done = items.filter((i) => i.done).sort((a, b) => (b.done_at || 0) - (a.done_at || 0));
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
        <button class="btn primary" data-act="new">${ICON.plus}Crear servicio</button>
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

async function updateService(id) {
  try {
    await api("POST", `/api/services/${id}/update`);
    toast("Actualizando desde GitHub: el progreso sale en la consola", "ok");
    $('[data-tab="console"]')?.click();
    refreshDetail(id);
  } catch (e) { toast(e.message, "error"); }
}

// «Nuevo servicio»: desde un repositorio de GitHub o en blanco.
function openNew() {
  const dlg = modal(`
    <form method="dialog">
      <header><h2>Nuevo servicio</h2><button type="button" class="btn ghost icon" data-close aria-label="Cerrar">${ICON.close}</button></header>
      <div class="body">
        <div class="choices">
          <button type="button" class="choice" data-choice="github">${ICON.git}<strong>Desde GitHub</strong><small>Clona uno de tus repositorios, instala sus dependencias y te propone el comando y el puerto.</small></button>
          <button type="button" class="choice" data-choice="template">${ICON.grid}<strong>Desde una plantilla</strong><small>Empieza un proyecto nuevo (web, API, bot…) con los archivos de inicio ya creados y funcionando.</small></button>
          <button type="button" class="choice" data-choice="blank">${ICON.plus}<strong>En blanco</strong><small>Rellena tú el comando y la carpeta de un programa que ya está en el servidor.</small></button>
        </div>
      </div>
    </form>`, "small");
  dlg.addEventListener("click", (e) => {
    const c = e.target.closest("[data-choice]")?.dataset.choice;
    if (!c) return;
    dlg.close();
    if (c === "github") openGithub();
    else if (c === "template") openTemplates();
    else openForm(null);
  });
}

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
        openForm(null, {
          name: pretty, description: info.description || "", tags: r.tags, command: r.command,
          cwd: r.path, port: r.port, env: r.env || {}, autostart: true, restart_on_crash: true,
        });
      };
      poll();
    } catch (err) {
      $("#gh-error", dlg).textContent = err.message;
      btn.disabled = false;
    }
  });
}

// Ajustes → avisos por correo (Gmail con contraseña de aplicación).
async function openSettings() {
  const dlg = modal(`
    <form id="nt-form" novalidate>
      <header><h2>Avisos y vigilancia</h2><button type="button" class="btn ghost icon" data-close aria-label="Cerrar">${ICON.close}</button></header>
      <div class="body" id="nt-body"><div class="pane-msg">Cargando…</div></div>
      <footer>
        <button type="button" class="btn ghost" data-close>Cancelar</button>
        <button type="button" class="btn" id="nt-test">Enviar correo de prueba</button>
        <button type="submit" class="btn primary" id="nt-save">Guardar</button>
      </footer>
    </form>`);
  const body = $("#nt-body", dlg);
  const draw = (n) => {
    const status = n.last_error ? `<p class="git-note bad">Último error: ${esc(n.last_error)}</p>`
      : n.last_sent ? `<p class="nt-ok">Último correo enviado ${fmtAgo(n.last_sent)}.</p>`
      : n.configured ? `<p class="nt-ok">Configurado. Pulsa «Enviar correo de prueba» para comprobarlo.</p>` : "";
    body.innerHTML = `
      <p>NovaHub te escribirá cuando algo vaya mal. Como mucho un correo por servicio y tipo de aviso cada 10 minutos.</p>
      ${status}
      <div class="form-error" id="nt-error"></div>
      <label class="field"><span>Tu Gmail</span><input id="nt-user" type="email" autocomplete="off" placeholder="tu.cuenta@gmail.com" value="${esc(n.user)}"></label>
      <label class="field"><span>Contraseña de aplicación</span>
        <input id="nt-pass" type="password" autocomplete="new-password" spellcheck="false" placeholder="${n.configured ? "guardada · déjala vacía para mantenerla" : "16 letras"}">
        <small>No es tu contraseña de Google: créala en <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener">myaccount.google.com/apppasswords</a>
          (hace falta tener activada la verificación en dos pasos). Se guarda en el servidor y no se vuelve a mostrar.</small></label>
      <label class="field"><span>Enviar a</span><input id="nt-to" autocomplete="off" placeholder="${esc(n.user || "el mismo Gmail")}" value="${esc(n.to)}">
        <small>Opcional. Varias direcciones separadas por comas.</small></label>
      <p class="label">Avisarme cuando…</p>
      <div class="checks">${n.events.map((e) => `
        <label><input type="checkbox" data-event="${e.key}" ${e.on ? "checked" : ""}><span><strong>${esc(e.label)}</strong></span></label>`).join("")}
      </div>
      <p class="label">Vigilante externo</p>
      <label class="field"><span>Dirección de ping (healthchecks.io)</span>
        <input id="nt-hb" class="mono" spellcheck="false" autocomplete="off" placeholder="https://hc-ping.com/…" value="${esc(n.heartbeat_url)}">
        <small>NovaHub manda una señal de vida cada minuto mientras todo funciona. Si deja de llegar (corte de luz,
          sin internet, servidor colgado), <a href="https://healthchecks.io" target="_blank" rel="noopener">healthchecks.io</a> te avisa.
          Configura allí el check con periodo de 1 minuto y 3 de gracia.</small></label>
      ${n.heartbeat_error ? `<p class="git-note bad">Señal de vida: ${esc(n.heartbeat_error)}</p>`
        : n.heartbeat_last ? `<p class="nt-ok">Última señal de vida ${fmtAgo(n.heartbeat_last)}.</p>` : ""}`;
  };
  const values = () => {
    const events = {};
    body.querySelectorAll("[data-event]").forEach((c) => { events[c.dataset.event] = c.checked; });
    return { user: $("#nt-user", dlg).value.trim(), app_password: $("#nt-pass", dlg).value, to: $("#nt-to", dlg).value.trim(), events,
      heartbeat_url: $("#nt-hb", dlg).value.trim() };
  };
  const busy = (on) => dlg.querySelectorAll("footer .btn").forEach((b) => { b.disabled = on; });
  const save = async () => {
    $("#nt-error", dlg).textContent = "";
    return api("PUT", "/api/notify", values());
  };
  $("#nt-form", dlg).addEventListener("submit", async (e) => {
    e.preventDefault();
    busy(true);
    try { await save(); dlg.close(); toast("Avisos guardados", "ok"); }
    catch (err) { $("#nt-error", dlg).textContent = err.message; busy(false); }
  });
  $("#nt-test", dlg).addEventListener("click", async () => {
    busy(true);
    try {
      draw(await save());
      draw(await api("POST", "/api/notify/test"));
      toast("Correo de prueba enviado: mira tu bandeja de entrada", "ok");
    } catch (err) {
      const el = $("#nt-error", dlg);
      if (el) el.textContent = err.message;
    }
    busy(false);
  });
  try { draw(await api("GET", "/api/notify")); }
  catch (err) { body.innerHTML = `<div class="pane-msg bad-text">${esc(err.message)}</div>`; }
}

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
  else if (act === "new") openNew();
  else if (act === "poweroff") powerOff();
  else if (act === "theme") toggleTheme();
  else if (act === "settings") openSettings();
  else if (act === "logout") {
    await api("POST", "/api/logout").catch(() => {});
    showLogin();
  }
  else if (!s) return;
  else if (act === "restart") restart(s.id);
  else if (act === "update") updateService(s.id);
  else if (act === "edit") openForm(s);
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
    <div class="d-body">
      <section class="term module" id="term">
        <div class="term-bar">
          <div class="tabs" role="tablist" aria-label="Vistas del servicio">
            <button type="button" role="tab" class="tab term-title" id="live" data-tab="console" aria-selected="true">Consola <span class="live">en directo</span></button>
            <button type="button" role="tab" class="tab" data-tab="files" aria-selected="false">${ICON.folder}Archivos</button>
            <button type="button" role="tab" class="tab" data-tab="git" aria-selected="false">${ICON.git}Git<span class="count" id="git-count" hidden></span></button>
          </div>
          <div class="term-tools" data-for="console">
            <label class="chk" title="Auto-scroll"><input type="checkbox" id="autoscroll" checked><span>Auto-scroll</span></label>
            <a class="btn sm icon" href="/api/services/${esc(id)}/logs/download" download title="Descargar log" aria-label="Descargar log">${ICON.download}</a>
            <button class="btn sm icon" data-act="clear-log" title="Limpiar consola" aria-label="Limpiar consola">${ICON.trash}</button>
            <button class="btn sm icon" data-term="max" title="Pantalla completa (Esc para salir)" aria-label="Pantalla completa">${ICON.expand}</button>
          </div>
        </div>
        <div class="screen" data-pane="console">
          <pre class="term-out" id="out"></pre>
          <form class="term-in" id="cin">
            <span class="prompt" id="prompt"></span>
            <input id="cmd" placeholder="enviar un comando al proceso…" autocomplete="off" spellcheck="false" aria-label="Comando">
            <button class="btn sm" type="submit">↵</button>
          </form>
        </div>
        <div class="pane" data-pane="files" id="files" hidden></div>
        <div class="pane" data-pane="git" id="git" hidden></div>
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
  setupInput(id);
  setupTabs(id);
}

// ───────────────────────── ficha: pestañas ─────────────────────────

function setupTabs(id) {
  const term = $("#term");
  const loaded = new Set();
  term.querySelector(".tabs").addEventListener("click", (e) => {
    const tab = e.target.closest("[data-tab]")?.dataset.tab;
    if (!tab) return;
    term.querySelectorAll("[data-tab]").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === tab)));
    term.querySelectorAll("[data-pane]").forEach((p) => { p.hidden = p.dataset.pane !== tab; });
    term.querySelector("[data-for=console]").hidden = tab !== "console";
    if (tab === "console") $("#out").scrollTop = $("#out").scrollHeight;
    if (!loaded.has(tab)) {
      loaded.add(tab);
      if (tab === "files") loadFiles(id, "");
      if (tab === "git") loadGit(id);
    }
  });
  $("#files").addEventListener("click", (e) => {
    const el = e.target.closest("[data-path]");
    if (!el) return;
    e.preventDefault();
    if (el.dataset.kind === "file") openFile(id, el.dataset.path);
    else loadFiles(id, el.dataset.path);
  });
  $("#git").addEventListener("click", (e) => {
    const act = e.target.closest("[data-git]")?.dataset.git;
    if (act) gitAction(id, act);
  });
  // el número de cambios pendientes se ve en la pestaña aunque no esté abierta
  api("GET", `/api/services/${id}/git`).then(drawGitCount).catch(() => {});
}

// ───────────────────────── ficha: archivos ─────────────────────────

const fileUrl = (id, path, action = "file") => `/api/services/${encodeURIComponent(id)}/${action}?path=${encodeURIComponent(path)}`;

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
      <div class="pane-bar">${crumbsHTML(d.root, d.path)}<span class="lcd">${d.total} elemento${d.total === 1 ? "" : "s"}</span></div>
      <div class="flist">
        ${d.path ? `<button type="button" class="frow up" data-path="${esc(parent)}" data-kind="dir"><span class="ficon">${ICON.back}</span><span class="fname">Subir un nivel</span></button>` : ""}
        ${rows || '<div class="pane-msg">Carpeta vacía.</div>'}
        ${d.total > d.entries.length ? `<div class="pane-msg">Se muestran ${d.entries.length} de ${d.total} elementos.</div>` : ""}
      </div>`;
  } catch (e) {
    pane.innerHTML = `<div class="pane-msg bad-text">${esc(e.message)}</div>`;
  }
}

async function openFile(id, path) {
  const pane = $("#files");
  pane.innerHTML = `<div class="pane-msg">Abriendo…</div>`;
  try {
    const f = await api("GET", fileUrl(id, path));
    const dir = path.includes("/") ? path.slice(0, path.lastIndexOf("/")) : "";
    let body;
    if (f.binary) {
      body = `<div class="pane-msg">Es un archivo binario (${fmtBytes(f.size)}): no se puede mostrar como texto. Puedes descargarlo.</div>`;
    } else {
      const lines = f.text.split("\n");
      if (lines.length > 1 && lines[lines.length - 1] === "") lines.pop();
      body = `<div class="code">${lines.map((l) => `<span class="ln">${esc(l) || " "}</span>`).join("")}</div>
        ${f.truncated ? `<div class="pane-msg">Se muestran los primeros ${fmtBytes(f.text.length)} de ${fmtBytes(f.size)}. Descárgalo para verlo entero.</div>` : ""}`;
    }
    pane.innerHTML = `
      <div class="pane-bar">
        <button type="button" class="btn sm" data-path="${esc(dir)}" data-kind="dir">${ICON.back}Volver</button>
        <span class="fpath mono">${esc(f.path)}</span>
        <span class="lcd">${fmtBytes(f.size)} · ${fmtAgo(f.mtime)}</span>
        <a class="btn sm icon" href="${fileUrl(id, path, "file/download")}" download title="Descargar" aria-label="Descargar">${ICON.download}</a>
      </div>
      ${body}`;
  } catch (e) {
    pane.innerHTML = `<div class="pane-msg bad-text">${esc(e.message)}</div>`;
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
    if (e.message === "Servicio no encontrado") { toast(e.message, "error"); location.hash = "#/servicios"; }
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
        ${ui.gitRepo === s.id ? `<button class="btn" data-act="update" ${s.updating ? "disabled" : ""} title="Traer cambios de GitHub, instalar dependencias y reiniciar">${ICON.download}${s.updating ? "Actualizando…" : "Actualizar"}</button>` : ""}
        <button class="btn" data-act="restart" ${s.status === "running" ? "" : "disabled"}>${ICON.restart}Reiniciar</button>
        <button class="btn" data-act="edit">${ICON.edit}Editar</button>
        <button class="btn danger" data-act="delete" ${isOn(s) || busy ? "disabled title=\"Detén el servicio para eliminarlo\"" : ""}>${ICON.trash}Eliminar</button>
        <button class="btn power ${isOn(s) ? "off" : "on"}" data-act="toggle" ${s.status === "stopping" ? "disabled" : ""}>
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
    <div class="module">
      <span class="label">Configuración</span>
      <dl class="readout">
        ${cell("Comando", `<code>${esc(s.command)}</code>`, "wide")}
        ${cell("Directorio", `<code>${esc(s.cwd || "~")}</code>`, "wide")}
        ${envKeys.length ? cell("Variables", `<code>${envKeys.map(esc).join("\n")}</code>`, "wide") : ""}
        ${cell("Autoarranque", s.autostart ? "Sí" : "No")}
        ${cell("Si falla", s.restart_on_crash ? "Reinicia" : "Se para")}
        ${cell("Parada", s.stop_command ? `<code>${esc(s.stop_command)}</code>` : "SIGTERM")}
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

  const es = new EventSource(`/api/services/${encodeURIComponent(id)}/logs/stream`);
  // al (re)conectar el servidor vuelve a mandar la cola del log: se empieza de cero
  es.onopen = () => { term.clear(); live.classList.add("on"); };
  es.onmessage = (e) => { term.write(JSON.parse(e.data)); scroll(); };
  es.addEventListener("clear", () => term.clear());
  es.onerror = () => live.classList.remove("on");
  ui.es = es;
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

function openForm(svc, prefill = null) {
  const dlg = modal(`
    <form id="svc-form" novalidate>
      <header>
        <h2>${svc ? "Editar servicio" : "Nuevo servicio"}</h2>
        <button type="button" class="btn ghost icon" data-close aria-label="Cerrar">${ICON.close}</button>
      </header>
      <div class="body">
        <div class="form-error" id="form-error"></div>
        <label class="field"><span>Nombre *</span><input name="name" maxlength="60" placeholder="Bot de Discord"></label>
        <label class="field"><span>Descripción</span><input name="description" maxlength="500" placeholder="Para qué sirve este servicio"></label>
        <label class="field"><span>Etiquetas</span><input name="tags" placeholder="bot, discord, producción"><small>Separadas por comas. Sirven para filtrar en la pantalla principal.</small></label>
        <label class="field"><span>Comando *</span><textarea name="command" rows="3" class="mono" spellcheck="false" placeholder="npm start"></textarea>
          <small>Se ejecuta con bash: puedes usar <code>&amp;&amp;</code>, variables, activar un venv, etc.</small></label>
        <div class="row2">
          <label class="field"><span>Directorio de trabajo</span><input name="cwd" class="mono" spellcheck="false" placeholder="~/mi-proyecto"></label>
          <label class="field"><span>Puerto</span><input name="port" inputmode="numeric" placeholder="3000"></label>
        </div>
        ${ui.publishDomain ? `<label class="field"><span>Publicar en internet</span>
          <div class="affix"><input name="subdomain" class="mono" spellcheck="false" autocapitalize="off" placeholder="mi-app"><span>.${esc(ui.publishDomain)}</span></div>
          <small>Crea el DNS en Cloudflare y la ruta del túnel hacia el puerto. Vacío = solo en la red local.</small></label>` : ""}
        <label class="field"><span>URL</span><input name="url" placeholder="https://mi-app.ejemplo.com"><small>Enlace de acceso rápido desde la ficha del servicio.${ui.publishDomain ? " Si publicas el servicio, se rellena sola." : ""}</small></label>
        <div class="checks">
          <label><input type="checkbox" name="autostart"><span><strong>Arrancar automáticamente</strong><small>Se inicia cuando arranca NovaHub (p. ej. tras reiniciar el servidor).</small></span></label>
          <label><input type="checkbox" name="restart_on_crash"><span><strong>Reiniciar si se cae</strong><small>Hasta 5 intentos por minuto si el proceso termina con error.</small></span></label>
        </div>
        <details class="adv">
          <summary>Opciones avanzadas</summary>
          <div class="inner">
            <label class="field"><span>Variables de entorno</span><textarea name="env" rows="3" class="mono" spellcheck="false" placeholder="NODE_ENV=production&#10;TOKEN=..."></textarea><small>Una por línea: CLAVE=valor</small></label>
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
              <small>Si el servicio usa más durante 30 s seguidos, se reinicia solo (máximo 3 veces por hora). Ejemplo: 1024 = 1 GB.</small></label>
            <div class="row2">
              <label class="field"><span>Comando de parada</span><input name="stop_command" class="mono" placeholder="stop"><small>Se escribe en la consola del proceso antes de cerrarlo (p. ej. <code>stop</code> en Minecraft).</small></label>
              <label class="field"><span>Espera (s)</span><input name="stop_timeout" inputmode="numeric" placeholder="15"></label>
            </div>
          </div>
        </details>
      </div>
      <footer>
        <button type="button" class="btn ghost" data-close>Cancelar</button>
        <button type="submit" class="btn primary">${svc ? "Guardar cambios" : "Crear servicio"}</button>
      </footer>
    </form>`);

  const form = dlg.querySelector("form");
  const f = form.elements;
  const src = svc || prefill;
  if (src) {
    f.name.value = src.name;
    f.description.value = src.description || "";
    f.tags.value = (src.tags || []).join(", ");
    f.command.value = src.command;
    f.cwd.value = src.cwd || "";
    f.port.value = src.port ?? "";
    f.url.value = src.url || "";
    if (f.subdomain) f.subdomain.value = src.subdomain || "";
    f.autostart.checked = !!src.autostart;
    f.restart_on_crash.checked = !!src.restart_on_crash;
    f.env.value = Object.entries(src.env || {}).map(([k, v]) => `${k}=${v}`).join("\n");
    f.stop_command.value = src.stop_command || "";
    f.stop_timeout.value = src.stop_timeout ?? "";
    f.memory_limit.value = src.memory_limit ?? "";
    f.health_check.value = src.health_check || "auto";
    f.health_path.value = src.health_path && src.health_path !== "/" ? src.health_path : "";
    if (f.env.value || f.stop_command.value || f.memory_limit.value || f.health_check.value !== "auto") dlg.querySelector("details").open = true;
  }
  f.name.focus();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      name: f.name.value, description: f.description.value, tags: f.tags.value,
      command: f.command.value, cwd: f.cwd.value, port: f.port.value.trim(), url: f.url.value.trim(),
      autostart: f.autostart.checked, restart_on_crash: f.restart_on_crash.checked,
      env: f.env.value, stop_command: f.stop_command.value, stop_timeout: f.stop_timeout.value.trim(),
      memory_limit: f.memory_limit.value.trim(),
      health_check: f.health_check.value, health_path: f.health_path.value.trim(),
    };
    if (f.subdomain) body.subdomain = f.subdomain.value.trim();
    const btn = form.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      const saved = svc
        ? await api("PUT", `/api/services/${svc.id}`, body)
        : await api("POST", "/api/services", body);
      dlg.close();
      if (svc) {
        toast(isOn(saved) ? "Guardado. Reinicia el servicio para aplicar los cambios." : "Cambios guardados", "ok");
        if (saved.notice) toast(saved.notice, "ok");
        refreshCurrent();
      } else {
        toast(saved.notice ? `Servicio creado. ${saved.notice}` : "Servicio creado", "ok");
        location.hash = `#/s/${saved.id}`;
      }
    } catch (err) {
      $("#form-error", dlg).textContent = err.message;
      dlg.querySelector(".body").scrollTop = 0;
      btn.disabled = false;
    }
  });
}

// ───────────────────────── enrutado ─────────────────────────

function route() {
  if (!$("#main")) shell();
  clearView();
  const hash = location.hash;
  const m = hash.match(/^#\/s\/([a-z0-9-]+)$/);
  let section = "overview";
  if (m) { viewDetail(m[1]); section = "services"; }
  else if (hash === "#/servicios") { viewList(); section = "services"; }
  else if (hash === "#/procesos") { viewTasks(); section = "tasks"; }
  else if (hash === "#/mejoras") { viewRoadmap(); section = "roadmap"; }
  else viewOverview();
  document.querySelectorAll("[data-nav]").forEach((a) => a.classList.toggle("active", a.dataset.nav === section));
  window.scrollTo(0, 0);
  refreshSystem();
  every(5000, refreshSystem);
}

async function start() {
  try {
    await api("GET", "/api/me");
  } catch { return; } // showLogin ya se ha mostrado
  shell();
  route();
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") $("#term.max")?.classList.remove("max");
  // 1, 2… cambian de pestaña (salvo escribiendo o con un diálogo abierto)
  if (e.ctrlKey || e.metaKey || e.altKey || e.target.closest("input, textarea, select, dialog") || !$("#main")) return;
  const nav = NAV.find(([, , , k]) => k === e.key);
  if (nav) location.hash = nav[1];
  else if (e.key === "m") location.hash = "#/mejoras";
});
window.addEventListener("hashchange", () => { if ($("#main")) route(); });
start();
