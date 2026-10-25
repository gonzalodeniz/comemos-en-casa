# HU-002 — Planificación de comidas

**Producto:** Comemos en casa  
**Épica:** Planificación de comidas  
**Prioridad:** Alta  
**Estado:** Implementación completada; verificación local T1–T10 completada. No implica publicación.
**Módulo:** Planificación semanal y mensual

**Estado de verificación (2026-10-25):** funcionalidad implementada y T1–T10 verificadas localmente. Los 22 escenarios se recorrieron en Chrome contra FastAPI real con SQLite temporal; en una ejecución limpia separada también se verificaron bootstrap, registro sin auto-login, login explícito y logout sin usuarios/sesiones sembrados. La suite `make test` pasó fuera de sandbox autorizado (61 backend/15 frontend); los timeouts previos de sandbox y su comparación posterior se registran en TASKS, sin atribuir causa al producto. No se ejecutó navegador contra PostgreSQL ni se probó la URL desplegada. La matriz y las limitaciones observadas están en el [TASKS de HU-002](../../odd/tasks/hu-002-planificacion-de-comidas.md#evidencia-de-t10-y-cobertura-de-escenarios). La evidencia de interfaz simulada, SQLite y PostgreSQL se mantiene diferenciada.

## 1. Historia de usuario

**Como** miembro de la familia autenticado,  
**quiero** consultar la planificación de almuerzos y cenas por semanas o por meses, asignar una etiqueta alimentaria a cada franja y repetir operaciones cada cierto número de semanas,  
**para** organizar las comidas familiares con antelación y modificar cada día de forma independiente cuando sea necesario.

## 2. Objetivo

Facilitar la organización compartida de las comidas familiares mediante una vista semanal de lunes a domingo y una vista mensual. Cada día distingue **almuerzo** y **cena**, y cada franja puede contener como máximo una **etiqueta alimentaria**.

Al asignar, sustituir o eliminar una etiqueta, el usuario puede aplicar la operación únicamente a la fecha seleccionada o repetirla cada cierto número de semanas hasta una fecha final elegida por el usuario, dentro del límite anual definido en RN-09. La fecha final se incluye si coincide con una repetición calculada; no se añade una asignación fuera del intervalo semanal. Se permite consultar y modificar fechas pasadas. Las asignaciones generadas mediante repetición se guardan como copias individuales e independientes, no como ocurrencias vinculadas a una serie permanente.

## 3. Glosario específico

- **Planificación de comidas:** conjunto de asignaciones de etiquetas alimentarias a almuerzos y cenas de fechas concretas.
- **Franja de comida:** uno de los dos espacios planificables en una fecha: **almuerzo** o **cena**.
- **Asignación:** relación entre una fecha, una franja de comida y, como máximo, una etiqueta alimentaria.
- **Etiqueta alimentaria:** término que identifica un alimento concreto, un tipo de alimento o un grupo de alimentos y sirve para clasificar recetas y planificar comidas.
- **Repetición de una operación:** aplicación de una asignación, sustitución o eliminación en fechas separadas por un intervalo entero de semanas, desde la fecha inicial hasta una fecha final elegida, dentro del límite anual.
- **Fecha final:** límite inclusivo elegido por el usuario; solo se aplica la operación ese día si coincide con una de las fechas calculadas por el intervalo semanal.
- **Fecha final máxima:** día anterior a la misma fecha del año siguiente; si el inicio es el 29 de febrero, es el 28 de febrero del año siguiente, incluido.
- **Intervalo de repetición:** número entero positivo de semanas entre las fechas afectadas por una operación repetida (1, 2, 3, 4, etc.).
- **Copia individual:** asignación concreta creada por una repetición que, una vez guardada, puede modificarse o eliminarse sin afectar a las demás copias.

## 4. Criterios de aceptación

### CA-01 — Vista semanal

1. El sistema muestra la semana completa, **de lunes a domingo**, en orden cronológico.
2. Para cada día se muestran dos espacios diferenciados: **almuerzo** y **cena**.
3. En cada espacio se muestra la etiqueta alimentaria asignada; si no hay ninguna, se indica que está sin planificar.
4. Por defecto se muestra la semana que contiene la fecha actual según la zona horaria IANA `Atlantic/Canary`.
5. Se identifica claramente el intervalo de fechas de la semana; si cruza un mes o un año, las fechas siguen siendo inequívocas.

### CA-02 — Navegación entre semanas

1. Existe una acción para consultar la **semana anterior** y otra para la **semana siguiente**.
2. Cada navegación desplaza exactamente siete días el intervalo visible, manteniendo el comienzo en lunes.
3. Las etiquetas mostradas corresponden al nuevo intervalo.
4. La navegación permite atravesar los límites de mes y año.

### CA-03 — Vista mensual

1. El usuario puede alternar entre vista semanal y **vista mensual**.
2. La vista mensual muestra los días del mes seleccionado con sus almuerzos y cenas planificados.
3. En la vista mensual se distinguen las asignaciones de almuerzo y cena.
4. Se puede avanzar al **mes siguiente** o retroceder al **mes anterior**.
5. El calendario utiliza el lunes como primer día de la semana.
6. Al cambiar de vista se conserva la fecha de referencia seleccionada.
7. Los datos visibles de una misma fecha son coherentes en ambas vistas.

### CA-04 — Asignar una etiqueta alimentaria

1. Un usuario autenticado puede seleccionar una fecha y una franja de comida y asignarle una etiqueta alimentaria existente.
2. Cada almuerzo o cena puede contener **como máximo una etiqueta**.
3. Si la franja está vacía, la etiqueta se añade como una nueva asignación.
4. Si la franja ya contiene una etiqueta, el sistema informa de que será sustituida y solicita confirmación antes de guardar.
5. La etiqueta se muestra en la planificación una vez guardada.
6. El sistema valida que la fecha, la franja y la etiqueta seleccionada sean válidas.
7. La selección procede del [catálogo de etiquetas predeterminadas](../etiquetas-predeterminadas.md). La creación y edición de etiquetas por parte del usuario se abordará más adelante.
8. Se permite seleccionar y modificar fechas pasadas, tanto de forma individual como mediante repetición.

### CA-05 — Repetir una asignación o sustitución

1. Al asignar o sustituir una etiqueta, se ofrece la opción **«Repetir cada N semanas»**, desactivada por defecto.
2. Si se activa, el usuario elige un intervalo de repetición expresado en semanas: **cada 1, 2, 3, 4, ... semanas**.
3. Solo se admiten intervalos enteros positivos.
4. La repetición conserva la misma franja de comida y el mismo día de la semana de la fecha inicial.
5. La primera asignación se realiza en la fecha seleccionada y las siguientes se calculan sumando el intervalo indicado en semanas.
6. El usuario elige una fecha final comprendida entre la fecha inicial y la fecha final máxima de RN-09, ambas incluidas. Puede elegir un final anterior al máximo. Si el final coincide con una repetición calculada, se incluye; si no coincide, no se añade una operación en esa fecha. Un final igual al inicio es válido y afecta solo a la fecha inicial. Se rechazan finales anteriores al inicio o posteriores al máximo anual.
7. En cada fecha coincidente, la nueva etiqueta sustituye cualquier etiqueta que ya exista en esa franja.
8. Antes de guardar, el sistema informa de que las etiquetas existentes en las fechas coincidentes serán sustituidas.
9. Todas las asignaciones resultantes se guardan como copias individuales e independientes.
10. Modificar o eliminar posteriormente una de las copias no altera las demás.
11. Si no se activa la repetición, la operación afecta exclusivamente a la fecha seleccionada.
12. Se permiten fechas iniciales pasadas; el límite anual se calcula desde la fecha inicial seleccionada, no desde la fecha actual.
13. Cancelar la confirmación no guarda asignaciones ni sustituciones.

### CA-06 — Sustituir una etiqueta individual

1. El usuario puede sustituir la etiqueta de un almuerzo o una cena por otra etiqueta existente.
2. La sustitución afecta únicamente a la fecha y franja seleccionadas, salvo que el usuario active expresamente una nueva repetición.
3. Sustituir una copia creada mediante una repetición no modifica ninguna otra copia anterior o posterior.
4. Los cambios guardados aparecen inmediatamente en las vistas semanal y mensual.

### CA-07 — Eliminar una etiqueta individual

1. El usuario puede eliminar la etiqueta asignada a una fecha y franja.
2. La eliminación afecta únicamente a la asignación seleccionada, salvo que el usuario active expresamente la repetición del borrado.
3. El sistema solicita confirmación antes de eliminarla.
4. Tras eliminarla, la franja queda sin planificar.
5. Si el usuario cancela la confirmación, la asignación permanece sin cambios.

### CA-08 — Repetir la eliminación de una etiqueta

1. Al eliminar una etiqueta, se ofrece la opción **«Repetir cada N semanas»**, desactivada por defecto.
2. Si se activa, el usuario elige un intervalo entero positivo de semanas.
3. La operación parte de la fecha seleccionada y revisa las fechas coincidentes con el mismo día de la semana y la misma franja.
4. El usuario elige una fecha final entre el inicio y el máximo anual de RN-09, ambos incluidos. Rigen las mismas reglas de CA-05: final inclusivo solo si coincide con una repetición, inicio igual a final válido, rechazo de finales anteriores al inicio o superiores al máximo, y cálculo desde el inicio aunque esté en el pasado.
5. En cada fecha coincidente se elimina la asignación solo si contiene exactamente la misma etiqueta que se está borrando en la fecha inicial.
6. Si una fecha coincidente está vacía o contiene otra etiqueta, no se modifica.
7. Antes de guardar, el sistema informa del intervalo y de las asignaciones que serán eliminadas.
8. El borrado repetido actúa sobre las asignaciones existentes en el momento de la operación y no crea una regla que afecte a asignaciones añadidas posteriormente.
9. Cancelar la confirmación no elimina ninguna asignación.

### CA-09 — Independencia de las asignaciones copiadas

1. Cada etiqueta creada mediante una repetición se almacena como una asignación individual.
2. Las copias no permanecen vinculadas a una serie después de guardarse.
3. Una modificación o eliminación posterior de una copia no se propaga automáticamente a las demás.
4. Para aplicar una nueva operación repetida, el usuario debe activarla expresamente al asignar, sustituir o eliminar una etiqueta.
5. Consultar reiteradamente la planificación no crea asignaciones nuevas ni duplica las existentes.

### CA-10 — Acceso y colaboración familiar

1. Solo los usuarios autenticados y activos pueden consultar o gestionar la planificación.
2. Todos los usuarios activos pueden consultar, asignar, sustituir y eliminar etiquetas, sin distinción de roles.
3. La planificación es **compartida**: los cambios guardados por un usuario son visibles para los demás al actualizar o volver a consultar la vista.
4. Si dos usuarios modifican simultáneamente la misma fecha y franja, prevalece la última operación que el servidor guarde correctamente.

## 5. Reglas de negocio

**RN-01.** La planificación es única y compartida por los miembros de la familia que tengan una cuenta activa.

**RN-02.** La semana comienza el lunes y termina el domingo.

**RN-03.** Cada fecha tiene dos franjas planificables: almuerzo y cena.

**RN-04.** Cada franja puede contener cero o una etiqueta alimentaria.

**RN-05.** Una asignación hace referencia a una etiqueta alimentaria existente; no implica la elección de una receta concreta.

**RN-06.** Asignar una etiqueta a una franja ocupada sustituye la etiqueta anterior después de la confirmación del usuario.

**RN-07.** El intervalo de repetición es un entero positivo expresado en semanas.

**RN-08.** Una operación repetida conserva el día de la semana y la franja de la fecha inicial.

**RN-09.** El usuario elige una fecha final entre la fecha inicial y la fecha final máxima, ambas incluidas. Para un inicio distinto del 29 de febrero, la fecha final máxima es el día anterior a la misma fecha del año siguiente; esa fecha equivalente queda excluida. Para un inicio el 29 de febrero, la fecha final máxima es el 28 de febrero del año siguiente, incluido. El final elegido se incluye únicamente si coincide con una fecha calculada por el intervalo semanal; no genera una ocurrencia adicional fuera de ese intervalo. Inicio y final iguales son válidos; se rechaza un final anterior al inicio o superior al máximo.

**RN-10.** Las asignaciones producidas mediante una repetición son copias individuales e independientes.

**RN-11.** Una asignación o sustitución repetida reemplaza cualquier etiqueta existente en las fechas y franjas coincidentes.

**RN-12.** Una eliminación repetida solo borra asignaciones cuya etiqueta coincida exactamente con la etiqueta seleccionada inicialmente.

**RN-13.** Una eliminación repetida no constituye una regla permanente y no afecta a asignaciones creadas después de ejecutarla.

**RN-14.** Los cambios deben persistir y ser compartidos entre todos los usuarios autorizados.

**RN-15.** La fecha de la planificación se interpreta según la zona horaria **Atlantic/Canary**, evitando cambios de día inesperados por conversiones horarias.

**RN-16.** Se permite consultar y modificar fechas pasadas. Una repetición puede comenzar en el pasado y su máximo anual se calcula desde la fecha seleccionada, no desde hoy.

**RN-17.** Cancelar una confirmación de sustitución o eliminación, individual o repetida, no modifica la planificación.

## 6. Escenarios de prueba

### Escenario 1 — Visualizar la semana actual

**Dado** que un usuario activo ha iniciado sesión,  
**cuando** abre la planificación,  
**entonces** ve de lunes a domingo la semana actual, con almuerzo y cena de cada fecha.

### Escenario 2 — Navegar a otras semanas

**Dado** que el usuario está viendo una semana,  
**cuando** pulsa «Semana siguiente» y después «Semana anterior»,  
**entonces** regresa al mismo intervalo inicial de lunes a domingo.

### Escenario 3 — Consultar el mes

**Dado** que el usuario está en la vista semanal,  
**cuando** cambia a la vista mensual,  
**entonces** ve la planificación de los días del mes de referencia, distinguiendo almuerzos y cenas.

### Escenario 4 — Añadir una etiqueta sin repetición

**Dado** que un almuerzo está sin planificar,  
**cuando** el usuario añade «Garbanzos» sin repetición,  
**entonces** la etiqueta aparece exclusivamente en el almuerzo de la fecha seleccionada.

### Escenario 5 — Sustituir una etiqueta

**Dado** que una cena contiene «Pescado»,  
**cuando** el usuario la sustituye por «Sardinas» y confirma la operación,  
**entonces** la cena muestra únicamente «Sardinas».

### Escenario 6 — Repetición cada semana

**Dado** que el usuario añade «Carne» al almuerzo de un lunes,  
**cuando** configura la repetición cada 1 semana y elige una fecha final válida,\
**entonces** se crean copias individuales de «Carne» en los almuerzos de los lunes desde el inicio hasta el final elegido, incluido si coincide, sin superar el máximo anual de RN-09.

### Escenario 7 — Repetición cada tres semanas

**Dado** que el usuario añade «Sardinas» a una cena de viernes,  
**cuando** configura la repetición cada 3 semanas y elige una fecha final válida,\
**entonces** se crean copias individuales en el viernes inicial y en los viernes separados por intervalos de 21 días hasta el final elegido, sin añadir fechas fuera del intervalo ni superar el máximo anual de RN-09.

### Escenario 8 — Sustitución repetida

**Dado** que varios almuerzos de lunes contienen etiquetas diferentes,  
**cuando** el usuario asigna «Legumbres» a uno de ellos y repite la operación cada semana,  
**entonces** «Legumbres» sustituye las etiquetas existentes en los almuerzos de los lunes coincidentes durante el período de repetición.

### Escenario 9 — Modificar una copia individual

**Dado** que una repetición creó «Garbanzos» en varios almuerzos,  
**cuando** el usuario sustituye una de esas copias por «Lentejas» sin activar otra repetición,  
**entonces** únicamente la fecha seleccionada cambia a «Lentejas».

### Escenario 10 — Eliminar una copia individual

**Dado** que una repetición creó «Sardinas» en varias cenas,  
**cuando** el usuario elimina una de esas copias sin activar la repetición del borrado,  
**entonces** únicamente esa cena queda sin planificar.

### Escenario 11 — Repetir el borrado de la misma etiqueta

**Dado** que varios almuerzos coincidentes contienen «Carne»,  
**cuando** el usuario elimina «Carne» y repite el borrado cada dos semanas,  
**entonces** se elimina «Carne» de los almuerzos coincidentes hasta la fecha final elegida, incluida si coincide, dentro del máximo anual de RN-09.

### Escenario 12 — No borrar una etiqueta diferente

**Dado** que el usuario repite el borrado de «Carne» y una fecha coincidente contiene «Pescado»,  
**cuando** se ejecuta la operación,  
**entonces** «Pescado» permanece sin cambios.

### Escenario 13 — No aplicar el borrado a cambios futuros

**Dado** que se ha ejecutado un borrado repetido de «Carne»,  
**cuando** posteriormente un usuario asigna «Carne» a una de las fechas revisadas,  
**entonces** la nueva asignación permanece porque el borrado no constituye una regla permanente.

### Escenario 14 — Compartir la planificación

**Dado** que dos usuarios activos consultan la planificación familiar,  
**cuando** uno asigna una etiqueta y el otro vuelve a consultar la planificación,  
**entonces** el segundo ve el cambio guardado.

### Escenario 15 — Impedir acceso sin sesión

**Dado** que un visitante no ha iniciado sesión,  
**cuando** intenta acceder a la planificación,  
**entonces** el sistema le solicita autenticarse.

### Escenario 16 — Incluir una fecha final coincidente

**Dado** un inicio el lunes 2 de noviembre de 2026 y un intervalo de una semana,\
**cuando** el usuario elige como final el lunes 30 de noviembre de 2026,\
**entonces** las fechas son 2, 9, 16, 23 y 30 de noviembre.

### Escenario 17 — No añadir una fecha final fuera del intervalo

**Dado** el mismo inicio e intervalo del escenario 16,\
**cuando** el usuario elige como final el domingo 29 de noviembre de 2026,\
**entonces** la última fecha afectada es el lunes 23 y no se añade una operación el día 29.

### Escenario 18 — Inicio y final iguales

**Dado** que el usuario activa la repetición con un intervalo entero positivo,\
**cuando** elige la misma fecha como inicio y final,\
**entonces** la operación es válida y afecta únicamente a la fecha inicial.

### Escenario 19 — Rechazar fechas finales no válidas

**Dado** un inicio el 2 de noviembre de 2026, cuya fecha final máxima es el 1 de noviembre de 2027,\
**cuando** el usuario introduce un final anterior al inicio o posterior a ese máximo,\
**entonces** se rechaza la operación sin modificar ninguna asignación.

### Escenario 20 — Límite para un inicio el 29 de febrero

**Dado** un inicio el 29 de febrero de 2028,\
**cuando** se valida la fecha final de la repetición,\
**entonces** se acepta como máximo el 28 de febrero de 2029, incluido como límite, y se rechaza el 1 de marzo de 2029; solo se aplican operaciones en fechas que coincidan con el intervalo semanal.

### Escenario 21 — Modificar planificación histórica

**Dado** que la fecha seleccionada está en el pasado,\
**cuando** un usuario activo asigna, sustituye o elimina una etiqueta, de forma individual o repetida,\
**entonces** la operación está permitida y, si se repite, el máximo anual parte de esa fecha inicial, no de hoy.

### Escenario 22 — Cancelar sin modificar la planificación

**Dado** que se muestra una confirmación de sustitución o eliminación individual o repetida,\
**cuando** el usuario la cancela,\
**entonces** no se guarda ningún cambio y todas las asignaciones permanecen como estaban.

## 7. Dependencias

- HU-001 — Gestión de usuarios y autenticación.
- [Catálogo de etiquetas predeterminadas](../etiquetas-predeterminadas.md) y posibilidad de consultar sus identificadores.
- Persistencia de asignaciones individuales.
- Soporte de fechas y horas en la zona horaria IANA `Atlantic/Canary`.

## 8. Consideraciones técnicas

- Almacenar cada asignación mediante una fecha local, una franja y una referencia a una etiqueta alimentaria.
- Garantizar mediante una restricción de unicidad que solo exista una asignación por fecha y franja.
- Materializar como registros individuales todas las asignaciones producidas por una repetición.
- Calcular las fechas repetidas a partir de la fecha inicial y del intervalo semanal, sin depender del número de semana del año.
- Validar el final elegido entre el inicio y el máximo anual de RN-09: día anterior a la misma fecha del año siguiente, con el caso especial del 29 de febrero limitado al 28 de febrero siguiente, incluido.
- Generar las fechas desde el inicio mediante múltiplos enteros del intervalo semanal y conservar solo las menores o iguales al final elegido. No añadir ese final si no coincide con una ocurrencia.
- Aceptar inicio y final iguales, rechazar finales fuera del intervalo válido y no imponer una restricción basada en hoy para la planificación histórica.
- Ejecutar de forma transaccional las asignaciones, sustituciones y eliminaciones repetidas para evitar resultados parciales.
- Informar antes de una sustitución repetida qué asignaciones existentes serán reemplazadas.
- Al repetir un borrado, filtrar por fecha, franja y etiqueta exacta.
- Aplicar una política de «última escritura prevalece» cuando dos usuarios modifiquen la misma fecha y franja.
- Usar fechas locales para los días planificados y mantener los cálculos consistentes con la zona horaria IANA `Atlantic/Canary`.

## 9. Definición de terminado (Definition of Done)

- [ ] Se muestra la semana de lunes a domingo, con almuerzo y cena.
- [ ] Cada almuerzo o cena contiene como máximo una etiqueta.
- [ ] La navegación entre semanas funciona al cruzar meses y años.
- [ ] La vista mensual permite consultar y navegar entre meses.
- [ ] Se pueden asignar, sustituir y eliminar etiquetas individuales.
- [ ] Se pueden repetir asignaciones, sustituciones y eliminaciones cada N semanas.
- [ ] El usuario puede elegir un final anterior al máximo anual; se incluye si coincide con una repetición, sin añadir fechas fuera del intervalo semanal.
- [ ] Se valida el máximo anual de RN-09, incluido el límite del 28 de febrero para un inicio el 29 de febrero.
- [ ] Inicio y final iguales son válidos; un final anterior al inicio o posterior al máximo se rechaza sin cambios.
- [ ] Se pueden consultar y modificar fechas pasadas; el máximo anual se calcula desde el inicio seleccionado.
- [ ] Cancelar una confirmación individual o repetida no modifica la planificación.
- [ ] Las asignaciones repetidas se guardan como copias independientes.
- [ ] Una sustitución repetida reemplaza las etiquetas coincidentes existentes.
- [ ] Un borrado repetido solo elimina la misma etiqueta.
- [ ] La planificación es compartida y está protegida mediante autenticación.
- [ ] Se han probado cambios de mes, año, límite anual y edición concurrente.
- [ ] La funcionalidad y los criterios de aceptación están documentados.

## 10. Decisiones y cuestiones pendientes

1. **Creación y edición del catálogo de etiquetas:** esta historia utiliza el catálogo predeterminado; la creación y edición por parte del usuario se cubrirá más adelante.
2. **Fecha final de repetición:** la elige el usuario dentro del máximo anual; es inclusiva si coincide con una ocurrencia del intervalo semanal.
3. **Inicio el 29 de febrero:** fecha final máxima del 28 de febrero siguiente, incluida como límite.
4. **Planificación histórica:** se puede consultar y modificar; la ventana anual parte siempre de la fecha inicial seleccionada.

No hay cuestiones funcionales pendientes para esta historia. La planificación técnica y su TASKS no autorizan por sí solos la implementación.
