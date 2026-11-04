# HU-LC-002 — Marcar productos pendientes como comprados

**Estado:** refinamiento aprobado; pendiente de implementación.

Corresponde a la [historia #2 del backlog de la lista de la compra](../product/backlog-lista-de-la-compra.md).

Depende de [HU-LC-001 — Añadir productos a la lista de la compra](HU-LC-001-lista-de-la-compra.md).

## Historia de usuario

Como usuario, quiero marcar productos pendientes como comprados y verlos en una sección inferior, para distinguir lo que falta comprar.

## Criterios de aceptación

- [ ] Dado un elemento pendiente, cuando lo marco como comprado, entonces desaparece de pendientes y aparece en «Comprados», debajo, conservando producto, cantidad y medida. El cambio se mantiene al recargar y es visible para otros usuarios al consultar la lista.
- [ ] Dado un producto comprado, cuando vuelvo a añadirlo, entonces el registro comprado permanece intacto y aparece una entrada pendiente con la nueva cantidad.
- [ ] Dadas una entrada pendiente y otra comprada del mismo producto con medida compatible, cuando marco la pendiente como comprada, entonces queda un único registro en «Comprados» con la suma de ambas cantidades. Las medidas incompatibles no se fusionan.

## Plan

- Incorporar el estado de compra a los elementos almacenados.
- Adaptar la adición para distinguir pendientes de comprados.
- Permitir marcar como comprado y fusionar cantidades compatibles.
- Mostrar pendientes arriba y comprados debajo.
- Verificar marcado, persistencia compartida, nueva adición y fusión mediante pruebas.

## Fuera de alcance

- Desmarcar productos y borrar elementos: corresponden a otras historias.
- Actualización en tiempo real entre usuarios.

## Siguiente paso

Implementar esta historia mediante `/pair`, sin ampliar el alcance aprobado.
