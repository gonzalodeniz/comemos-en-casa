# Planes y tareas

- `docs/planes/`: propuestas de alcance y criterios de aceptación. Un plan puede quedar pendiente de aprobación; [arquitectura-base](arquitectura-base.md) ya está aprobado, pero mover un plan aquí **no** lo aprueba ni inicia su ejecución.
- `odd/tasks/`: documentos de tareas de ejecución, uno por iniciativa que requiera seguimiento. Se crean tras aprobar el plan y solicitar expresamente las tareas o autorizar la implementación, enlazando el plan aprobado; generar tareas no autoriza por sí solo ejecutarlas. No duplican aquí el texto del plan. Por petición expresa del usuario puede prepararse un borrador TASKS antes de aprobar el plan; en ese caso ambos mantienen su aprobación pendiente y no se inicia la implementación.

Las historias de usuario y decisiones de producto permanecen en `docs/`. La arquitectura tiene un [documento de tareas](../../odd/tasks/architecture-foundation.md); sus tareas y evidencias se registran allí durante la ejecución.

## Planes disponibles

- [Base del proyecto y persistencia](arquitectura-base.md): aprobado e implementado.
- [HU-001 — Gestión de usuarios y acceso](hu-001-gestion-de-usuarios.md): plan y [TASKS](../../odd/tasks/hu-001-gestion-de-usuarios.md) aprobados; T1–T3 y T5 completadas, T4/T6–T8 pendientes.
- [HU-002 — Planificación de comidas](hu-002-planificacion-de-comidas.md): implementación autorizada; T1–T10 verificadas localmente. Los 22 escenarios pasaron en Chrome contra las rutas reales de FastAPI con SQLite temporal; una sesión limpia separada verificó bootstrap, registro sin auto-login, login explícito y logout sin usuarios/sesiones sembrados. Este recorrido no sustituye PostgreSQL ni verifica la URL publicada. T9 pasó por separado en el proyecto PostgreSQL aislado `hu002-t9-bd1hsp` (15 pruebas; concurrencia 9/9). `make test` completo pasó fuera de sandbox autorizado (61 backend/15 frontend) y `make build-frontend` pasó. Se mantienen los timeouts históricos de sandbox y la comparación controlada posterior mostró bloqueos de TestClient/AnyIO previos al trabajo de producto, sin aislar la restricción interna ni atribuir causa al producto. La historia recoge las aclaraciones y el [TASKS](../../odd/tasks/hu-002-planificacion-de-comidas.md) registra dependencias y evidencia. Sin commit ni publicación.
- [HU-003 — Gestión de comidas](hu-003-gestion-comidas.md): plan aprobado el 2026-10-29; [TASKS](../../odd/tasks/hu-003-gestion-comidas.md) creado, pendiente de aprobación y ejecución. Sin implementación autorizada.
