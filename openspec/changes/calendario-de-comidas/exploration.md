# Exploración: calendario de comidas

**Cambio:** `calendario-de-comidas`  
**Fuente de producto autorizada:** GitHub issue #1, “Feature: Calendario de comidas”  
**Estado:** listo para propuesta; requiere resolver decisiones de producto señaladas antes del diseño detallado.

## Problema y valor

La persona que cocina en casa necesita anticipar comidas y cenas para reducir la improvisación y preparar la compra. Actualmente la visión de producto declara la planificación recurrente como objetivo, pero no describe un flujo ni una interfaz para consultar y mantener un plan semanal. El calendario aporta una vista temporal única para consultar una semana, desplazarse por semanas y organizar varias recetas en cada franja de comida o cena.

## Evidencia revisada

| Fuente | Hallazgos relevantes |
| --- | --- |
| `docs/sdd/01-vision-producto.md` | Define como usuario principal a la persona que cocina y planifica en casa; declara la planificación recurrente de comidas y cenas para reducir improvisación, además de recetas públicas y privadas y acceso con cuenta de Gmail. |
| `prototipos/calendario-01.png` | Muestra una página de calendario seleccionada en la navegación, encabezado “Semana del 12 al 18 de mayo”, controles anterior/siguiente, `Hoy` y acción global `+ Añadir comida`. La cuadrícula tiene lunes a domingo, fecha del mes, filas Comida (sol) y Cena (luna), tarjetas con imagen, título, menú de puntos suspensivos y botón `+ Añadir`; el domingo ilustra celdas vacías punteadas con la acción específica de turno. |
| `openspec/config.yaml` | El repositorio es documentación/prototipo-first, no tiene aplicación, framework, manifiesto ni pruebas ejecutables; `strict_tdd` permanece desactivado. |

## Alcance funcional propuesto

### Incluido

- Mostrar por defecto la semana actual de la persona autenticada.
- Navegar cronológicamente a la semana anterior o siguiente y volver a la semana actual mediante `Hoy`.
- Presentar una cuadrícula semanal fija de siete columnas, de lunes a domingo, y dos filas fijas: Comida y Cena, con el nombre del día y día del mes.
- Mostrar el rango de fechas de la semana consultada en la cabecera.
- Asociar múltiples recetas a una misma combinación de fecha y turno.
- Representar cada receta planificada con imagen de portada, título y acciones contextuales para ver detalle o desasignarla.
- Ofrecer `+ Añadir` cuando ya existan recetas y un estado vacío punteado con `+ Añadir comida` o `+ Añadir cena` para celdas sin recetas.
- Ofrecer una acción global `+ Añadir comida` que guíe la selección de día y turno, además de selectores/acciones directas desde la celda.
- Persistir los planes entre sesiones y dispositivos sin requerir inicio de sesión, mediante una base de datos PostgreSQL.
- Entregar documentación de uso del calendario y especificaciones de interfaz mediante una subtarea documental vinculada.

### Fuera de alcance de esta entrega

- Compartir planes, edición colaborativa, gestión multiusuario o planes familiares compartidos.
- Reglas de compra, recordatorios de preparación o generación de listas derivadas del calendario, aunque sean objetivos generales del producto.
- Drag and drop, recurrencias, copia de semanas, nutrición, cantidades o horarios concretos; no aparecen en la issue ni en el prototipo.
- Definir o implementar el sistema de acceso, la gestión de recetas o una plataforma técnica, que pertenecen a dependencias o decisiones posteriores.

## Dependencias y precondiciones

1. **#6 Control de acceso:** queda fuera del alcance de esta feature. El calendario podrá visualizarse y modificarse sin iniciar sesión.
2. **#5 Recetas públicas y privadas:** no aplica en su alcance original. No habrá recetas públicas ni privadas: todas las recetas serán públicas y seleccionables.
3. La asignación debe guardar una referencia a receta, fecha y turno, no solo una representación visual de la tarjeta; esto mantiene las acciones de detalle y desasignación conectadas a la receta correcta. La persistencia será multidispositivo mediante PostgreSQL, sin requerir autenticación; el mecanismo de identificación anónima queda pendiente de diseño.
4. No hay fuente de código ni entorno de pruebas. Las fases posteriores deben producir primero artefactos de especificación/diseño y no declarar validación automatizada hasta que exista un stack y runner.

## Suposiciones de trabajo

- “Semana actual” se calcula en la zona horaria Europa/Canarias y la semana comienza el lunes.
- La semana se organiza de lunes a domingo, tal como exige el criterio y muestra el prototipo.
- Cada asignación es independiente, por lo que una receta puede aparecer más de una vez salvo que producto decida prohibirlo.
- “Desasignar” elimina solo la asociación del calendario, no la receta subyacente.
- El menú contextual es por tarjeta, aunque el prototipo muestre los puntos suspensivos de forma compacta.
- La imagen del prototipo es una referencia de interfaz y jerarquía visual; no establece por sí sola medidas, paleta exacta ni comportamiento no descrito por la issue.

## Decisiones de producto abiertas

| Decisión | Por qué importa | Recomendación para propuesta/diseño | Respuesta |
| --- | --- | --- | --- |
| Zona horaria y definición de “Hoy” | Puede desplazar la semana por defecto cerca de medianoche o entre dispositivos. | Definir una zona única y una regla explícita de inicio semanal. | Usar Europa/Canarias; la semana comienza el lunes. |
| Selector de recetas | La issue pide selectores directos y flujo guiado, pero no define búsqueda, filtros ni estado sin resultados. | Especificar un selector reutilizable con estado vacío y búsqueda si procede. | Incluir listado completo y búsqueda libre; todas las recetas son seleccionables. |
| Duplicados y orden de varias tarjetas | Determina cómo se presenta una celda con varias asignaciones. | Fijar orden estable, límite visual, desbordamiento y comportamiento responsive. | Permitir duplicados, ordenar alfabéticamente y mostrar todas las tarjetas con scroll. |
| Desasignación | No se indica confirmación ni recuperación. | Definir si es inmediata con deshacer o confirmación, y el feedback de éxito/error. | Será inmediata. El feedback visual queda por definir. |
| Acceso a detalle | “Ver detalle” no concreta destino ni conservación del contexto semanal. | Definir destino de detalle y forma de volver al mismo calendario/semana. | Abrirá la vista de detalle y permitirá volver conservando la semana consultada. |
| Evolución de recetas | Una receta puede cambiar título/imagen o eliminarse, afectando asignaciones existentes. | Determinar integridad de planes y tratamiento de referencias no disponibles. | No hay recetas privadas. Si se elimina, la asignación mostrará “Receta no disponible”. |
| Etiqueta de la acción global | El botón se llama `+ Añadir comida`, pero también permite elegir Cena. | Confirmar nombre neutro o aclarar que el flujo permite ambos turnos. | `Comida` es el término general; existen almuerzo y cena. |

## Riesgos

- **Persistencia anónima:** al no requerirse autenticación, debe definirse el mecanismo y alcance de persistencia entre sesiones, navegadores y dispositivos.
- **Catálogo de recetas:** todas las recetas serán públicas; sigue siendo necesario definir el contrato del catálogo y sus estados de carga o ausencia.
- **Ambigüedad temporal:** una definición incompleta de semana actual/zona horaria puede originar planes en semanas distintas de las esperadas.
- **Escalabilidad de la interfaz:** varias recetas por celda pueden romper la cuadrícula fija o el comportamiento en pantallas estrechas si no se diseña el desbordamiento.
- **Integridad:** cambios o eliminación de una receta podrían dejar asignaciones huérfanas si no se especifican.
- **Alcance documental:** la issue hace obligatoria una subtarea documental; omitirla dejaría la entrega incompleta incluso sin código.

## Artefactos probablemente afectados

| Artefacto | Acción posterior esperada |
| --- | --- |
| `openspec/changes/calendario-de-comidas/proposal.md` | Formular problema, alcance y exclusiones a partir de esta exploración. |
| `openspec/changes/calendario-de-comidas/specs/` | Crear requisitos verificables del calendario: consulta semanal, navegación, cuadrícula, múltiples asignaciones, acciones, vacío, persistencia anónima. |
| `openspec/changes/calendario-de-comidas/design.md` | Resolver modelo de asignación, contrato del catálogo público y persistencia sin autenticación, estados y tradeoffs de densidad/responsive. |
| `openspec/changes/calendario-de-comidas/tasks.md` | Incluir explícitamente la subtarea documental vinculada y ordenar el trabajo considerando que #5 y #6 quedan fuera de alcance. |
| `docs/sdd/01-vision-producto.md` | Evaluar una actualización acotada para enlazar el objetivo de planificación recurrente con el calendario, si se usa como visión viva. |
| Documentación de uso del calendario (ruta por decidir) | Crear guía de navegación, alta de receta, múltiples recetas, detalle y desasignación. |
| Especificación de interfaz (ruta por decidir) | Documentar estados, controles, cuadrícula, tarjetas y adaptación responsive tomando el prototipo como referencia. |

## Recomendación de siguiente fase

Crear propuesta y especificación del cambio, manteniendo como decisiones pendientes las preguntas adicionales de comportamiento y el mecanismo de identificación anónima. La planificación de tareas deberá tratar #5 y #6 como fuera de alcance, incluir backend Python, pruebas pytest, responsive para todas las vistas y reservar una subtarea documental vinculada.

## Preguntas adicionales para cerrar el comportamiento

1. ¿La persistencia sin login se identifica mediante una cuenta anónima, un token de dispositivo o una sesión compartible?
2. ¿Qué ocurre si la persona usa el calendario desde dos dispositivos al mismo tiempo y ambos modifican la misma celda?
3. ¿Debe existir una acción para borrar todo el plan de una semana?
4. ¿Se puede navegar indefinidamente a semanas pasadas y futuras o existe un rango permitido?
5. ¿La semana actual debe resaltarse visualmente cuando se consulta otra semana?
6. ¿El calendario debe mostrar festivos, el día actual o algún indicador adicional?
7. ¿Qué mensaje se muestra cuando no existen recetas en el catálogo?
8. ¿La búsqueda debe considerar únicamente el título o también ingredientes, categorías y etiquetas?
9. ¿La búsqueda debe ignorar mayúsculas, acentos y diferencias entre singular/plural?
10. ¿Qué sucede si una receta se elimina mientras está abierta en el selector o en la vista de detalle?
11. ¿La acción inmediata de desasignar debe mostrar un aviso de éxito, y cuánto tiempo debe permanecer visible?
12. ¿La vista de detalle se abre en la misma página, en una ruta nueva o en un modal?
13. ¿Al volver del detalle deben conservarse también filtros, búsqueda y posición de scroll, además de la semana?
14. ¿Cómo se presenta una celda con muchas recetas en móvil: scroll horizontal, vertical o tarjetas apiladas?
15. ¿Debe poder añadirse una receta varias veces en una misma franja desde una sola interacción?
16. ¿La asignación debe registrar fecha de creación o solo receta, fecha y turno?
17. ¿Qué ocurre si falla PostgreSQL al guardar una asignación: reintento, cola local o mensaje de error?
18. ¿Debe existir control de concurrencia o historial para evitar que una actualización sobrescriba otra?

## Decisiones adicionales confirmadas

- El usuario anónimo será `guest`.
- Una variable de entorno en `.env` habilitará o deshabilitará el acceso como `guest`; con `guest` habilitado no se exige login y con `guest` deshabilitado sí.
- Ante ediciones simultáneas se aplica el último guardado; no habrá control de concurrencia ni historial.
- No se podrá borrar una semana completa, no habrá límite de navegación, resaltado de semana actual ni festivos.
- Si no hay recetas, se podrá crear una entrada de texto libre sin referencia a receta.
- La búsqueda solo considera el título, pero ignora mayúsculas y acentos.
- El detalle se abrirá en un modal y al cerrarlo se conservarán semana, búsqueda y scroll.
- No se registrará la fecha de creación de una asignación.
- Si PostgreSQL no está disponible, se mostrará un aviso al usuario.

## Incoherencias y bloqueos detectados

1. **Dependencia #6:** el control de acceso se declaró fuera de alcance, pero vuelve a ser necesario cuando el acceso `guest` está deshabilitado. La propuesta debe tratarlo como dependencia externa, no como trabajo de esta feature.
2. **Identidad `guest`:** debe definirse si todo el mundo comparte el mismo plan del usuario `guest` o si cada visitante obtiene una identidad anónima derivada. Compartir un único plan puede provocar exposición y sobrescritura de datos.
3. **Texto libre:** hay que definir si una entrada libre tiene las mismas acciones que una receta, cómo se edita y cómo se elimina, y si puede coexistir con recetas en la misma celda.
4. **Persistencia ante error:** si PostgreSQL falla, hay que definir si el cambio se descarta o se mantiene visualmente como no guardado.
5. **Configuración `.env`:** falta definir el nombre de la variable, sus valores válidos y el comportamiento cuando está ausente.

## Recomendación para el diseño responsive móvil

Para conservar la cuadrícula de siete días sin reducir las tarjetas hasta hacerlas ilegibles, recomiendo:

- scroll horizontal para la cuadrícula semanal completa;
- cabecera de días sincronizada con el contenido;
- tarjetas apiladas verticalmente dentro de cada celda;
- scroll vertical dentro de una celda cuando tenga muchas tarjetas;
- mantener siempre visibles la etiqueta de turno y la acción de añadir.

Alternativas menos recomendables: convertir los días en un carrusel (oculta el contexto semanal) o apilar los siete días en una sola columna (deja de ser una cuadrícula semanal comparable).

## Decisiones adicionales confirmadas — segunda ronda

- `guest` utilizará un único calendario compartido por todas las visitas anónimas.
- Se recomienda la variable `ENABLE_GUEST_USER`, con valores booleanos `true`/`false`; si no está definida, el valor efectivo será `false`.
- Las entradas de texto libre se pueden editar y borrar, permiten duplicados, conviven con recetas, se ordenan alfabéticamente junto con ellas y no tienen menú contextual.
- El texto libre tendrá un límite máximo de caracteres y no aceptará vacío ni espacios; la cantidad exacta del límite sigue pendiente.
- Si PostgreSQL no está disponible, se mostrará un toast y se reintentará la operación hasta tres veces.
- El modal de detalle no permite editar ni desasignar recetas.
- No se podrá modificar el calendario durante la carga inicial.
- Si una receta cambia de título, el calendario mostrará el título actualizado.
- En móvil, la columna de Comida/Cena permanecerá fija mientras la cuadrícula se desplaza horizontalmente.

## Recomendación para la carga inicial

Usar un estado `skeleton` de la cuadrícula: conservar la estructura de siete columnas y dos filas, mostrando bloques visuales temporales para encabezados y tarjetas. Esto evita saltos de layout y comunica que el calendario está cargando. El estado debe bloquear las acciones de modificación hasta completar la carga.

## Nuevas preguntas pendientes

1. ¿Cuál es el límite exacto de caracteres para una entrada de texto libre? Recomiendo 100 caracteres.
2. ¿El calendario global compartido permite que cualquier visitante borre o modifique lo planificado por otra persona? Recomiendo asumir que sí y documentarlo explícitamente, o reconsiderar el modelo de `guest`.
3. ¿Los tres reintentos usan backoff? Recomiendo backoff exponencial acotado, por ejemplo 250 ms, 500 ms y 1 s.
4. ¿Después de tres fallos se conserva el formulario para reintento manual? Recomiendo conservarlo.
5. ¿El toast se muestra también cuando fallan las lecturas, o solo los guardados?
6. ¿El skeleton se muestra también al cambiar de semana o solo en la carga inicial?
7. ¿La semana nueva reemplaza el contenido inmediatamente o espera a que termine la carga?
8. ¿Qué ocurre si la receta cambia de título mientras el calendario está abierto?
9. ¿Las entradas de texto libre muestran una imagen placeholder o solo texto?
10. ¿El límite de texto cuenta caracteres Unicode completos, incluidos emojis y acentos?
11. ¿Se debe escapar o sanitizar HTML en el texto libre?
12. ¿Qué idioma y formato usa el mensaje del toast de indisponibilidad?
13. ¿El calendario global debe mostrar quién realizó la última modificación? Recomiendo no mostrarlo.
14. ¿Se necesita un mecanismo de limpieza para planes antiguos o el calendario permanece indefinidamente?
15. ¿Qué ocurre si dos visitantes añaden simultáneamente entradas distintas a la misma celda bajo la regla de último guardado?

## Decisiones adicionales confirmadas — tercera ronda

- El límite de texto libre será de 100 caracteres.
- Cualquier visitante podrá modificar o borrar entradas ajenas del calendario global.
- Tras tres fallos de PostgreSQL, se conservará el formulario para reintento manual.
- Los fallos de lectura también mostrarán un toast en español.
- Las entradas de texto libre mostrarán solo texto, contarán emojis como caracteres y se sanitizará su contenido HTML.
- No se mostrará quién realizó la última modificación.
- Las entradas de recetas eliminadas no conservarán su imagen ni mostrarán placeholder.
- No se permitirá editar entradas mediante teclado.
- El guardado del formulario se realizará al salir de foco de cada campo o al pulsar guardar.
- Se pedirá confirmación antes de abandonar cambios no guardados.
- Las modificaciones simultáneas aplicarán la regla de último guardado.

## Decisiones simples recomendadas para entradas de texto libre

- No abrir modal de detalle para texto libre; mostrarlo directamente en la celda.
- Permitir su borrado mediante una acción directa claramente visible en la propia entrada, sin menú contextual y con la misma eliminación inmediata definida para asignaciones.

## Aclaración: skeleton

Un `skeleton` es una representación temporal de carga: bloques grises o neutros que imitan la forma de encabezados y tarjetas mientras se recuperan los datos. No es contenido real. Su objetivo es evitar una pantalla vacía y saltos visuales. Para este calendario recomiendo mostrar skeleton también al cambiar de semana, bloquear las acciones durante la carga y reemplazarlo por los datos cuando la nueva semana haya terminado de cargar.

## Preguntas nuevas pendientes

1. Cuando dijiste que la semana nueva “reemplaza el contenido”, ¿debe reemplazarse al **iniciar** la carga o al **terminar** la carga? Recomiendo reemplazarla al terminar.
2. Si cambia el título de una receta mientras el calendario está abierto, ¿qué comportamiento preferís? Recomiendo actualización inmediata: la tarjeta cambia automáticamente.
3. ¿Los planes antiguos deben conservarse indefinidamente o eliminarse después de un período? “Limpieza automática” significa borrar asignaciones de semanas muy antiguas.
4. ¿El borrado directo de texto libre requiere confirmación o sigue siendo inmediato? Recomiendo mantenerlo inmediato.
5. ¿El botón Guardar debe estar siempre disponible aunque el guardado por pérdida de foco ya haya persistido el campo?
6. ¿Qué ocurre si el usuario pulsa Guardar y un campo todavía no perdió el foco?
7. ¿La confirmación de cambios no guardados aplica solo al texto libre o también a cambios de recetas?
8. ¿El límite de 100 caracteres se muestra como contador?
9. ¿El texto libre se recorta visualmente si es largo o siempre se muestra completo dentro del scroll?
10. ¿El toast de error debe indicar que se hicieron tres reintentos?
11. ¿El reintento manual vuelve a intentar solo la operación fallida o recarga toda la semana?
12. ¿El cambio de semana cancela operaciones de guardado pendientes o espera a que terminen?

## Decisiones adicionales confirmadas — cuarta ronda

- Los títulos de recetas se actualizarán inmediatamente en el calendario.
- Los planes antiguos se conservarán indefinidamente.
- El borrado de texto libre será inmediato y sin confirmación.
- Existirá un botón `Guardar` además del guardado al perder foco; `Guardar` también persistirá el campo que tenga el foco.
- La confirmación de cambios pendientes aplicará a recetas y texto libre.
- No se mostrará contador de caracteres.
- El texto libre largo se consultará mediante tooltip.
- El toast no informará que se hicieron tres reintentos.
- Al cambiar de semana se esperará a que terminen los guardados pendientes.
- Se mostrará skeleton también al cargar una semana ya visitada.
- Mientras `guest` esté habilitado se mostrará un aviso constante de que el usuario guest está activo, para que el administrador pueda deshabilitarlo en `.env`.

## Recomendación para el aviso de guest

Mostrarlo como un banner persistente en el shell de la aplicación, no como toast: debe permanecer visible y no desaparecer automáticamente. Debe indicar `Guest user enabled` y señalar que se puede desactivar mediante `ENABLE_GUEST_USER=false`. Hay una decisión de seguridad pendiente: sin un rol de administrador definido, el aviso será visible para todas las personas, no solo para un administrador.

## Preguntas nuevas pendientes

1. La pregunta sobre “reintento manual” significa: después de tres reintentos automáticos fallidos, ¿el usuario pulsa un botón para repetir solo esa operación? Recomiendo que sí.
2. ¿El botón `Guardar` debe quedar deshabilitado cuando no hay cambios?
3. ¿El guardado al perder foco y el botón `Guardar` deben evitar solicitudes duplicadas?
4. ¿Qué texto exacto debe mostrar el banner persistente de guest?
5. ¿El banner debe mostrarse a todos o solo a una futura cuenta administradora?
6. ¿Cambiar `ENABLE_GUEST_USER` requiere reiniciar la aplicación?
7. ¿El banner debe aparecer también en la pantalla de login cuando guest está deshabilitado?
8. ¿El tooltip del texto libre se activa al pasar el cursor, al pulsar o en ambos casos?
9. ¿Cómo se accede al tooltip en dispositivos táctiles?
10. ¿El tooltip debe mostrar el texto completo sin HTML?
11. ¿El skeleton de una semana ya visitada conserva las tarjetas anteriores o las reemplaza temporalmente?
12. ¿Se bloquea también la navegación mientras existen guardados pendientes?
13. ¿Qué sucede si el usuario intenta salir mientras hay reintentos activos?
14. ¿El botón `Guardar` muestra estados `Guardando` y `Guardado`?
15. ¿El texto libre se guarda como una asignación independiente con fecha y turno?
16. ¿El tooltip necesita una longitud máxima o se adapta al contenido?
17. ¿El banner de guest debe poder cerrarse temporalmente?
18. ¿Qué endpoint o comprobación determinará que PostgreSQL está disponible?

## Decisiones adicionales confirmadas — quinta ronda

- La semana nueva reemplazará el contenido al terminar la carga.
- Se acepta explícitamente el riesgo de que cualquier visitante modifique o borre datos del calendario guest compartido.
- El banner de guest habilitado será visible para todas las personas y no podrá ocultarse.
- Una receta eliminada se representará mediante un cuadro vacío.
- El botón `Guardar` se deshabilitará cuando no haya cambios.
- El cambio de `.env` requerirá reiniciar la aplicación.
- El banner de guest funcionará al pasar el cursor y al pulsarlo; en dispositivos táctiles se activará al pulsar y no podrá cerrarse.
- La navegación no se bloqueará durante guardados pendientes.
- El botón mostrará los estados `Guardando` y `Guardado`.
- El texto libre se almacenará como una asignación mínima con texto, fecha y turno, sin referencia a receta.
- El tooltip mostrará el texto completo sin HTML.

## Recomendaciones técnicas confirmadas

- Evitar solicitudes duplicadas con un estado de operación por campo: ignorar un segundo guardado mientras el primero sigue pendiente y volver a marcar el campo como pendiente si cambia durante la solicitud.
- Un reintento manual es una acción explícita posterior a los tres reintentos automáticos fallidos. Recomiendo un botón `Reintentar` que repita únicamente la operación fallida, conservando el formulario.
- Al cambiar de semana, conservar temporalmente los datos anteriores bajo un overlay de carga/skeleton hasta que lleguen los nuevos datos; así se evita una cuadrícula vacía o un salto visual. Las acciones de contenido pueden bloquearse, pero la navegación permanece disponible según la decisión confirmada.
- Mostrar el toast: `No se pudo conectar con la base de datos. El cambio no se guardó. Intentá nuevamente.`
- Detectar la disponibilidad de PostgreSQL en la capa de repositorio/servicio al ejecutar la operación real, capturando el error, reintentando y traduciendo el fallo a un estado de UI; no hace falta un endpoint de health-check separado.

## Preguntas nuevas pendientes

1. ¿El overlay de carga debe bloquear las acciones de edición aunque la navegación siga disponible?
2. ¿El estado `Guardado` desaparece después de un tiempo o permanece hasta el siguiente cambio?
3. ¿El texto del toast debe usar voseo (`Intentá`) o español neutro (`Inténtalo`)?
4. ¿El cuadro vacío de una receta eliminada debe conservar el título `Receta no disponible`?
5. ¿El cuadro vacío debe mantener el espacio original de la imagen?
6. ¿Una operación fallida al borrar se reintenta igual que una operación de guardado?
7. ¿Los tres reintentos automáticos se aplican también a lecturas?
8. ¿El botón `Reintentar` debe estar dentro del toast o en el formulario?
9. ¿La navegación a otra semana cancela el reintento manual pendiente?
10. ¿Una entrada de texto libre puede tener el mismo texto repetido en la misma franja?
11. ¿El tooltip debe tener un ancho máximo para evitar desbordamiento en móvil?
12. ¿El banner guest debe ocupar espacio fijo sin tapar la cuadrícula?
13. ¿La variable `ENABLE_GUEST_USER` se evalúa solo al arrancar el backend?
14. ¿El calendario guest debe incluir protección contra abuso o spam?
15. ¿El cuadro vacío de receta eliminada debe permitir desasignación?

## Decisiones adicionales confirmadas — sexta ronda

- Mientras carga una semana, la edición quedará bloqueada; la navegación seguirá disponible. Es la solución más sencilla y evita modificaciones sobre datos todavía no cargados.
- El estado `Guardado` se mostrará durante 2 segundos y desaparecerá automáticamente.
- Los mensajes usarán español neutro.
- Una receta eliminada conservará el título `Receta no disponible` y el espacio original de la imagen, representado como un cuadro vacío.
- Las operaciones de borrado y los fallos de lectura tendrán hasta tres reintentos automáticos.
- El botón `Reintentar` se mostrará dentro del toast.
- Cambiar de semana cancelará un reintento pendiente.
- Se permitirán entradas de texto libre idénticas dentro de la misma franja.
- El tooltip tendrá un ancho máximo en móvil.
- El banner de guest ocupará espacio propio y no tapará la cuadrícula.
- `ENABLE_GUEST_USER` se evaluará únicamente al iniciar el backend; cambiarlo requiere reiniciar.
- Se incorporará protección contra spam o abuso del calendario público.
- La receta eliminada podrá desasignarse mediante una acción directa visible en su cuadro vacío, sin modal adicional.

## Preguntas bloqueantes pendientes

1. ¿Qué protección mínima contra abuso se requiere: límite por IP, CAPTCHA, rate limiting por operación o las tres? Recomiendo rate limiting por IP y operación, sin CAPTCHA para no complicar el MVP.
2. ¿Qué límite de solicitudes por IP se aplicará al calendario guest? Recomiendo 60 lecturas y 30 escrituras por minuto.
3. ¿El rate limiting devolverá un toast en español cuando se alcance el límite? Recomiendo que sí.
4. Cuando `ENABLE_GUEST_USER=false`, ¿la pantalla de login pertenece a la dependencia #6 y queda fuera de esta entrega? Recomiendo que sí.
5. ¿El calendario guest compartido tendrá un aviso adicional de que todas las modificaciones son públicas? Recomiendo que sí.
6. ¿El texto exacto del toast neutral será `No se pudo conectar con la base de datos. El cambio no se guardó. Inténtalo de nuevo.`?
7. ¿Los tres reintentos automáticos usarán backoff de 250 ms, 500 ms y 1 s? Recomiendo que sí.
8. ¿Al cancelar un reintento al cambiar de semana se conserva el formulario o se descarta la operación? Recomiendo conservarlo.
9. ¿El cuadro vacío de receta eliminada mostrará una acción `Desasignar` siempre visible? Recomiendo que sí.
10. ¿El estado `Guardado` se muestra por campo o para todo el formulario? Recomiendo mostrarlo por operación guardada.
11. ¿El banner guest se muestra también durante la pantalla de carga inicial? Recomiendo que sí.
12. ¿El rate limiting aplica también a usuarios autenticados cuando guest está deshabilitado? Recomiendo aplicarlo a todo el tráfico público de la feature.

## Decisiones finales confirmadas

- Se aplicará rate limiting por IP y operación, sin CAPTCHA.
- Los límites serán 60 lecturas y 30 escrituras por IP y por minuto.
- La protección se aplicará a todo el tráfico de la feature, incluidos usuarios autenticados.
- Al alcanzar el límite se mostrará un toast en español.
- Cuando `ENABLE_GUEST_USER=false`, el login seguirá siendo responsabilidad de la dependencia #6 y quedará fuera de esta feature.
- Se mostrará un aviso persistente de que el calendario guest es público y compartido.
- El mensaje de error de PostgreSQL será: `No se pudo conectar con la base de datos. El cambio no se guardó. Inténtalo de nuevo.`
- Los reintentos usarán backoff de 250 ms, 500 ms y 1 s.
- Si se cancela un reintento al cambiar de semana, se conservará el formulario.
- El cuadro de receta eliminada mostrará siempre la acción `Desasignar`.
- El estado `Guardado` se mostrará por operación individual durante 2 segundos.
- El banner de guest aparecerá también durante la carga inicial.

## Estado de exploración

La exploración queda cerrada y lista para `sdd-proposal`. Las decisiones de producto, restricciones técnicas, riesgos aceptados, dependencias externas y comportamiento de resiliencia están documentados. No se requiere resolver más preguntas bloqueantes antes de redactar la propuesta.