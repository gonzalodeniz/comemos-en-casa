# F01 — Catálogo de recetas

**Estado:** APPROVED  
**Versión:** 0.1  
**Procedencia histórica:** migración del cambio `recetas-publicas-privadas`; el contenido original permanece en el historial Git.

## Contexto

El calendario necesita un propietario de la identidad de receta y de los valores públicos actuales que consulta. Esta feature define esa fundación sin convertirla en un producto completo de gestión de recetas. La [visión de producto](../../../01-vision-producto.md) establece que el catálogo es público: no existen recetas privadas ni visibilidad restringida.

## Alcance y no alcance

Incluye la identidad canónica de receta, los datos mínimos públicos de título, portada y detalle, su normalización y validación, lecturas públicas actuales, y la compatibilidad de migración con el calendario.

No incluye gestión autenticada, usuarios, hogares, propiedad, permisos, visibilidad, colecciones, favoritos, contenido enriquecido, publicación, interfaz, rutas HTTP ni la migración de referencia del calendario.

## Actores

- **Persona consultora:** consume el catálogo público cuando una interfaz futura lo exponga.
- **Consumidor de calendario:** busca y consulta recetas públicas mediante el contrato fundacional.
- **Operador de migraciones:** aplica las migraciones en el orden documentado.

## Historias y criterios de aceptación

### US-REC-001 — Disponer de una identidad de receta interoperable

Como consumidor de calendario, quiero una identidad de receta estable para poder referenciar recetas sin que el calendario posea su almacenamiento.

- **CA-REC-001:** al aplicar la migración del catálogo sobre una base PostgreSQL soportada sin tablas de calendario, existe una única relación `recipes` con `id` UUID como clave primaria.
- **CA-REC-002:** la migración es aditiva, versionada y no crea, altera ni referencia `meal_assignments`.

### US-REC-002 — Representar una receta pública mínima

Como consumidor del catálogo, quiero obtener título, portada y detalle actuales de una receta pública.

- **CA-REC-003:** una receta válida ofrece `id`, título, URL de imagen y detalle como datos públicos fundacionales.
- **CA-REC-004:** una actualización ordinaria de esos valores conserva el mismo UUID y las lecturas posteriores devuelven los valores actuales.

### US-REC-003 — Encontrar y consultar recetas públicas

Como consumidor de calendario, quiero buscar por título y consultar detalle por identidad.

- **CA-REC-005:** la búsqueda de título normalizado no distingue mayúsculas, minúsculas ni acentos; `tortilla espanola` incluye `Tortilla Española`.
- **CA-REC-006:** una consulta por identidad existente devuelve exactamente `id`, título, URL de imagen y detalle actuales; valores históricos de una asignación no forman parte del resultado.

### US-REC-004 — Mantener asignaciones al retirar una receta

Como persona planificadora, quiero que una receta retirada no elimine una asignación existente.

- **CA-REC-007:** cuando el calendario haya añadido su futura referencia `meal_assignments.recipe_id REFERENCES recipes(id) ON DELETE SET NULL`, borrar la receta conserva la asignación y deja su `recipe_id` en `NULL`.

## Reglas

- **RD-REC-001:** el catálogo es el único propietario de `recipes(id)`; `id` es UUID, se asigna al crear la receta y no cambia en actualizaciones ordinarias.
- **RD-REC-002:** cada receta fundacional pública tiene título, URL de imagen y detalle; extensiones futuras del catálogo son únicamente aditivas.
- **RD-REC-003:** antes de validar, texto y detalle se normalizan a NFC; se recortan sus extremos; el título colapsa espacios internos y el detalle convierte CRLF y CR en LF.
- **RD-REC-004:** el título normalizado tiene entre 1 y 200 puntos de código Unicode; el detalle, entre 1 y 10.000; la URL de imagen, entre 1 y 2.048 caracteres y es una URL absoluta `http` o `https`.
- **RD-REC-005:** se rechaza cualquier valor que incumpla RD-REC-003 o RD-REC-004; los valores aceptados se exponen normalizados.
- **RD-REC-006:** la búsqueda usa títulos normalizados sin distinción de caso ni acentos y las lecturas devuelven valores actuales del catálogo, nunca snapshots de `meal_assignments`.
- **RD-REC-007:** la migración del catálogo es independiente del calendario y debe aplicarse antes de la migración de calendario que cree su clave foránea; esa clave foránea no redefine `recipes`.
- **RD-REC-008:** la fundación permite el borrado de una receta sin definir una clave foránea de calendario; la semántica `ON DELETE SET NULL` pertenece a la migración posterior propiedad del calendario.
- **RD-REC-009:** todas las recetas del catálogo son públicas; no se modela ni se implementa visibilidad privada o restringida.

## Modelo conceptual

**Receta pública**: identidad UUID estable, título, URL de imagen y detalle actuales.  
**Clave de búsqueda**: representación normalizada interna del título para búsqueda sin caso ni acentos; no pertenece al contrato de lectura público.  
**Asignación tombstone**: asignación de calendario conservada cuya referencia queda nula después de borrar su receta.

## Interfaces

- **Búsqueda pública:** recibe un título y devuelve elementos con `id`, título y URL de imagen actuales.
- **Detalle público por identidad:** recibe un UUID y devuelve `id`, título, URL de imagen y detalle actuales cuando existe.
- **Referencia diferida del calendario:** el calendario podrá referenciar `recipes(id)` solo después de la migración del catálogo y con la semántica de RD-REC-008.

No se define protocolo HTTP, interfaz de usuario ni operaciones de gestión en esta feature.

## Requisitos no funcionales

- La migración es expand-only y puede aplicarse sin tablas de calendario.
- La identidad se mantiene estable entre lecturas y actualizaciones ordinarias.
- La normalización preserva una representación Unicode canónica y resultados de búsqueda consistentes para los títulos equivalentes definidos por RD-REC-006.
- Las comprobaciones deben cubrir migración, normalización, validación, lecturas actuales, identidad estable y compatibilidad de tombstone sin exigir implementar la integración de calendario.

## Supuestos y decisiones pendientes

- Se asume PostgreSQL como persistencia y Python como backend, conforme al contexto de la fuente.
- Se asume que una futura gestión autenticada decidirá quién puede modificar recetas, pero no podrá introducir visibilidad privada.
- Está pendiente especificar la gestión completa, el contenido enriquecido y cualquier protocolo o interfaz de usuario; no se infieren en esta feature.
- La estrategia concreta de repositorio, driver y almacenamiento se decidirá en el PLAN sin modificar estos requisitos.

## Dependencias

- La [visión de producto](../../../01-vision-producto.md) es la fuente de la regla de catálogo exclusivamente público.
- [R1 — Calendario de comidas](../../R1-calendario-de-comidas/README.md) consume la identidad y lecturas definidas aquí; su migración de referencia permanece fuera de esta feature.
- La futura autenticación es dependencia de la gestión, no de las lecturas públicas fundacionales.

## Riesgos

- Un modelo mínimo puede requerir migraciones aditivas para contenido de receta posterior.
- Aplicar primero la clave foránea del calendario fallará si no existe `recipes`; el orden de RD-REC-007 es obligatorio.
- Copiar título o portada en asignaciones generaría datos obsoletos y contradice RD-REC-006.
- Añadir propiedad o visibilidad en esta fundación introduciría una capacidad prohibida por la visión de producto.

## Glosario

- **Catálogo público:** conjunto de recetas consultables sin visibilidad privada o restringida.
- **Portada:** URL de imagen actual de una receta.
- **Tombstone:** asignación que se conserva tras borrar la receta y queda sin referencia.
- **Expand-only:** migración que añade estructura sin una degradación destructiva automática.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | SPEC creada en DRAFT desde la fuente OpenSpec. |
| 0.1 | 2026-09-16 | Aprobada por la persona usuaria. |
