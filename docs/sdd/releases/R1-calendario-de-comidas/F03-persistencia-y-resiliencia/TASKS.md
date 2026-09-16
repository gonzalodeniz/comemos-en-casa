# TASKS — F03 Persistencia y resiliencia

**Estado:** DRAFT · **Versión:** 0.1  
**Bases aprobadas:** [`SPEC.md`](SPEC.md) v0.1 (`APPROVED`, aprobada 2026-09-16) y [`PLAN.md`](PLAN.md) v0.1 (`APPROVED`, aprobado por la persona usuaria 2026-09-16).  
**Entrega:** PR 1 y PR 2A; requiere definir estrategia de PR encadenadas antes de implementar. **Pruebas:** usar `pytest`, ya configurado; ejecutar las comprobaciones específicas de cada tarea.

## Secuencia y checklist

- [x] PER-T01 — Fundación temporal y esquema expandible (PR 1; completada).
- [ ] PER-T02 — Repositorio PostgreSQL y catálogo de lectura (PR 2A; depende de PER-T01 y del destino real de `recipes(id)`).
- [ ] PER-T03 — Recuperación, idempotencia y concurrencia (PR 3; depende de PER-T02 y ACC-T02).

## PER-T01 — Fundación temporal y esquema expandible

**Entrega/estado:** PR 1, completada. **Trazabilidad:** PLAN §Hitos 1, §Datos e interfaces, §Pruebas; US-PER-001; CA-PER-001…002; RD-PER-001, RD-PER-004…005.  
**Preparación:** `backend/src/comemos_en_casa/meal_calendar/`, migración `0001_meal_calendar_foundation.sql` y pruebas `test_time_text.py`, `test_schema_migration.py`; sin FK inventada mientras falte `recipes(id)`.  
**Pasos realizados:** RED de validación temporal/texto y esquema; GREEN de frontera y migración; TRIANGULATE de formas inválidas, duplicados e índices; REFACTOR de constantes/validadores.  
**Pruebas esperadas:** cálculo Canary, lunes, Unicode y checks de esquema; duplicados de celda coexistentes.  
**DoD:** los contratos de fundación y migración expandible quedan cubiertos sin rollback destructivo.  
**Evidencia histórica:** `.venv/bin/pytest -q` devolvió `16 passed` y se ejecutaron pruebas focalizadas; el registro original permanece en el historial Git.
**Estimación:** 1 jornada (histórica; completada).

## PER-T02 — Repositorio PostgreSQL y catálogo de lectura

**Entrega/estado:** PR 2A, pendiente. **Trazabilidad:** PLAN §Hitos 2, §Datos e interfaces, §Pruebas; US-PER-001; CA-PER-001…002; RD-PER-004…005; dependencias F01/F02.  
**Preparación:** confirmar propietario y migración de `recipes(id)`; trabajar en `repository.py`, `catalog_adapter.py` y `test_repository.py`; depende de PER-T01.  
**Pasos:** (1) RED para lecturas semanales Monday-only, orden mixto, búsqueda/paginación, detalle y tombstones; (2) GREEN con repositorio/transacciones y adaptador sin snapshots; (3) TRIANGULATE para UUID repetido/mismo payload, conflicto, DELETE idempotente/404 y joins actuales; (4) REFACTOR de límites SQL, adaptación, desempate y errores.  
**Pruebas esperadas:** PostgreSQL aislado conserva UUID distintos, devuelve orden autoritativo y representa receta borrada sin título/imagen copiados.  
**DoD:** lectura y persistencia usan PostgreSQL; catálogo cumple el contrato de F02 sin duplicar su semántica.  
**Evidencia requerida:** salida RED y GREEN, `.venv/bin/pytest -q backend/tests/meal_calendar/test_repository.py`, suite PR1+PR2A, entorno PostgreSQL aislado y referencia al destino real de `recipes(id)`.  
**Estimación:** 1 jornada.

## PER-T03 — Recuperación, idempotencia y concurrencia

**Entrega/estado:** PR 3, pendiente. **Trazabilidad:** PLAN §Hitos 2, 3 y 5, §Pruebas; US-PER-002…004; CA-PER-003…012; RD-PER-002…004.  
**Preparación:** PER-T02 y ACC-T02; puntos `repository.py`, capa API y `test_resilience_access.py`; coordinar contrato HTTP con F01/F02 y cuota con F04.  
**Pasos:** (1) RED de cuatro intentos, 503, altas concurrentes, última actualización confirmada y PATCH posterior a DELETE; (2) GREEN con transacción nueva por reintento y errores estables; (3) TRIANGULATE con inyección de fallo y conexiones concurrentes; (4) REFACTOR de clasificación y descriptor de operación.  
**Pruebas esperadas:** 250/500/1000 ms tras intento inicial; reintentos internos no duplican efectos; PATCH tardío responde 404.  
**DoD:** recuperación aislada y concurrencia satisfacen la SPEC sin locks, ETags ni historial.  
**Evidencia requerida:** comandos pytest focalizados y backend completo, resultados de PostgreSQL aislado/concurrente, ciclo TDD por caso y cuerpos/cabeceras de error.  
**Estimación:** 1 jornada.
