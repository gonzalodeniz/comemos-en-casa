# F03 — Persistencia y resiliencia

**Estado:** DRAFT · **Versión:** 0.1 · **Fuente:** `specs/persistencia-y-resiliencia/spec.md`, `proposal.md`, `design.md` de `openspec/changes/calendario-de-comidas/`.

## Contexto

Esta feature hace persistentes y recuperables las operaciones de F01 y F02. Las decisiones de acceso y cuota están canonizadas en [F04](../F04-acceso-guest-y-proteccion/SPEC.md), aunque su almacenamiento usa PostgreSQL.

## Alcance y no alcance

Incluye PostgreSQL, guardado, cargas, reintentos, borradores y última escritura gana. No incluye offline, historial, autoría, locks, versiones, ETags de escritura, deshacer ni limpieza automática.

## Actores

- Persona que consulta o modifica el calendario.
- PostgreSQL como fuente de verdad.

## Historias y criterios de aceptación

### US-PER-001 — Conservar el calendario
Como persona con acceso, quiero que mis asignaciones estén disponibles tras reinicios y desde otro dispositivo.

- **CA-PER-001:** lecturas y mutaciones persisten en PostgreSQL y los planes se conservan hasta su eliminación manual.
- **CA-PER-002:** varias altas con UUID distintos en la misma celda coexisten.

### US-PER-002 — Guardar sin perder cambios
Como persona planificadora, quiero guardar por blur o explícitamente sin duplicar solicitudes.

- **CA-PER-003:** `Guardar` incorpora el campo enfocado, está deshabilitado sin cambios y no duplica una operación en vuelo.
- **CA-PER-004:** un cambio durante el guardado queda pendiente para una operación posterior.
- **CA-PER-005:** cada operación muestra `Guardando` y luego `Guardado` durante dos segundos.
- **CA-PER-006:** abandonar cambios no guardados pide confirmación; navegar espera guardados activos sin deshabilitar controles.

### US-PER-003 — Cargar y recuperarse
Como persona planificadora, quiero entender cargas y recuperar solo la operación que falló.

- **CA-PER-007:** toda carga de semana muestra skeleton, bloquea edición y mantiene navegación; puede conservar datos previos inertes bajo overlay.
- **CA-PER-008:** cada fallo real de lectura, escritura o borrado hace un intento inicial y tres reintentos tras 250 ms, 500 ms y 1 s.
- **CA-PER-009:** tras agotarlos muestra el toast exacto `No se pudo conectar con la base de datos. El cambio no se guardó. Inténtalo de nuevo.` y `Reintentar` repite solo la operación fallida.
- **CA-PER-010:** una mutación fallida conserva formulario/valor; una lectura fallida conserva contenido visible si existe; navegar cancela un reintento manual pendiente, no el borrador.

### US-PER-004 — Resolver concurrencia acotada
Como persona planificadora, quiero un resultado definido para modificaciones simultáneas.

- **CA-PER-011:** la última transacción de actualización confirmada prevalece, sin aviso de conflicto ni historial.
- **CA-PER-012:** un PATCH tardío no resucita una asignación ya eliminada y devuelve `404`.

## Reglas

- **RD-PER-001:** el backend Python y sus pruebas usan pytest cuando exista runner; esta SPEC no declara evidencia de ejecución.
- **RD-PER-002:** cada intento de escritura abre transacción nueva; solo el repositorio clasifica fallos transitorios y reintenta.
- **RD-PER-003:** el cliente no hace reintentos automáticos de datos; una acción manual es una solicitud nueva.
- **RD-PER-004:** alta usa idempotencia UUID; DELETE repetido devuelve `204`.
- **RD-PER-005:** no hay restricción única por fecha, turno, receta ni texto; los planes no se eliminan automáticamente.

## Modelo conceptual

`meal_calendars` contiene solo `shared`. `meal_assignments` contiene la asignación polimórfica con fecha, turno, receta nullable o texto. `meal_calendar_rate_limits` guarda buckets por IP/minuto/clase para F04.

## Interfaces

Todas usan JSON UTF-8, prefijo `/api/v1/meal-calendar` y `Cache-Control: no-store`.

- `POST /assignments` devuelve `201` o `200` idempotente; `PATCH` devuelve recurso actual; `DELETE` devuelve `204`.
- Errores: `400 malformed_request`, `404 assignment_not_found`, `409 idempotency_conflict`, `422 validation_failed`, `503 database_unavailable` con `{error:{code,message,retryable,fieldErrors}}`.

## RNF

La migración es expandible: no se ejecuta downgrade destructivo automático. El borrado de receta debe preservar la asignación (`ON DELETE SET NULL` cuando exista `recipes(id)`). Las pruebas futuras cubren PostgreSQL aislado, migración, idempotencia, cuatro intentos, concurrencia y fallo de borrado.

## Supuestos, dependencias y riesgos

- Depende de PostgreSQL y de catálogo que aporte `recipes(id)` antes de incorporar la FK real.
- Si PostgreSQL falla, no hay operación offline; la cuota de F04 falla cerrada.
- Riesgo: última escritura gana permite sobrescrituras deliberadamente sin recuperación.

## Glosario

- **Borrador:** valor local pendiente o fallido durante la sesión.
- **Operación:** una lectura, alta, actualización o baja identificable y reintentable de forma aislada.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | SPEC migrada desde OpenSpec. |
