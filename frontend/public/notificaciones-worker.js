// Muestra los recordatorios que llegan incluso cuando la aplicación no está abierta.
self.addEventListener("push", (evento) => {
  const datos = evento.data.json();
  evento.waitUntil(self.registration.showNotification(datos.titulo, { body: datos.mensaje }));
});
