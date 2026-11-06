# HU-005: Añadir recetas a la lista de compra

## Historia

Como usuario, quiero añadir los ingredientes de una receta a la lista de compra en una sección independiente, para gestionar su compra conservando las indicaciones originales.

## Criterios de aceptación

- [x] Dada una receta con ingredientes, cuando la añado a la compra, aparece una nueva sección con su nombre y una entrada pendiente por cada línea de ingredientes, conservando texto y orden, sin mezclarse con los productos manuales.
- [x] Dada una sección de receta, cuando marco o desmarco un ingrediente como comprado, elimino un ingrediente o elimino toda la sección, solo se modifica lo seleccionado, sin afectar a otras secciones ni a productos manuales.
- [x] Dada una receta ya añadida, cuando la añado otra vez, aparece otra sección independiente; editar o borrar la receta original no modifica ninguna de las secciones existentes.

## Plan

- Guardar cada incorporación como una copia independiente del nombre y los ingredientes.
- Permitir añadirla desde la receta.
- Mostrar las secciones de recetas diferenciadas de los productos manuales.
- Permitir cambiar el estado y eliminar ingredientes o secciones completas.
- Comprobar la independencia entre copias y respecto a la receta original.

## Fuera de alcance

- Sumar cantidades, interpretar ingredientes o vincularlos al catálogo.
- Sincronizar cambios posteriores de la receta original.
- Modificar el comportamiento de los productos añadidos manualmente.
