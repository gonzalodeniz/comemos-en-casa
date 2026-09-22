# Especificación de categorías de recetas

## Propósito

Definir el contrato para clasificar recetas públicas con etiquetas globales, consultarlas mediante filtros AND y eliminar el ciclo de borrador/publicada. Las recetas y sus imágenes son gestionables anónimamente por ahora.

## Requisitos

### Requisito: Normalizar y validar nombres de etiqueta

El sistema DEBE normalizar cada nombre con Unicode NFC, minúsculas sin perder acentos, recorte de extremos y colapso de cualquier secuencia de espacios a un único espacio interno. DEBE permitir letras Unicode, números Unicode, espacios internos y caracteres especiales Unicode; DEBE rechazar caracteres de control. El frontend DEBE renderizar los valores de etiqueta como texto escapado, nunca como marcado. El nombre DEBE tener como máximo 25 caracteres Unicode.

#### Escenario: Conservar acentos y espacios internos

- **DADO** un formulario que contiene `  COCINA   rápida  `
- **CUANDO** se normaliza el valor
- **ENTONCES** se guarda como `cocina rápida`
- **Y** la `á` se conserva
- **Y** los espacios internos quedan representados por uno solo

#### Escenario: Aceptar caracteres especiales Unicode y rechazar controles

- **DADO** un valor `menú ★ 2 / fácil` que contiene caracteres especiales Unicode
- **CUANDO** se valida y se muestra en el frontend
- **ENTONCES** se acepta como texto normalizado
- **Y** el frontend lo renderiza como texto escapado, nunca como marcado
- **Y** un valor con un carácter de control se rechaza con `422`
- **Y** la receta y sus asociaciones permanecen sin cambios

#### Escenario: Rechazar más de 25 caracteres

- **DADO** un nombre cuya longitud después de normalizar supera 25 caracteres
- **CUANDO** se guarda la receta
- **ENTONCES** la API devuelve `422`
- **Y** no crea una etiqueta parcial ni una asociación

#### Escenario: Ignorar un valor vacío

- **DADO** un elemento compuesto solo por espacios o vacío
- **CUANDO** se procesa la lista de etiquetas
- **ENTONCES** el elemento se ignora
- **Y** la receta puede guardarse sin esa etiqueta

### Requisito: Deduplicar y limitar etiquetas por receta

Una receta DEBE admitir cero o diez etiquetas efectivas. El sistema DEBE deduplicar por nombre normalizado, ignorar vacíos y aplicar el máximo de diez DESPUÉS de deduplicar. Los valores posteriores al décimo DEBEN ignorarse y no crear etiquetas ni asociaciones.

#### Escenario: Deduplicar antes de aplicar el máximo

- **DADO** `['Sopa', ' sopa ', '', 'Ágil', 'ágil']` y otros valores hasta superar diez entradas
- **CUANDO** se normaliza
- **ENTONCES** `sopa` aparece una sola vez, el vacío desaparece y `Ágil`/`ágil` se comparan según su forma normalizada en minúsculas
- **Y** se conservan como máximo diez nombres efectivos en el orden de su primera aparición

#### Escenario: Guardar una receta sin etiquetas

- **DADO** que todos los valores enviados están vacíos
- **CUANDO** se crea o actualiza una receta
- **ENTONCES** se guarda con cero asociaciones
- **Y** el catálogo no inventa una etiqueta predeterminada

### Requisito: Mantener etiquetas globales y su paleta accesible

Una etiqueta DEBE ser única globalmente por nombre normalizado y DEBE poder estar asociada a varias recetas. Cada respuesta de etiqueta DEBE exponer `id`, `name` y `color`. Al crear una etiqueta, el sistema DEBE elegir el color menos utilizado de la paleta accesible configurada; en empate DEBE elegir el primero de la paleta. DEBE reutilizar un color cuando corresponda. El color de una etiqueta existente DEBE permanecer estable mientras la etiqueta tenga asociaciones.

#### Escenario: Compartir una etiqueta entre recetas

- **DADO** que una receta ya usa `sin gluten`
- **CUANDO** otra receta se guarda con `SIN   GLUTEN`
- **ENTONCES** ambas recetas apuntan a la misma etiqueta global
- **Y** la respuesta expone el mismo `id`, `name = "sin gluten"` y `color`
- **Y** no se crea un duplicado por mayúsculas o espacios

#### Escenario: Asignar y reutilizar colores

- **DADO** una paleta con conteos de uso conocidos
- **CUANDO** se crea una etiqueta nueva
- **ENTONCES** recibe el color con menor conteo, resolviendo empates por el orden de la paleta
- **Y** una etiqueta nueva puede reutilizar un color cuyo uso sea menor que el de los demás
- **Y** el color mantiene contraste WCAG AA con el texto de la interfaz

### Requisito: Actualizar asociaciones y eliminar huérfanas de forma transaccional

La creación y edición de una receta DEBEN modificar receta, etiquetas y asociaciones en una transacción. Al quitar una asociación, el sistema DEBE eliminar en esa misma transacción las etiquetas que ya no estén referenciadas por ninguna receta. NO DEBE eliminar una etiqueta que otra receta siga usando. Un fallo en cualquier paso DEBE revertir toda la operación.

#### Escenario: Sustituir etiquetas y limpiar una huérfana

- **DADO** que una receta usa `rápido` y `fácil`, y ninguna otra receta usa `fácil`
- **CUANDO** se actualiza para usar solo `rápido`
- **ENTONCES** la asociación a `fácil` se elimina
- **Y** la etiqueta `fácil` se elimina en la misma transacción
- **Y** `rápido` y su color permanecen disponibles para las recetas que la usan

#### Escenario: No borrar una etiqueta todavía referenciada

- **DADO** que dos recetas usan `vegetariano`
- **CUANDO** una de ellas quita la etiqueta
- **ENTONCES** la otra asociación permanece
- **Y** la etiqueta global permanece

#### Escenario: Revertir una escritura fallida

- **DADO** que falla la inserción de una asociación después de crear una etiqueta
- **CUANDO** termina la transacción
- **ENTONCES** se revierten la receta, la etiqueta y las asociaciones de esa operación
- **Y** no queda una etiqueta huérfana visible en autocompletado

### Requisito: Permitir CRUD anónimo de recetas e imágenes

`GET`, `POST`, `PUT`, `PATCH` y `DELETE` de `/api/v1/recipes` DEBEN funcionar sin sesión, al igual que la subida, sustitución y eliminación de imagen de una receta. La API DEBE conservar la validación de contenido y tamaño de imagen. El borrado DEBE ser idempotente y NO DEBE requerir un parámetro de confirmación; la confirmación es responsabilidad exclusiva del frontend.

#### Escenario: Crear y editar una receta sin sesión

- **DADO** un cliente anónimo con una receta válida y hasta diez nombres de etiqueta
- **CUANDO** envía `POST /api/v1/recipes` y después `PATCH /api/v1/recipes/{id}`
- **ENTONCES** ambas operaciones responden correctamente sin `401`
- **Y** las respuestas incluyen las etiquetas normalizadas como objetos

#### Escenario: Gestionar una imagen sin sesión

- **DADO** una receta existente
- **CUANDO** un cliente anónimo sube un JPEG, PNG o WebP válido a `POST /api/v1/recipes/{id}/image`
- **ENTONCES** la receta devuelve el `imageUrl` actualizado
- **Y** un archivo inválido responde `422` sin cambiar la imagen actual
- **Y** eliminar o reemplazar la imagen no altera las etiquetas

#### Escenario: Confirmar el borrado solo en frontend

- **DADO** una persona pulsa eliminar en una receta
- **CUANDO** cancela el diálogo de confirmación
- **ENTONCES** el frontend no envía `DELETE`
- **Y** cuando confirma, envía `DELETE /api/v1/recipes/{id}` sin un requisito de confirmación de API

### Requisito: Exponer autocompletado público de etiquetas

`GET /api/v1/labels?q=` DEBE ser público. DEBE normalizar `q`; cuando `q` no quede vacío, DEBE devolver las etiquetas cuyo nombre normalizado contenga esa consulta como subcadena. DEBE exponer solo `id`, `name` y `color`, ordenar alfabéticamente y limitar el tamaño de la respuesta. Consultar no DEBE crear etiquetas.

#### Escenario: Autocompletar sin sesión

- **DADO** que existen `cocina rápida` y `sin gluten`
- **CUANDO** un cliente anónimo solicita `GET /api/v1/labels?q=ráp`
- **ENTONCES** recibe una respuesta `200` con objetos de etiqueta, incluyendo `cocina rápida` porque contiene la consulta como subcadena
- **Y** los objetos contienen `id`, `name` y `color`
- **Y** el número de etiquetas persistidas no cambia

#### Escenario: Consultar con q vacío

- **DADO** que existen etiquetas globales
- **CUANDO** se solicita `GET /api/v1/labels?q=`
- **ENTONCES** se devuelve la primera página ordenada de sugerencias
- **Y** no se crean etiquetas por la consulta

### Requisito: Filtrar el catálogo con parámetros label repetidos y AND

`GET /api/v1/recipes` DEBE aceptar parámetros `label` repetidos. El servidor DEBE normalizar, ignorar vacíos y deduplicar los parámetros antes de consultar. Con varias etiquetas efectivas, una receta DEBE tener todas ellas. Sin etiquetas efectivas, DEBE devolver todas las recetas. NO DEBE ofrecer OR ni combinar este filtro con texto, ingredientes, autor u otros filtros.

#### Escenario: Aplicar AND con parámetros repetidos

- **DADO** una receta con `rápido` y `vegetariano`, otra solo con `rápido` y otra solo con `vegetariano`
- **CUANDO** se solicita `/api/v1/recipes?label=rápido&label=vegetariano&label=rápido`
- **ENTONCES** solo se devuelve la primera receta
- **Y** la respuesta no contiene duplicados

#### Escenario: Tratar valores vacíos como ausencia de filtro

- **DADO** un catálogo con varias recetas
- **CUANDO** se solicita `/api/v1/recipes?label=&label=%20`
- **ENTONCES** se interpreta como ningún filtro
- **Y** se devuelven todas las recetas

#### Escenario: Etiqueta inexistente

- **DADO** que no existe la etiqueta `desconocida`
- **CUANDO** se solicita `/api/v1/recipes?label=desconocida`
- **ENTONCES** se devuelve una lista vacía
- **Y** no se crea la etiqueta

### Requisito: Mantener un catálogo único y retirar el ciclo editorial

El frontend DEBE presentar un único catálogo público llamado `Recetas`. El backend, frontend, persistencia, respuestas, tipos y pruebas DEBEN dejar de exponer o depender de `draft` y `published`. Todas las recetas existentes y nuevas DEBEN aparecer bajo la misma regla de visibilidad. Los endpoints de cambiar estado DEBEN retirarse.

#### Escenario: Mostrar todas las recetas en Recetas

- **DADO** que existen recetas creadas bajo los antiguos estados `draft` y `published`
- **CUANDO** se abre `/recetas` sin filtro
- **ENTONCES** ambas aparecen como recetas públicas sin insignia de estado
- **Y** el detalle tampoco muestra borrador/publicada

#### Escenario: Rechazar una operación de estado retirada

- **DADO** un cliente que intenta `POST /api/v1/recipes/{id}/publish` o `/draft`
- **CUANDO** se procesa la solicitud después de la migración de contrato
- **ENTONCES** la ruta no está disponible
- **Y** la receta conserva su visibilidad pública sin transición de estado

### Requisito: Ordenar etiquetas y conservar el estado del filtro en la interfaz

Las tarjetas, el detalle y el formulario DEBEN mostrar las etiquetas en orden alfabético con la misma clave estable. El filtro DEBE reflejar sus valores en la URL usando parámetros `label` repetidos, restaurarse al cargar la página y responder a atrás/adelante. La disposición DEBE ser usable en móvil y escritorio.

#### Escenario: Compartir y restaurar un filtro

- **DADO** una selección `rápido` y `vegetariano`
- **CUANDO** la persona navega o recarga `/recetas?label=rápido&label=vegetariano`
- **ENTONCES** el filtro se restaura con ambas etiquetas
- **Y** la petición usa dos parámetros `label`
- **Y** tarjetas, detalle y formulario muestran los nombres en orden alfabético

#### Escenario: Adaptar filtros a una pantalla estrecha

- **DADO** una ventana móvil con varias etiquetas seleccionadas
- **CUANDO** se muestra el catálogo
- **ENTONCES** los controles siguen siendo accesibles, no superponen contenido y permiten quitar cada etiqueta
- **Y** cambiar el filtro actualiza la URL sin introducir un modo OR

### Requisito: Mantener Mis recetas como seguimiento explícito, no como parte de esta historia

La eliminación de la antigua área `Mis recetas`, incluyendo sus endpoints, componentes, pruebas y enlaces de favoritos y colecciones, DEBE quedar registrada como seguimiento posterior. Esta historia NO DEBE eliminar esos elementos ni fingir que ya se retiraron.

#### Escenario: No ampliar el alcance durante la implementación

- **DADO** el trabajo de categorías de recetas
- **CUANDO** se implementa este cambio
- **ENTONCES** se modifican el catálogo público, el CRUD anónimo, las etiquetas y el ciclo editorial según esta especificación
- **Y** la retirada de `Mis recetas` queda en una tarea posterior separada
- **Y** favoritos y colecciones no se eliminan en esta entrega
