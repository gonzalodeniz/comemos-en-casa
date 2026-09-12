# Flujo compartido

## Alcance y fuentes

Este contrato se aplica a todos los roles activados según [AGENTS.md](AGENTS.md).
La visión define el producto. La issue define la entrega asignada y conserva
su coordinación. El código y las pruebas aportan evidencia del comportamiento.
Los procedimientos propios de cada rol están en [agentes/](agentes/).

El objetivo autorizado se registra en una issue de coordinación. Incluye
alcance, exclusiones y condiciones verificables de finalización. No se amplía
por descubrir mejoras: estas se registran para priorización posterior.
Las decisiones rutinarias y reversibles se resuelven con criterio y evidencia.
Las decisiones de producto sin respaldo que cambien el alcance se escalan.

## Comunicación y asignación

Toda asignación, resultado, bloqueo y siguiente paso se registra en la issue.
Las PR, informes y artefactos se enlazan desde ella; no sustituyen ese registro.
Las respuestas locales solo transportan enlaces, nunca el único resultado.

El agente trabaja exclusivamente en la issue y el objetivo inmediato asignados.
Si no puede ejecutarlos, registra el motivo y devuelve el turno. No selecciona
otra issue ni invoca otros agentes. El lanzador ejecuta los roles en serie.

Cada asignación tiene un identificador único, por ejemplo
`<ejecucion>-<iteracion>`. Antes de actuar, el agente busca su resultado y
comprueba el estado real de ramas, PR y archivos. Si ya está resuelta, reutiliza
la evidencia. Nunca duplica issues, PR, comentarios de resultado o commits
por reintentar una operación cuya respuesta se perdió.

Todo comentario operativo empieza por `Rol: <rol>` e identifica
`Asignación:`. El resultado de cada agente contiene:

- `Objetivo atendido:` y `Resultado: hecho|parcial|bloqueado`.
- `Evidencia:`: enlaces, SHA, pruebas o decisiones verificables.
- `Siguiente responsable:`: rol, externo o ninguno.
- `Siguiente paso:`: una acción concreta o ninguno.
- `Bloqueo actual:`: motivo o ninguno.
- `Responsable del desbloqueo:` y `Condición para reanudar:`, o no aplica.

`hecho` significa que terminó la asignación, no que la entrega esté cerrada.
Las subtareas enlazan la issue madre; cualquier resultado que afecte a su
avance se referencia también en la madre. El orquestador deja en coordinación
un enlace a cada asignación y resultado para reconstruir la ejecución.

## Tipos, preparación y estado

Cada issue contiene `Tipo:`, con uno de estos valores:

- `funcional`: funcionalidad o cambio técnico que afecta al sistema.
- `documental`: documentación o producto versionado independiente.
- `auditoria`: informe de calidad o seguridad.
- `subtarea documental`: documentación incluida en una entrega funcional.
- `coordinacion`: alcance y registro de la ejecución.

Product Manager crea y prepara las issues de trabajo. El orquestador puede
crear y mantener únicamente la issue de coordinación, sin gestionar estados
de las entregas. Las issues en refinamiento usan `Preparación: pendiente`;
no tienen estado operativo hasta cumplir los requisitos de entrada.
Las listas usan `Preparación: lista` y `Estado operativo: nuevo`.

Una issue lista incluye `Backlog:`, `Descripción:`, `Prioridad:`,
`Criterios de aceptación:` y `Dependencias:`. Las funcionales de producto
incluyen además `Historia de usuario:` y `Caso de uso:`; en cambios técnicos,
el origen y la justificación sustituyen esos dos campos. Las subtareas indican
`Entrega madre:` y heredan su prioridad salvo una excepción justificada.

El único estado operativo oficial está en el cuerpo de la issue. Los únicos
valores son `nuevo`, `en desarrollo`, `listo para qa`,
`listo para revision`, `no validado`, `validado` y `cerrado`.
La coordinación usa `Situación: activa|bloqueada|completada|limite`, no
estados de entrega. Un bloqueo no sustituye al estado del trabajo.

### Transiciones y responsables

| Tipo | Autor | Revisor | Integrador |
| --- | --- | --- | --- |
| Funcional | Desarrollo | QA | Desarrollo |
| Documental | Doc Teams | Producto | Doc Teams |
| Auditoría | Auditor | Producto | Auditor |
| Subtarea documental | Doc Teams | QA con la madre | Desarrollo con la madre |

El autor establece `en desarrollo` al iniciar o retomar. Entrega las funcionales
en `listo para qa` y los otros tipos en `listo para revision`.

Producto establece `nuevo` al preparar cada issue. En los circuitos de revisión,
el revisor indicado establece `validado` o `no validado`. El autor retoma un
rechazo con `en desarrollo` y vuelve a entregar para su revisión. Producto
puede redactar cambios funcionales de producto en una issue o propuesta;
Doc Teams prepara sus cambios versionados en la PR documental.

Una subtarea documental en `listo para revision` significa que su contenido
está preparado en la PR de la madre, no que esté integrado ni cerrado.
QA valida o rechaza la subtarea y la madre en su revisión conjunta; si rechaza
solo la implementación, conserva la aprobación documental mientras su
contenido no cambie. No exige cerrar la subtarea para validar la madre.

Solo Product Manager cierra issues de trabajo. Confirma aprobación del revisor,
integración y criterios de aceptación; cierra primero las subtareas y luego
la madre. Las documentales y auditorías no requieren QA funcional.
El orquestador cierra la coordinación cuando Producto confirme el objetivo.

### Escrituras y recuperación

Para una transición, el responsable:

1. Relee el cuerpo y confirma el estado de origen y la evidencia.
2. Publica el resultado con `Transición propuesta: <origen> → <destino>`.
3. Actualiza únicamente sus campos en el cuerpo, conservando los demás.
4. Relee y confirma la actualización; si falla, deja la operación pendiente.

El comentario no cambia por sí mismo el estado. Si una interrupción deja solo
el resultado, el orquestador devuelve la asignación al responsable para
completar la transición sin repetir el trabajo. Si el cuerpo indica una
aprobación sin evidencia válida, no se integra ni cierra: se solicita al
revisor reconciliarla. Nunca se considera suficiente el texto del estado.

`cerrado` debe coincidir con la issue cerrada en GitHub. Producto actualiza el
campo y cierra en GitHub; al recuperar una interrupción completa la operación
pendiente. Si GitHub la cerró antes de cumplir requisitos, Producto la reabre
y restaura el último estado respaldado por evidencia.
No uses palabras de cierre automático en PR: enlaza mediante `Refs #<issue>`.
Un cambio de alcance posterior al cierre se gestiona en otra issue.

## Capacidad y bloqueos

Hay una entrega activa por defecto. Sus subtareas, revisiones, correcciones e
integración cuentan como parte de ella. Tener una rama no equivale a capacidad.
Solo se inicia otra entrega si la activa depende de un bloqueo externo
registrado y no existe ningún paso interno que permita avanzar.
Nunca hay dos agentes ejecutándose a la vez en el mismo repositorio.

Antes de delegar, el orquestador consulta en el cuerpo `Bloqueo actual:`,
`Responsable del desbloqueo:`, `Condición para reanudar:`,
`Siguiente responsable:` y `Siguiente paso:`. El agente saliente mantiene
estos campos además del comentario de resultado. Ninguno es otro estado.
Un bloqueo técnico va a Desarrollo, uno funcional a Producto y uno de acceso
o decisión fuera del alcance a su responsable externo.

El backlog `docs/sdd/02-product-backlog.md` se crea cuando sea útil. Contiene
alcance, prioridad, dependencias y enlaces; no copia estados operativos.
Los elementos sin issue pueden tener estado de refinamiento. Toda issue de
trabajo se vincula al backlog; coordinación queda fuera. Producto agrupa las
actualizaciones pendientes en una entrega documental, evitando una PR por
transición. No exige integrar el backlog para empezar una issue ya lista.

## Git, validación e integración

Cada entrega tiene una rama y una PR hacia `main`, nacidas del `main` remoto
actualizado. Desarrollo mantiene las ramas técnicas
`feat/<issue>-<resumen>`, `fix/<issue>-<resumen>` o
`chore/<issue>-<resumen>`. Doc Teams usa `docs/<issue>-<resumen>`;
los auditores, `chore/<issue>-auditoria-<resumen>`.
Las subtareas de una misma entrega comparten su rama y PR.

Los commits están en español y empiezan por `[<rol>]`. No se añaden cambios
ajenos. Cada PR enlaza su issue, explica el resultado e incluye verificación.
Se integra por squash, se registra el SHA integrado en la issue y después se
borra únicamente la rama de la entrega. Si existe `changelog/`, se añade como
máximo una entrada relevante en esa PR, nunca un commit administrativo aparte.

Antes de entregar, el autor sincroniza con `main`, resuelve conflictos y
registra `Commit a validar:` y `Base main a validar:` completos.
QA y los revisores documentales comprueban esos SHA contra la PR y el remoto.
Si la base avanzó antes de revisar, el autor prepara una nueva entrega; QA
registra un bloqueo operativo y no atribuye al producto un defecto inexistente.

Antes de integrar, el integrador comprueba:

1. La aprobación corresponde al SHA actual de la PR. Cualquier cambio en su
   contenido después de aprobar requiere nueva revisión, incluida documentación.
2. No hay conflictos, bloqueos de seguridad ni comprobaciones requeridas fallidas
   o pendientes. Se respetan las protecciones de la rama sin omitirlas.
3. Si avanzó `main`, sincroniza y repite verificación. Si el avance y la
   sincronización son exclusivamente documentales, sin efecto en lo validado,
   puede conservar la aprobación, registrando los SHA anterior y nuevo y la
   evidencia de equivalencia. Todo cambio que pueda afectar al comportamiento
   exige nueva validación. Esta es la única excepción al punto 1.
4. Integra usando una comprobación del SHA esperado cuando la API lo permita.
   Si la PR o la base cambian durante la operación, vuelve a comprobar antes
   de reintentar; no fuerza la integración.

Si se necesita repetir QA, Desarrollo devuelve la entrega a `en desarrollo`
y publica otro handoff antes de `listo para qa`. Para entregas documentales
o auditorías hace lo equivalente su autor hacia `listo para revision`.
Una aprobación antigua queda como historial y no autoriza la nueva versión.

Los agentes trabajan preferentemente en un worktree de la entrega, cuya ruta
registran en la issue. Doc Teams reutiliza el de la madre cuando corresponda.
QA puede crear un checkout o worktree aislado y separado de la rama, en el SHA
exacto a validar, y ejecutar allí las pruebas sin publicar cambios.
No necesita que exista un entorno de PR. El handoff incluye arranque, datos
de prueba y configuración necesaria sin secretos.

El checkout principal se conserva en su rama inicial; no se fuerza un cambio
a `main` con cambios ajenos. No se borran worktrees con cambios pendientes.
Si el arranque encuentra trabajo local sin identificar, el orquestador registra
el bloqueo y lo deriva antes de permitir cambios que puedan incorporarlo.

## Auditorías y seguridad

Se audita por un riesgo identificable: autenticación, permisos, privacidad,
dependencias, configuración sensible o indicios de deuda estructural.
No se repite una auditoría del mismo alcance y SHA sin evidencia nueva.
Cada informe tiene su issue y se enlaza desde la entrega afectada.
Los hallazgos compartidos entre auditores usan un único identificador y origen.

Un hallazgo de seguridad `critica` o `alta` aplicable a una entrega bloquea su
integración. Security Auditor registra el bloqueo en esa issue. Producto
prioriza y Desarrollo corrige; Security Auditor verifica la corrección en el
SHA nuevo y levanta el bloqueo con evidencia antes de QA e integración.
Los demás hallazgos se priorizan por riesgo; QA puede bloquear un riesgo
inmediato verificable, no una preferencia de diseño fuera de alcance.

No se publican secretos ni datos personales en los informes. Si revelar un
hallazgo facilita su explotación, usa el canal privado autorizado del
repositorio y deja solo una referencia no sensible en la issue. Si no existe
ese canal, registra el bloqueo sin detalles explotables y escala al responsable.
Los agentes no realizan pentesting de red ni gestionan producción.
