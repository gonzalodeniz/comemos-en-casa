# HU-017 — Gestionar recordatorios pendientes

## Historia

Como usuario, quiero que los avisos pendientes se actualicen al editar la comida o el recordatorio, y se cancelen al borrar la comida o desactivar el aviso, para evitar correos obsoletos.

[Contexto de producto](../../product/recordatorios-de-comidas/contexto.md) · [Backlog](../../product/recordatorios-de-comidas/backlog.md)

## Criterios de aceptación

- [ ] Dada una comida con un aviso pendiente, cuando guardo cambios en la comida o el recordatorio, entonces el aviso se actualiza según los cambios y no se envía con los datos ni en el horario anteriores si estos cambiaron.
- [ ] Dada una comida con un aviso pendiente, cuando borro la comida o desactivo el recordatorio, entonces no se envía ese correo.
- [ ] Dado un recordatorio cuyo correo ya se envió, cuando edito la comida o el recordatorio, entonces no se reenvía el aviso de esa fecha por la edición.

## Plan propuesto

- Vincular la actualización o cancelación del aviso pendiente con el cambio guardado en la planificación.
- Respetar las reglas para horarios vencidos y distinguir los avisos que ya se enviaron.
- Verificar con MailHog que no se envían correos obsoletos, cancelados o duplicados por una edición.

## Fuera de alcance

- Añadir una acción para reenviar avisos ya enviados.
