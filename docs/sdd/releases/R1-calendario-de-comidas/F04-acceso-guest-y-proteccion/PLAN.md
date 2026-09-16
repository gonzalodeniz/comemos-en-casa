# PLAN — F04 Acceso guest y protección

**Estado:** APPROVED · **Versión:** 0.1  
**SPEC base:** [`SPEC.md`](SPEC.md) v0.1, estado `APPROVED`, aprobada por la persona usuaria el 2026-09-16.  
**Dependencias:** [F03](../F03-persistencia-y-resiliencia/PLAN.md); issue #6 cuando guest esté deshabilitado.  
**Cubre:** US-ACC-001…003; CA-ACC-001…010; RD-ACC-001…006.

## Arquitectura

Este PLAN canoniza acceso y limitación. Al inicio de proceso, settings recorta y acepta únicamente `true`/`false` en minúsculas para `ENABLE_GUEST_USER`; ausencia equivale a `false` y otro valor aborta. El valor permanece inmutable y `GET /context` lo devuelve como `guestMode`.

Un middleware común a todas las rutas de calendario primero identifica IP según socket y proxies explícitamente confiables, aplica cuota y después resuelve acceso. Con guest activo acepta visitas anónimas y autenticadas sobre `calendar_key='shared'`; con guest inactivo delega exclusivamente la credencial a la issue #6 y devuelve `401 authentication_required` si no existe. No crea login, identidad ni propiedad.

Los buckets PostgreSQL de F03 son por IP, minuto UTC fijo y clase. Una inserción/upsert condicionado incrementa una vez al ingreso: 60 lecturas (GET/HEAD/OPTIONS) y 30 escrituras (POST/PATCH/DELETE) por minuto. Los reintentos internos no consumen cuota; la solicitud manual sí.

## Hitos

1. Implementar parsing inmutable de configuración y pruebas de arranque seguro.
2. Implementar middleware de acceso compartido y delegación a #6 sin interfaz alternativa.
3. Implementar operación atómica de cuota, `429`, `Retry-After` y cabeceras de límite/restantes/reset.
4. Integrar `guestMode`, banner y feedback con F05; probar fallo cerrado al no poder consultar bucket.

## Datos e interfaces

- `GET /context` expone `guestMode` con zona y semana de F01.
- El bucket usa IP, inicio de ventana y `read|write`; F03 es dueño del esquema y de los reintentos de infraestructura.
- `429 rate_limited` no se reintenta automáticamente y produce el texto exacto de CA-ACC-010 en la UI de F05.
- El banner se muestra desde contexto antes de cargar semana, ocupa fila propia y no puede cerrarse; su copia exacta pertenece a CA-ACC-007.

## Seguridad, observabilidad e infraestructura

No aceptar cabeceras de proxy salvo configuración explícita de proxy confiable. Si el almacén de cuota falla, se reintenta como F03 y se cierra con `503`, sin ejecutar la operación. Medir límites excedidos, fallos de almacén y arranques con modo efectivo sin registrar IPs crudas innecesariamente. La configuración de proxies, destino de logs/métricas y plataforma de despliegue son decisiones pendientes.

## Pruebas

Con `pytest`: parsing de valores, ausencia, espacios y abortos; acceso guest/no guest; dependencia de #6 y `401`; clasificación de rutas; límites separados 60/30, reset UTC, headers, atomicidad, reintentos internos y fallo cerrado. Tras elegir runner frontend, verificar banner en carga inicial, ausencia con guest inactivo y toast alcanzable por teclado.

## Despliegue y riesgos

Desplegar backend con guest deshabilitado por defecto. Habilitar guest exige decisión operativa explícita y reinicio; deshabilitarlo conserva datos y corta el acceso anónimo. Riesgos aceptados: exposición, vandalismo, spam, sobrescritura y pérdida sin recuperación; NAT penaliza grupos y múltiples IP pueden eludir cuotas. No se añaden mitigaciones encubiertas.

## Decisiones pendientes

- Integración concreta de la credencial de issue #6.
- Configuración de proxies confiables, observabilidad y despliegue.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | PLAN aprobado por la persona usuaria. |
