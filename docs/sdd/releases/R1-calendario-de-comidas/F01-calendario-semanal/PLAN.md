# PLAN — F01 Calendario semanal

**Estado:** APPROVED · **Versión:** 0.1  
**SPEC base:** [`SPEC.md`](SPEC.md) v0.1, estado `APPROVED`, aprobada por la persona usuaria el 2026-09-16.  
**Dependencias:** [F03](../F03-persistencia-y-resiliencia/PLAN.md), [F04](../F04-acceso-guest-y-proteccion/PLAN.md).  
**Cubre:** US-CAL-001…003; CA-CAL-001…006; RD-CAL-001…005.

## Arquitectura

Este PLAN canoniza el contrato temporal. El backend Python calcula `currentWeekStart` desde un reloj inyectable convertido a `Europe/Canary`; el cliente solo presenta fechas ISO y solicita contexto para `Hoy`. La API expone `GET /api/v1/meal-calendar/context` y `GET /api/v1/meal-calendar/weeks/{weekStart}`; el segundo valida que el parámetro sea lunes antes de delegar la lectura a F03.

La vista mantiene `weekStart` y un token creciente de navegación. Anterior y siguiente suman/restan siete días de calendario; no calculan horas. El contenido de las celdas, su orden y la lectura se delegan respectivamente a [F02](../F02-asignaciones-de-comida/PLAN.md) y [F03](../F03-persistencia-y-resiliencia/PLAN.md). La composición responsive y accesible pertenece a [F05](../F05-interfaz-y-documentacion/PLAN.md).

## Hitos

1. Implementar funciones puras de semana canaria, validación de lunes y rango inclusivo lunes-domingo.
2. Publicar contexto y consulta semanal con el contrato JSON establecido por F03.
3. Conectar navegación, `Hoy` y entradas de alta global/contextual con el estado de F05 y el editor de F02.

## Datos e interfaces

- Las fechas de solicitud y respuesta son `YYYY-MM-DD`; no se admiten timestamps del navegador.
- La semana se consulta siempre en backend y devuelve zona, inicio, fin y asignaciones; F03 define persistencia, errores y `Cache-Control`.
- `lunch` y `dinner` son los únicos valores persistidos; la presentación usa Comida y Cena.
- Una celda conserva todas las asignaciones; F02 es dueño de su orden conjunto y semántica visual.

## Seguridad, observabilidad e infraestructura

F04 aplica autorización y límites antes de las rutas. Se registrarán de forma estructurada los parámetros inválidos de semana y fallos de consulta sin exponer datos de usuario. No se selecciona framework HTTP, frontend ni plataforma de despliegue; la decisión queda pendiente y deberá conservar estos contratos. La infraestructura PostgreSQL es de F03.

## Pruebas

Con `pytest` y TDD estricto ya configurados en OpenSpec, las entregas seguirán RED → GREEN → TRIANGULATE → REFACTOR. Se cubrirán medianoche canaria, cambio de año, DST, lunes inválido, desplazamientos por días y refresco de `Hoy`. Las pruebas de contrato verificarán el contexto y la semana. Las pruebas de UI de navegación quedan pendientes de seleccionar runner frontend, sin bloquear las pruebas Python.

## Despliegue y riesgos

Desplegar el cálculo y rutas de backend antes de habilitar la vista consumidora. Riesgos: una pestaña cruza medianoche y respuestas de navegación llegan fuera de orden; `Hoy` vuelve a pedir contexto y F05 descartará respuestas obsoletas. No se añade límite de navegación de producto.

## Decisiones pendientes

- Framework HTTP y frontend, y runner de pruebas frontend.
- Instrumentación concreta y destino de logs/métricas.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | PLAN aprobado por la persona usuaria. |
