# PLAN — F02 Asignaciones de comida

**Estado:** APPROVED · **Versión:** 0.1  
**SPEC base:** [`SPEC.md`](SPEC.md) v0.1, estado `APPROVED`, aprobada por la persona usuaria el 2026-09-16.  
**Dependencias:** [F01](../F01-calendario-semanal/PLAN.md), [F03](../F03-persistencia-y-resiliencia/PLAN.md), catálogo público de recetas.  
**Cubre:** US-ASG-001…003; CA-ASG-001…009; RD-ASG-001…005.

## Arquitectura

Este PLAN canoniza el modelo de asignación y la integración con el catálogo. Un servicio de calendario valida el tipo, normaliza/sanea texto libre y consulta el adaptador interno de catálogo; el repositorio de F03 persiste la relación. La API ofrece búsqueda pública paginada, detalle de receta y mutaciones de asignación bajo el prefijo de calendario.

Una asignación es polimórfica: `recipe` conserva `recipeId`; `free_text`, texto. Las consultas semanales realizan `LEFT JOIN` contra el catálogo actual para obtener título y portada: una referencia rota produce tombstone, no snapshot. El backend ordena por fecha, turno, texto visible normalizado NFKD sin marcas y `casefold`, con UUID como desempate. F03 es dueño de idempotencia, transacciones, errores y reintentos; F05 implementa selector, modal, tooltip y restauración de foco.

## Hitos

1. Definir esquemas de entrada/salida y validación de tipos, fecha, turno, UUID y texto libre.
2. Implementar adaptador de catálogo: búsqueda por título normalizado, paginación y detalle público.
3. Implementar altas, edición y desasignación, incluidos duplicados, tombstones y orden de lectura.
4. Integrar selector, formulario, tarjetas, detalle de solo consulta y tooltip mediante los contratos de F05.

## Datos e interfaces

- `POST` recibe UUID generado una vez en cliente; F03 devuelve `201`, o `200` para mismo ID/payload y `409` para un payload distinto.
- `PATCH` no permite cambiar `kind`; transformar receta/texto crea otra asignación. `DELETE` elimina solo la relación.
- La creación de receta exige una receta existente; `recipeId` nulo solo representa una receta borrada.
- Texto libre: NFC, recorte, saneado con lista permitida vacía y validación posterior de 1–100 puntos de código; se renderiza como texto, nunca HTML.
- Catálogo: `GET /recipes?q=&cursor=&limit=` busca solo título y limita `limit` a 50; `GET /recipes/{recipeId}` devuelve detalle o `404 recipe_not_found`.

## Seguridad, observabilidad e infraestructura

La autorización y cuota se aplican por F04; nunca se confía en validación de cliente. Registrar rechazos de validación, conflictos de idempotencia y referencias de receta inexistentes con identificadores técnicos mínimos. La FK, índices y retención de tombstones se diseñan en [F03](../F03-persistencia-y-resiliencia/PLAN.md). No se elige librería de sanitización: debe soportar lista permitida vacía y conservar la semántica especificada.

## Pruebas

Con `pytest` y TDD estricto ya configurados en OpenSpec: pruebas unitarias de NFC, puntos de código, saneado, normalización de búsqueda/orden y validación de `kind`; integración PostgreSQL de duplicados, FK/tombstone, lecturas actuales e idempotencia; contrato de errores y paginación. Tras seleccionar runner frontend, probar modal sin acciones de mutación, retorno de scroll/foco y tooltip por puntero, foco y táctil.

## Despliegue y riesgos

Publicar después de que F03 disponga de las tablas y antes de la UI de F05. El catálogo debe aportar `recipes(id)`, identificador estable, título, portada y detalle públicos; si se separa de PostgreSQL, requiere una estrategia explícita equivalente de tombstone antes de retirar la FK. Riesgo: normalizaciones divergentes entre cliente y backend; el orden autoritativo es del backend.

## Decisiones pendientes

- Implementación concreta del adaptador si el catálogo no comparte PostgreSQL.
- Librería de sanitización y runner frontend.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | PLAN aprobado por la persona usuaria. |
