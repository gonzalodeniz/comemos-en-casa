# HU-003 — Gestión de comidas

## Historia de usuario

**Como** usuario autenticado,  
**quiero** añadir, editar y eliminar comidas de un catálogo compartido mediante una interfaz visual clara y amigable,  
**para** reutilizarlas en la planificación.

## Relación con la planificación existente

Las «comidas» de esta historia son las mismas **etiquetas alimentarias** utilizadas en [HU-002 — Planificación de comidas](HU-002-planificacion-de-comidas.md). Esta historia amplía su catálogo existente con gestión de nombre e imagen; no crea un catálogo independiente. Las comidas del catálogo pueden seleccionarse desde la planificación.

## Criterios de aceptación

### Catálogo y navegación

1. El menú lateral incluye **Comidas**, debajo de **Plan semanal**, y abre el catálogo en la ventana principal.
2. La gestión del catálogo requiere autenticación. El catálogo es compartido: todos los usuarios autenticados pueden crear, editar y eliminar cualquier comida.
3. Las comidas se muestran en una cuadrícula de tarjetas con su nombre e imagen, tomando como referencia visual el selector del editor de comidas existente.
4. El catálogo permite buscar comidas por nombre.
5. Cada tarjeta muestra un icono de lápiz para editar, una papelera para eliminar y un ojo para visualizar recetas. El ojo permanece deshabilitado mientras la funcionalidad de recetas esté fuera del alcance.

### Crear y editar

6. Una comida tiene únicamente nombre e imagen. El nombre es obligatorio, se guarda sin espacios al principio ni al final y admite un máximo de 100 caracteres. No se permite guardar un nombre vacío o compuesto únicamente por espacios. La imagen es opcional; si no se proporciona, se muestra la imagen actual de cubiertos.
7. El usuario puede añadir una imagen arrastrándola desde su dispositivo, seleccionando un fichero, mediante una URL o pegándola desde el portapapeles.
8. Antes de guardar la imagen, el usuario puede elegir y ajustar un recorte cuadrado.
9. No se permite crear una comida ni renombrarla con un nombre que ya pertenezca a otra comida; se muestra un mensaje indicando que la comida ya existe. Los nombres que solo difieren en mayúsculas o espacios al principio o al final se consideran duplicados. Conservar el nombre de la propia comida al editarla no se considera un duplicado.
10. Al editar el nombre o la imagen de una comida, los cambios se reflejan también en las asignaciones existentes de la planificación.

### Eliminar

11. Siempre se solicita confirmación antes de eliminar una comida.
12. El aviso muestra un icono de calendario junto al número de asignaciones de la comida en la planificación y un icono de plato junto al número de recetas asociadas. Se cuentan asignaciones, no días distintos: una comida asignada al almuerzo y a la cena de un mismo día cuenta como dos asignaciones. El recuento incluye fechas pasadas y futuras. Mientras las recetas estén fuera del alcance, su recuento se mostrará como cero.
13. Si el usuario confirma, se elimina la comida del catálogo y se eliminan todas sus asignaciones de la planificación, tanto pasadas como futuras. Si cancela, no se elimina la comida ni sus asignaciones.
14. Los recuentos del aviso corresponden al momento en que se abre. No se requiere actualizarlos ni solicitar una nueva confirmación si otro usuario cambia las asignaciones mientras el aviso está abierto.

### Validación y edición de imágenes

15. Se admiten imágenes estáticas JPG, PNG y WebP de hasta 2 MiB y 5 megapíxeles, independientemente de la forma utilizada para añadirlas. Se aplica la orientación EXIF y se eliminan los metadatos. La imagen guardada se genera en WebP de 512 × 512 píxeles, calidad 85, conservando transparencia. Si formato, tamaño o dimensiones no son válidos, se muestra un error y no se acepta la nueva imagen.
16. El usuario puede quitar la imagen de una comida existente para volver a mostrar los cubiertos predeterminados.
17. Si falla la carga de una imagen, se muestra un error, pero se permite guardar el nombre sin imagen, utilizando los cubiertos predeterminados.
18. Si se está editando una comida que ya tiene imagen y falla la carga de una nueva, se conserva la imagen anterior y se permite guardar el nombre sin sustituirla.

## Fuera de alcance

La creación, gestión y visualización de recetas asociadas a las comidas.
