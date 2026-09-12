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
