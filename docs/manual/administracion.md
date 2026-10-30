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

Aplica migraciones con `make migrate`; inspecciona la versión con `docker compose exec backend python -m alembic current`. El volumen `postgres_data` solo conserva datos locales entre reinicios: no equivale a una copia de seguridad. Las imágenes de comidas viven en `data/`, por lo que una copia válida incluye **la base PostgreSQL y todo `data/` en una misma ventana sin escrituras**. No guardes la copia dentro de `data/` ni en el repositorio.

### Copia coherente de base de datos e imágenes

Ejecuta desde la raíz del proyecto, en una ventana de mantenimiento. Detén el backend y confirma que no hay escritores directos a PostgreSQL; detener solo la interfaz no es suficiente. La carpeta de copias debe estar en almacenamiento protegido, fuera de `data/`, y disponer de espacio suficiente. El ejemplo conserva una carpeta temporal si falla para permitir diagnóstico; solo publica el directorio final después de validar ambos archivos.

```sh
set -eu
umask 077
: "${BACKUP_ROOT:?Define una carpeta de copias protegida fuera de data/}"
DATA_ROOT=${DATA_ROOT:-data}
mkdir -p "$BACKUP_ROOT"
data_real=$(realpath "$DATA_ROOT")
backup_real=$(realpath "$BACKUP_ROOT")
case "$backup_real/" in "$data_real/"*) echo 'BACKUP_ROOT no puede estar dentro de data/' >&2; exit 1;; esac
test -d "$data_real"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
stage=$(mktemp -d "$BACKUP_ROOT/.comemos-$stamp.XXXXXX")
final="$BACKUP_ROOT/comemos-$stamp"
test ! -e "$final"
restore_backend() { docker compose start backend; }
trap 'docker compose start backend || true' EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
docker compose stop backend

docker compose exec -T postgres sh -ec \
  'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' \
  > "$stage/database.dump"
tar -C "$DATA_ROOT" -czf "$stage/data.tar.gz" .
docker compose exec -T postgres pg_restore --list \
  < "$stage/database.dump" > "$stage/database.contents"
tar -tzf "$stage/data.tar.gz" > "$stage/data.contents"
test -s "$stage/database.dump"
(cd "$stage" && sha256sum database.dump data.tar.gz > SHA256SUMS && sha256sum -c SHA256SUMS)
mv "$stage" "$final"
printf 'Backup created: %s\n' "$final"
```

Si falla cualquier paso, el `trap` vuelve a iniciar el backend y la copia no se publica como final. Investiga y elimina manualmente solo el directorio temporal exacto después de preservar la evidencia necesaria. Protege las copias con permisos/acceso equivalentes a la base de datos; el formato comprimido no cifra los datos.

### Verificación de restauración sin sobrescribir datos

Prueba cada copia en un proyecto Compose y almacenamiento **nuevos y aislados**, nunca en el proyecto o `data/` reales. Verifica primero integridad y contenido; restaura PostgreSQL en una base vacía de validación y extrae las imágenes en un directorio temporal vacío. No uses `--clean`, no elimines volúmenes y no conectes una restauración parcial a usuarios.

```sh
set -eu
BACKUP_DIR=${1:?Uso: BACKUP_DIR=/ruta/completa/de/copia}
(cd "$BACKUP_DIR" && sha256sum -c SHA256SUMS)
docker compose exec -T postgres pg_restore --list \
  < "$BACKUP_DIR/database.dump" > /dev/null
tar -tzf "$BACKUP_DIR/data.tar.gz" | while IFS= read -r member; do
  case "$member" in /*|../*|*/../*|*/..) echo "Ruta insegura en archivo: $member" >&2; exit 1;; esac
done
restore_data=$(mktemp -d "${TMPDIR:-/tmp}/comemos-restore-data.XXXXXX")
tar -xzf "$BACKUP_DIR/data.tar.gz" -C "$restore_data" --no-same-owner
```

En el PostgreSQL aislado crea una base vacía de validación con el usuario configurado y restaura el dump sin cambiar propietarios:

```sh
docker compose exec -T postgres sh -ec \
  'createdb -U "$POSTGRES_USER" -O "$POSTGRES_USER" hu003_restore_check'
docker compose exec -T postgres sh -ec \
  'pg_restore --exit-on-error --no-owner -U "$POSTGRES_USER" -d hu003_restore_check' \
  < "$BACKUP_DIR/database.dump"
test "$(docker compose exec -T postgres sh -ec \
  'psql -U "$POSTGRES_USER" -d hu003_restore_check -Atc "SELECT version_num FROM alembic_version"')" \
  = '0006_food_catalog_images'
docker compose exec -T postgres sh -ec \
  'psql -U "$POSTGRES_USER" -d hu003_restore_check -Atc "SELECT image_path FROM food_labels WHERE image_path IS NOT NULL"' \
  | RESTORE_DATA="$restore_data" python3 -c 'import os,re,sys; from pathlib import Path; root=(Path(os.environ["RESTORE_DATA"])/"comidas").resolve(); paths=[line.strip() for line in sys.stdin if line.strip()]; bad=[p for p in paths if not re.fullmatch(r"comidas/[0-9a-f]{32}\.webp",p) or not (root/Path(p).name).is_file()]; print(f"image references={len(paths)} invalid={len(bad)}"); sys.exit(bool(bad))'
```

La validación falla si la revisión no es la esperada o hay referencias de imagen ausentes/fuera de `comidas/`. Para que la API de validación vea los bytes extraídos, configura el proyecto Compose temporal para montar `$restore_data` en `/app/data`; configura también su `POSTGRES_DB` con la base restaurada. Restaura únicamente copias protegidas creadas por este procedimiento; no extraigas archivos no confiables. Abre el servicio de validación contra esa base y ese directorio temporal, prueba lectura de comidas e imágenes y registra resultados antes de cualquier cutover. El cutover a datos reales requiere una ventana sin escritores y una decisión operativa separada; esta guía no borra, reemplaza ni promueve automáticamente bases, volúmenes o directorios.

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

Ambas deben indicar `0005_meal_planning (head)` en una instalación que incluya HU-002, o `0006_food_catalog_images (head)` si también incluye HU-003. `heads` por sí solo no demuestra que la base esté migrada. `/ready` comprueba conexión, no la revisión ni la compatibilidad del esquema; confirma también `GET /api/v1/auth/bootstrap` antes de crear la primera cuenta. La migración `0005` añade el catálogo predeterminado y las tablas/restricciones de planificación; `0006` añade nombres normalizados e imágenes de comidas. Aplícalas únicamente en la base del entorno previsto tras revisar el procedimiento de migración y mantener una copia de seguridad adecuada.

## Cuentas y seguridad

El alta inicial se cierra después de crear la primera cuenta. Después, cualquier usuario activo puede crear familiares, editar sus datos, activar/desactivar, cambiar contraseñas ajenas y eliminar cuentas. No hay consola/API privilegiada reservada a operadores. No se puede desactivar o eliminar la última cuenta activa, ni desactivar la propia; las desactivaciones y cambios de contraseña revocan las sesiones afectadas. El borrado es permanente.

La aplicación aplica contraseñas de 8–128 caracteres, Argon2id, cookies de sesión revocables (30 minutos de inactividad, 8 horas absolutas), CSRF y verificación de origen para escrituras; limita intentos de inicio de sesión y recuperación. Uvicorn no confía en cabeceras de proxy por defecto. No configures un proxy confiable sin un diseño explícito: la detección de IP afecta a los límites de intentos. La longitud mínima de contraseña y la falta de MFA requieren una evaluación de riesgo antes de uso público.

## Planificación de comidas

La planificación familiar es compartida entre usuarios activos autenticados y no añade un rol de administrador. El catálogo de etiquetas se carga mediante la migración `0005_meal_planning`; la API valida sesión en lectura y CSRF/origen en operaciones de escritura. No se requiere tarea de mantenimiento periódica ni existe una serie recurrente: las repeticiones se materializan como asignaciones independientes. HU-002 completó la verificación local de T1–T10, incluidos escenarios de navegador contra FastAPI/SQLite y el flujo bootstrap/registro/login/logout. No se probó navegador contra PostgreSQL ni la URL publicada; consulta la [evidencia y límites de HU-002](../../odd/tasks/hu-002-planificacion-de-comidas.md#evidencia-de-t10-y-cobertura-de-escenarios) antes de planificar una puesta en producción.

**Mantenimiento del manual:** actualízalo con cualquier cambio de despliegue, secretos, migraciones, seguridad, gestión de usuarios, respaldo o recuperación.

**Referencias:** [README](../../README.md), [README backend](../../backend/README.md), [arquitectura](../arquitectura.md), [historia HU-001](../historias-usuarios/HU-001-gestion-de-usuarios.md), [historia HU-002](../historias-usuarios/HU-002-planificacion-de-comidas.md), [estado HU-002](../../odd/tasks/hu-002-planificacion-de-comidas.md).
