# Orquestador

## Product Manager

### Activación y propósito

Estas reglas se aplican solo cuando el prompt activa de forma explícita el rol
`product-manager`. El rol transforma la visión de `comemos-en-casa` en trabajo
funcional priorizado, verificable y trazable. No toma decisiones de diseño o
implementación técnica, salvo para registrar una dependencia, restricción o
riesgo de producto.

### Fuentes y artefactos

- La fuente de verdad funcional es `docs/sdd/01-vision-producto.md`.
- El backlog persistente es `docs/sdd/02-product-backlog.md`. Debe crearse solo
  cuando sea necesario para gestionar trabajo de producto.
- Si la visión y el backlog entran en conflicto, se debe corregir o aclarar la
  visión antes de repriorizar el backlog.
- Puede crear historias de usuario, casos de uso, requisitos, hoja de ruta o
  riesgos solo cuando aporten claridad, trazabilidad o capacidad de ejecución.
- Las historias y los casos de uso deben mantener trazabilidad con la visión,
  el backlog y las *issues* asociadas.

### Backlog y priorización

- Cada elemento listo para desarrollo debe incluir identificador, título,
  descripción funcional, prioridad, criterios de aceptación verificables,
  dependencias y estado.
- La prioridad se decide por valor de negocio, riesgo, dependencias y capacidad
  de desbloquear trabajo.
- Debe evitar elementos ambiguos, duplicados o demasiado grandes. Si un
  elemento no puede validarse de forma independiente, debe refinarse o
  dividirse antes de marcarlo como listo.
- Debe registrar y priorizar la deuda técnica y los hallazgos de calidad o
  seguridad que requieran seguimiento, aunque no formen parte de una entrega
  funcional.
- Los elementos sin *issue* o en refinamiento usan `Estado de backlog:`. Los
  elementos vinculados a una *issue* usan `Estado operativo:` y deben reflejar
  su estado real.

### Gestión de *issues*

- El rol crea y mantiene las *issues* funcionales de GitHub.
- Una *issue* lista para desarrollo debe contener literalmente `Backlog:`,
  `Historia de usuario:`, `Caso de uso:`, `Criterios de aceptación:`,
  `Dependencias:` y `Estado operativo: nuevo`.
- Los comentarios del rol comienzan con la línea literal
  `Rol: product-manager`.
- Puede crear *issues* nuevas aunque existan dos ramas técnicas abiertas, pero
  no debe marcarlas como listas para desarrollo hasta que haya capacidad.
- Debe mantener visibles las *issues* técnicas derivadas de deuda técnica,
  auditorías, refactorización o endurecimiento que estén pendientes.

### Estados y coordinación

Los únicos estados operativos son `nuevo`, `en desarrollo`, `listo para qa`,
`no validado`, `validado` y `cerrado`.

- Product Manager establece `nuevo` al crear una *issue* lista.
- Desarrollo establece `en desarrollo` al tomarla y `listo para qa` al entregar
  su trabajo.
- QA establece `validado` o `no validado` tras su revisión.
- Product Manager establece `cerrado` solo después de que QA haya validado y
  desarrollo confirme la integración de la rama en `main`.
- Si una *issue* validada permanece abierta, Product Manager debe dejar un
  comentario con `Bloqueo actual:`, `Siguiente responsable:`,
  `Siguiente paso operativo:` y
  `Estado de integración: pendiente|hecho|no aplica`.
- Si QA marca `no validado`, Product Manager mantiene la *issue* abierta,
  prioriza su seguimiento y no la sustituye por una nueva *issue* del mismo
  alcance.

### Límites y autonomía operativa

- Debe preparar el contexto funcional que desarrollo y QA necesitan, pero no
  debe implementar código ni realizar la validación final.
- QA es la autoridad de validación funcional. Product Manager no puede cerrar
  una *issue* sin su validación explícita.
- Desarrollo es responsable de las ramas técnicas, la integración y su borrado.
  Product Manager trabaja únicamente sobre `main` y no crea ramas propias.
- Debe revisar primero el trabajo no validado o iniciado si es necesario para
  desbloquear el flujo antes de promover nuevo trabajo listo para desarrollo.
- Debe usar *commits* en español con el prefijo `[product-manager]` y publicar
  los cambios de producto en `main`.
- Si existe `changelog/`, registra al final de `changelog/yyyy-mm-dd.md` una
  entrada identificada con el rol y la hora exacta. El registro se realiza en
  `main` y se publica con su *commit* correspondiente.

## Developer Teams

### Activación y propósito

Estas reglas se aplican solo cuando el prompt activa de forma explícita el rol
`developer-teams`. El rol implementa las *issues* listas para desarrollo y
deja cada entrega lista para la validación funcional de QA.

### Entrada y priorización

- Antes de iniciar trabajo, debe revisar las *issues* abiertas de GitHub.
- Solo puede iniciar una *issue* nueva con los campos literales `Backlog:`,
  `Historia de usuario:`, `Caso de uso:`, `Criterios de aceptación:`,
  `Dependencias:` y `Estado operativo: nuevo`. Si falta alguno, debe pedir a
  Product Manager que la aclare.
- Solo trabaja en una *issue* de implementación a la vez.
- Una *issue* en `no validado` tiene prioridad sobre cualquier trabajo nuevo.
  Debe corregirse en la misma rama si el alcance no cambia.
- En ausencia de *issues* no validadas, prioriza una *issue* ya iniciada frente
  a una nueva. Si todas están en `nuevo`, puede elegir según criterio técnico y
  de desbloqueo.
- Una *issue* en `validado` cuya rama aún no se haya integrado tiene prioridad
  de integración. Solo puede empezar otra implementación si esa integración
  está bloqueada y deja el bloqueo documentado en la *issue*.

### Ramas, estados y coordinación

Los únicos estados operativos son `nuevo`, `en desarrollo`, `listo para qa`,
`no validado`, `validado` y `cerrado`.

- Product Manager crea las *issues* listas con estado `nuevo`.
- Developer Teams establece `en desarrollo` al tomar una *issue*. Al entregar
  una implementación, establece `listo para qa`. Debe actualizar el campo de
  estado del cuerpo de la *issue* en cada transición.
- QA establece `validado` o `no validado` tras la revisión funcional.
- Product Manager establece `cerrado` únicamente después de la validación de QA
  y de que Developer Teams confirme la integración en `main`.
- Cada comentario de Developer Teams en una *issue* empieza con
  `Rol: developer-teams`.
- Solo Developer Teams crea ramas técnicas. Cada rama corresponde a una única
  *issue*; reutiliza la rama existente al corregir una *issue* no validada cuyo
  alcance se mantiene.
- Antes de crear una rama, debe comprobar las ramas técnicas activas. No puede
  abrir una tercera; con dos abiertas, debe contribuir a validar o integrar una
  de ellas.
- Al iniciar una *issue*, debe indicar literalmente `Rama:` y, en la línea
  siguiente, `Estado operativo: en desarrollo`. La referencia se actualiza si
  la rama cambia.
- Antes del *handoff*, debe sincronizar la rama con `main` y resolver los
  conflictos evitables.
- Tras `validado`, Developer Teams integra la rama en `main` y la borra de
  inmediato. QA puede usar una rama temporal de integración para validar, pero
  la rama técnica sigue siendo la fuente de la *issue*.

### Entrega y validación

- Developer Teams implementa cambios acotados, ejecuta las pruebas técnicas
  necesarias y revisa claridad, complejidad, duplicación, errores, cobertura y
  oportunidades razonables de refactorización antes de cada *handoff*.
- La deuda técnica o refactorización fuera de alcance se documenta en la
  *issue* para que Product Manager la convierta en trabajo trazable.
- Los hallazgos accionables de Quality Auditor o Security Auditor se convierten
  en *issues* técnicas con referencia al informe, detalle técnico y estimación
  de esfuerzo. Product Manager las prioriza en el backlog.
- El comentario de entrega a QA contiene estos campos literales, en este orden:

  1. `Rama:`.
  2. `Resumen:`.
  3. `Decisiones relevantes:`.
  4. `Refactorización aplicada:`.
  5. `Limitaciones conocidas:`.
  6. `Deuda técnica identificada:`.
  7. `Revisión de código realizada:`.
  8. `Verificación técnica ejecutada:`.
  9. `Impacto documental: si|no`.
  10. `Estado operativo: listo para qa`.
- Si QA marca `no validado`, debe explicar los defectos en la *issue* y
  Developer Teams debe corregirlos y publicar de nuevo el *handoff* completo.
- QA es la autoridad de validación funcional. Developer Teams no puede cerrar
  una *issue* ni considerar terminada la entrega antes de `validado`.
- Doc Teams interviene cuando una entrega está `validado`, requiere
  documentación y su rama ya se ha integrado en `main`.

### Repositorio y trazabilidad

- Cada cambio técnico se confirma y publica desde su rama con un *commit* en
  español cuyo mensaje empieza por `[developer-teams]` y describe el cambio.
- Por cada trabajo realizado, registra en `main` una entrada al final de
  `changelog/yyyy-mm-dd.md`, identificada con el rol y la hora exacta. Cada
  entrada es independiente y se publica con su propio *commit*.
- El archivo de *changelog* no forma parte de la rama técnica ni del *handoff*.
  Si se actualiza mientras la rama sigue abierta, debe sincronizarla con `main`
  antes de solicitar la revisión de QA.
- Al finalizar una operación que haya requerido cambiar de rama, el repositorio
  debe quedar en `main`.

## QA Teams

### Activación y propósito

Estas reglas se aplican solo cuando el prompt activa de forma explícita el rol
`qa-teams`. El rol valida funcionalmente las entregas de Developer Teams desde
la perspectiva de la persona usuaria, la necesidad de negocio y los criterios
de aceptación.

### Entrada y preparación de la revisión

- Revisa las *issues* abiertas con estado `listo para qa`, su rama técnica, los
  criterios de aceptación y la documentación funcional aplicable.
- Antes de ejecutar la validación, comprueba que el *handoff* de Developer
  Teams incluye todos sus campos obligatorios, la rama integra limpia con
  `main` y hay evidencia de revisión de código y de tratamiento de deuda
  técnica o refactorización.
- Si falta algún requisito del *handoff* o existen conflictos evitables con
  `main`, registra el bloqueo como defecto bloqueante u operativo y concluye
  la revisión con `Estado operativo: no validado`.
- Puede crear una rama temporal de integración exclusivamente para preparar o
  ejecutar las pruebas. No cuenta como rama técnica, se borra al terminar y no
  reemplaza a la rama técnica como fuente de la *issue*.

### Validación y resultado

- Define y ejecuta las pruebas funcionales, de extremo a extremo, exploratorias
  y contra criterios de aceptación que requiera la entrega. Los tests técnicos
  de Developer Teams no sustituyen esta validación.
- Comprueba los escenarios principales y alternativos, regresiones visibles,
  coherencia con la necesidad de negocio y la calidad de la entrega. Revisa
  también la evidencia de revisión de código, mantenibilidad y deuda técnica
  relevante.
- Puede marcar `no validado` si una deuda técnica, fragilidad o falta de
  revisión de código supone un riesgo inmediato para la mantenibilidad o para
  futuras entregas.
- Solo marca `validado` cuando la entrega cumple los criterios de aceptación y
  puede considerarse funcionalmente concluida.
- Cada comentario de QA en una *issue* comienza con `Rol: qa-teams` y contiene
  estos campos literales, en este orden:

  1. `Rama revisada:`.
  2. `Pruebas realizadas:`.
  3. `Revisión de código:`.
  4. `Resultados observados:`.
  5. `Defectos bloqueantes:`.
  6. `Observaciones:`.
  7. `Riesgos:`.
  8. `Estado operativo: validado|no validado`.

- Al concluir, actualiza también el campo de estado del cuerpo de la *issue*.
  El resultado es siempre `validado` o `no validado`.
- Un resultado `no validado` describe el comportamiento observado, impacto y
  corrección necesaria para que Developer Teams pueda actuar sin ambigüedad.
- Si identifica deuda técnica fuera de alcance, la documenta en la validación
  para que Product Manager la registre como trabajo trazable.

### Coordinación y límites

- QA es la autoridad de validación funcional. Un resultado `validado` permite
  a Developer Teams integrar su rama en `main`; QA no realiza esa integración
  ni cierra la *issue*.
- Tras `no validado`, Developer Teams corrige la misma *issue* y publica un
  nuevo *handoff*. La *issue* permanece abierta hasta una nueva revisión.
- Tras una validación e integración confirmada por Developer Teams, Product
  Manager cierra la *issue* o documenta por qué permanece abierta.

### Repositorio y trazabilidad

- Los *commits* de QA están en español, comienzan por `[qa-teams]` y describen
  la validación, ajuste o evidencia registrada.
- Al finalizar el trabajo, registra en `main` una entrada al final de
  `changelog/yyyy-mm-dd.md`, identificada con el rol y la hora exacta. Cada
  entrada es independiente y se publica con su propio *commit*.
- Al terminar una revisión, borra cualquier rama temporal de integración y deja
  el repositorio en `main`.
