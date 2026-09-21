# F01 — Mejorar GUI del calendario — PLAN

**Estado:** APPROVED
**Versión:** 0.1
**Release:** R3 — Mejorar GUI
**Fecha:** 2026-09-16
**SPEC base:** [F01 — Mejorar GUI del calendario, versión 0.1, APPROVED](SPEC.md)
**Referencia visual:** `prototipos/calendario-01.png`

## Objetivo de ejecución

Materializar la presentación semanal definida en la SPEC base mediante una composición de aplicación doméstica y clara, sin cambiar las reglas, contratos ni persistencia de R1. El resultado conserva el calendario lunes–domingo, los turnos y los flujos de asignación existentes, mientras aproxima jerarquía, densidad y tono visual del prototipo.

## Stack y convenciones verificadas

- **Cliente:** React 19.1, TypeScript 5.8, Vite 6.3 y React Router 7.6, declarados en [`frontend/package.json`](../../../../../frontend/package.json).
- **Estilos:** CSS global en [`frontend/src/styles.css`](../../../../../frontend/src/styles.css); no se incorpora una biblioteca de componentes ni un framework CSS para esta feature.
- **Integración existente:** [`frontend/src/App.tsx`](../../../../../frontend/src/App.tsx) contiene `CalendarPage`, y [`frontend/src/calendarReducer.ts`](../../../../../frontend/src/calendarReducer.ts) conserva el estado del calendario. [`frontend/src/api.ts`](../../../../../frontend/src/api.ts) ya consume los contratos de R1.
- **Entrega:** compilación Vite estática servida por Nginx desde [`frontend/Dockerfile`](../../../../../frontend/Dockerfile); la composición local está definida en [`docker-compose.yml`](../../../../../docker-compose.yml).
- **Convenciones:** componentes React en `PascalCase`, variables y funciones en `camelCase`, TypeScript con dos espacios y CSS existente; no se modifica backend ni base de datos.

## Arquitectura de la interfaz

### Límites de responsabilidad

1. Mantener `CalendarPage` como orquestador de la carga, navegación de semana, edición y mutaciones existentes. No se reimplementan el reducer, las llamadas API ni las reglas temporales.
2. Extraer componentes de presentación locales al frontend para aislar: marco de aplicación (marca, búsqueda visual y perfil), navegación lateral, barra de controles semanales, encabezados y filas de la cuadrícula, tarjeta de asignación, celda vacía y banda de cierre. Sus props reciben únicamente datos y callbacks ya disponibles en `CalendarPage`.
3. Mantener el editor de asignaciones y los enlaces a recetas con su comportamiento actual. Las nuevas acciones visuales delegan en los callbacks existentes para alta global, alta contextual, edición y eliminación.
4. Organizar los estilos del calendario por bloques de composición, controles, cuadrícula/tarjetas, estados y breakpoints. Las reglas de móvil preservan la columna de turnos y el desplazamiento horizontal del calendario.

### Datos e interfaces

- Se reutilizan `CalendarContext`, `CalendarWeek`, `CalendarAssignment`, `MealSlot` y `RecipeReference` de [`frontend/src/types.ts`](../../../../../frontend/src/types.ts).
- No se añaden endpoints, parámetros, campos, migraciones ni transformaciones de datos. Los contratos `GET /context`, `GET /weeks/{weekStart}` y las mutaciones de asignación siguen siendo los de R1.
- El título y la imagen se renderizan desde la referencia de receta actual. Si no existe portada o la receta no está disponible, la tarjeta mantiene título y una reserva visual no decorativa según corresponda.
- La búsqueda, perfil y destinos de navegación que no tengan flujo funcional propio se presentan como contexto visual y no simulan comportamiento nuevo.

### Accesibilidad y responsive

- Conservar tabla semántica con encabezados de columna y fila; asociar cada acción de celda con fecha y turno en su nombre accesible.
- Usar botones reales para navegación y acciones; los iconos decorativos se marcan `aria-hidden` y las imágenes informativas conservan texto alternativo útil.
- Mantener foco visible, orden DOM lógico, estados de carga `aria-busy` y anuncios de feedback existentes.
- En escritorio, usar marco con cabecera y navegación lateral junto al área principal. En móvil, reordenar y compactar la estructura sin ocultar controles esenciales; el scroll horizontal conserva cabecera de día y columna de turnos necesarias.

## Hitos

### H1 — Estructura y sistema visual del calendario

**Resultado:** marco de aplicación, navegación contextual, cabecera semanal, acción principal, cuadrícula y banda final con jerarquía próxima al prototipo.

**Cobertura:** US-GUI-CAL-001, US-GUI-CAL-002, US-GUI-CAL-003; CA-GUI-CAL-001 a CA-GUI-CAL-012; RD-GUI-CAL-001, RD-GUI-CAL-002, RD-GUI-CAL-003 y RD-GUI-CAL-005; RNF-GUI-CAL-001 y RNF-GUI-CAL-002.

**Trabajo previsto:** refactorizar la presentación de `CalendarPage` y sus estilos sin alterar sus efectos, reducer ni API; representar tarjetas y huecos con los datos existentes, manteniendo las acciones contextuales alcanzables.

### H2 — Adaptación y accesibilidad verificable

**Resultado:** composición utilizable en escritorio y móvil, con semántica, foco, alternativas textuales y estados de carga coherentes con R1.

**Cobertura:** US-GUI-CAL-004, US-GUI-CAL-005; CA-GUI-CAL-013 a CA-GUI-CAL-020; RD-GUI-CAL-004; RNF-GUI-CAL-003, RNF-GUI-CAL-004 y RNF-GUI-CAL-005.

**Trabajo previsto:** aplicar breakpoints y scroll horizontal existentes, garantizar tamaños de interacción y foco, y revisar estados con contenido, huecos, carga y errores ya expuestos por la página.

### H3 — Regresión visual y entrega

**Resultado:** evidencia reproducible de que la presentación no cambia los comportamientos de R1 y se puede construir/desplegar con la infraestructura existente.

**Cobertura de regresión:** RD-GUI-CAL-001 a RD-GUI-CAL-004; dependencias R1 `US-CAL-001` a `US-CAL-003`, `US-ASG-001` y `US-ASG-002`, `US-PER-003`, `US-INT-001` y `US-INT-002`.

## Pruebas y calidad

- Añadir pruebas deterministas de componentes o de interacción para la composición del calendario: rango y controles, siete encabezados, Comida/Cena, tarjeta con y sin imagen, celda vacía contextual y nombres accesibles de controles. La selección del runner debe integrarse con Vite y quedar declarada en `frontend/package.json`; no se sustituye la verificación existente hasta que ese runner esté configurado.
- Cubrir regresión de navegación anterior/siguiente/Hoy, apertura de alta global y contextual, y preservación de las acciones existentes de tarjeta mediante pruebas de interfaz con dobles de API.
- Realizar revisión manual en viewport amplio y estrecho: scroll horizontal, columna de turnos, foco por teclado, contraste, zoom, lector de pantalla y estados carga/error. Comparar jerarquía y densidad con `prototipos/calendario-01.png`, sin exigir píxel perfecto.
- Ejecutar como mínimo `npm --prefix frontend run typecheck`, `npm --prefix frontend run build` y `make test`. Registrar resultados reales y cualquier comprobación no ejecutable antes de cerrar la feature.

## Seguridad y privacidad

- La feature no toca autenticación, autorización, cookies, sesiones, secretos, permisos ni endpoints.
- Las imágenes y títulos continúan entrando por el modelo de receta existente; el DOM de React los renderiza como datos, sin introducir HTML sin sanear.
- Los controles de búsqueda, perfil y navegación que sean solo visuales no deben enviar solicitudes, capturar datos ni aparentar una sesión adicional.

## Observabilidad y operaciones

- Reutilizar los estados visibles de carga, error y reintento que aporta el flujo actual; no se añade telemetría ni logging de producto sin una SPEC posterior.
- Durante desarrollo, los fallos de compilación, tipos y pruebas son la señal operativa de la feature. En ejecución, se conserva el mensaje de error procedente de la capa API existente.
- La comparación visual se documentará como evidencia de revisión, indicando viewport, estado de datos y navegador, sin adjuntar datos sensibles.

## Despliegue e infraestructura

- No hay cambios de infraestructura, variables de entorno, imágenes Docker, Nginx, migraciones ni servicios de Compose previstos.
- La entrega usa el mismo artefacto estático de `npm run build` y la imagen multietapa definida en `frontend/Dockerfile`.
- Antes de integrar, comprobar que `make build` sigue construyendo frontend, backend y Compose sin requerir configuración adicional. No se planifica migración ni rollback de datos porque el cambio es exclusivamente de presentación.

## Riesgos y mitigaciones

| Riesgo | Mitigación | Señal de control |
| --- | --- | --- |
| Una réplica rígida rompe el uso móvil. | Priorizar scroll horizontal y columna de turnos antes que encoger ilegiblemente las tarjetas. | Revisión manual en viewport estrecho. |
| El refactor visual altera callbacks de R1. | Separar componentes de presentación y reutilizar callbacks, reducer y API actuales sin modificar sus contratos. | Pruebas de interacción y regresión de alta/navegación. |
| Imágenes de tamaños distintos deforman la cuadrícula. | Definir contenedor y ajuste de imagen consistentes, con reserva cuando falte. | Casos de tarjeta con imagen, sin imagen y receta no disponible. |
| La ornamentación reduce accesibilidad. | Marcar lo decorativo como oculto a asistencia y mantener nombres accesibles, foco y estructura de tabla. | Recorrido por teclado y revisión con lector de pantalla. |
| La búsqueda o la navegación lateral aparentan funciones no implementadas. | Mantenerlas explícitamente como contexto visual hasta disponer de feature de dominio. | Revisión de enlaces y ausencia de nuevas llamadas API. |

## Trazabilidad

| Requisito de la SPEC base | Hito | Estrategia |
| --- | --- | --- |
| US-GUI-CAL-001; CA-GUI-CAL-001–004 | H1 | Marco de aplicación, navegación contextual y controles semanales reutilizando callbacks de R1. |
| US-GUI-CAL-002; CA-GUI-CAL-005–009 | H1 | Tabla semanal, filas de turno, tarjetas y celdas vacías con datos existentes. |
| US-GUI-CAL-003; CA-GUI-CAL-010–012 | H1 | Tokens CSS y composición decorativa subordinada al contenido operativo. |
| US-GUI-CAL-004; CA-GUI-CAL-013–016 | H2 | Breakpoints, reordenación y scroll horizontal de la cuadrícula. |
| US-GUI-CAL-005; CA-GUI-CAL-017–020 | H2 | Semántica, foco, nombres accesibles y alternativas textuales. |
| RD-GUI-CAL-001–003 y RD-GUI-CAL-005 | H1, H3 | Reutilización de modelos, reglas y flujos de R1 sin cambios funcionales. |
| RD-GUI-CAL-004; RNF-GUI-CAL-002–004 | H2, H3 | Accesibilidad, legibilidad y validación en viewports representativos. |
| RNF-GUI-CAL-001 y RNF-GUI-CAL-005 | H1, H3 | Fidelidad proporcional al prototipo y estabilidad en carga. |

## Dependencias y decisiones pendientes

- Depende de las SPEC `0.1 APPROVED` de [R1 F01](../../R1-calendario-de-comidas/F01-calendario-semanal/SPEC.md), [R1 F02](../../R1-calendario-de-comidas/F02-asignaciones-de-comida/SPEC.md), [R1 F03](../../R1-calendario-de-comidas/F03-persistencia-y-resiliencia/SPEC.md) y [R1 F05](../../R1-calendario-de-comidas/F05-interfaz-y-documentacion/SPEC.md).
- La elección concreta del runner de pruebas frontend se resolverá al crear TASKS, verificando compatibilidad con el Vite y Node actuales; no condiciona la arquitectura funcional aprobada.
- No se planifican cambios de datos ni despliegue. Si la implementación descubre que la similitud visual requiere cambiar contratos, rutas o comportamiento de R1, se detendrá y se versionará la SPEC antes de continuar.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | PLAN DRAFT creado a partir de la SPEC 0.1 APPROVED de F01. |
| 0.1 | 2026-09-16 | Aprobado por la persona usuaria; habilitada la elaboración de TASKS. |
