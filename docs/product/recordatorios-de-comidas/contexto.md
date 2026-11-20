# Recordatorios de comidas

## Contexto

Los usuarios pueden programar avisos por correo para tener los ingredientes listos en la fecha de cada comida planificada.

## Alcance confirmado

- En la planificación semanal, el panel «Asignar comida» incluye un bloque «Recordatorio» debajo de «Repetir». Al activar el recordatorio, el usuario elige los días de antelación y la hora de envío, y escribe el mensaje.
- El correo incluye el mensaje, la comida a la que corresponde y su fecha. Lo reciben todas las cuentas activas, incluida la que configuró el recordatorio.
- Cada comida con un recordatorio activado muestra un icono pequeño junto a «Editar». El icono es informativo, no tiene aspecto de botón y no es interactivo.

## Decisiones de producto

- Se admiten 0 días de antelación para enviar el aviso el mismo día de la comida. La hora se interpreta en `Atlantic/Canary`, sin mostrar una etiqueta de zona horaria en el formulario.
- Si al guardar ya pasó la hora prevista de envío para una fecha, se omite el correo sin notificarlo en la interfaz.
- En una comida repetida se programa un aviso para cada fecha. Por ejemplo, si la comida se repite cada domingo y el aviso es un día antes a las 18:00, se envía cada sábado a las 18:00.
- Al editar la comida o el recordatorio, se actualizan los avisos pendientes que correspondan. Al borrar la comida o desactivar el recordatorio, se cancelan. Los correos ya enviados no se reenvían por una edición.

## Stack y pruebas

Se mantiene el stack actual: React, FastAPI y PostgreSQL. Para comprobar los envíos en desarrollo se utiliza MailHog.

## Documentación relacionada

- [Backlog de recordatorios](backlog.md).
- [HU-002: Planificación de comidas](../../historias-usuarios/HU-002-planificacion-de-comidas.md).
