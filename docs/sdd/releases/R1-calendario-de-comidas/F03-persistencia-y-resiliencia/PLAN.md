# PLAN — F03 Persistencia y resiliencia

**Estado:** APPROVED · **Versión:** 0.1  
**SPEC base:** [`SPEC.md`](SPEC.md) v0.1, estado `APPROVED`, aprobada por la persona usuaria el 2026-09-16.  
**Dependencias:** PostgreSQL; `recipes(id)` antes de la FK real.  
**Cubre:** US-PER-001…004; CA-PER-001…012; RD-PER-001…005.

## Arquitectura

Este PLAN canoniza la fuente de verdad y los contratos de fallo. PostgreSQL contiene el singleton `meal_calendars('shared')`, `meal_assignments` polimórficas y `meal_calendar_rate_limits`. El repositorio es el único componente que abre transacciones y clasifica fallos transitorios. La capa API traduce errores al sobre JSON de la SPEC; el servicio no filtra errores de driver.

Cada operación de base de datos hace un intento inicial y exactamente tres reintentos (250 ms, 500 ms, 1 s); cada reintento de escritura abre transacción nueva. El cliente no reintenta datos automáticamente: conserva el descriptor de una operación fallida y `Reintentar` crea una solicitud nueva. Sin locks, versiones o ETags, la última transacción de actualización confirmada prevalece; un `PATCH` tardío después de `DELETE` devuelve `404`.

## Hitos

1. Añadir migración expandible: singleton, asignaciones, checks, índices y buckets; insertar exactamente `shared`.
2. Implementar repositorios, transacciones, clasificación de errores, idempotencia de alta/baja y unión de recetas actual.
3. Exponer contratos API comunes, incluyendo errores y cabeceras `Cache-Control: no-store`.
4. Implementar máquina de estado de carga, borradores, guardado individual, fallo y navegación en coordinación con F05.
5. Validar concurrencia y recuperación aislada contra PostgreSQL efímero.

## Datos e interfaces

- No hay `created_at`, propietario ni índice único por fecha, turno, receta o texto; UUID distintos coexisten.
- La migración usa `DATE`, `lunch|dinner`, `recipe|free_text`, checks de consistencia e índices semanal/celda, receta parcial y limpieza de buckets.
- `recipe_id` usa `ON DELETE SET NULL`; nunca snapshot. La FK se añade cuando exista `recipes(id)`.
- Las rutas usan JSON UTF-8, `/api/v1/meal-calendar`, `Cache-Control: no-store`; `503 database_unavailable` incluye `retryable=true` y el mensaje exacto de la SPEC.
- F01 define tiempo y semana, F02 el contenido, F04 buckets/cuota y F05 la representación y accesibilidad de estados.

## Seguridad, observabilidad e infraestructura

PostgreSQL es obligatorio y compartido entre réplicas; no se admite contador de memoria. Las migraciones no ejecutan downgrade destructivo automático. Registrar intentos, agotamiento de reintentos, conflictos de idempotencia y `404` posterior a borrado, sin valores de formularios. Métricas, alertas, plataforma de despliegue, gestor de migraciones y política de backups quedan pendientes; deben permitir comprobar migración expandible y recuperación sin borrar planes.

## Pruebas

Pruebas unitarias: clasificación y calendario de reintentos. Integración con PostgreSQL efímero: migración/checks, duplicados, `ON DELETE SET NULL`, idempotencia, cuatro intentos, concurrencia, borrado y buckets atómicos. Contrato: estados, cuerpos, cabeceras y errores. El estado frontend se probará cuando se seleccione su runner.

## Despliegue y riesgos

Aplicar primero migración compatible y backend; luego clientes. Mantener `ENABLE_GUEST_USER=false` por defecto; F04 decide su activación operativa tras reinicio. Rollback de aplicación deja esquema y datos; retirar tablas exige backup y operación separada. Riesgos: PostgreSQL indisponible bloquea operaciones y cuota, y última escritura gana pierde cambios sin historial; son comportamientos deliberados de la SPEC.

## Decisiones pendientes

- Migrador versionado, plataforma, observabilidad, backups y runner frontend.
- Forma concreta de PostgreSQL efímero en CI, preservando el contrato de pruebas.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | PLAN aprobado por la persona usuaria. |
