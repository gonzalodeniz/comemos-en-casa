# HU-LC-003 — Desmarcar productos comprados

**Estado:** completada; criterios de aceptación verificados.

Corresponde a la [historia #3 del backlog de la lista de la compra](../../product/lista-de-la-compra/backlog.md).

Depende de [HU-LC-002 — Marcar productos pendientes como comprados](HU-LC-002-marcar-productos-comprados.md).

## Historia de usuario

Como usuario, quiero desmarcar productos comprados y devolverlos a pendientes, para corregir marcados o volver a comprarlos.

## Criterios de aceptación

- [x] Dado un producto comprado sin entrada pendiente compatible, cuando lo desmarco, entonces desaparece de «Comprados» y aparece en «Pendientes», conservando producto, cantidad y medida.
- [x] Dado un producto comprado que también está pendiente, cuando lo desmarco, entonces las cantidades compatibles se suman en una única entrada pendiente; las medidas incompatibles permanecen separadas.
- [x] Dado un producto desmarcado, cuando recargo la lista o la consulta otro usuario, entonces se conserva el estado pendiente y la cantidad resultante.

## Plan

- Permitir devolver una entrada comprada al estado pendiente.
- Sumar cantidades cuando exista una entrada pendiente compatible.
- Incorporar la acción de desmarcar en «Comprados» y actualizar ambas secciones.
- Verificar traslado, suma de cantidades, medidas incompatibles y persistencia compartida.

## Fuera de alcance

- Desmarcar cantidades parciales.
- Borrar productos o modificar sus cantidades manualmente.
- Sincronización en tiempo real entre usuarios.
