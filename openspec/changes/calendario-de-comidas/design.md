# Diseño técnico: calendario de comidas

**Cambio:** `calendario-de-comidas`  
**Estado:** diseño listo para planificación; aplicación bloqueada  
**Base aprobada:** `proposal.md` y las cinco especificaciones del cambio

## 1. Decisión resumida

Se construirá una feature web con un frontend orientado a estados, un backend Python y PostgreSQL como fuente de verdad. Todas las visitas con acceso operan sobre un único calendario compartido; `ENABLE_GUEST_USER=true` permite acceso anónimo a ese mismo calendario y no crea identidades, calendarios ni propiedad por visitante.

Las fechas se almacenan como `DATE` y el backend calcula `Hoy` y el lunes de la semana en `Europe/Canary`. Las asignaciones de receta y texto libre comparten una tabla, admiten duplicados y no guardan copias del título ni de la imagen de recetas. Los errores transitorios de PostgreSQL se reintentan en backend; el frontend conserva borradores y permite reintentar solo la operación fallida.

No se selecciona aquí framework frontend, framework HTTP Python, librería visual ni despliegue. Sí se fijan los contratos observables, límites de módulos, esquema, estados y rutas documentales que cualquier selección posterior deberá respetar.

## 2. Contexto, alcance y restricciones

- El repositorio no tiene aplicación, manifiestos, framework, runner ni pruebas ejecutables.
- Se activa **TDD estricto** para la implementación: cada tarea de código deberá seguir RED → GREEN → TRIANGULATE → REFACTOR y registrar evidencia. El comando de prueba obligatorio será `pytest` una vez configurado el proyecto.
- Se activa **RDD (Receipt-Driven Development)** para los candidatos de implementación: cada candidato deberá conservar evidencia y revisión independiente ligadas a su línea exacta; RDD no autoriza commits, pushes, PRs ni releases.
- Aunque la activación queda decidida en este diseño, todavía no hay comandos configurados de test, lint, typecheck o formato. La primera tarea de implementación deberá crear el esqueleto Python y configurar `pytest`; hasta entonces no podrá afirmarse que las pruebas automatizadas pasan.
- El catálogo de recetas aporta recetas públicas con identificador estable, título actual, portada y detalle. La visibilidad pública/privada de la issue #5 no se incorpora.
- Con guest deshabilitado, la autenticación es responsabilidad exclusiva de la issue #6. Esta feature no crea login.
- No se añaden calendarios personales, propiedad, roles, auditoría, historial, deshacer, resolución de conflictos ni funcionamiento offline.
- Permanecen fuera de alcance drag and drop, recurrencias, copia o borrado completo de semanas, limpieza de planes, festivos, resaltado especial de la semana actual, nutrición, cantidades, horarios, recordatorios, preparación anticipada, listas de compra y CAPTCHA.

## 3. Arquitectura y límites

```text
Navegador
  └─ feature calendario
      ├─ estado de semana, borradores, modal, tooltip y foco
      └─ cliente HTTP sin reintentos automáticos de datos
             │
             ▼
Backend Python /api/v1/meal-calendar
  ├─ middleware de acceso y rate limiting
  ├─ API: validación y traducción de errores
  ├─ servicio: semana canaria, sanitización y casos de uso
  ├─ repositorio: transacciones y reintentos PostgreSQL
  └─ adaptador de catálogo público
             │
             ▼
PostgreSQL: calendario compartido, asignaciones, recetas y buckets de límite
```

### Backend

El backend es autoritativo para acceso, configuración efectiva, fecha actual canaria, validación, sanitización, existencia de recetas, rate limiting, reintentos y persistencia. El repositorio ejecuta SQL; el servicio no filtra errores de driver hacia la API.

La integración de recetas se hace mediante un adaptador interno. En el primer despliegue se asume que el catálogo y el calendario usan la misma PostgreSQL, lo que permite una clave foránea y lecturas con `LEFT JOIN`. Si en el futuro el catálogo se separa, deberá conservar el mismo contrato y una estrategia explícita de tombstones antes de retirar la clave foránea.

### Frontend

El frontend es autoritativo solo para interacción efímera: destino de navegación, borradores, revisiones en vuelo, feedback, temporizadores de `Guardado`, contexto de modal, scroll y foco. Nunca decide acceso, no confía en validación solo cliente y no conserva un calendario alternativo local.

Rutas lógicas recomendadas para la futura base de código:

- `backend/src/comemos_en_casa/meal_calendar/`: `api`, `service`, `repository`, `schemas`, `settings`, `rate_limit`.
- `backend/tests/meal_calendar/`: pruebas unitarias y de integración pytest.
- `frontend/src/features/meal-calendar/`: API client, store/state machine, grid, editors, modal y feedback.

Estas rutas no seleccionan framework; si el scaffolding adopta otra convención, deberá mantener los mismos límites y contratos.

## 4. Contrato temporal y semanal

1. El backend obtiene un instante UTC consciente de zona, lo convierte con `zoneinfo.ZoneInfo("Europe/Canary")`, toma la fecha local y resta `weekday()` días para obtener el lunes.
2. `weekStart` y `date` viajan como ISO `YYYY-MM-DD`; nunca como timestamp ni como fecha interpretada en la zona del navegador.
3. Anterior y siguiente suman o restan siete días de calendario al lunes, no 168 horas. Así los cambios de horario de verano no desplazan fechas.
4. El backend rechaza con `422 invalid_week_start` una fecha que no sea lunes. No existe un límite de producto para navegar; solo aplican los límites representables de la plataforma y PostgreSQL.
5. `Hoy` consulta de nuevo el contexto al backend para no quedar obsoleto si la pestaña atraviesa medianoche canaria.
6. El rango visible es inclusivo `[weekStart, weekStart + 6 días]`; se formatea en español en la presentación sin cambiar sus fechas.

El reloj y la función de cálculo serán inyectables para probar medianoche, cambio de año y transiciones DST de Canarias.

## 5. Contratos HTTP y recursos

Todos los endpoints usan JSON UTF-8 bajo `/api/v1/meal-calendar`, `Cache-Control: no-store` y el mismo middleware de acceso y límites.

### Lecturas

| Método y ruta | Respuesta y semántica |
| --- | --- |
| `GET /context` | `{timezone, currentWeekStart, guestMode}`. Se resuelve antes de montar la cuadrícula; con guest activo permite mostrar banner y skeleton juntos. `Hoy` vuelve a consultarlo. |
| `GET /weeks/{weekStart}` | `{weekStart, weekEnd, timezone, assignments[]}`. Exige lunes; incluye todas las asignaciones del rango y datos actuales de receta. Siempre vuelve a PostgreSQL, incluso al revisitar. |
| `GET /recipes?q=&cursor=&limit=` | Fachada del catálogo público. Busca solo por título con normalización Unicode, sin caja ni acentos. `q` vacío lista el catálogo; `limit` máximo 50 y cursor permiten recorrerlo completo. |
| `GET /recipes/{recipeId}` | Detalle público para el modal. No expone edición. Una receta eliminada responde `404 recipe_not_found`. |

`assignments[]` se ordena en backend por fecha, turno y una clave derivada del texto visible: normalización NFKD, eliminación de marcas combinantes y `casefold`; los empates se resuelven por UUID. Esta regla ordena conjuntamente recetas, textos y `Receta no disponible` sin deduplicar.

### Mutaciones

| Método y ruta | Contrato |
| --- | --- |
| `POST /assignments` | Crea una asignación con `{id, date, slot, kind, recipeId?, text?}`. `id` es UUID generado una vez por el cliente y reutilizado en reintentos. Devuelve `201`; repetir el mismo ID y payload devuelve `200`, evitando duplicados de transporte. El mismo ID con otro payload devuelve `409 idempotency_conflict`. |
| `PATCH /assignments/{id}` | Actualiza fecha, turno y el valor propio del tipo. `kind` es inmutable; cambiar receta/texto exige otra asignación. Devuelve el recurso actual. No usa versión ni `If-Match`: gana la última transacción confirmada. |
| `DELETE /assignments/{id}` | Desasigna o elimina solo la asignación. Devuelve `204`; repetirlo también devuelve `204`. Nunca borra una receta. |

`slot` admite únicamente `lunch` y `dinner`, presentados como `Comida` y `Cena`. `kind` admite `recipe` y `free_text`. La API permite duplicados porque cada alta lleva UUID independiente.

Una asignación de receta disponible se representa así:

```json
{"id":"uuid","date":"2026-05-12","slot":"lunch","kind":"recipe","recipe":{"id":"uuid","available":true,"title":"Tortilla española","coverImageUrl":"https://..."}}
```

Su tarjeta ofrece detalle y `Desasignar` como acciones directas; `Desasignar` queda fuera del modal y no pide confirmación. Si la receta fue borrada, `recipe` será `{"id":null,"available":false,"title":"Receta no disponible","coverImageUrl":null}`. La UI mantiene el mismo ratio de portada como cuadro vacío y muestra siempre `Desasignar`; no abre modal.

Una asignación libre devuelve `text` sanitizado y no devuelve receta ni imagen. El texto se normaliza a NFC, se recortan espacios exteriores, se procesa con un sanitizador HTML de lista permitida vacía y se valida después. El resultado debe contener de 1 a 100 puntos de código Unicode; no se cuentan bytes UTF-8. Una secuencia emoji compuesta puede ocupar varios puntos de código. El frontend vuelve a renderizarla con primitivas de texto (`textContent` o equivalente), nunca HTML interpretado.

### Errores

Todos los errores tienen la forma:

```json
{"error":{"code":"database_unavailable","message":"…","retryable":true,"fieldErrors":{}}}
```

| HTTP | Código | Semántica frontend |
| --- | --- | --- |
| `400` | `malformed_request` | JSON o parámetros ilegibles; no reintentar. |
| `401` | `authentication_required` | Guest deshabilitado y issue #6 sin credencial válida; no mostrar login propio. |
| `404` | `assignment_not_found` / `recipe_not_found` | Refrescar el recurso afectado; una receta ausente se presenta como no disponible. |
| `409` | `idempotency_conflict` | No repetir la creación con payload distinto. No se usa para concurrencia normal. |
| `422` | `validation_failed` / `invalid_week_start` | Asociar `fieldErrors` al formulario accesible; conserva el borrador. |
| `429` | `rate_limited` | Incluye `Retry-After` y el mensaje exacto `Has superado el límite de solicitudes. Inténtalo de nuevo en un minuto.` |
| `503` | `database_unavailable` | Tras agotar reintentos; mensaje exacto `No se pudo conectar con la base de datos. El cambio no se guardó. Inténtalo de nuevo.` y `retryable=true`. |

No existe endpoint de health check para esta feature. Validación, no encontrado, autenticación y límite no son fallos de PostgreSQL reintentables. Un conflicto de actualización contra una fila ya eliminada responde `404` y no resucita datos.

## 6. PostgreSQL y migraciones

### Esquema

```sql
CREATE TABLE meal_calendars (
  calendar_key text PRIMARY KEY CHECK (calendar_key = 'shared')
);

CREATE TABLE meal_assignments (
  id uuid PRIMARY KEY,
  calendar_key text NOT NULL REFERENCES meal_calendars(calendar_key),
  meal_date date NOT NULL,
  meal_slot text NOT NULL CHECK (meal_slot IN ('lunch', 'dinner')),
  assignment_kind text NOT NULL CHECK (assignment_kind IN ('recipe', 'free_text')),
  recipe_id uuid NULL REFERENCES recipes(id) ON DELETE SET NULL,
  free_text text NULL,
  CHECK (
    (assignment_kind = 'recipe' AND free_text IS NULL) OR
    (assignment_kind = 'free_text' AND recipe_id IS NULL AND free_text IS NOT NULL
      AND free_text = btrim(free_text)
      AND char_length(free_text) BETWEEN 1 AND 100)
  )
);

CREATE INDEX meal_assignments_week_cell_idx
  ON meal_assignments (calendar_key, meal_date, meal_slot);
CREATE INDEX meal_assignments_recipe_idx
  ON meal_assignments (recipe_id) WHERE recipe_id IS NOT NULL;

CREATE TABLE meal_calendar_rate_limits (
  client_ip inet NOT NULL,
  window_start timestamptz NOT NULL,
  operation_class text NOT NULL CHECK (operation_class IN ('read', 'write')),
  request_count integer NOT NULL CHECK (request_count > 0),
  PRIMARY KEY (client_ip, window_start, operation_class)
);
CREATE INDEX meal_calendar_rate_limits_cleanup_idx
  ON meal_calendar_rate_limits (window_start);
```

La migración inserta exactamente `meal_calendars('shared')`. No hay usuario, propietario ni `created_at` en asignaciones. Tampoco hay restricción única por fecha, turno, receta o texto, por lo que los duplicados son válidos. La sanitización/NFC requiere backend; los `CHECK` son defensa adicional, no su sustituto.

`recipes(id)` debe existir antes de añadir la clave foránea. `ON DELETE SET NULL` conserva la asignación sin snapshot: un `LEFT JOIN` usa siempre título e imagen actuales, y `recipe_id IS NULL` en una asignación `recipe` produce el estado no disponible. La API solo permite crear una receta con un `recipe_id` existente; el `NULL` de ese tipo es un tombstone producido por borrado.

El catálogo deberá mantener una clave de búsqueda de título con la misma normalización sin caja ni acentos y un índice adecuado. Esa columna/índice pertenece a la migración del catálogo, no a la tabla de calendario.

### Secuencia y rollback

1. Crear/configurar el proyecto Python, migrador versionado y pytest; verificar una base PostgreSQL efímera antes de migrar producción.
2. Aplicar migración expandible: singleton, asignaciones, índices y buckets; añadir la FK después de existir `recipes`.
3. Desplegar backend compatible y mantener `ENABLE_GUEST_USER=false` por defecto.
4. Desplegar frontend y habilitar guest solo mediante decisión operativa explícita seguida de reinicio.

Deshabilitar guest no modifica ni borra filas. Un rollback de aplicación deja el esquema y los datos; no se ejecuta automáticamente un downgrade destructivo. Retirar tablas requiere copia de seguridad y una operación separada. Los buckets de rate limit pueden purgarse por ventana mediante tarea operativa; esta limpieza no toca planes, que se conservan indefinidamente.

## 7. Reintentos, concurrencia y rate limiting

### PostgreSQL

Cada operación real de calendario o catálogo captura errores transitorios de conexión/timeout en repositorio. Hace un intento inicial y exactamente tres reintentos tras 250 ms, 500 ms y 1 s. Cada intento de escritura abre una transacción nueva. El UUID de creación y la idempotencia de borrado evitan duplicados si se pierde una respuesta. El frontend no añade reintentos automáticos, para no multiplicar los cuatro intentos del backend.

Tras `503`, el toast conserva un descriptor de esa única operación. `Reintentar` emite una nueva solicitud para ese descriptor, que vuelve a disponer de su ciclo backend. Si el borrador cambió, el descriptor anterior se invalida y el nuevo valor constituye otra operación.

No hay locks de usuario, versiones, ETags de escritura ni historial. Entre actualizaciones válidas del mismo UUID, queda el valor de la transacción que confirme última. Altas concurrentes con UUID distintos coexisten. Un borrado confirmado no se deshace por una actualización tardía.

### Límites por IP/minuto

- GET/HEAD/OPTIONS de `context`, semanas, búsqueda y detalle son lecturas: máximo 60 por IP y minuto.
- POST/PATCH/DELETE son escrituras: máximo 30 por IP y minuto.
- Los contadores son independientes, incluyen tráfico guest y autenticado, y usan ventanas fijas basadas en el minuto UTC de PostgreSQL.
- Un `INSERT … ON CONFLICT … DO UPDATE` condicionado incrementa atómicamente hasta el máximo; la siguiente petición recibe `429`, `Retry-After` con los segundos restantes y headers de límite/restantes/reset.
- El incremento ocurre una vez en el ingreso. Los reintentos internos de repositorio no consumen más cuota; un reintento manual sí es una petición nueva.
- La IP procede del socket. Cabeceras proxy solo se aceptan desde proxies configurados como confiables, evitando suplantación de `X-Forwarded-For`.
- Si el almacén del límite no está disponible, se aplican los tres reintentos de conexión y se falla cerrado con `503`; no se ejecuta la operación sin límite.

Usar PostgreSQL evita introducir Redis y mantiene contadores coherentes entre réplicas, a cambio de una escritura pequeña por petición y dependencia del mismo servicio que se protege. Si el volumen futuro lo exige, el adaptador podrá pasar a un gateway/almacén atómico compartido sin cambiar la semántica HTTP. No se permite un contador solo en memoria en despliegues con varias réplicas.

## 8. Ciclo de configuración guest

- Al arrancar, settings lee una sola vez `ENABLE_GUEST_USER`.
- Ausencia equivale a `false`; se aceptan, tras recortar espacios, únicamente `true` o `false` en minúsculas. Otro valor aborta el arranque para no abrir acceso por error.
- El valor efectivo es inmutable durante el proceso y se devuelve como `guestMode` en `/context`.
- Con `true`, el middleware acepta anónimos y autenticados sobre `calendar_key='shared'`. El banner aparece para ambos.
- Con `false`, el middleware exige la credencial de #6. Si esa integración no existe, responde `401`; no se ofrece login alternativo.
- Cambiar `.env` no tiene efecto hasta reiniciar. Pasar a `false` corta acceso anónimo pero conserva todas las asignaciones.

El banner ocupa una fila propia desde que `/context` autoriza el montaje y antes de pedir la semana. Es persistente, no tiene cierre y muestra exactamente: `El modo guest está activo: este calendario es público y compartido. Cualquier persona puede ver y cambiar las asignaciones.`

El riesgo guest se acepta sin mitigaciones encubiertas: cualquier visitante puede leer, crear, editar o borrar datos ajenos; puede haber exposición, vandalismo, spam, sobrescritura y pérdida sin autoría ni recuperación. Banner y límites reducen sorpresa y abuso básico, pero no crean privacidad ni propiedad.

## 9. Modelo de estado del frontend

### Semana y navegación

- `bootstrapping`: obtiene `/context`; todavía no monta controles de datos.
- `initialLoading`: banner guest ya visible si aplica; cuadrícula skeleton, edición inerte y navegación disponible.
- `ready(week, data)`: contenido editable.
- `navigating(target, staleData, requestToken)`: encabezado indica destino, datos anteriores quedan debajo de overlay/skeleton, `aria-hidden` e inertes. Al resolver el token vigente se reemplazan atómicamente.
- `readFailed(target, staleData, failedOperation)`: conserva datos anteriores, muestra toast exacto y permite reintentar solo esa lectura.

Cada intención de navegación recibe un token creciente. Una nueva intención durante lectura cancela/ignora la respuesta anterior. Si hay guardados activos, se conserva el último destino solicitado y se espera a que terminen; los botones nunca se deshabilitan. Si al terminar queda una operación fallida, se conserva su borrador y se confirma antes de abandonar. Al navegar se cancela la acción manual asociada al toast de la semana origen, no su borrador en memoria.

Los borradores se indexan por semana y UUID temporal. Aceptar una salida de un borrador ordinario permite descartarlo; un borrador de mutación fallida se retiene durante la sesión y reaparece al volver. No se promete persistencia offline ni después de cerrar la pestaña. `beforeunload`, cambio de semana, cierre de editor y cierre de ruta usan la misma confirmación cuando existe estado `dirty` o `failed`.

### Guardado individual

Cada editor mantiene `{revision, persistedRevision, inFlightRevision, status}`:

- `clean`: no habilita `Guardar`.
- `dirty`: habilita `Guardar`; blur o botón encola la revisión actual.
- `saving`: muestra `Guardando`; otro blur/Guardar no duplica la solicitud.
- Si cambia durante `saving`, incrementa `revision`; al completar, queda `dirty` y se ejecuta como máximo un guardado posterior con el valor nuevo.
- `saved`: muestra `Guardado` durante 2 segundos y luego vuelve a `clean`; una nueva edición cancela el temporizador.
- `failed`: mantiene formulario/valor y referencia a una sola operación reintentable.

`Guardar` sincroniza primero el valor del control enfocado y luego encola todas las revisiones sucias del formulario. Cada asignación conserva feedback individual. Una baja es visualmente inmediata: la tarjeta queda retirada pero retenida como tombstone local mientras se ejecuta; si falla tras reintentos, se restaura con su acción `Reintentar`.

### Modal, búsqueda y contexto

El selector tiene estados `loading`, `ready`, `emptyCatalog`, `noResults` y `failed`. Catálogo vacío o búsqueda sin resultados nunca bloquean la alternativa de texto libre. La acción global se llama exactamente `+ Añadir comida` y exige escoger día y turno; cada celda ofrece una alta directa con fecha/turno preseleccionados.

Antes de abrir detalle se captura `weekStart`, consulta/cursor de búsqueda, `scrollLeft`, `scrollTop` y elemento disparador. El modal no altera esos estados, bloquea scroll de fondo, no incluye editar ni desasignar y, al cerrar, restaura scroll y foco después del render. Si la receta desaparece, muestra el estado no disponible y al cerrar actualiza la tarjeta; la desasignación sigue fuera del modal.

Los títulos no se copian a la asignación: cada lectura une el catálogo actual. En la misma sesión, el store compartido de recetas actualiza las tarjetas al confirmar una mutación de catálogo; cambios remotos se ven en la siguiente lectura de semana. No se introduce transporte realtime fuera del alcance.

## 10. Interfaz responsive y accesibilidad

La cuadrícula se implementará como una única CSS Grid semánticamente equivalente a tabla: una columna de turnos, siete columnas de días y dos filas de contenido. Encabezados tienen asociaciones accesibles con cada celda.

- En escritorio, las siete columnas comparten el ancho y las tarjetas se apilan.
- En móvil, el grid tiene ancho mínimo legible y vive en un único contenedor con scroll horizontal. Encabezados y celdas comparten ese contenedor, por lo que se desplazan sincronizados.
- La columna `Comida/Cena` es sticky; los encabezados de día son sticky arriba y la esquina define capas opacas para no mezclar contenido.
- Cada celda apila tarjetas y admite recorrido vertical cuando supera su altura máxima. La región recibe nombre por día/turno y foco solo cuando existe overflow.
- El banner reserva espacio en el shell y nunca se superpone al skeleton o grid. Controles táctiles tienen objetivo mínimo recomendado de 44×44 CSS px.

Se usarán controles nativos siempre que sea posible, nombres accesibles, foco visible y orden DOM lógico. Durante carga, el grid usa `aria-busy=true`; skeleton es decorativo y los datos previos son inertes. `Guardando`, `Guardado`, validaciones y toasts se anuncian en regiones live sin duplicar mensajes visuales. Los errores de campo usan `aria-invalid` y `aria-describedby`; la acción del toast es alcanzable por teclado.

El detalle usa diálogo modal con título, foco inicial, trampa de foco, cierre por botón y `Escape`, y retorno al disparador. El texto libre no usa `contenteditable` ni atajos de edición: teclado y toque activan el botón que abre el único formulario definido.

El tooltip de texto libre muestra texto completo sanitizado al hover y foco; pulsación alterna su apertura en táctil y `Escape` lo cierra. El disparador expone `aria-describedby`. No contiene acciones y limita su ancho a `min(20rem, calc(100vw - 2rem))`.

## 11. Documentación, pruebas y entrega

La implementación no se considera completa sin estos artefactos:

- `docs/calendario-de-comidas/uso.md`: navegación, altas de receta/texto, edición, desasignación, guardado, estados, errores y riesgo guest; explica `ENABLE_GUEST_USER=false` + reinicio sin prometer borrado.
- `docs/calendario-de-comidas/interfaz.md`: estructura, controles, estados, textos exactos, banner, modal, tooltip, accesibilidad y responsive en móvil/escritorio.
- `docs/interfaces/calendario-de-comidas.openapi.yaml`: contrato HTTP, esquemas, errores, headers de límite y ejemplos aquí definidos.

Prerrequisito de implementación: crear el proyecto Python, dependencias de test, configuración pytest y una base PostgreSQL aislada/efímera. Solo después se incorporan y ejecutan pruebas. La primera tarea deberá actualizar `openspec/config.yaml` con `strict_tdd: true` y el comando real `pytest` (o su invocación equivalente del proyecto), además de registrar las capas de prueba disponibles.

Con TDD estricto activo, ninguna tarea de implementación puede declarar completado un comportamiento sin evidencia RED, GREEN, TRIANGULATE y REFACTOR. Con RDD activo, la revisión nativa y sus recibos se vinculan al candidato exacto después de la normalización; la evidencia de revisión es informativa y no sustituye las decisiones ordinarias de entrega.

Cobertura mínima futura:

- unitarias pytest: semana canaria/DST, normalización y límite Unicode, sanitización, orden, parsing seguro de guest, clasificación de límites y máquina de reintentos;
- integración pytest + PostgreSQL: migraciones, checks, duplicados, `ON DELETE SET NULL`, título actual, transacciones/idempotencia, cuatro intentos totales, concurrencia de última escritura y buckets atómicos;
- contrato API: estados/cuerpos/headers, acceso guest/auth, mensajes exactos y reintento aislado;
- frontend, cuando se seleccione runner: revisiones durante save, navegación en cola, borradores fallidos, temporizador, respuestas obsoletas, modal/scroll/foco y tooltip;
- accesibilidad y responsive: teclado/lector, análisis automatizado complementado con revisión manual en viewport móvil táctil y escritorio para todos los estados.

No se declara validación automatizada en esta fase documental.

## 12. Tradeoffs y decisiones rechazadas

| Decisión | Beneficio | Coste / alternativa rechazada |
| --- | --- | --- |
| Calendario singleton explícito | Hace verificable el riesgo guest y conserva datos al apagarlo. | No prepara calendarios personales; añadirlos requiere otro cambio de producto. |
| Una tabla polimórfica con checks | Consulta semanal y orden conjunto simples; duplicados naturales. | Dos tablas darían tipos más rígidos, pero complicarían orden, API y mutaciones. |
| FK `ON DELETE SET NULL` sin snapshot | Títulos actuales y tombstone inequívoco sin datos obsoletos. | No conserva título/imagen históricos, decisión coherente con `Receta no disponible`. |
| Fechas `DATE` y semana calculada en servidor | Evita errores de navegador y DST. | `Hoy` requiere una lectura adicional para pestañas abiertas. |
| Reintentos solo backend | Una política exacta y observable, sin tormentas del cliente. | El cliente depende de `503` y del reintento manual posterior. |
| Buckets PostgreSQL compartidos | Sin infraestructura adicional y consistencia multi-réplica. | Añade escritura por petición; Redis/gateway queda como evolución compatible. |
| Contenido previo bajo overlay | Reduce vacíos y saltos. | Puede parecer desactualizado; por eso queda inerte y claramente cubierto. |
| Grid semanal con scroll | Preserva comparación de siete días y columna fija. | Exige desplazamiento móvil; carrusel/lista romperían el contexto aprobado. |
| Sin realtime entre dispositivos | Evita ampliar infraestructura y alcance. | Cambios remotos aparecen en la siguiente lectura, no por push. |

## 13. Trazabilidad de requisitos

| Especificación / requisito | Decisión verificable |
| --- | --- |
| Acceso: configuración al arranque | §8 parseo, default, fallo seguro y reinicio. |
| Acceso: calendario guest compartido | §§3, 6 y 8 singleton sin propiedad. |
| Acceso: guest deshabilitado | §§5 y 8 delegación a #6 y `401`. |
| Acceso: banner persistente | §§8–10 texto exacto, carga y espacio reservado. |
| Acceso: límites y feedback | §§5 y 7 límites 60/30, todas las rutas, `429` y toast exacto. |
| Asignaciones: búsqueda pública | §§3, 5 y 6 título normalizado, catálogo completo y público. |
| Asignaciones: independencia/duplicados | §§5–6 UUID, sin unique de celda y DELETE aislado. |
| Asignaciones: presentación/modal | §§5, 9 y 10 datos actuales, solo consulta y contexto restaurado. |
| Asignaciones: receta cambiada/eliminada | §§5–6 y 9 join actual, `SET NULL`, cuadro vacío y desasignar. |
| Asignaciones: texto válido/seguro | §§5–6 NFC, sanitización, 1–100 puntos de código y texto puro. |
| Asignaciones: edición/baja/tooltip | §§5, 9 y 10 acciones directas, sin confirmación, tooltip accesible. |
| Calendario: semana actual/estructura | §§4 y 10 Canarias, lunes-domingo y dos turnos. |
| Calendario: navegación ilimitada/Hoy | §§4 y 9 sin límite de producto, navegación y contexto renovado. |
| Calendario: altas global/contextual | §§5 y 9 mismo editor con fecha/turno preseleccionados. |
| Calendario: contenido y orden | §§5–6 orden conjunto estable, todo visible y sin deduplicar. |
| Interfaz: responsive | §10 scroll sincronizado, columna fija, apilado y overflow vertical. |
| Interfaz: controles/feedback accesibles | §§9–10 teclado, toque, foco, live regions y diálogo. |
| Interfaz: especificación obligatoria | §11 ruta y cobertura de `interfaz.md`. |
| Interfaz: documentación de uso | §11 ruta, contenidos y explicación guest. |
| Interfaz: límites de producto | §2 exclusiones preservadas y sin controles adicionales. |
| Persistencia: calendario compartido | §§3 y 6 PostgreSQL singleton y conservación indefinida. |
| Persistencia: guardado pendiente | §9 blur/Guardar, campo enfocado, revisión y deduplicación. |
| Persistencia: feedback individual | §9 estados y temporizador de 2 segundos. |
| Persistencia: cambios y navegación | §9 confirmación, controles activos y espera de guardados. |
| Persistencia: carga y continuidad | §9 skeleton siempre, edición bloqueada y overlay anterior. |
| Persistencia: reintentos/recuperación | §§5, 7 y 9 backoff exacto, toast, formulario y operación aislada. |
| Persistencia: cancelar reintento manual | §9 cancela acción al navegar y retiene borrador. |
| Persistencia: plataforma futura | §§2 y 11 Python + pytest como prerrequisito, sin runner actual. |
| Persistencia: última escritura | §§5 y 7 sin versión, lock, historial ni autoría. |

## 14. Riesgos residuales y siguiente paso

Riesgos residuales: exposición y vandalismo guest, límites injustos en NAT/redes compartidas, evasión por múltiples IP, indisponibilidad total si falla PostgreSQL, sobrescritura por última escritura, densidad/scroll móvil, borradores perdidos al cerrar pestaña y bloqueo funcional con guest apagado mientras #6 no exista. Todos son visibles y no se corrigen alterando silenciosamente el alcance.

**Siguiente recomendación:** ejecutar la fase `tasks`, empezando por scaffolding Python + pytest y contrato/migraciones, después backend, frontend, accesibilidad/responsive y finalmente los tres documentos de §11. No iniciar `apply` hasta que las tareas expliciten la dependencia del catálogo, el bloqueo de #6 para modo no guest y un comando pytest real.