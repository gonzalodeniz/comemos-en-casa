# TASKS — F01 Calendario semanal

**Estado:** DRAFT · **Versión:** 0.1  
**Bases aprobadas:** [`SPEC.md`](SPEC.md) v0.1 (`APPROVED`, aprobada 2026-09-16) y [`PLAN.md`](PLAN.md) v0.1 (`APPROVED`, aprobado por la persona usuaria 2026-09-16).  
**Entrega:** PR 1 (fundación completada), PR 2B y PR 4; requiere estrategia de PR encadenadas antes de implementar. **Pruebas:** TDD estricto con `pytest`: RED → GREEN → TRIANGULATE → REFACTOR; no crear setup duplicado.

## Secuencia y checklist

- [x] CAL-T01 — Reglas temporales Canary y semana válida (PR 1; completada).
- [ ] CAL-T02 — Contexto y lectura semanal HTTP (PR 2B; depende de PER-T02, ACC-T03).
- [ ] CAL-T03 — Navegación y entradas de alta (PR 4; depende de CAL-T02, F02 y F05).

## CAL-T01 — Reglas temporales Canary y semana válida

**Entrega/estado:** PR 1, completada. **Trazabilidad:** PLAN §Hitos 1, §Datos e interfaces, §Pruebas; US-CAL-001…002; CA-CAL-001…004; RD-CAL-001…004.  
**Preparación:** frontera `meal_calendar`, `test_time_text.py` y evidencia PR1; F03-T01 como base de esquema.  
**Pasos realizados:** RED de cálculo/validación; GREEN de funciones puras y zona inyectable; TRIANGULATE de medianoche, año y DST; REFACTOR de constantes.  
**Pruebas esperadas:** lunes-domingo ISO, rechazo de no-lunes y desplazamiento por siete días de calendario.  
**DoD:** cálculo backend canario comprobado sin timestamps de navegador.  
**Evidencia:** `apply-progress.md` registra las pruebas de Canary y `.venv/bin/pytest -q` con 16 passed.
**Estimación:** 1 jornada (histórica; completada).

## CAL-T02 — Contexto y lectura semanal HTTP

**Entrega/estado:** PR 2B, pendiente. **Trazabilidad:** PLAN §Hitos 2, §Datos e interfaces, §Pruebas; US-CAL-001…002; CA-CAL-001…004; RD-CAL-001…005.  
**Preparación:** PER-T02, ACC-T03; `api.py`, registro de rutas y `test_api_contract.py`; el framework HTTP se descubre sin cambiar contratos.  
**Pasos:** (1) RED de `/context`, semana Monday-only, JSON UTF-8/no-store y sobre de error; (2) GREEN de rutas contra repositorio; (3) TRIANGULATE de orden de asignaciones, rango y errores; (4) REFACTOR de traducción HTTP separada de SQL.  
**Pruebas esperadas:** contexto devuelve zona/inicio/guestMode; lectura devuelve semana inclusiva y asignaciones ordenadas; fecha no lunes rechazada.  
**DoD:** rutas leen exclusivamente contratos de F03/F04 y no introducen semántica de asignación.  
**Evidencia requerida:** RED/GREEN, pytest API/repositorio/PR1, cuerpos y headers de contrato.  
**Estimación:** 1 jornada.

## CAL-T03 — Navegación y entradas de alta

**Entrega/estado:** PR 4, pendiente. **Trazabilidad:** PLAN §Hitos 3, §Pruebas; US-CAL-002…003; CA-CAL-003…006; RD-CAL-003…005.  
**Preparación:** CAL-T02, F02-T02 y F05-T01; runner frontend pendiente de selección, por lo que la ejecución de esas pruebas queda bloqueada por esa decisión, no omitida.  
**Pasos:** (1) RED de Anterior/Siguiente/Hoy, token contra respuesta obsoleta y preselección global/celda; (2) GREEN de estado y composición; (3) TRIANGULATE de navegación durante carga/guardado y domingo/cena; (4) REFACTOR de tokens/fechas fuera de componentes.  
**Pruebas esperadas:** Hoy reconsulta contexto; cada celda preselecciona fecha+turno; navegación no bloquea controles.  
**DoD:** interacción cumple F01 y delega edición a F02 y estados visuales a F05.  
**Evidencia requerida:** comando del runner frontend seleccionado, resultados de casos de estado y `.venv/bin/pytest -q` sin regresiones.  
**Estimación:** 1 jornada.
