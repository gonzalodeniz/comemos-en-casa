# HU-LC-001 — Añadir productos a la lista de la compra

**Estado:** pendiente de implementación; refinamiento aprobado.

Corresponde a la [historia #1 del backlog de la lista de la compra](../product/backlog-lista-de-la-compra.md).

## Historia de usuario

Como usuario, quiero añadir productos por categoría indicando unidades o peso y verlos en la lista de la compra, para registrar lo que necesitamos comprar.

## Criterios de aceptación

- [ ] Dado un producto del catálogo de productos dentro de una categoría, cuando lo añado indicando una cantidad en unidades, kilogramos o gramos, entonces aparece en la lista de la compra con su cantidad y medida.
- [ ] Dado un producto añadido, cuando yo u otro usuario consultamos la lista de la compra, entonces vemos ese producto con su cantidad y medida.
- [ ] Dado un producto que ya está en la lista de la compra, cuando se añade nuevamente, entonces se suman sus cantidades compatibles: unidades con unidades y pesos con pesos, convirtiendo entre kilogramos y gramos cuando corresponda. Si el mismo producto se añade en unidades y en peso, se mantienen dos registros diferentes.

## Plan

- Guardar productos con cantidad y medida.
- Acumular cantidades compatibles, manteniendo separados unidades y peso.
- Permitir añadir productos desde el catálogo de productos y consultar los totales.
- Verificar adición, acumulación, conversión de pesos y consulta por otros usuarios.

## Fuera de alcance

- Incorporación de ingredientes y ajuste de aportaciones de recetas.
- Alternancia entre vistas por categorías y por recetas.
- Marcar como comprado, desmarcar y borrar.

## Siguiente paso

El usuario invocará `/pair` manualmente para implementar esta historia refinada. No se inicia automáticamente.
