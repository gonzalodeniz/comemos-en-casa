# PLAN — F05 Interfaz y documentación

**Estado:** APPROVED · **Versión:** 0.1  
**SPEC base:** [`SPEC.md`](SPEC.md) v0.1, estado `APPROVED`, aprobada por la persona usuaria el 2026-09-16.  
**Dependencias:** [F01](../F01-calendario-semanal/PLAN.md), [F02](../F02-asignaciones-de-comida/PLAN.md), [F03](../F03-persistencia-y-resiliencia/PLAN.md), [F04](../F04-acceso-guest-y-proteccion/PLAN.md).  
**Cubre:** US-INT-001…003; CA-INT-001…008; RD-INT-001…005.

## Arquitectura

Este PLAN canoniza composición visual, accesibilidad y documentación. La vista semanal usa una única CSS Grid semánticamente equivalente a tabla: columna de turnos y siete columnas de días, con encabezados asociados a celdas. En móvil el mismo contenedor desplaza horizontalmente encabezados y celdas; columna de turnos y cabecera permanecen sticky con capas opacas. F01 define las fechas, F02 las tarjetas/modal/tooltip, F03 los estados de datos y F04 el modo guest; este PLAN no altera sus contratos.

La vista representa `bootstrapping`, `initialLoading`, `ready`, `navigating` y `readFailed`. Skeleton es decorativo; grid marca `aria-busy` y datos anteriores son inertes y se ocultan a asistencia. Cada editor refleja revisiones y estados de F03, con regiones live no duplicadas. Modal y tooltip conservan contexto efímero y restauran foco/scroll conforme al contrato de F02.

## Hitos

1. Construir shell, navegación, banner reservado y grid responsive con estados de carga/navegación.
2. Implementar controles accesibles, editor, feedback, modal y tooltip conectados a F01–F04.
3. Revisar teclado, lector, táctil y viewports móvil/escritorio para todos los estados de la SPEC.
4. Redactar `docs/calendario-de-comidas/uso.md`, `docs/calendario-de-comidas/interfaz.md` y `docs/interfaces/calendario-de-comidas.openapi.yaml` a partir de los contratos finales de F01–F04.

## Datos e interfaces

- No se crean contratos funcionales nuevos: OpenAPI recopila rutas, esquemas, errores y headers definidos por F01–F04.
- La UI presenta los textos exactos de F03/F04 por referencia, sin redefinirlos.
- El modal es solo consulta, con título, foco inicial, trampa de foco, Escape y retorno al disparador; el tooltip no contiene acciones y usa `aria-describedby`.
- Errores de campo usan `aria-invalid`/`aria-describedby`; acciones de toast se operan con teclado.

## Seguridad, observabilidad e infraestructura

La interfaz no decide acceso ni valida de forma autoritativa. Evitar inyectar HTML de texto libre y no exponer datos previos inertes a tecnología de asistencia. Instrumentar de forma agregada fallos de carga, reintentos manuales y aperturas de modal/tooltip solo después de decidir producto de analítica y privacidad. Framework, librería visual, herramienta automática de accesibilidad, hosting y despliegue siguen pendientes.

## Pruebas

Tras seleccionar runner frontend, aplicar TDD estricto donde corresponda y probar: navegación con respuestas obsoletas y guardados en curso; revisiones durante guardado y temporizador; skeleton/inert; teclado, live regions, errores, toast, modal y tooltip; grid denso y scroll en móvil/escritorio; banner guest. Complementar automatización con revisión manual táctil y lector. Validar documentación contra los contratos de F01–F04 y OpenAPI contra sus respuestas/errores.

## Despliegue y riesgos

Desplegar la UI solo con endpoints compatibles ya disponibles; publicar la documentación junto con esos contratos. Riesgo: scroll horizontal reduce contexto móvil y celdas densas incrementan carga; se mitiga con columna fija, encabezado sincronizado y recorrido vertical. No se selecciona framework ni herramienta de accesibilidad hasta una decisión posterior.

## Decisiones pendientes

- Framework frontend, librería visual, runner de pruebas y automatización de accesibilidad.
- Hosting, despliegue, analítica y política de privacidad asociada.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | PLAN aprobado por la persona usuaria. |
