// Se carga en <head> antes de pintar: aplica el tema elegido con el botón (si lo hay) para evitar un destello.
try {
  const t = localStorage.getItem("nh-theme");
  if (t === "light" || t === "dark") document.documentElement.dataset.theme = t;
} catch { /* sin almacenamiento: se usa el tema del sistema */ }
