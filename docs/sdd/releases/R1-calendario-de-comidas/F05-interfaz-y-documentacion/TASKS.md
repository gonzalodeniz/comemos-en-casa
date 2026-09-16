# TASKS — F05 Interfaz y documentación

**Estado:** DRAFT · **Versión:** 0.1  
**Bases aprobadas:** [`SPEC.md`](SPEC.md) v0.1 (`APPROVED`, aprobada 2026-09-16) y [`PLAN.md`](PLAN.md) v0.1 (`APPROVED`, aprobado por la persona usuaria 2026-09-16).  
**Entrega:** PR 4 y PR 5; requiere estrategia de PR encadenadas antes de implementar. **Pruebas:** usar `pytest`, ya configurado; las pruebas frontend requieren un runner aún no seleccionado.

## Secuencia y checklist

- [ ] INT-T01 — Shell, grid y estados de semana (PR 4; depende de CAL-T02 y ACC-T03).
- [ ] INT-T02 — Edición, feedback y contexto accesible (PR 4; depende de INT-T01 y ASG-T02).
- [ ] INT-T03 — Resiliencia visual, accesibilidad y responsive (PR 5; depende de INT-T02 y PER-T03).
- [ ] INT-T04 — Documentación contractual y aceptación (PR 5; depende de CAL-T03, ASG-T03, INT-T03).

## INT-T01 — Shell, grid y estados de semana

**Entrega/estado:** PR 4, pendiente. **Trazabilidad:** PLAN §Hitos 1, §Arquitectura, §Pruebas; US-INT-001; CA-INT-001…003; RD-INT-001…003.  
**Preparación:** CAL-T02, ACC-T03 y runner frontend seleccionado; puntos de trabajo feature de calendario, ruta/shell y estilos.  
**Pasos:** (1) RED de bootstrap, guest banner, skeleton, navegación tokenizada y grid lunes-domingo; (2) GREEN de shell/store/grid; (3) TRIANGULATE de datos obsoletos inertes, respuestas fuera de orden y celdas densas; (4) REFACTOR de estados y capas sticky.  
**Pruebas esperadas:** `aria-busy`, skeleton decorativo, datos previos inaccesibles y banner previo a semana.  
**DoD:** una sola grid conserva orden lógico y estado de F01/F03/F04 sin contratos nuevos.  
**Evidencia requerida:** salida del runner frontend, capturas o revisión de viewport móvil/escritorio y `.venv/bin/pytest -q`.  
**Estimación:** 1 jornada.

## INT-T02 — Edición, feedback y contexto accesible

**Entrega/estado:** PR 4, pendiente. **Trazabilidad:** PLAN §Hitos 2, §Datos e interfaces, §Pruebas; US-INT-002; CA-INT-004…006; RD-INT-004…005; referencias F02 y F03.  
**Preparación:** INT-T01, ASG-T02; editor, feedback, modal, tooltip y store; no duplicar texto contractual de F03/F04.  
**Pasos:** (1) RED de Guardar/blur, revisiones, toasts, modal, tooltip, foco y errores de campo; (2) GREEN de controles/live regions; (3) TRIANGULATE de cambio durante guardado, navegación en espera y retorno de scroll/foco; (4) REFACTOR de temporizadores/descriptores de fallo.  
**Pruebas esperadas:** una solicitud en vuelo por revisión, Guardado dos segundos, modal solo consulta, tooltip sin acciones y teclado completo.  
**DoD:** feedback aislado por operación y accesibilidad cumple contratos referenciados.  
**Evidencia requerida:** pruebas frontend focalizadas, matriz teclado/puntero/táctil y pytest backend sin regresiones.  
**Estimación:** 1 jornada.

## INT-T03 — Resiliencia visual, accesibilidad y responsive

**Entrega/estado:** PR 5, pendiente. **Trazabilidad:** PLAN §Hitos 3, §Pruebas, §Despliegue; US-INT-001…002; CA-INT-001…008; RD-INT-001…005.  
**Preparación:** INT-T02, PER-T03; componentes Feedback/Modal/Tooltip/Grid y estilos.  
**Pasos:** (1) RED de borrador fallido, reintento aislado/cancelación, 429/503, receta ausente, overlay y foco; (2) GREEN de representación; (3) TRIANGULATE de Escape, lector, mobile touch, scroll y guest on/off; (4) REFACTOR de helpers de feedback/breakpoint/a11y.  
**Pruebas esperadas:** celdas con overflow vertical, scroll horizontal móvil, objetivos 44×44 CSS px y regiones live no duplicadas.  
**DoD:** estados de fallo/carga y aceptación responsive/accesible verificables sin controles fuera de alcance.  
**Evidencia requerida:** suite frontend, pruebas de contrato API, revisión manual teclado/lector/táctil y viewports.  
**Estimación:** 1 jornada.

## INT-T04 — Documentación contractual y aceptación

**Entrega/estado:** PR 5, pendiente. **Trazabilidad:** PLAN §Hitos 4, §Datos e interfaces, §Pruebas; US-INT-003; CA-INT-007…008; RD-INT-001…005; contratos F01–F04.  
**Preparación:** contratos implementados de F01–F04; destinos `docs/calendario-de-comidas/uso.md`, `docs/calendario-de-comidas/interfaz.md`, `docs/interfaces/calendario-de-comidas.openapi.yaml`.  
**Pasos:** (1) RED de validación/inspección contra API; (2) GREEN de uso, interfaz y OpenAPI sin añadir requisitos; (3) TRIANGULATE de rutas, esquemas, errores, headers, textos y límite #6/riesgo guest; (4) REFACTOR terminológico y de ejemplos.  
**Pruebas esperadas:** OpenAPI coincide con respuestas reales; documentación no afirma setup ni login, privacidad, CAPTCHA o alcance excluido.  
**DoD:** tres documentos coherentes con contratos finales y aceptación transversal registrada.  
**Evidencia requerida:** validador OpenAPI/contrato usado, diff documental, suites aplicables y checklist manual final RED/GREEN/TRIANGULATE/REFACTOR.  
**Estimación:** 1 jornada.
