# Diseño técnico: repetir comidas en el calendario

## Estado y decisiones de diseño

- **Cambio:** `repetir-comidas-calendario`
- **Estado:** listo para implementación
- **Skill resolution:** `none` (no se inyectó una ruta de skill para esta fase)
- **Entradas:** `proposal.md` y `specs/meal-calendar/spec.md` finalizados

Este diseño mantiene el calendario único `CALENDAR_KEY = "shared"`, las asignaciones existentes en `meal_assignments` y el contrato de semana lunes-domingo. Una serie recurrente es una única regla persistida; una ocurrencia es una proyección de lectura, nunca una fila propia.

## Arquitectura elegida

### Modelo persistido

Añadir la migración aditiva `backend/migrations/versions/0007_meal_calendar_recurrence.sql` con una sola tabla nueva:

```sql
CREATE TABLE meal_recurrence_rules (
    id uuid PRIMARY KEY,
    calendar_key text NOT NULL REFERENCES meal_calendars (calendar_key),
    initial_date date NOT NULL,
    meal_slot text NOT NULL CHECK (meal_slot IN ('lunch', 'dinner')),
    free_text text NOT NULL,
    interval_weeks smallint NOT NULL CHECK (interval_weeks IN (1, 2, 3, 4)),
    CHECK (free_text = btrim(free_text)),
    CHECK (char_length(free_text) BETWEEN 1 AND 100)
);

CREATE INDEX meal_recurrence_rules_calendar_initial_idx
    ON meal_recurrence_rules (calendar_key, initial_date);
```

`id` es simultáneamente la identidad estable de la serie y la clave de idempotencia de su creación. La aplicación genera el UUID una vez al abrir el editor de creación y lo conserva para reintentos. No se añade `recipe_id`, `assignment_kind`, fecha de fin, contador, regla de días alternativos, excepción ni tabla de ocurrencias: todos entrarían en conflicto con el alcance aprobado.

La migración replica las restricciones SQL de texto libre de `meal_assignments`; el dominio seguirá usando `normalize_free_text`, que además elimina marcado HTML y normaliza NFC. El `date` de PostgreSQL y `datetime.date` son deliberados: representan una fecha civil del producto, no un instante UTC.

### Dominio, repositorio y expansión

Extender `backend/src/comemos_en_casa/meal_calendar/schemas.py` con:

- `RECURRENCE_INTERVALS = frozenset({1, 2, 3, 4})` y la representación de entrada `0` para `No repetir` solo en la capa de escritura;
- un `RecurrenceRuleDraft` validado, exclusivamente `free_text`, con `initial_date`, `slot`, `free_text` e `interval_weeks`;
- un valor de dominio `RecurrenceRule` y una representación de lectura `RecurringOccurrence` que contienen `series_id`, `occurrence_date` e información de presentación.

Mantener en `service.py` las reglas temporales puras y añadir una función equivalente a:

```python
def occurrence_in_week(rule, week_start, week_end) -> date | None:
    if rule.initial_date > week_end:
        return None
    period_days = rule.interval_weeks * 7
    elapsed = (week_start - rule.initial_date).days
    cycles = max(0, (elapsed + period_days - 1) // period_days)
    occurrence = rule.initial_date + timedelta(days=cycles * period_days)
    return occurrence if occurrence <= week_end else None
```

La llamada recibe el intervalo ya validado por `week_dates`: lunes y domingo inclusivos. La aritmética es siempre de fechas locales y días enteros; no hay conversión de zona horaria ni suma de meses. Por ello una regla conserva el día de la semana al cruzar meses y transiciones DST, y una semana de siete días recibe como máximo una ocurrencia por regla.

`MealCalendarRepository` incorporará operaciones para reglas (`find_rule_by_id`, inserción idempotente, actualización, borrado y listado de candidatas) y extenderá `list_week` para:

1. leer las asignaciones ordinarias existentes entre `week_start` y `week_end`, incluyendo el `LEFT JOIN recipes` actual;
2. leer reglas con `calendar_key = 'shared'` e `initial_date <= week_end`, usando el índice nuevo;
3. expandir cada candidata con la función pura y descartar las que no caen en la semana;
4. combinar asignaciones y ocurrencias virtuales y aplicar un único orden.

El filtro de fecha impide analizar reglas que aún no han comenzado. Con el volumen esperado de un calendario doméstico compartido, expandir candidatas antiguas en memoria es más legible y auditable que codificar aritmética de intervalos en SQL, y la salida queda estrictamente acotada a siete días. El índice permite excluir reglas futuras. Si el número de reglas históricas creciera de forma demostrable, se puede sustituir internamente el listado por una CTE PostgreSQL que calcule la siguiente fecha sin alterar tabla, API ni semántica; no se anticipa una tabla de ocurrencias para esa optimización.

El orden combinado es exactamente:

1. `date` ascendente;
2. `lunch` antes de `dinner`;
3. texto visible normalizado con el actual `normalize_title_search` (para recetas se conserva título o `Receta no disponible`);
4. identidad estable como desempate.

Para una asignación ordinaria el desempate es su UUID existente; para una ocurrencia es `series:{series_id}:{occurrence_date ISO}`. Así dos series con el mismo texto siguen siendo entradas distintas y el orden se repite de forma determinista.

### Identidad y respuesta de lectura

Conservar `id` de las asignaciones ordinarias como el UUID que los clientes ya conocen. Ampliar `AssignmentResponse`/`CalendarAssignment` con un discriminante y metadatos de recurrencia:

```json
{
  "id": "series:5d…:2026-09-30",
  "entryType": "recurring_occurrence",
  "date": "2026-09-30",
  "slot": "lunch",
  "kind": "free_text",
  "text": "Sopa",
  "seriesId": "5d…",
  "occurrenceDate": "2026-09-30",
  "initialDate": "2026-09-16",
  "recurrenceWeeks": 2
}
```

Para las filas existentes, la respuesta conserva `id`, `date`, `slot`, `kind`, `text`/`recipe` y expone `entryType: "assignment"`; no incorpora campos de serie. El identificador de una ocurrencia se deriva, no se almacena, y es la tupla `(seriesId, occurrenceDate)` codificada de forma legible. `entryType` evita que el cliente la interprete como identidad de una fila de `meal_assignments`; toda mutación recurrente usa exclusivamente `seriesId`.

Las respuestas de lectura de recetas no cambian: las asignaciones históricas de receta conservan `kind: "recipe"`, su referencia actual y el texto de receta no disponible si su FK quedó a `NULL`.

## Contratos de escritura y transacciones

Se conserva la familia `/api/v1/meal-calendar` y sus dependencias actuales de acceso, límites y `Cache-Control: no-store`.

### Asignaciones ordinarias y conversión explícita

Extender el cuerpo actual de `POST /assignments` y `PATCH /assignments/{assignment_id}` con `recurrenceWeeks` (alias de entrada/salida `recurrence_weeks` cuando corresponda), entero permitido `0 | 1 | 2 | 3 | 4`; el valor ausente se interpreta como `0` para conservar clientes actuales.

- `POST` con `recurrenceWeeks: 0` conserva la creación ordinaria actual, incluida la idempotencia por `id`.
- `POST` con `1..4` requiere `id`, `kind: "free_text"`, texto válido, fecha y franja válidas; crea solo `meal_recurrence_rules.id = id` y devuelve la ocurrencia virtual del ancla. Repetir el mismo UUID y el mismo borrador devuelve la representación ya creada; cambiar cualquier campo devuelve `409 idempotency_conflict` sin modificarla.
- `PATCH /assignments/{id}` con `0` mantiene la actualización ordinaria actual. Con `1..4`, solo si la asignación encontrada es `free_text`, convierte explícitamente la asignación en una serie. La serie usa el UUID de la asignación como `seriesId`, los valores editados como ancla, texto, franja e intervalo, y devuelve una ocurrencia virtual.
- Una petición recurrente para una receta, un `recipeId` no nulo, un tipo incompatible, un intervalo no permitido, una fecha no ISO/`date`, una franja no permitida o texto inválido recibe `422 validation_failed` antes de mutar. La ruta ordinaria de receta se conserva para clientes y registros antiguos cuando no se solicita recurrencia.

La conversión se realiza dentro de un `with connection.transaction():` (savepoint seguro incluso tras el consumo del límite de tasa): validar, leer y confirmar que la asignación es de texto libre, insertar la regla y borrar la asignación original. Cualquier fallo revierte ambas instrucciones; nunca queda una serie más la asignación ni se pierde la asignación ante un fallo de inserción. El repositorio no hace `commit`, siguiendo la convención actual de conexión propiedad del llamador.

### Mutaciones de serie

Añadir rutas explícitas, sin rutas de ocurrencia:

- `PATCH /series/{series_id}` acepta exclusivamente `{initialDate, text, recurrenceWeeks, confirmAnchorChange}`. `recurrenceWeeks` es `1..4`, el cuerpo no acepta `slot`, `kind` ni receta (`extra="forbid"`). El cambio de fecha de ancla exige `confirmAnchorChange: true` solo cuando difiere de la fecha persistida; si falta, responde `422` y no modifica nada. El `meal_slot` no se toca, por lo que se conserva aunque se cambie el día de la semana. La respuesta es una representación de regla (`seriesId`, `initialDate`, `slot`, `text`, `recurrenceWeeks`) y no una ocurrencia inexistente.
- `DELETE /series/{series_id}?confirmed=true` elimina la regla completa. La ausencia o el valor falso de `confirmed` devuelve `422`; con confirmación, una regla existente se borra y una ya ausente responde igualmente `204`. Esto satisface tanto la confirmación del flujo `No repetir` como la idempotencia de reintentos de borrado.

No se implementan `PATCH` ni `DELETE` de una URL construida desde `occurrenceDate`, ni cuerpos que contengan solo una fecha de ocurrencia. Esas entradas reciben `404`/`422` como objetivo inválido según la ruta o el esquema y no crean excepciones u overrides. `PATCH /series` es idempotente por estado: reenviar el mismo objetivo y borrador deja la misma regla; borrar repetidamente con `confirmed=true` no produce un segundo efecto ni crea una asignación. Las actualizaciones y borrados afectan la fila de regla en una transacción; el comportamiento ante escrituras concurrentes es último escritor confirmado, que es suficiente al no existir revisión u ownership en el contrato aprobado.

Cuando una serie se edita con `No repetir`, el frontend no envía un `PATCH` con intervalo cero: después de la confirmación usa el `DELETE` confirmado. Por tanto no se crea ni conserva una asignación en el ancla ni en la ocurrencia desde la que se abrió el editor.

## Diseño de frontend

### Tipos, cliente API y estado

En `frontend/src/types.ts` separar la procedencia de una entrada con una unión discriminada:

- `CalendarAssignment` ordinaria: `entryType: "assignment"`, `id` actual y sin datos de recurrencia;
- `RecurringCalendarOccurrence`: `entryType: "recurring_occurrence"`, `id` derivado, `seriesId`, `occurrenceDate`, `initialDate` y `recurrenceWeeks: 1 | 2 | 3 | 4`.

Añadir `RecurrenceWeeks = 0 | 1 | 2 | 3 | 4`, un payload ordinario ampliado y un payload de actualización de serie sin `slot`. En `frontend/src/api.ts`, conservar `createAssignment`, `updateAssignment` y `deleteAssignment` para asignaciones; añadir `updateSeries` y `deleteSeries(seriesId, confirmed)` para las rutas de regla.

En `frontend/src/calendarReducer.ts`, el editor pasa a ser un estado discriminado con:

- objetivo (`assignmentId` o `seriesId` y `occurrenceDate` informativo);
- `date` para asignación ordinaria o `initialDate` para serie;
- `slot`, `kind`, texto e intervalo seleccionado;
- UUID de creación generado al abrir el editor y retenido hasta éxito/cancelación;
- fecha de ancla original para decidir si hay que pedir confirmación.

El UUID se genera al abrir una creación, no al pulsar Guardar. Así un reintento manual tras timeout reutiliza la misma identidad. Tras cualquier creación recurrente, conversión, actualización de serie o borrado de serie, el cliente invalida y vuelve a leer la semana activa en lugar de parchear optimistamente una sola tarjeta: una modificación puede añadir, eliminar o cambiar entradas fuera de la celda mostrada, incluida la semana actual tras reanclar. Las mutaciones ordinarias pueden conservar el refresco local existente, pero la implementación puede unificar también mediante refetch para reducir ramas.

### Editor y confirmaciones

Actualizar `frontend/src/App.tsx` y estilos mínimos en `frontend/src/styles.css` sobre el modal accesible actual:

1. Las altas nuevas de esta HU abren editor de **texto libre** y muestran un selector `Repetir`: `No repetir`, `Cada semana`, `Cada 2 semanas`, `Cada 3 semanas`, `Cada 4 semanas`. No se añade búsqueda, selección ni enlace de recetas a este flujo.
2. Al editar una asignación ordinaria de texto libre, fecha, franja, texto y selector siguen siendo editables. Elegir `1..4` llama al `PATCH /assignments/{id}` de conversión. Elegir `No repetir` mantiene la asignación ordinaria.
3. Al abrir cualquier tarjeta recurrente, el editor deja claro que se está editando toda la serie y usa `initialDate`, no `occurrenceDate`, como campo de ancla. La franja aparece visible pero deshabilitada/no editable. Texto e intervalo `1..4` se pueden cambiar.
4. Al cambiar la fecha inicial de una serie, antes de enviar se abre una confirmación con el aviso de que cambia el día de la semana de toda la serie, incluidas lecturas pasadas y futuras. Si se cancela, no se llama a la API ni se altera la regla.
5. Al seleccionar `No repetir` en una serie, mostrar una confirmación inequívoca de borrado completo; al confirmar, llamar a `deleteSeries(..., true)`. El botón Eliminar de una serie usa el mismo aviso y el mismo endpoint. No se ofrece una opción de editar/eliminar solo la tarjeta abierta.
6. Las tarjetas de recurrencia pueden indicar visualmente «Se repite cada N semanas», sin que ese texto sustituya sus etiquetas accesibles de comida/cena y fecha. Las tarjetas de receta heredadas siguen siendo legibles y no obtienen controles de recurrencia; los flujos ordinarios ya existentes de receta no se convierten ni se amplían.

La confirmación del navegador actual puede reutilizarse si conserva mensaje específico y la rama no ejecuta la petición al declinar; un submodal con el mismo foco atrapado es preferible si se necesita una advertencia más visible. En ambos casos, el backend sigue exigiendo la confirmación explícita, por lo que no se confía en la UI.

## Cambios previstos por archivo

| Ruta | Cambio previsto |
| --- | --- |
| `backend/migrations/versions/0007_meal_calendar_recurrence.sql` | Tabla de reglas, checks e índice aditivos; no ocurrencias. |
| `backend/migrations/README.md` | Documentar la versión 0007, su orden y reversión operativa. |
| `backend/src/comemos_en_casa/meal_calendar/schemas.py` | Valores, borradores y validaciones de recurrencia. |
| `backend/src/comemos_en_casa/meal_calendar/service.py` | Expansión pura de fecha local y coordinación transaccional si se mantiene ahí. |
| `backend/src/comemos_en_casa/meal_calendar/repository.py` | Persistencia de reglas, listado combinado y orden determinista. |
| `backend/src/comemos_en_casa/meal_calendar/api.py` | Modelos/respuestas discriminadas y rutas de conversión y serie. |
| `backend/tests/meal_calendar/test_time_text.py` | Intervalos, validación y límites temporales puros. |
| `backend/tests/meal_calendar/test_calendar_repository.py` | SQL parametrizado, expansión/mezcla y orden. |
| `backend/tests/meal_calendar/test_api_contract.py` | Identidad, idempotencia, conversión, mutaciones y errores HTTP. |
| `backend/tests/meal_calendar/test_recurrence_migration.py` | Aplicación aislada de 0001–0007, checks, índice y ausencia de tabla de ocurrencias. |
| `frontend/src/types.ts` | Unión de entradas y payloads de recurrencia. |
| `frontend/src/api.ts` | Llamadas de serie y serialización de frecuencia. |
| `frontend/src/calendarReducer.ts` | Estado discriminado del editor, UUID retenido e invalidación/refresco. |
| `frontend/src/App.tsx` | Selector, campos bloqueados y advertencias modales. |
| `frontend/src/styles.css` | Etiqueta recurrente y presentación de confirmaciones, sin cambiar el layout semanal. |
| `frontend/src/App.test.tsx` | Flujos visibles de creación, conversión, edición, confirmación y borrado. |

## Estrategia de pruebas

### Backend

- **Dominio temporal:** ancla en lunes y domingo inclusivos, inicio futuro, semana adyacente vacía, cada 1–4 semanas, cruce de mes, año y DST; comprobar que no hay más de una ocurrencia por regla y que la aritmética usa `date`.
- **Validación:** rechazar intervalo fuera de `0..4`, `0` para regla, receta/`recipeId` recurrente, texto vacío, HTML que queda vacío, fecha inválida, franja inválida, cambio de franja de serie, ancla sin confirmación y cuerpos extra en serie.
- **Repositorio:** una fila de regla por UUID, parámetros SQL, índice/candidatas, combinación de receta histórica, asignación libre y varias series en misma celda; probar el orden por texto normalizado e identidad incluso con textos iguales.
- **API:** crear regla y retry idéntico (`201`/`200`), conflicto de idempotencia, identidad estable de la misma ocurrencia en lecturas repetidas, conversión atómica con fallo simulado de inserción, edición desde una ocurrencia posterior, reanclaje confirmado, rechazos no mutantes y DELETE confirmado repetido `204`.
- **Migración PostgreSQL:** ejecutar las versiones en orden dentro de esquema y transacción aislados; comprobar FK al calendario, checks, índice, coexistencia sin `UNIQUE` por celda, y que no se crea tabla/columna de ocurrencias ni vínculo de receta.

### Frontend

Con Vitest/Testing Library y API simulada:

- crear una comida libre con cada etiqueta de frecuencia y comprobar payload con UUID estable;
- editar una asignación libre y convertirla a serie mediante su `assignmentId`;
- abrir una ocurrencia, comprobar que se muestra el ancla y que la franja no se puede editar;
- rechazar la confirmación de reanclaje o `No repetir` sin llamada de red; aceptarla y comprobar `confirmAnchorChange` o `deleteSeries(id, true)`;
- comprobar que el borrado de una serie no llama a `deleteAssignment`, que después se recarga la semana y que las tarjetas coincidentes siguen separadas;
- verificar que una receta heredada sigue mostrando su tarjeta/referencia y no muestra controles recurrentes.

La verificación final de implementación seguirá las convenciones de `COMMANDOS.md`: pruebas backend, `npm --prefix frontend run typecheck`, build y la suite correspondiente. No se ejecutan como parte de esta fase de diseño.

## Migración, despliegue y reversión

La migración es exclusivamente expansiva: no modifica `meal_assignments`, recetas, permisos ni datos existentes. Debe aplicarse después de `0006_collections_favorites.sql` en el orden léxico ya documentado. Se despliega primero la migración y después el backend/frontend que saben leer reglas; antes de habilitar la UI, no existe riesgo de generar ocurrencias porque la tabla empieza vacía.

Una reversión de aplicación es segura para los datos ordinarios: la versión anterior ignora `meal_recurrence_rules` y continúa leyendo `meal_assignments`. No se debe hacer un `DROP TABLE` automático como rollback de producción, porque eliminaría series creadas y no hay ocurrencias materializadas que restaurar. La reversión completa requiere una migración posterior, una decisión explícita sobre retener o exportar reglas y una ventana en la que las escrituras recurrentes estén deshabilitadas. No se materializarán fechas para «recuperarlas» durante la reversión, porque eso contradice el modelo aprobado.

## Alternativas rechazadas y tradeoffs

- **Materializar una fila por ocurrencia en `meal_assignments`: rechazado.** Introduce limpieza infinita, duplicados, reanclajes costosos y semántica de borrado parcial, y contradice expresamente la propuesta y especificación.
- **Excepciones u overrides por ocurrencia:** rechazado. Requieren identidad persistida de ocurrencia y habilitan el CRUD aislado prohibido; toda edición/borrado aplica a la regla.
- **Regla por fecha/franja con clave única o reemplazo de celda:** rechazado. El calendario ya permite múltiples comidas, y la especificación exige coexistencia sin conflicto ni aviso.
- **Frecuencias mensuales, fin de serie o fechas UTC:** rechazado. Añaden semántica no solicitada y los instantes UTC pueden desplazar la fecha civil alrededor de DST. El intervalo es exactamente `7 × n` días desde el ancla.
- **Usar el UUID de una regla como si fuera `meal_assignments.id` en el cliente:** rechazado. La respuesta derivada incluye discriminante, `seriesId` e identidad compuesta para impedir que una ocurrencia virtual alcance rutas de asignación ordinaria.
- **Convertir una serie a asignación al elegir `No repetir`: rechazado.** El contrato requiere borrar la regla completa tras confirmación y no conservar una comida en el ancla ni en la ocurrencia abierta.
- **Calcular todas las ocurrencias de una serie en cliente:** rechazado. Haría divergentes las lecturas compartidas y desplazaría reglas temporales fuera del backend. El cliente solo presenta ocurrencias ya expandidas para la semana solicitada.

El tradeoff principal es evaluar reglas históricas candidatas en una lectura semanal. Se acepta para el alcance y se protege con el índice de inicio, rango de salida fijo y una función de fecha fácil de probar. La alternativa SQL optimizada queda compatible para un problema medido, mientras que las alternativas de materialización y excepciones son incompatibles por diseño.
