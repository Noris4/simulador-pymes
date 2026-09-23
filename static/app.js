/* Almacena el empresa_id activo en sessionStorage */
const SESSION_KEY = "empresa_id";

function getEmpresaId() {
  return sessionStorage.getItem(SESSION_KEY);
}

function setEmpresaId(id) {
  sessionStorage.setItem(SESSION_KEY, id);
}

/* Marca el link de la navbar activo según la página actual */
document.addEventListener("DOMContentLoaded", () => {
  const path = window.location.pathname;
  document.querySelectorAll("nav .steps-nav a").forEach(a => {
    if (a.getAttribute("href") === path) a.classList.add("active");
  });
});

/* Helper: fetch JSON con manejo de errores */
async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || data.detalle || "Error desconocido");
  return data;
}

/* Muestra un mensaje de alerta en el elemento dado */
function showAlert(el, mensaje, tipo = "error") {
  el.textContent = mensaje;
  el.className = `alert alert-${tipo} show`;
}

function hideAlert(el) {
  el.className = "alert";
}
