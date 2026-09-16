# TASKS — F01 Catálogo de recetas

**Estado:** APPROVED · **Versión:** 0.1  
**SPEC base:** [SPEC.md](SPEC.md) v0.1, `APPROVED`.  
**PLAN base:** [PLAN.md](PLAN.md) v0.1, `APPROVED` por la persona usuaria el 2026-09-16.  
**Procedencia histórica:** cambio `recetas-publicas-privadas`; el registro original permanece en el historial Git.

## Secuencia y dependencia

| Orden | Tarea | Estado | Dependencia |
| --- | --- | --- | --- |
| 1 | REC-CAT-001 | DONE | — |
| 2 | REC-CAT-002 | DONE | REC-CAT-001 |
| 3 | REC-CAT-003 | BLOCKED | REC-CAT-002; PostgreSQL disponible y autorización de intento |
| 4 | REC-CAT-004 | TODO | REC-CAT-003 |
| 5 | REC-CAT-005 | TODO | REC-CAT-004 |
| 6 | REC-CAT-006 | TODO | REC-CAT-005 |
| 7 | REC-CAT-007 | TODO | REC-CAT-006 |
| 8 | REC-CAT-008 | TODO | REC-CAT-007 |
| 9 | REC-CAT-009 | TODO | REC-CAT-008 |
| 10 | REC-CAT-010 | TODO | REC-CAT-009 |

Las tareas 1–4 corresponden al hito 1 del PLAN; 5–7, al hito 2; 8–9, al hito 3; y 10, al hito 4. La migración de catálogo debe estar terminada antes de que R1/F02 cree su FK; esta feature no modifica R1.

## Tareas

### REC-CAT-001 — Cerrar RED del contrato de migración

- **Estado:** DONE.
- **Trazabilidad:** PLAN §Pruebas y §Despliegue e infraestructura; US-REC-001, CA-REC-001…002, RD-REC-001, RD-REC-007…008.
- **Preparación:** `backend/tests/recipes/test_repository.py`; no alterar `0001` ni artefactos de calendario.
- **Pasos ejecutados:** se añadieron los tres contratos RED de identidad, independencia del calendario y documentación de orden.
- **Prueba y resultado:** `.venv/bin/pytest -q backend/tests/recipes/test_repository.py` devolvió `FFF` (3 fallos esperados) por ausencia de `0002` y de sus notas.
- **DoD:** los contratos fallan por la funcionalidad ausente, no por infraestructura ajena.
- **Evidencia de cierre:** el resultado RED y la verificación quedaron registrados en el historial Git del cambio.
- **Estimación:** 0,25 jornada.

### REC-CAT-002 — Aplicar GREEN de migración y dependencia

- **Estado:** DONE.
- **Trazabilidad:** PLAN §Arquitectura, §Despliegue e infraestructura y §Pruebas; US-REC-001, CA-REC-001…002, RD-REC-001, RD-REC-007…008.
- **Preparación:** REC-CAT-001 cerrada; puntos de trabajo: `backend/migrations/versions/0002_recipe_catalogue_foundation.sql`, `backend/migrations/README.md`, `requirements.txt` y `requirements-dev.txt`.
- **Pasos ejecutados:** se creó la migración de catálogo independiente, se documentó el orden catálogo→calendario y se añadió Psycopg 3 sin cambiar `0001` ni R1.
- **Prueba y resultado:** `.venv/bin/pytest -q backend/tests/recipes/test_repository.py` devolvió `3 passed in 0.01s`.
- **DoD:** existe el contrato de migración y dependencia requerido por el PLAN; el calendario sigue sin cambios.
- **Evidencia de cierre:** los archivos y la salida del comando constan en el historial Git del cambio.
- **Estimación:** 0,5 jornada.

### REC-CAT-003 — Triangular la migración en PostgreSQL aislado

- **Estado:** BLOCKED.
- **Trazabilidad:** PLAN §Pruebas y §Despliegue e infraestructura; CA-REC-001…002, RD-REC-001, RD-REC-007…008.
- **Preparación:** REC-CAT-002; servicio PostgreSQL con `pg_trgm`, esquema transaccional aislado y autorización de intento disponible.
- **Pasos:** aplicar `0002` sin tablas de calendario; comprobar tabla, restricciones, índice, independencia expand-only y orden de migración; revertir el esquema de prueba.
- **Prueba y resultado esperado:** la integración PostgreSQL confirma el contrato sin crear ni modificar `meal_assignments`.
- **DoD:** integración ejecutada y resultado registrado; el calendario no se modifica.
- **Evidencia requerida:** comando pytest de integración, versión/entorno PostgreSQL, resultado y referencia a la prueba. El intento histórico quedó bloqueado antes de ejecutar; el registro técnico original permanece en el historial Git.
- **Estimación:** 0,5 jornada.

### REC-CAT-004 — Refactorizar y regresionar la migración

- **Estado:** TODO.
- **Trazabilidad:** PLAN §Arquitectura y §Pruebas; CA-REC-001…002, RD-REC-001, RD-REC-007.
- **Preparación:** REC-CAT-003 completada; revisar únicamente SQL, notas y pruebas de migración.
- **Pasos:** simplificar solo duplicación detectada; mantener el contrato explícito; ejecutar pruebas focalizadas y la regresión existente.
- **Prueba y resultado esperado:** pruebas de migración y suite existente en verde, sin cambios de comportamiento.
- **DoD:** el SQL permanece acotado e independiente de calendario; resultados de regresión registrados.
- **Evidencia requerida:** diff revisado, comandos exactos, entorno y salidas resumidas.
- **Estimación:** 0,25 jornada.

### REC-CAT-005 — Escribir RED del límite de esquema

- **Estado:** TODO.
- **Trazabilidad:** PLAN §Arquitectura y §Pruebas; US-REC-002…003, CA-REC-003…005, RD-REC-001…005.
- **Preparación:** REC-CAT-004; crear o ampliar `backend/tests/recipes/test_schemas.py` sin añadir frameworks de validación.
- **Pasos:** escribir pruebas fallidas para UUID de creación/restauración, NFC y espacios, límites, URL HTTP(S) absoluta y clave de búsqueda sin acentos.
- **Prueba y resultado esperado:** el test focalizado falla exclusivamente porque aún no existe el límite de dominio.
- **DoD:** cada regla cubierta tiene un fallo RED observable.
- **Evidencia requerida:** comando pytest, salida RED y motivo de fallo por caso.
- **Estimación:** 0,5 jornada.

### REC-CAT-006 — Implementar GREEN del límite de esquema

- **Estado:** TODO.
- **Trazabilidad:** PLAN §Arquitectura y §Datos e interfaces; US-REC-001…003, CA-REC-003…005, RD-REC-001…005.
- **Preparación:** REC-CAT-005; puntos de trabajo previstos: `backend/src/comemos_en_casa/recipes/__init__.py` y `schemas.py`.
- **Pasos:** implementar valores inmutables, normalización, validación y creación/restauración UUID según la SPEC; no exponer API ni autorización.
- **Prueba y resultado esperado:** los RED de REC-CAT-005 pasan.
- **DoD:** valores aceptados quedan normalizados y los inválidos se rechazan conforme a la SPEC.
- **Evidencia requerida:** salida pytest focalizada y referencia a los casos que demuestran cada regla.
- **Estimación:** 0,5 jornada.

### REC-CAT-007 — Triangular y refactorizar el límite de esquema

- **Estado:** TODO.
- **Trazabilidad:** PLAN §Pruebas; CA-REC-003…005, RD-REC-001…005.
- **Preparación:** REC-CAT-006; ampliar las pruebas de esquema existentes.
- **Pasos:** cubrir CRLF/CR, límites Unicode, URL inválidas y claves con comodines; consolidar helpers sin cambiar el contrato.
- **Prueba y resultado esperado:** la suite de esquema pasa y conserva UUID al actualizar valores.
- **DoD:** límites y normalizaciones de borde quedan cubiertos y no se introduce una política HTTP, UI ni privada.
- **Evidencia requerida:** comando focalizado, resultado, casos añadidos y regresión ejecutada.
- **Estimación:** 0,5 jornada.

### REC-CAT-008 — Escribir RED e implementar repositorio de catálogo

- **Estado:** TODO.
- **Trazabilidad:** PLAN §Arquitectura, §Datos e interfaces y §Seguridad y observabilidad; US-REC-002…003, CA-REC-004…006, RD-REC-001, RD-REC-006, RD-REC-009.
- **Preparación:** REC-CAT-007; ampliar `backend/tests/recipes/test_repository.py` antes de crear `backend/src/comemos_en_casa/recipes/repository.py`; conexión Psycopg abierta gestionada por el consumidor.
- **Pasos:** (1) añadir RED para inserción, actualización, detalle, valores actuales, búsqueda literal limitada y UUID desconocido; (2) implementar SQL parametrizado, orden determinista y transacción propiedad del llamador; (3) ejecutar GREEN.
- **Prueba y resultado esperado:** RED falla sin repositorio; GREEN devuelve solo los campos públicos actuales y trata `%`, `_` y `\\` como literales.
- **DoD:** no hay snapshots, commits internos, pool, reintentos, HTTP ni filtros de visibilidad.
- **Evidencia requerida:** salidas RED y GREEN separadas, comando/entorno PostgreSQL y resultados por contrato.
- **Estimación:** 1 jornada.

### REC-CAT-009 — Triangular y refactorizar el repositorio

- **Estado:** TODO.
- **Trazabilidad:** PLAN §Pruebas y §Riesgos y decisiones pendientes; CA-REC-004…006, RD-REC-001, RD-REC-006.
- **Preparación:** REC-CAT-008; PostgreSQL aislado y repositorio funcional.
- **Pasos:** probar actualización de título/URL/detalle y clave, UUID inmutable, límites 1–50, búsquedas con comodines y detalle inexistente; separar mapeo SQL de validación solo si hay duplicación.
- **Prueba y resultado esperado:** lecturas posteriores devuelven valores actuales, ordenados de forma determinista, y la regresión pasa.
- **DoD:** la capa conserva el límite de responsabilidades del PLAN y toda consulta es parametrizada.
- **Evidencia requerida:** comandos, resultados focalizados y completos, versión PostgreSQL y revisión de SQL.
- **Estimación:** 0,75 jornada.

### REC-CAT-010 — Demostrar tombstone y cerrar límites de integración

- **Estado:** TODO.
- **Trazabilidad:** PLAN §Pruebas y §Despliegue e infraestructura; US-REC-004, CA-REC-007, RD-REC-007…009.
- **Preparación:** REC-CAT-009; `0001` y `0002` aplicables solo dentro de una prueba PostgreSQL aislada.
- **Pasos:** añadir en la prueba una FK temporal propiedad conceptual de R1 con `ON DELETE SET NULL`; borrar una receta; comprobar que la asignación persiste con referencia nula; verificar que el diff no altera las migraciones de R1, ni añade autenticación, UI, rutas o recetas privadas.
- **Prueba y resultado esperado:** la asignación se conserva como tombstone; la migración de catálogo sigue siendo aplicable antes de la futura FK.
- **DoD:** compatibilidad demostrada sin implementar ni migrar R1 y límites de alcance revisados.
- **Evidencia requerida:** comando de integración, resultado, esquema temporal empleado y diff/inspección de fronteras.
- **Estimación:** 0,5 jornada.

## Control de entrega

El PLAN estima 350–395 líneas. Antes de implementar cada tarea se recalcula el diff real; si supera 400 líneas, se pausa para la decisión de entrega prevista en el PLAN. No se crea ni modifica una migración de R1 hasta que esta fundación esté integrada.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | TASKS creadas en DRAFT desde PLAN v0.1 aprobado y estado histórico del cambio. |
| 0.1 | 2026-09-16 | TASKS aprobadas por la persona usuaria. |
