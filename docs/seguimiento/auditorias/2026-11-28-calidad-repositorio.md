# Auditoría de calidad · Repositorio completo · 28 de noviembre de 2026

**Resultado:** 13 hallazgos locales: **4 de severidad crítica, 1 alta, 6 medias y 2 bajas**. Dos riesgos afectan a datos existentes: repetir una acción de compra puede borrar la línea y escribir una copia con el mismo nombre puede sustituir la anterior. Hay además una prueba que puede borrar copias ajenas a su fixture. Son conclusiones del código versionado, no incidentes observados en producción. **521 pruebas pasaron; 18 casos no se ejecutaron.** No se certifica el funcionamiento del sistema.

## Alcance y antecedentes

- Rol: `quality-auditor`. Rama `develop`; revisión `a0a924909cdc3fcb0c366acc82f774f32addd0eb`. Se examinó el árbol del commit: aplicación, pruebas, migraciones, configuración, scripts, documentación de dominio, guías y seguimiento. Se usaron los umbrales de referencia de la auditoría; el perfil y la arquitectura inicial no fijan otros.
- Al inicio, `git status --short` solo devolvió `?? docs/seguimiento/auditorias/2026-11-28-calidad-cambios-pendientes.md`. Se reconoció su alcance (un diff vacío), sin usarlo como evidencia del código, importar sus resultados ni modificarlo.
- El [perfil](../../project/PERFIL.md), el [flujo local](../../process/FLUJO_DE_TRABAJO.md) y el rol versionado establecen seguimiento en documentos. No se consultó GitHub, no se abrieron ni comentaron issues, ni se consultaron credenciales. No se modificó código, no se hizo build, commit ni validación funcional.
- **Tendencia:** sin auditoría de calidad anterior versionada en la historia de esta rama: `git log HEAD --format= --name-only -- docs/seguimiento/auditorias | sort -u` solo enumera el informe de **seguridad** del 27/11. Los 13 registros constituyen una línea base, no 13 regresiones. Distribución local por categoría: 5 «hallazgo critico», 2 «deuda tecnica acumulada», 1 «observacion de test», 3 «inconsistencia documental» y 2 «riesgo de eficiencia». Cierres, reapariciones, antigüedad e inventario remoto por estado: no determinables. No se atribuye ningún hallazgo a una entrega del roadmap ni se asigna prioridad.

## Las doce áreas

| Área | Resultado |
| --- | --- |
| 1. Complejidad ciclomática | C09: dos funciones vuelven a decidir qué cambia en cada fecha. |
| 2. Duplicación | C02, C03, C09: la validación, la creación del ZIP y las reglas de planificación están repartidas entre caminos equivalentes. |
| 3. Nomenclatura | C13: el término de propiedad de la lista contradice su carácter familiar. Los nombres de contratos externos no se consideran infracción por estar en inglés. |
| 4. SOLID | C10: navegación y ciclo de edición no se pueden probar de forma independiente sin montar el calendario. |
| 5. Patrones y antipatrones | C01, C03: transición que se fusiona consigo misma y publicación no atómica de archivos. |
| 6. Tamaño | C09, C10; los restantes excesos se enumeran abajo sin convertir umbrales por sí solos en defectos. |
| 7. Cobertura y calidad de pruebas | C04, C06. Hay evidencia de ejecución, no porcentajes de cobertura. |
| 8. Deuda técnica | C09 y C10 representan deuda aunque no lleven marcadores; cero TODO/FIXME/HACK en el corpus de código. Sin acceso a handoffs de PR remotas. |
| 9. Estándares y convenciones | C04: aislamiento de datos; C05: configuración de base de datos; C11: correspondencia del índice con el árbol. |
| 10. Documentación | C11–C13. Se contrastaron COMMANDS.md, el índice, la arquitectura histórica, historias y manuales; el número histórico de pruebas de COMMANDS.md no se trató como cifra vigente. |
| 11. Eficiencia | C07: recorridos por sección y resolución duplicada de imágenes; C08: compilación repetida. No se estiman segundos ni memoria sin medirlos. |
| 12. Métricas y tendencia | Resultados y límites abajo; sin serie histórica comparable. |

## Hallazgos

Cada ficha es independiente. Campos comunes: **Rol:** quality-auditor · **Entrega:** pendiente de asignación · **Requisitos:** ninguno · **Reglas de negocio añadidas:** ninguna · **Dependencias:** ninguna para registrar el hallazgo · **Auditoría:** commit `a0a9249`, 2026-11-28. Los casos de aceptación son los descritos en cada ficha; cuando hay una historia relacionada se cita como contexto, no como nuevo requisito. **Fuera de alcance:** cambios fuera del problema descrito, rediseñar contratos públicos sin necesidad, ejecutar correcciones, cambiar estados o priorizar.

### C01 · Repetir un marcado puede borrar la línea de compra

Severidad: critica · Categoria: hallazgo critico · Area: Patrones de diseño

**Descripción e impacto:** Un segundo marcado sobre una línea numérica ya comprada selecciona la propia fila como destino de la fusión. SQLAlchemy devuelve el mismo objeto: el código le suma su cantidad y lo borra. Ocurre también al desmarcar dos veces. Dos familiares con la lista abierta pueden actuar sobre la misma entrada sin saberlo.

**Evidencia:** `backend/app/shopping_list_api.py:233–253,273–293`: la consulta filtra por el estado de destino, sin comprobar el estado de origen ni excluir `item.id`; después ejecuta `db.delete(item)`. Con una única fila numérica sin observación y ya en el estado solicitado, solo puede coincidir ella. `frontend/src/ShoppingList.tsx:295–309,463` permite marcar desde la vista local. HU-LC-002 y HU-LC-003 requieren conservar la cantidad.

**Recomendación:** Comprobar el estado antes de buscar una fusión: si ya es el solicitado, devolver la representación actual sin escribir. Excluir además el ID de origen en la búsqueda. Probar ambos sentidos y la fusión legítima entre dos filas distintas.

**Criterios de aceptación:**
- [ ] Dos peticiones sucesivas al mismo ID conservan ID, cantidad y fila; dos filas compatibles distintas siguen sumándose una sola vez.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** API y pruebas de lista de compra. **Esfuerzo orientativo:** medio.  
**Huella:** `patrones|lista-compra|fusion-con-la-propia-fila`.

### C02 · El alta admite cantidades que se guardan como cero

Severidad: critica · Categoria: hallazgo critico · Area: Duplicación y reglas de dominio

**Descripción e impacto:** El formulario admite 0,1 gramos; el alta redondea ese valor a cero y confirma el guardado. La edición rechaza exactamente el mismo resultado. Una entrada numérica puede por tanto aparecer sin la cantidad pedida.

**Evidencia:** `frontend/src/DialogoCantidadCompra.tsx:39–44,58`: `min="0.01" step="any"`; `backend/app/shopping_list_api.py:62–88` comprueba el signo antes, pero no después del redondeo; `:167–172` sí lo comprueba en PATCH. `backend/app/models.py:217`: `Numeric(12, 3)`. Verificación aritmética independiente indicada abajo.

**Recomendación:** Usar en POST y PATCH la misma normalización y validar el intervalo representable tras redondear, también al acumular; devolver un error de validación sin escribir si el resultado es cero o desborda. Conservar el comportamiento de texto libre.

**Criterios de aceptación:**
- [ ] 0,1 g no crea ni modifica filas y da el mismo error en alta y edición; los pesos válidos siguen convirtiéndose y acumulándose según HU-LC-001.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** API, pruebas de cantidades y formulario de alta. **Esfuerzo orientativo:** medio.  
**Huella:** `duplicacion|lista-compra|validacion-despues-del-redondeo`.

### C03 · Una copia nueva puede sustituir una anterior o aparecer a medio escribir

Severidad: critica · Categoria: hallazgo critico · Area: Diseño de persistencia

**Descripción e impacto:** Las rutas manual y programada escriben directamente en un nombre público con resolución de un segundo. Dos creaciones en el mismo segundo comparten destino; el modo `w` trunca la anterior. La manual calcula el nombre antes de esperar el bloqueo y, si falla, puede borrar una copia preexistente. Un fallo al añadir imágenes en la automática deja el ZIP parcial bajo el patrón del listado.

**Evidencia:** `backend/app/backups.py:37–42,143–154,184–190,264–279`. Contrastar con HU-010, criterios de creación coherente y tratamiento de fallos. El listado no exige que haya terminado el escritor. No se indujo ningún fallo sobre almacenamiento real.

**Recomendación:** Unificar ambas rutas en un creador que escriba un temporal no listable y solo publique después de cerrar el ZIP, sin sobrescribir un destino existente. Resolver la colisión dentro del bloqueo, conservando el formato que aceptan descarga y restauración. Ante error, retirar solo el temporal propio.

**Criterios de aceptación:**
- [ ] Con reloj fijo, la segunda petición no altera la primera copia; un error simulado al añadir imágenes no deja otro ZIP listable y conserva las anteriores.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** Servicio de copias y pruebas de creación/listado. **Esfuerzo orientativo:** medio.  
**Huella:** `diseño|copias|publicacion-directa-sin-exclusion`.

### C04 · Una prueba puede aplicar la retención al directorio de copias configurado

Severidad: critica · Categoria: hallazgo critico · Area: Aislamiento de pruebas

**Descripción e impacto:** La prueba de programación usa SQLite temporal, pero solo simula el creador del ZIP. El código de retención sigue siendo real. Si el directorio configurado contiene más de tres copias coincidentes y es escribible, la prueba elimina las más antiguas. Aislar la base de datos no aísla el sistema de archivos.

**Evidencia:** `backend/tests/test_backups.py:220–236`: `maximum=3`, doble de `create_backup_archive`, llamada real a `run_scheduled_backup`. `backend/app/backups.py:26,186–188`: `BACKUP_ROOT` seguido de `obsolete.unlink()`. `docker-compose.yml:65` monta `./data:/app/data`. El caso contiguo de retención sí usa `tmp_path` (`backend/tests/test_backups.py:239–252`). No verificado: no se inspeccionó el almacenamiento de usuarios ni se ha comprobado pérdida de archivos.

**Recomendación:** Aislar `BACKUP_ROOT` en una fixture de `test_backups.py` aplicada antes de invocar el código. Dar a la prueba una raíz temporal propia y comprobar con directorios señuelo temporales que solo se inspecciona o modifica esa raíz. No repetirla sobre rutas operativas.

**Criterios de aceptación:**
- [ ] La prueba no depende de `APP_BACKUP_ROOT` del proceso; cuatro archivos de prueba fuera de la raíz aislada permanecen intactos.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** Pruebas de copias; sin cambios en producción. **Esfuerzo orientativo:** pequeño.  
**Huella:** `pruebas|programacion-copias|retencion-no-aislada`.

### C05 · Restaurar con una URL de PostgreSQL sin puerto construye `--port None`

Severidad: alta · Categoria: hallazgo critico · Area: Configuración y convenciones

**Descripción e impacto:** La configuración admite `DATABASE_URL`. Si contiene host pero omite puerto, el volcado usa 5432 y la restauración pasa la cadena `None` a `psql`. No depende del contenido de la copia. No se afirma que haya ocurrido en un despliegue.

**Evidencia:** `backend/app/database.py:13–17` acepta la URL explícita; `backend/app/backups.py:196–205` usa `parsed.port or 5432`, mientras `:211–222` usa `str(parsed.port if parsed else 5432)`. La prueba `backend/tests/test_backups.py:185–202` especifica `:5432` y simula `subprocess.run`. Verificación del argumento indicada abajo; no se ejecutó `psql`.

**Recomendación:** Compartir entre volcado y restauración la resolución de host y puerto; probar URLs con puerto omitido y explícito inspeccionando argumentos simulados, sin restaurar datos reales.

**Criterios de aceptación:**
- [ ] Sin puerto, ambos comandos pasan `5432` (o ambos delegan en el valor por defecto); con `:5433`, ambos conservan `5433`.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** Servicio de copias y prueba de argumentos. **Esfuerzo orientativo:** medio.  
**Huella:** `configuracion|restaurar-copia|puerto-omitido`.

### C06 · La prueba del endpoint de copia no comprueba el contenido que anuncia

Severidad: media · Categoria: observacion de test · Area: Calidad de pruebas

**Descripción e impacto:** El caso de la copia manual podría pasar aunque el ZIP no contuviera la imagen o el volcado: solo comprueba respuesta y existencia del archivo. La prueba del servicio sí abre el ZIP, pero prueba otra función; hoy el endpoint empaqueta por separado.

**Evidencia:** `backend/tests/test_backups.py:30–45`: crea `images/example.webp` directamente bajo `DATA_ROOT` y acaba en `archive.is_file()`. `backend/app/backups.py:157–167` solo acepta `comidas`, `productos`, `recetas`. Contraste: `backend/tests/test_backups.py:11–27` prueba `create_backup_archive`; el endpoint manual escribe en `backend/app/backups.py:268–275`.

**Recomendación:** Crear una imagen bajo `DATA_ROOT/comidas/`, abrir el ZIP devuelto por el POST y comparar nombres y bytes del volcado y la imagen; incluir un archivo fuera de alcance que no deba aparecer.

**Criterios de aceptación:**
- [ ] La prueba automatizada falla tanto si el endpoint omite la imagen como si omite `database.sql`.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** `backend/tests/test_backups.py`. **Esfuerzo orientativo:** pequeño.  
**Huella:** `pruebas|copia-manual|zip-no-inspeccionado`.

### C07 · El listado de compra vuelve a recorrer ingredientes y resolver imágenes

Severidad: media · Categoria: riesgo de eficiencia · Area: Rendimiento y eficiencia

**Descripción e impacto:** Por cada sección se recorren todos los ingredientes, aunque ya vienen ordenados. Además, si existe imagen, se resuelve dos veces para la misma fila; resolver la de un ingrediente recorre el catálogo. Es trabajo adicional en cada consulta de la lista compartida, sin necesidad de asumir un volumen o una latencia.

**Evidencia:** `backend/app/shopping_list_api.py:104–109,128–139,185–195`; `backend/app/ingredient_images.py:14–24`. Con S secciones e I ingredientes se hacen S×I comparaciones de pertenencia; la expresión condicional de `image_url` invoca de nuevo al mismo resolutor cuando devuelve un valor. No se midió tiempo ni se asume que cada `db.get` haga una consulta.

**Recomendación:** Agrupar los ingredientes en una pasada por `section_id` manteniendo el orden; calcular cada URL una vez y reutilizarla. Comprobar número de invocaciones con dobles y comparar la respuesta con y sin imagen.

**Criterios de aceptación:**
- [ ] Cada ingrediente se asigna una sola vez, cada resolutor se llama como máximo una vez por elemento y no cambia el orden ni el contrato JSON.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** Listado y pruebas de secciones e imágenes. **Esfuerzo orientativo:** medio.  
**Huella:** `eficiencia|lista-compra|recorridos-por-seccion`.

### C08 · Las pruebas de instalación repiten tres veces la misma compilación

Severidad: media · Categoria: riesgo de eficiencia · Area: Rendimiento de pruebas

**Descripción e impacto:** Los tres casos leen una salida de producción idéntica y no cambian ninguna entrada. Cada uno invoca de nuevo TypeScript y Vite. Así, incluso ejecutar la suite unitaria completa escribe artefactos y no es posible correr esos casos bajo la restricción de esta auditoría.

**Evidencia:** `frontend/src/instalacion.test.js:7–10,16–19,32–35`: tres `execFileSync("npm", ["run", "build"])`. `frontend/package.json` define `build` como `tsc -b && vite build`. Tres invocaciones observadas en el código, no una estimación temporal.

**Recomendación:** Separar la comprobación del paquete de la suite sin build, con un comando documentado que compile una sola vez antes de los tres casos y compruebe artefactos de esa ejecución, no de un `dist/` anterior.

**Criterios de aceptación:**
- [ ] La comprobación de instalación valida los tres contratos con un solo build en un checkout limpio; el comando unitario no escribe `dist/`.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** Pruebas de instalación, scripts del frontend y COMMANDS.md. **Esfuerzo orientativo:** medio.  
**Huella:** `eficiencia|pruebas-instalacion|build-repetido`.

### C09 · Previsualizar y guardar vuelven a decidir por separado qué cambia

Severidad: media · Categoria: deuda tecnica acumulada · Area: Complejidad y duplicación

**Descripción e impacto:** La previsualización y la aplicación clasifican las mismas fechas y reglas de sustitución, borrado y recordatorio en dos recorridos. Una ampliación de HU-002 o de los recordatorios tiene que mantener ambos caminos alineados para que el usuario confirme exactamente lo que se guarda. No se afirma que actualmente discrepen.

**Evidencia:** `backend/app/meal_planning_api.py:226–315,598–682`: 90 y 85 líneas; estimación AST de complejidad 17 y 18, anidamiento 5 y 5. Comparar `:247–269` con `:636–666`; el guardado llama primero a `build_preview` (`:608`) y después vuelve a decidir.

**Recomendación:** Extraer una decisión por fecha que reciba estado actual y operación; usar su resultado para representar la previsualización y para aplicar el cambio. Mantener cálculo y comprobación del token dentro del flujo actual de bloqueo.

**Criterios de aceptación:**
- [ ] Pruebas parametrizadas comprueban que altas, reemplazos, cambios de aviso, borrados y operaciones sin cambios producen las mismas fechas en vista previa y confirmación; se conserva el conflicto de token.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** Planificación backend y pruebas de operaciones. **Esfuerzo orientativo:** medio.  
**Huella:** `complejidad|planificacion|decisiones-duplicadas-por-fecha`.

### C10 · El editor y la navegación semanal comparten un solo componente

Severidad: media · Categoria: deuda tecnica acumulada · Area: Responsabilidad única y tamaño

**Descripción e impacto:** El componente `MealPlanning` controla a la vez el desplazamiento, la carga de semanas y el ciclo de edición, previsualización y confirmación. Probar cambios de recordatorio obliga a montar también la infraestructura del calendario.

**Evidencia:** `frontend/src/MealPlanning.tsx:64–774` (711 líneas inclusivas); `:210–364` observadores y carga, `:430–580` editor, `:582–773` presentación. `frontend/src/MealPlanning.reminder.test.tsx:10–20` prepara API, media queries, ResizeObserver y fuentes para probar el editor.

**Recomendación:** Separar la sección de edición y su estado de borrador/confirmación de la navegación semanal. Inyectar operación y eventos por una interfaz interna; conservar una prueba de integración con el calendario y probar la edición sin observadores.

**Criterios de aceptación:**
- [ ] Un caso de conflicto de previsualización puede probarse sin montar el desplazamiento semanal; siguen pasando los casos de navegación y reapertura.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** Componente de planificación y pruebas React. **Esfuerzo orientativo:** medio.  
**Huella:** `diseño|MealPlanning|editor-acoplado-al-calendario`.

### C11 · El índice remite a fuentes Markdown que no se distribuyen

Severidad: baja · Categoria: inconsistencia documental · Area: Documentación técnica

**Descripción e impacto:** En un checkout del commit, quien consulte el índice buscará fuentes de roles que no existen allí.

**Evidencia:** `INDEX.md:14` anuncia «sus fuentes Markdown de Claude conservadas»; `git ls-tree -r --name-only a0a9249 .codex/agents` devuelve siete TOML y ningún `.md`. La comprobación se refiere al commit, no a archivos privados.

**Recomendación:** Corregir la entrada para describir los siete TOML versionados; no importar fuentes externas para satisfacer el texto.

**Criterios de aceptación:**
- [ ] Cada formato y ubicación mencionados en esa entrada existen en el árbol del commit.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** `INDEX.md`. **Esfuerzo orientativo:** pequeño.  
**Huella:** `documentacion|INDEX.md|fuentes-markdown-ausentes`.

### C12 · La arquitectura inicial no distingue su fotografía histórica del mecanismo actual de copias

Severidad: media · Categoria: inconsistencia documental · Area: Documentación técnica

**Descripción e impacto:** El documento avisa de que es inicial, pero concluye en presente que el mecanismo de copias sigue sin definirse. Quien lo use como punto de entrada no encontrará la implementación ni distinguirá estado técnico de aceptación de una historia.

**Evidencia:** `docs/arquitectura.md:30–34` contrasta con `backend/app/backups.py:78–89,143–167,260–279` y con HU-010 en `docs/historias-usuarios/HIT-002-copias-de-seguridad/`. El propio perfil pide contrastar la arquitectura histórica.

**Recomendación:** Fechar o delimitar el apartado histórico y enlazar desde él las rutas y el documento vigente de copias. No cambiar estados de historias ni declarar verificado un despliegue.

**Criterios de aceptación:**
- [ ] El lector distingue el alcance inicial de la implementación actual y encuentra la descripción de las copias sin inferir que ya están validadas en producción.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** `docs/arquitectura.md`. **Esfuerzo orientativo:** pequeño.  
**Huella:** `documentacion|arquitectura|copias-descritas-como-indefinidas`.

### C13 · La cabecera del módulo de compra describe una lista por usuario

Severidad: baja · Categoria: inconsistencia documental · Area: Nomenclatura y vocabulario de dominio

**Descripción e impacto:** La frase «a user's shopping-list items» sugiere propiedad individual donde el perfil exige una única lista compartida. No se considera defecto la mera presencia de identificadores en inglés.

**Evidencia:** `backend/app/shopping_list_api.py:1,98–106,213–219` y `backend/tests/test_shopping_list_api.py:1112` (lectura por otro usuario). `docs/project/PERFIL.md`, «Modelo de dominio», dice expresamente que la lista es compartida.

**Recomendación:** Describir en español la lista familiar compartida en el docstring de módulo; no añadir un filtro por usuario ni renombrar el contrato HTTP.

**Criterios de aceptación:**
- [ ] La descripción coincide con el perfil y sigue pasando la prueba de lectura compartida.
- [ ] Las pruebas relacionadas siguen pasando sin cambiar otros contratos.

**Alcance del cambio:** `backend/app/shopping_list_api.py`, solo documentación interna. **Esfuerzo orientativo:** pequeño.  
**Huella:** `nomenclatura|lista-compra|propiedad-individual-en-docstring`.

## Pruebas y cobertura

| Suite | Comando ejecutado | Resultado de esta auditoría |
| --- | --- | --- |
| Backend, desde `backend/`, fuera del sandbox | `RUN_DB_INTEGRATION=0 PYTHONDONTWRITEBYTECODE=1 ../.venv/bin/python -m pytest -q -p no:cacheprovider` | 261 pasaron; 15 omitidas por requerir PostgreSQL nuevo y aislado. Sin reejecución tras identificar C04. |
| Frontend, desde `frontend/` | `npm test -- --no-cache --configLoader runner --exclude '**/instalacion.test.js'` | 249 pasaron en 28 archivos. Los 3 casos de instalación quedaron fuera deliberadamente: cada uno ejecuta un build (C08). No se informa la suite completa como aprobada. |
| Lanzador, desde la raíz | `python3 -B -m unittest discover -s scripts/tests -v` | 11 pasaron con ejecutables simulados y directorios temporales. |
| **Total identificado** | **539 casos** | **521 pasaron, 0 fallaron, 15 omitidos por el ejecutor y 3 no lanzados.** |

**Cobertura global y por archivo: no medida** (no equivale ni a 0 % ni a 100 %). En el entorno virtual del proyecto no están `coverage` ni `pytest_cov`; en el frontend no se encontró el proveedor de cobertura de Vitest bajo `node_modules/@vitest/`. No se instalaron herramientas, generaron informes en disco ni se infirió cobertura de los nombres de tests.

**Archivos de la aplicación sin medición**, agrupados por directorio:
- `backend/app/`: `auth.py`, `backups.py`, `database.py`, `food_images.py`, `ingredient_images.py`, `kitchen_tips_api.py`, `mailer.py`, `main.py`, `meal_planning.py`, `meal_planning_api.py`, `models.py`, `notificaciones_push.py`, `recipes_api.py`, `safe_image_url.py`, `security.py`, `settings.py`, `shopping_catalog_api.py`, `shopping_list_api.py`.
- `frontend/src/`: `App.tsx`, `AppBrand.tsx`, `AppIcon.tsx`, `AppWorkspace.tsx`, `Backups.tsx`, `CalendarDay.tsx`, `DialogoCantidadCompra.tsx`, `DialogoEditarCompra.tsx`, `FoodCatalog.tsx`, `ImagenCatalogo.tsx`, `KitchenTips.tsx`, `MealPlanning.tsx`, `ProductCatalog.tsx`, `Recipes.tsx`, `SelectorCompra.tsx`, `ShoppingList.tsx`, `ToastMessage.tsx`, `api.ts`, `appViewPersistence.ts`, `main.tsx`, `mealPlanningApi.ts`, `mealPlanningDates.ts`.
- `frontend/src/ui/`: `Button.tsx`, `Field.tsx`, `Message.tsx`, `Panel.tsx`, `index.ts`.
- `frontend/public/`: `notificaciones-worker.js`.
- Tampoco se instrumentaron migraciones, utilidades de desarrollo, scripts, configuración, pruebas ni biblioteca de vistas previas. No es posible distinguir por cobertura qué módulos se importaron.

## Métricas estructurales

Se inventariaron **138 archivos** versionados con extensiones `.py`, `.sh`, `.ts`, `.tsx`, `.js`, `.jsx` y `.css` (incluye pruebas). Líneas físicas, incluidos comentarios y líneas vacías; **11 archivos >400 líneas**:

- `backend/app/auth.py`: 1098.
- `backend/app/meal_planning_api.py`: 682.
- `backend/tests/test_auth.py`: 731.
- `backend/tests/test_database_integration.py`: 1220.
- `backend/tests/test_meal_planning.py`: 881.
- `backend/tests/test_shopping_list_api.py`: 1402.
- `frontend/src/App.css`: 838.
- `frontend/src/App.tsx`: 628.
- `frontend/src/MealPlanning.tsx`: 806.
- `frontend/src/ShoppingList.integration.test.tsx`: 1262.
- `frontend/src/ShoppingList.tsx`: 502.

**Funciones:** análisis estático con `ast` de Python y el compilador TypeScript ya instalado, sin ejecutar la aplicación. 623 definiciones Python (sin lambdas) y 1355 funciones/métodos/callbacks JS/TS con cuerpo. Se contaron también fixtures y callbacks de prueba, no funciones shell. Longitud inclusiva desde la declaración hasta su final (sin decoradores previos de Python, incluye funciones interiores en el intervalo). Resultado sobre ese corpus:

| Señal | Número de funciones |
| --- | ---: |
| Más de 50 líneas | 42 |
| Complejidad estimada >10 | 54 |
| Más de cuatro parámetros | 29 |
| Más de tres niveles de decisión anidados | 10 |

Complejidad estimada por árbol, no por un analizador normalizado: base 1 + bifurcaciones, bucles, manejadores de excepción, casos, expresiones condicionales y operadores booleanos/de coalescencia; en Python también iteradores y filtros de comprensiones. Se excluyeron las decisiones de funciones internas al medir la externa. El anidamiento cuenta decisiones, no bloques de contexto; un `elif` anidado en el árbol puede aumentar la profundidad. No se midió porcentaje global de duplicación: las repeticiones se contrastaron directamente en las ubicaciones citadas.

**Funciones >50 líneas**: nombre y línea inicial, seguidos de longitud; `λ` indica callback anónimo. Los grupos `describe` pueden abarcar varios tests: esa longitud no equivale a una sola prueba compleja.

| Archivo | Declaraciones |
| --- | --- |
| `backend/app/auth.py` | `get_active_session:193` (56); `login:577` (61); `update_user:817` (74); `request_password_reset:979` (63); `confirm_password_reset:1045` (54) |
| `backend/app/meal_planning_api.py` | `build_preview:226` (90); `apply_meal_planning_operation:598` (85) |
| `backend/app/safe_image_url.py` | `safe_fetch_image:97` (88) |
| `backend/app/shopping_list_api.py` | `add_shopping_list_item:39` (57) |
| `backend/migrations/versions/0002_user_auth_persistence.py` | `upgrade:18` (76) |
| `backend/tests/test_database_integration.py` | `test_auth_schema_and_concurrent_email_uniqueness:83` (53); `test_meal_planning_migration_seeds_exact_default_catalog:142` (56); `test_concurrent_deactivation_never_removes_all_active_accounts:301` (76); `test_password_reset_limits_are_atomic_per_account_and_ip:383` (58); `test_password_reset_token_can_be_consumed_only_once_concurrently:447` (59); `test_concurrent_assignments_to_initially_empty_slot_require_fresh_confirmation:775` (59); `test_concurrent_assign_and_exact_delete_never_removes_replacement:840` (67); `test_concurrent_overlapping_repeats_serialize_and_last_confirmed_batch_wins:913` (80); `test_postgresql_repeated_operation_rolls_back_all_rows_on_mid_batch_failure:1053` (65); `test_postgresql_repeated_delete_removes_all_occupied_occurrences:1124` (55) |
| `backend/tests/test_meal_planning.py` | `test_meal_planning_range_is_inclusive_and_reports_canary_date:178` (53); `test_assignment_repeat_replaces_only_after_confirming_current_preview:303` (51) |
| `backend/tests/test_shopping_list_api.py` | `test_marking_item_keeps_incompatible_units_separate:1024` (52) |
| `frontend/src/api.test.ts` | `λ:9` (63) |
| `frontend/src/App.tsx` | `App:29` (408); `UserCard:480` (149) |
| `frontend/src/AppWorkspace.test.tsx` | `λ:19` (121) |
| `frontend/src/AppWorkspace.tsx` | `AppWorkspace:33` (73) |
| `frontend/src/Backups.tsx` | `Backups:36` (89) |
| `frontend/src/CalendarDay.test.tsx` | `λ:14` (71) |
| `frontend/src/DialogoCantidadCompra.tsx` | `DialogoCantidadCompra:11` (54) |
| `frontend/src/FoodCatalog.tsx` | `FoodCatalog:22` (114) |
| `frontend/src/ImagenCatalogo.tsx` | `ImagenCatalogo:15` (61) |
| `frontend/src/KitchenTips.test.tsx` | `λ:14` (172) |
| `frontend/src/KitchenTips.tsx` | `KitchenTips:9` (145) |
| `frontend/src/MealPlanning.tsx` | `MealPlanning:64` (711) |
| `frontend/src/mealPlanningApi.test.ts` | `λ:21` (196) |
| `frontend/src/ProductCatalog.tsx` | `ProductCatalog:50` (189) |
| `frontend/src/SelectorCompra.tsx` | `SelectorCompra:17` (55) |
| `frontend/src/ShoppingList.integration.test.tsx` | `λ:35` (1228) |
| `frontend/src/ShoppingList.test.tsx` | `λ:25` (156) |
| `frontend/src/ShoppingList.tsx` | `ShoppingList:60` (443) |

**Marcadores:** búsqueda sensible a mayúsculas por palabra completa en el corpus anterior: TODO **0**, FIXME **0**, HACK **0**. No incluye el español «todo» en mensajes o pruebas. Para repetir: `git grep -nE '\b(TODO|FIXME|HACK)\b' a0a9249 -- '*.py' '*.sh' '*.ts' '*.tsx' '*.js' '*.jsx' '*.css'` (sin coincidencias).

**Reproducción sin servicios:** las ubicaciones se pueden consultar con `git show a0a9249:ruta | nl -ba`. Para C02 y C05, desde la raíz, se comprobaron las operaciones con los mismos tipos que usa la aplicación:

```bash
.venv/bin/python -B -c 'from decimal import Decimal, ROUND_HALF_UP; from sqlalchemy.engine import make_url; print(Decimal("0.1").quantize(Decimal("1"), rounding=ROUND_HALF_UP)); p=make_url("postgresql+psycopg://localhost/db"); print(repr(str(p.port if p else 5432)),p.port or 5432)'
# Salida: 0
#         'None' 5432
```

## Límites y seguimiento

- **A revisar:** `backend/app/meal_planning_api.py:559–583` comunica `recipients` según el número de correos aunque también envía push. No se encontró evidencia de si el contrato cuenta personas únicas, correos o entregas por canal; no se propone una corrección sin aclararlo. Los efectos reales de carga en C07 y cualquier impacto histórico de C01, C03 o C04 no se verificaron.
- **Para security-auditor:** el [informe de seguridad previo](2026-11-27-seguridad-aplicacion.md) ya trata el corte parcial de una restauración. C03 es distinto: trata de la **creación** y publicación de una copia. No se repitieron pruebas de seguridad ni se abrieron hallazgos de ese ámbito.
- **Herramientas propuestas:** si se aprueba incorporarlas, usar coverage.py y el proveedor V8 compatible con Vitest en un entorno desechable. Permitirían medir líneas por archivo; implican dependencias adicionales y no sustituyen las aserciones sobre los datos de C04 y C06.
