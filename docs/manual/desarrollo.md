# Manual de desarrollo

## Stack y estructura

- `frontend/`: React, TypeScript, Vite y Vitest; componentes e interfaz en `src/`.
- `backend/app/`: API FastAPI; `auth.py` contiene las rutas y reglas de cuentas, `models.py` las entidades SQLAlchemy, `security.py` las primitivas de contraseña/tokens y `settings.py` la configuración de orígenes y URL pública.
- `backend/migrations/versions/`: migraciones Alembic; `backend/tests/`: pytest.
- `docker-compose.yml`: frontend empaquetado, API y PostgreSQL; Nginx es el único servicio público.
- `docker-compose.mailhog.yml`: captura local de correo para desarrollo, en la red Docker compartida `comemos-dev`.

La API está bajo `/api/v1`; las comprobaciones operativas son `/health` (proceso HTTP) y `/ready` (también comprueba PostgreSQL). La HU-001 sigue con verificación integral pendiente. En HU-002, los 22 escenarios se recorrieron en Chrome contra FastAPI real y SQLite efímera; además, una ejecución limpia verificó registro bootstrap sin auto-login, login explícito y logout. `make test` pasó; no se ejecutó navegador contra PostgreSQL ni se probó la URL publicada. Consulta la [matriz de evidencia](../../odd/tasks/hu-002-planificacion-de-comidas.md#evidencia-de-t10-y-cobertura-de-escenarios).

## Entorno local integrado

Requisitos: Docker con Compose y `openssl`. En un checkout nuevo, copia la plantilla de configuración y edita los valores locales:

```sh
cp .env.example .env
```

Reemplaza los marcadores de `POSTGRES_PASSWORD` y `AUTH_RATE_LIMIT_HMAC_KEY` por valores propios (genera la clave HMAC con `openssl rand -hex 32`); no los dejes como marcadores. `.env` es configuración local privada y está excluido de Git: no lo publiques, compartas ni incluyas en commits. No copies secretos reales a documentación o registros. Después, Compose lee `.env` automáticamente:

```sh
make up
make mailhog-up
make migrate
```

Interfaz empaquetada local: `http://localhost:5173/comemos/`; API no se publica al host. Para edición con HMR, inicia Vite con `npm run dev` y abre `http://localhost:5173/comemos/`; el servidor dev no forma parte del proxy público. En producción solo se expone `https://gonzalodeniz.com/comemos/` tras emitir/activar TLS. Compose publica ambos puertos solo en loopback y no publica PostgreSQL al host. El volumen `postgres_data` conserva datos al reiniciar. No uses `down -v` en un entorno con datos que quieras conservar.

MailHog captura los mensajes SMTP de la aplicación: abre `http://127.0.0.1:8025` para inspeccionar el buzón y generar un flujo como recuperación de contraseña para probarlo. El backend usa `mailhog:1025` por DNS interno; SMTP no se publica en el host y la interfaz solo está ligada a loopback. MailHog almacena mensajes en memoria, por lo que se pierden al reiniciarlo o eliminarlo. Es solo para desarrollo local, nunca para producción ni correo/datos reales. Usa `make mailhog-down` para pararlo y eliminar el contenedor sin afectar el volumen de PostgreSQL. `make help` muestra los comandos de ciclo de vida y registros.

Compose usa PostgreSQL 16 y una base `comemos` por defecto. Si reutilizas un volumen con una base heredada, sigue el [procedimiento de separación sin pérdida de datos](administracion.md#volúmenes-existentes-y-bases-heredadas) antes de migrar. Cambiar `POSTGRES_DB` no crea otra base en un volumen ya inicializado.

## Desarrollo por servicio y validación

Backend (Python 3; base PostgreSQL propia):

```sh
cd backend
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg://usuario:contraseña@localhost:5432/base'
export AUTH_RATE_LIMIT_HMAC_KEY="$(openssl rand -hex 32)"
uvicorn app.main:app --reload --no-proxy-headers
python -m pytest -q
```

Frontend:

```sh
cd frontend
npm install
npm run dev
npm test
npm run build
```

Para API local fuera de Compose, configura `CORS_ALLOWED_ORIGINS` como lista separada por comas si la interfaz no usa los orígenes locales predeterminados. El cliente usa `/comemos/api/v1` por defecto; Vite reescribe este prefijo hacia la API local durante desarrollo y Nginx lo enruta en despliegue. `VITE_API_BASE_URL` solo se necesita para sobrescribirlo explícitamente.

Las pruebas de integración de base de datos deben ejecutarse únicamente sobre una base/proyecto Compose nuevo y aislado; requieren `RUN_DB_INTEGRATION=1`. Consulta el procedimiento seguro de [README](../../README.md#pruebas). No ejecutes integración sobre datos que deban preservarse.

## Migraciones y convenciones

Con variables de conexión válidas, desde `backend/` ejecuta `alembic upgrade head` y revisa con `alembic current`. Las migraciones versionadas actuales son `0001_baseline`, `0002_user_auth_persistence`, `0003_login_attempt_events`, `0004_password_reset_rate_scopes` y `0005_meal_planning` (planificación y catálogo predeterminado). Revisa migraciones contra PostgreSQL aislado; no edites versiones ya aplicadas para cambiar su efecto.

La API de HU-002 ofrece `GET /api/v1/food-labels`, `GET /api/v1/meal-planning`, `POST /api/v1/meal-planning/preview` y `POST /api/v1/meal-planning/operations`. Todas requieren sesión activa; los POST requieren origen permitido y CSRF. La previsualización no escribe; guardar vuelve a validar y puede responder 409 con una previsualización actualizada si cambió el estado que requiere confirmación. La documentación del [contrato y matriz](../planes/hu-002-planificacion-de-comidas.md) describe solicitudes y respuestas. La prueba PostgreSQL aislada T9 acreditó la migración, la atomicidad y la concurrencia. `make test` pasó fuera de sandbox autorizado: 61 backend y 15 frontend; usa `.venv` y excluye integración PostgreSQL.

Se conservaron los primeros timeouts de `make test` en sandbox (60/240/600 s) y de la prueba de autenticación focalizada (120 s). En comparación controlada, un GET mínimo FastAPI/TestClient se colgó a 15 s en sandbox y respondió HTTP 200 en 0,20 s fuera; la prueba focalizada, limitada a 30 s en sandbox, dio `1 passed` en 0,74 s fuera. Los stacks se detenían en coordinación de portal/hilos de AnyIO antes del trabajo de producto; la restricción interna exacta no quedó aislada y no se atribuye causa al producto. No se requieren cambios de dependencias, seguridad, workflow ni Makefile. La integración PostgreSQL permanece en su tarea aislada T9. T10 está completada localmente; el recorrido autenticado de escenarios usó sesiones sembradas, pero una sesión distinta verificó registro/login/logout sin sembrar usuarios o sesiones. No se probó navegador contra PostgreSQL ni la URL publicada.

Sigue los patrones existentes: Python en `snake_case`, componentes React en `PascalCase`, pruebas Python `test_*.py` y Vitest `*.test.tsx`. Añade pruebas focalizadas con cada cambio. No hay formatter/linter general documentado. Si cambias comportamiento, configuración o seguridad, actualiza los manuales y documentación pertinente.

**Mantenimiento del manual:** actualízalo al modificar estructura, dependencias, comandos, pruebas, migraciones o configuración.

**Referencias:** [README](../../README.md), [README backend](../../backend/README.md), [arquitectura](../arquitectura.md), [plan HU-001](../planes/hu-001-gestion-de-usuarios.md).
