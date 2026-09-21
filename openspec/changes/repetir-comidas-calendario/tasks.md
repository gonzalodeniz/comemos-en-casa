# Tareas de implementación: repetir comidas en el calendario

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 900–1,300 líneas (código, pruebas, migración y documentación) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → persistencia/dominio backend; PR 2 → repositorio/API backend; PR 3 → tipos/API/reducer frontend; PR 4 → editor, estilos y pruebas de integración frontend |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

## Alcance y orden

Estas tareas implementan únicamente recurrencia de comidas `free_text` en el calendario compartido (`CALENDAR_KEY = "shared"`). No incluyen selección o vínculo nuevo de recetas, excepciones por ocurrencia, fechas de fin, materialización de ocurrencias, conflictos de celda ni cambios de permisos. Cada unidad conserva una frontera de rollback en los archivos indicados; si la revisión supera el presupuesto, se debe detener el apply y decidir el encadenamiento antes de continuar.

La secuencia estricta es **RED → GREEN → TRIANGULATE → REFACTOR**. Las tareas RED solo añaden evidencia fallida y no deben modificar producción.

## Backend — persistencia y dominio

### 1. RED: fijar contrato de migración, validación y expansión

- [x] Añadir pruebas deterministas que fallen para la migración `0007`, los checks de intervalo/texto/franja, la ausencia de tabla de ocurrencias y la expansión inclusiva lunes–domingo para intervalos 1–4, cruce de mes/año y ancla futura. Usar `backend/tests/meal_calendar/test_recurrence_migration.py` y `backend/tests/meal_calendar/test_time_text.py`; verificar con `pytest backend/tests/meal_calendar/test_recurrence_migration.py backend/tests/meal_calendar/test_time_text.py`. La evidencia debe mostrar fallos por comportamiento ausente, no por errores de sintaxis. <!-- sdd-owner: implementation -->

**Aceptación/evidencia:** los tests expresan fecha civil, una sola ocurrencia por regla, conservación del día de semana y `No repetir` como asignación ordinaria (`0`), sin tocar código de aplicación. **Rollback:** revertir únicamente esos dos archivos de pruebas.

### 2. GREEN: crear migración y valores de dominio

- [x] Implementar `backend/migrations/versions/0007_meal_calendar_recurrence.sql` y actualizar `backend/migrations/README.md` con la tabla aditiva `meal_recurrence_rules`, FK al calendario compartido, checks de `lunch`/`dinner`, texto normalizado de 1–100 caracteres, intervalos 1–4 e índice `(calendar_key, initial_date)`; extender `backend/src/comemos_en_casa/meal_calendar/schemas.py` con `RECURRENCE_INTERVALS`, `RecurrenceRuleDraft` y `RecurrenceRule`, reutilizando `normalize_free_text` y rechazando recetas. Verificar con la RED de migración/dominio y `pytest backend/tests/meal_calendar/test_schema_migration.py backend/tests/meal_calendar/test_recurrence_migration.py backend/tests/meal_calendar/test_time_text.py`. <!-- sdd-owner: implementation -->

**Aceptación/evidencia:** una regla guarda solo una fila, no guarda ocurrencias ni `recipe_id`, y la migración sigue el orden `0001`–`0007`; la reversión de aplicación deja intactas las asignaciones ordinarias. **Rollback:** eliminar los cambios de `0007`, README y `schemas.py` sin modificar migraciones previas.

### 3. GREEN: implementar expansión temporal pura

- [x] Añadir en `backend/src/comemos_en_casa/meal_calendar/service.py` la función de expansión equivalente a `occurrence_in_week`, usando exclusivamente `datetime.date`, intervalo `7 * n` días y límites inclusivos de `week_dates`; cubrir el ancla confirmada, semanas adyacentes vacías, domingo final, cruce de mes y ausencia de deriva por DST. Ejecutar `pytest backend/tests/meal_calendar/test_time_text.py`. <!-- sdd-owner: implementation -->

**Aceptación/evidencia:** la función devuelve como máximo una ocurrencia por regla, nunca filtra fuera de los siete días solicitados y reanclar cambia también lecturas históricas y futuras. **Rollback:** revertir únicamente la función y sus imports en `service.py`.

## Backend — repositorio y API

### 4. RED: fijar persistencia combinada y contratos HTTP

- [x] Extender primero las pruebas de `backend/tests/meal_calendar/test_calendar_repository.py` y `backend/tests/meal_calendar/test_api_contract.py` para exigir listado de reglas candidatas compartidas, expansión combinada, orden por fecha/franja/texto/identidad, identidad estable `(seriesId, occurrenceDate)`, creación idempotente, conflicto `409`, conversión ordinaria atómica, `PATCH /series/{series_id}`, `DELETE /series/{series_id}?confirmed=true` y rechazos no mutantes. Incluir coexistencia de varias series/ordinarias en la misma celda, slot inmutable, `No repetir` destructivo confirmado y compatibilidad con receta heredada. Ejecutar ambos archivos y registrar los fallos esperados. <!-- sdd-owner: implementation -->

**Aceptación/evidencia:** los tests no permiten mutar una ocurrencia aislada ni materializarla y comprueban que los reintentos no duplican ni cambian una regla; no añadir implementación en esta tarea. **Rollback:** revertir solo las ampliaciones de ambos archivos de pruebas.

### 5. GREEN: persistir reglas y leer semanas combinadas

- [x] Extender `backend/src/comemos_en_casa/meal_calendar/repository.py` con `find_rule_by_id`, inserción idempotente, actualización, borrado y listado de candidatas `calendar_key = "shared"`; modificar `list_week` para combinar asignaciones existentes (incluido `LEFT JOIN recipes`) con ocurrencias virtuales, derivar el identificador estable y aplicar un único orden determinista. Verificar con `backend/tests/meal_calendar/test_calendar_repository.py` y los tests de compatibilidad de `backend/tests/meal_calendar/test_api_contract.py`. <!-- sdd-owner: implementation -->

**Aceptación/evidencia:** no se crean filas en `meal_assignments` para ocurrencias, varias entradas de igual fecha/franja permanecen separadas y las recetas no disponibles siguen siendo legibles. **Rollback:** revertir solo los métodos de reglas y la combinación de `list_week` en `repository.py`.

### 6. GREEN: exponer creación, conversión y mutaciones de serie

- [x] Extender `backend/src/comemos_en_casa/meal_calendar/api.py` para aceptar `recurrenceWeeks: 0|1|2|3|4` con ausencia equivalente a `0`, devolver `entryType` discriminado y añadir `PATCH /series/{series_id}` y `DELETE /series/{series_id}?confirmed=true`; ejecutar creación/actualización/borrado y conversión de asignación libre dentro de transacciones, con UUID reutilizable, conflicto de idempotencia, `422` para receta/intervalo/fecha/franja/texto inválidos, confirmación obligatoria de reanclaje y borrado confirmado idempotente. No ofrecer rutas por `occurrenceDate`. Verificar con `pytest backend/tests/meal_calendar/test_api_contract.py`. <!-- sdd-owner: implementation -->

**Aceptación/evidencia:** editar cualquier ocurrencia actualiza toda la serie; cambiar el ancla confirmado conserva slot e intervalo; cambiar slot es rechazado; `No repetir` confirmado elimina sin crear una asignación; la conversión elimina la asignación original solo tras insertar correctamente la regla. **Rollback:** revertir los modelos, handlers y wiring nuevos de `api.py`, dejando la ruta ordinaria existente.

### 7. TRIANGULATE: comprobar límites, compatibilidad y transacciones backend

- [ ] Ejecutar y ajustar únicamente las pruebas backend necesarias en `backend/tests/meal_calendar/test_time_text.py`, `test_calendar_repository.py`, `test_api_contract.py` y `test_recurrence_migration.py` para triangular errores de límites de semana, retries, fallos simulados de inserción, reanclaje no confirmado, borrado repetido, coexistencia, calendario compartido y recetas históricas; verificar con `pytest` y después `make test-backend`. <!-- sdd-owner: implementation -->

**Aceptación/evidencia:** queda demostrada la matriz de escenarios de `spec.md`, incluida la conservación de datos ante conversión fallida, sin ampliar el alcance. **Rollback:** revertir solo correcciones de pruebas o adaptadores introducidas durante esta triangulación.

## Frontend — contratos, estado y editor

### 8. RED: fijar contratos de tipos, API, reducer y flujos visibles

- [ ] Ampliar `frontend/src/App.test.tsx` con pruebas fallidas para la unión `entryType`, frecuencias `0..4`, payload con UUID estable de creación, conversión mediante `assignmentId`, apertura de ocurrencia con `initialDate`, franja deshabilitada, confirmación de reanclaje, confirmación destructiva de `No repetir`, `deleteSeries` en vez de `deleteAssignment`, refetch posterior, coexistencia y receta heredada sin controles recurrentes. Añadir casos de reducer solo si la cobertura de la interfaz no permite observar el estado; ejecutar `cd frontend && npm test`. <!-- sdd-owner: implementation -->

**Aceptación/evidencia:** cada caso falla por la capacidad ausente y verifica que cancelar una confirmación no llama a la red. **Rollback:** revertir solo las pruebas RED en `App.test.tsx`.

### 9. GREEN: actualizar tipos, serialización API y reducer

- [ ] Implementar en `frontend/src/types.ts` `RecurrenceWeeks`, la unión `CalendarAssignment`/`RecurringCalendarOccurrence` y payloads de serie; en `frontend/src/api.ts` conservar contratos ordinarios y añadir `updateSeries`/`deleteSeries(seriesId, confirmed)`; en `frontend/src/calendarReducer.ts` modelar editor discriminado, `seriesId`, `occurrenceDate`, `initialDate`, intervalo, UUID retenido desde apertura y refresco posterior a mutación. Verificar con los tests RED y `cd frontend && npm run typecheck`. <!-- sdd-owner: implementation -->

**Aceptación/evidencia:** las ocurrencias no se tratan como filas ordinarias, el slot de serie no puede formar parte del payload de actualización y los clientes actuales siguen compilando. **Rollback:** revertir únicamente `types.ts`, `api.ts` y `calendarReducer.ts`.

### 10. GREEN: integrar editor, confirmaciones y presentación

- [ ] Modificar `frontend/src/App.tsx` y los estilos mínimos de `frontend/src/styles.css` para altas de texto libre con selector `No repetir`/`Cada semana`/`Cada 2–4 semanas`, conversión explícita de asignación, edición de serie sobre `initialDate`, slot visible deshabilitado, advertencia confirmada de reanclaje, borrado confirmado de serie y etiqueta accesible de frecuencia; mantener las tarjetas de receta heredadas legibles y sin controles de recurrencia. Verificar con `cd frontend && npm test` y `cd frontend && npm run typecheck`. <!-- sdd-owner: implementation -->

**Aceptación/evidencia:** cancelar cualquier confirmación deja la regla intacta y no hace petición; aceptar reanclaje envía `confirmAnchorChange`, aceptar `No repetir` llama `deleteSeries(id, true)`, y las comidas que comparten fecha/franja no se reemplazan ni se ocultan. **Rollback:** revertir los cambios del editor y estilos, conservando los contratos tipados ya verificados.

### 11. TRIANGULATE: validar interacción frontend y compatibilidad visual

- [ ] Ejecutar la suite de `frontend/src/App.test.tsx` junto con `cd frontend && npm run build`, y ajustar casos deterministas para relectura de semana tras crear, convertir, editar o borrar, identidad estable en reintento, series en una misma celda, confirmaciones canceladas y presentación de recetas disponibles/no disponibles. No modificar el layout semanal fuera de los estilos estrictamente necesarios. <!-- sdd-owner: implementation -->

**Aceptación/evidencia:** Vitest, typecheck y build pasan; la UI nunca ofrece mutación aislada y el comportamiento ordinario previo permanece cubierto. **Rollback:** revertir solo ajustes de tests o markup descubiertos durante la triangulación.

## Cierre técnico

### 12. REFACTOR: simplificar sin cambiar el contrato

- [ ] Revisar los archivos modificados del backend y frontend para eliminar duplicación entre asignaciones y ocurrencias, mantener nombres `camelCase`/`PascalCase` y PEP 8, conservar consultas parametrizadas, mensajes de confirmación específicos y documentación de rollback; ejecutar `make test`, `cd frontend && npm run typecheck` y `cd frontend && npm run build`, y documentar la evidencia antes de solicitar revisión. <!-- sdd-owner: implementation -->

**Aceptación/evidencia:** todos los criterios de `proposal.md`, `spec.md` y `design.md` tienen una prueba o evidencia explícita; la migración es aditiva y no se editan archivos fuera de este cambio durante apply. **Rollback:** revertir la unidad de refactor sin revertir comportamiento ya cubierto por las unidades previas.

## Verificación final prevista

- Backend: `pytest`, `make test-backend` y revisión aislada de `0007_meal_calendar_recurrence.sql`.
- Frontend: `cd frontend && npm test`, `cd frontend && npm run typecheck`, `cd frontend && npm run build`.
- Suite completa: `make test`.
- Antes de apply, confirmar la decisión de entrega exigida por `ask-on-risk`; mientras `Chain strategy` siga en `pending`, no asumir una cadena ni una excepción de tamaño.
