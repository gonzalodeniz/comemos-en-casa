// Muestra los recordatorios que llegan incluso cuando la aplicación no está abierta.
self.addEventListener("push", (evento) => {
  const datos = evento.data.json();
  // Resuelve ambos recursos dentro del ámbito de instalación, también bajo /comemos/.
  const ambito = self.registration.scope;
  evento.waitUntil(self.registration.showNotification(datos.titulo, {
    body: datos.mensaje,
    icon: new URL("icono-192.png", ambito).href,
    badge: new URL("insignia-casa.png", ambito).href,
  }));
});
