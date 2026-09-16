# F01 — Calendario semanal

**Estado:** APPROVED · **Versión:** 0.1 · **Procedencia histórica:** cambio `calendario-de-comidas`, preservado en el historial Git.

## Contexto

Esta feature concreta la planificación semanal de la [visión](../../../01-vision-producto.md). Las asignaciones que muestra se definen en [F02](../F02-asignaciones-de-comida/SPEC.md); su carga y persistencia, en [F03](../F03-persistencia-y-resiliencia/SPEC.md).

## Alcance y no alcance

Incluye calendario lunes–domingo, turnos Comida/Cena, navegación y puntos de alta. No incluye festivos, límites temporales, resaltado de la semana actual, recurrencias, copia o borrado de semanas.

## Actores

- Persona con acceso al calendario, guest o autenticada según [F04](../F04-acceso-guest-y-proteccion/SPEC.md).

## Historias y criterios de aceptación

### US-CAL-001 — Consultar la semana actual
Como persona con acceso, quiero abrir la semana canaria actual para planificar comidas y cenas.

- **CA-CAL-001:** se abre la semana que contiene la fecha actual en `Europe/Canary`.
- **CA-CAL-002:** el rango empieza en lunes, termina en domingo y expone siete días con Comida y Cena.

### US-CAL-002 — Navegar semanas
Como persona planificadora, quiero moverme sin límite y volver a Hoy.

- **CA-CAL-003:** anterior y siguiente permiten cualquier semana representable.
- **CA-CAL-004:** `Hoy` vuelve a consultar el contexto temporal y muestra la semana actual canaria.

### US-CAL-003 — Iniciar una asignación
Como persona planificadora, quiero añadir desde un lugar global o desde una celda.

- **CA-CAL-005:** `+ Añadir comida` permite elegir fecha y turno, incluido Cena.
- **CA-CAL-006:** cada celda inicia el flujo con su fecha y turno preseleccionados.

## Reglas

- **RD-CAL-001:** las fechas de semana y asignación usan ISO `YYYY-MM-DD`; no timestamps de navegador.
- **RD-CAL-002:** una semana válida comienza en lunes; una petición con otro día se rechaza como `invalid_week_start`.
- **RD-CAL-003:** anterior/siguiente desplazan siete días de calendario, no 168 horas.
- **RD-CAL-004:** `lunch` y `dinner` son los únicos valores de turno; se presentan como Comida y Cena.
- **RD-CAL-005:** una celda muestra todas las asignaciones sin deduplicar; su orden conjunto es el definido por **RD-ASG-002**.

## Modelo conceptual

`Semana` = `weekStart` (lunes) + siete `Día`; cada `Día` contiene dos `Celda` (`slot`) y cada celda contiene cero o más asignaciones.

## Interfaces

- `GET /api/v1/meal-calendar/context` devuelve zona horaria y `currentWeekStart`.
- `GET /api/v1/meal-calendar/weeks/{weekStart}` devuelve `weekStart`, `weekEnd`, `timezone` y `assignments[]`; exige lunes.

## RNF

El cálculo temporal se realiza en backend con zona canaria y debe ser comprobable en medianoche, cambio de año y DST. La navegación permanece disponible durante cargas; el estado visual corresponde a F03 y F05.

## Supuestos, dependencias y riesgos

- Se asume que `Europe/Canary` está disponible o se resuelve al identificador IANA compatible documentado por la plataforma.
- Depende de F03 para datos y de F04 para autorización.
- Riesgo: una pestaña abierta puede cruzar medianoche; `Hoy` mitiga la obsolescencia al pedir contexto de nuevo.

## Glosario

- **Semana actual canaria:** semana que contiene la fecha local en `Europe/Canary`.
- **Celda:** combinación de fecha y turno.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | SPEC aprobada por la persona usuaria. |
