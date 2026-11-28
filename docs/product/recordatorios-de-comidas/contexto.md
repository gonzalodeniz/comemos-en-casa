# Recordatorios de comidas

## Contexto

Los usuarios pueden programar avisos por correo para tener los ingredientes listos en la fecha de cada comida planificada.

## Alcance confirmado

- En la planificación semanal, el panel «Asignar comida» incluye un bloque «Recordatorio» debajo de «Repetir». Al activar el recordatorio, el usuario elige los días de antelación y la hora de envío, y escribe el mensaje.
- El aviso incluye el mensaje, la comida a la que corresponde y su fecha. Cada cuenta activa elige en su perfil si lo recibe por correo, por notificación móvil, por ambos o por ninguno. Las cuentas existentes mantienen inicialmente el correo activado.
- Con las notificaciones móviles seleccionadas, la campana del perfil permite enviar una notificación de prueba inmediata a los dispositivos registrados de esa cuenta, sin avisar a otras cuentas ni modificar los recordatorios programados.
- Los avisos móviles se solicitan de inmediato con una validez máxima de 15 minutos para que el servicio push pueda conservarlos brevemente si el dispositivo no está disponible.
- Las notificaciones push usan el icono de Comemos en casa y una insignia monocroma con forma de casa para los sistemas que muestran el icono pequeño.
- El botón «Desactivar en este dispositivo» retira solo la suscripción del navegador actual; no cambia la preferencia general de la cuenta.
- Cada comida con un recordatorio activado muestra un icono pequeño junto a «Editar». El icono es informativo, no tiene aspecto de botón y no es interactivo.

## Decisiones de producto

- Se admiten 0 días de antelación para enviar el aviso el mismo día de la comida. La hora se interpreta en `Atlantic/Canary`, sin mostrar una etiqueta de zona horaria en el formulario.
- Si al programar o cambiar el horario ya pasó la hora prevista de envío para una fecha, se omite el envío automático, no la configuración. La campana indica que el aviso venció y el editor conserva la antelación, la hora y el mensaje. Cambiar el horario por uno futuro vuelve a programar el envío de esa fecha.
- En una comida repetida se programa un aviso para cada fecha. Por ejemplo, si la comida se repite cada domingo y el aviso es un día antes a las 18:00, se envía cada sábado a las 18:00.
- Al editar la comida o el recordatorio, se actualizan los avisos pendientes que correspondan. Al borrar la comida o desactivar el recordatorio, se cancelan. Mover un aviso ya enviado a una nueva fecha u hora futura programa un nuevo envío; editar solo el texto no lo reenvía.
- La vista previa cuenta también los cambios que afectan solo al recordatorio. Si otra sesión cambia la comida o el recordatorio entre la vista previa y el guardado, se conserva el borrador y se pide revisar y confirmar antes de volver a guardar.

## Stack y pruebas

Se mantiene el stack actual: React, FastAPI y PostgreSQL. Para comprobar los envíos en desarrollo se utiliza MailHog.

La migración `0026_meal_reminder_skipped` distingue los avisos omitidos de los pendientes. Al desplegar, aplica la migración y evita que un planificador anterior procese avisos mientras la versión nueva empieza a guardarlos. Los avisos que la versión anterior descartó deben volver a configurarse en la comida correspondiente.

## Documentación relacionada

- [Backlog de recordatorios](backlog.md).
- [HU-002: Planificación de comidas](../../historias-usuarios/HU-002-planificacion-de-comidas.md).
