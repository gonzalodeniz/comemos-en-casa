# Tareas de implementación: categorías globales para recetas

## Alcance y orden

Estas tareas implementan únicamente etiquetas globales, CRUD anónimo de recetas e imágenes, filtrado AND del catálogo público, eliminación de `draft`/`published` y presentación única `Recetas`. La secuencia recomendada es **RED → GREEN → TRIANGULATE → REFACTOR**. Cada tarea debe cerrar con pruebas deterministas y mantener el cambio de datos transaccional.

**Fuera de alcance en esta entrega:** retirar la antigua área `Mis recetas`, sus endpoints, componentes, pruebas y enlaces de favoritos y colecciones. Ese trabajo queda como seguimiento posterior explícito; favoritos y colecciones no se borran aquí.

## Backend — dominio y persistencia

### 1. RED: fijar normalización, validación y contratos de etiqueta

- [ ] Añadir pruebas de dominio para NFC, minúsculas con acentos, recorte, colapso de espacios, espacios internos, límite de 25 caracteres, regla de caracteres especiales y controles, rechazo de controles/marcado, valores vacíos, deduplicación y máximo de diez aplicado después de deduplicar. Cubrir también respuestas con `id`, `name` y `color`.
- [ ] Añadir pruebas de contrato para `labels: string[]`, errores `422` sin mutación, nombres normalizados y ausencia total de `status`.
- [ ] Verificar con las suites focalizadas de `backend/tests/recipes/` y registrar el fallo por comportamiento ausente, sin implementar producción en esta tarea.

**Aceptación/evidencia:** las pruebas distinguen `á` de `a`, permiten espacios internos, ignoran vacíos, conservan la primera aparición hasta diez y exigen la regla de caracteres especiales y controles. **Rollback:** revertir solo las pruebas añadidas.

### 2. GREEN: implementar el valor de etiqueta y la paleta

- [ ] Añadir el valor de dominio y las funciones de normalización en `backend/src/comemos_en_casa/recipes/`, manteniendo PEP 8 y mensajes de validación deterministas.
- [ ] Implementar la paleta accesible versionada, la selección de color menos utilizado y el desempate por orden de paleta. Mantener el color de etiquetas existentes y permitir reutilización cuando una etiqueta se elimina.
- [ ] Ejecutar las pruebas de la tarea 1 y añadir casos de concurrencia o reintento donde el repositorio lo permita.

**Aceptación/evidencia:** la normalización es única para escritura, consulta y deduplicación; ningún nombre inválido alcanza SQL; cada etiqueta expone `id`, `name` y `color`. **Rollback:** revertir el dominio y la paleta sin cambiar migraciones existentes.

### 3. RED/GREEN: migrar tablas y asociaciones

- [ ] Añadir una migración posterior a la última existente con tabla global de etiquetas, unicidad por nombre normalizado, tabla de unión receta-etiqueta, claves foráneas `ON DELETE CASCADE` e índices de nombre y asociación.
- [ ] Añadir pruebas de migración para columnas, restricciones, unicidad, cascada, índices y ausencia de datos inventados.
- [ ] Verificar que la migración no cambia todavía recetas existentes ni crea etiquetas de forma implícita.

**Aceptación/evidencia:** la migración es aplicable en orden, no contiene duplicados posibles y las asociaciones no pueden apuntar a recetas o etiquetas inexistentes. **Rollback:** documentar reversión controlada de las tablas solo antes de aceptar escrituras de producción; no borrar automáticamente datos en un rollback de aplicación.

### 4. GREEN: implementar repositorio y transacciones de etiquetas

- [ ] Añadir inserción/recuperación global idempotente, asociación de receta, carga ordenada y cálculo de uso por color.
- [ ] Implementar reemplazo de asociaciones dentro de una transacción; eliminar solo etiquetas sin asociaciones mediante `NOT EXISTS` y conservar las todavía referenciadas.
- [ ] Cubrir carreras de creación del mismo nombre, fallos a mitad de escritura y borrado de receta con `ON DELETE CASCADE` más limpieza de huérfanas.

**Aceptación/evidencia:** un fallo revierte receta, etiquetas y asociaciones; una etiqueta compartida conserva identidad y color; una etiqueta huérfana no aparece en autocompletado. **Rollback:** revertir el repositorio y dejar las tablas nuevas intactas para una reversión segura de aplicación.

## Backend — API pública y catálogo

### 5. RED: fijar CRUD anónimo y eliminación del ciclo editorial

- [ ] Ampliar `backend/tests/recipes/test_api.py` para exigir `POST`, `PUT`, `PATCH`, `DELETE` y gestión de imagen sin sesión, respuestas con etiquetas, confirmación solo en frontend y ausencia de dependencia en `CurrentUser`.
- [ ] Añadir pruebas que exijan que `draft`/`published` no aparezcan en respuesta, que las rutas de estado se retiren y que recetas antiguas de ambos estados sean públicas.
- [ ] Cubrir errores de imagen y borrado idempotente sin tocar todavía la implementación.

**Aceptación/evidencia:** cada caso falla por la capacidad ausente y no por fixture compartida o sintaxis. **Rollback:** revertir solo las pruebas RED.

### 6. GREEN: exponer CRUD anónimo de receta e imagen

- [ ] Retirar la dependencia de usuario actual de las mutaciones de recetas y conservar validaciones de contenido, tamaño, UUID y componentes.
- [ ] Añadir o completar reemplazo/eliminación de imagen sin sesión; asegurar que un error no deja un URL nuevo ni una etiqueta parcial.
- [ ] Eliminar endpoints y modelos de publicar/volver a borrador; hacer que la lectura trate todas las filas existentes como públicas.
- [ ] Verificar con la suite de API y repositorio de recetas, además de la prueba de aplicación que enumera rutas.

**Aceptación/evidencia:** un anónimo puede crear, editar, borrar y gestionar imagen; no hay `status` en ningún contrato; la confirmación de borrado no se implementa en backend. **Rollback:** revertir handlers y modelos de API, sin eliminar aún la columna editorial hasta completar la migración por fases.

### 7. RED/GREEN: implementar autocompletado y filtros AND

- [ ] Añadir `GET /api/v1/labels?q=` público, con consulta normalizada, límite documentado, orden alfabético y respuesta `{labels: [{id, name, color}]}` sin creación de datos.
- [ ] Extender `GET /api/v1/recipes` para aceptar parámetros `label` repetidos, normalizarlos, ignorar vacíos, deduplicarlos y filtrar por AND mediante agrupación/cantidad, sin OR ni filtros combinados.
- [ ] Añadir pruebas de cero etiquetas (todo el catálogo), una inexistente (lista vacía), duplicados, acentos, paginación y autocompletado anónimo.

**Aceptación/evidencia:** el filtro se resuelve en SQL/repositorio, no en el cliente; una receta debe tener todas las etiquetas; no se crean etiquetas al consultar. **Rollback:** retirar el parámetro y endpoint nuevos sin alterar el CRUD base.

### 8. TRIANGULATE: validar integridad y compatibilidad backend

- [ ] Ejecutar pruebas focalizadas de recetas, migraciones, catálogo y cualquier adaptador de calendario que lea resúmenes de receta.
- [ ] Triangular transacciones con fallo de inserción, dos recetas compartiendo etiqueta, eliminación de una receta, concurrencia de color, reintento de DELETE y entrada con diez etiquetas tras deduplicación.
- [ ] Ejecutar `make test-backend` y corregir solo regresiones causadas por este cambio.

**Aceptación/evidencia:** pasan los escenarios de `spec.md`, las recetas históricas siguen visibles y no se modifican favoritos/colecciones ni el alcance de `Mis recetas`. **Rollback:** revertir únicamente ajustes introducidos durante la triangulación.

## Persistencia — retirada de estado editorial

### 9. GREEN: retirar `draft`/`published` de datos y consumidores

- [ ] Desplegar primero el código que ya no lee/escribe el estado, elimina publish/draft y representa todas las recetas como públicas.
- [ ] Aplicar una migración posterior que retire la columna y restricciones de estado solo tras confirmar que ningún consumidor la selecciona.
- [ ] Actualizar fixtures, migración de pruebas, repositorios, esquemas, adaptadores del calendario y documentación para que no quede referencia funcional a los estados.

**Aceptación/evidencia:** la columna puede eliminarse sin que fallen lecturas, las filas existentes permanecen y `/recetas` es el único catálogo público. **Rollback:** la vuelta del código anterior requiere restaurar la columna desde una copia/migración de contingencia; no ejecutar un `DROP` automático durante rollback.

## Frontend — catálogo, formulario y navegación

### 10. RED: fijar tipos, API, URL y presentación

- [ ] Ampliar `frontend/src/App.test.tsx` y pruebas de API para exigir `RecipeLabel`, ausencia de `RecipeStatus`, etiquetas ordenadas en tarjeta/detalle/formulario, parámetros `label` repetidos, restauración desde URL y navegación atrás/adelante.
- [ ] Cubrir selección vacía, deduplicación, sugerencias, AND visible, cero filtros como catálogo completo, límite de diez y errores de validación.
- [ ] Cubrir confirmación de borrado: cancelar no hace petición y confirmar llama a DELETE sin parámetro de confirmación.

**Aceptación/evidencia:** cada caso falla por la capacidad ausente y observa comportamiento accesible, no detalles frágiles de implementación. **Rollback:** revertir solo las pruebas RED.

### 11. GREEN: integrar tipos, cliente API y CRUD público

- [ ] Actualizar `frontend/src/types.ts` y `frontend/src/api.ts` con etiquetas, `labels: string[]`, respuesta `{id, name, color}`, URLSearchParams repetidos y CRUD/imágenes anónimo.
- [ ] Eliminar tipos, serializadores, insignias y ramas `draft`/`published`; mantener legibles las recetas existentes.
- [ ] Integrar el formulario en el flujo público de `Recetas`, con límite visible de diez, nombres normalizados devueltos por servidor y confirmación accesible de borrado.
- [ ] Verificar con la suite frontend y `npm --prefix frontend run typecheck`.

**Aceptación/evidencia:** el cliente no envía CSV ni parámetros de estado, el formulario conserva espacios internos y las tarjetas no presentan estado editorial. **Rollback:** revertir tipos, cliente y componentes nuevos sin tocar la deuda pendiente de `Mis recetas`.

### 12. GREEN: implementar filtro responsive y estado URL

- [ ] Añadir autocompletado de etiquetas con debounce/control de cancelación apropiado y mostrar nombres/colores accesibles.
- [ ] Sincronizar selección con `location.search`, usando parámetros `label` repetidos, sin duplicados y con comportamiento correcto de atrás/adelante.
- [ ] Ordenar etiquetas en tarjetas, detalle y formulario; adaptar controles a móvil y escritorio sin perder foco, nombre accesible ni posibilidad de retirar una selección.

**Aceptación/evidencia:** una URL compartida reproduce exactamente el conjunto AND; vacío equivale a todas; no aparece un modo OR ni filtros combinados. **Rollback:** revertir solo markup, estado URL y estilos del filtro.

### 13. TRIANGULATE: pruebas de interacción y build frontend

- [ ] Ejecutar la suite frontend y comprobar catálogo vacío, carga completa, filtros AND, etiquetas repetidas, autocompletado, URL, atrás/adelante, orden alfabético, confirmaciones y CRUD de imagen.
- [ ] Ejecutar `npm --prefix frontend run typecheck` y `npm --prefix frontend run build`.
- [ ] Revisar que favoritos, colecciones y enlaces de la antigua `Mis recetas` sigan presentes porque su retirada es posterior, y que no queden referencias a `draft`/`published` dentro del flujo de catálogo.

**Aceptación/evidencia:** pasan pruebas, typecheck y build; el layout sigue usable y la confirmación cancelada no hace red. **Rollback:** revertir ajustes de presentación o pruebas de triangulación.

## Cierre

### 14. REFACTOR: consolidar contrato y documentación

- [ ] Eliminar duplicación entre lecturas de etiqueta en lista/detalle, mantener consultas parametrizadas y conservar transacciones alrededor de receta, asociación y limpieza.
- [ ] Revisar que la lista de caracteres permitidos, límite de 25, máximo de diez, política de color, AND, URL y ausencia de filtros combinados sean coherentes en propuesta, diseño, especificación y pruebas.
- [ ] Ejecutar `make test`, `npm --prefix frontend run typecheck` y `npm --prefix frontend run build`; registrar cualquier fallo ambiental sin ampliar el alcance.

**Aceptación/evidencia:** todo requisito de `spec.md` tiene una prueba de backend o frontend; no se edita ningún archivo de `Mis recetas`, favoritos o colecciones para retirarlos en esta entrega; se documenta la estrategia de rollback de estado editorial.

## Verificación final prevista

- Backend: suites focalizadas de recetas y migraciones, después `make test-backend`.
- Frontend: pruebas de interacción, `npm --prefix frontend run typecheck` y `npm --prefix frontend run build`.
- Suite completa: `make test`.
- La retirada de `Mis recetas` se verifica únicamente en una historia posterior dedicada; en esta entrega se verifica que permanece fuera de los cambios.
