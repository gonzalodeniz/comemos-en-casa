# F02 — Asignaciones de comida

**Estado:** APPROVED · **Versión:** 0.1 · **Fuente:** `specs/asignaciones-de-comida/spec.md`, `proposal.md`, `design.md` de `openspec/changes/calendario-de-comidas/`.

## Contexto

Las asignaciones llevan recetas públicas o texto libre a las celdas de [F01](../F01-calendario-semanal/SPEC.md). La fuente de verdad, errores y concurrencia pertenecen a [F03](../F03-persistencia-y-resiliencia/SPEC.md).

## Alcance y no alcance

Incluye buscar, crear, editar y desasignar recetas y texto libre. No modifica el catálogo, no crea recetas privadas ni guarda copias históricas de título o imagen. No hay edición mediante atajo de teclado fuera del formulario.

## Actores

- Persona con acceso al calendario.
- Catálogo público de recetas, como dependencia de lectura.

## Historias y criterios de aceptación

### US-ASG-001 — Asignar recetas públicas
Como persona planificadora, quiero encontrar y asignar recetas públicas.

- **CA-ASG-001:** la búsqueda por título ignora mayúsculas/minúsculas y acentos; una consulta vacía permite listar catálogo.
- **CA-ASG-002:** se permiten recetas repetidas y varias asignaciones en la misma celda.
- **CA-ASG-003:** desasignar elimina solo la relación del calendario, de forma inmediata y sin confirmación.

### US-ASG-002 — Consultar receta asignada
Como persona planificadora, quiero consultar detalles sin perder mi contexto.

- **CA-ASG-004:** una receta disponible muestra título actual, portada y detalle en modal de solo consulta.
- **CA-ASG-005:** al cerrar el modal se restauran semana, búsqueda, scroll y foco disparador; no contiene editar ni desasignar.
- **CA-ASG-006:** una receta eliminada conserva su asignación como `Receta no disponible`, cuadro vacío de portada y acción `Desasignar`, sin modal.

### US-ASG-003 — Gestionar texto libre
Como persona planificadora, quiero añadir notas de comida sin receta.

- **CA-ASG-007:** receta y texto libre coexisten, incluidos textos idénticos.
- **CA-ASG-008:** se rechazan vacío, solo espacios y valores de más de 100 puntos de código Unicode; el HTML no se interpreta.
- **CA-ASG-009:** el texto libre se edita y elimina directamente; su tooltip muestra el texto completo mediante puntero, foco o pulsación táctil.

## Reglas

- **RD-ASG-001:** `kind` es `recipe` o `free_text`; receta conserva `recipeId`, texto libre conserva texto, fecha y turno, sin `created_at`.
- **RD-ASG-002:** las asignaciones se ordenan conjuntamente por texto visible normalizado (NFKD, sin marcas combinantes, `casefold`) y UUID como desempate.
- **RD-ASG-003:** el texto se normaliza NFC, se recortan extremos, se sanea con lista permitida vacía y se valida después entre 1 y 100 puntos de código; se renderiza exclusivamente como texto.
- **RD-ASG-004:** título y portada se leen del catálogo actual; al desaparecer una receta no se conserva snapshot y la asignación queda como tombstone no disponible.
- **RD-ASG-005:** `kind` no cambia mediante edición; convertir receta/texto requiere otra asignación.

## Modelo conceptual

`Asignación` tiene `id`, `date`, `slot`, `kind` y exactamente uno de `recipeId` o `text`. Una referencia de receta puede quedar sin destino tras su borrado y se representa como no disponible.

## Interfaces

- `GET /recipes?q=&cursor=&limit=` busca solo título, normalizado; `limit` máximo 50.
- `GET /recipes/{recipeId}` devuelve detalle público o `404 recipe_not_found`.
- `POST /assignments`, `PATCH /assignments/{id}` y `DELETE /assignments/{id}` siguen el contrato de F03. Alta usa UUID de cliente: mismo ID y payload devuelve `200`; payload distinto, `409 idempotency_conflict`.

## RNF

El modal debe preservar contexto y gestionar foco conforme a F05. El tooltip no contiene acciones, se cierra con Escape y limita su ancho a `min(20rem, calc(100vw - 2rem))`.

## Supuestos, dependencias y riesgos

- Depende de catálogo con identificador estable, título, portada y detalle públicos.
- Depende de F03 para `ON DELETE SET NULL` o una semántica equivalente de tombstone si el catálogo se separa.
- Riesgo: el orden de Unicode depende de la normalización canonizada; implementaciones cliente no deben sustituir al orden del backend.

## Glosario

- **Desasignar:** eliminar una asignación, nunca la receta.
- **Tombstone:** estado de una asignación cuya receta ya no existe.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | SPEC aprobada por la persona usuaria. |
