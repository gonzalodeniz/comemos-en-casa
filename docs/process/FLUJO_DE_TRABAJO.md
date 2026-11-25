# Flujo de trabajo local con agentes

El seguimiento se realiza en archivos del repositorio, **sin GitHub, issues, PR ni milestones**. Este documento no autoriza por sí mismo implementar, delegar, hacer commits, desplegar ni acceder a servicios remotos. Prevalecen el usuario, `AGENTS.md`, las instrucciones de la sesión y los permisos efectivos. Los agentes no disponen de un sandbox independiente ni de los hooks de Claude.

## Fuentes y ubicación

- `docs/product-vision.md`, `docs/glosario.md`, `docs/historias-usuarios/` y `docs/product/`: visión, vocabulario, historias y backlogs.
- `docs/planes/`: planes y criterios; su mera creación no implica aprobación, como explica `docs/planes/README.md`.
- `docs/seguimiento/`: seguimiento local nuevo y hallazgos de auditoría.
- `odd/tasks/`: registros de tareas ya existentes. Se conservan y actualizan donde ya viven; no se duplican ni migran automáticamente. Cuando una iniciativa tenga un registro previo allí, este sigue siendo su fuente de seguimiento.
- `docs/manual/`, `README.md` y `docs/arquitectura.md`: documentación existente, que debe contrastarse con el código y sus evidencias.

## Roles

| Rol | Responsabilidad |
| --- | --- |
| `orquestador` | Coordina la tarea solicitada, comprueba el seguimiento y reúne resultados; no implementa ni valida. |
| `product-manager` | Refina historias o propone planes cuando se le solicita; no aprueba el alcance ni implementa. |
| `developer-teams` | Implementa únicamente el alcance expresamente autorizado, aporta pruebas y prepara el handoff. |
| `qa-teams` | Revisa de forma independiente criterios, cambios y pruebas; registra evidencia y defectos. |
| `doc-teams` | Actualiza la documentación pertinente según el comportamiento verificado. |
| `quality-auditor` y `security-auditor` | Auditan bajo petición expresa y registran hallazgos; no corrigen ni priorizan por su cuenta. |

Los roles son responsabilidades, no una obligación de lanzar agentes. Solo se crean subagentes cuando el usuario o las instrucciones aplicables lo autoricen expresamente. Sin autorización de delegación, el asistente principal atiende el trabajo permitido. No trabajar en paralelo sobre los mismos archivos.

## Del alcance a la ejecución

1. Identificar la historia o iniciativa solicitada y leer sus documentos y registros existentes. Si hay estados contradictorios, señalarlo y comprobar la evidencia; no elegir silenciosamente el más favorable.
2. Si hace falta, proponer un plan en `docs/planes/`. Solicitar su aprobación antes de ejecutarlo. Crear tareas no aprueba el plan ni autoriza implementar; seguir `docs/planes/README.md`.
3. Crear el seguimiento nuevo en `docs/seguimiento/<id>-<nombre>.md` solo tras aprobar el plan y recibir una solicitud expresa de tareas o autorización de implementación. Si el usuario pide expresamente un borrador antes de aprobar el plan, marcarlo como pendiente de aprobación y no implementar. Si ya existe un TASKS, usar ese archivo sin duplicarlo ni reescribir sus estados históricos.
4. Implementar solo cuando el usuario lo haya autorizado explícitamente y las dependencias estén satisfechas. Registrar cambios, comprobaciones y bloqueos en el seguimiento correspondiente. No tomar la existencia de un plan aprobado como autorización de ejecución.
5. Pasar a revisión con evidencia. QA verifica contra los criterios y registra `validado`, `no validado` o `pendiente de verificación`; no puede validar lo que no comprobó. Si hay defectos, devolver a desarrollo y repetir la revisión afectada.
6. Actualizar documentación cuando sea necesario. Comunicar al usuario el resultado, las limitaciones y las verificaciones manuales pendientes. La validación de QA no sustituye una aceptación explícita del usuario cuando esta sea necesaria.

## Estados de seguimiento nuevos

Usar estos estados en seguimientos nuevos, no como sustitución automática de estados existentes:

| Estado | Significado y transición |
| --- | --- |
| `pendiente` | Trabajo identificado; no implica aprobación ni autorización. |
| `en desarrollo` | Plan aprobado y ejecución autorizada expresamente; hay trabajo en curso. |
| `listo para revisión` | Implementación terminada para el alcance acordado, con evidencias y limitaciones registradas. |
| `no validado` | QA identificó defectos; vuelve a desarrollo tras autorización aplicable. |
| `pendiente de verificación` | Falta ejecutar o completar una comprobación necesaria; no equivale a aprobado. |
| `validado` | QA verificó los criterios y registró evidencia; no implica aceptación del usuario ni publicación. |
| `bloqueado` | Falta decisión, autorización o recurso; registrar causa y próximo paso. |
| `finalizado` | Alcance y documentación completados, validación suficiente y aceptación del usuario cuando corresponda. |

No inferir `validado` o `finalizado` por ausencia de errores. Cada cambio de estado debe acompañarse de fecha, responsable o rol, motivo y evidencia; si una verificación necesaria está pendiente, indicar la limitación sin ocultarla.

## Plantilla de seguimiento

```markdown
# Seguimiento — <ID y título>

- Historia o iniciativa: <enlace local>
- Plan: <enlace y estado de aprobación>
- Autorización de implementación: <confirmación y alcance, o pendiente>
- Estado: pendiente
- Dependencias: <enlaces o ninguna>

## Alcance y criterios
<Referencias a la historia y al plan; no duplicar requisitos sin necesidad.>

## Tareas
- [ ] <tarea verificable>

## Registro y handoff
### <fecha> — <rol>
- Estado y motivo: …
- Cambios y archivos: …
- Criterios cubiertos: …
- Pruebas: <comando, entorno, resultado o no ejecutada y motivo>
- Limitaciones y verificación manual pendiente: …
- Siguiente paso o bloqueo: …

## Revisión QA
- Resultado: <validado | no validado | pendiente de verificación>
- Criterios y evidencia: …
- Defectos y limitaciones: …
- Documentación afectada: …
```

Cuando se corrija un defecto, conservar los registros anteriores y añadir nueva evidencia, sin reescribir resultados históricos.

## Auditorías

Invocar auditores solo si se solicita. Crear, cuando haga falta, `docs/seguimiento/auditorias/<fecha>-<tipo>-<alcance>.md`; indicar alcance y revisión examinada, limitaciones, sospechas no comprobadas y, para cada hallazgo, severidad, ubicación, evidencia reproducible, impacto, recomendación y huella estable. Comprobar registros previos para evitar duplicados; actualizar el seguimiento cuando cambie la evidencia. Enmascarar secretos y no instalar herramientas ni consultar redes o credenciales sin autorización. Un hallazgo no autoriza su corrección ni establece automáticamente su prioridad.

## Preguntas y bloqueos

Si falta una decisión de producto, autorización o comprobación necesaria, anotar el bloqueo en el seguimiento e informar al usuario. Preguntar una sola cuestión cada vez y esperar. No convertir una suposición en decisión confirmada ni saltarse restricciones de permisos.

## Pruebas y seguridad

Seguir `COMMANDS.md` y `AGENTS.md`. Las pruebas backend con `TestClient`, `make test` y `make test-backend` requieren ejecución fuera del sandbox con aprobación; si no se autoriza, comunicarlo. Integración PostgreSQL solo con base y proyecto Compose nuevos y aislados. Registrar comandos, resultados y límites reales; no modificar datos que deban preservarse. Acceso remoto, publicación y uso de credenciales requieren autorización explícita previa para destino, operación y sesión o credencial.

## Ramas, commits y documentación

No crear ramas, hacer commits ni publicar salvo autorización explícita. Si se autorizan commits, usar Conventional Commits en español y sin atribución de IA. Actualizar documentación e índice cuando corresponda. Los cambios de producto, planes y ficheros protegidos siguen sujetos a las instrucciones del usuario y del repositorio.
