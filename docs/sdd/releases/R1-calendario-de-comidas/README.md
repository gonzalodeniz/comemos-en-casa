# R1 — Calendario de comidas

**Estado:** DRAFT  
**Versión:** 0.1  
**Procedencia histórica:** cambio `calendario-de-comidas`; los requisitos vigentes se canonizan en las SPEC de este release. El contenido original permanece en el historial Git.

## Propósito

Materializar el objetivo de planificación recurrente de [la visión de producto](../../01-vision-producto.md): organizar comidas y cenas sin introducir calendarios privados, autenticación propia ni funciones de compra o preparación.

## Features y orden

1. [F01 — Calendario semanal](F01-calendario-semanal/PLAN.md): semana canaria, navegación y celdas.
2. [F02 — Asignaciones de comida](F02-asignaciones-de-comida/PLAN.md): recetas públicas y texto libre.
3. [F03 — Persistencia y resiliencia](F03-persistencia-y-resiliencia/PLAN.md): datos, guardado, carga, fallos y concurrencia.
4. [F04 — Acceso guest y protección](F04-acceso-guest-y-proteccion/PLAN.md): acceso compartido, aviso y límites.
5. [F05 — Interfaz y documentación](F05-interfaz-y-documentacion/PLAN.md): adaptación responsive, accesibilidad y entregables documentales.

Las SPEC v0.1 y los PLAN v0.1 en `DRAFT` fueron aprobados por la persona usuaria el 2026-09-16. Cada feature dispone de TASKS v0.1 en `DRAFT`; requieren aprobación antes de implementar.

**Orden de implementación previsto:** F03 → F04 → F01 → F02 → F05. La numeración conserva el desglose funcional; este orden materializa sus dependencias sin redefinir los PLAN.

## Dependencias de release

- Catálogo público con identificadores estables, título, portada y detalle; la visibilidad privada de la issue #5 no forma parte de R1.
- Cuando guest esté deshabilitado, el acceso depende de la issue #6; R1 no incorpora login.
- PostgreSQL es la fuente de verdad. La futura implementación backend usará Python y pytest.

## Exclusiones comunes

No se incluyen recurrencias, copia o borrado total de semanas, limpieza automática, festivos, nutrición, cantidades, horarios, recordatorios, listas de compra, CAPTCHA, calendarios personales, roles, privacidad, historial, auditoría ni deshacer.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | Migración documental desde OpenSpec; cinco SPEC de feature en DRAFT. |
| 0.1 | 2026-09-16 | Creados cinco PLAN en DRAFT desde SPEC v0.1 aprobadas por la persona usuaria; TASKS pendiente de aprobación de PLAN. |
| 0.1 | 2026-09-16 | Aprobados los cinco PLAN y creados TASKS v0.1 en DRAFT; PR 1 histórico completado y PR 2–5 pendientes. |
