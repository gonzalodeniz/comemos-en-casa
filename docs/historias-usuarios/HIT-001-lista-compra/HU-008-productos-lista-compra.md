# HU-008 — Crear productos dentro de una categoría

**Estado:** completada.

## Historia de usuario

Como usuario, quiero crear productos dentro de una categoría desde la interfaz, para que todos podamos añadirlos a la compra.

## Criterios de aceptación

- [ ] Dada una categoría existente y un usuario autenticado, cuando crea un producto indicando su nombre, entonces lo ve dentro de esa categoría.
- [ ] Dado un producto creado, cuando otro usuario consulta esa categoría, entonces también puede verlo en el catálogo de productos.
- [ ] Dado un nombre vacío o compuesto solo por espacios, cuando intenta guardar, entonces se muestra una validación y no se crea el producto.

## Plan

- Incorporar productos asociados a categorías en el catálogo de categorías y productos.
- Permitir su creación y consulta a usuarios autenticados.
- Mostrar los productos y el formulario de creación dentro de cada categoría.
- Verificar creación, validación y visibilidad desde otra cuenta.

## Fuera de alcance

Añadir productos a la compra, cantidades y unidades (HU-001 de la lista de la compra); imágenes (HU-009); edición y eliminación de productos; reglas de duplicados.

## Siguiente paso

El usuario invocará `/pair` manualmente para implementar esta historia refinada. No se inicia automáticamente.

## Tareas antes del cierre

- [x] Refactorizar `backend/tests/test_meal_planning.py`.
- [x] Añadir comentarios en español al código relacionado con las historias.
- [x] Verificar manualmente la creación de productos desde la lista de la compra.
