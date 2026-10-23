# Arquitectura inicial — Comemos en casa

La primera versión será una aplicación web con **React y TypeScript** para la interfaz, **FastAPI (Python)** para la API y **PostgreSQL** para los datos persistentes. El entorno inicial será **local con Docker Compose**. Estas son decisiones de arquitectura; este documento no afirma que los componentes ya estén implementados.

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

- La estructura de datos se evolucionará mediante migraciones versionadas; la herramienta concreta se elegirá al iniciar la implementación.
- Las operaciones que afecten varias asignaciones de comidas deberán ser transaccionales, según [HU-002](historias-usuarios/HU-002-planificacion-de-comidas.md). La unicidad de correo y de fecha/franja se garantizará en la base de datos, además de las validaciones de la API.
- Las [etiquetas predeterminadas](etiquetas-predeterminadas.md) estarán disponibles para la planificación. La creación y edición de etiquetas por usuarios queda fuera de esta etapa.
- La autenticación y el control de sesiones de [HU-001](historias-usuarios/HU-001-gestion-de-usuarios.md) deben verificarse en la API, no solo en la interfaz.

## Orden de implementación propuesto

1. Estructura de frontend y backend, configuración local con Docker Compose, conexión a PostgreSQL y primera migración verificable.
2. Gestión de usuarios y acceso (HU-001).
3. Carga del catálogo de etiquetas predeterminadas y planificación de comidas (HU-002).

El despliegue remoto, el mecanismo de copias de seguridad y las herramientas concretas de migración y acceso a datos no se han decidido todavía; se definirán cuando correspondan, sin asumirlos en esta base documental.
