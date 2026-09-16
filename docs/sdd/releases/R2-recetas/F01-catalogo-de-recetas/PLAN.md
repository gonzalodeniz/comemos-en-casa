# PLAN — F01 Catálogo de recetas

**Estado:** APPROVED · **Versión:** 0.1  
**SPEC base:** [`SPEC.md`](SPEC.md) v0.1, estado `APPROVED`, aprobada por la persona usuaria el 2026-09-16.  
**Dependencia consumidora:** [R1/F02 — Asignaciones de comida](../../R1-calendario-de-comidas/F02-asignaciones-de-comida/PLAN.md).  
**Cubre:** US-REC-001…004; CA-REC-001…007; RD-REC-001…009.

## Arquitectura

La feature entrega el propietario de `recipes(id)` mediante una migración SQL versionada, aditiva e independiente del calendario. Un límite Python de esquema/dominio crea o conserva UUID y normaliza/valida los valores de fundación; un repositorio síncrono recibe una conexión PostgreSQL abierta del consumidor y concentra las lecturas y escrituras necesarias. El consumidor conserva la propiedad de transacciones, reintentos y ciclo de vida de conexión.

No se añade framework web, ORM, rutas HTTP, UI, autenticación ni modelo de visibilidad. La gestión autenticada queda para una feature posterior y no podrá crear recetas privadas.

## Hitos

1. Crear la migración de catálogo y documentar que precede a cualquier clave foránea de calendario (RD-REC-001, RD-REC-007, RD-REC-008).
2. Implementar el límite de esquema/dominio para identidad estable y datos públicos normalizados (RD-REC-001…005).
3. Implementar el repositorio de catálogo para búsqueda literal y lectura actual por identidad (RD-REC-006).
4. Verificar compatibilidad de borrado en un esquema aislado con la futura FK propiedad de R1, sin modificar el calendario (CA-REC-007).

## Datos e interfaces

La migración crea `recipes` con UUID primario, título, URL de imagen, detalle y una clave de búsqueda interna derivada. La clave no forma parte de las lecturas públicas; se indexa para búsqueda por subcadena sin distinción de caso ni acentos. Las escrituras actualizan título y clave en la misma operación y nunca actualizan `id`.

El adaptador expone solo las dos lecturas de [`SPEC.md`](SPEC.md#interfaces): búsqueda por título y detalle por UUID. Devuelve los campos indicados por la SPEC y valores actuales del catálogo; no lee ni conserva snapshots de asignaciones. Las consultas de búsqueda establecen orden determinista y tratan los caracteres comodín como literales. La semántica exacta de normalización, validación y tombstone se mantiene en RD-REC-003…008.

## Seguridad y observabilidad

El repositorio usa SQL parametrizado y no asume autorización: esta fundación tiene datos públicos y no ofrece mutaciones expuestas. Se registrarán fallos de validación, consultas por UUID inexistente y errores de persistencia con identificadores técnicos mínimos, sin valores completos de receta. La instrumentación concreta y su destino quedan pendientes.

## Pruebas

Cubrir migración independiente y expand-only, forma de tabla e índice, UUID estable, normalización Unicode, límites, URL absoluta HTTP(S), búsqueda sin caso/acentos, lecturas de valores actuales y consultas inexistentes. Una prueba PostgreSQL aislada incorporará la futura FK `ON DELETE SET NULL` para demostrar CA-REC-007 sin implementar ni migrar R1.

## Despliegue e infraestructura

La infraestructura mínima es PostgreSQL con `pg_trgm` para el índice de búsqueda y Psycopg 3 como dependencia del adaptador. Aplicar primero esta migración de catálogo; solo después R1 puede publicar su migración de `meal_assignments.recipe_id REFERENCES recipes(id) ON DELETE SET NULL`. El despliegue no habilita endpoint, interfaz ni gestión de recetas.

## Riesgos y decisiones pendientes

- El esquema mínimo puede necesitar extensiones aditivas cuando se especifique contenido enriquecido o gestión; no se anticipan campos.
- La dependencia de `pg_trgm` debe verificarse en todos los entornos PostgreSQL soportados.
- Aplicar la FK de R1 antes de esta migración falla; el orden del hito 1 es obligatorio.
- Siguen pendientes la política de gestión autenticada, el contenido de receta, cualquier protocolo/UI y el destino de observabilidad. Ninguna decisión pendiente habilita privacidad de recetas.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | PLAN creado en DRAFT a partir de SPEC v0.1 aprobada. |
| 0.1 | 2026-09-16 | PLAN aprobado por la persona usuaria. |
