"use strict";

// ───────────────────────── utilidades ─────────────────────────

const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const BRAND = `<span class="wordmark">NOVA<b>HUB</b></span>`;
// Rótulo de arranque del login (fuente «ANSI Shadow»).
const BANNER = `███╗   ██╗ ██████╗ ██╗   ██╗ █████╗ ██╗  ██╗██╗   ██╗██████╗
████╗  ██║██╔═══██╗██║   ██║██╔══██╗██║  ██║██║   ██║██╔══██╗
██╔██╗ ██║██║   ██║██║   ██║███████║███████║██║   ██║██████╔╝
██║╚██╗██║██║   ██║╚██╗ ██╔╝██╔══██║██╔══██║██║   ██║██╔══██╗
██║ ╚████║╚██████╔╝ ╚████╔╝ ██║  ██║██║  ██║╚██████╔╝██████╔╝
╚═╝  ╚═══╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝`;

const STATUS_LABEL = {
  running: "En marcha",
  stopped: "Detenido",
  starting: "Iniciando…",
  stopping: "Deteniendo…",
  crashed: "Error",
};
const isOn = (s) => s.status === "running" || s.status === "starting";
const STATUS_SHORT = { running: "ON ", stopped: "OFF", starting: "...", stopping: "...", crashed: "ERR" };
const statusHTML = (s) => {
  const busy = s.status === "starting" || s.status === "stopping";
  return `<span class="status${busy ? " busy" : ""}" title="${STATUS_LABEL[s.status]}">${STATUS_SHORT[s.status]}</span>`;
};
function switchHTML(s) {
  const busy = s.status === "starting" || s.status === "stopping";
  return `<button class="switch${busy ? " busy" : ""}" role="switch" aria-checked="${isOn(s)}" data-act="toggle" data-id="${esc(s.id)}"
    title="${isOn(s) ? "Apagar" : "Encender"}" aria-label="${isOn(s) ? "Apagar" : "Encender"} ${esc(s.name)}"><span class="on">ON</span><span class="off">OFF</span></button>`;
}
const pct = (a, b) => (b ? (a / b) * 100 : 0);
// barra de texto: [██████░░░░░░░░]; ámbar desde el 75 %, rojo desde el 90 %
function tbarHTML(p, cells = 20) {
  const n = Math.round((Math.min(100, Math.max(0, p)) / 100) * cells);
  const cls = p >= 90 ? " crit" : p >= 75 ? " hot" : "";
  return `<span class="tbar${cls}">[<span class="f">${"█".repeat(n)}</span><span class="e">${"░".repeat(cells - n)}</span>]</span>`;
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

async function api(method, url, body) {
  const headers = { "X-NovaHub": "1" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const res = await fetch(url, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined, credentials: "same-origin" });
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
      <div class="login">
        <pre class="banner" aria-label="NovaHub">${BANNER}</pre>
        <pre class="boot">novahub v2 · panel de servicios
cargando módulos ........... <span class="ok">OK</span>
enlace seguro .............. <span class="ok">OK</span>
acceso restringido: identifícate</pre>
        <form id="login-form">
          <div class="form-error" id="login-error"></div>
          <div class="prompt-line"><label for="pw">password:</label><input id="pw" type="password" name="password" autocomplete="current-password" required autofocus></div>
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
  ["overview", "#/", "Resumen", "1"],
  ["services", "#/servicios", "Servicios", "2"],
];

function shell() {
  app.innerHTML = `
    <header class="topbar">
      <a class="brand" href="#/" aria-label="NovaHub · inicio">${BRAND}</a>
      <nav class="nav" aria-label="Secciones">
        ${NAV.map(([key, href, label, k]) => `<a href="${href}" data-nav="${key}"><span class="key">${k}</span>${label}</a>`).join("")}
      </nav>
      <div class="top-actions">
        <span class="host-chip" id="host-chip"></span>
        <span class="clock num" id="clock"></span>
        <button class="btn primary" data-act="new"><span>Nuevo servicio</span></button>
        <button class="btn" data-act="poweroff" title="Apagar el servidor">Apagar</button>
        <button class="btn" data-act="logout" title="Cerrar sesión">Salir</button>
      </div>
    </header>
    <main id="main"></main>`;
  const tick = () => { const c = $("#clock"); if (c) c.textContent = new Date().toLocaleTimeString("es-ES"); };
  tick();
  clearInterval(ui.clock);
  ui.clock = setInterval(tick, 1000);
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
    if (chip) chip.innerHTML = `<span>${esc(s.user)}@<b>${esc(s.hostname)}</b></span>`;
    drawKpis();
    if (!ui.current && ui.services.length) { drawList(); drawOverview(); } // los enlaces «Abrir» dependen de la IP del servidor
  } catch { /* silencioso */ }
}

// ───────────────────────── vista: resumen ─────────────────────────

function viewOverview() {
  $("#main").innerHTML = `
    <section class="page-head">
      <div>
        <h1 class="page-title cursor">Resumen</h1>
        <p class="page-sub" id="ov-sub">estado del servidor y de tus servicios</p>
      </div>
    </section>
    <section class="box" id="kpis"><span class="box-title">sistema</span></section>
    <div class="section-title"><h2></h2><a href="#/servicios">ver todos →</a></div>
    <section class="box flush"><span class="box-title">servicios</span><div class="rows" id="ov-rows"></div></section>`;
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

function drawKpis() {
  const el = $("#kpis"), s = ui.sys;
  if (!el || !s) return;
  const cpu = pct(s.load[0], s.cpus), mem = pct(s.mem_used, s.mem_total), disk = pct(s.disk_used, s.disk_total);
  const line = (k, p, v, sub) => `<span class="k">${k}</span>${p != null ? tbarHTML(p) : "<span></span>"}<span class="v num">${v}</span><span class="s">${sub}</span>`;
  const html = `<span class="box-title">sistema · <b>${esc(s.hostname)}</b></span>
    <div class="meters">
      ${line("cpu", cpu, `${cpu.toFixed(0)}%`, `carga ${s.load[0].toFixed(2)} / ${s.cpus} núcleos`)}
      ${line("ram", mem, fmtBytes(s.mem_used), `de ${fmtBytes(s.mem_total)}`)}
      ${line("disco", disk, `${disk.toFixed(0)}%`, `${fmtBytes(s.disk_used)} de ${fmtBytes(s.disk_total)}`)}
      ${line("uptime", null, fmtDuration(s.uptime), `${esc(s.user)}@${esc(s.hostname)}`)}
    </div>`;
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
    ? `<span class="hi">${running}/${all.length}</span> servicios en marcha${crashed ? ` · <span class="bad-text">${crashed} con error</span>` : ""}`
    : "aún no hay servicios";
  // primero los que tienen error, luego los encendidos
  const order = { crashed: 0, starting: 1, stopping: 1, running: 2, stopped: 3 };
  const list = [...all].sort((a, b) => order[a.status] - order[b.status]);
  const html = list.length ? list.map((s) => {
    const url = s.status === "running" ? openUrl(s) : null;
    return `<a class="row" href="#/s/${esc(s.id)}" data-status="${s.status}">
      <span class="row-name">${esc(s.name)}</span>
      <span class="row-fill"></span>
      <span class="row-meta">
        ${s.subdomain && url ? `<span class="opt amber">${esc(url.replace(/^https?:\/\//, ""))}</span>` : ""}
        ${s.status === "running" ? `<span class="num">${fmtDuration(s.uptime)}</span>` : ""}
      </span>
      ${statusHTML(s)}
    </a>`;
  }).join("") : `<div class="row-empty">-- vacío -- crea tu primer servicio con [nuevo servicio]</div>`;
  if (el._html !== html) { el.innerHTML = html; el._html = html; }
}

// ───────────────────────── vista: lista ─────────────────────────

function viewList() {
  $("#main").innerHTML = `
    <section class="page-head">
      <div>
        <h1 class="page-title cursor">Servicios</h1>
        <p class="page-sub">enciende, apaga y vigila cada proceso</p>
      </div>
      <div id="summary"></div>
    </section>
    <section class="toolbar">
      <label class="search"><input id="q" type="search" placeholder="buscar" aria-label="Buscar"></label>
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
  } catch (e) { /* el 401 ya redirige */ }
}

function cardHTML(s, index) {
  const foot = [];
  if (s.status === "running") foot.push(`<span><span class="k">Activo</span><span class="v">${fmtDuration(s.uptime)}</span></span>`);
  else if (s.status === "crashed" && s.last_exit != null) foot.push(`<span><span class="k">Salida</span><span class="v bad-text">${s.last_exit}</span></span>`);
  if (s.status === "running" && s.memory != null) foot.push(`<span><span class="k">RAM</span><span class="v">${fmtBytes(s.memory)}</span></span>`);
  if (s.port) {
    foot.push(`<span title="${s.listening ? "El puerto está escuchando" : "El puerto no está escuchando"}"><span class="k">Puerto</span>` +
      `<span class="v ${s.listening ? "ok-text" : "dim-text"}">${s.port}</span></span>`);
  }
  if (!foot.length) foot.push(`<span class="faint">-- detenido --</span>`);
  const url = s.status === "running" ? openUrl(s) : null;
  const link = url
    ? `<a class="card-link" href="${esc(url)}" target="_blank" rel="noopener">${esc(url.replace(/^https?:\/\//, ""))}</a>`
    : "";
  return `
    <span class="box-title">${String(index + 1).padStart(2, "0")} · <b>${esc(s.id)}</b></span>
    <div class="card-top">
      ${statusHTML(s)}
      <h3 class="card-name">${esc(s.name)}</h3>
      ${switchHTML(s)}
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
      tags.map((t) => `<button class="chip tagchip${ui.tag === t ? " active" : ""}" data-tag="${esc(t)}">${esc(t)}</button>`).join("")
    : "";
  const filters = $("#filters");
  if (filters._html !== filtersHTML) { filters.innerHTML = filtersHTML; filters._html = filtersHTML; }

  const running = all.filter((s) => s.status === "running").length;
  $("#summary").innerHTML = all.length ? `<span class="pill"><b>${running}/${all.length}</b> en marcha</span>` : "";

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
        <p>añade tu primer servicio: un bot, una web, un servidor de juegos…</p>
        <button class="btn primary" data-act="new">Crear servicio</button>
      </div>`);
    return;
  }

  const visible = new Set(list.map((s) => s.id));
  for (const [id, el] of ui.cards) if (!visible.has(id)) el.remove();

  for (const s of list) {
    let el = ui.cards.get(s.id);
    if (!el) {
      el = document.createElement("article");
      el.className = "card box";
      el.tabIndex = 0;
      el.dataset.id = s.id;
      ui.cards.set(s.id, el);
    }
    const html = cardHTML(s, all.indexOf(s));
    if (el._html !== html) { el.innerHTML = html; el._html = html; }
    el.dataset.status = s.status;
    grid.appendChild(el); // mantiene el orden
  }
  if (!list.length) grid.insertAdjacentHTML("beforeend", `<div class="empty"><p>-- ningún servicio coincide con el filtro --</p></div>`);
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
  else if (act === "new") openForm(null);
  else if (act === "poweroff") powerOff();
  else if (act === "logout") {
    await api("POST", "/api/logout").catch(() => {});
    showLogin();
  }
  else if (!s) return;
  else if (act === "restart") restart(s.id);
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
    <a class="back" href="#/servicios">Servicios</a>
    <div id="d-head"></div>
    <section class="d-kpis" id="d-kpis"></section>
    <div class="d-body">
      <section class="term box" id="term">
        <div class="term-bar">
          <span class="term-title" id="live">consola <span class="live">en directo</span></span>
          <div class="term-tools">
            <label class="chk" title="Auto-scroll"><input type="checkbox" id="autoscroll" checked><span>auto-scroll</span></label>
            <a class="btn sm" href="/api/services/${esc(id)}/logs/download" download title="Descargar log">Log</a>
            <button class="btn sm" data-act="clear-log" title="Limpiar consola">Limpiar</button>
            <button class="btn sm" data-term="max" title="Pantalla completa (Esc para salir)">Max</button>
          </div>
        </div>
        <pre class="term-out" id="out"></pre>
        <form class="term-in" id="cin">
          <span class="prompt" id="prompt"></span>
          <input id="cmd" placeholder="enviar un comando al proceso…" autocomplete="off" spellcheck="false" aria-label="Comando">
          <button class="btn sm" type="submit">↵</button>
        </form>
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
        <div class="d-status">${statusHTML(s)}<span class="sid">#${esc(s.id)}</span></div>
        <h1 class="cursor">${esc(s.name)}</h1>
        ${s.description ? `<p class="d-desc">${esc(s.description)}</p>` : ""}
        ${tagsHTML(s.tags)}
      </div>
      <div class="d-actions">
        ${url ? `<a class="btn" href="${esc(url)}" target="_blank" rel="noopener">Abrir ↗</a>` : ""}
        <button class="btn" data-act="restart" ${s.status === "running" ? "" : "disabled"}>Reiniciar</button>
        <button class="btn" data-act="edit">Editar</button>
        <button class="btn danger" data-act="delete" ${isOn(s) || busy ? "disabled title=\"Detén el servicio para eliminarlo\"" : ""}>Eliminar</button>
        <button class="btn power ${isOn(s) ? "off" : "on"}" data-act="toggle" ${s.status === "stopping" ? "disabled" : ""}>
          ${isOn(s) ? "Apagar" : "Encender"}</button>
      </div>
    </div>`;
  const headEl = $("#d-head");
  if (headEl && headEl._html !== head) { headEl.innerHTML = head; headEl._html = head; }

  const cell = (k, v, cls = "") => `<div class="${cls}"><dt>${k}</dt><dd>${v}</dd></div>`;
  const dash = '<span class="dim-text">—</span>';
  const on = s.status === "running";
  const kpi = (k, v, sub) => `<span class="d-kpi"><span class="k">${k}</span><span class="v num">${v}</span><span class="s">${sub}</span></span>`;
  const kpis =
    kpi("up", on ? fmtDuration(s.uptime) : "--", on ? `desde ${fmtTime(s.started_at)}` : STATUS_LABEL[s.status].toLowerCase()) +
    kpi("cpu", s.cpu != null ? `${s.cpu.toFixed(1)}%` : "--", s.processes ? `${s.processes} proc` : "") +
    kpi("mem", s.memory != null ? fmtBytes(s.memory) : "--", s.pid ? `pid ${s.pid}` : "") +
    kpi("port", s.port ?? "--", s.port ? (s.listening ? '<span class="ok-text">escuchando</span>' : "no escucha") : "");
  const kpiEl = $("#d-kpis");
  if (kpiEl && kpiEl._html !== kpis) { kpiEl.innerHTML = kpis; kpiEl._html = kpis; }

  const envKeys = Object.keys(s.env || {});
  const info = `
    <div class="box">
      <span class="box-title">estado</span>
      <dl class="readout">
        ${s.url ? cell("URL", `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url.replace(/^https?:\/\//, ""))}</a>`) : ""}
        ${cell("Última salida", s.last_exit_at ? `${s.last_exit ?? "?"} <span class="dim-text">· ${fmtTime(s.last_exit_at)}</span>` : dash)}
        ${cell("Reinicios auto · 1 h", s.auto_restarts)}
      </dl>
    </div>
    <div class="box">
      <span class="box-title">configuración</span>
      <dl class="readout">
        ${cell("Comando", `<code>${esc(s.command)}</code>`, "wide")}
        ${cell("Directorio", `<code>${esc(s.cwd || "~")}</code>`, "wide")}
        ${envKeys.length ? cell("Variables", `<code>${envKeys.map(esc).join("\n")}</code>`, "wide") : ""}
        ${cell("Autoarranque", s.autostart ? "Sí" : "No")}
        ${cell("Si falla", s.restart_on_crash ? "Reinicia" : "Se para")}
        ${cell("Parada", s.stop_command ? `<code>${esc(s.stop_command)}</code>` : "SIGTERM")}
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

function openForm(svc) {
  const dlg = modal(`
    <form id="svc-form" novalidate>
      <header>
        <h2>${svc ? "Editar servicio" : "Nuevo servicio"}</h2>
        <button type="button" class="btn ghost icon" data-close aria-label="Cerrar"></button>
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
  if (svc) {
    f.name.value = svc.name;
    f.description.value = svc.description || "";
    f.tags.value = (svc.tags || []).join(", ");
    f.command.value = svc.command;
    f.cwd.value = svc.cwd || "";
    f.port.value = svc.port ?? "";
    f.url.value = svc.url || "";
    if (f.subdomain) f.subdomain.value = svc.subdomain || "";
    f.autostart.checked = !!svc.autostart;
    f.restart_on_crash.checked = !!svc.restart_on_crash;
    f.env.value = Object.entries(svc.env || {}).map(([k, v]) => `${k}=${v}`).join("\n");
    f.stop_command.value = svc.stop_command || "";
    f.stop_timeout.value = svc.stop_timeout ?? "";
    if (f.env.value || f.stop_command.value) dlg.querySelector("details").open = true;
  }
  f.name.focus();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      name: f.name.value, description: f.description.value, tags: f.tags.value,
      command: f.command.value, cwd: f.cwd.value, port: f.port.value.trim(), url: f.url.value.trim(),
      autostart: f.autostart.checked, restart_on_crash: f.restart_on_crash.checked,
      env: f.env.value, stop_command: f.stop_command.value, stop_timeout: f.stop_timeout.value.trim(),
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
});
window.addEventListener("hashchange", () => { if ($("#main")) route(); });
start();
