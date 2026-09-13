# Interfaz y Documentación Specification

## Purpose

Garantizar que el calendario, sus estados y su uso estén definidos y sean utilizables en escritorio y móvil.

## Requirements

### Requirement: Interfaz responsive de cuadrícula semanal

La interfaz MUST ser completamente responsive en todos los estados de esta feature. En móvil MUST conservar la cuadrícula semanal mediante scroll horizontal, con el encabezado sincronizado con las columnas desplazadas y la columna Comida/Cena fija. Las tarjetas MUST apilarse en cada celda y la celda MUST permitir desbordamiento vertical. En escritorio y móvil, el contenido y los feedbacks MUST permanecer utilizables.

#### Scenario: Semana con contenido denso en móvil

- GIVEN que una celda contiene varias asignaciones y el calendario se visualiza en un viewport móvil táctil
- WHEN una persona desplaza horizontalmente la cuadrícula y consulta esa celda
- THEN los días y su encabezado se desplazan sincronizados, la columna Comida/Cena sigue fija, las tarjetas se apilan y el contenido vertical de la celda puede recorrerse

### Requirement: Controles y feedback accesibles

Todos los controles interactivos del calendario MUST ser operables con teclado y pulsación, tener un nombre accesible y mostrar un estado de foco visible. Los estados `Guardando`, `Guardado`, los toasts de error y rate limiting, y la validación de texto libre MUST comunicarse también a tecnologías de asistencia. Al abrir un modal de receta, el foco MUST entrar en el modal; al cerrarlo, MUST volver al control que lo abrió.

#### Scenario: Feedback de guardado con tecnología de asistencia

- GIVEN que una persona usa teclado y lector de pantalla para guardar una asignación
- WHEN la operación pasa de pendiente a completada
- THEN puede activar `Guardar`, percibe el foco visible y recibe los estados `Guardando` y `Guardado` mediante la tecnología de asistencia

#### Scenario: Modal de receta accesible

- GIVEN que una persona activa el detalle de una receta asignada mediante teclado
- WHEN el modal se abre y después se cierra
- THEN el foco se mueve al modal y vuelve al control que abrió el detalle, sin habilitar edición ni desasignación dentro del modal

### Requirement: Especificación de interfaz obligatoria

La entrega MUST incluir una especificación de interfaz del calendario. La especificación MUST describir la estructura de la vista, sus controles, estados de carga y edición, feedback de guardado y error, banner guest, modal de detalle, tooltips de texto libre y comportamiento responsive de escritorio y móvil, incluidos los textos exactos definidos para banner y toasts.

#### Scenario: Revisión de la especificación de interfaz

- GIVEN que se revisan los artefactos entregados para el cambio
- WHEN se consulta la especificación de interfaz
- THEN cubre estructura, controles, estados, feedback, banner, modal, tooltips, accesibilidad y adaptación responsive, incluyendo los textos exactos aplicables

### Requirement: Documentación de uso obligatoria

La entrega MUST incluir documentación de uso del calendario que explique cómo consultar y navegar semanas, añadir recetas o texto libre, editar o desasignar, guardar cambios, interpretar los estados y errores, y el carácter público compartido del modo guest. La documentación MUST indicar que guest puede deshabilitarse configurando `ENABLE_GUEST_USER=false` y reiniciando el backend, sin afirmar que ello elimina datos existentes.

#### Scenario: Persona usuaria consulta el uso y el modo guest

- GIVEN que una persona abre la documentación de uso entregada
- WHEN necesita planificar una comida y entender el modo guest
- THEN encuentra los pasos de uso, los feedbacks y la advertencia de que cualquier visita guest puede ver y cambiar el calendario compartido

### Requirement: Límites explícitos de interfaz y producto

La interfaz MUST NOT incluir drag and drop, recurrencias, copia de semanas, borrado completo de semanas, limpieza automática de planes antiguos, festivos, nutrición, cantidades, horarios concretos, recordatorios, preparación anticipada, listas de compra, CAPTCHA, calendarios personales, colaboración identificada ni flujos de privacidad o permisos. Las recetas MUST tratarse como públicas y seleccionables sin incorporar la distinción pública/privada de la issue #5.

#### Scenario: Revisión de controles fuera de alcance

- GIVEN que se revisan los controles y flujos expuestos por el calendario
- WHEN se buscan funciones explícitamente fuera de alcance
- THEN ninguna de esas funciones está disponible y todas las recetas se presentan como públicas y seleccionables
