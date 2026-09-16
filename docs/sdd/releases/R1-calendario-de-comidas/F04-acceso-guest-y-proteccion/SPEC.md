# F04 — Acceso guest y protección

**Estado:** APPROVED · **Versión:** 0.1 · **Fuente:** `specs/acceso-guest-y-proteccion/spec.md`, `proposal.md`, `design.md` de `openspec/changes/calendario-de-comidas/`.

## Contexto

La visión contempla autenticación Gmail para operaciones protegidas, pero el login de la issue #6 no pertenece a esta feature. R1 puede habilitar temporalmente un calendario único, público y compartido, declarando su riesgo de forma explícita.

## Alcance y no alcance

Incluye configuración guest, autorización delegada, banner y rate limiting por IP. No incluye login alternativo, cuentas anónimas, calendarios por dispositivo, propiedad, roles, permisos, CAPTCHA ni otra protección antiabuso.

## Actores

- Visita anónima.
- Persona autenticada por la dependencia #6.
- Operación que configura y reinicia el backend.

## Historias y criterios de aceptación

### US-ACC-001 — Habilitar guest de forma explícita
Como responsable de operación, quiero controlar el acceso anónimo al arrancar el servicio.

- **CA-ACC-001:** `ENABLE_GUEST_USER=true` habilita guest; `false` o ausencia lo deshabilitan.
- **CA-ACC-002:** cambiar la variable solo tiene efecto tras reiniciar.
- **CA-ACC-003:** valores distintos de `true`/`false` en minúsculas, después de recortar espacios, abortan el arranque.

### US-ACC-002 — Usar un calendario compartido
Como visita guest, quiero acceder al calendario público cuando esté habilitado.

- **CA-ACC-004:** toda visita guest puede leer, crear, modificar y borrar cualquier asignación del único calendario `shared`.
- **CA-ACC-005:** no se crean identidades, calendarios aislados, propiedad, historial ni atribución.
- **CA-ACC-006:** con guest deshabilitado se exige la credencial de #6 o se responde `401 authentication_required`; R1 no muestra login propio.

### US-ACC-003 — Entender y limitar el modo público
Como persona usuaria, quiero conocer el modo compartido y recibir feedback ante abuso.

- **CA-ACC-007:** durante todo guest, incluida carga inicial, aparece sin cierre y con espacio propio el texto exacto `El modo guest está activo: este calendario es público y compartido. Cualquier persona puede ver y cambiar las asignaciones.`
- **CA-ACC-008:** el banner no tapa la cuadrícula y no aparece con guest deshabilitado.
- **CA-ACC-009:** cada IP puede hacer hasta 60 lecturas y 30 escrituras por minuto, tanto guest como autenticada.
- **CA-ACC-010:** al superar el límite se devuelve `429` y se muestra `Has superado el límite de solicitudes. Inténtalo de nuevo en un minuto.`

## Reglas

- **RD-ACC-001:** la configuración se lee una vez al inicio y el valor efectivo es inmutable durante el proceso.
- **RD-ACC-002:** guest y personas autenticadas operan sobre `calendar_key='shared'`.
- **RD-ACC-003:** GET/HEAD/OPTIONS son lecturas; POST/PATCH/DELETE son escrituras; altas, cambios y bajas cuentan como escritura.
- **RD-ACC-004:** los buckets son independientes, de minuto UTC fijo, se incrementan atómicamente una vez al ingreso; reintentos internos no consumen cuota adicional.
- **RD-ACC-005:** la IP procede del socket; cabeceras proxy se aceptan solo desde proxies configurados como confiables.
- **RD-ACC-006:** si el almacén de límites no está disponible, se reintenta según **RD-PER-002** y finalmente se falla cerrado con `503`.

## Modelo conceptual

`ModoGuest` es configuración de proceso. `Acceso` resulta de modo guest o credencial externa. `BucketDeLímite` se identifica por IP, inicio de minuto UTC y clase (`read`/`write`).

## Interfaces

- `GET /context` expone `guestMode` junto a zona y semana actual.
- `429 rate_limited` incluye `Retry-After` y headers de límite/restantes/reset; no es reintentable automáticamente.
- `401 authentication_required` no define ni enlaza una interfaz de login propia.

## RNF

Los límites deben ser coherentes entre réplicas mediante almacenamiento atómico compartido en PostgreSQL; un contador en memoria no es válido. Banner, toast y foco siguen las reglas de F05.

## Supuestos, dependencias y riesgos

- Depende de la issue #6 si guest se deshabilita y de F03 para PostgreSQL/buckets.
- Riesgo aceptado: guest permite exposición, vandalismo, spam, sobrescritura y pérdida de datos sin recuperación. Banner y cuota solo reducen sorpresa y abuso básico.
- Riesgo: NAT puede afectar a varias personas y varias IP pueden eludir el límite.

## Glosario

- **Guest:** visita anónima autorizada solo cuando la configuración efectiva lo permite.
- **Fail closed:** no ejecutar la operación si no puede aplicarse el límite.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | SPEC aprobada por la persona usuaria. |
