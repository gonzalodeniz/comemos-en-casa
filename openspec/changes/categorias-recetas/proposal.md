# Propuesta: categorías globales para recetas

## Intento

Permitir que cualquier persona consulte, cree y mantenga recetas públicas clasificadas mediante etiquetas globales. Las etiquetas deben facilitar el descubrimiento desde un único catálogo público `Recetas`, sin introducir cuentas privadas, estados editoriales ni un sistema independiente de administración de etiquetas.

## Alcance

### Comportamiento de producto

- Las etiquetas son globales y se crean implícitamente al guardar una receta; no habrá una pantalla separada para administrarlas.
- Una receta admite de cero a diez etiquetas. Los valores vacíos se ignoran y los valores normalizados repetidos se deduplican antes de aplicar el máximo de diez.
- La normalización convierte a minúsculas conservando los acentos, recorta los extremos y convierte cualquier secuencia de espacios en un único espacio interno. Se permiten espacios internos.
- Una etiqueta normalizada no supera 25 caracteres. Se permiten letras, números, espacios internos y caracteres especiales; se rechazan caracteres de control. El frontend muestra el valor como texto escapado, no como marcado.
- Las etiquetas expuestas por la API contienen `id`, `name` y `color`. La paleta es accesible; las nuevas etiquetas reciben el color menos utilizado y los colores pueden reutilizarse.
- Las etiquetas sin recetas asociadas se eliminan dentro de la misma transacción que elimina o actualiza la asociación de la receta.
- La creación, edición, eliminación de recetas y la gestión de sus imágenes serán anónimas por ahora. La confirmación de borrado pertenece exclusivamente al frontend; la API no dependerá de un diálogo de navegador.
- El catálogo público ofrece una sola sección `Recetas`. Se elimina el ciclo `draft`/`published` de dominio, persistencia, API, frontend y pruebas: todas las recetas existentes y nuevas son públicas.
- El catálogo se filtra con parámetros repetidos `label`: varias etiquetas significan AND. Los parámetros se normalizan, deduplican e ignoran cuando quedan vacíos. Sin etiquetas, se devuelven todas las recetas. No se añade OR ni combinación con filtros de texto, ingredientes, autor u otros.
- La interfaz muestra las etiquetas alfabéticamente en tarjetas, detalle y formulario. El filtro se refleja en la URL, admite navegación atrás/adelante y funciona en pantallas estrechas y anchas.
- La API pública `GET /api/v1/labels?q=` ofrece autocompletado de etiquetas sin autenticación.

### Contratos previstos

- `GET /api/v1/recipes` devuelve el catálogo público; acepta cero o más `label` y devuelve cada receta con `labels` ordenadas alfabéticamente.
- `GET /api/v1/recipes/{recipe_id}` devuelve el detalle público con sus etiquetas.
- `POST /api/v1/recipes`, `PUT/PATCH /api/v1/recipes/{recipe_id}` y `DELETE /api/v1/recipes/{recipe_id}` quedan disponibles sin sesión.
- `POST /api/v1/recipes/{recipe_id}/image` y la operación de eliminación/reemplazo de imagen quedan disponibles sin sesión, conservando las validaciones de tipo y tamaño de imagen existentes.
- `GET /api/v1/labels?q=` devuelve etiquetas `{id, name, color}` ordenadas de forma determinista; `q` vacío devuelve las primeras opciones disponibles.
- Las escrituras reciben etiquetas como nombres; las lecturas devuelven objetos de etiqueta. Un error de validación no debe dejar asociaciones ni etiquetas huérfanas.

## Límites y no objetivos

- No se crea un panel independiente de administración de etiquetas, historial de etiquetas, alias, traducciones ni identificadores retenidos después de eliminar una etiqueta huérfana.
- No se añaden filtros OR, filtros combinados ni un lenguaje de consulta para el catálogo.
- No se mantiene ninguna diferencia de visibilidad entre borradores y publicadas; tampoco habrá endpoints de publicar o volver a borrador.
- No se cambia en esta historia la lógica de autenticación general ni las capacidades de favoritos y colecciones.

### Seguimiento pendiente, fuera de esta historia

La eliminación de la antigua área **`Mis recetas`** queda explícitamente pendiente para una historia posterior. Ese seguimiento debe retirar sus endpoints, componentes, pruebas y enlaces asociados a favoritos y colecciones. No se debe realizar esa eliminación durante esta historia: esos elementos permanecen como deuda de transición, aunque el catálogo público `Recetas` sea el único catálogo de recetas y las operaciones CRUD de recetas sean anónimas.

## Impacto

- **Personas usuarias:** podrán explorar por una o varias etiquetas y mantener recetas sin iniciar sesión; el estado del filtro podrá compartirse mediante la URL.
- **Datos:** se añaden tablas globales de etiquetas y de asociación receta-etiqueta. La identidad de una etiqueta es global por nombre normalizado y su color es estable mientras tenga vida.
- **API:** las respuestas de receta incorporan etiquetas y desaparece `status`; las mutaciones dejan de requerir `CurrentUser`. Las rutas de favoritos/colecciones no se retiran en esta entrega.
- **Frontend:** el catálogo, las tarjetas, el detalle y el formulario dejan de mostrar estados de borrador/publicada, incorporan etiquetas ordenadas y un filtro responsive sincronizado con la URL.
- **Operación:** la asignación de color y la eliminación de huérfanas deben ejecutarse bajo transacción para evitar colores desequilibrados, asociaciones parciales o etiquetas sin uso.

## Criterios de éxito

1. Una receta puede guardarse anónimamente con cero a diez etiquetas; los valores vacíos, duplicados y los que exceden el décimo se tratan según la normalización confirmada.
2. La misma etiqueta escrita con mayúsculas, espacios exteriores o espacios repetidos se guarda una sola vez en minúsculas, conservando sus acentos.
3. Las etiquetas devueltas contienen `id`, `name` y `color`, usan una paleta accesible y reciben el color menos utilizado con reutilización determinista.
4. `GET /api/v1/recipes?label=a&label=b` solo devuelve recetas que tengan ambas etiquetas; sin etiquetas devuelve todo el catálogo.
5. `GET /api/v1/labels?q=` es público, devuelve sugerencias globales y no crea etiquetas por consultar.
6. Crear, editar, borrar recetas y gestionar imágenes funciona sin sesión; borrar exige confirmación visible en frontend y no en el backend.
7. Ninguna respuesta, tabla, componente o prueba del flujo de recetas depende de `draft`/`published` tras la migración.
8. Tarjetas, detalle, formulario y filtro muestran las etiquetas en orden alfabético y el filtro se conserva en la URL en diseño responsive.

## Estrategia de reversión

La migración de etiquetas debe ser aditiva y reversible mientras no se retire el estado editorial. Para una reversión de aplicación, el backend anterior ignora las tablas nuevas y el catálogo anterior sigue leyendo recetas. La eliminación del estado `draft`/`published` es una migración de contrato: antes de aplicarla se debe haber desplegado la versión que ya no depende de `status`; recuperar ese estado requeriría restaurar la columna desde una copia o migración de contingencia. No se deben borrar tablas de etiquetas automáticamente durante un rollback, porque podrían contener asociaciones creadas por usuarios.

## Tradeoffs

- La unicidad por nombre normalizado simplifica el catálogo y el autocompletado, pero hace que dos usos lingüísticamente distintos que normalicen igual compartan etiqueta.
- Asignar el color menos utilizado equilibra la paleta y permite reutilización, pero no conserva un color histórico después de eliminar una etiqueta huérfana.
- Limitar a diez etiquetas y descartar las posteriores conserva formularios manejables y hace explícita la capacidad máxima, aunque una persona puede no advertir que aportó más de diez; la UI debe mostrar el límite y el resultado normalizado.
- Hacer anónimas las mutaciones satisface el alcance actual, pero deja la moderación y protección contra abuso fuera de esta historia.

## Ronda de preguntas

Las decisiones de producto están confirmadas en la tarea. No se abre una nueva ronda: la implementación debe respetar este alcance y dejar la retirada de `Mis recetas` como seguimiento posterior explícito.
