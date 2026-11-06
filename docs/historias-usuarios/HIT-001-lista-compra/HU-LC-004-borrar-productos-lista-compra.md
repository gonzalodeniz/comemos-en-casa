# HU-LC-004 — Borrar productos de la lista

**Estado:** completada y verificada.

Corresponde a la [historia #4 del backlog de la lista de la compra](../../product/backlog-lista-de-la-compra.md).

Depende de [HU-LC-001 — Lista de la compra](HU-LC-001-lista-de-la-compra.md).

## Historia de usuario

Como usuario, quiero borrar productos de la lista, para retirar lo que ya no necesitamos.

## Criterios de aceptación

- [x] Dada una entrada en «Pendientes» o «Comprados», cuando la borro, entonces desaparece únicamente esa entrada; las demás entradas del mismo producto conservan su estado, cantidad y medida.
- [x] Dado un producto cuya entrada he borrado, cuando consulto el catálogo, entonces sigue disponible para añadirlo nuevamente.
- [x] Dada una entrada borrada, cuando recargo la lista o la consulta otro usuario, entonces continúa ausente y las demás entradas permanecen intactas.

## Plan

- Permitir eliminar una entrada concreta de la lista compartida.
- Incorporar la acción de borrar en «Pendientes» y «Comprados».
- Actualizar la sección correspondiente tras el borrado.
- Verificar el aislamiento del borrado, la conservación del catálogo y la persistencia compartida.

## Fuera de alcance

- Borrado masivo.
- Eliminación parcial de cantidades.
- Borrado de productos o categorías del catálogo.
