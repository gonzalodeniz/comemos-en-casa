# Asignaciones de Comida Specification

## Purpose

Permitir planificar varias recetas públicas o entradas de texto libre por fecha y turno sin alterar el catálogo de recetas.

## Requirements

### Requirement: Selección de recetas públicas

El sistema MUST permitir buscar y seleccionar cualquier receta del catálogo público por título. La búsqueda MUST ignorar diferencias de mayúsculas, minúsculas y acentos.

#### Scenario: Búsqueda de receta sin acentos ni distinción de caja

- GIVEN que el catálogo público contiene una receta titulada `Tortilla Española`
- WHEN una persona busca `tortilla espanola`
- THEN la receta aparece como seleccionable

### Requirement: Asignaciones de receta independientes

El sistema MUST permitir varias asignaciones de receta en la misma fecha y turno, incluidos duplicados. Cada asignación de receta MUST conservar su referencia a receta, fecha y turno, y eliminar una asignación MUST eliminar solo su relación con el calendario, nunca la receta del catálogo.

#### Scenario: Duplicar y desasignar una receta

- GIVEN que una receta está asignada a la Comida de una fecha
- WHEN la misma receta se asigna otra vez y después se usa `Desasignar` en una de las dos asignaciones
- THEN ambas asignaciones se muestran antes de desasignar, solo la seleccionada desaparece después y la receta sigue disponible en el catálogo

### Requirement: Presentación y detalle de recetas asignadas

El sistema MUST mostrar el título actual y la imagen de portada de cada receta asignada, y MUST permitir abrir su detalle. El detalle MUST abrirse en un modal de solo consulta que no permita editar ni desasignar. Al cerrarlo, MUST conservar la semana visible, la consulta de búsqueda y la posición de scroll existentes antes de abrirlo.

#### Scenario: Cierre de detalle sin pérdida de contexto

- GIVEN que una persona ha buscado recetas, se ha desplazado por la semana y abre el detalle de una receta asignada
- WHEN cierra el modal
- THEN se conserva la misma semana, la misma búsqueda y la misma posición de scroll, y el modal no ofreció controles de edición ni desasignación

### Requirement: Actualización y ausencia de recetas referenciadas

El sistema MUST reflejar inmediatamente el título actual de una receta referenciada. Si la receta referenciada ha sido eliminada del catálogo, MUST conservar la asignación mostrando `Receta no disponible`, un cuadro vacío que reserve el espacio de la imagen original y una acción directa `Desasignar`.

#### Scenario: Receta eliminada conservada como asignación reconocible

- GIVEN que una asignación referencia una receta que deja de existir en el catálogo
- WHEN se muestra su celda
- THEN se muestra `Receta no disponible`, un cuadro vacío de imagen y `Desasignar`, sin eliminar la asignación automáticamente

### Requirement: Texto libre válido y seguro

El sistema MUST permitir texto libre como asignación independiente junto a recetas, conservando texto, fecha y turno sin referencia a receta ni fecha de creación. MUST rechazar valores vacíos, compuestos solo por espacios o de más de 100 caracteres Unicode completos, incluidos emojis. MUST sanitizar cualquier HTML y renderizar el resultado exclusivamente como texto.

#### Scenario: Rechazo de texto libre inválido

- GIVEN que una persona está creando o editando texto libre
- WHEN intenta guardar solo espacios o más de 100 caracteres Unicode completos
- THEN el valor no se guarda y se informa que el texto no es válido

#### Scenario: Texto con emoji y marcado HTML

- GIVEN que una persona introduce un texto libre válido que contiene un emoji y marcado HTML
- WHEN se guarda y se muestra la asignación
- THEN el emoji se conserva dentro del límite y el marcado no se interpreta como HTML sino como contenido de solo texto sanitizado

### Requirement: Edición, eliminación y ayuda de texto libre

El sistema MUST permitir editar y eliminar directamente cada texto libre, sin menú contextual ni confirmación de borrado. Una eliminación MUST ser inmediata. Las entradas MUST mostrarse sin imagen y MUST ofrecer el texto completo en un tooltip activable mediante cursor o pulsación, con ancho máximo que se adapte al viewport móvil. El sistema MUST NOT ofrecer una vía de edición mediante teclado distinta del formulario de edición definido.

#### Scenario: Eliminación directa de texto libre

- GIVEN que una celda contiene una entrada de texto libre
- WHEN una persona activa su acción directa de eliminar
- THEN la entrada se elimina inmediatamente sin menú contextual ni confirmación

#### Scenario: Consulta accesible de texto truncado

- GIVEN que el texto visible de una entrada no muestra todo su contenido
- WHEN una persona lo activa con cursor o pulsación
- THEN el tooltip muestra el texto completo con un ancho que no desborda el viewport móvil
