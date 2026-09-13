# Persistencia y Resiliencia Specification

## Purpose

Conservar el plan de comidas y dar feedback recuperable ante operaciones lentas, fallidas o concurrentes.

## Requirements

### Requirement: Persistencia compartida del calendario

El sistema MUST persistir las lecturas y las altas, cambios y bajas de asignaciones del calendario en PostgreSQL. Las asignaciones guardadas MUST sobrevivir a reinicios y poder consultarse desde otro dispositivo con el mismo acceso al calendario. El sistema MUST conservar los planes indefinidamente hasta que se elimine manualmente una asignación y MUST NOT limpiarlos automáticamente.

#### Scenario: Consulta desde otro dispositivo tras persistir

- GIVEN que una persona guarda una asignación en el calendario
- WHEN otra persona con acceso al mismo calendario abre la misma semana desde otro dispositivo tras un reinicio del servicio
- THEN la asignación guardada se muestra en esa fecha y turno

### Requirement: Guardado de cambios pendientes

El sistema MUST guardar cambios al perder el foco del campo y mediante un botón explícito `Guardar`. `Guardar` MUST incluir el campo que siga enfocado y MUST estar deshabilitado cuando no existan cambios pendientes. El sistema MUST evitar solicitudes duplicadas para una misma operación; si un valor cambia durante una solicitud, MUST volver a quedar pendiente para un guardado posterior.

#### Scenario: Guardar incluye el campo enfocado

- GIVEN que un campo modificado sigue enfocado y existen cambios pendientes
- WHEN una persona activa `Guardar`
- THEN se intenta guardar también el valor del campo enfocado y no se emite una solicitud duplicada para la misma operación

#### Scenario: Cambio durante un guardado en curso

- GIVEN que un valor se está guardando
- WHEN el valor cambia antes de que la operación termine
- THEN el nuevo valor queda pendiente para otro guardado después de finalizar la operación en curso

### Requirement: Feedback individual de guardado

El sistema MUST mostrar `Guardando` para cada operación individual mientras está en curso y MUST mostrar `Guardado` al completarse. El estado `Guardado` MUST desaparecer a los 2 segundos.

#### Scenario: Confirmación efímera de una operación guardada

- GIVEN que una operación individual se inicia correctamente
- WHEN la operación se completa
- THEN su feedback cambia de `Guardando` a `Guardado` y `Guardado` deja de mostrarse tras 2 segundos

### Requirement: Cambios no guardados y navegación

El sistema MUST solicitar confirmación antes de abandonar cambios no guardados de recetas o texto libre. Los controles de navegación MUST permanecer disponibles. Si existen guardados activos, el cambio de semana MUST esperar a que terminen antes de cargar la semana de destino.

#### Scenario: Salida con un cambio no guardado

- GIVEN que una persona tiene un cambio no guardado de receta o texto libre
- WHEN intenta abandonar ese contexto
- THEN se solicita confirmación antes de abandonar el cambio

#### Scenario: Navegación mientras se guarda

- GIVEN que se está guardando una asignación y una persona solicita otra semana
- WHEN la solicitud de guardado termina
- THEN se inicia la carga de la semana solicitada sin haber deshabilitado los controles de navegación

### Requirement: Carga semanal y continuidad visual

El sistema MUST mostrar un skeleton de la cuadrícula durante la carga inicial y en cada cambio de semana, incluso al revisitar una semana. MUST bloquear la edición durante la carga y mantener disponible la navegación. Al finalizar, MUST reemplazar el contenido por los datos de la semana cargada y SHOULD conservar visualmente los datos previos bajo un overlay o skeleton hasta recibirlos para evitar vacíos y saltos.

#### Scenario: Carga de una semana ya visitada

- GIVEN que una persona ya ha consultado una semana
- WHEN vuelve a navegar a ella
- THEN se muestra el skeleton, la edición queda bloqueada, la navegación sigue disponible y los datos de esa semana reemplazan el contenido al finalizar la carga

### Requirement: Reintentos y recuperación de fallos de datos

El sistema MUST detectar cada fallo de lectura, escritura o borrado al ejecutar la operación real en la capa de repositorio o servicio, y MUST NOT requerir un endpoint específico de health check. Para cada fallo, MUST realizar exactamente tres reintentos automáticos después de 250 ms, 500 ms y 1 s. Tras agotarlos, MUST mostrar el toast neutral exacto `No se pudo conectar con la base de datos. El cambio no se guardó. Inténtalo de nuevo.` con la acción `Reintentar`. `Reintentar` MUST repetir únicamente la operación fallida. Para una mutación fallida, el sistema MUST conservar el formulario y su valor; para una lectura fallida, MUST conservar el contenido semanal que estuviera visible, si lo hubiera.

#### Scenario: Escritura que agota los reintentos

- GIVEN que una edición de texto libre falla en cada intento de persistencia
- WHEN finalizan los reintentos con esperas de 250 ms, 500 ms y 1 s
- THEN se muestra el toast exacto con `Reintentar`, el formulario conserva el valor fallido y no se repite ninguna otra operación

#### Scenario: Reintento aislado de una lectura fallida

- GIVEN que la carga de una semana ha agotado sus reintentos
- WHEN una persona activa `Reintentar` en el toast
- THEN se repite solo la lectura de esa semana y no se reintenta ninguna mutación no relacionada

### Requirement: Cancelación de reintentos manuales al cambiar de semana

El sistema MUST cancelar un reintento manual pendiente al cambiar de semana sin descartar el formulario ni su valor conservado.

#### Scenario: Cambio de semana antes de reintentar

- GIVEN que una mutación fallida conserva su formulario y tiene un reintento manual pendiente
- WHEN una persona cambia de semana
- THEN el reintento manual pendiente no se ejecuta y el formulario conservado no se descarta

### Requirement: Plataforma de implementación futura

La futura implementación del backend del calendario MUST usar Python y sus pruebas backend MUST usar pytest una vez que exista un runner configurado. Esta especificación MUST NOT interpretarse como evidencia de que el repositorio actual tiene un runner o pruebas automatizadas ejecutables.

#### Scenario: Configuración futura del backend verificable

- GIVEN que comienza la implementación del backend del calendario
- WHEN se incorporan sus pruebas backend
- THEN el backend está implementado en Python, las pruebas usan pytest y no se declara validación automatizada antes de configurar el runner

### Requirement: Concurrencia de última escritura

El sistema MUST aplicar la regla de último guardado gana para modificaciones concurrentes. MUST NOT introducir bloqueo, historial, atribución de autoría, resolución avanzada de conflictos ni recuperación o deshacer de eliminaciones.

#### Scenario: Modificaciones concurrentes de la misma asignación

- GIVEN que dos personas modifican concurrentemente la misma asignación
- WHEN ambas modificaciones se guardan
- THEN el valor de la última operación guardada es el valor persistido sin aviso de conflicto ni historial
