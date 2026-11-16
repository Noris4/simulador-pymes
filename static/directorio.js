document.getElementById('form-oportunidades')?.addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const mensaje = document.getElementById('mensaje-oportunidades');
  const boton = evento.target.querySelector('button[type="submit"]');
  boton.disabled = true;
  mensaje.textContent = 'Guardando…';
  try {
    await apiFetch('/empresa/activa/oportunidades', {
      method: 'PUT',
      body: JSON.stringify({
        descripcion: document.getElementById('descripcion-directorio').value,
        financiamiento: document.getElementById('busca-financiamiento').checked,
        inversion: document.getElementById('busca-inversion').checked,
        empleados: document.getElementById('busca-empleados').checked,
      }),
    });
    window.location.assign('/directorio-page?guardado=1');
  } catch (error) {
    mensaje.textContent = error.message;
    boton.disabled = false;
  }
});
if (document.getElementById('mensaje-oportunidades') && new URLSearchParams(window.location.search).has('guardado')) {
  document.getElementById('mensaje-oportunidades').textContent = 'Tu tarjeta se actualizó. Puedes encontrarla en el directorio.';
}
