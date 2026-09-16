# TASKS — F04 Acceso guest y protección

**Estado:** DRAFT · **Versión:** 0.1  
**Bases aprobadas:** [`SPEC.md`](SPEC.md) v0.1 (`APPROVED`, aprobada 2026-09-16) y [`PLAN.md`](PLAN.md) v0.1 (`APPROVED`, aprobado por la persona usuaria 2026-09-16).  
**Entrega:** PR 3; requiere estrategia de PR encadenadas antes de implementar. **Pruebas:** usar `pytest`, ya configurado; ejecutar las comprobaciones específicas de cada tarea.

## Secuencia y checklist

- [ ] ACC-T01 — Configuración guest y delegación a #6 (depende de PER-T01).
- [ ] ACC-T02 — Cuota atómica y fallo cerrado (depende de PER-T02; desbloquea PER-T03).
- [ ] ACC-T03 — Contrato de acceso y contexto (depende de ACC-T01 y ACC-T02; coordina F01/F05).

## ACC-T01 — Configuración guest y delegación a #6

**Entrega/estado:** PR 3, pendiente. **Trazabilidad:** PLAN §Hitos 1–2, §Datos e interfaces, §Pruebas; US-ACC-001…002; CA-ACC-001…006; RD-ACC-001…003.  
**Preparación:** `settings.py`, middleware/capa de acceso y `test_resilience_access.py`; PER-T01 disponible; no implementar login ni identidad.  
**Pasos:** (1) RED para ausencia, espacios, `true`/`false`, valores inválidos, reinicio y guest deshabilitado; (2) GREEN con parsing al arranque y delegación exclusiva a #6; (3) TRIANGULATE de visitas guest/autenticadas sobre `shared`; (4) REFACTOR de fronteras de configuración/acceso.  
**Pruebas esperadas:** valores inválidos abortan; ausencia/false exige #6 y devuelve `401 authentication_required`; guest activo no crea propiedad.  
**DoD:** configuración inmutable por proceso y límite de alcance #6 quedan verificables.  
**Evidencia requerida:** salida RED/GREEN, pytest focalizado, configuración de proceso usada y respuestas de acceso sin credenciales sensibles.  
**Estimación:** 1 jornada.

## ACC-T02 — Cuota atómica y fallo cerrado

**Entrega/estado:** PR 3, pendiente. **Trazabilidad:** PLAN §Hitos 3, §Seguridad y §Pruebas; US-ACC-003; CA-ACC-008…010; RD-ACC-004…006.  
**Preparación:** PER-T02; `rate_limit.py`, repositorio de buckets y pruebas PostgreSQL/concurrencia; no confiar en cabeceras de proxy sin configuración explícita.  
**Pasos:** (1) RED de clases read/write, 60/30, reset UTC, proxy confiable, headers, 429 y fallo de almacén; (2) GREEN con upsert condicionado previo a ruta; (3) TRIANGULATE de entradas simultáneas, reintentos internos y manuales; (4) REFACTOR de clasificación de ruta/IP y mapeo de errores.  
**Pruebas esperadas:** nunca se exceden umbrales bajo concurrencia; fallo de bucket impide operación y retorna 503; reintentos internos no consumen cuota adicional.  
**DoD:** límite PostgreSQL compartido, atómico y fail-closed con headers/Retry-After según contrato.  
**Evidencia requerida:** pytest focalizado y backend, evidencia PostgreSQL aislada/concurrente, respuesta 429/503 con headers y ciclo TDD.  
**Estimación:** 1 jornada.

## ACC-T03 — Contrato de acceso y contexto

**Entrega/estado:** PR 3, pendiente. **Trazabilidad:** PLAN §Hitos 4, §Datos e interfaces; CA-ACC-004, CA-ACC-007, CA-ACC-009…010; RD-ACC-002…006.  
**Preparación:** ACC-T01/02, endpoint de contexto F01 y banner F05.  
**Pasos:** (1) RED de `guestMode`, orden cuota→acceso→ruta y contrato de rechazo; (2) GREEN en middleware/contexto; (3) TRIANGULATE guest on/off y petición manual posterior a rate limit; (4) REFACTOR de hooks sin mezclar UI.  
**Pruebas esperadas:** `guestMode` se expone antes de la semana; el banner será responsabilidad de F05; rutas no ejecutan trabajo tras cuota fallida.  
**DoD:** contrato backend estable y consumible por F01/F05 sin controles extra.  
**Evidencia requerida:** pruebas API, pytest backend completo y matriz guest activo/inactivo.  
**Estimación:** 1 jornada.
