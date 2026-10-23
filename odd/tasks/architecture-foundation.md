# Architecture foundation — execution tasks
Objective: Implement the approved [architecture foundation plan](../../docs/planes/arquitectura-base.md) on `feat/architecture-foundation`; HU-001 and HU-002 remain out of scope.
Delivery: ask-on-risk; estimated ~400–600 authored lines, split into reviewable work-unit commits. Checks: pytest, frontend checks, isolated PostgreSQL integration, Docker Compose when available.

## Specs

S1. User request (verbatim): «crea una nueva rama para la implementación de la arquitectura; crea un plan para la implementación y espera mi aprobación.» The branch exists; the plan linked above is the approved scope.
S2. User approval and current request (verbatim): «aprobado el plan. genera los ficheros de tareas».
S3. Approved plan, unit 1 (verbatim): «Proyecto React + TypeScript con Vite y API FastAPI con una respuesta de salud básica; comandos de desarrollo y pruebas mínimas de arranque.» Check: frontend/backend start and focused checks pass.
S4. Approved plan, unit 2 (verbatim): «PostgreSQL en Compose con volumen persistente; configuración por variables de entorno sin secretos en el repositorio; API conectada a la base y comprobación de disponibilidad; migraciones versionadas con una revisión inicial sin tablas de negocio.» Check: connection failure is reflected in readiness, baseline revision is recorded, and no business tables are created.
S5. Approved plan, unit 3 (verbatim): «Prueba de integración contra una base aislada para confirmar conexión y versión de migración; verificación de persistencia tras reiniciar servicios sin borrar volúmenes; instrucciones para configurar, arrancar, migrar y ejecutar pruebas.» Check: isolated integration check and documented local restart demonstrate persistence.
S6. Approved plan, boundary (verbatim): «Quedan fuera de esta etapa la implementación de HU-001, HU-002, la carga de etiquetas predeterminadas, el correo, el despliegue remoto y las copias de seguridad.» Check: no feature implementation or unapproved delivery is included.

## Tasks

T1 | S3,S6 | inline | pending | commit: pending — scaffold FastAPI and Vite/React TypeScript with smoke tests; document start commands alongside behavior.
T2 | S4,S6 | inline | pending | commit: pending — wire PostgreSQL and Docker Compose, environment example, readiness and versioned baseline migration; prove failure path and migration state.
T3 | S5,S6 | inline | pending | commit: pending — add isolated integration checks, verify persistence without deleting volumes, complete reproducible startup/test documentation and final checks.

## Log

L1. Original user request (verbatim): «crea una nueva rama para la implementación de la arquitectura; crea un plan para la implementación y espera mi aprobación.»
L2. Later user request (verbatim): «organiza los ficheros de plan y tasks de algún modo coherente».
L3. Approval and task-file request (verbatim): «aprobado el plan. genera los ficheros de tareas».
L4. Evidence: `feat/architecture-foundation` branches from `96e0e7f`. The plan is approved; T1–T3 are not implemented or checked. The current request generates task artifacts, not source code.
