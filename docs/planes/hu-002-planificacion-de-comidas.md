# Propuesta de plan — HU-002: planificación de comidas

**Estado:** pendiente de aprobación; no autoriza implementación.  
**Referencia:** [HU-002](../historias-usuarios/HU-002-planificacion-de-comidas.md), [catálogo predeterminado](../etiquetas-predeterminadas.md) y [arquitectura](../arquitectura.md).  
**Rama de trabajo:** `feat/hu-002-meal-planning`.

## 1. Resultado esperado y punto de partida

Los usuarios activos autenticados consultan una planificación familiar compartida, semanal o mensual, y gestionan una etiqueta por almuerzo o cena. Las operaciones pueden repetirse cada N semanas; las asignaciones resultantes son registros independientes, nunca una serie permanente.

El código actual ya incorpora autenticación, sesiones revocables y CSRF en `backend/app/auth.py`, modelos SQLAlchemy en `backend/app/models.py` y migraciones hasta `0004_password_reset_rate_scopes`. `backend/app/main.py` monta el router de autenticación. No hay modelos ni rutas de etiquetas o planificación.

La interfaz de acceso y administración existe en `frontend/src/App.tsx`; `frontend/src/api.ts` centraliza cookies, CSRF y errores. El plan reutiliza estos contratos sin volver a implementar HU-001 ni dar por completadas sus verificaciones pendientes. Los documentos anteriores conservan estados históricos: el punto de partida técnico de este plan se fundamenta en el código actual.

## 2. Alcance y aclaraciones confirmadas

Se preservan CA-01–CA-10 y RN-01–RN-17 de la historia, con estas precisiones confirmadas por el usuario:

1. La repetición admite una **fecha final elegida por el usuario**, anterior al máximo anual. La fecha final es **inclusiva** si coincide con una ocurrencia calculada; no genera una ocurrencia fuera del intervalo semanal.
2. Para una fecha inicial distinta del 29 de febrero, el máximo final es el día anterior a la misma fecha del año siguiente. Para un inicio el **29 de febrero**, el máximo es el **28 de febrero del año siguiente, incluido**.
3. Se permite consultar y modificar fechas pasadas, incluidas operaciones repetidas cuyo inicio esté en el pasado; el máximo se calcula desde la fecha inicial, no desde hoy.

**Historia sincronizada:** las precisiones están incorporadas a la historia original, incluidos sus criterios, reglas, escenarios y definición de terminado. El [borrador TASKS](../../odd/tasks/hu-002-planificacion-de-comidas.md) se ha creado por petición expresa del usuario; su creación no aprueba el plan ni autoriza la implementación.

La repetición estará desactivada inicialmente. Al activarla se propondrá el máximo anual como fecha final, editable dentro del intervalo válido; es una propuesta de interfaz, no una nueva regla de negocio.

## 3. Propuesta técnica

### 3.1. Catálogo y persistencia

- Ampliar `backend/app/models.py` con `FoodLabel` y `MealAssignment` (nombres propuestos). No asociar las asignaciones a un usuario propietario: la planificación es única y compartida, y eliminar una cuenta no debe borrar comidas.
- `FoodLabel`: identificador UUID estable, código técnico único y nombre visible. La migración contendrá un mapa explícito de identificadores/códigos y cargará exactamente las **18 etiquetas** del catálogo. «Pescado» y «Sardinas», por ejemplo, son registros distintos. Los grupos orientativos no implican jerarquía ni asignación múltiple.
- `MealAssignment`: fecha SQL `DATE`, franja técnica `lunch` o `dinner`, y clave foránea obligatoria a `FoodLabel`. Una franja vacía se representa por ausencia de fila, no por una etiqueta nula.
- Restricción única de base de datos para `(date, slot)`, restricción de valores de franja y clave foránea que impida referencias a etiquetas inexistentes. No introducir tablas de series, ocurrencias pendientes ni reglas de borrado futuras.
- Crear la migración **prevista** `backend/migrations/versions/0005_meal_planning.py`, enlazada a `0004_password_reset_rate_scopes`, con tablas, restricciones y carga del catálogo. El `downgrade` solo afectará a las tablas de HU-002; probarlo exclusivamente en una base desechable.
- La migración es la fuente de carga inicial; consultar el calendario nunca insertará semillas ni asignaciones. Verificar estabilidad de IDs y ausencia de duplicados al volver a ejecutar `upgrade head`.

### 3.2. Fechas y repetición

Extraer el cálculo a funciones puras en el módulo **previsto** `backend/app/meal_planning.py`, separadas de las rutas HTTP:

1. Validar fecha, franja, etiqueta y, si hay repetición, `interval_weeks` entero positivo y `end_date` entre el inicio y el máximo anual, ambos incluidos. Rechazar valores fraccionarios, booleanos, cero, negativos y fechas inválidas.
2. Calcular cada ocurrencia como `start_date + k × 7 × interval_weeks` días, empezando por `k = 0`. Añadir solo fechas menores o iguales a `end_date`. No usar números de semana del año ni sumar horas UTC.
3. Para un intervalo mayor que la ventana disponible, el resultado es únicamente la fecha inicial; no es necesario imponer un máximo de semanas como nueva regla de producto. Evitar desbordamientos al evaluar intervalos grandes.
4. Usar fechas locales sin hora para planificación. Obtener «hoy» en `Atlantic/Canary` mediante un reloj controlable y mantener el mismo criterio en cliente y servidor; no interpretar una cadena de fecha como medianoche UTC para luego convertirla.

Ejemplos que deben convertirse en pruebas:

| Inicio / intervalo / final | Resultado o límite esperado |
| --- | --- |
| 2026-11-02 / 1 semana / 2026-11-30 | 2, 9, 16, 23 y 30 de noviembre. |
| 2026-11-02 / 1 semana / 2026-11-29 | Última ocurrencia el 23; no añadir el 29. |
| 2026-11-02 / máximo anual | Fecha final máxima 2027-11-01; excluir 2027-11-02. |
| 2028-02-29 / máximo anual | Fecha final máxima 2029-02-28, inclusiva como límite; solo generar fechas que respeten el intervalo. |
| 2026-12-25 / 3 semanas / 2027-02-05 | 25 de diciembre, 15 de enero y 5 de febrero. |

### 3.3. Contrato de API propuesto

Reutilizar `/api/v1`, `get_active_session`, `require_csrf` y `get_database_session`. Todas las rutas exigirán sesión activa; las escrituras y la previsualización por POST usarán origen permitido y CSRF. No incorporar un esquema de permisos distinto ni cambiar la configuración CORS existente para añadir métodos innecesarios.

| Ruta propuesta | Contrato |
| --- | --- |
| `GET /food-labels` | Catálogo de solo lectura: IDs estables, códigos y nombres visibles. Sin creación, edición ni borrado de etiquetas. |
| `GET /meal-planning?start_date=...&end_date=...` | Intervalo inclusivo validado; devuelve asignaciones ordenadas con fecha, franja y etiqueta. Las franjas ausentes se presentan sin planificar. Incluir la fecha actual y zona de referencia del servidor para inicializar la navegación de forma coherente. |
| `POST /meal-planning/preview` | Recibe la operación individual o repetida; devuelve fechas afectadas, asignaciones actuales, sustituciones o borrados efectivos y totales. No modifica datos de planificación. |
| `POST /meal-planning/operations` | Valida de nuevo y ejecuta una operación individual o repetida en una transacción. Devuelve el resumen efectivo y permite refrescar las vistas. |

El cuerpo de operación propuesto contendrá `action` (`assign` o `delete`), `start_date`, `slot`, `label_id`, repetición opcional con `interval_weeks` y `end_date`, y confirmación explícita cuando corresponda. `assign` sirve tanto para añadir como para sustituir. En un borrado, `label_id` representa exactamente la etiqueta seleccionada, no un grupo ni una coincidencia textual.

Respuestas de validación coherentes con la API actual: 401 para sesión no válida, 403 para CSRF/origen, 422 para parámetros o etiquetas no válidos y errores de disponibilidad sin exponer detalles SQL. Un intervalo invertido no es una consulta válida. Precisar los esquemas de respuesta durante la fase de contrato, antes de implementar cliente y servidor por separado.

### 3.4. Transacciones, concurrencia y confirmaciones

- Asignación individual o repetida: insertar o actualizar por `(date, slot)` de forma atómica, conservando la unicidad. No usar una secuencia vulnerable de consulta y alta sin protección contra inserciones concurrentes.
- Borrado individual o repetido: filtrar conjuntamente por fechas calculadas, franja y `label_id`. Si está vacío o contiene otra etiqueta, no modificarlo. Las asignaciones creadas después del commit no quedan sujetas a ninguna regla.
- Cada lote se confirma completo o se revierte completo. Ordenar las fechas de manera consistente y verificar en PostgreSQL la serialización de operaciones solapadas, incluidas franjas todavía vacías. Una propuesta acotada es un bloqueo transaccional compartido para escrituras de planificación; simplifica el orden de guardado a cambio de serializar los lotes familiares. No reutilizar el bloqueo de ciclo de vida de usuarios ni un bloqueo solo en memoria.
- Conservar «última escritura guardada prevalece». No introducir resolución manual de conflictos ni versionado optimista como nueva política de producto. La operación que se ejecuta después aplica sus reglas sobre el estado entonces disponible; en borrados sigue vigente el filtro de etiqueta exacta.
- Antes de sustituir una asignación ocupada, mostrar confirmación. En operaciones repetidas, previsualizar el intervalo y las asignaciones que se reemplazarán o eliminarán; al cancelar no debe enviarse la operación de guardado.
- La previsualización es informativa, no reserva las franjas ni mantiene una transacción abierta mientras el usuario decide. La confirmación debe explicar que abarca las fechas de la operación y que pueden haberse producido cambios ajenos. Al guardar, recalcular sobre el estado actual bajo la política anterior y devolver el efecto real. Si una asignación inicialmente vacía pasa a estar ocupada y no hay consentimiento de sustitución, no sobrescribirla silenciosamente: solicitar confirmación y presentar el estado actualizado.

## 4. Interfaz y organización de archivos

Extender la pantalla autenticada de `frontend/src/App.tsx` conservando acceso y administración de usuarios. Reutilizar `apiRequest` y el token CSRF de la sesión. No introducir un framework de rutas o calendario sin necesidad demostrada.

Separar la nueva funcionalidad en los archivos **previstos** `frontend/src/MealPlanning.tsx`, `frontend/src/mealPlanningDates.ts` y `frontend/src/mealPlanningApi.ts`, con pruebas próximas a cada módulo. Son ubicaciones propuestas, no archivos ya existentes.

- Mantener una única fecha de referencia y un estado de vista semanal/mensual. Cambiar de vista conserva esa fecha; la navegación semanal desplaza siete días y la mensual cambia el mes, sin arrastrar accidentalmente los días 29–31 al siguiente. Cubrir explícitamente el ajuste al último día válido del mes destino.
- Semana de lunes a domingo; mes con lunes como primera columna, fechas inequívocas al cruzar meses/años y almuerzo/cena diferenciados. Construir ambas vistas a partir del mismo conjunto de asignaciones por fecha y franja.
- Editor individual accesible con selector de etiqueta, repetición desactivada inicialmente, intervalo y fecha final cuando corresponda. Reutilizar el mismo cálculo contractual para mostrar límites, manteniendo la validación del servidor como autoridad.
- Mostrar carga, errores, confirmación y resultado. Impedir envíos duplicados mientras una petición está pendiente y evitar que una respuesta antigua sobrescriba otra consulta más reciente al navegar rápidamente.
- Tras guardar, volver a consultar el intervalo visible; al alternar vistas no conservar una copia obsoleta de los datos. No se requiere actualización en tiempo real: los demás usuarios ven cambios al refrescar o consultar de nuevo.
- Manejar una sesión caducada o revocada usando el flujo de acceso existente, sin dejar controles de escritura aparentemente activos.

## 5. Fases, dependencias y pruebas de salida

Estas fases son una propuesta de orden, no un documento TASKS ni autorización de ejecución.

| Fase | Entrega propuesta y dependencias | Prueba de salida / trazabilidad |
| --- | --- | --- |
| 1. Contratos y alineación documental | Comprobar la coherencia con la historia ya actualizada; fijar cuerpos/respuestas y ejemplos. Base para todas las demás fases. | CA-01–CA-10 cubiertos por contratos y matriz; fechas finales y caso bisiesto inequívocos. |
| 2. Catálogo y persistencia | Modelos, migración desde `0004`, 18 etiquetas con IDs estables y restricciones. Depende de 1. | Catálogo exacto; fechas/franjas únicas; FK válida; actualización de una base con usuarios conserva HU-001. CA-04, CA-09, CA-10. |
| 3. Reglas de calendario y lectura | Cálculo puro de fechas e intervalos; consulta autenticada del catálogo y de asignaciones. Depende de 1–2. | Cruces de mes/año, fechas pasadas, reloj canario y final inclusivo; consultar no crea datos. CA-01–CA-03, CA-05, CA-08, CA-09. |
| 4. Operaciones individuales y repetidas | Previsualización, confirmaciones, transacciones, sustitución y borrado exacto; controles de acceso/CSRF. Depende de 2–3. | Sin resultados parciales, sin duplicados, sin borrado de etiquetas diferentes; última escritura prevalece en operaciones concurrentes. CA-04–CA-10. |
| 5. Vistas y edición integrada | Vista semanal/mensual, navegación, editor y confirmaciones conectados a la API. Depende de contratos de 1 y API de 3–4; el trabajo visual puede usar respuestas simuladas antes. | Alternancia conserva referencia, datos coherentes y flujos completos de asignar/sustituir/borrar/cancelar. CA-01–CA-10. |
| 6. Verificación y documentación | Ejecutar escenarios de HU-002, regresión de HU-001, integración PostgreSQL y comprobación en navegador; actualizar manuales. Depende de 2–5. | Evidencia por criterio y por punto de la definición de terminado, sin marcar completado lo no verificado. |

## 6. Estrategia de verificación

- **Reglas puras:** pytest con fechas explícitas y reloj controlable. Probar semanas de 1, 2 y 3 intervalos, año bisiesto, límite anual, fin inclusivo, fin no coincidente, inicio igual a fin, intervalos mayores que la ventana y fechas históricas. Sin esperas ni dependencia de la fecha real de ejecución.
- **API local:** reutilizar el patrón de base SQLite temporal e inyección de dependencias observado en `backend/tests/test_auth.py`, sin confundir esa evidencia con PostgreSQL. Archivos **previstos** `backend/tests/test_meal_planning.py` y `backend/tests/test_meal_planning_dates.py`: validación, permisos, CSRF, previsualización, confirmación, ausencia de efectos al cancelar, edición independiente y consultas repetidas sin escrituras.
- **PostgreSQL aislado:** ampliar `backend/tests/test_database_integration.py` para migración nueva, catálogo, restricciones, rollback completo ante fallo y carreras entre altas/sustituciones/borrados, con conexiones independientes. Actualizar su expectativa de revisión Alembic, actualmente fijada a `0004_password_reset_rate_scopes`. Verificar que borrar un usuario no elimina la planificación compartida. No usar SQLite como prueba de bloqueo o concurrencia real.
- **Frontend:** Vitest para aritmética de calendario, fecha de referencia compartida, estados de carga/error, respuestas fuera de orden y contratos del cliente. Comprobar el soporte de pruebas de interacción antes de añadir herramientas; no presuponer que la configuración actual ejecuta interacciones de navegador. Añadir comprobación integral en navegador de los 22 escenarios de la historia actualizada.
- **Regresión:** acceso, sesiones, usuarios y recuperación deben conservar su comportamiento. La nueva migración no altera tablas ni datos de autenticación.

Comandos existentes de comprobación local, a ejecutar durante la implementación, no en esta planificación:

```bash
# Desde la raíz: pytest con .venv y Vitest; excluye la integración PostgreSQL.
make test

# Tipos y paquete de producción del frontend.
make build-frontend

# Prueba de reglas/API local enfocada, cuando existan los archivos previstos.
cd backend
../.venv/bin/python -m pytest -q tests/test_meal_planning.py tests/test_meal_planning_dates.py
```

La integración se ejecutará **aparte** con `RUN_DB_INTEGRATION=1`, apuntando exclusivamente a un proyecto Compose/base nueva y aislada, con las migraciones aplicadas y la configuración reproducible del [README](../../README.md). El comando local del módulo es `cd backend && RUN_DB_INTEGRATION=1 ../.venv/bin/python -m pytest -q tests/test_database_integration.py`, pero **no debe ejecutarse sin preparar primero ese aislamiento**. `make test` no prueba migraciones ni concurrencia PostgreSQL y no sustituye esta verificación.

## 7. Riesgos, exclusiones y aprobación

- **Coherencia documental:** mantener la historia ya actualizada, este plan y el TASKS alineados; no resolver contradicciones silenciosamente en el código.
- **Concurrencia entre previsualizar y guardar:** la confirmación no es una reserva. Probar el estado real al guardar, las franjas inicialmente vacías y las operaciones repetidas solapadas.
- **Diferencias de base de datos:** SQLite permite pruebas rápidas, pero solo PostgreSQL acredita los bloqueos, restricciones y transacciones previstos.
- **Fechas del navegador:** evitar conversiones UTC que desplacen el día y navegación mensual que salte meses; verificar desde zonas de navegador distintas de `Atlantic/Canary`.
- **HU-001:** reutilizar lo implementado sin dar por cerradas tareas históricas todavía pendientes; un fallo de autenticación preexistente debe quedar registrado como tal.

Quedan fuera recetas concretas, creación/edición/borrado de etiquetas por usuarios, multihogar, nuevos roles, series permanentes, actualizaciones en tiempo real, importaciones, despliegue remoto y cambios de credenciales. No se introduce una biblioteca de calendario, un nuevo almacén de estado ni una reestructuración global de la aplicación como condición de esta historia.

Este documento queda **pendiente de aprobación**. El usuario ha solicitado expresamente el [borrador TASKS de HU-002](../../odd/tasks/hu-002-planificacion-de-comidas.md), también pendiente de aprobación. Ninguno autoriza cambios de código, migraciones en una base real, commits, fusiones, tags, publicación o PR; la implementación requiere autorización posterior, según el [índice de planes y tareas](README.md).
