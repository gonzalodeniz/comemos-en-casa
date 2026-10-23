# HU-001 — Gestión de usuarios

**Épica:** Administración y acceso a la aplicación  
**Prioridad:** Alta  
**Estado:** Especificación aprobada; implementación pendiente  
**Módulo:** Usuarios

## 1. Descripción

**Como** miembro de la familia,  
**quiero** disponer de una cuenta de usuario con la que pueda identificarme y gestionar tanto mis datos personales como las cuentas de otros miembros de la familia,  
**para** acceder de forma segura a la aplicación «Comemos en casa» y colaborar en la administración de sus usuarios.

## 2. Objetivo

Permitir la creación, autenticación y gestión de cuentas de usuario, garantizando que únicamente los miembros autorizados de la familia puedan acceder a la aplicación.

Todos los usuarios registrados y activos tendrán los mismos permisos para gestionar las cuentas de los demás usuarios, sin distinción de roles.

## 3. Criterios de aceptación

### CA-01 — Registro de usuarios
- El sistema debe permitir crear usuarios mediante nombre, correo electrónico y contraseña.
- El correo electrónico debe tener un formato válido.
- No pueden existir dos usuarios con el mismo correo electrónico.
- La contraseña debe cumplir unos requisitos mínimos de seguridad.
- Cualquier usuario autenticado y activo puede registrar nuevos miembros de la familia y establecer su contraseña.
- Si el sistema no tiene usuarios, debe mostrar el formulario para crear la primera cuenta. Tras crearla, debe mostrar el formulario de inicio de sesión.
- No se permite el registro público cuando ya existe al menos un usuario.
- No se requiere verificar el correo electrónico.

### CA-02 — Inicio de sesión
- El usuario debe poder iniciar sesión mediante correo electrónico y contraseña.
- El sistema debe validar las credenciales introducidas.
- Si las credenciales son incorrectas, debe mostrar un mensaje de error genérico.
- Solo los usuarios autenticados y activos pueden acceder a las funcionalidades privadas de la aplicación.

### CA-03 — Protección contra ataques de fuerza bruta
- El sistema debe limitar los intentos fallidos de autenticación por dirección IP y por combinación de cuenta e IP.
- Tras cinco intentos fallidos para la misma combinación de cuenta e IP en quince minutos, debe rechazar temporalmente nuevos intentos para esa combinación durante quince minutos. No debe bloquear la cuenta para intentos procedentes de otras direcciones IP.
- Tras cinco intentos fallidos desde una misma dirección IP en quince minutos, el sistema debe rechazar temporalmente nuevos intentos desde esa IP durante quince minutos, para dificultar ataques contra múltiples cuentas.
- Las respuestas de autenticación no deben revelar si una cuenta existe, está limitada o tiene una contraseña incorrecta.
- El sistema debe registrar los intentos fallidos y las restricciones sin almacenar contraseñas ni otros secretos.
- Las restricciones deben finalizar automáticamente al expirar el período establecido.
- Los controles de seguridad deben ejecutarse en el servidor y no depender exclusivamente del navegador.

### CA-04 — Cierre de sesión
- El usuario debe poder cerrar su sesión en cualquier momento.
- Al cerrar sesión, el sistema debe invalidar la sesión activa.
- El usuario debe volver a autenticarse para acceder a las funcionalidades protegidas.

### CA-05 — Consulta y modificación del perfil
- Cualquier usuario autenticado y activo debe poder consultar los datos de los usuarios registrados.
- Cualquier usuario autenticado y activo debe poder modificar el nombre y correo electrónico de cualquier usuario.
- El sistema debe validar los datos modificados y rechazar un correo electrónico que ya esté asociado a otra cuenta.
- No se requiere verificar la propiedad del correo electrónico.
- Los cambios deben persistir correctamente.

### CA-06 — Cambio de contraseña
- El usuario autenticado debe poder cambiar su propia contraseña proporcionando la contraseña actual.
- La nueva contraseña debe cumplir los requisitos de seguridad establecidos.
- Cualquier usuario autenticado y activo puede cambiar la contraseña de otro usuario sin conocer la contraseña actual ni requerir verificación del titular.
- El sistema no debe almacenar contraseñas en texto plano.

### CA-07 — Recuperación de contraseña
- El usuario debe poder solicitar la recuperación de su contraseña mediante su correo electrónico.
- El sistema debe enviar por correo electrónico un enlace seguro para restablecer la contraseña.
- El enlace de restablecimiento debe ser de un solo uso y tener una validez limitada.
- El sistema no debe revelar si un correo electrónico está registrado.
- Las solicitudes de recuperación deben estar sujetas a limitación de frecuencia para evitar abusos.

### CA-08 — Control de acceso
- Solo los usuarios autenticados y activos pueden acceder a las funcionalidades de la aplicación.
- Todos los usuarios tienen los mismos permisos, sin distinción de roles.
- Los usuarios no autenticados deben ser redirigidos al inicio de sesión cuando intenten acceder a funcionalidades protegidas.
- Las operaciones de gestión de usuarios deben verificar la autenticación y el estado activo de quien las ejecuta.

### CA-09 — Gestión de usuarios
- Cualquier usuario autenticado y activo puede consultar el listado de usuarios registrados.
- Cualquier usuario autenticado y activo puede crear y modificar cuentas de otros usuarios.
- Cualquier usuario autenticado y activo puede activar o desactivar otras cuentas.
- No debe permitirse que un usuario desactive su propia cuenta.
- No debe permitirse desactivar ni eliminar la última cuenta activa.
- Un usuario desactivado no puede iniciar nuevas sesiones ni continuar utilizando sesiones anteriores.
- Se permite eliminar definitivamente una cuenta; al hacerlo, se eliminan permanentemente los datos de su perfil. Los datos compartidos no se eliminan automáticamente.

## 4. Reglas de negocio

**RN-01.** La aplicación está destinada exclusivamente a miembros de una misma familia.

**RN-02.** Cada usuario debe tener un identificador único.

**RN-03.** El correo electrónico debe ser único dentro de la aplicación.

**RN-04.** Las contraseñas deben almacenarse mediante mecanismos criptográficos seguros, adecuados para contraseñas.

**RN-05.** Un usuario no puede acceder a funcionalidades privadas sin autenticarse.

**RN-06.** No existen roles ni jerarquías de permisos entre usuarios.

**RN-07.** Todos los usuarios activos tienen los mismos permisos para administrar las cuentas de los demás usuarios.

**RN-08.** El registro de nuevos usuarios requiere la intervención de un usuario previamente autenticado y activo, salvo para la creación inicial cuando no existe ninguna cuenta.

**RN-09.** Un usuario no puede desactivar su propia cuenta ni dejar la aplicación sin usuarios activos, tampoco mediante una eliminación definitiva.

**RN-10.** La desactivación o eliminación de una cuenta no debe eliminar automáticamente las recetas, planificaciones o listas de la compra compartidas. La eliminación definitiva elimina los datos propios del perfil.

**RN-11.** El sistema debe aplicar mecanismos de protección contra intentos de acceso por fuerza bruta.

**RN-12.** Las restricciones temporales de autenticación no deben provocar la desactivación permanente de una cuenta.

**RN-13.** No se requiere verificación del correo electrónico.

## 5. Escenarios de prueba

### Escenario 1 — Inicio de sesión correcto

**Dado** que existe un usuario activo,  
**cuando** introduce correctamente su correo electrónico y contraseña,  
**entonces** el sistema inicia su sesión y le permite acceder a la aplicación.

### Escenario 2 — Credenciales incorrectas

**Dado** que un usuario intenta iniciar sesión,  
**cuando** introduce credenciales incorrectas,  
**entonces** el sistema rechaza el acceso y muestra un mensaje de error genérico.

### Escenario 3 — Protección contra fuerza bruta por cuenta e IP

**Dado** que se han producido cuatro intentos fallidos para la misma combinación de cuenta e IP durante los últimos quince minutos,  
**cuando** se produce un quinto intento fallido,  
**entonces** el sistema restringe durante quince minutos los intentos para esa combinación, sin impedir el acceso a esa cuenta desde otra IP.

### Escenario 4 — Finalización de la restricción temporal

**Dado** que una cuenta tiene una restricción temporal por intentos fallidos,  
**cuando** transcurren los quince minutos de restricción,  
**entonces** el sistema permite realizar nuevos intentos de autenticación.

### Escenario 5 — Creación de la primera cuenta

**Dado** que todavía no existen usuarios,  
**cuando** se abre la aplicación y se crea una cuenta con datos válidos,  
**entonces** el sistema muestra inicialmente el formulario de creación y, tras crear la cuenta, muestra el formulario de inicio de sesión.

### Escenario 6 — Registro de un familiar

**Dado** que un usuario activo ha iniciado sesión,  
**cuando** crea una cuenta para un nuevo familiar con datos válidos y establece su contraseña,  
**entonces** el sistema crea la cuenta y permite que el familiar acceda con esas credenciales.

### Escenario 7 — Gestión de otro usuario

**Dado** que existen dos usuarios activos,  
**cuando** uno modifica el nombre del otro,  
**entonces** el sistema guarda el cambio sin requerir permisos adicionales.

### Escenario 8 — Desactivación de otro usuario

**Dado** que existen al menos dos usuarios activos,  
**cuando** uno desactiva la cuenta del otro,  
**entonces** el sistema impide que la cuenta desactivada acceda a la aplicación, incluidas sus sesiones anteriores.

### Escenario 9 — Prevención de autodesactivación

**Dado** que un usuario ha iniciado sesión,  
**cuando** intenta desactivar su propia cuenta,  
**entonces** el sistema rechaza la operación.

### Escenario 10 — Prevención de ausencia de usuarios activos

**Dado** que solamente existe un usuario activo,  
**cuando** se intenta desactivar su cuenta,  
**entonces** el sistema rechaza la operación y mantiene la cuenta activa.

### Escenario 11 — Acceso sin autenticación

**Dado** que un visitante no ha iniciado sesión,  
**cuando** intenta acceder a una funcionalidad protegida,  
**entonces** el sistema le redirige a la pantalla de inicio de sesión.

### Escenario 12 — Correo electrónico duplicado

**Dado** que un correo electrónico ya está asociado a una cuenta,  
**cuando** se intenta asignarlo a otra cuenta,  
**entonces** el sistema rechaza el cambio y mantiene los datos existentes.

### Escenario 13 — Cambio de contraseña de otro usuario

**Dado** que dos usuarios están activos,  
**cuando** uno cambia la contraseña del otro,  
**entonces** el sistema guarda la nueva contraseña sin solicitar verificación al titular.

## 6. Dependencias

- Sistema de persistencia de datos.
- Servicio de autenticación y gestión de sesiones.
- Mecanismo de limitación de intentos de autenticación.
- Servicio de envío de correos electrónicos para recuperación de contraseñas.
- Mecanismo para mostrar la creación inicial de cuenta cuando aún no existen usuarios.

## 7. Consideraciones técnicas

- Utilizar identificadores internos independientes del correo electrónico.
- Almacenar las contraseñas mediante un algoritmo de derivación seguro, como Argon2id.
- Implementar controles de autenticación y autorización en el servidor.
- Proteger las sesiones frente a accesos no autorizados.
- Aplicar límites de intentos por combinación de cuenta e IP y por IP, con contadores compartidos y operaciones atómicas. La restricción por cuenta debe estar acotada a la combinación con la IP que originó los intentos fallidos, para que un tercero no bloquee el acceso desde otras IP.
- Considerar retardos progresivos y mecanismos de verificación adicionales ante patrones de acceso sospechosos.
- Registrar eventos de autenticación relevantes sin almacenar información sensible.
- Invalidar las sesiones cuando se desactive o elimine una cuenta.
- Garantizar mediante operaciones transaccionales que no pueda desactivarse la última cuenta activa.
- Eliminar permanentemente los datos propios del perfil al borrar una cuenta, preservando los datos compartidos.
- Crear la primera cuenta solo cuando no exista ningún usuario y dirigir luego al inicio de sesión.
- No realizar verificación de correo electrónico.

## 8. Definición de terminado (Definition of Done)

- [ ] Los criterios de aceptación están implementados.
- [ ] Las validaciones funcionan correctamente en cliente y servidor.
- [ ] Los escenarios de prueba se han ejecutado satisfactoriamente.
- [ ] Todos los usuarios activos disponen de los mismos permisos.
- [ ] Las rutas y operaciones protegidas requieren autenticación.
- [ ] Las contraseñas y sesiones se gestionan de forma segura.
- [ ] La protección contra fuerza bruta está implementada y probada.
- [ ] Se ha verificado la imposibilidad de desactivar la última cuenta activa.
- [ ] La funcionalidad está documentada.
- [ ] Los cambios han sido revisados e integrados en el proyecto.

## 9. Cuestiones pendientes

No hay cuestiones pendientes.
