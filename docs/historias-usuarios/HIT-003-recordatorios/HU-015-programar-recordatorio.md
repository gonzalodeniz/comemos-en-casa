# HU-015 — Programar un recordatorio por correo

## Historia

Como usuario, quiero programar un recordatorio con mi propio mensaje, eligiendo los días de antelación y la hora, para que todos sepamos qué preparar y para qué comida.

[Contexto de producto](../../product/recordatorios-de-comidas/contexto.md) · [Backlog](../../product/recordatorios-de-comidas/backlog.md)

## Criterios de aceptación

- [ ] Dado el panel «Asignar comida» de la planificación semanal, cuando activo «Recordatorio» debajo de «Repetir», entonces puedo elegir los días de antelación (incluido 0) y la hora, y escribir el mensaje. Si lo dejo desactivado, no se programa ningún aviso.
- [ ] Dada una comida puntual con un aviso programado para una hora futura, cuando llega esa hora en Canarias, entonces todas las cuentas activas, incluida la que lo configuró, reciben un correo con el mensaje, la comida y su fecha. Con 0 días, el aviso se envía el mismo día de la comida. El formulario no muestra una etiqueta de zona horaria.
- [ ] Dada una comida cuya hora de envío ya pasó, cuando guardo el recordatorio, entonces no se envía el correo ni se muestra un aviso sobre la omisión.

## Plan propuesto

- Incorporar la configuración opcional del recordatorio al asignar una comida puntual.
- Guardar la configuración junto con la asignación y calcular su fecha y hora de envío en la zona de Canarias.
- Enviar el mensaje a las cuentas activas cuando llegue la hora prevista, sin programar envíos cuya hora ya pasó al guardar.
- Verificar con MailHog los destinatarios, el contenido y el envío el mismo día, y comprobar que no se envían avisos omitidos.

## Fuera de alcance

- Avisos recurrentes (HU-016), gestión de avisos pendientes (HU-017) e indicador en la planificación (HU-018).
