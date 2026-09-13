# Calendario Semanal Specification

## Purpose

Permitir consultar y recorrer un plan de comidas semanal consistente en cualquier fecha.

## Requirements

### Requirement: Semana actual y estructura del calendario

El sistema MUST abrir el calendario en la semana que contiene la fecha actual en la zona horaria `Europe/Canary`, con lunes como primer día y domingo como último. MUST mostrar el rango de fechas de esa semana y una cuadrícula con los siete días y los turnos fijos `Comida` y `Cena`.

#### Scenario: Apertura en la semana actual canaria

- GIVEN que la fecha actual en `Europe/Canary` pertenece a una semana concreta
- WHEN una persona abre el calendario
- THEN se muestra de lunes a domingo esa misma semana, su rango de fechas y los turnos Comida y Cena para cada día

### Requirement: Navegación semanal sin límites

El sistema MUST permitir navegar a cualquier semana anterior o posterior y volver a la semana actual mediante la acción `Hoy`. MUST NOT imponer límites temporales, mostrar festivos ni aplicar un resaltado especial a la semana actual.

#### Scenario: Consulta de una semana remota y retorno a hoy

- GIVEN que una persona está viendo una semana del calendario
- WHEN navega repetidamente a semanas anteriores o posteriores y selecciona `Hoy`
- THEN cada navegación solicitada queda disponible sin límite y `Hoy` muestra la semana actual de `Europe/Canary`

### Requirement: Acciones de alta contextual y global

El sistema MUST ofrecer una acción global llamada `+ Añadir comida` que permita elegir fecha y turno, y MUST ofrecer acciones directas de alta en cada celda de fecha y turno. El término global `Comida` MAY crear una asignación tanto en Comida como en Cena.

#### Scenario: Alta desde la acción global

- GIVEN que una persona visualiza una semana
- WHEN activa `+ Añadir comida` y escoge un día y el turno Cena
- THEN el flujo de alta queda dirigido a la celda de ese día y turno

#### Scenario: Alta desde una celda

- GIVEN que una persona visualiza la celda de Comida de un día
- WHEN activa la acción directa de la celda
- THEN el flujo de alta queda dirigido a esa fecha y al turno Comida

### Requirement: Contenido y orden de las celdas

El sistema MUST mostrar todas las asignaciones de cada fecha y turno, incluidas asignaciones duplicadas. MUST ordenar conjuntamente recetas y textos libres de forma alfabética por el texto visible de cada asignación.

#### Scenario: Recetas y textos repetidos en una misma celda

- GIVEN que una celda contiene recetas y textos libres, incluidos valores visibles repetidos
- WHEN se muestra la celda
- THEN se muestran todas las asignaciones sin deduplicarlas y en orden alfabético conjunto
