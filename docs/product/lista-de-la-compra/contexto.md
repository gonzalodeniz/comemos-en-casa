# Lista de la compra

## Contexto

La funcionalidad ofrece una lista de la compra común para todos los usuarios de la aplicación. Todos pueden consultar y gestionar la lista, así como el catálogo compartido de productos y categorías. No existe un concepto de hogar.

## Alcance confirmado

- La interfaz y el contenido de esta funcionalidad estarán en español.
- La lista requiere conexión; no se necesita uso sin conexión ni sincronización posterior.
- No se necesita gestionar monedas ni importes.
- Los usuarios podrán añadir productos individuales a la lista o añadir ingredientes de recetas.
- Al añadir ingredientes de una receta, se podrá elegir entre añadirlos todos o seleccionar solo algunos.
- La lista tendrá una sección de productos pendientes de comprar y otra, situada debajo, de productos comprados.
- Marcar un producto pendiente lo moverá a comprados. Desmarcar un producto comprado lo devolverá a pendientes.
- Se podrán borrar productos de la lista.
- Los productos manuales se organizarán en categorías (por ejemplo, verduras, frutas y productos de limpieza), que contendrán productos (por ejemplo, manzanas, peras y lejía).
- Al añadir manualmente un producto a la lista se podrá indicar una cantidad en unidades o en peso.
- Desde la interfaz se podrán crear productos y categorías. Tanto los productos como las categorías podrán tener una imagen.
- El catálogo tendrá una entrada propia en el menú lateral y permitirá editar y eliminar categorías y productos. El comportamiento detallado está en la [especificación del catálogo de productos del hito HIT-001](../../historias-usuarios/HIT-001-lista-compra/especificacion-catalogo-productos.md).

## Decisiones

- Lista única y catálogo global compartidos por todos los usuarios.
- Todos los usuarios tienen los mismos permisos para gestionar la lista, los productos y las categorías.
- No se introduce una entidad o ámbito de hogar.
- El idioma es español; no se implementa funcionalidad multidivisa ni de importes.

## Stack

Se utilizará el stack actual del proyecto. Las tecnologías concretas no se detallan aquí porque no se han acordado como parte de esta definición de producto.

## Fuera de alcance o pendiente de definir

- Funcionamiento sin conexión.
- Gestión de precios, importes o monedas.
- Reglas para combinar productos repetidos o sumar cantidades en la lista.
- Cómo se trasladan o calculan cantidades de ingredientes al añadirlos desde una receta.

El backlog de historias de usuario se mantiene en el tracker; este documento recoge el contexto y las decisiones de producto.
