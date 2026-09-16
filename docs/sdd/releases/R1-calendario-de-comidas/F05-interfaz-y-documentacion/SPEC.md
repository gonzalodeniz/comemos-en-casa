# F05 — Interfaz y documentación

**Estado:** APPROVED · **Versión:** 0.1 · **Procedencia histórica:** cambio `calendario-de-comidas`, preservado en el historial Git.

## Contexto

Esta feature presenta de forma usable los comportamientos canonizados por F01–F04 y exige su documentación. No redefine reglas funcionales de calendario, asignaciones, resiliencia ni acceso.

## Alcance y no alcance

Incluye responsive, accesibilidad, estados visuales y documentación de uso/interfaz/contrato. No incluye controles fuera del alcance común del release ni distinción pública/privada de recetas.

## Actores

- Persona que usa teclado, puntero, táctil o tecnología de asistencia.
- Persona que consulta la documentación de uso y contrato.

## Historias y criterios de aceptación

### US-INT-001 — Usar la cuadrícula en cualquier viewport
Como persona planificadora, quiero usar la semana completa en escritorio y móvil.

- **CA-INT-001:** en móvil la cuadrícula mantiene siete días mediante scroll horizontal sincronizado, con columna Comida/Cena fija.
- **CA-INT-002:** tarjetas se apilan y una celda densa permite recorrido vertical; contenido y feedback siguen utilizables.

### US-INT-002 — Recibir interacción accesible
Como persona usuaria, quiero operar y entender todos los estados.

- **CA-INT-003:** controles tienen nombre accesible, foco visible y operación por teclado y pulsación.
- **CA-INT-004:** `Guardando`, `Guardado`, validaciones y toasts se anuncian a tecnologías de asistencia sin duplicar mensajes.
- **CA-INT-005:** modal mueve foco al abrir, admite Escape y devuelve foco al disparador al cerrar.

### US-INT-003 — Consultar especificaciones de uso
Como persona usuaria o equipo, quiero documentación verificable del calendario.

- **CA-INT-006:** la especificación de interfaz cubre estructura, controles, carga, edición, feedback, banner guest, modal, tooltip, accesibilidad y responsive, incluidos textos exactos definidos en F03/F04.
- **CA-INT-007:** la guía de uso explica consultar/navegar, añadir recetas o texto, editar/desasignar, guardar, estados/errores y riesgo guest.
- **CA-INT-008:** la guía indica que `ENABLE_GUEST_USER=false` y reinicio deshabilitan guest, sin afirmar que borren datos existentes.

## Reglas

- **RD-INT-001:** skeleton es decorativo; durante carga el grid usa `aria-busy=true` y los datos previos son inertes/ocultos a asistencia.
- **RD-INT-002:** errores de campo usan `aria-invalid` y `aria-describedby`; acciones de toast son alcanzables con teclado.
- **RD-INT-003:** el modal es diálogo con título, foco inicial y trampa de foco; no incorpora acciones prohibidas por F02.
- **RD-INT-004:** tooltip de texto libre muestra contenido saneado, se activa en hover/foco/pulsación, expone `aria-describedby` y no contiene acciones.
- **RD-INT-005:** los artefactos obligatorios de entrega son `docs/calendario-de-comidas/uso.md`, `docs/calendario-de-comidas/interfaz.md` y `docs/interfaces/calendario-de-comidas.openapi.yaml`.

## Modelo conceptual

`VistaSemanal` contiene banner, navegación, grid y feedback. Sus estados son bootstrap, carga inicial, lista, navegación y fallo de lectura; la semántica de cada estado procede de F03. `Modal` y `Tooltip` conservan contexto efímero, sin alterar datos.

## Interfaces

La especificación OpenAPI documentará los recursos de F01–F04, sus esquemas de error y headers de rate limit. Los textos exactos de banner y rate limit se referencian en **CA-ACC-007** y **CA-ACC-010**; el de base de datos, en **CA-PER-009**.

## RNF

Se usa orden DOM lógico, encabezados asociados a celdas y objetivos táctiles recomendados de 44×44 CSS px. Escritorio y móvil deben revisarse con carga, contenido denso, modal, tooltip, errores y modo guest.

## Supuestos, dependencias y riesgos

- Depende de F01–F04; no puede documentar comportamientos aún no definidos por esas SPEC.
- Riesgo: scroll horizontal reduce contexto visible en móvil; la columna fija y encabezado sincronizado lo mitigan sin cambiar la cuadrícula semanal.
- Decisión pendiente: la elección de framework y herramienta automática de accesibilidad queda para planificación, sin alterar estos criterios.

## Glosario

- **Skeleton:** representación temporal de estructura durante carga, no contenido.
- **Feedback:** anuncio visual y accesible del resultado de una operación.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | SPEC aprobada por la persona usuaria. |
