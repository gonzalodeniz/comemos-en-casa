# Plan — HU-004: recetas

**Estado (2026-10-31):** historia y plan aprobados expresamente por el usuario; sin implementación.  
**Fuente:** [HU-004 — Recetas](../historias-usuarios/HU-004-recetas.md).  
**Alcance:** planificación. El desglose se encuentra en [TASKS de HU-004](../../odd/tasks/hu-004-recetas.md). La aprobación de la historia y el plan y la creación de las tareas no autorizan por sí mismas implementación, migraciones, instalación de dependencias, operaciones remotas ni publicación.

## 1. Objetivo y decisiones confirmadas

Crear un catálogo compartido de recetas, accesible desde el menú y desde las comidas existentes. Cada receta tiene título obligatorio y único; imagen, ingredientes, elaboración y asociaciones son opcionales. Ingredientes y elaboración son texto libre. Las recetas y comidas se relacionan muchos a muchos. La creación, edición y lectura se realizan en páginas completas.

La búsqueda admite cualquier palabra y coincidencias parciales sin distinguir mayúsculas ni tildes; prioriza título, comidas asociadas e ingredientes. La prioridad del título prevalece aunque existan más coincidencias solo en ingredientes. El ejemplo «sopa pollo» de la HU es obligatorio. **No exigir todas las palabras**: el usuario corrigió esa interpretación con dicho ejemplo.

## 2. Propuesta técnica

Las soluciones siguientes son propuestas, no comportamiento existente ni autorización de ejecución.

### 2.1 Datos y relaciones

- Añadir una entidad de recetas y una tabla de asociación con las comidas existentes, con claves foráneas e índice único por pareja. Permitir recetas sin asociaciones y evitar duplicados simultáneos.
- Guardar el título sin espacios extremos y establecer una clave de unicidad que ignore mayúsculas/minúsculas, con restricción en base de datos y tratamiento claro del conflicto. La edición con el título propio no es un duplicado. No asumir reglas adicionales sobre tildes en la unicidad.
- Añadir una migración nueva y reversible, sin modificar migraciones publicadas ni los IDs de comidas. Al borrar una comida, retirar sus asociaciones sin borrar recetas; mantener el comportamiento existente de las asignaciones de planificación.
- Persistir ingredientes y elaboración como texto libre; no introducir un catálogo estructurado de ingredientes ni pasos en esta historia.

### 2.2 API y búsqueda

- Diseñar operaciones autenticadas para listar, consultar, crear, editar y eliminar recetas; validar CSRF y origen en escrituras según las convenciones existentes. Todas las cuentas autenticadas comparten los mismos permisos de gestión.
- Ofrecer filtro por comida y búsqueda parcial normalizada. Proponer una ordenación determinista por prioridad del mejor campo, seguida por coincidencias adicionales y desempate alfabético. Verificar explícitamente los ejemplos de HU-004 antes de fijar el contrato; no dar al número de coincidencias en ingredientes prioridad sobre una coincidencia en título.
- Integrar las asociaciones y el recuento real de recetas en los flujos de comidas, sustituyendo el cero provisional de HU-003. Devolver errores diferenciados de título duplicado, validación, autenticación y recurso inexistente.
- Preservar filtro y búsqueda durante la navegación de ida y vuelta; evitar que un fallo o una petición obsoleta muestre datos incorrectos.

### 2.3 Imágenes y almacenamiento

- Reutilizar, sin duplicar innecesariamente, la adquisición, validación, recorte y publicación de imágenes de comidas: selección de fichero, arrastre, portapapeles y URL. Aplicar las mismas reglas existentes de formato, límites, protección de URL y tratamiento de imagen.
- Usar `data/recetas/` bajo la raíz de datos configurada, con nombres opacos y referencias relativas. No almacenar binarios ni rutas arbitrarias en base de datos; no servir la carpeta completa públicamente.
- Mantener integridad ante fallos al publicar, sustituir, quitar o borrar una imagen. Reutilizar la coordinación existente de archivos activos/en preparación y la reconciliación exclusivamente manual, sin programar borrados automáticos. Comprobar permisos y persistencia del volumen; documentar copia y restauración conjunta de datos e imágenes.

### 2.4 Interfaz

- Añadir **Recetas** debajo de **Plan semanal**, con listado responsive, buscador y selector de comida. Acceder desde cualquier comida al listado filtrado; mostrar estado vacío cuando corresponda.
- Abrir detalle, creación y edición en páginas completas. Mostrar comidas asociadas, permitir seleccionar y quitar varias, y preseleccionar la comida si se crea desde el listado filtrado.
- Mantener filtro, búsqueda y scroll al regresar desde el detalle; entrar desde el menú sin filtro. Solicitar confirmación al descartar cambios y antes de eliminar definitivamente.
- Conservar la accesibilidad de teclado, etiquetas, foco y mensajes de error; adaptar escritorio, tableta y móvil sin alterar la lógica de planificación.

## 3. Tareas propuestas

| Tarea | Trabajo | Dependencias |
| --- | --- | --- |
| T1 | Revisar el modelo, la navegación y el servicio de imágenes existentes; concretar contratos y criterios de ordenación sin alterar las decisiones de producto. | Ninguna |
| T2 | Implementar migración, recetas, relación muchos a muchos y unicidad concurrente; preservar datos y borrado de comidas. | T1 |
| T3 | Implementar API, permisos, CSRF, filtro y búsqueda ordenada; integrar recuento real de recetas. | T2 |
| T4 | Adaptar carga, recorte, persistencia y limpieza manual de imágenes para `data/recetas/`. | T1, T2 |
| T5 | Implementar listado, filtros, navegación desde comidas y detalle de receta. | T3, T4 |
| T6 | Implementar páginas de creación/edición, asociaciones, confirmaciones y preservación de contexto. | T3, T4, T5 |
| T7 | Ejecutar regresión integrada, accesibilidad y pruebas responsive; actualizar documentación operativa. | T2–T6 |

## 4. Validación prevista

- **Datos y API:** migración en PostgreSQL aislado y desechable; usuarios autenticados distintos, CSRF, títulos vacíos/duplicados y mayúsculas/espacios, duplicados simultáneos, edición del título propio, relaciones cero/múltiples y eliminación de comida sin borrar recetas.
- **Búsqueda:** coincidencias parciales, tildes y mayúsculas, palabras en campos distintos, ausencia de resultados, prioridad de campos y ejemplo «sopa pollo»; filtro por comida combinado con búsqueda, orden alfabético sin búsqueda y desempate alfabético en resultados de igual relevancia.
- **Imágenes:** archivo, arrastre, portapapeles y URL; recorte cuadrado, imagen ausente/sustitución/eliminación, validaciones y protección de URL; fallos de archivos y base de datos, concurrencia y reconciliación manual sin eliminar imágenes activas o en preparación.
- **Interfaz:** navegación desde planificación y catálogo, estado sin recetas, filtro desde menú/comida, asociación preseleccionada y retirada, páginas completas, retorno con búsqueda/filtro/scroll y confirmaciones. Comprobar móvil, tableta, escritorio, teclado y lectores de pantalla.
- Ejecutar las suites correspondientes de backend y frontend y la compilación de frontend; ejecutar integración de PostgreSQL únicamente en una base aislada y desechable. Probar restauración y persistencia de imágenes tras recrear el contenedor.

## 5. Riesgos y puntos a concretar durante T1

- La puntuación exacta de resultados con coincidencias mixtas requiere concretarse respetando las prioridades y ejemplos confirmados; los resultados de igual relevancia se desempatan alfabéticamente por título.
- La eliminación concurrente de una comida y la edición de asociaciones requieren integridad transaccional sin pérdida de recetas.
- Base de datos y archivos no comparten transacción: evitar referencias a archivos inexistentes y no borrar imágenes activas ante fallos ambiguos.
- Las imágenes importadas por URL requieren las mismas defensas de red y límites existentes para comidas.
- Preservar el contexto del listado y la compatibilidad de navegación al acceder desde vistas distintas requiere pruebas reales de navegador.
