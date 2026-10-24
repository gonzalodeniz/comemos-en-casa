# TASKS — HU-001: gestión de usuarios y acceso

**Objetivo:** ejecutar, cuando se autorice, el [plan aprobado de HU-001](../../docs/planes/hu-001-gestion-de-usuarios.md) sobre la base existente, preservando la [especificación funcional](../../docs/historias-usuarios/HU-001-gestion-de-usuarios.md).

**Estado:** plan y tareas aprobados. T1, T2, T3 y T5 completadas; T4, T6, T7 y T8 pendientes. La implementación autorizada sigue sin incluir commit, publicación ni PR.

## Especificaciones y límites

- **S1:** solicitud del usuario: «aprueba el plan y genera el fichero TASKS».
- **S2:** CA-01–09, RN-01–13 y los 13 escenarios de HU-001 son el alcance funcional aprobado; el plan define seis fases.
- **S3:** solo una primera cuenta mediante registro público; después, creación por usuarios activos autenticados. Tras crear la primera cuenta se muestra login, sin autenticarla automáticamente. No hay roles ni verificación de correo.
- **S4:** cinco fallos en quince minutos por cuenta/IP y por IP global producen quince minutos de restricción; otra IP puede acceder a la misma cuenta. Recuperación por correo mediante enlace de un solo uso y validez limitada.
- **S5:** impedir autodesactivación y desactivación/eliminación de la última cuenta activa; invalidar sesiones al desactivar/eliminar y preservar datos compartidos.
- **S6:** quedan fuera HU-002, etiquetas, recetas, compra, despliegue y copias de seguridad. No crear tablas de futuras funcionalidades para probar su preservación.

## Tareas

La implementación autorizada cubre T1–T3 y T5. La evidencia se registra tras las comprobaciones; una descripción o un enlace no equivale a una prueba superada.

- [x] **T1 — Concretar contratos técnicos (fase 1).** Dependencias: ninguna. Entrega: registrar y confirmar contrato API, normalización/unicidad del correo, reactivación, política y derivación de contraseñas, duración/renovación/revocación de sesiones, cookies/CSRF/origen/IP fiable, caducidad y límite de recuperación, proveedor de correo y URL del enlace. Salida: decisiones confirmadas, sin valores inventados; contratos y casos de error trazados a CA-01–09 antes de implementar las tareas dependientes. **Evidencia:** contratos registrados en este TASKS, la historia HU-001 y el plan aprobado; confirmación del usuario: 8–128 caracteres y aceptación de las demás propuestas.
- [x] **T2 — Persistencia y migraciones (fase 1).** Dependencias: T1. Entrega: modelos SQLAlchemy y migraciones de usuarios, sesiones, recuperación y contadores compartidos, con identificadores internos y correo único en PostgreSQL. Salida: pruebas en base aislada de migración desde `0001_baseline`, unicidad concurrente y almacenamiento sin contraseñas ni tokens utilizables en claro según el contrato confirmado. CA-01, CA-03, CA-05, CA-06, CA-07. **Evidencia:** `0002_user_auth` se aplicó sobre PostgreSQL recién creado desde el baseline; la prueba de unicidad concurrente insertó exactamente un usuario y rechazó el duplicado. Suite backend en Compose: 9 passed, 2 skipped (pruebas que requieren el CLI Compose dentro del contenedor), 1 aviso deprecado.
- [x] **T3 — Primera cuenta, sesiones y acceso (fase 2).** Dependencias: T1, T2. Entrega: creación inicial atómica, registro privado, login/logout, revocación y control común de autenticación/estado activo en la API. Salida: dos solicitudes iniciales concurrentes crean solo una primera cuenta; después se cierra el registro público; acceso permitido solo a cuentas activas, sin roles, y denegado con sesión ausente, inválida, caducada o cerrada; nombre vacío tras normalización rechazado. CA-01, CA-02, CA-04, CA-08; escenarios 1, 2, 5, 6, 11. **Evidencia:** suite PostgreSQL aislada volvió a pasar el registro concurrente (201/409), login/logout/sesión y creación privada; `test_whitespace_only_account_name_is_rejected` verifica 422 y que bootstrap sigue abierto.
- [ ] **T4 — Administración y contraseñas (fase 3).** Dependencias: T1, T2, T3. Entrega: listado, edición de perfiles, cambios de contraseña propia/ajena, activación, desactivación y eliminación. Salida: validar correos duplicados, contraseña actual para cambio propio y ausencia de verificación del titular para cambio ajeno; rechazar autodesactivación; carreras de desactivación/eliminación no dejan cero activos. Invalidar sesiones anteriores al desactivar/eliminar; reactivar no las restaura. El borrado elimina el perfil sin cascada sobre datos compartidos; comprobar relaciones sin crear tablas fuera de alcance. CA-05, CA-06, CA-09; escenarios 7–10, 12, 13.
- [x] **T5 — Limitación y eventos de acceso (fase 4).** Dependencias: T1, T2, T3. Entrega: controles atómicos compartidos por cuenta/IP e IP global en el servidor, respuestas genéricas y eventos sin secretos. Salida: conteo de timestamps en ventana móvil inclusiva de 15 minutos, lock al quinto evento dentro de esa ventana, expiración del lock, concurrencia y acceso desde otra IP; no revelar existencia de cuenta ni motivo de rechazo. CA-02, CA-03; escenarios 2–4. **Evidencia:** pruebas SQLite del recorrido t=0/1/2/14/14:59 y del límite inclusivo t=15 bloquean ambos scopes; un evento fuera del rolling window no bloquea; el lock expira a los 15 minutos. PostgreSQL confirmó incrementos concurrentes de ocho sesiones.
- [ ] **T6 — Recuperación por correo (fase 4).** Dependencias: T1, T2, T3, T4. Entrega: solicitud limitada, adaptador de correo y consumo atómico del enlace para restablecer la contraseña. Salida: respuesta sin enumeración; verificar destinatario/contenido con adaptador de pruebas, enlace válido/caducado/reutilizado y consumo concurrente; aplicar política confirmada de contraseñas e invalidación. No enviar correo real a terceros durante las pruebas. CA-06, CA-07.
- [ ] **T7 — Interfaz integrada (fase 5).** Dependencias: T3, T4, T5, T6. Entrega: formularios de primera cuenta, acceso, usuarios, perfil, contraseñas y recuperación; navegación protegida, validaciones, errores y carga. Salida: pruebas de interacción y recorrido en navegador; crear primera cuenta conduce a login y acceder sin sesión redirige; todos los usuarios activos tienen los mismos permisos. La UI no sustituye los controles de la API. CA-01–09; escenarios 1–13.
- [ ] **T8 — Verificación y documentación (fase 6).** Dependencias: T2, T3, T4, T5, T6, T7. Entrega: matriz de resultados, configuración sin secretos, migraciones y comandos reproducibles. Salida: ejecutar todos los criterios y escenarios, pruebas de concurrencia/seguridad y regresión; documentar incidencias y evidencias antes de marcar la historia terminada. CA-01–09 y definición de terminado completa; revisión e integración requieren la autorización correspondiente.

## Matriz de cobertura

| Criterio | Tareas | Escenarios de HU-001 |
| --- | --- | --- |
| CA-01 — Registro | T1, T2, T3, T7, T8 | 5, 6; validaciones y cierre del registro público adicionales |
| CA-02 — Login | T3, T5, T7, T8 | 1, 2 |
| CA-03 — Fuerza bruta | T2, T5, T7, T8 | 3, 4; límite IP global adicional |
| CA-04 — Logout | T3, T7, T8 | Prueba adicional de revocación y nuevo acceso |
| CA-05 — Perfil | T2, T4, T7, T8 | 7, 12 |
| CA-06 — Contraseña | T2, T4, T6, T7, T8 | 13; cambio propio y almacenamiento seguro adicionales |
| CA-07 — Recuperación | T2, T6, T7, T8 | Pruebas adicionales de correo, límite, caducidad y uso único |
| CA-08 — Acceso | T3, T7, T8 | 11; cuenta inactiva y controles API adicionales |
| CA-09 — Gestión | T4, T7, T8 | 6–10; eliminación y concurrencia adicionales |

Los escenarios 1–13 se ejecutarán y registrarán individualmente en T8, junto con las pruebas adicionales necesarias para criterios no cubiertos explícitamente por ellos.

## Verificación prevista

- Backend: `cd backend && python -m pytest -q`.
- Frontend: `cd frontend && npm test && npm run build`.
- Integración: usar exclusivamente una base nueva en un proyecto Compose aislado, según el [README](../../README.md); aplicar migraciones y establecer `RUN_DB_INTEGRATION=1` cuando corresponda. No apuntar a datos que deban conservarse ni borrar volúmenes existentes.
- Verificar restricciones/transacciones con PostgreSQL, reloj controlable para ventanas/caducidades, sesiones compartidas entre instancias y correo sustituido por un adaptador de pruebas. Registrar cualquier comando adicional junto a su configuración.
- Cada tarea de implementación incorporará pruebas de sus reglas y fallos, no solo comprobaciones finales. No se entrega un acceso parcialmente protegido antes de completar T5 y las comprobaciones integrales.

## Registro

L1. El usuario aprobó el plan y pidió este fichero: «aprueba el plan y genera el fichero TASKS».
L2. El usuario aprobó el plan y las tareas y autorizó el commit de la documentación: «aprueba el plan y tarea y haz commit».
L3. El usuario autorizó iniciar la implementación y confirmó los contratos de T1, con longitud de contraseña de 8–128 caracteres.
L4. T1, T2, T3 y T5 completadas; T4, T6, T7 y T8 pendientes. No se afirma HU-001 completa.
L5. En PostgreSQL nuevo y aislado, `docker compose -p cec-hu001-check-1792799847-2819093 exec -T backend python -m alembic upgrade head` aplicó `0001_baseline` y `0002_user_auth`; `docker compose -p cec-hu001-check-1792799847-2819093 exec -T -e RUN_DB_INTEGRATION=1 backend python -m pytest -q -rs tests/test_database_integration.py` pasó 2 pruebas, incluida unicidad concurrente. La suite backend completa pasó 9 pruebas: `docker compose -p cec-hu001-full-1792799951-2820687 exec -T -e RUN_DB_INTEGRATION=1 backend python -m pytest -q -rs`; omitió dos pruebas de configuración que requieren el CLI Compose dentro del contenedor y emitió un aviso deprecado de `TestClient`/`httpx`.
L6. El intento local `cd backend && ../.venv/bin/python -m pytest -q -p no:cacheprovider tests` emitió `..ss` y se interrumpió manualmente tras aproximadamente 90 s. La suite aislada de Compose se ejecutó después e incluyó las pruebas de PostgreSQL.
L7. La suite completa en PostgreSQL aislado, `docker compose -p cec-hu001-auth-1792801663-2835565 exec -T -e RUN_DB_INTEGRATION=1 backend python -m pytest -q -rs`, pasó: 18 passed, 2 skipped (CLI Compose no disponible dentro del contenedor) y un aviso deprecado de `TestClient`/`httpx`. Incluyó registro inicial concurrente (201/409), incremento concurrente de bucket de acceso con ocho sesiones y pruebas de autenticación/CSRF/sesiones/límites.
L8. En la base aislada recién creada, `docker compose -p cec-hu001-auth-1792801663-2835565 exec -T backend python -m alembic upgrade head` aplicó `0001_baseline` y `0002_user_auth`. Los tests focalizados en el contenedor (`tests/test_auth.py tests/test_user_models.py tests/test_health.py`) pasaron: 14 passed y un aviso deprecado. El comando local exacto `cd backend && ../.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_user_models.py tests/test_health.py` produjo cuatro puntos de tests de modelo y quedó bloqueado en TestClient; se interrumpió manualmente tras 15 s. La suite Compose completa ejecutada después pasó.
L9. En proyecto Compose fresco `cec-hu001-roll-1792802697-2848053`, `docker compose -p cec-hu001-roll-1792802697-2848053 exec -T backend python -m alembic upgrade head` aplicó baseline, `0002_user_auth` y `0003_login_attempt_events`. Tests focalizados `docker compose -p cec-hu001-roll-1792802697-2848053 exec -T backend python -m pytest -q -p no:cacheprovider tests/test_auth.py tests/test_user_models.py tests/test_health.py`: 18 passed, 1 aviso. Suite completa `docker compose -p cec-hu001-roll-1792802697-2848053 exec -T -e RUN_DB_INTEGRATION=1 backend python -m pytest -q -rs`: 22 passed, 2 skipped (CLI Compose no disponible en contenedor), 1 aviso. Incluye eventos rolling para account_ip e IP, límite inclusivo, expiración, evento fuera de ventana, thread-safe contention PostgreSQL de ocho incrementos y validation de nombre whitespace.
