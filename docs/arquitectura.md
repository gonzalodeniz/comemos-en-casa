# Arquitectura inicial — Comemos en casa

La aplicación utiliza **React y TypeScript** para la interfaz, **FastAPI (Python)** para la API y **PostgreSQL** para los datos persistentes, en un entorno **local con Docker Compose**. La base técnica está implementada; las responsabilidades funcionales descritas a continuación siguen siendo el objetivo de HU-001 y HU-002, todavía pendientes.

## Componentes y responsabilidades

```text
Navegador → React (TypeScript) → API FastAPI (Python) → PostgreSQL
                            Docker Compose (entorno local)
```

| Componente | Responsabilidad |
| --- | --- |
| React + TypeScript | Presentar formularios y vistas de la aplicación y comunicarse con la API. |
| FastAPI + Python | Aplicar las reglas de negocio, validar operaciones y controlar el acceso en el servidor. |
| PostgreSQL | Persistir usuarios, etiquetas alimentarias y asignaciones de comidas con integridad relacional. |
| Docker Compose | Levantar los servicios necesarios para trabajar localmente y conservar los datos de PostgreSQL entre reinicios mediante almacenamiento persistente. |

## Persistencia y alcance inicial

- La base incorpora **SQLAlchemy** para el acceso a datos, **psycopg** como controlador PostgreSQL y **Alembic** para migraciones versionadas. La revisión `0001_baseline` registra la versión sin crear tablas de negocio; los modelos y restricciones funcionales llegarán con cada historia.
- Las operaciones que afecten varias asignaciones de comidas deberán ser transaccionales, según [HU-002](historias-usuarios/HU-002-planificacion-de-comidas.md). La unicidad de correo y de fecha/franja se garantizará en la base de datos, además de las validaciones de la API.
- Las [etiquetas predeterminadas](etiquetas-predeterminadas.md) estarán disponibles para la planificación. La creación y edición de etiquetas por usuarios queda fuera de esta etapa.
- La autenticación y el control de sesiones de [HU-001](historias-usuarios/HU-001-gestion-de-usuarios.md) deben verificarse en la API, no solo en la interfaz.

## Estado y orden de implementación

1. **Completado:** estructura React/TypeScript con Vite, API FastAPI con `/health` y `/ready`, PostgreSQL con volumen persistente y migración inicial. Compose publica frontend y API únicamente en `127.0.0.1`; PostgreSQL no publica un puerto al host. Las pruebas utilizan pytest y Vitest.
2. **Pendiente:** gestión de usuarios y acceso ([HU-001](historias-usuarios/HU-001-gestion-de-usuarios.md)); su [plan de implementación](planes/hu-001-gestion-de-usuarios.md) está aprobado y dispone de [tareas aprobadas y pendientes](../odd/tasks/hu-001-gestion-de-usuarios.md); la implementación no ha comenzado.
3. **Pendiente:** carga del catálogo de etiquetas predeterminadas y planificación de comidas (HU-002).

El [plan de la base](planes/arquitectura-base.md) y su [documento de tareas](../odd/tasks/architecture-foundation.md) recogen el alcance completado y las evidencias de pruebas, migración y persistencia tras reinicio. El [README](../README.md) contiene las instrucciones reproducibles. La interfaz actual solo muestra el título de la aplicación; aún no hay cuentas, sesiones, correo, etiquetas ni asignaciones.

El despliegue remoto y el mecanismo de copias de seguridad siguen sin definirse. Las decisiones de autenticación, sesiones y correo se concretarán para HU-001; no forman parte de la base ejecutada.
