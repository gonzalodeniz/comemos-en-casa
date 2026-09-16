# F01 — Mejorar GUI del calendario

**Estado:** APPROVED
**Versión:** 0.1
**Release:** R3 — Mejorar GUI
**Fecha:** 2026-09-16
**Referencia visual:** `prototipos/calendario-01.png`

## Contexto

La planificación semanal ya está definida funcionalmente en R1. Esta feature mejora su presentación para que la vista de calendario sea igual o muy similar al prototipo de referencia: una aplicación doméstica, cálida y clara que permite reconocer rápidamente la semana, las comidas y las cenas planificadas, y las acciones disponibles.

La mejora persigue reducir la carga visual sin alterar la semántica de calendario, asignaciones, persistencia o acceso definida en R1.

## Alcance

- Presentación de la vista semanal con cabecera de aplicación, navegación lateral, controles de semana y cuadrícula de planificación.
- Representación visual de comidas y cenas mediante tarjetas de receta, acciones contextuales y espacios vacíos para añadir una planificación.
- Identidad visual coherente con el prototipo: fondo claro, acentos verdes suaves, tipografía legible, iconografía de apoyo y una composición espaciosa.
- Comportamiento visual responsive y accesible de la vista de calendario.

## No alcance

- Cambiar reglas de fechas, navegación, turnos o asignaciones de R1.
- Crear, editar o eliminar recetas, ni definir el catálogo de recetas.
- Añadir nuevas secciones funcionales de navegación lateral, búsqueda, perfil, familia, trucos o compra.
- Definir la arquitectura, el framework, componentes, recursos gráficos concretos o mecanismos de carga de imágenes.
- Modificar contratos API, persistencia, autenticación, permisos o reglas de negocio existentes.

## Actores

- **Persona planificadora:** consulta y organiza sus comidas y cenas semanales.
- **Persona usuaria de tecnologías de asistencia:** navega y opera la vista con teclado, lector de pantalla u otros productos de apoyo.

## Historias de usuario y criterios de aceptación

### US-GUI-CAL-001 — Reconocer el contexto de planificación

Como persona planificadora, quiero identificar de inmediato dónde estoy, qué semana consulto y qué acciones puedo realizar para orientarme antes de modificar mi menú.

- **CA-GUI-CAL-001:** la vista muestra una cabecera de aplicación con marca “Como en casa”, un campo de búsqueda y una representación del perfil, manteniendo jerarquía visual clara respecto al calendario.
- **CA-GUI-CAL-002:** en pantallas amplias se muestra una navegación lateral con “Calendario” como sección activa y accesos visuales a Recetas, Lista de la compra, Trucos, Mi familia y Perfil.
- **CA-GUI-CAL-003:** el área principal muestra el rango de la semana en lenguaje natural, controles anterior/siguiente y un control “Hoy”; estos controles representan las acciones ya definidas por F01 de R1.
- **CA-GUI-CAL-004:** existe una acción principal visible “Añadir comida”, diferenciada de los controles secundarios y utilizable para iniciar la asignación global definida en R1.

### US-GUI-CAL-002 — Consultar el menú semanal de un vistazo

Como persona planificadora, quiero ver los siete días y ambos turnos en una cuadrícula ordenada para comparar mi planificación sin perderme.

- **CA-GUI-CAL-005:** la cuadrícula muestra de lunes a domingo, con nombre del día y número de fecha en cada encabezado; las filas se identifican como “Comida” y “Cena” mediante texto e iconografía de apoyo.
- **CA-GUI-CAL-006:** cada planificación con receta se presenta en una tarjeta que muestra una imagen representativa, el nombre de la receta y acciones contextuales visibles o alcanzables.
- **CA-GUI-CAL-007:** las tarjetas preservan una estructura y tamaño visual consistentes dentro de la cuadrícula, aunque los títulos sean de distinta longitud.
- **CA-GUI-CAL-008:** una celda sin asignación muestra un área claramente distinguible con la acción “Añadir comida” o “Añadir cena”, según corresponda, sin aparentar contenido ya planificado.
- **CA-GUI-CAL-009:** la composición usa separación suficiente entre encabezados, filas, tarjetas y bordes para que los días, turnos y asignaciones puedan distinguirse sin depender solo del color.

### US-GUI-CAL-003 — Percibir una interfaz doméstica y tranquilizadora

Como persona planificadora, quiero que la vista transmita orden y cercanía para que planificar las comidas resulte agradable y no abrumador.

- **CA-GUI-CAL-010:** la vista utiliza una base clara con acentos verdes suaves para navegación, acciones y elementos de énfasis, sin comprometer la legibilidad del texto.
- **CA-GUI-CAL-011:** la navegación lateral incluye un bloque visual decorativo de cocina y un mensaje breve orientado a la planificación; el contenido decorativo no interfiere con la navegación ni con tecnologías de asistencia.
- **CA-GUI-CAL-012:** al pie del área principal se muestra una banda visual de tono suave con un mensaje relacionado con planificación, cocina y disfrute, diferenciada del contenido operativo del calendario.

### US-GUI-CAL-004 — Usar el calendario en cualquier dispositivo

Como persona planificadora, quiero consultar y accionar el calendario desde escritorio o móvil sin perder información ni control.

- **CA-GUI-CAL-013:** en pantallas amplias, cabecera, navegación lateral y cuadrícula conservan la composición de varias columnas del prototipo sin producir solapamientos ni recortes.
- **CA-GUI-CAL-014:** en pantallas estrechas, las acciones esenciales —rango de semana, navegación, “Hoy”, acción principal y acceso a cada celda— permanecen disponibles y comprensibles.
- **CA-GUI-CAL-015:** si los siete días no caben simultáneamente, la cuadrícula permite recorrerlos horizontalmente conservando la identificación de los turnos y los encabezados de día necesarios para interpretar cada tarjeta.
- **CA-GUI-CAL-016:** las tarjetas, controles e imágenes se adaptan al espacio disponible sin ocultar el nombre de la receta ni convertir los objetivos de interacción en difíciles de pulsar.

### US-GUI-CAL-005 — Operar la presentación de forma accesible

Como persona usuaria de tecnologías de asistencia, quiero entender y usar los controles y la cuadrícula con la misma información esencial que una persona usuaria visual.

- **CA-GUI-CAL-017:** los controles de navegación, búsqueda, perfil, navegación lateral, acción principal, acciones de tarjeta y celdas vacías tienen nombre accesible y pueden operarse con teclado y puntero o pulsación.
- **CA-GUI-CAL-018:** el foco visible permite identificar el control activo sobre fondos claros y verdes, y sigue un orden de lectura coherente con la estructura visual.
- **CA-GUI-CAL-019:** la relación entre día, fecha, turno y tarjeta se expone de modo que una persona usuaria de lector de pantalla pueda conocer el contexto de cada asignación o de cada acción de alta.
- **CA-GUI-CAL-020:** las imágenes de receta aportan una alternativa textual útil cuando comunican la receta; los iconos decorativos y la ornamentación se omiten de la lectura asistida.

## Reglas de dominio

- **RD-GUI-CAL-001:** la mejora visual no altera los valores, nombres ni semántica de semana, fecha y turnos definidos por las reglas `RD-CAL-*` de R1 F01.
- **RD-GUI-CAL-002:** “Comida” y “Cena” son los rótulos visibles de los dos turnos funcionales del calendario; una acción de celda debe identificar el turno al que aplica.
- **RD-GUI-CAL-003:** toda tarjeta representa una asignación existente; un espacio vacío representa la ausencia de asignación y no puede confundirse con una tarjeta incompleta.
- **RD-GUI-CAL-004:** la similitud con el prototipo no prevalece sobre legibilidad, contraste, navegación por teclado, alternativa textual ni adaptación al viewport.
- **RD-GUI-CAL-005:** la navegación lateral, búsqueda y perfil se presentan como contexto visual salvo que una feature de su dominio les otorgue comportamiento funcional.

## Modelo conceptual

- **Vista de calendario:** composición que reúne cabecera, navegación contextual, controles semanales, cuadrícula, tarjetas y banda de cierre.
- **Encabezado de día:** representación del nombre y fecha de uno de los siete días de la semana.
- **Fila de turno:** agrupación visual de celdas para Comida o Cena.
- **Tarjeta de planificación:** representación visual de una asignación, con imagen, nombre y acciones contextuales.
- **Celda vacía:** punto de entrada visual para crear una asignación en una fecha y turno concretos.
- **Elemento decorativo:** contenido visual que aporta identidad pero no información operativa necesaria.

## Interfaces

- La vista consume el contexto semanal y las asignaciones ya definidos por las interfaces de R1 F01 y F02; esta SPEC no añade ni modifica interfaces externas.
- La interfaz de usuario expone controles identificables para navegar semanas, volver a Hoy, iniciar un alta global e iniciar un alta contextual por fecha y turno.
- La presentación de recetas debe poder recibir, como mínimo, el nombre y una representación visual disponible de la receta; la ausencia de imagen no debe impedir identificar la asignación por texto.

## Requisitos no funcionales

- **RNF-GUI-CAL-001 — Fidelidad visual:** la jerarquía, distribución, densidad y tono visual deben ser muy similares al prototipo, sin exigir coincidencia píxel a píxel ni depender de sus recursos exactos.
- **RNF-GUI-CAL-002 — Legibilidad:** el texto, fechas, controles y acciones mantienen contraste y tamaño legibles en fondos claros y en los estados activo, hover, foco y deshabilitado cuando existan.
- **RNF-GUI-CAL-003 — Adaptación:** la vista funciona desde un viewport móvil estrecho hasta escritorio amplio sin pérdida de operaciones esenciales ni desbordamiento que oculte contenido sin mecanismo de acceso.
- **RNF-GUI-CAL-004 — Accesibilidad:** la vista satisface los criterios de accesibilidad aplicables de R1 F05, incluidos foco visible, nombres accesibles, semántica de cuadrícula y objetivos táctiles recomendados de 44 × 44 CSS px.
- **RNF-GUI-CAL-005 — Rendimiento percibido:** mientras se recuperan datos se conserva una estructura estable que evita saltos visuales bruscos y comunica que el calendario está cargando, conforme a R1 F03 y F05.

## Supuestos

- El prototipo es una referencia de resultado visual, no una fuente de reglas funcionales nuevas.
- Las recetas planificadas podrán proporcionar una imagen; cuando no esté disponible, se usará una representación de reserva sin perder el título ni el acceso a acciones.
- Los textos mostrados en el prototipo pueden ajustarse a los datos reales y a la localización existente, manteniendo la intención y jerarquía visual.
- R1 continúa siendo la fuente canónica para navegación semanal, asignaciones, carga, errores y autorización.

## Dependencias

- [R1 F01 — Calendario semanal](../../R1-calendario-de-comidas/F01-calendario-semanal/SPEC.md), para rango, días, turnos y navegación.
- [R1 F02 — Asignaciones de comida](../../R1-calendario-de-comidas/F02-asignaciones-de-comida/SPEC.md), para contenido y acciones de las tarjetas.
- [R1 F03 — Persistencia y resiliencia](../../R1-calendario-de-comidas/F03-persistencia-y-resiliencia/SPEC.md), para estados de carga, guardado y error.
- [R1 F05 — Interfaz y documentación](../../R1-calendario-de-comidas/F05-interfaz-y-documentacion/SPEC.md), para requisitos transversales de responsive y accesibilidad.

## Riesgos

- **R-GUI-CAL-001:** priorizar una réplica visual rígida puede degradar la experiencia móvil; se mitiga preservando los controles y el contexto de la cuadrícula en viewport estrecho.
- **R-GUI-CAL-002:** imágenes heterogéneas pueden desequilibrar las tarjetas; se mitiga definiendo una presentación consistente y una alternativa cuando falten.
- **R-GUI-CAL-003:** demasiada ornamentación puede distraer de la planificación; se mitiga manteniendo los elementos decorativos subordinados al calendario y fuera de la lectura asistida.
- **R-GUI-CAL-004:** la navegación lateral mostrada en el prototipo puede sugerir funcionalidades no disponibles; se mitiga presentándola como contexto visual hasta que cada dominio la implemente.

## Glosario

- **Vista semanal:** representación de los siete días de una semana y sus turnos de comida.
- **Tarjeta de receta:** bloque visual que identifica una receta asignada a un día y turno.
- **Acción contextual:** acción asociada a una tarjeta o celda concreta.
- **Viewport:** área visible de la aplicación en un dispositivo o ventana.
- **Referencia visual:** material usado para orientar el aspecto y la jerarquía de una interfaz, sin definir por sí mismo comportamiento técnico.

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-09-16 | Creada en DRAFT a partir de `prototipos/calendario-01.png` para definir la mejora visual del calendario. |
| 0.1 | 2026-09-16 | Aprobada por la persona usuaria; el alcance funcional queda congelado para planificación. |
