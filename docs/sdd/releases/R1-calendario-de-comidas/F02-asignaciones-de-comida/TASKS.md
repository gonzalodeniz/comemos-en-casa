# TASKS — F02 Asignaciones de comida

**Estado:** DRAFT · **Versión:** 0.1  
**Bases aprobadas:** [`SPEC.md`](SPEC.md) v0.1 (`APPROVED`, aprobada 2026-09-16) y [`PLAN.md`](PLAN.md) v0.1 (`APPROVED`, aprobado por la persona usuaria 2026-09-16).  
**Entrega:** PR 2A, PR 2B y PR 4; requiere estrategia de PR encadenadas antes de implementar. **Pruebas:** TDD estricto con `pytest`: RED → GREEN → TRIANGULATE → REFACTOR; no crear setup duplicado.

## Secuencia y checklist

- [ ] ASG-T01 — Catálogo, forma y orden de asignaciones (PR 2A; depende de PER-T01 y `recipes(id)`).
- [ ] ASG-T02 — Mutaciones y contrato HTTP (PR 2B; depende de ASG-T01, PER-T02, ACC-T03).
- [ ] ASG-T03 — Selector, tarjetas y edición visual (PR 4; depende de ASG-T02, CAL-T03, F05-T02).

## ASG-T01 — Catálogo, forma y orden de asignaciones

**Entrega/estado:** PR 2A, pendiente. **Trazabilidad:** PLAN §Hitos 1–3, §Datos e interfaces, §Pruebas; US-ASG-001…003; CA-ASG-001…002, CA-ASG-006…009; RD-ASG-001…004.  
**Preparación:** PER-T01 y propietario real del catálogo; `repository.py`, `catalog_adapter.py`, esquemas y `test_repository.py`; sin snapshot ni tabla de catálogo falsa.  
**Pasos:** (1) RED de tipo, Unicode, búsqueda normalizada/cursor, detalle, orden y tombstone; (2) GREEN del adaptador/validadores/lectura; (3) TRIANGULATE de duplicados y receta eliminada; (4) REFACTOR de normalización y desempate backend.  
**Pruebas esperadas:** título actual y portada se leen del catálogo; texto libre se sanea/valida y receta ausente queda no disponible.  
**DoD:** modelo polimórfico y orden autoritativo cumplen SPEC sin HTML ejecutable.  
**Evidencia requerida:** RED/GREEN, pytest de repositorio, PostgreSQL aislado y referencia al catálogo real.  
**Estimación:** 1 jornada.

## ASG-T02 — Mutaciones y contrato HTTP

**Entrega/estado:** PR 2B, pendiente. **Trazabilidad:** PLAN §Hitos 3, §Datos e interfaces; CA-ASG-002…003, CA-ASG-007…009; RD-ASG-001, RD-ASG-003, RD-ASG-005.  
**Preparación:** ASG-T01, PER-T02, ACC-T03; `api.py` y `test_api_contract.py`.  
**Pasos:** (1) RED POST/PATCH/DELETE, UUID idempotente, conflictos y errores; (2) GREEN de mutaciones; (3) TRIANGULATE mismo UUID/payload, distinto payload, delete repetido y PATCH de kind; (4) REFACTOR de validación/traducción HTTP.  
**Pruebas esperadas:** 201/200/409, 204 repetido y 404 tras borrado; PATCH no transforma kind.  
**DoD:** API conserva errores de F03 y no acopla SQL a la ruta.  
**Evidencia requerida:** pytest API/repositorio/PR1 y respuestas JSON/cabeceras.  
**Estimación:** 1 jornada.

## ASG-T03 — Selector, tarjetas y edición visual

**Entrega/estado:** PR 4, pendiente. **Trazabilidad:** PLAN §Hitos 4, §Pruebas; CA-ASG-001…009; RD-ASG-002…005.  
**Preparación:** ASG-T02, CAL-T03, F05-T02; runner frontend por decidir.  
**Pasos:** (1) RED de búsqueda/listado, duplicados, formulario y desasignación; (2) GREEN de selector/editor/tarjetas; (3) TRIANGULATE de texto idéntico, receta ausente y modal/tooltip; (4) REFACTOR de estado efímero en store.  
**Pruebas esperadas:** modal no muta; tooltip responde a puntero/foco/táctil; texto se presenta como texto.  
**DoD:** UI delega accesibilidad/responsive a F05 y conserva contrato backend.  
**Evidencia requerida:** runner frontend seleccionado, pruebas de componente/estado y pytest sin regresiones.  
**Estimación:** 1 jornada.
