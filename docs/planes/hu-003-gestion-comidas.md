# Propuesta de plan — HU-003: gestión de comidas

**Estado (2026-10-29):** plan y TASKS aprobados expresamente por el usuario; implementación iniciada.  
**Fuente:** [HU-003 — Gestión de comidas](../historias-usuarios/HU-003-gestion-comidas.md).  
**Alcance de este documento:** planificación únicamente. Su creación no autoriza implementación, migraciones, instalación de dependencias, ejecución remota ni publicación. El desglose está en [TASKS de HU-003](../../odd/tasks/hu-003-gestion-comidas.md); su creación no aprueba las tareas ni autoriza ejecutarlas.

## 1. Objetivo y alcance confirmado

Ampliar el catálogo compartido de etiquetas alimentarias de HU-002, presentado al usuario como **Comidas**, para crear, editar y eliminar comidas con nombre e imagen opcional. No crear un segundo catálogo ni propietarios por usuario.

- Acceso y gestión para cualquier usuario autenticado, sin permisos adicionales por rol.
- Entrada **Comidas** debajo de **Plan semanal** en el menú lateral.
- Almacenamiento de imágenes decidido: archivos en `data/comidas`, con montaje persistente de `data/`; la base de datos conserva referencias relativas y metadatos, no el contenido binario.
- Nombre obligatorio, sin espacios externos, máximo 100 caracteres y único ignorando mayúsculas y espacios externos, también al editar.
- Imagen opcional: JPG, PNG o WebP estática de hasta 2 MiB y 5 megapíxeles; entrada por fichero, arrastre, URL o portapapeles; recorte ajustable. Resultado WebP 512×512, calidad 85, conservando alpha; cubiertos por defecto.
- Los cambios de nombre e imagen se reflejan en las asignaciones existentes.
- Borrado siempre confirmado con calendario y número de **asignaciones**, y plato y número de recetas, provisionalmente cero. Se eliminan todas las asignaciones pasadas y futuras de esa comida.
- Los contadores se obtienen al abrir el aviso; no hay actualización automática ni reconfirmación por cambios concurrentes.
- Recetas fuera de alcance: ojo visible y deshabilitado, sin construir entidades, pantallas ni API de recetas.

## 2. Punto de partida verificado y diferencias

| Área | Estado actual | Cambio previsto |
| --- | --- | --- |
| Persistencia | `FoodLabel` en `backend/app/models.py`: UUID, código único y nombre de 80 caracteres. `MealAssignment` referencia su ID mediante FK con `ondelete="RESTRICT"`. | Mantener IDs y referencias, ampliar nombre a 100, añadir unicidad normalizada e imagen opcional. Borrar asignaciones e identificador de comida en una transacción. |
| API | `backend/app/meal_planning_api.py` expone `GET /api/v1/food-labels`, calendario y operaciones con previsualización. | Ampliar el catálogo y las representaciones de etiquetas; no reemplazar la API de planificación. |
| Concurrencia | `serialize_meal_planning_writes` usa bloqueo transaccional PostgreSQL para escrituras de planificación. | Coordinar el borrado del catálogo con ese mismo mecanismo, sin aplicar a este borrado la reconfirmación por token de HU-002. |
| Cliente | `frontend/src/mealPlanningApi.ts` define `FoodLabel` sin imagen. | Extenderlo y refrescar catálogo y calendario tras mutaciones. |
| Navegación | `frontend/src/AppWorkspace.tsx` muestra «Plan semanal» y «Gestión de usuarios». | Añadir «Comidas» debajo de «Plan semanal», conforme a la aclaración del usuario y CA-1; no crear otra vista de planificación. |
| Iconos | `frontend/src/AppIcon.tsx` incluye calendario y cubiertos, pero no lápiz, papelera, ojo ni plato. | Extender el sistema SVG existente. No se necesitan imágenes generadas por IA. |
| Dependencias | `backend/requirements.txt` no declara un procesador de imágenes; `frontend/package.json` no declara herramienta de recorte. | Incorporar Pillow y react-easy-crop según decisiones de T1. |

## 3. Propuesta técnica

Las rutas, nombres y módulos nuevos que se indican a continuación son **propuestos**, no funcionalidad existente.

### 3.1. Modelo y migración

1. Mantener `FoodLabel.id` y `code`; generar códigos técnicos estables para nuevas comidas sin derivarlos del nombre editable ni exponer un nuevo campo de formulario.
2. Ampliar el nombre a 100 caracteres y guardar una clave normalizada para unicidad, calculada con la misma función en alta y edición. Aplicar restricción única de base de datos para evitar duplicados simultáneos; mapear el conflicto a un error de negocio comprensible.
3. Normalizar nombres con Unicode NFC, recortar espacios externos y comparar sin distinguir mayúsculas; mantener espacios internos y diacríticos.
4. Guardar las imágenes como archivos en `data/comidas`, con montaje persistente de `data/`, según la decisión del usuario. Guardar en base de datos únicamente una referencia relativa a la raíz de datos (por ejemplo, `comidas/<uuid>.webp`) y metadatos de formato, tamaño y dimensiones. No guardar binarios, rutas absolutas del host ni nombres de archivo proporcionados por el usuario. La referencia es opcional y no cambia el UUID de la comida.
5. Crear una migración posterior a `0005_meal_planning.py`, sin modificar migraciones publicadas. Comprobar previamente colisiones de nombres normalizados y detener con diagnóstico si aparecen, sin fusionar ni borrar comidas automáticamente.
6. Conservar las etiquetas y asignaciones existentes, sin resembrar registros eliminados al consultar. No añadir tablas de recetas.
7. Definir un downgrade seguro en base desechable: los nombres entre 81 y 100 caracteres requieren una política explícita; nunca truncarlos silenciosamente.

### 3.2. Contrato de API propuesto

Reutilizar `get_active_session`, `require_csrf` y `get_database_session`. Aplicar CSRF y comprobación de origen a escrituras y operaciones POST auxiliares. Mantener `/api/v1` y separar la lógica del catálogo y de procesamiento de imágenes en módulos nuevos, registrados desde `backend/app/main.py` si se utiliza otro router.

| Operación | Contrato propuesto |
| --- | --- |
| Consultar catálogo | Ampliar `GET /food-labels` conservando `labels`, `id`, `code`, `name`; añadir referencia opcional de imagen. |
| Crear / editar | `POST /food-labels` y `PATCH /food-labels/{id}` con nombre e intención explícita de conservar, sustituir o quitar imagen. |
| Obtener impacto | `GET /food-labels/{id}/deletion-impact`: número de filas de asignaciones sin filtro de fechas y `recipe_count: 0`. |
| Eliminar | `DELETE /food-labels/{id}` con confirmación explícita. Borrar asignaciones, comida y referencia de imagen en una transacción de base de datos; eliminar el archivo propio después del commit mediante el ciclo de limpieza descrito abajo. No exigir coincidencia del contador mostrado. |
| Preparar imagen | Entrada autenticada y limitada para fichero o URL, devolución de una previsualización temporal apta para recorte; nombres de rutas definitivos pendientes. |
| Consultar imagen | Ruta autenticada por ID de imagen, con tipo de contenido verificado y caché privada. Evitar que la caché pública exponga recursos de la sesión. |

- Ampliar las representaciones de comida en catálogo, calendario y previsualización, para que todas utilicen los mismos datos actuales y no instantáneas del nombre o de la imagen.
- Distinguir errores de validación, duplicado, inexistencia, autenticación y fallo de imagen; nunca responder con éxito a un guardado que haya fallado.
- Dentro del bloqueo compartido, eliminar **todas** las asignaciones actuales antes de la comida, incluidas las incorporadas desde la apertura del aviso. Mantener la FK como defensa frente a referencias huérfanas y probar la carrera con nuevas asignaciones en PostgreSQL.
- La edición no altera las reglas de repetición ni el protocolo de confirmación de las operaciones propias de HU-002.

### 3.3. Flujo de imágenes y seguridad

1. Unificar fichero, arrastre y portapapeles como entrada binaria; el selector de ficheros representa la elección de una ruta local, no acceso arbitrario al sistema de archivos desde el servidor.
2. Para URL, proponer importación controlada desde backend que produzca una previsualización del mismo origen. Evita depender de permisos CORS de servidores externos; implica proteger expresamente el acceso de red.
3. Aplicar límite de 2 MiB durante lectura, validar formato real, decodificación y máximo 5 megapíxeles antes del recorte, también para URL y portapapeles.
4. Para URL, admitir solo HTTP(S), bloquear credenciales y destinos locales/privados/loopback/link-local/metadatos; validar DNS y dirección de conexión en cada salto, máximo cinco redirecciones y diez segundos totales. Probar con DNS/transporte simulados.
5. Usar Pillow para decodificar, aplicar orientación EXIF, eliminar metadatos y generar WebP de 512×512, calidad 85, alpha conservado. Rechazar contenido animado y limitar a 5 megapíxeles.
6. Permitir ajustar el cuadrado antes de guardar; validar también en backend que el resultado es una imagen cuadrada válida. No confiar solo en el recorte del navegador.
7. Imágenes temporales vinculadas a sesión, expiran en una hora y limitadas a 50 MiB por sesión; limpiar abandonos. Un fallo no modifica imagen persistida.
8. Guardar el nombre independientemente de la preparación fallida: en alta, sin imagen; en edición, conservando la anterior. Quitar una imagen es una intención explícita distinta de fallar al sustituirla.
9. Si se propone multipart, adaptar `frontend/src/api.ts` para no forzar cabecera JSON y verificar dependencias de backend y límites del proxy. No introducir codificación base64 sin evaluar su sobrecoste.

### 3.4. Persistencia de archivos y operación

- `backend/Dockerfile` usa `WORKDIR /app`; se propone añadir al servicio `backend` de `docker-compose.yml` el montaje de lectura/escritura `./data:/app/data` (volumen persistente de tipo bind). Así, `data/comidas` del host corresponde a `/app/data/comidas` dentro del backend. La raíz de almacenamiento debe configurarse explícitamente como `/app/data` en contenedor, evitando depender del directorio desde el que se inicia el proceso.
- La implementación deberá preparar la raíz y `comidas/` con permisos mínimos de lectura/escritura para el UID/GID efectivo del backend. No utilizar permisos globales `0777`, no incluir imágenes en la imagen Docker ni servir todo `data/` como directorio público. Este plan no crea directorios, cambia permisos ni monta volúmenes.
- Generar nombres opacos únicos en servidor y extensión según formato verificado. Resolver las referencias exclusivamente bajo la raíz autorizada; rechazar traversal, rutas absolutas y enlaces que escapen de ella. Entregar imágenes por la ruta autenticada de API, sin aceptar rutas arbitrarias del cliente.
- Base de datos y sistema de archivos **no comparten transacción**. Preparar el nuevo archivo validado, publicar con renombrado atómico dentro del mismo sistema de archivos y después confirmar su referencia en base de datos. Si falla la escritura, mantener la referencia anterior; si falla la transacción, limpiar compensatoriamente el archivo nuevo. No eliminar la imagen anterior hasta confirmar la sustitución.
- Al quitar imagen o borrar comida, confirmar primero el cambio de referencia y datos en base de datos, y después borrar el archivo antiguo. Un fallo de limpieza deja un huérfano para reintento, no una comida apuntando a un archivo eliminado. Añadir limpieza idempotente y reconciliación de huérfanos con período de seguridad que no elimine archivos en preparación ni referencias activas; probar caídas entre cada paso.
- Respaldar y restaurar **base de datos y `data/` conjuntamente**, con una ventana sin escrituras o un mecanismo equivalente de consistencia. Verificar la restauración de referencias e imágenes, persistencia tras recrear el contenedor y exclusión de archivos de usuario del control de versiones. La limpieza no debe ejecutarse sobre una copia o restauración incompleta.

### 3.5. Interfaz e integración

- Proponer una vista `FoodCatalog` nueva en `frontend/src/`, integrada con `App.tsx` y `AppWorkspace.tsx`, y estilos coherentes en `App.css`.
- Cuadrícula responsive, buscador por nombre y acción visible de crear; tarjetas con imagen, nombre, lápiz, papelera y ojo deshabilitado. Acciones con nombre accesible, foco visible y manejo por teclado.
- Formulario de nombre e imagen con guardar/cancelar; elección, pegado, arrastre, URL y recorte con alternativa accesible a arrastrar. Presentar validaciones y errores sin perder el nombre introducido.
- Modal de borrado con calendario y número de asignaciones y plato y cero recetas; distinguir claramente confirmar y cancelar. Recuento fijo durante su apertura.
- Extender `MealPlanning.tsx` y `CalendarDay.tsx` para usar la imagen de la comida o los cubiertos. Invalidar/refrescar catálogo y planificación al regresar a esas vistas tras crear, editar o eliminar, sin añadir tiempo real entre sesiones como requisito.

## 4. Secuencia de trabajo propuesta

1. Plan aprobado y TASKS solicitado expresamente el 2026-10-29. Resolver los puntos técnicos de la sección 7 antes de ejecutar las tareas afectadas; aprobar el plan no demuestra que estas elecciones estén resueltas. La implementación requiere autorización expresa adicional.
2. Preparar pruebas de normalización, unicidad y migración; implementar persistencia conservando IDs y datos.
3. Implementar API de catálogo, impacto y borrado transaccional; verificar autenticación, CSRF y concurrencia con planificación.
4. Implementar adquisición, validación, recorte y persistencia de imágenes con sus pruebas y límites.
5. Implementar vista del catálogo y formularios; integrar imágenes y refresco con planificación.
6. Ejecutar pruebas de regresión y recorrido de aceptación; actualizar documentación de configuración, almacenamiento y recuperación si corresponde.

## 5. Trazabilidad y validación propuesta

Los números se refieren a los criterios de la HU; las pruebas siguientes están **planificadas, no ejecutadas**.

| Criterios | Evidencia prevista |
| --- | --- |
| 1 | Navegación lateral en escritorio y móvil: «Comidas» debajo de «Plan semanal» y apertura de la vista principal. |
| 2 | API sin sesión rechazada; operaciones permitidas a distintas cuentas autenticadas sobre el mismo catálogo; escrituras sin CSRF rechazadas. |
| 3–5 | Cuadrícula, nombre, imagen, búsqueda, acciones accesibles y ojo deshabilitado sin navegación a recetas. |
| 6 | Nombre vacío, espacios, límites 100/101 y persistencia sin espacios externos; alta sin imagen muestra cubiertos. |
| 7–8 | Las cuatro entradas alcanzan el recorte ajustable; resultado cuadrado persistido. |
| 9 | Duplicados en alta, edición y dos peticiones concurrentes; diferencias de mayúsculas y espacios externos; conservar nombre propio permitido. |
| 10 | Edición visible en catálogo, selector y asignaciones semanales/mensuales existentes tras refresco de datos. |
| 11–13 | Confirmación siempre, incluso sin uso; calendario/plato; almuerzo y cena del mismo día cuentan dos; cero recetas; cancelar conserva datos; confirmar elimina pasado y futuro sin afectar otras comidas. |
| 14 | Cambiar asignaciones desde otra sesión con aviso abierto; conservar contador mostrado y aceptar confirmación sin nueva previsualización, sin referencias huérfanas. |
| 15 | JPG/PNG/WebP, límite exacto y exceso de bytes por cada origen; formato falso, contenido corrupto, dimensiones excesivas y URL no permitida. |
| 16–18 | Quitar imagen restaura cubiertos; fallo en alta permite guardar nombre; sustitución fallida conserva imagen previa y permite editar nombre. |

Además, probar archivos persistentes tras recrear el backend, permisos insuficientes, intentos de traversal, fallo de escritura o commit, limpieza compensatoria, reconciliación sin borrar referencias activas y restauración conjunta de base de datos y `data/`.

Comandos para la implementación futura: `make test`, `make build-frontend` y pruebas de integración PostgreSQL en un proyecto/base **aislados y desechables**, con `RUN_DB_INTEGRATION=1` según el README raíz. No ejecutar migraciones de prueba ni downgrade sobre datos a preservar. Añadir pruebas focalizadas backend/frontend junto a las existentes y comprobar que HU-002 conserva su comportamiento.

## 6. Límites del plan

No incluye recetas, permisos por propietario, sincronización en tiempo real, importación masiva ni cambios en las reglas de repetición. No modifica ni aprueba HU-002 retroactivamente. La eliminación del catálogo es distinta del borrado individual o repetido de asignaciones de HU-002.

## 7. Decisiones pendientes antes de implementar

- **Procesamiento confirmado por el usuario:** react-easy-crop en cliente y Pillow en servidor; JPG/PNG/WebP estáticos hasta 2 MiB y 5 megapíxeles; orientación EXIF aplicada, metadatos eliminados; salida WebP 512×512, calidad 85, conserva alpha; temporales una hora y máximo 50 MiB por sesión.
- **Normalización confirmada por el usuario:** Unicode NFC, trim externo y unicidad ignorando mayúsculas; generar código con UUID estable. En migración, abortar con diagnóstico ante colisiones; el downgrade aborta si encuentra nombres que no caben en 80 caracteres, sin truncar.
- **Importación URL confirmada por el usuario:** HTTP(S), máximo cinco redirecciones y diez segundos totales; bloquear destinos locales y privados. La verificación DNS/conexión de cada salto sigue siendo requisito de seguridad.
- **API confirmada por el usuario:** conservar GET `/food-labels`; añadir POST/PATCH/DELETE y endpoint de impacto; imágenes solo autenticadas y caché privada; duplicados 409 y datos inválidos 422. Restan detalles de contrato que se documentarán en T1.
- **Compatibilidad:** revisar datos actuales antes de imponer unicidad y definir fallo seguro del downgrade ante nombres de más de 80 caracteres.

La aprobación del plan no resuelve automáticamente estas decisiones; deben registrarse antes de ejecutar sus partes afectadas. El almacenamiento en archivos y el respaldo conjunto de base de datos y `data/` sí están confirmados por el usuario.
