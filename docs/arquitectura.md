# Arquitectura inicial — Comemos en casa

La aplicación utiliza **React y TypeScript** para la interfaz, **FastAPI (Python)** para la API y **PostgreSQL** para los datos persistentes, en un entorno **local con Docker Compose**. La base técnica está implementada. HU-001 está parcialmente implementada en backend: alta inicial, autenticación, sesiones y protección frente a intentos repetidos; administración completa, recuperación por correo e interfaz siguen pendientes.

## Componentes y responsabilidades

```text
Navegador → React (TypeScript) → API FastAPI (Python) → PostgreSQL
                            Docker Compose (entorno local)
```

| Componente | Responsabilidad |
| --- | --- |
| React + TypeScript | Presentar formularios y vistas de la aplicación y comunicarse con la API. |
| FastAPI + Python | Aplicar las reglas de negocio, validar operaciones y controlar el acceso en el servidor. |
| PostgreSQL | Persistir usuarios y sesiones revocables; las tablas de etiquetas y comidas llegarán con HU-002. |
| Docker Compose | Levantar los servicios necesarios para trabajar localmente y conservar los datos de PostgreSQL entre reinicios mediante almacenamiento persistente. |

## Persistencia y alcance inicial

- La base incorpora **SQLAlchemy** para el acceso a datos, **psycopg** como controlador PostgreSQL y **Alembic** para migraciones versionadas. `0001_baseline` registra la versión inicial; `0002_user_auth` crea usuarios, sesiones, tokens de recuperación y buckets compartidos; `0003_login_attempt_events` persiste timestamps para contar fallos en una ventana móvil inclusiva de 15 minutos. Los tokens de sesión y recuperación y las claves de rate-limit se almacenan como digest, no como valores utilizables.
- Las operaciones que afecten varias asignaciones de comidas deberán ser transaccionales, según [HU-002](historias-usuarios/HU-002-planificacion-de-comidas.md). La unicidad de correo y de fecha/franja se garantizará en la base de datos, además de las validaciones de la API.
- Las [etiquetas predeterminadas](etiquetas-predeterminadas.md) estarán disponibles para la planificación. La creación y edición de etiquetas por usuarios queda fuera de esta etapa.
- La API de [HU-001](historias-usuarios/HU-001-gestion-de-usuarios.md) aplica Argon2id, sesión revocable con límites de inactividad/vida absoluta, CSRF y lista explícita de orígenes. Los intentos de login se cuentan en PostgreSQL mediante actualizaciones atómicas; la API usa la IP cliente observada por el servidor y Uvicorn no confía en cabeceras proxy por defecto.

## Estado y orden de implementación

1. **Completado:** estructura React/TypeScript con Vite, API FastAPI con `/health` y `/ready`, PostgreSQL con volumen persistente y migraciones versionadas. Compose publica frontend y API únicamente en `127.0.0.1`; PostgreSQL no publica un puerto al host. Las pruebas utilizan pytest y Vitest.
2. **En curso:** gestión de usuarios y acceso ([HU-001](historias-usuarios/HU-001-gestion-de-usuarios.md)); su [plan](planes/hu-001-gestion-de-usuarios.md) y [tareas](../odd/tasks/hu-001-gestion-de-usuarios.md) están aprobados. T1, T2, T3 y T5 están completadas; T4, T6, T7 y T8 siguen pendientes. La API inicial incluye `/api/v1/auth/bootstrap`, `/register-initial`, `/login`, `/session`, `/logout` y `/users`.
3. **Pendiente:** carga del catálogo de etiquetas predeterminadas y planificación de comidas (HU-002).

El [plan de la base](planes/arquitectura-base.md) y su [documento de tareas](../odd/tasks/architecture-foundation.md) recogen las evidencias de la base técnica. El [README](../README.md) contiene las instrucciones reproducibles. El código ya incluye interfaz de acceso/usuarios y rutas para gestión de perfiles y recuperación por correo; las tareas T4, T6 y T7 permanecen abiertas hasta completar su verificación integral. No se envía correo real en pruebas.

El despliegue remoto y el mecanismo de copias de seguridad siguen sin definirse. Las decisiones de autenticación y correo constan en HU-001 y en el plan aprobado; la implementación parcial no completa la historia ni autoriza su despliegue.
