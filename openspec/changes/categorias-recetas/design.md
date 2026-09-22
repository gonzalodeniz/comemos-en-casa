# Diseño técnico: categorías globales para recetas

## Estado y decisiones

- **Cambio:** `categorias-recetas`
- **Estado:** listo para implementación
- **Entrada:** decisiones confirmadas en `odd/tasks/categorias-recetas.md` y en la propuesta de este cambio.
- **Principio:** las etiquetas son datos globales de catálogo; no son propiedad de una cuenta ni un recurso administrable por separado.

## Modelo de dominio y normalización

### Etiquetas

Introducir un valor de dominio `RecipeLabel` con `id`, `name` y `color`. El nombre se normaliza antes de comparar, deduplicar o persistir:

1. aplicar normalización Unicode NFC;
2. convertir a minúsculas Unicode sin eliminar ni transliterar acentos;
3. recortar espacios Unicode de los extremos;
4. reemplazar cada secuencia de espacios Unicode por un único espacio ASCII;
5. ignorar el resultado si queda vacío;
6. validar un máximo de 25 caracteres Unicode;
7. permitir letras Unicode, números Unicode, espacios internos y caracteres especiales Unicode;
8. rechazar caracteres de control; el frontend debe renderizar los valores como texto escapado, nunca como marcado.

La longitud se comprueba después de la normalización. La deduplicación usa el nombre normalizado exacto, por lo que conserva la diferencia semántica entre letras acentuadas y no acentuadas. El orden de la primera aparición se conserva hasta el límite de diez; las repeticiones se eliminan antes de contar. Los valores posteriores al décimo se ignoran, no producen una segunda asociación y deben poder comunicarse en el formulario.

La consulta de autocompletado aplica la misma normalización, pero no crea datos. El orden visible de etiquetas es alfabético mediante una clave de búsqueda Unicode sensible a los acentos conservados y estable por `id` en caso de empate.

### Paleta accesible y asignación

Mantener una paleta versionada de colores de fondo que proporcione contraste WCAG AA (mínimo 4.5:1 con el color de texto definido por la interfaz). La primera versión puede usar estos colores oscuros con texto blanco: `#1D4ED8`, `#047857`, `#B45309`, `#BE123C`, `#7C3AED`, `#0F766E`, `#C2410C` y `#4338CA`.

Al crear una etiqueta nueva, dentro de la transacción se cuentan las etiquetas existentes que usan cada color. Se elige el color con menor uso y, en empate, el primero de la paleta. El color no cambia en una etiqueta existente al editar una receta. Al eliminar su última asociación, la etiqueta desaparece y su color vuelve a estar disponible para reutilización; no se conserva historial de colores.

## Persistencia y migraciones

Añadir una migración posterior a las migraciones existentes (la siguiente versión libre, sin renumerar las anteriores) con:

```sql
CREATE TABLE recipe_labels (
    id uuid PRIMARY KEY,
    name text NOT NULL UNIQUE,
    color text NOT NULL
);

CREATE TABLE recipe_label_assignments (
    recipe_id uuid NOT NULL REFERENCES recipes (id) ON DELETE CASCADE,
    label_id uuid NOT NULL REFERENCES recipe_labels (id) ON DELETE CASCADE,
    PRIMARY KEY (recipe_id, label_id)
);

CREATE INDEX recipe_label_assignments_label_recipe_idx
    ON recipe_label_assignments (label_id, recipe_id);
```

Los nombres reales podrán seguir la convención de las migraciones del repositorio, pero deben conservar unicidad sobre el nombre normalizado y una tabla de unión con claves foráneas. La tabla de etiquetas no se puebla por la migración: las etiquetas nacen al escribir recetas. No se guarda un contador de uso como fuente de verdad; el uso se obtiene contando asociaciones bajo la misma transacción.

La transición del ciclo editorial se realiza en dos fases operativas:

1. desplegar la aplicación que deja de leer/escribir `status`, trata todas las recetas como públicas y elimina los endpoints `publish`/`draft`;
2. aplicar una migración posterior que elimine la columna y las restricciones de estado cuando ningún consumidor dependa de ellas.

Si el despliegue exige una única migración, primero se verifica que el código de lectura ya no seleccione `status` y después se elimina la columna en la misma ventana. Las filas existentes no se borran ni se filtran: pasan a formar parte del catálogo público único.

## Transacciones de escritura

La creación y actualización de receta deben ejecutar en una única transacción:

1. validar y normalizar la receta y su lista de nombres;
2. deduplicar e ignorar vacíos y limitar a diez;
3. insertar o recuperar cada etiqueta por nombre normalizado con una estrategia segura ante carreras (`INSERT ... ON CONFLICT ...` y lectura del registro existente);
4. asignar color solo para etiquetas recién creadas, aplicando la regla de menor uso;
5. insertar o reemplazar las asociaciones de la receta;
6. eliminar etiquetas que ya no tengan asociaciones (`DELETE ... WHERE NOT EXISTS (...)`), sin borrar etiquetas todavía usadas por otras recetas;
7. confirmar solo si todos los pasos tienen éxito.

El borrado de una receta elimina sus asociaciones por `ON DELETE CASCADE` y, en la misma transacción, elimina las etiquetas huérfanas. La subida o eliminación de una imagen debe actualizar el recurso de receta de manera coherente: un archivo nuevo no se publica en la respuesta si el registro no se actualiza, y un fallo de receta no debe dejar una asociación de etiqueta parcial. La limpieza física de un archivo reemplazado puede diferirse a una operación segura de mantenimiento; no debe eliminar el archivo actual antes de confirmar el nuevo URL.

Las mutaciones ya no dependen de `CurrentUser`. La protección temporal contra abuso y la moderación no forman parte de este cambio. La confirmación de borrado se verifica en la interfaz; el endpoint `DELETE` es idempotente y no recibe un parámetro de confirmación de UI.

## Contratos HTTP

### Recetas

`GET /api/v1/recipes` es el catálogo público. Sus parámetros de filtro son cero o más `label` repetidos:

```http
GET /api/v1/recipes?label=rápido&label=sin%20gluten&label=rápido
```

El servidor normaliza, ignora vacíos y deduplica los valores. El ejemplo exige `rápido` **y** `sin gluten`; una etiqueta inexistente produce una lista vacía. Sin valores efectivos, devuelve todas las recetas. No se implementan OR, negación, texto, ingrediente, autor ni combinación con otros filtros en este catálogo. La paginación existente, si se conserva, no cambia la semántica del filtro.

`POST /api/v1/recipes` y `PUT/PATCH /api/v1/recipes/{recipe_id}` aceptan la receta actual más `labels: string[]`. La respuesta incorpora:

```json
{
  "id": "uuid",
  "title": "Sopa",
  "detail": "…",
  "imageUrl": "",
  "labels": [
    {"id": "uuid", "name": "sin gluten", "color": "#047857"}
  ]
}
```

Los nombres de entrada son texto; un nombre inválido devuelve `422` sin mutar receta, asociaciones ni etiquetas. La respuesta siempre ordena `labels` alfabéticamente. No se devuelve `status`.

`GET /api/v1/recipes/{recipe_id}` devuelve la misma forma de detalle y es público. `DELETE /api/v1/recipes/{recipe_id}` devuelve `204` y elimina la receta y sus asociaciones; repetirlo conserva la semántica idempotente existente. Las rutas `POST /{recipe_id}/publish` y `POST /{recipe_id}/draft` se eliminan y devuelven `404` una vez retiradas.

### Imágenes

Mantener la validación existente de JPEG, PNG y WebP y el límite de 10 MB. `POST /api/v1/recipes/{recipe_id}/image` acepta multipart sin sesión y devuelve el detalle con `imageUrl`. Añadir la operación `DELETE /api/v1/recipes/{recipe_id}/image` (o el equivalente del adaptador de medios existente) para dejar la URL vacía; ambas operaciones deben ser públicas y no alterar etiquetas. Un recurso inexistente devuelve `404`; un archivo inválido devuelve `422`.

### Autocompletado

`GET /api/v1/labels?q=` es público y no crea etiquetas. `q` se normaliza con las reglas de etiqueta; una consulta vacía devuelve las primeras sugerencias globales. La respuesta es:

```json
{
  "labels": [
    {"id": "uuid", "name": "sin gluten", "color": "#047857"}
  ]
}
```

Las sugerencias se limitan a un tamaño documentado, se ordenan alfabéticamente y no exponen etiquetas duplicadas. Una consulta inválida no modifica persistencia y devuelve `422`.

## Consultas y rendimiento

Para cada filtro efectivo, el repositorio debe unir `recipe_label_assignments` con `recipe_labels`, filtrar por el conjunto solicitado y agrupar por receta con `COUNT(DISTINCT label_id) = número de etiquetas solicitadas`. No se debe resolver AND cargando todo el catálogo en el frontend. Crear índices sobre nombre normalizado y sobre ambas direcciones de la tabla de unión. El autocompletado usa el índice de nombre o su clave de búsqueda. La respuesta de detalle carga las etiquetas una vez y las ordena en la consulta o en una capa de presentación única.

## Diseño de frontend

- `types.ts` elimina `RecipeStatus` y el campo `status`; añade `RecipeLabel` y `labels` a los resúmenes, detalles y formularios.
- `api.ts` serializa `labels` al crear/editar y usa `URLSearchParams.append("label", value)` para cada filtro. No fabrica una cadena CSV.
- El catálogo `Recetas` lee `location.search`, normaliza la selección, actualiza la URL con `history`/router y conserva atrás/adelante. El estado vacío equivale a todas las recetas.
- La barra de filtros permite buscar/seleccionar sugerencias de `/api/v1/labels?q=` y eliminar selecciones. Las etiquetas de cada tarjeta, detalle y formulario se ordenan con la misma clave alfabética. La presentación debe seguir siendo usable en móvil mediante envoltura, desplazamiento horizontal controlado o controles apilados.
- El formulario de receta muestra el límite diez, ignora visualmente entradas vacías, evita duplicados normalizados y permite espacios internos. Al guardar, refleja las etiquetas devueltas por el servidor para mostrar nombres e identificadores definitivos.
- El botón de borrado usa una confirmación accesible del frontend y solo llama a la API cuando se confirma. No se añade `confirmed` ni lógica de diálogo al contrato backend.
- Se eliminan de la experiencia de receta los textos, insignias, botones y ramas de `draft`/`published`. La futura retirada de `Mis recetas`, favoritos y colecciones no se implementa aquí.

## Archivos previstos

| Área | Cambio previsto |
| --- | --- |
| `backend/migrations/versions/` | Migración de etiquetas, tabla de unión e incorporación pública gradual del modelo sin estado editorial. |
| `backend/src/comemos_en_casa/recipes/` | Dominio, repositorio, transacciones, CRUD anónimo, imágenes, respuestas con etiquetas y eliminación de estado. |
| `backend/src/comemos_en_casa/meal_calendar/` | Adaptar resúmenes públicos de receta para no depender de `status`, sin cambiar el alcance del calendario. |
| `backend/tests/recipes/` | Pruebas de normalización, persistencia, colores, transacciones, CRUD anónimo, filtros y contratos de imagen. |
| `backend/tests/meal_calendar/` | Compatibilidad de asignaciones y catálogo sin estado editorial. |
| `frontend/src/types.ts`, `api.ts` | Tipos de etiqueta, serialización y filtros repetidos. |
| `frontend/src/App.tsx`, `styles.css` | Catálogo único, tarjetas/detalle/formulario, filtro URL y responsive. |
| `frontend/src/App.test.tsx` y pruebas de API | Flujos de etiquetas, URL, responsive semántico, confirmación y ausencia de estado. |

## Alternativas rechazadas

- **Etiquetas por usuario:** rechazado; el requisito es un vocabulario global visible para todo el catálogo.
- **Crear etiquetas desde un panel:** rechazado; las etiquetas nacen en el formulario de receta y el autocompletado solo consulta.
- **Guardar contadores de uso como verdad:** rechazado; los contadores pueden quedar obsoletos. Se cuentan asociaciones en la transacción.
- **Una sola cadena separada por comas:** rechazado; impide representar con claridad espacios, duplicados y parámetros repetidos.
- **Filtrar en cliente:** rechazado; rompe paginación, URLs compartibles y consistencia del catálogo.
- **Mantener borrador/publicada como compatibilidad visible:** rechazado; contradice el catálogo público único y duplica reglas de presentación.

## Riesgos

- Las mutaciones anónimas requieren límites o controles de abuso posteriores; no se inventa una autorización parcial en esta historia.
- Quitar `status` no es una reversión de aplicación completamente inocua; se debe observar el despliegue anterior y conservar una copia de la columna durante la migración.
- La asignación de colores depende de carreras concurrentes; la selección y la inserción deben usar bloqueo o una transacción con reintento ante conflicto.
