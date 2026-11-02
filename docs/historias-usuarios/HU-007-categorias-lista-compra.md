# HU-007 — Crear categorías de la lista de la compra

**Estado:** completada.

## Historia de usuario

Como usuario, quiero crear categorías desde la interfaz, para organizar el catálogo común.

## Criterios de aceptación

- [ ] Dado un usuario autenticado, cuando crea una categoría indicando su nombre, entonces la categoría aparece en el catálogo.
- [ ] Dada una categoría creada, cuando otro usuario consulta el catálogo, entonces puede verla.

## Plan

- Guardar las categorías en el catálogo compartido.
- Permitir su creación y consulta a los usuarios autenticados.
- Incorporar un formulario de creación y mostrar las categorías guardadas.
- Verificar la creación y la consulta desde otro usuario.

## Fuera de alcance

Productos, imágenes, edición y eliminación de categorías, y lista de la compra.

## Siguiente paso

El usuario invocará `/pair` manualmente para implementar esta historia refinada. No se inicia automáticamente.
