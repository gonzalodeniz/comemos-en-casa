# Acceso Guest y Protección Specification

## Purpose

Regular el acceso configurable al calendario compartido y limitar el abuso sin alterar el alcance de identidad acordado.

## Requirements

### Requirement: Configuración de acceso guest al arranque

El backend MUST leer `ENABLE_GUEST_USER` una sola vez al iniciarse. El valor `true` MUST habilitar acceso guest y el valor `false` o la ausencia de la variable MUST deshabilitarlo. Un cambio de la variable MUST requerir reiniciar el backend para tener efecto.

#### Scenario: Habilitación guest tras reinicio

- GIVEN que el backend se inició con `ENABLE_GUEST_USER=false`
- WHEN la variable se cambia a `true` y el backend se reinicia
- THEN una visita anónima puede acceder al calendario

#### Scenario: Variable ausente

- GIVEN que el backend se inicia sin `ENABLE_GUEST_USER`
- WHEN una visita anónima solicita el calendario
- THEN no se le concede acceso guest

### Requirement: Modelo de calendario compartido en guest

Cuando `ENABLE_GUEST_USER=true`, el sistema MUST permitir que cualquier visita anónima lea, cree, modifique y borre asignaciones en un único calendario público compartido, incluidas las creadas por otras visitas. El sistema MUST NOT crear calendarios por dispositivo, aislamiento entre visitantes, propiedad de entradas, roles, permisos, cuentas anónimas aisladas, historial ni atribución de autoría.

#### Scenario: Visitante modifica una asignación de otra visita

- GIVEN que una visita anónima crea una asignación en el calendario guest
- WHEN una segunda visita anónima abre la misma semana y modifica o elimina esa asignación
- THEN el cambio se permite en el único calendario compartido

### Requirement: Acceso con guest deshabilitado

Cuando `ENABLE_GUEST_USER=false`, la feature MUST requerir el acceso definido por la dependencia externa issue #6. La feature MUST NOT implementar una pantalla de login alternativa ni redefinir el sistema de autenticación.

#### Scenario: Invitado deshabilitado sin login disponible

- GIVEN que `ENABLE_GUEST_USER=false` y el acceso de la issue #6 no está disponible
- WHEN una visita anónima intenta abrir el calendario
- THEN no obtiene acceso guest y la feature no presenta un login alternativo

### Requirement: Banner persistente de calendario público

Mientras `ENABLE_GUEST_USER=true`, el sistema MUST mostrar a todas las personas, incluida una visita durante la carga inicial, un banner persistente, no descartable y con espacio reservado en el layout. El banner MUST contener exactamente: `El modo guest está activo: este calendario es público y compartido. Cualquier persona puede ver y cambiar las asignaciones.` El banner MUST NOT superponerse ni ocultar la cuadrícula. Cuando guest está deshabilitado, el banner MUST NOT mostrarse.

#### Scenario: Banner visible durante la primera carga guest

- GIVEN que `ENABLE_GUEST_USER=true` y una visita abre el calendario por primera vez
- WHEN se muestra el estado de carga inicial
- THEN el banner exacto ya está visible, no ofrece cierre y no tapa el skeleton ni la cuadrícula

### Requirement: Límites de solicitudes por IP

El sistema MUST aplicar rate limiting por dirección IP y por intervalo de un minuto a todo el tráfico de la feature, autenticado o anónimo. MUST permitir como máximo 60 lecturas y 30 escrituras por IP en cada intervalo; altas, ediciones y bajas MUST clasificarse como escrituras. El sistema MUST NOT incorporar CAPTCHA ni otra protección antiabuso adicional como parte de esta feature.

#### Scenario: Límite de lecturas autenticadas

- GIVEN que una misma IP autenticada ya ha realizado 60 lecturas en el intervalo actual de un minuto
- WHEN realiza una lectura adicional del calendario
- THEN la lectura adicional queda limitada

#### Scenario: Límite de escrituras guest

- GIVEN que una misma IP guest ya ha realizado 30 altas, ediciones o bajas en el intervalo actual de un minuto
- WHEN intenta otra escritura
- THEN la escritura adicional queda limitada

### Requirement: Feedback de rate limiting

Al limitar una solicitud, el sistema MUST mostrar el toast neutral exacto `Has superado el límite de solicitudes. Inténtalo de nuevo en un minuto.` El feedback MUST estar disponible en los flujos de lectura y escritura, tanto guest como autenticados.

#### Scenario: Toast al superar un límite

- GIVEN que una solicitud de la feature supera su límite por IP
- WHEN el sistema la rechaza por rate limiting
- THEN muestra el toast exacto en español neutro
