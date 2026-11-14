# Plan — Rediseño de la lista de la compra

**Estado (2026-11-14):** propuesta pendiente de aprobación. Sin implementación autorizada.

## 1. Objetivo

Reducir el desplazamiento y la carga visual, dar prioridad a la compra y mantener la coherencia con los catálogos y las demás vistas. Este plan no modifica estados de historias anteriores ni acredita nuevas validaciones.

Fuentes: [contexto](../product/lista-de-la-compra/contexto.md), [backlog](../product/lista-de-la-compra/backlog.md) e [historias del hito](../historias-usuarios/HIT-001-lista-compra/).

## 2. Alcance y comportamiento propuesto

### Selector superior de productos

- Mostrar categorías como tarjetas compactas con imagen o marcador y nombre, reutilizando el lenguaje visual del catálogo de productos.
- Elegir una categoría sustituye las categorías por sus productos en el mismo bloque; no añade otro listado debajo.
- Mostrar el nombre de la categoría y un botón explícito «Volver a categorías». Conservar la posición del selector al volver.
- Cargar productos al entrar en la categoría, con estado de carga, error recuperable y categoría vacía. Ignorar respuestas obsoletas tras cambiar de categoría o volver.
- Mantener el bloque adherido a la parte superior al desplazar la página, sin superponer contenido. Propuesta inicial: altura máxima de un tercio del área visible; desplazamiento interno solo si no cabe el contenido. Validar este límite con datos abundantes y zoom antes de fijarlo.
- Permitir recoger y desplegar el selector, especialmente en móvil, dejando visible una cabecera compacta «Añadir productos». No dejar una cuadrícula alta permanentemente fija.

### Ventana de cantidad

- Al pulsar un producto, abrir una ventana con su nombre, imagen pequeña opcional, cantidad y unidad: unidades, kg o g.
- Proponer cantidad inicial 1 y unidades; permitir cambiar ambos valores respetando las validaciones actuales del servicio, sin introducir reglas de negocio nuevas.
- Acciones «Cancelar» y «Añadir». Evitar envíos repetidos durante la petición.
- Tras éxito, actualizar la lista con la cantidad agregada devuelta por la API, mostrar confirmación y cerrar la ventana. Mantener la categoría y su posición para añadir más productos.
- Ante error, mantener abierta la ventana con los valores y permitir reintento; no mostrar éxito ni modificar la lista como si se hubiera guardado.
- Foco inicial en cantidad, recorrido de teclado contenido en la ventana, cierre mediante Escape cuando no haya envío en curso y retorno del foco al producto. Adaptar el contenido al teclado virtual y a pantallas pequeñas.

### Lista y separación del catálogo

- Colocar la compra inmediatamente debajo del selector, sin formularios de administración intermedios.
- Retirar de esta vista la creación de categorías/productos y la edición/importación/recorte de imágenes; conservar estas capacidades en «Catálogo de productos», con acceso secundario desde la compra.
- Mantener los productos manuales en «Pendientes» y «Comprados», esta última sección plegable y con contador. No ocultar pendientes por defecto.
- Usar filas compactas: casilla para comprado/pendiente, imagen pequeña opcional, nombre, cantidad y eliminación secundaria con nombre accesible. No hacer que eliminar active también la casilla.
- Conservar las recetas como grupos independientes con su nombre, texto y orden originales y todas sus operaciones actuales. No trasladar ni agregar ingredientes con productos manuales; mejorar solo su presentación y diferenciar visualmente los comprados.
- Usar el nombre que devuelve la lista sin depender de que termine de cargar el catálogo; evitar exponer identificadores técnicos como texto normal.
- Incorporar estados vacíos y de carga diferenciados, errores recuperables y bloqueo por entrada durante cambios. No mover ni eliminar filas hasta confirmar la operación; conservarlas si falla.
- Reutilizar colores, tipografía, bordes, iconos, espaciado y patrones de foco existentes; reservar el botón primario para la acción principal.

## 3. Límites

- Solo frontend: reutilizar consulta de categorías, consulta de productos por categoría y operaciones actuales de lista y recetas.
- Sin nuevos endpoints, migraciones, dependencias, búsqueda global, funcionamiento sin conexión ni sincronización en tiempo real.
- Preservar agregación de cantidades compatibles y conversión g/kg; unidades y peso continúan separados. No recalcular totales en el cliente.
- Mantener lista compartida, autenticación y protección CSRF existentes. Gestionar sesión caducada de forma coherente con la aplicación.
- Sin renombrado, traslado ni borrado de elementos del catálogo. Eliminar una entrada de compra no equivale a eliminar el producto del catálogo.

## 4. Fases de implementación

### Registro inicial de contratos

- La API de alta recibe `product_id`, `quantity` y `unit` y devuelve la entrada agregada; el servidor conserva la conversión y agregación. La historia HU-LC-001 exige separar unidades y peso.
- La consulta devuelve pendientes, comprados y secciones de recetas; las recetas conservan ingredientes y estado propios. Sus operaciones de marcado, desmarcado y borrado son independientes.
- `apiRequest` envía cookies y, cuando se proporciona, el encabezado CSRF. La vista actual no gestiona de forma uniforme los errores de sesión de todas las operaciones: comprobar y corregir durante el rediseño, sin asumir que ya funciona.
- Las pruebas actuales cubren acciones de recetas, agregación y envío CSRF; algunas dependen de formularios de administración que se retirarán y deberán trasladarse al catálogo, no perderse.
- `ShoppingList.redisenio.test.tsx` contiene dos pruebas de especificación explícitamente omitidas hasta las fases 2 y 3. No representan comportamiento implementado ni verificado.

| Fase | Trabajo y resultado verificable |
| --- | --- |
| 1. Contratos y regresión | Revisar `ShoppingList`, integración en `App`, API y pruebas. Registrar comportamiento vigente de agregación, recetas, cantidades y sesión. Añadir pruebas del recorrido nuevo sin conservar expectativas de formularios que se retirarán. |
| 2. Selector progresivo | Implementar categorías → productos → volver, consulta bajo demanda y protección frente a respuestas obsoletas. Separar la navegación del catálogo de las operaciones de compra. |
| 3. Ventana y adición | Implementar cantidad/unidad, validación, foco, cancelación, envío único, error y confirmación; conservar categoría y posición. |
| 4. Compra compacta | Reorganizar pendientes, comprados y grupos de recetas; retirar administración duplicada y ajustar callbacks de `App` que dejen de ser necesarios. Mantener todas las operaciones existentes. |
| 5. Estética y adaptación | Aplicar estilos acotados a la vista, selector adherente limitado y plegable, ventanas y filas coherentes. Comprobar que no cambian otros catálogos ni planificación. |
| 6. Verificación y documentación | Ejecutar pruebas, compilación y recorridos reales de navegador; documentar resultados y capturas. Actualizar el manual afectado sin marcar historias como hechas sin evidencia. |

Trabajar con pruebas focalizadas y cambios pequeños. Extraer selector, ventana y filas a componentes si facilita separar navegación, formularios y operaciones; mantener la coordinación de la lista en su vista. Los nombres nuevos y comentarios seguirán las convenciones del repositorio en español, preservando contratos existentes.

## 5. Criterios de aceptación

1. Se puede añadir un producto recorriendo categoría → producto → cantidad/unidad → añadir, volver a categorías y repetir sin recorrer todo el catálogo.
2. Añadir o cancelar mantiene la categoría seleccionada; volver restaura la posición del selector. Una respuesta tardía no cambia la categoría actual.
3. La compra no queda detrás de formularios de administración. El selector se puede recoger, no tapa filas ni foco y deja espacio útil para comprar en móvil.
4. Añadir repetidamente conserva los totales del servidor, incluidas conversiones compatibles. Fallos y dobles pulsaciones no generan éxitos falsos ni envíos duplicados desde la interfaz.
5. Marcar, desmarcar y eliminar siguen funcionando tanto para productos manuales como para ingredientes; se conserva el borrado de secciones de receta y su independencia respecto a los productos manuales.
6. La vista funciona con teclado, nombres largos, imágenes ausentes, catálogo vacío o abundante, carga lenta y fallos de consulta/escritura. Las otras vistas mantienen apariencia y comportamiento.

## 6. Validación prevista

- Pruebas de componentes e integración frontend: navegación y retorno, cantidades/unidades, cancelación, foco, errores/reintentos, carga, respuestas obsoletas, bloqueo de envío y sesión caducada.
- Regresión: agregación g/kg y unidades, pendientes/comprados, borrados, recetas, acceso al catálogo y operaciones de imágenes conservadas allí.
- Ejecutar `cd frontend && npm test` y `cd frontend && npm run build`.
- Navegador local: anchos de 375, 768 y 1280 px, zoom al 200 %, teclado, listas y catálogos largos; comprobar sticky, desplazamiento, foco visible y ventana con teclado virtual cuando haya dispositivo disponible. Registrar las limitaciones de simulación.
- Comparar antes/después con los mismos datos y dimensiones: altura previa al primer pendiente, desplazamiento para añadir y marcar, y pasos para añadir varios productos de la misma categoría. No fijar una reducción porcentual sin medir la situación inicial.
- No ejecutar backend por defecto para un cambio exclusivamente frontend. Si resulta necesario, usar la `.venv`, solicitar ejecución fuera del sandbox para `TestClient` y usar una base aislada para integración.

## 7. Archivos previstos y aprobación

- `frontend/src/ShoppingList.tsx` y posibles componentes auxiliares: composición y comportamiento.
- `frontend/src/App.tsx`: integración, navegación al catálogo y callbacks.
- `frontend/src/App.css`: estilos específicos sin efectos globales.
- `frontend/src/ShoppingList.test.tsx`, `ShoppingList.integration.test.tsx` y pruebas de integración de la aplicación afectadas.
- Manual de la funcionalidad bajo `docs/manual/`, según el recorrido resultante.

El siguiente paso es aprobar o ajustar este plan. No se crean tareas de ejecución ni se inicia implementación, commit, operación remota o publicación con este documento.
