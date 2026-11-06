# HU-009 — Imágenes de productos y categorías

**Estado:** implementada y verificada.

Corresponde a la [historia #9 del backlog de la lista de la compra](../../product/lista-de-la-compra/backlog.md).

## Historia de usuario

Como usuario, quiero añadir imágenes a productos y categorías, para identificarlos visualmente.

## Criterios de aceptación

- [x] Dado que creo un producto o categoría, cuando selecciono, arrastro, pego o importo por URL una imagen, entonces puedo previsualizarla, ajustar su recorte y guardarla; añadir imagen es opcional.
- [x] Dado un producto o categoría existente, cuando añado, sustituyo o quito su imagen y guardo, entonces el cambio se conserva y es visible para todos los usuarios al consultar la lista de la compra y su catálogo.
- [x] Dado que intento incorporar una imagen no válida o cuya carga falla, cuando se produce el error, entonces veo un mensaje explicativo y la imagen guardada anteriormente se conserva.

## Plan

- Ampliar los datos y su persistencia para asociar una imagen opcional a productos y categorías.
- Reutilizar el procesamiento y las validaciones de imágenes existentes para su incorporación y gestión posterior, sin duplicar las reglas de seguridad.
- Incorporar estos controles a la creación y gestión del catálogo.
- Mostrar las imágenes en categorías y productos, manteniendo sus nombres visibles.
- Verificar creación, sustitución, eliminación, persistencia y errores.

## Restricciones técnicas

- Las imágenes de productos y categorías se almacenarán en `data/productos/`.
- La reutilización del procesamiento y las validaciones existentes es obligatoria, no una sugerencia.
- Se mantienen las opciones de incorporación y gestión de imágenes de las recetas, con el recorte ajustable del catálogo de comidas confirmado durante el refinamiento.

## Fuera de alcance

- Cambiar nombres, mover productos entre categorías o eliminar elementos del catálogo.
- Modificar la gestión de imágenes de recetas y comidas.

## Verificación

- Pruebas backend: 168 pasaron; 15 pruebas de integración se ejecutaron aparte contra PostgreSQL aislado y pasaron.
- Pruebas frontend: 145 pasaron; compilación de producción correcta.
- La comprobación visual manual en navegador queda como revisión opcional.
