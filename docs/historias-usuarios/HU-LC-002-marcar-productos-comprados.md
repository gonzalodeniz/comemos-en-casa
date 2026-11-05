# HU-LC-002 — Marcar productos pendientes como comprados

**Estado:** completada; criterios de aceptación verificados.

Corresponde a la [historia #2 del backlog de la lista de la compra](../product/backlog-lista-de-la-compra.md).

Depende de [HU-LC-001 — Añadir productos a la lista de la compra](HU-LC-001-lista-de-la-compra.md).

## Historia de usuario

Como usuario, quiero marcar productos pendientes como comprados y verlos en una sección inferior, para distinguir lo que falta comprar.

## Criterios de aceptación

- [x] Dado un elemento pendiente, cuando lo marco como comprado, entonces desaparece de pendientes y aparece en «Comprados», debajo, conservando producto, cantidad y medida. El cambio se mantiene al recargar y es visible para otros usuarios al consultar la lista.
- [x] Dado un producto comprado, cuando vuelvo a añadirlo, entonces el registro comprado permanece intacto y aparece una entrada pendiente con la nueva cantidad.
- [x] Dadas una entrada pendiente y otra comprada del mismo producto con medida compatible, cuando marco la pendiente como comprada, entonces queda un único registro en «Comprados» con la suma de ambas cantidades. Las medidas incompatibles no se fusionan.

## Plan

- Incorporar el estado de compra a los elementos almacenados.
- Adaptar la adición para distinguir pendientes de comprados.
- Permitir marcar como comprado y fusionar cantidades compatibles.
- Mostrar pendientes arriba y comprados debajo.
- Verificar marcado, persistencia compartida, nueva adición y fusión mediante pruebas.

## Fuera de alcance

- Desmarcar productos y borrar elementos: corresponden a otras historias.
- Actualización en tiempo real entre usuarios.

## Verificación y cierre

- Pruebas backend: `tests/test_shopping_list_api.py` y `tests/test_shopping_catalog.py` — 19 pasaron.
- Pruebas de interfaz: `ShoppingList.integration.test.tsx` — 16 pasaron.
- Compilación de frontend: `npm run build` — correcta.
- Verificación manual en la interfaz: confirmada por el usuario.
