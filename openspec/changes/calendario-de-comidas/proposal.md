# Propuesta: calendario de comidas

**Cambio:** `calendario-de-comidas`  
**Fuente de producto:** GitHub issue #1, “Feature: Calendario de comidas”  
**Estado:** propuesta  
**Base:** exploración cerrada en `openspec/changes/calendario-de-comidas/exploration.md`

## Intención

Incorporar un calendario semanal de comidas y cenas que permita consultar y mantener la planificación doméstica desde cualquier dispositivo. En el modo `guest`, el calendario será único, público y compartido por todas las visitas anónimas. La propuesta define el comportamiento funcional, de resiliencia y de seguridad mínimo que deberán concretar las fases de especificación y diseño, sin seleccionar todavía un framework ni implementar código.

## Problema

La persona que cocina en casa necesita anticipar comidas y cenas para reducir la improvisación y preparar mejor la compra. La visión actual declara la planificación recurrente como objetivo, pero el repositorio no describe todavía un flujo verificable para consultar una semana, navegar en el tiempo, añadir recetas o texto libre y mantener esas asignaciones entre sesiones y dispositivos.

Sin este cambio, la planificación permanece como una intención de producto sin interfaz, persistencia ni reglas operativas. Además, habilitar planificación anónima sin explicitar que todas las visitas comparten y pueden alterar el mismo calendario produciría expectativas incorrectas de privacidad y propiedad de los datos.

## Valor para las personas usuarias

- Ofrece una vista semanal única y predecible de comidas y cenas.
- Permite planificar con recetas existentes o con texto libre cuando el catálogo no cubra una necesidad.
- Conserva el plan en PostgreSQL para consultarlo desde distintos dispositivos.
- Mantiene el contexto de trabajo al consultar el detalle de una receta.
- Comunica de forma permanente cuándo el calendario funciona como espacio público compartido y proporciona feedback ante guardados, límites o fallos de persistencia.

## Objetivos

1. Permitir consultar y navegar un calendario semanal de lunes a domingo, calculado en `Europe/Canary` (Europa/Canarias), sin límites temporales.
2. Permitir varias asignaciones de receta o texto libre por fecha y turno (`Comida` o `Cena`), incluidos duplicados.
3. Persistir lecturas, altas, cambios y bajas en PostgreSQL con comportamiento resiliente y feedback comprensible.
4. Proporcionar una experiencia completamente responsive, utilizable en móvil sin perder el contexto semanal.
5. Habilitar de forma configurable un calendario `guest` público y compartido, haciendo visible y explícito su modelo de acceso.
6. Entregar documentación de uso y una especificación de interfaz como parte obligatoria del cambio.

## Alcance incluido

### Vista y navegación semanal

- Abrir por defecto la semana actual según Europa/Canarias, comenzando el lunes.
- Mostrar el rango de fechas y una cuadrícula de lunes a domingo con dos turnos fijos: Comida y Cena.
- Navegar a cualquier semana anterior o posterior y volver a la semana actual mediante `Hoy`.
- No limitar la navegación ni mostrar festivos o resaltado especial de la semana actual.
- Mostrar una acción global `+ Añadir comida` que permita escoger día y turno, además de acciones directas en cada celda.
- Mostrar todas las asignaciones de cada celda, ordenadas alfabéticamente; se permiten recetas y textos libres repetidos.

### Asignaciones de recetas

- Buscar recetas públicas por título, ignorando mayúsculas y acentos, y seleccionar cualquiera del catálogo.
- Mostrar cada asignación con su título e imagen de portada y permitir abrir su detalle o desasignarla.
- Abrir el detalle en un modal, sin edición ni desasignación desde el propio modal, conservando al cerrarlo la semana, la búsqueda y la posición de scroll.
- Reflejar inmediatamente los cambios de título de una receta.
- Si una receta fue eliminada, conservar la asignación con el título `Receta no disponible`, reservar el espacio original de imagen como cuadro vacío y ofrecer siempre una acción directa `Desasignar`.
- Entender la desasignación como eliminación inmediata de la relación con el calendario, nunca como eliminación de la receta.

### Asignaciones de texto libre

- Permitir que recetas y entradas de texto libre convivan en una misma celda.
- Guardar cada texto como asignación independiente con texto, fecha y turno, sin referencia a receta ni fecha de creación.
- Permitir edición y eliminación directa e inmediata, sin menú contextual ni confirmación de borrado.
- Validar un máximo de 100 caracteres Unicode completos, incluidos emojis, y rechazar valores vacíos o compuestos solo por espacios.
- Sanitizar cualquier HTML y presentar siempre contenido de solo texto.
- Mostrar la entrada sin imagen y ofrecer el texto completo mediante tooltip, activable por cursor o pulsación, con ancho máximo adaptado a móvil.
- No habilitar una vía de edición mediante teclado distinta del formulario definido.

### Guardado y cambios pendientes

- Guardar al perder el foco de cada campo y mediante un botón explícito `Guardar`.
- Hacer que `Guardar` incluya el campo actualmente enfocado y permanezca deshabilitado cuando no existan cambios.
- Evitar solicitudes duplicadas por operación; si el valor cambia durante una petición, volver a marcarlo como pendiente.
- Mostrar `Guardando` y después `Guardado` por operación individual; `Guardado` desaparecerá a los 2 segundos.
- Pedir confirmación antes de abandonar cambios no guardados, tanto para recetas como para texto libre.
- Mantener disponibles los controles de navegación; si hay guardados pendientes, esperar a que terminen antes de cambiar de semana.
- Aplicar último guardado gana ante modificaciones concurrentes, sin bloqueo, historial ni atribución de autoría.

### Carga y errores

- Mostrar un skeleton de la cuadrícula durante la carga inicial y cada cambio de semana, incluso al revisitar semanas.
- Bloquear la edición durante la carga, pero mantener disponible la navegación.
- Reemplazar el contenido semanal cuando finalice la carga. El diseño deberá priorizar conservar los datos anteriores bajo un overlay/skeleton mientras llegan los nuevos para evitar vacíos y saltos visuales.
- Ante fallos de lectura, escritura o borrado en PostgreSQL, realizar tres reintentos automáticos con esperas de 250 ms, 500 ms y 1 s.
- Tras agotar los reintentos, conservar el formulario fallido y mostrar el toast neutral: `No se pudo conectar con la base de datos. El cambio no se guardó. Inténtalo de nuevo.`
- Incluir `Reintentar` dentro del toast para repetir únicamente la operación fallida.
- Cancelar el reintento manual pendiente al cambiar de semana, sin descartar el formulario conservado.
- Detectar los fallos al ejecutar la operación real en la capa de repositorio o servicio; no se requiere un endpoint de health check específico.

### Acceso guest, aviso y protección contra abuso

- Leer `ENABLE_GUEST_USER` al iniciar el backend; aceptar valores booleanos `true`/`false` y usar `false` cuando la variable no exista.
- Requerir reinicio del backend para que un cambio de configuración tenga efecto.
- Cuando `ENABLE_GUEST_USER=true`, permitir acceso anónimo a un único calendario compartido. Toda visita podrá leer, crear, modificar y borrar asignaciones, incluidas las creadas por otras personas.
- Mostrar a todas las personas un banner persistente, no descartable y con espacio reservado en el layout, también durante la carga inicial, que indique que el modo guest está activo y que el calendario es público y compartido.
- Aplicar rate limiting por IP y por minuto a todo el tráfico de esta feature, incluido el tráfico autenticado: 60 lecturas y 30 escrituras.
- No incorporar CAPTCHA. Al superar un límite, mostrar un toast en español neutro; su texto exacto se fijará en la especificación de interfaz.

### Persistencia, plataforma y documentación

- Persistir el calendario en PostgreSQL para conservarlo entre sesiones y dispositivos.
- Implementar el backend futuro en Python y sus pruebas futuras con pytest.
- Hacer completamente responsive todas las vistas y estados de esta feature. En móvil, conservar una cuadrícula semanal con scroll horizontal, encabezado sincronizado, columna Comida/Cena fija, tarjetas apiladas y desbordamiento vertical por celda.
- Crear documentación obligatoria sobre el uso del calendario.
- Crear una especificación obligatoria de interfaz que cubra estructura, controles, estados, feedback, banner, modal, tooltips y adaptación responsive.

## Fuera de alcance

- Implementar el login, la pantalla de acceso o el sistema de identidad de la dependencia #6.
- Incorporar la distinción entre recetas públicas y privadas de la issue #5; para este cambio todas las recetas son públicas.
- Calendarios personales, aislamiento entre visitantes guest, propiedad de entradas, roles, permisos, planes familiares o colaboración identificada.
- Historial, auditoría, autoría, resolución avanzada de conflictos o recuperación/deshacer de eliminaciones.
- Borrado completo de una semana, limpieza automática de planes antiguos o almacenamiento de fecha de creación.
- Drag and drop, recurrencias, copia de semanas, festivos, nutrición, cantidades, horarios concretos, recordatorios, preparación anticipada o generación de listas de compra.
- CAPTCHA u otras protecciones antiabuso adicionales al rate limiting acordado.
- Elegir en esta propuesta el framework frontend, framework backend, librería de componentes, mecanismo de despliegue o estrategia completa de autenticación.
- Implementar código o afirmar validación automatizada en el estado actual del repositorio.

## Dependencias y precondiciones

### Dependencia externa condicional: issue #6

Cuando `ENABLE_GUEST_USER=false`, el acceso requiere el login definido por la issue #6. Ese login es una dependencia externa y condicional, no una parte de `calendario-de-comidas`. La feature no debe implementar una pantalla de login alternativa ni redefinir autenticación. Cuando `ENABLE_GUEST_USER=true`, el calendario puede operar anónimamente sin esperar a #6.

### Catálogo de recetas

La feature necesita un contrato de lectura de recetas y referencias estables para sus asignaciones. La issue #5 no es una dependencia funcional para distinguir visibilidad: todas las recetas se consideran públicas y seleccionables. El diseño deberá cubrir catálogo vacío, actualización de títulos y referencias a recetas eliminadas.

### Base técnica aún no creada

El repositorio es actualmente documentation/prototype-first. No existe aplicación, manifiesto de dependencias, framework, build, runner fiable ni pruebas ejecutables. `strict_tdd` está desactivado y los comandos de test, lint, typecheck y formato están vacíos en `openspec/config.yaml`. Las fases siguientes deberán definir primero especificación y diseño; posteriormente, la implantación del backend Python deberá configurar pytest antes de declarar pruebas automatizadas superadas.

## Riesgos aceptados

### Calendario público compartido

Se acepta explícitamente que el modo guest expone un único calendario público y compartido: cualquier visitante anónimo puede consultar, añadir, modificar o borrar datos de cualquier otra visita. No existe privacidad, propiedad individual, atribución ni recuperación histórica. Esta decisión puede causar exposición de información introducida por usuarios, vandalismo, spam, sobrescrituras, pérdida de datos y confusión sobre quién controla el plan. El banner persistente y el rate limiting reducen sorpresa y abuso básico, pero no eliminan estos riesgos.

Este riesgo no debe mitigarse silenciosamente mediante calendarios por dispositivo, cuentas anónimas aisladas o restricciones de edición, porque eso cambiaría el alcance confirmado. Una evolución hacia aislamiento o permisos requerirá una decisión de producto separada.

### Seguridad y abuso

- El rate limiting por IP puede afectar redes compartidas y puede eludirse mediante múltiples direcciones.
- El texto libre es una superficie de contenido no confiable; su sanitización y renderizado como texto son obligatorios, pero no sustituyen controles de autorización inexistentes en guest.
- Mostrar detalles de configuración en un banner público puede revelar que el modo guest está habilitado, aunque esa visibilidad es deliberada.
- La regla de último guardado gana puede sobrescribir cambios concurrentes sin aviso ni recuperación.

### Operación y experiencia

- Una indisponibilidad de PostgreSQL impide consultar o persistir el calendario; los reintentos y formularios conservados reducen pérdida de trabajo, pero no ofrecen funcionamiento offline.
- Un número ilimitado de semanas, planes conservados indefinidamente y múltiples asignaciones por celda pueden aumentar volumen de datos y densidad visual.
- Una cuadrícula de siete días exige scroll en móvil y puede ocultar parte del contexto pese a mantener fija la columna de turnos.
- La dependencia condicional de #6 impide acceder con guest deshabilitado hasta que exista el sistema externo de login.

## Suposiciones

- El término global `Comida` puede introducir tanto el turno Comida como Cena.
- Una asignación de receta conserva una referencia a receta, fecha y turno; una asignación libre conserva texto, fecha y turno.
- Los planes se conservan indefinidamente salvo eliminación manual de sus asignaciones.
- El orden alfabético se aplica conjuntamente a recetas y textos libres dentro de cada celda.
- Los límites de rate limiting clasifican las operaciones según lectura o escritura; altas, ediciones y bajas son escrituras.
- El banner solo aparece cuando guest está habilitado; con guest deshabilitado, el flujo visible depende de #6.
- Los detalles de contratos API, esquema PostgreSQL, conteo técnico de Unicode y textos de feedback no fijados aquí se resolverán en especificación y diseño sin alterar las decisiones de producto cerradas.

## Restricciones de producto

- Semana de lunes a domingo en Europa/Canarias, sin límite de navegación, festivos ni resaltado de semana actual.
- Dos turnos fijos: Comida y Cena.
- Asignaciones múltiples, duplicados permitidos y orden alfabético.
- Texto libre de hasta 100 caracteres, no vacío, sanitizado y renderizado como texto.
- Eliminación inmediata y sin confirmación para texto libre y desasignaciones.
- Modal de receta solo para consulta; conserva semana, búsqueda y scroll.
- Todas las recetas son públicas; no se incorpora la visibilidad pública/privada de #5.
- Interfaz y estados completamente responsive.
- Banner guest público, persistente, no descartable y sin superposición del contenido.
- Documentación de uso y especificación de interfaz obligatorias.

## Restricciones técnicas

- Persistencia en PostgreSQL y backend en Python.
- Pruebas backend futuras con pytest; actualmente no existe runner y no se ejecutarán pruebas durante esta fase documental.
- `ENABLE_GUEST_USER` se evalúa una sola vez al arrancar, con valor por defecto `false`.
- Tres reintentos automáticos para lecturas, escrituras y borrados, con backoff 250 ms/500 ms/1 s.
- Rate limiting por IP, operación y ventana de un minuto: 60 lecturas y 30 escrituras, también para tráfico autenticado.
- Último guardado gana, sin control de concurrencia ni historial.
- Sin fecha de creación y sin eliminación automática de planes antiguos.

## Áreas y artefactos afectados

- Especificaciones verificables bajo `openspec/changes/calendario-de-comidas/specs/`.
- Diseño técnico y de interacción en `openspec/changes/calendario-de-comidas/design.md`.
- Plan de trabajo en `openspec/changes/calendario-de-comidas/tasks.md`.
- Futuro backend Python, persistencia PostgreSQL, configuración y pruebas pytest.
- Futura interfaz web responsive y su integración con catálogo de recetas.
- Documentación de uso del calendario y especificación de interfaz, con rutas por decidir.
- Posible enlace acotado desde `docs/sdd/01-vision-producto.md`, si se mantiene como visión viva.

## Dirección de aceptación y éxito medible

La especificación posterior deberá convertir como mínimo los siguientes resultados en escenarios verificables:

1. Al abrir el calendario, se consulta la semana correcta de lunes a domingo según Europa/Canarias y se muestran los turnos Comida y Cena.
2. Una persona puede navegar sin límite entre semanas y usar `Hoy`; cada carga muestra skeleton, bloquea edición y permite navegación.
3. Una celda admite múltiples recetas y textos libres, incluidos duplicados, y presenta todos los elementos en orden alfabético.
4. La búsqueda de recetas encuentra títulos sin distinguir mayúsculas ni acentos, y todas las recetas del catálogo son seleccionables.
5. El texto libre rechaza vacío, solo espacios y más de 100 caracteres; neutraliza HTML, admite emojis, se muestra como texto y ofrece tooltip accesible en puntero y táctil.
6. El guardado por blur y por `Guardar` persiste el campo enfocado sin duplicar solicitudes; el botón se deshabilita sin cambios y cada operación muestra `Guardando`/`Guardado` durante el tiempo definido.
7. Salir con cambios pendientes solicita confirmación, y cambiar de semana espera guardados activos sin inutilizar la navegación.
8. El modal de detalle conserva semana, búsqueda y scroll, y no permite editar ni desasignar.
9. Los cambios de título aparecen inmediatamente; una receta eliminada conserva una asignación reconocible con `Receta no disponible`, cuadro de imagen vacío y `Desasignar` directo.
10. Los planes sobreviven a reinicios y pueden verse desde otro dispositivo mediante PostgreSQL.
11. Cada fallo de lectura, escritura o borrado ejecuta los tres reintentos con el backoff acordado; al agotarlos se conserva el formulario, aparece el toast exacto y `Reintentar` repite solo la operación fallida.
12. Cambiar de semana cancela un reintento manual pendiente sin perder el formulario conservado.
13. Con `ENABLE_GUEST_USER` ausente o en `false`, la feature no concede acceso guest y deriva la necesidad de acceso a #6; con `true` tras reiniciar, cualquier visita usa el calendario compartido.
14. Durante todo el modo guest, incluida la carga inicial, se ve un banner no descartable que informa del carácter público y compartido sin tapar la cuadrícula.
15. Los límites de 60 lecturas y 30 escrituras por IP/minuto se aplican tanto a tráfico anónimo como autenticado y producen un toast neutral en español al superarse.
16. La interfaz mantiene disponibles sus flujos y feedback en tamaños de escritorio y móvil, incluida la cuadrícula desplazable y la columna fija de turnos.
17. La entrega incluye documentación de uso y especificación de interfaz; no se considerará completa si falta cualquiera de ellas.

## Indicadores de resultado

- El 100 % de los escenarios funcionales y de resiliencia anteriores queda especificado con criterios comprobables antes de implementar.
- El 100 % de las rutas de escritura, borrado y lectura del calendario incorpora rate limiting y manejo de reintentos acordado.
- Ningún flujo guest presenta el calendario sin el aviso persistente de espacio público compartido.
- Las pruebas backend de la futura implementación se ejecutan mediante pytest una vez configurado el runner; hasta entonces no se atribuye cobertura ni validación automatizada al repositorio.
- La revisión responsive cubre, como mínimo, un viewport móvil táctil y uno de escritorio para carga, contenido, modal, tooltip, errores y celdas con desbordamiento.

## Rollback y desactivación

La medida operativa inmediata de rollback será establecer `ENABLE_GUEST_USER=false` y reiniciar el backend, deteniendo el acceso anónimo sin borrar datos existentes. Si #6 no está disponible, el calendario quedará inaccesible en lugar de abrirse públicamente. Los planes almacenados en PostgreSQL no se eliminarán automáticamente durante el rollback.

La reversión de despliegue deberá retirar conjuntamente la interfaz y las rutas de la feature o mantener contratos compatibles; las migraciones de base de datos deberán diseñarse para no destruir asignaciones al desactivar la funcionalidad. Los límites, banner y sanitización no podrán deshabilitarse de forma independiente mientras el calendario guest siga accesible.

## Siguiente fase recomendada

Redactar las especificaciones verificables del cambio. Después, producir el diseño que defina contratos API, modelo PostgreSQL, estados de UI, semántica exacta de las operaciones concurrentes, accesibilidad, responsive, rate limiting y estrategia de configuración. La planificación deberá incluir explícitamente la configuración de pytest y las dos entregas documentales obligatorias, sin afirmar que el repositorio actual dispone ya de un runner.
