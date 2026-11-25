# PERFIL.md — Comemos en casa

Contexto del proyecto para los agentes de `.codex/agents/`. No sustituye `AGENTS.md`, las instrucciones del usuario ni la documentación aprobada. El flujo de seguimiento es local y está definido en `docs/process/FLUJO_DE_TRABAJO.md`.

## Producto

Aplicación web para miembros de una familia que permite planificar comidas, gestionar la lista de la compra y compartir recetas y consejos culinarios. Fuente: `docs/product-vision.md`.

## Idioma

Seguir `AGENTS.md`: identificadores en español cuando sea posible, preservando contratos y convenciones existentes; comentarios breves en español en las declaraciones nuevas. Documentación y mensajes de commit en español; commits con Conventional Commits y sin atribución de IA.

## Fuentes de verdad

- `AGENTS.md`: reglas de trabajo y pruebas.
- `docs/product-vision.md` y `docs/glosario.md`: visión y vocabulario.
- `docs/historias-usuarios/` y `docs/product/`: historias, contexto y backlogs por iniciativa.
- `docs/planes/`, `docs/seguimiento/` y los registros existentes en `odd/tasks/`: planes, aprobación, tareas y evidencia; consultar su estado específico antes de trabajar.
- `README.md`, manuales y código: comportamiento y configuración actuales; contrastar documentación histórica con la implementación.

Las historias usan identificadores `HU-*`; los backlogs también agrupan iniciativas `HIT-*`. No hay un documento único de requisitos ni un roadmap común para todas las iniciativas. No inventar identificadores ni inferir la aprobación de un plan por su mera existencia.

## Restricciones de arquitectura

- Frontend React/TypeScript con Vite; API FastAPI/Python; PostgreSQL y migraciones Alembic; entorno local con Docker Compose.
- Respetar validación, autorización, protección CSRF y límites de seguridad existentes; no confiar en cabeceras proxy sin configuración explícita.
- No exponer secretos ni credenciales. No ejecutar operaciones remotas sin autorización explícita del destino, operación y credencial o sesión.
- No poner en riesgo datos existentes; las pruebas de integración de base de datos requieren un proyecto y una base aislados y nuevos.
- Consultar `docs/arquitectura.md` como documento inicial: contiene información histórica, no prueba por sí mismo el estado actual.

## Modelo de dominio

Consultar `docs/glosario.md` y la historia concreta. La lista de la compra es compartida; las cantidades compatibles se acumulan y las unidades no se suman con el peso. Las aportaciones de recetas deben poder distinguirse. No extender estas reglas más allá de lo documentado o implementado sin verificar.

## Configuración

La configuración y los secretos se suministran mediante variables de entorno; `.env.example`, `backend/app/settings.py`, Compose y los manuales documentan su uso. No leer ni publicar el contenido de archivos de secretos para una tarea que no lo requiera.

## Base técnica

La base ya existe. Ver `docs/planes/arquitectura-base.md`, `odd/tasks/architecture-foundation.md`, `backend/`, `frontend/` y `COMMANDS.md`. No recrearla como si fuera un proyecto nuevo.

## Comprobaciones obligatorias

1. Revisar el alcance, la historia y los criterios aplicables, sin dar por aprobado un plan pendiente.
2. Añadir o actualizar pruebas pertinentes; ejecutar las suites relevantes y el build frontend cuando corresponda.
3. Las pruebas backend que usan `TestClient`, así como `make test` y `make test-backend`, se ejecutan fuera del sandbox mediante aprobación. Si no se autoriza, comunicar la limitación, sin eludirla.
4. Las pruebas de integración de PostgreSQL solo se ejecutan contra una base nueva y aislada, como indica el README.
5. Revisar migraciones, seguridad, datos persistentes y documentación cuando el cambio los afecte; informar de las comprobaciones no realizadas.

## Verificación manual

Cuando proceda, indicar pasos reproducibles para comprobar la interfaz y los flujos afectados. No asumir que sustituye las pruebas automáticas ni declarar validada una funcionalidad sin evidencia.

## Documentación de usuario

- `README.md`: arranque y pruebas locales.
- `docs/manual/usuario.md`: uso de la aplicación.
- `docs/manual/administracion.md`: administración y despliegue.
- `docs/manual/desarrollo.md`: desarrollo.

No existe actualmente un `CHANGELOG.md`; no crear uno automáticamente.

## Entregas

La planificación está distribuida en historias, backlogs, planes y tareas. El seguimiento nuevo se guarda en `docs/seguimiento/`; los registros previos de `odd/tasks/` se mantienen en su ubicación. No usar GitHub para el flujo de trabajo.
