# HU-015 — Programar un recordatorio por correo

**Estado:** Cerrada por decisión del usuario; validación con MailHog dada por aceptada sin ejecución registrada.

## Historia

Como usuario, quiero programar un recordatorio con mi propio mensaje, eligiendo los días de antelación y la hora, para que todos sepamos qué preparar y para qué comida.

[Contexto de producto](../../product/recordatorios-de-comidas/contexto.md) · [Backlog](../../product/recordatorios-de-comidas/backlog.md)

## Criterios de aceptación

- [x] Dado el panel «Asignar comida» de la planificación semanal, cuando activo «Recordatorio» debajo de «Repetir», entonces puedo elegir los días de antelación (incluido 0) y la hora, y escribir el mensaje. Si lo dejo desactivado, no se programa ningún aviso.
- [x] Dada una comida puntual con un aviso programado para una hora futura, cuando llega esa hora en Canarias, entonces todas las cuentas activas, incluida la que lo configuró, reciben un correo con el mensaje, la comida y su fecha. Con 0 días, el aviso se envía el mismo día de la comida. El formulario no muestra una etiqueta de zona horaria.
- [x] Dada una comida cuya hora de envío ya pasó, al guardar se conserva la configuración sin enviar el correo. La campana indica que el aviso venció y se puede volver a editar.

La comprobación SMTP real con MailHog no se realizó; el usuario aceptó cerrar la historia sin ella. Los envíos se intentan una vez: los fallos se registran y no se reintentan, por lo que pueden perderse correos.

## Plan propuesto

- Incorporar la configuración opcional del recordatorio al asignar una comida puntual.
- Guardar la configuración junto con la asignación y calcular su fecha y hora de envío en la zona de Canarias.
- Enviar el mensaje a las cuentas activas cuando llegue la hora prevista, sin programar envíos cuya hora ya pasó al guardar.
- Verificar con MailHog los destinatarios, el contenido y el envío el mismo día, y comprobar que no se envían avisos omitidos.

## Fuera de alcance

- Avisos recurrentes (HU-016), gestión de avisos pendientes (HU-017) e indicador en la planificación (HU-018).
