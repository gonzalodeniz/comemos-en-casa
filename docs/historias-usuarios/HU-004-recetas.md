# HU-004 — Recetas

**Estado (2026-10-31):** historia aprobada expresamente por el usuario; pendiente de implementación. Plan aprobado: [HU-004 — Recetas](../planes/hu-004-recetas.md). Tareas: [TASKS de HU-004](../../odd/tasks/hu-004-recetas.md).

## Historia de usuario

**Como** usuario autenticado,
**quiero** guardar y consultar recetas, y asociarlas con comidas,
**para** encontrar cómo prepararlas cuando vaya a cocinar.

## Relación con las comidas

Las comidas son las del catálogo compartido de [HU-003](HU-003-gestion-comidas.md). Una receta puede asociarse a ninguna, una o varias comidas; una comida puede tener ninguna, una o varias recetas. No se crea un catálogo de comidas independiente.

## Criterios de aceptación

### Acceso, navegación y consulta

1. El menú lateral incluye **Recetas** debajo de **Plan semanal**. Al seleccionarlo se abre el listado principal de todas las recetas sin filtro por comida.
2. El catálogo de recetas es compartido. Todos los usuarios autenticados pueden consultar, crear, editar y eliminar cualquier receta.
3. Al pulsar una comida desde cualquier lugar de la aplicación, se abre el listado principal de recetas filtrado por esa comida. Si no tiene recetas asociadas se muestra un mensaje que lo indique.
4. Al pulsar una receta se abre su página completa, que muestra su título, imagen si existe, ingredientes, elaboración y comidas asociadas.
5. Al regresar de una receta al listado se conservan la búsqueda, el filtro por comida y la posición de desplazamiento anteriores.

### Listado, filtro y búsqueda

6. El listado incluye un buscador y un desplegable para filtrar por comida. Sin texto de búsqueda, las recetas se ordenan alfabéticamente.
7. La búsqueda admite coincidencias por partes de palabras e ignora mayúsculas, minúsculas y tildes. Una receta puede aparecer aunque solo coincida alguna de las palabras buscadas.
8. Los resultados priorizan coincidencias por campo: primero título, después comidas asociadas y por último ingredientes. Una coincidencia de una palabra en el título precede a varias coincidencias exclusivamente en ingredientes. Las coincidencias adicionales ayudan a ordenar resultados con coincidencias de la misma prioridad; si siguen empatados, se ordenan alfabéticamente por título.
9. Al buscar «sopa pollo», si «Sopa casera» tiene pollo en sus ingredientes y «Sopa de pescado» no contiene pollo, se muestra primero «Sopa casera» y después «Sopa de pescado».

### Creación y edición

10. La creación y la edición se realizan en una página completa. El único campo obligatorio es el título. Ingredientes y elaboración son campos opcionales de texto libre; la imagen y las asociaciones también son opcionales.
11. No se permiten títulos duplicados, ignorando mayúsculas, minúsculas y espacios al principio y al final. Al editar se permite conservar el título de la propia receta.
12. El formulario permite seleccionar y quitar las comidas asociadas. Si se crea una receta desde un listado filtrado por comida, esta aparece asociada por defecto y puede quitarse antes de guardar.
13. Al intentar salir de la creación o edición con cambios sin guardar se solicita confirmación antes de descartarlos.

### Imágenes

14. Cada receta puede tener una imagen, con recorte cuadrado y los mismos métodos de carga que las comidas: seleccionar un archivo, arrastrar y soltar, pegar e importar desde URL. La imagen se puede sustituir o quitar.
15. Las imágenes de recetas se almacenan en `data/recetas/`. Su gestión debe respetar las validaciones y medidas de seguridad existentes para las imágenes de comidas.

### Eliminación

16. Se solicita confirmación antes de eliminar definitivamente una receta. Si se cancela, la receta y sus asociaciones se conservan.
17. Al eliminar una comida se eliminan sus asociaciones con recetas, pero las recetas y sus demás asociaciones se conservan.

## Fuera de alcance

- Ingredientes estructurados en campos de cantidad y unidad.
- Elaboración como pasos individuales ordenados.
- Más de una imagen por receta.
