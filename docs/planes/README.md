# Planes y tareas

- `docs/planes/`: propuestas de alcance y criterios de aceptación. Un plan puede quedar pendiente de aprobación; [arquitectura-base](arquitectura-base.md) ya está aprobado, pero mover un plan aquí **no** lo aprueba ni inicia su ejecución.
- `odd/tasks/`: documentos de tareas de ejecución, uno por iniciativa que requiera seguimiento. Se crean tras aprobar el plan y solicitar expresamente las tareas o autorizar la implementación, enlazando el plan aprobado; generar tareas no autoriza por sí solo ejecutarlas. No duplican aquí el texto del plan. Por petición expresa del usuario puede prepararse un borrador TASKS antes de aprobar el plan; en ese caso ambos mantienen su aprobación pendiente y no se inicia la implementación.

Las historias de usuario y decisiones de producto permanecen en `docs/`. La arquitectura tiene un [documento de tareas](../../odd/tasks/architecture-foundation.md); sus tareas y evidencias se registran allí durante la ejecución.

## Planes disponibles

- [Base del proyecto y persistencia](arquitectura-base.md): aprobado e implementado.
- [HU-001 — Gestión de usuarios y acceso](hu-001-gestion-de-usuarios.md): plan y [TASKS](../../odd/tasks/hu-001-gestion-de-usuarios.md) aprobados; T1–T3 y T5 completadas, T4/T6–T8 pendientes.
- [HU-002 — Planificación de comidas](hu-002-planificacion-de-comidas.md): propuesta pendiente de aprobación; incorpora las aclaraciones confirmadas sobre fecha final inclusiva, inicio el 29 de febrero y edición de fechas pasadas. La historia ya recoge las aclaraciones y el [borrador TASKS](../../odd/tasks/hu-002-planificacion-de-comidas.md) se creó por petición expresa del usuario; plan y tareas siguen pendientes de aprobación y no autorizan implementación.
