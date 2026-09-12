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
- Persistir los planes entre sesiones sin requerir inicio de sesión; el mecanismo de identidad y el alcance de esa persistencia para personas o dispositivos sigue siendo una decisión de diseño.
- Entregar documentación de uso del calendario y especificaciones de interfaz mediante una subtarea documental vinculada.

### Fuera de alcance de esta entrega

- Compartir planes, edición colaborativa, gestión multiusuario o planes familiares compartidos.
- Reglas de compra, recordatorios de preparación o generación de listas derivadas del calendario, aunque sean objetivos generales del producto.
- Drag and drop, recurrencias, copia de semanas, nutrición, cantidades o horarios concretos; no aparecen en la issue ni en el prototipo.
- Definir o implementar el sistema de acceso, la gestión de recetas o una plataforma técnica, que pertenecen a dependencias o decisiones posteriores.

## Dependencias y precondiciones

1. **#6 Control de acceso:** queda fuera del alcance de esta feature. El calendario podrá visualizarse y modificarse sin iniciar sesión.
2. **#5 Recetas públicas y privadas:** no aplica en su alcance original. No habrá recetas públicas ni privadas: todas las recetas serán públicas y seleccionables.
3. La asignación debe guardar una referencia a receta, fecha y turno, no solo una representación visual de la tarjeta; esto mantiene las acciones de detalle y desasignación conectadas a la receta correcta. Como no se requiere autenticación, queda pendiente definir si la persistencia será local al navegador, anónima compartida o mediante otro identificador.
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
| Selector de recetas | La issue pide selectores directos y flujo guiado, pero no define búsqueda, filtros ni estado sin resultados. | Especificar un selector reutilizable con estado vacío y búsqueda si procede. | Sigue abierta; todas las recetas son seleccionables. |
| Duplicados y orden de varias tarjetas | Determina cómo se presenta una celda con varias asignaciones. | Fijar orden estable, límite visual, desbordamiento y comportamiento responsive. | Permitir duplicados; el resto sigue abierto. |
| Desasignación | No se indica confirmación ni recuperación. | Definir si es inmediata con deshacer o confirmación, y el feedback de éxito/error. | Sigue abierta. |
| Acceso a detalle | “Ver detalle” no concreta destino ni conservación del contexto semanal. | Definir destino de detalle y forma de volver al mismo calendario/semana. | Sigue abierta. |
| Evolución de recetas | Una receta puede cambiar título/imagen o eliminarse, afectando asignaciones existentes. | Determinar integridad de planes y tratamiento de referencias no disponibles. | No hay recetas privadas; el resto sigue abierto. |
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

Crear propuesta y especificación del cambio, manteniendo como bloqueadores de diseño las decisiones de zona horaria, selector de recetas, duplicados/orden y desasignación. La planificación de tareas deberá tratar #5 y #6 como fuera de alcance y reservar una subtarea documental vinculada.
