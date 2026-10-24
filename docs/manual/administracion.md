# Manual de administración

## Alcance y despliegue

Compose mantiene frontend, API y PostgreSQL separados; únicamente el servicio Nginx publica los puertos 80/443. El modo de TLS de este manual usa HTTP-01 de Let's Encrypt para `gonzalodeniz.com`. La emisión solo se considera completada cuando Certbot lo confirma y una comprobación HTTPS funciona. No se configuran DNS, firewall ni acceso remoto desde este proyecto.

No existe un rol de administrador separado. Todo usuario autenticado y activo puede gestionar todas las cuentas familiares; la primera cuenta se crea solo mientras no exista ninguna. Protege la dirección de la aplicación y las credenciales iniciales como acceso administrativo compartido.

## Preparar y arrancar Compose

En un checkout nuevo, desde la raíz copia la plantilla y completa sus valores locales:

```sh
cp .env.example .env
```

Reemplaza los marcadores de contraseña y clave HMAC; genera esta última con `openssl rand -hex 32`. Para el despliegue público, configura `APP_PUBLIC_URL=https://gonzalodeniz.com/comemos` y añade `https://gonzalodeniz.com` a `CORS_ALLOWED_ORIGINS`; conserva los orígenes loopback para desarrollo. Mantén `.env` con modo `600`. No inicies Compose con los marcadores de ejemplo. `.env` contiene configuración privada local y está excluido de Git; no lo publiques, compartas ni incluyas en commits. Mantén secretos fuera de registros y documentación.

Inicia servicios y aplica migraciones:

```sh
make up
make mailhog-up
make migrate
```

Los valores entre `<...>` son marcadores, no valores válidos. No guardes secretos en el repositorio, logs o documentación. `AUTH_RATE_LIMIT_HMAC_KEY` debe ser exactamente 32 bytes representados en hexadecimal; conserva el mismo valor entre reinicios y compártelo entre instancias del mismo entorno para que los límites basados en HMAC sean consistentes. La rotación requiere evaluación operativa; no la hagas de forma casual.

Variables:

- `POSTGRES_PASSWORD` es obligatorio; `POSTGRES_USER` y `POSTGRES_DB` son opcionales (por defecto `comemos`).
- `APP_PUBLIC_URL` es obligatoria y debe ser URL absoluta HTTP(S) de la interfaz; se usa en enlaces de recuperación.
- `CORS_ALLOWED_ORIGINS` es una lista explícita separada por comas; no admite `*`. Debe coincidir con el origen real de navegador.
- En desarrollo local, `.env` configura `EMAIL_SMTP_HOST=mailhog`, puerto `1025`, `EMAIL_SMTP_STARTTLS=false` y un remitente local. La aplicación conecta por DNS del servicio en la red interna `comemos-dev`; el puerto SMTP no se publica. Inicia MailHog con `make mailhog-up` después de crear la red con `make up`; consulta los mensajes en `http://127.0.0.1:8025`. `make mailhog-status` y `make mailhog-logs` ayudan a diagnosticarlo; `make mailhog-down` lo elimina sin borrar volúmenes. Los mensajes solo viven en memoria y se pierden al reiniciar. MailHog es de desarrollo exclusivamente: no lo uses en producción ni para correos reales. Para un proveedor externo, sustituye estos valores por host, puerto, credenciales y STARTTLS/TLS proporcionados por ese proveedor; si se define usuario SMTP, también se necesita contraseña.
- Para conexión backend fuera de Compose, usa `DATABASE_URL` o `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`; los valores `DB_*` evitan incrustar contraseñas reservadas en una URL.

El puerto local de frontend se limita a `127.0.0.1:5173`; API y PostgreSQL no publican puertos al host. El proxy público es el único servicio ligado a todas las direcciones. `/health` indica proceso vivo; `/ready` devuelve 503 si PostgreSQL no está disponible.


## Proxy público y HTTPS

Nginx acepta solo `gonzalodeniz.com`: `/.well-known/acme-challenge/` sirve el webroot ACME; `/comemos` y `/comemos/` son las únicas rutas de aplicación admitidas. HTTP redirige solo esa ruta a HTTPS; host/rutas ajenas responden 404. La API se publica únicamente como `/comemos/api/v1/` y Nginx elimina el prefijo `/comemos` al reenviarla. El build React usa `/comemos/` como base; el servidor Vite de desarrollo no se expone públicamente.

Antes de empezar, el DNS público del dominio debe apuntar a este host y el tráfico entrante TCP 80 debe llegar al contenedor; HTTPS requiere además TCP 443. No se modifican DNS ni firewall aquí. Comprueba primero `docker compose ps` y que ningún servicio use esos puertos. Arranca primero el proxy: el entrypoint selecciona automáticamente el modo HTTP bootstrap si aún no existe certificado y TLS cuando Certbot ya lo haya emitido; así Nginx no falla en un volumen nuevo:

```sh
make proxy-up
make cert-issue
make cert-enable-tls
make cert-status
```

`cert-issue` usa Certbot webroot con HTTP-01 y modo sin correo (`--register-unsafely-without-email`); no se inventa una dirección de notificación. Si falla por DNS, conectividad/puerto 80 o validación, conserva el modo bootstrap HTTP y corrige el prerrequisito fuera de este procedimiento. `make cert-enable-tls` reinicia Nginx y verifica que el certificado exista y que la configuración TLS sea válida; no cambia archivos de configuración versionados.

La renovación se ejecuta con `make cert-renew`; Certbot reutiliza el webroot y luego se valida y recarga Nginx. Para automatizarla, programa este comando con un mecanismo de tareas del host y monitoriza su resultado. Verifica externamente `https://gonzalodeniz.com/comemos/` y rutas no permitidas antes de anunciar disponibilidad. `make proxy-status` muestra contenedores y `make cert-status` el estado del certificado.

## Esquema, persistencia y copias

Aplica migraciones con `make migrate`; inspecciona la versión con `docker compose exec backend python -m alembic current`. No hay procedimiento de copia de seguridad, restauración ni retención definido en el repositorio. El volumen `postgres_data` solo conserva datos locales entre reinicios: no equivale a una copia de seguridad. Antes de operar datos reales, establece y prueba una política de copias fuera del contenedor, restauración y control de acceso; no borres el volumen para resolver errores.

### Volúmenes existentes y bases heredadas

Compose usa PostgreSQL 16 (`postgres:16-alpine`). La versión mayor debe coincidir con la del volumen existente; cambiar la imagen no actualiza los datos. No borres el volumen para resolver incompatibilidades.

`POSTGRES_DB` solo crea la base durante la primera inicialización del volumen. Si cambias ese nombre con un volumen ya inicializado, crea primero la base nueva de forma explícita y sin sobrescribir otra existente. Para separar una base heredada incompatible, comprueba que `comemos` no existe y, solo entonces, ejecuta:

```sh
docker compose exec -T postgres psql -U comemos -d postgres -Atc "SELECT datname FROM pg_database WHERE datname = 'comemos'"
docker compose exec -T postgres createdb -U comemos -O comemos comemos
```

Si la consulta devuelve una base existente, inspecciona su esquema y sus datos antes de continuar; no ejecutes el segundo comando ni elimines datos. Ajusta los nombres si usas otro `POSTGRES_USER` o `POSTGRES_DB`. Cambia únicamente `POSTGRES_DB` en `.env`, conserva sus secretos y restringe sus permisos con `chmod 600 .env`. Después ejecuta `make up` y `make migrate`. La base heredada queda intacta; este procedimiento no importa sus cuentas.

Comprueba por separado la revisión **aplicada** y la cabeza **disponible**:

```sh
docker compose exec -T backend python -m alembic current
docker compose exec -T backend python -m alembic heads
```

Ambas deben indicar `0004_password_reset_rate_scopes (head)`. `heads` por sí solo no demuestra que la base esté migrada. `/ready` comprueba conexión, no la revisión ni la compatibilidad del esquema; confirma también `GET /api/v1/auth/bootstrap` antes de crear la primera cuenta.

## Cuentas y seguridad

El alta inicial se cierra después de crear la primera cuenta. Después, cualquier usuario activo puede crear familiares, editar sus datos, activar/desactivar, cambiar contraseñas ajenas y eliminar cuentas. No hay consola/API privilegiada reservada a operadores. No se puede desactivar o eliminar la última cuenta activa, ni desactivar la propia; las desactivaciones y cambios de contraseña revocan las sesiones afectadas. El borrado es permanente.

La aplicación aplica contraseñas de 8–128 caracteres, Argon2id, cookies de sesión revocables (30 minutos de inactividad, 8 horas absolutas), CSRF y verificación de origen para escrituras; limita intentos de inicio de sesión y recuperación. Uvicorn no confía en cabeceras de proxy por defecto. No configures un proxy confiable sin un diseño explícito: la detección de IP afecta a los límites de intentos. La longitud mínima de contraseña y la falta de MFA requieren una evaluación de riesgo antes de uso público.

**Mantenimiento del manual:** actualízalo con cualquier cambio de despliegue, secretos, migraciones, seguridad, gestión de usuarios, respaldo o recuperación.

**Referencias:** [README](../../README.md), [README backend](../../backend/README.md), [arquitectura](../arquitectura.md), [historia HU-001](../historias-usuarios/HU-001-gestion-de-usuarios.md).
