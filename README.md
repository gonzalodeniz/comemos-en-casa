# Comemos en casa — base local

Esta rama prepara React/TypeScript, FastAPI y PostgreSQL. El código backend y frontend incluye flujos de cuenta, gestión de usuarios y recuperación; la verificación integral de T4/T6/T7 sigue abierta. Etiquetas y planificación también están pendientes. Consultá el [plan aprobado](docs/planes/arquitectura-base.md) y el [estado de HU-001](odd/tasks/hu-001-gestion-de-usuarios.md).

## Arranque local

Requisitos: Docker con Compose. Elegí una contraseña y una clave HMAC propias para la base local; no las guardes en Git. Configuración de ejemplo (los valores de marcador no son credenciales):

```sh
export POSTGRES_PASSWORD='<elegí-una-contraseña-local>'
export AUTH_RATE_LIMIT_HMAC_KEY="$(openssl rand -hex 32)"
export APP_PUBLIC_URL='https://gonzalodeniz.com/comemos'
make up
make mailhog-up
make migrate
```

La interfaz local empaquetada está en <http://localhost:5173/comemos/> (solo loopback); para desarrollo con recarga rápida ejecuta `cd frontend && npm run dev`. La API y PostgreSQL no se publican al host. El proxy público solo atenderá <https://gonzalodeniz.com/comemos/> después de obtener y activar el certificado TLS. El backend ofrece `/health` (proceso vivo) y `/ready` (conexión a PostgreSQL; HTTP 503 si no está disponible) dentro de la red Docker. Compose conserva PostgreSQL en el volumen `postgres_data`. Las migraciones `0002_user_auth`, `0003_login_attempt_events` y `0004_password_reset_rate_scopes` incluyen persistencia para cuentas, sesiones, recuperación y límites de acceso. `AUTH_RATE_LIMIT_HMAC_KEY` debe ser una clave hexadecimal aleatoria de 32 bytes; consérvala entre reinicios y compártela entre instancias del mismo entorno. `APP_PUBLIC_URL` es obligatorio y debe apuntar a la ruta pública de interfaz. MailHog captura los correos de desarrollo en <http://127.0.0.1:8025>; abre la interfaz de usuario y revisa el buzón después de generar un correo de recuperación. SMTP (1025) solo está disponible dentro de la red Docker compartida `comemos-dev`, y MailHog solo se publica en loopback. El almacenamiento es en memoria y desaparece al reiniciar/eliminar MailHog. Es una herramienta exclusivamente de desarrollo; no la uses para producción ni conectes datos reales. `make mailhog-down` detiene y elimina únicamente MailHog (sin borrar el volumen PostgreSQL). Opcionalmente, `POSTGRES_USER` y `POSTGRES_DB` modifican usuario y nombre de base.

Compose usa PostgreSQL 16. Para reutilizar un volumen con una base heredada incompatible, consulta el [procedimiento seguro de separación](docs/manual/administracion.md#volúmenes-existentes-y-bases-heredadas); no borres datos ni apliques migraciones a un esquema ajeno.

La API de autenticación usa `/api/v1`: `GET /auth/bootstrap`, `POST /auth/register-initial`, `POST /auth/login`, `GET /auth/session`, `POST /auth/logout` y `POST /users` (creación privada). Las escrituras requieren un `Origin` permitido; logout y creación privada requieren además el token CSRF devuelto por la sesión. El registro inicial no inicia sesión automáticamente.

## Pruebas

Para probar la integración, usá un **proyecto Compose aislado** sobre una base nueva; no ejecutes estas comprobaciones contra datos que quieras conservar. Si ya tenés otra instancia ocupando los puertos 80, 443 o 5173, detenela primero o usa otro host/proyecto aislado. Desde la raíz:

```sh
PROJECT="cec-foundation-test-$$"
export AUTH_RATE_LIMIT_HMAC_KEY="$(openssl rand -hex 32)"
export APP_PUBLIC_URL='https://gonzalodeniz.com/comemos'
docker compose -p "$PROJECT" up -d --build --wait
docker compose -p "$PROJECT" exec -T backend python -m alembic upgrade head
docker compose -p "$PROJECT" exec -T -e RUN_DB_INTEGRATION=1 backend python -m pytest -q
docker compose -p "$PROJECT" stop
docker compose -p "$PROJECT" up -d --wait
docker compose -p "$PROJECT" exec -T backend python -m alembic current
docker compose -p "$PROJECT" exec -T -e RUN_DB_INTEGRATION=1 backend python -m pytest -q tests/test_database_integration.py
```

La prueba de integración debe pasar después de migrar y nuevamente tras el reinicio: la versión persiste. Para detener el proyecto de prueba sin borrar sus datos, ejecutá `docker compose -p "$PROJECT" down` (sin `-v`). El nombre del proyecto y el volumen quedan separados del entorno habitual.

Si ya instalaste dependencias locales, las pruebas aisladas de la API se ejecutan con `cd backend && python -m pytest -q` y las del frontend con `cd frontend && npm test && npm run build`. La prueba de integración se omite en la suite local salvo que establezcas `RUN_DB_INTEGRATION=1` con una base aislada. Consultá también [backend/README.md](backend/README.md) y [frontend/README.md](frontend/README.md).

## Publicación HTTPS

El procedimiento inicial, prerrequisitos HTTP-01, activación TLS y renovación están en [administración](docs/manual/administracion.md#proxy-público-y-https). No se afirma disponibilidad pública hasta validar DNS, emisión y respuesta HTTPS.
