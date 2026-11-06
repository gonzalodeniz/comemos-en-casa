# Especificación funcional — Catálogo de productos

**Hito:** HIT-001 — Lista de la compra.
**Estado:** implementación limitada a las operaciones disponibles de las API; el resto permanece pendiente.

Este documento recoge el comportamiento acordado durante el refinamiento. Complementa el [contexto de producto](../../product/lista-de-la-compra/contexto.md) y las historias existentes, sin cambiar su estado de implementación.

## Acceso y alcance compartido

- Añadir la opción **Catálogo de productos** al menú lateral, inmediatamente debajo de **Lista de la compra**.
- Al abrirla, mostrar las categorías de productos.
- El catálogo es único y compartido: los cambios realizados por un usuario son visibles para los demás.
- Cualquier usuario autenticado puede crear, editar y eliminar categorías y productos; estas acciones no están reservadas a administradores.

## Vista de categorías

- Usar como referencia visual el [prototipo de categorías](../../interfaces/prototipo-comemos-catalogo-categorias.png), con las diferencias indicadas en esta especificación.
- Mostrar las categorías en tarjetas, ordenadas alfabéticamente por nombre.
- Cada categoría tiene nombre e imagen opcional. Si no tiene imagen, mostrar una imagen predeterminada.
- No mostrar descripciones, buscador ni filtros; tampoco los filtros «Alimentación», «Hogar» y «Otros» del prototipo.
- Ofrecer la acción **Nueva categoría**.
- Al pulsar una categoría, abrir una pantalla con sus productos y las acciones para gestionarlos.
- El menú de tres puntos de cada categoría permite **Editar** y **Borrar**, salvo la categoría especial descrita a continuación.

## Gestión de categorías

- Crear y editar categorías permite indicar su nombre y gestionar su imagen opcional, sin descripción.
- Al solicitar el borrado de una categoría, pedir confirmación y permitir elegir entre:
  - Eliminar también los productos asociados.
  - Conservar esos productos y moverlos a **Sin categoría**.
- Eliminar productos del catálogo no elimina sus entradas en listas de la compra existentes, también cuando se eliminan junto con su categoría.

### Sin categoría

- Es una categoría especial para productos sin otra categoría asignada.
- Solo aparece cuando contiene productos.
- No se puede editar ni borrar.
- Puede elegirse como destino al cambiar la categoría de un producto o al borrar una categoría conservando sus productos.

## Vista y gestión de productos

- Dentro de una categoría se pueden crear, editar y eliminar productos.
- Cada producto tiene nombre e imagen opcional; si no tiene imagen, mostrar una imagen predeterminada.
- Al editar un producto también se puede cambiar su categoría, incluida **Sin categoría**.
- Eliminar un producto lo retira del catálogo, pero conserva sus entradas en listas de la compra existentes.
- Los cambios en productos son visibles para los demás usuarios.

## Imágenes

Reutilizar el comportamiento existente definido en [HU-009 — Imágenes de productos y categorías](HU-009-imagenes-productos-categorias.md), sin redefinir su procesamiento ni sus validaciones. La imagen es opcional tanto en categorías como en productos.

## Restricciones y verificación pendiente

- No crear nuevas llamadas a la API; reutilizar las actuales.
- Las API existentes no permiten renombrar ni borrar categorías o productos, cambiar un producto de categoría ni implementar la categoría especial. Su implementación queda pospuesta por decisión del usuario.
- El borrado físico de productos también eliminaría sus entradas de compra por la relación en cascada; preservar dichas entradas requiere adaptar la persistencia.
- En la interfaz actual se permite consultar y crear categorías y productos, y gestionar sus imágenes; no se muestran acciones que la API no admite.
- No modificar ni reabrir las historias completadas de creación de categorías y productos (HU-007 y HU-008) ni la historia de imágenes (HU-009) por documentar este alcance adicional.
- No se ha definido un orden específico, buscador o filtros para la pantalla de productos; la ausencia de buscador y filtros confirmada se refiere a la vista de categorías.

## Comprobaciones funcionales

- La nueva entrada del menú abre las tarjetas de categorías en orden alfabético, sin descripciones, buscador ni filtros.
- Crear o editar una categoría o producto conserva su nombre y su imagen opcional; los elementos sin imagen muestran la predeterminada.
- Abrir una categoría muestra sus productos y permite crearlos, editarlos, eliminarlos y cambiar su categoría.
- Borrar una categoría solicita confirmación y permite eliminar sus productos o trasladarlos a **Sin categoría**.
- **Sin categoría** aparece solo cuando contiene productos y no permite editarse ni borrarse.
- Eliminar productos del catálogo conserva sus entradas en listas de la compra existentes.
- Los cambios realizados por un usuario son visibles para los demás, y todos tienen acceso a las acciones de gestión.
