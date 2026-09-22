# Propuesta: repetir comidas en el calendario

## Intento

Permitir que las personas planifiquen una comida de texto libre que se repita semanalmente sin tener que crear manualmente cada asignación. Esto avanza el objetivo de reducir la improvisación en la planificación doméstica, conservando el calendario único compartido por todos los usuarios.

## Alcance

### Comportamiento de producto

- El editor del calendario permitirá configurar repetición tanto al crear una comida como al editar una existente.
- Las únicas opciones de frecuencia serán: **No repetir**, **Cada semana**, **Cada 2 semanas**, **Cada 3 semanas** y **Cada 4 semanas**.
- La fecha elegida inicialmente será la primera ocurrencia y determinará de forma inmutable el día de la semana de la regla.
- Una regla no tendrá fecha de finalización: las ocurrencias continuarán indefinidamente.
- Una edición o eliminación realizada sobre una comida recurrente actuará sobre toda la serie, incluidas sus ocurrencias pasadas y futuras.
- No se permitirá editar o eliminar una ocurrencia aislada.
- Varias comidas o series podrán coexistir en una misma fecha y franja (`lunch` o `dinner`); el calendario las conservará todas, sin reemplazos, avisos ni confirmaciones de conflicto.
- La recurrencia conservará `free_text` como tipo de comida. Para esta HU, la creación y modificación desde el calendario se limita a comidas de texto libre y no incluye selección ni vínculo de recetas.
- Las comidas no recurrentes existentes conservarán su comportamiento actual. Los registros históricos de receta, si existen, deberán seguir siendo legibles sin ampliar el alcance de selección de recetas.

### Persistencia y lectura

- Se añadirá una entidad o estructura persistente de regla de recurrencia, asociada al calendario compartido (`CALENDAR_KEY = "shared"`), con la fecha inicial, franja, frecuencia y texto libre normalizado.
- La base de datos almacenará una sola regla por serie; no se materializarán ni almacenarán asignaciones independientes para sus ocurrencias.
- La lectura semanal combinará las asignaciones no recurrentes existentes con las ocurrencias de reglas que pertenezcan al intervalo solicitado.
- Cada ocurrencia expuesta por la API deberá identificarse de forma que el cliente pueda solicitar la edición o eliminación de su serie, sin confundirla con una asignación individual.
- Crear o actualizar una comida con repetición persistirá o actualizará la regla correspondiente. Elegir **No repetir** mantendrá o convertirá el elemento en una asignación individual, según el flujo de edición definido en la especificación posterior.

## Áreas afectadas

| Área | Impacto previsto |
| --- | --- |
| `backend/migrations/` | Migración para la estructura de reglas recurrentes y sus restricciones. |
| `backend/src/comemos_en_casa/meal_calendar/` | Validación de frecuencias, modelo de dominio, repositorio de reglas, expansión por intervalo, y contratos CRUD/lectura de la API. |
| `backend/tests/meal_calendar/` | Pruebas deterministas de migración, validación, expansión, convivencia, CRUD de serie y compatibilidad de asignaciones individuales. |
| `frontend/src/types.ts`, `frontend/src/api.ts`, `frontend/src/calendarReducer.ts`, `frontend/src/App.tsx` | Tipos y llamadas de recurrencia, estado del editor y controles para crear, editar y borrar series de texto libre. |
| `frontend/src/App.test.tsx` | Flujos visibles de frecuencia y comportamiento de edición/eliminación de toda la serie. |

## Límites y no objetivos

- No se implementará ni se completará la selección, asociación, búsqueda o edición de recetas desde el calendario.
- No se añadirán reglas con fecha de fin, número máximo de repeticiones, días de semana alternativos ni frecuencias distintas de una a cuatro semanas.
- No se persistirán ocurrencias generadas ni se ofrecerá CRUD por ocurrencia.
- No habrá detección, prevención, reemplazo ni confirmación de conflictos entre comidas en la misma fecha y franja.
- No se cambiará el modelo de calendario compartido, permisos, autenticación o propiedad por familia/usuario.
- No se alterará el comportamiento de las asignaciones no recurrentes existentes fuera de la compatibilidad necesaria para mostrarlas junto a ocurrencias recurrentes.

## Impacto

- **Personas usuarias:** podrán repetir rápidamente comidas habituales y verlas en las semanas que correspondan; cualquier cambio de una serie tendrá alcance global y deberá comunicarse con claridad en la interfaz.
- **Datos:** se introduce una nueva fuente de datos de calendario. Las consultas semanales deberán fusionar resultados reales y virtuales sin duplicar ni ocultar asignaciones.
- **API y cliente:** los contratos actuales de `CalendarAssignment` y de escritura deberán evolucionar para distinguir una asignación individual de una serie y para dirigir mutaciones de una serie completa.
- **Operación:** la expansión se ejecutará en cada lectura de semana, por lo que debe estar acotada al intervalo de siete días y respaldada por índices y pruebas de rendimiento razonables.
- **Compatibilidad:** `meal_assignments` permanece como fuente de las comidas no recurrentes; los consumidores existentes deben seguir interpretando esas respuestas.

## Riesgos y cuestiones por resolver en especificación/diseño

1. **Conversión en edición:** debe definirse de forma explícita si editar una asignación individual y elegir una frecuencia crea una nueva serie y elimina la asignación original, y si elegir `No repetir` al editar una serie la convierte en una sola asignación en su fecha inicial. La propuesta reserva ese comportamiento para la especificación, sin contradecir que las mutaciones de una serie existente alcancen toda la serie.
2. **Identidad de ocurrencias:** las ocurrencias virtuales necesitan una identidad estable para que el cliente abra el editor correcto y la API aplique la mutación a la regla, no a una fila inexistente.
3. **Cambios de fecha o franja:** al editar una serie, mover la fecha inicial o la franja cambia todas las ocurrencias; el contrato debe definir si se permite y cómo se comunica, evitando un desfase entre el día original y la nueva regla.
4. **Eficiencia e integridad:** la consulta semanal debe expandir solo reglas candidatas del calendario compartido y ordenar de forma determinista junto a asignaciones individuales, incluso con series antiguas e indefinidas.
5. **Datos históricos de receta:** la restricción de texto libre para esta HU no debe dejar ilegibles las asignaciones de receta que ya existan; el diseño debe precisar la presentación de solo lectura y evitar nuevos vínculos de receta.

## Estrategia de reversión

La migración y las rutas nuevas se diseñarán para ser aditivas. Una reversión de aplicación dejará las reglas persistidas sin expandirlas, mientras que `meal_assignments` y sus lecturas actuales seguirán intactos. La reversión completa requerirá una migración posterior que elimine las reglas únicamente después de decidir el tratamiento de las series creadas, pues no existen ocurrencias materializadas que recuperar.

## Criterios de éxito

1. Una persona puede crear una comida de texto libre con cualquiera de las cinco opciones de frecuencia y la ve en la semana inicial y en cada semana que corresponda.
2. La primera ocurrencia coincide con la fecha seleccionada y todas las posteriores conservan su día de la semana y su intervalo de una, dos, tres o cuatro semanas.
3. La lectura semanal muestra juntas y en orden determinista las asignaciones individuales y todas las ocurrencias aplicables, incluidas varias en la misma franja.
4. Editar o eliminar una serie desde cualquier ocurrencia actualiza o elimina la serie completa, sin ofrecer una mutación aislada.
5. Las comidas no recurrentes existentes continúan funcionando y los flujos de calendario de esta HU no permiten crear vínculos nuevos con recetas.
6. Las pruebas cubren la migración, límites de semana, frecuencias, texto libre, mutaciones de serie, coexistencia y compatibilidad de asignaciones individuales.

## Propuesta question round

Las decisiones de producto proporcionadas están confirmadas; por ello no se abre una nueva ronda de preguntas. Los cinco riesgos anteriores son precisiones de contrato y diseño que la siguiente fase debe resolver sin ampliar el alcance ni reinterpretar las decisiones aprobadas.
