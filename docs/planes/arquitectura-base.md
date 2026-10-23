# Plan aprobado — base del proyecto y persistencia

**Estado:** aprobado por el usuario; base implementada y verificada. **Rama:** `feat/architecture-foundation`, creada desde `main` en `96e0e7f`. Este plan desarrolla solo la primera etapa de [arquitectura](../arquitectura.md); no implementa HU-001 ni HU-002.

## Resultado esperado

Desde una copia limpia del repositorio, una persona puede levantar localmente React, FastAPI y PostgreSQL con Docker Compose, comprobar la conexión de la API a la base y ejecutar la primera migración versionada. Los datos de PostgreSQL sobreviven a un reinicio normal de los servicios.

## Trabajo propuesto

| Unidad | Entrega y prueba de salida | Alcance |
| --- | --- | --- |
| 1. Esqueleto ejecutable | Proyecto React + TypeScript con Vite y API FastAPI con una respuesta de salud básica; comandos de desarrollo y pruebas mínimas de arranque. | Solo estructura y comunicación básica, sin funcionalidades de usuarios o comidas. |
| 2. Persistencia local | PostgreSQL en Compose con volumen persistente; configuración por variables de entorno sin secretos en el repositorio; API conectada a la base y comprobación de disponibilidad; migraciones versionadas con una revisión inicial sin tablas de negocio. | Sin cuentas, autenticación, etiquetas ni asignaciones todavía. |
| 3. Prueba y documentación de arranque | Prueba de integración contra una base aislada para confirmar conexión y versión de migración; verificación de persistencia tras reiniciar servicios sin borrar volúmenes; instrucciones para configurar, arrancar, migrar y ejecutar pruebas. | No alterar ni borrar datos existentes para demostrar la persistencia. |

## Criterios de aceptación

1. `docker compose up` levanta frontend, backend y PostgreSQL con una configuración local documentada.
2. La API distingue entre estar en ejecución y poder conectar a PostgreSQL; si la base no está disponible, no informa de disponibilidad correcta.
3. La migración inicial se aplica desde cero, deja registrada su versión y puede comprobarse sin crear tablas de negocio prematuras.
4. Las pruebas de backend y frontend, y la prueba de integración con base aislada, terminan correctamente.
5. Un reinicio normal conserva los datos del volumen y la versión de migración; no se usa `down -v` en la comprobación.
6. El repositorio incluye configuración de ejemplo sin contraseñas reales y una guía reproducible de arranque y pruebas.

## Decisiones técnicas propuestas para esta etapa

- **Frontend:** Vite para el esqueleto React/TypeScript.
- **Backend y migraciones:** FastAPI, SQLAlchemy y Alembic con controlador PostgreSQL; primera revisión como punto de partida versionado. Los modelos de negocio llegarán con las historias correspondientes.
- **Pruebas:** pytest para backend; una comprobación mínima del frontend y prueba de integración sobre base aislada. Si los ejecutables o Docker no están disponibles en el entorno, registrar explícitamente qué prueba no se pudo ejecutar.
- **Entrega:** cambios en unidades revisables, con pruebas y documentación junto a cada unidad; no publicar la rama ni crear PR sin una decisión posterior.

## Fuera de alcance y puerta de aprobación

Quedan fuera de esta etapa la implementación de [HU-001](../historias-usuarios/HU-001-gestion-de-usuarios.md), [HU-002](../historias-usuarios/HU-002-planificacion-de-comidas.md), la carga de [etiquetas predeterminadas](../etiquetas-predeterminadas.md), el correo, el despliegue remoto y las copias de seguridad. La aprobación del plan y la evidencia de ejecución constan en el [documento de tareas](../../odd/tasks/architecture-foundation.md). HU-001 y HU-002 permanecen pendientes.
