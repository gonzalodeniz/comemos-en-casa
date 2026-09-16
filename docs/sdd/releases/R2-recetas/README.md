# R2 — Recetas

**Estado:** DRAFT  
**Versión:** 0.1  
**Procedencia histórica:** cambio `recetas-publicas-privadas`, conservado en el historial Git.

## Propósito

Establecer la fundación del catálogo público de recetas: su identidad estable, datos mínimos de lectura y orden de migración. No entrega la gestión completa de recetas.

## Feature y orden

1. [F01 — Catálogo de recetas](F01-catalogo-de-recetas/SPEC.md): SPEC y [PLAN](F01-catalogo-de-recetas/PLAN.md) `APPROVED`; [TASKS](F01-catalogo-de-recetas/TASKS.md) `DRAFT` para el contrato público fundacional y su compatibilidad de integración.

## Dependencias

- La visión de producto define que todas las recetas son públicas y prohíbe visibilidad privada o restringida.
- [R1 — Calendario de comidas](../R1-calendario-de-comidas/README.md), en particular su F02, consume la identidad y lecturas públicas del catálogo. La migración del catálogo debe existir antes de que el calendario añada su referencia a recetas; ese cambio de calendario sigue siendo propiedad de R1.
- La autenticación solo será necesaria para una futura gestión de recetas; no es dependencia de esta fundación.

## Exclusiones comunes

No incluye gestión autenticada, autorización, propiedad, hogares, recetas privadas, interfaz, rutas HTTP, colecciones, favoritos, contenido culinario enriquecido ni cambios de calendario.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | Migración documental desde OpenSpec; SPEC de F01 creada en DRAFT. |
| 0.1 | 2026-09-16 | SPEC de F01 aprobada y PLAN de F01 creado en DRAFT. |
| 0.1 | 2026-09-16 | PLAN de F01 aprobado y TASKS de F01 creadas en DRAFT. |
