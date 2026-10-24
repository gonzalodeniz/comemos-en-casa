# Plan aprobado — HU-001: gestión de usuarios y acceso

**Estado:** plan y tareas aprobados; implementación autorizada. T1, T2, T3 y T5 completadas; T4, T6, T7 y T8 pendientes. No hay commit de código, publicación ni PR autorizados. **Referencia:** [HU-001](../historias-usuarios/HU-001-gestion-de-usuarios.md), especificación funcional aprobada. Este documento define cómo implementarla sobre la [base arquitectónica](../arquitectura.md); no modifica sus reglas de negocio salvo la aclaración de contraseña confirmada por el usuario.

## Resultado esperado y punto de partida

Los familiares pueden crear la primera cuenta, autenticarse, administrar usuarios y recuperar contraseñas. La API exige una cuenta activa para cada operación privada; todos los usuarios activos tienen los mismos permisos, sin roles.

Ya existen React/TypeScript/Vite, FastAPI, PostgreSQL, SQLAlchemy y Alembic. La migración `0001_baseline` no crea tablas de negocio y la interfaz solo muestra un título. No hay usuarios, sesiones, limitadores ni servicio de correo implementados.

## Alcance y reglas que deben preservarse

- Registro público exclusivamente cuando no exista ninguna cuenta; tras crear la primera, mostrar el inicio de sesión, sin autenticarla automáticamente.
- Nombre, correo único y contraseña; sin verificación de correo. Cualquier usuario activo autenticado puede crear familiares, modificar cualquier perfil y cambiar contraseñas ajenas sin verificación del titular; cambiar la propia exige la contraseña actual.
- Impedir la autodesactivación y toda desactivación o eliminación que deje cero cuentas activas. Desactivar o eliminar invalida el acceso de sesiones anteriores. El borrado elimina el perfil, no los datos compartidos.
- Mantener ambos límites de acceso: cinco fallos en quince minutos por cuenta/IP y por IP global; restricción de quince minutos, sin bloquear la cuenta desde otras IP. Respuestas genéricas y registros sin secretos.
- Recuperación por enlace enviado por correo, de un solo uso y con caducidad; solicitudes limitadas y sin revelar si la cuenta existe.

## Propuesta técnica y decisiones previas

Se propone mantener una API modular dentro de `backend/app/`, con reglas de usuarios separadas del transporte HTTP y del acceso SQLAlchemy; componentes y pruebas de formularios en `frontend/src/`. Son ubicaciones propuestas, no archivos existentes.

Se mantienen sesiones revocables, tokens hash en PostgreSQL y contadores compartidos. El contrato T1 quedó confirmado por el usuario antes de implementar las tareas dependientes:

1. **Correo:** conservar el original para mostrarlo; minúsculas en el dominio y comparación local sin distinguir mayúsculas para identidad. No hacer transformaciones específicas de proveedores. Esta política puede considerar duplicadas direcciones que algunos servidores SMTP distinguen por mayúsculas.
2. **Contraseñas:** longitud de 8 a 128 caracteres, con espacios y Unicode, sin reglas de composición. Argon2id comienza en 19 MiB, 2 iteraciones y paralelismo 1; medir antes de ajustar. El mínimo elegido es inferior a la recomendación actual de NIST para contraseñas como único factor; el riesgo debe revisarse antes de despliegues sin MFA.
3. **Sesiones y navegador:** token aleatorio de 256 bits; guardar solo su hash. Cookie `HttpOnly`, `SameSite=Lax`, `Secure` bajo HTTPS, sin `Domain` y con `Path=/`. Aplicar en servidor caducidad por inactividad de 30 minutos y absoluta de 8 horas. Revocar en logout, cambio/restablecimiento de contraseña y desactivación/eliminación de cuenta. Exigir token CSRF y origen permitido en escrituras; CORS con credenciales solo para orígenes configurados explícitamente, nunca comodín.
4. **IP:** usar la dirección observada por la API; no confiar en `Forwarded`/`X-Forwarded-For` salvo configuración explícita de proxy de confianza.
5. **Recuperación:** token aleatorio de un solo uso, almacenado como hash, caducidad de 30 minutos, respuestas genéricas y límites de tres solicitudes por cuenta y diez por IP cada hora.
6. **Correo saliente y API:** adaptador SMTP configurable mediante variables de entorno, sin seleccionar proveedor; `APP_PUBLIC_URL` obligatoria para construir enlaces. API bajo `/api/v1`: `GET /auth/bootstrap`, `POST /auth/register-initial`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/session`, `GET/POST /users`, `PATCH/DELETE /users/{id}`, `POST /users/{id}/password`, `POST /password-resets` y `POST /password-resets/confirm`.

El contrato no fija un proveedor SMTP ni credenciales; no se enviará correo real en pruebas. Las decisiones funcionales aprobadas permanecen sin cambios.

## Fases y pruebas de salida

| Fase | Entrega propuesta | Prueba de salida y trazabilidad |
| --- | --- | --- |
| 1. Contratos y persistencia | Resolver decisiones previas; modelos y migraciones de usuarios, sesiones, recuperación y limitación; unicidad de correo en PostgreSQL. | Migrar una base aislada desde `0001_baseline`; validar datos y duplicados. CA-01, CA-03, CA-05–07. |
| 2. Primera cuenta y acceso | Creación inicial atómica, registro privado, credenciales, sesión, cierre y dependencia común de autenticación/estado activo. | Dos registros iniciales concurrentes producen solo una primera cuenta; cerrar la vía pública después; denegar acceso sin sesión, con sesión inválida o cuenta inactiva. CA-01, CA-02, CA-04, CA-08. |
| 3. Administración de usuarios | Listado, edición, cambios de contraseña, activación, desactivación y eliminación; protección transaccional de la última cuenta activa. | Autodesactivación rechazada; carreras entre operaciones no dejan cero activos; duplicados rechazados; borrado del perfil sin cascada sobre datos compartidos; sesiones previas inutilizables tras desactivar/eliminar. CA-05, CA-06, CA-09. |
| 4. Protección y recuperación | Contadores atómicos por cuenta/IP e IP, eventos seguros, emisión y consumo atómico de enlaces y adaptador de correo. | Quinto fallo, expiración y otra IP; ataques a varias cuentas; respuestas genéricas; limitación de recuperación; enlace válido, caducado, reutilizado o consumido concurrentemente. CA-03, CA-07. |
| 5. Interfaz integrada | Formularios de primera cuenta, acceso, usuarios, perfil, contraseñas y recuperación; navegación protegida, errores y estados de carga. | Crear primera cuenta lleva a login; flujos completos de administración y recuperación; redirección sin sesión; validaciones cliente/servidor. CA-01–09. |
| 6. Verificación y documentación | Evidencias, configuración de correo/sesiones, migraciones y guía reproducible; revisión de la definición de terminado. | Ejecutar los 13 escenarios de HU-001 y la matriz anterior; registrar resultados y pendientes sin marcar la historia terminada antes de comprobarlos. |

Las fases son un orden de entrega, no una autorización para integrar temporalmente un acceso sin protección: las pruebas de seguridad acompañan cada fase y la funcionalidad no se entrega completa hasta superar todas.

## Estrategia de verificación

- pytest para reglas, API, permisos y validaciones; reloj controlable para caducidades y ventanas de limitación, sin esperas reales.
- PostgreSQL aislado para restricciones, transacciones, concurrencia, migraciones y sesiones compartidas entre instancias. Comprobar el estado activo en cada petición y que reactivar no restaure sesiones invalidadas.
- Vitest y pruebas de interacción de formularios; evaluar el soporte adicional necesario antes de incorporarlo. Registrar una comprobación integral en navegador para los recorridos principales.
- Sustituir el envío real por un adaptador de pruebas para verificar contenido/destino y consumo del enlace sin enviar correo a terceros. Comprobar que respuestas y registros no exponen contraseñas, sesiones ni tokens.
- Usar los comandos existentes: `cd backend && python -m pytest -q` y `cd frontend && npm test && npm run build`. Documentar los comandos nuevos que requiera HU-001. Las integraciones deben usar una base/proyecto Compose aislado, nunca datos que deban conservarse.

## Fuera de alcance y aprobación

Quedan fuera HU-002, etiquetas, recetas, compra, roles, verificación de correo, despliegue remoto y copias de seguridad. No se crearán tablas de funcionalidades futuras solo para probar su preservación; se verificará el diseño de relaciones y se añadirá la integración cuando existan esos datos.

El usuario ha aprobado este plan y el [documento TASKS](../../odd/tasks/hu-001-gestion-de-usuarios.md), y ha autorizado la implementación. T1, T2, T3 y T5 están completadas según la evidencia del registro de tareas. El código de T4, T6 y T7 está presente, pero esas tareas siguen abiertas hasta completar la verificación integral; T8 también está pendiente. La autorización no incluye commits de código, publicación ni PR.
