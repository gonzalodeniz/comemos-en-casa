# Aprobación de la documentación inicial

Se aprueban los siguientes documentos como **base documental para iniciar la implementación**. Esta aprobación no significa que las historias estén implementadas ni que sus listas de definición de terminado estén completadas.

| Documento | Alcance aprobado |
| --- | --- |
| [Visión del producto](product-vision.md) | Objetivo, público y funcionalidades previstas. |
| [Glosario](glosario.md) | Terminología común. |
| [HU-001 — Gestión de usuarios](historias-usuarios/HU-001-gestion-de-usuarios.md) | Especificación funcional; implementación pendiente. |
| [HU-002 — Planificación de comidas](historias-usuarios/HU-002-planificacion-de-comidas.md) | Especificación funcional; implementación pendiente. |
| [Etiquetas predeterminadas](etiquetas-predeterminadas.md) | Catálogo inicial; gestión de etiquetas por usuarios aplazada. |
| [Arquitectura inicial](arquitectura.md) | Stack y entorno local elegidos; base técnica implementada, funcionalidades pendientes. |

La revisión de coherencia aclaró en HU-001 que la prohibición de dejar la aplicación sin usuarios activos también se aplica a la eliminación definitiva de la última cuenta activa.

## Estado posterior de ejecución

El [plan aprobado de la base del proyecto y persistencia](planes/arquitectura-base.md) está **implementado**: React/TypeScript con Vite, FastAPI, PostgreSQL persistente, SQLAlchemy y Alembic. El [documento de tareas](../odd/tasks/architecture-foundation.md) registra las unidades completadas y las evidencias de verificación.

El usuario ha **aprobado el [plan de HU-001](planes/hu-001-gestion-de-usuarios.md) y su [documento TASKS](../odd/tasks/hu-001-gestion-de-usuarios.md)** y autorizado iniciar la implementación. T1, T2, T3 y T5 están completadas: hay persistencia y API backend para primera cuenta, sesiones, login/logout y limitación rolling de intentos, verificadas en PostgreSQL aislado. El código de T4, T6 y T7 está presente, pero sus tareas siguen abiertas hasta completar pruebas integrales; T8 también está pendiente. HU-001 no está terminada. La autorización no incluye commit de código, publicación de la rama ni PR.

Como aclaración de HU-001, el usuario confirmó una contraseña de 8 a 128 caracteres y el resto de propuestas técnicas de T1 el 24-10-2026. El mínimo de 8 caracteres prevalece como requisito del producto; su riesgo frente a autenticación de factor único se documenta en la historia y el plan.
