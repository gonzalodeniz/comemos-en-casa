# TASKS — F01 Mejorar GUI del calendario

**Estado:** APPROVED · **Versión:** 0.1
**Bases aprobadas:** [`SPEC.md`](SPEC.md) v0.1 (`APPROVED`, 2026-09-16) y [`PLAN.md`](PLAN.md) v0.1 (`APPROVED`, 2026-09-16).
**Referencia visual:** `prototipos/calendario-01.png`.
**Límite de entrega:** no se modifican contratos API, reducer, persistencia, autenticación, backend, Docker, Nginx ni Compose. La implementación queda autorizada dentro de estos límites.

## Secuencia y checklist

- [ ] GUI-CAL-T01 — Configurar el runner de pruebas frontend.
- [ ] GUI-CAL-T02 — Componer el marco y la cuadrícula semanal.
- [ ] GUI-CAL-T03 — Representar tarjetas, huecos y acciones existentes.
- [ ] GUI-CAL-T04 — Adaptar la vista a móvil y reforzar su accesibilidad.
- [ ] GUI-CAL-T05 — Completar regresión, revisión visual y documentación de entrega.

## Dependencias de ejecución

`GUI-CAL-T01` desbloquea las pruebas de interfaz. `GUI-CAL-T02` precede a `GUI-CAL-T03` y `GUI-CAL-T04`. `GUI-CAL-T03` y `GUI-CAL-T04` deben terminar antes de `GUI-CAL-T05`. Cada tarea conserva los callbacks, tipos y contratos existentes de R1; ninguna tarea autoriza por sí misma un cambio funcional fuera de la SPEC.

---

## GUI-CAL-T01 — Configurar el runner de pruebas frontend

**Estado:** pendiente. **Estimación:** hasta 1 jornada.
**Trazabilidad:** PLAN §Stack y convenciones verificadas, §Pruebas y calidad, §Dependencias y decisiones pendientes; H3; SPEC US-GUI-CAL-001, US-GUI-CAL-002, US-GUI-CAL-005; CA-GUI-CAL-003, CA-GUI-CAL-005–009 y CA-GUI-CAL-017–019; RD-GUI-CAL-001 y RD-GUI-CAL-004.

### Preparación

- **Dependencias:** ninguna; se ejecuta antes de tareas que requieran pruebas frontend automatizadas.
- **Puntos de trabajo:** `frontend/package.json`, configuración y ficheros de pruebas frontend que resulten necesarios; `frontend/src/App.tsx`, `frontend/src/calendarReducer.ts` y `frontend/src/types.ts` solo como contexto de los casos iniciales.
- **Nota:** el runner no está decidido. Se elegirá únicamente tras verificar compatibilidad con las versiones actuales de Vite, React, TypeScript y Node; no se cambia el framework ni los contratos de R1.

### Pasos de ejecución

1. Inspeccionar scripts, versiones instaladas y capacidad actual de prueba del frontend; registrar la ausencia o presencia de runner antes de cambiar configuración.
2. Evaluar un runner y utilidades de renderizado compatibles con el stack declarado, justificando la elección frente a las pruebas de componentes, interacción y accesibilidad requeridas por el PLAN.
3. Añadir la dependencia mínima, configuración y scripts deterministas necesarios para ejecutar pruebas frontend sin servidor real; conservar `typecheck` y `build` existentes.
4. Crear una prueba de humo que renderice el calendario con dobles de API y demuestre que el comando de prueba se descubre y ejecuta.
5. Ejecutar el nuevo comando, `npm --prefix frontend run typecheck`, `npm --prefix frontend run build` y `make test`; documentar cualquier fallo preexistente o bloqueo sin ocultarlo.

### Casos de prueba y resultados esperados

| Caso | Preparación y acción | Resultado esperado |
| --- | --- | --- |
| Runner ejecutable | Ejecutar el script frontend nuevo en árbol limpio. | El runner detecta y ejecuta la prueba de humo de forma determinista. |
| Aislamiento HTTP | Renderizar la prueba de humo con dobles de API. | No se emite petición de red ni se requiere un servicio real. |
| Regresión de compilación | Ejecutar typecheck y build tras configurar el runner. | Ambos comandos terminan correctamente o dejan evidencia del fallo preexistente. |

### Definición de terminado

- El runner, su comando y la prueba de humo están configurados y son reproducibles.
- Los casos anteriores dejan preparada la base automatizada para T02–T05 sin modificar semántica de R1.
- La elección y sus límites quedan registrados en la evidencia de cierre.

### Evidencia de cierre requerida

Registrar versión de Node y paquetes elegidos, scripts configurados, salida resumida del runner, `npm --prefix frontend run typecheck`, `npm --prefix frontend run build`, `make test`, y cualquier incidencia previa separada de los resultados de esta tarea.

---

## GUI-CAL-T02 — Componer el marco y la cuadrícula semanal

**Estado:** pendiente. **Estimación:** hasta 1 jornada.
**Trazabilidad:** PLAN §Arquitectura de la interfaz/ Límites de responsabilidad, §Accesibilidad y responsive, H1 y §Pruebas y calidad; SPEC US-GUI-CAL-001, US-GUI-CAL-002 y US-GUI-CAL-003; CA-GUI-CAL-001–005 y CA-GUI-CAL-009–012; RD-GUI-CAL-001, RD-GUI-CAL-002 y RD-GUI-CAL-005; RNF-GUI-CAL-001–002.

### Preparación

- **Dependencias:** GUI-CAL-T01; las pantallas y datos de R1 deben poder cargarse localmente.
- **Puntos de trabajo:** `frontend/src/App.tsx`, `frontend/src/styles.css` y componentes locales de presentación que se extraigan desde `CalendarPage`; `frontend/src/types.ts` y `frontend/src/calendarReducer.ts` como contratos que no se alteran.
- **Nota:** conservar la tabla semántica, el orden DOM y los callbacks existentes. Marca, búsqueda, perfil y navegación lateral solo son contexto visual cuando no tengan flujo de dominio.

### Pasos de ejecución

1. Escribir pruebas de composición para cabecera, navegación lateral contextual, rango semanal, anterior/siguiente/Hoy, acción global y siete encabezados de día, con los callbacks de R1 como dobles verificables.
2. Extraer o crear componentes de presentación locales con props de datos y callbacks ya disponibles en `CalendarPage`; no mover reglas temporales, reducer ni llamadas API.
3. Aplicar estilos de marco, navegación, controles, cabecera de tabla, filas Comida/Cena y banda final para aproximar jerarquía, espaciado y tonos del prototipo.
4. Marcar iconos y ornamentación como decorativos cuando corresponda y preservar botones reales, etiquetas y estructura de tabla.
5. Ejecutar las pruebas focalizadas, typecheck y build; comparar en viewport amplio el estado con datos frente a `prototipos/calendario-01.png`.

### Casos de prueba y resultados esperados

| Caso | Preparación y acción | Resultado esperado |
| --- | --- | --- |
| Contexto semanal | Renderizar una semana conocida. | Se muestran rango, Anterior, Siguiente, Hoy, acción global, lunes–domingo y rótulos Comida/Cena. |
| Delegación de controles | Activar anterior, siguiente, Hoy y añadir global usando dobles. | Cada control invoca solo el callback existente esperado. |
| Contexto no funcional | Renderizar búsqueda, perfil y navegación lateral. | Son identificables visualmente; no generan solicitudes ni flujos nuevos. |
| Estructura accesible | Inspeccionar roles, encabezados y nombres de controles. | La tabla mantiene encabezados de día/fila y los controles tienen nombre accesible. |

### Definición de terminado

- El marco y la cuadrícula representan los siete días y dos turnos con jerarquía próxima al prototipo.
- Los controles conservan los flujos de R1 y no introducen contratos ni peticiones nuevos.
- Los cuatro casos están automatizados o, para comparación visual, documentados con viewport y navegador.

### Evidencia de cierre requerida

Registrar nombres y resultados de pruebas focalizadas, resultado de typecheck/build, captura o revisión de escritorio indicando viewport/navegador/estado de datos y confirmación de que no se modificaron `api.ts`, reducer ni tipos de contrato.

---

## GUI-CAL-T03 — Representar tarjetas, huecos y acciones existentes

**Estado:** pendiente. **Estimación:** hasta 1 jornada.
**Trazabilidad:** PLAN §Arquitectura de la interfaz/ Límites de responsabilidad y Datos e interfaces, H1 y H3, §Pruebas y calidad; SPEC US-GUI-CAL-002; CA-GUI-CAL-006–009; RD-GUI-CAL-001–003; RNF-GUI-CAL-001, RNF-GUI-CAL-002 y RNF-GUI-CAL-005.

### Preparación

- **Dependencias:** GUI-CAL-T01 y GUI-CAL-T02; callbacks de alta, edición y eliminación existentes disponibles desde `CalendarPage`.
- **Puntos de trabajo:** componentes locales de tarjeta/celda y sus estilos; `frontend/src/App.tsx`, `frontend/src/types.ts`, `frontend/src/api.ts` y `frontend/src/calendarReducer.ts` solo para preservar interfaces y verificar que no cambian.
- **Nota:** una tarjeta representa exclusivamente una asignación existente; la reserva de imagen no oculta el título. Un hueco representa ausencia de asignación e identifica fecha y turno.

### Pasos de ejecución

1. Escribir pruebas para tarjeta con imagen, tarjeta sin imagen o receta no disponible, título de longitud distinta, acción contextual y celda vacía de Comida/Cena.
2. Implementar la presentación consistente de tarjetas y reserva visual de imagen con texto alternativo útil cuando la imagen informa; ocultar decoración de lectores de pantalla.
3. Implementar celdas vacías claramente diferenciadas y conectar su acción a la preselección contextual existente de fecha y turno.
4. Mantener alcanzables las acciones existentes de tarjeta y verificar que editan/eliminan mediante los callbacks actuales, sin nuevas llamadas API.
5. Ejecutar las pruebas focalizadas y la regresión de navegación/alta de R1 con dobles de API; corregir solo defectos de presentación o enlace de callback dentro del alcance.

### Casos de prueba y resultados esperados

| Caso | Preparación y acción | Resultado esperado |
| --- | --- | --- |
| Tarjeta con imagen | Renderizar una asignación con referencia de imagen. | Imagen con alternativa útil, título visible y acción contextual alcanzable. |
| Tarjeta sin imagen | Renderizar una asignación sin portada o receta disponible. | Se muestra reserva visual y el título sigue identificando la asignación. |
| Títulos heterogéneos | Renderizar títulos corto y largo. | La tarjeta conserva estructura consistente sin perder el nombre. |
| Hueco contextual | Activar un hueco de lunes/Comida y otro de domingo/Cena. | El callback recibe la fecha y el turno correctos; el nombre accesible expresa ambos. |
| Acciones de tarjeta | Activar edición o eliminación con dobles. | Se invocan exclusivamente los callbacks existentes previstos. |

### Definición de terminado

- Tarjetas, huecos y acciones satisfacen los casos anteriores y no se confunden visual ni semánticamente.
- No cambian los tipos, reducer, endpoints ni contrato de asignaciones de R1.
- Las pruebas demuestran alta contextual y acciones de tarjeta con dobles de API.

### Evidencia de cierre requerida

Registrar archivos afectados, resultados de las cinco pruebas, salida del comando del runner, typecheck/build, y referencia a la comprobación de diff que confirme la ausencia de cambios en contratos API y reducer.

---

## GUI-CAL-T04 — Adaptar la vista a móvil y reforzar su accesibilidad

**Estado:** pendiente. **Estimación:** hasta 1 jornada.
**Trazabilidad:** PLAN §Accesibilidad y responsive, H2 y §Pruebas y calidad; SPEC US-GUI-CAL-004, US-GUI-CAL-005; CA-GUI-CAL-013–020; RD-GUI-CAL-004; RNF-GUI-CAL-003–005.

### Preparación

- **Dependencias:** GUI-CAL-T01, GUI-CAL-T02 y GUI-CAL-T03.
- **Puntos de trabajo:** estilos de calendario y componentes de presentación locales; estados de carga/error ya expuestos por `CalendarPage`; no se modifican capa API, reducer ni contratos.
- **Nota:** cuando no entren siete días, se conserva scroll horizontal y contexto de turno/encabezado. La reducción de tamaño nunca debe ocultar nombre de receta ni impedir pulsación.

### Pasos de ejecución

1. Añadir pruebas automatizadas de nombres accesibles, foco por teclado, `aria-busy` en carga y relación de día/fecha/turno en tarjeta y celda vacía.
2. Definir breakpoints y dimensiones de controles para escritorio y móvil; preservar columna de turnos y cabeceras necesarias durante el scroll horizontal.
3. Ajustar foco visible, orden DOM, alternativas de imagen y `aria-hidden` de ornamentos sin sustituir controles nativos por elementos no semánticos.
4. Revisar manualmente los estados con datos, huecos, carga y error en un viewport amplio y uno estrecho; recorrer con teclado, zoom y lector de pantalla disponible.
5. Ejecutar pruebas focalizadas, typecheck, build y regresión de R1; registrar las comprobaciones manuales que no se puedan automatizar.

### Casos de prueba y resultados esperados

| Caso | Preparación y acción | Resultado esperado |
| --- | --- | --- |
| Móvil con siete días | Abrir viewport estrecho y recorrer horizontalmente la cuadrícula. | Cada día es accesible sin recorte silencioso y se mantiene el contexto de turno/fecha. |
| Teclado | Tabular desde controles de semana hasta tarjeta y hueco. | Orden lógico y foco visible contrastado en cada control interactivo. |
| Carga y error | Simular carga y respuesta de error existentes. | Se comunica carga mediante `aria-busy`; el error existente permanece visible y operativo. |
| Tamaño táctil | Medir controles principales y de celda en viewport estrecho. | Los objetivos alcanzan 44 × 44 CSS px recomendados o la evidencia explica una excepción que requiere revisar PLAN/SPEC. |
| Lectura asistida | Inspeccionar tarjeta, hueco e iconos decorativos. | Día, fecha, turno y acción son comprensibles; ornamentación no se anuncia. |

### Definición de terminado

- La vista conserva operaciones esenciales en escritorio y móvil conforme a los cinco casos.
- La semántica, el foco, las alternativas textuales y estados de carga/error cumplen el alcance de R1 F05.
- Cualquier excepción que cambie requisitos se detiene y se remite a actualización versionada de SPEC/PLAN.

### Evidencia de cierre requerida

Registrar resultados del runner, typecheck/build, matriz manual con viewport, navegador, zoom, teclado y lector de pantalla usado, más mediciones de objetivos táctiles y capturas de escritorio/móvil sin datos sensibles.

---

## GUI-CAL-T05 — Completar regresión, revisión visual y documentación de entrega

**Estado:** pendiente. **Estimación:** hasta 1 jornada.
**Trazabilidad:** PLAN H3, §Pruebas y calidad, §Observabilidad y operaciones, §Despliegue e infraestructura, §Riesgos y mitigaciones y §Trazabilidad; SPEC CA-GUI-CAL-001–020; RD-GUI-CAL-001–005; RNF-GUI-CAL-001–005.

### Preparación

- **Dependencias:** GUI-CAL-T01–T04 completadas; acceso local al prototipo y a los comandos de verificación.
- **Puntos de trabajo:** pruebas frontend configuradas en T01, ficheros modificados por T02–T04, `docs/sdd/releases/R3-mejorar-gui/F01-mejorar-gui-calendario/` para evidencia de aceptación si el repositorio no dispone de una ubicación operativa existente.
- **Nota:** no se crea documentación de usuario ni se modifica infraestructura salvo que el cambio implementado lo requiera y permanezca dentro de PLAN; la tarea consolida evidencia, no amplía alcance.

### Pasos de ejecución

1. Ejecutar la suite frontend completa, `npm --prefix frontend run typecheck`, `npm --prefix frontend run build`, `make test` y `make build`; separar fallos preexistentes, de entorno y de la feature.
2. Repetir los flujos de R1: semana anterior/siguiente/Hoy, alta global, alta contextual Comida/Cena, acciones de tarjeta y estados de carga/error usando la estrategia de dobles o entorno disponible.
3. Comparar el resultado con `prototipos/calendario-01.png` en escritorio y móvil, evaluando jerarquía, densidad, espaciado, tonos, tarjetas, huecos y banda final sin exigir equivalencia píxel a píxel.
4. Revisar que el diff no contiene API, reducer, tipos de contrato, backend, migraciones, Docker, Nginx, Compose, secretos ni cambios funcionales fuera del alcance.
5. Guardar un informe de aceptación o actualizar la documentación operativa existente con comandos, entorno, resultados, incidencias y capturas referenciadas; marcar cualquier comprobación no ejecutable como pendiente.

### Casos de prueba y resultados esperados

| Caso | Preparación y acción | Resultado esperado |
| --- | --- | --- |
| Suite y compilación | Ejecutar los cinco comandos de verificación. | Resultados registrados; ningún fallo se atribuye a la feature sin evidencia. |
| Regresión funcional | Ejecutar navegación, altas y acciones de tarjeta. | Los flujos de R1 conservan su resultado y no aparece una solicitud nueva. |
| Comparación visual | Revisar escritorio y móvil frente al prototipo. | La composición es muy similar en jerarquía y tono, con responsive y a11y preservados. |
| Alcance técnico | Inspeccionar `git diff` y configuración. | No hay cambios excluidos ni secretos; no se requieren migraciones o despliegue nuevo. |

### Definición de terminado

- Existe evidencia reproducible de pruebas, revisión visual, accesibilidad y límites de alcance.
- Las regresiones funcionales de R1 están cubiertas y las incidencias abiertas tienen clasificación y siguiente acción explícita.
- La documentación de entrega permite repetir la verificación sin declarar como realizada una comprobación pendiente.

### Evidencia de cierre requerida

Registrar commit o revisión inspeccionada, salidas resumidas de suite/typecheck/build/make test/make build, versión de Node y navegador, matriz de viewports/estados, capturas referenciadas, resultado de `git diff --check` y lista explícita de comprobaciones pendientes o no ejecutables.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | TASKS DRAFT creada a partir de SPEC y PLAN 0.1 APPROVED; desglosa configuración de pruebas, composición, tarjetas, accesibilidad responsive y validación final. |
| 0.2 | 2026-09-16 | TASKS aprobadas para iniciar la implementación de F01. |
