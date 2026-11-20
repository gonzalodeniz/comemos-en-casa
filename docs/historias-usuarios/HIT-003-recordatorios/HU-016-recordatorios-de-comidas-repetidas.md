# HU-016 — Recibir recordatorios de comidas repetidas

## Historia

Como usuario, quiero que el recordatorio se envíe antes de cada repetición de una comida, para no tener que programarlo cada semana.

[Contexto de producto](../../product/recordatorios-de-comidas/contexto.md) · [Backlog](../../product/recordatorios-de-comidas/backlog.md)

## Criterios de aceptación

- [ ] Dada una comida que se repite cada domingo con un aviso un día antes a las 18:00, cuando llega cada sábado a las 18:00 de Canarias, entonces todas las cuentas activas reciben el aviso con el mensaje y la fecha del domingo correspondiente.
- [ ] Dada una asignación repetida cuya primera hora de envío ya pasó al guardar, cuando llega la hora prevista de una de las siguientes comidas, entonces se envía el correo correspondiente sin recuperar el aviso omitido.

## Plan propuesto

- Aplicar la configuración del aviso a cada fecha generada por «Repetir».
- Calcular el envío para cada comida y reutilizar las reglas de envío de HU-015.
- Verificar con MailHog que los correos corresponden a fechas distintas y que omitir un aviso no afecta a los siguientes.

## Fuera de alcance

- Cambios y cancelaciones de avisos pendientes (HU-017).
