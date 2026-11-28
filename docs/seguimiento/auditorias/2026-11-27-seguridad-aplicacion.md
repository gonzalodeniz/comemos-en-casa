# Auditoría de seguridad de Comemos en casa · 27 de noviembre de 2026

**Revisión:** `4272485`, rama `main`. **Resultado:** 1 hallazgo crítico, 5 altos y 9 medios. Las cabeceras incluyen una huella estable para su seguimiento.

**Primera medida recomendada:** suspender la subida y restauración web de copias no autenticadas en origen. Mantener una vía de recuperación operativa y ensayada fuera de la aplicación. No es necesario suspender la creación de copias para contener el hallazgo crítico.

## Alcance y criterio

Revisión estática local de rutas FastAPI, autenticación, persistencia, tratamiento de imágenes y copias, frontend React, Dockerfiles, Compose y Nginx. Se contrastaron las rutas de escritura con sus dependencias y las decisiones de producto con el comportamiento de la API. Las referencias son rutas y líneas relativas a la raíz en la revisión indicada. No se accedió al despliegue, bases, credenciales, copias ni registros reales; no se ejecutaron ataques, pruebas de carga ni suites funcionales. No se realizó un análisis de CVE sobre imágenes o paquetes instalados.

Clasificación según [OWASP Top 10:2025](https://owasp.org/Top10/2025/). La severidad expresa impacto y condiciones necesarias en **esta** aplicación, no la posición de la categoría OWASP ni una puntuación CVSS. Se distingue entre fallos del código, riesgos de decisiones explícitas y efectos que dependen del entorno. Ningún hallazgo demuestra un incidente.

## Hallazgos, de mayor a menor severidad

### 01 · Crítica · Se interpreta una copia subida como instrucciones de confianza — `backup/untrusted-restore` · A08, A05

**Evidencia.** En `backend/app/backups.py:95–125`, el archivo se acepta comprobando nombre, presencia de `database.sql` e integridad ZIP, sin autenticar quién lo generó. En las líneas 78–92, 209–246, una cuenta activa puede restaurarlo: el servidor entrega su contenido a `psql` con las credenciales del servicio. El filtro de una directiva de compatibilidad y la transacción no son controles de confianza. [PostgreSQL advierte del riesgo de restaurar volcados no confiables](https://www.postgresql.org/docs/current/app-pgdump.html).

**Impacto.** Una sola cuenta familiar comprometida puede introducir instrucciones ajenas al proceso legítimo de copia. El alcance no se limita a sustituir comidas e imágenes: incluye los permisos del cliente de restauración y del rol de base de datos. No se verificó acceso al host.

**Acción y cierre.** Bloquear la importación no autenticada en origen. Para reimportar copias propias, firmarlas al generarlas y verificar firma, versión y procedencia antes de interpretar contenido; conservar la clave fuera del archivo. Para intercambiar datos de terceros, usar un formato de datos con esquema cerrado, no SQL. Validar en un entorno aislado que una copia alterada se rechaza **antes** de invocar el restaurador y que una legítima sigue recuperándose.

### 02 · Alta · La API comparte la identidad de inicialización de PostgreSQL — `db/runtime-superuser` · A02

**Evidencia e impacto.** `docker-compose.yml:45–49,72–80` asigna el mismo usuario a la API y a la inicialización de PostgreSQL; `backend/app/database.py:12–24` lo usa para peticiones ordinarias. En un volumen nuevo, la [imagen oficial](https://hub.docker.com/_/postgres) crea ese usuario como superusuario. Los privilegios efectivos de un volumen preexistente no se inspeccionaron. Un fallo de la API puede, por tanto, afectar a todo el clúster y no solo a sus tablas.

**Acción y cierre.** Separar inicialización, migraciones, restauración y ejecución diaria; retirar las credenciales administrativas del entorno web. Verificar que el rol de la API puede realizar las operaciones normales, pero no crear roles ni administrar otras bases.

### 03 · Alta · Una cuenta familiar controla identidades y copias de todo el hogar — `auth/shared-administration` · A01, A06

**Evidencia e impacto.** `backend/app/auth.py:816–881,893–921,935–968` permite modificar el correo, eliminar otra cuenta o cambiar su contraseña sin verificar al titular. `backend/app/backups.py:37–89,143–154,194–206` permite descargar un volcado global sin cifrado propio y borrar copias. Contiene, entre otros datos, correos y hashes de contraseñas. Es un **riesgo de diseño**, no un incumplimiento de HU-001: tanto [la historia](../../historias-usuarios/HU-001-gestion-de-usuarios.md) como [el alcance de copias](../../product/copias-de-seguridad/contexto.md) conceden estos permisos deliberadamente. Compartir comidas no exige compartir la capacidad de tomar cuentas o destruir su recuperación.

**Acción y cierre.** Mantener compartidos los catálogos y separar permisos de titular, administración familiar y custodia de copias. Exigir autenticación reciente para acciones sensibles y conservar una copia independiente, cifrada y no borrable por la API. Verificar una matriz de permisos con dos miembros y un custodio.

### 04 · Alta · Una instalación nueva puede quedar en manos de la primera persona que acceda — `auth/bootstrap-ownership` · A07

**Evidencia e impacto.** `backend/app/auth.py:538–564` anuncia si faltan cuentas y acepta el alta si la tabla está vacía y el origen es admisible. El bloqueo evita dos primeras cuentas, pero no acredita al operador. Si la API se publica antes del alta legítima, la primera cuenta obtiene las facultades del hallazgo 03. Una instancia inicializada no tiene esta ventana.

**Acción y cierre.** Aprovisionar la primera cuenta localmente antes de publicar, o exigir un secreto de instalación de un solo uso. Verificar que, incluso con la base vacía, conocer la URL y el origen esperado no autoriza el alta.

### 05 · Alta · Las cookies pierden la marca Secure detrás del proxy TLS — `session/proxy-secure-cookie` · A02, A04

**Evidencia e impacto.** `deploy/nginx/tls.conf:39–55` termina TLS y reenvía por HTTP; `backend/Dockerfile:15` desactiva las cabeceras de proxy. `backend/app/auth.py:499–518` decide la marca Secure según el esquema que ve Uvicorn. Con esa combinación, la sesión y la cookie CSRF se emiten sin Secure. Una petición HTTP al mismo host podría enviar la sesión **antes** de recibir la redirección; el riesgo de interceptación depende de la red y de las políticas HTTPS del navegador.

**Acción y cierre.** Forzar Secure por configuración de producción y dejar HTTP como excepción explícita de desarrollo. No confiar indiscriminadamente en cabeceras reenviadas. Comprobar los dos encabezados Set-Cookie desde el punto de entrada TLS; mantener HttpOnly en la cookie de sesión.

### 06 · Alta · Restaurar una copia puede reactivar credenciales revocadas — `backup/auth-state-rollback` · A07, A08

**Evidencia e impacto.** El volcado y la restauración son globales (`backend/app/backups.py:194–206,227–257`); incluyen sesiones y tokens de recuperación (`backend/app/models.py:68–111`). No hay invalidación posterior. Incluso una copia legítima puede deshacer un cierre de sesión, un cambio de contraseña o una desactivación. Una cookie anterior aún en posesión de alguien podría volver a ser válida si el vencimiento original no ha pasado (`backend/app/auth.py:193–239`).

**Acción y cierre.** Excluir sesiones y tokens de recuperación de la copia o invalidarlos antes de reabrir el servicio. Conciliar cuentas desactivadas y cambios de credenciales posteriores al punto recuperado. Añadir una prueba de recuperación que conserve los datos familiares sin recuperar la validez de una credencial revocada.

### 07 · Media · Los límites de acceso identifican al proxy, no al cliente — `auth/proxy-rate-limit` · A07

**Evidencia e impacto.** `backend/app/auth.py:53–60,288–314,317–345,590–598` cuenta fallos por IP y por cuenta/IP. Con `--no-proxy-headers` y la topología de 05, los clientes del mismo proxy comparten su IP. Cinco fallos en quince minutos pueden bloquear el acceso de otros miembros de la familia durante quince minutos, aun con contraseña correcta. La recuperación también usa la IP (línea 1006).

**Acción y cierre.** Aplicar el límite por IP real en el proxy, o transmitirla desde un proxy inequívocamente autorizado que sobrescriba las cabeceras del cliente. Mantener protección por cuenta. Verificar que dos clientes distintos no agotan el mismo cupo por IP y que una cabecera aportada por el cliente no cambia su identidad.

### 08 · Media · La importación de copias carece de presupuesto de descompresión — `backup/resource-limits` · A06, A10

**Evidencia e impacto.** `backend/app/backups.py:104–121,231–245` limita a 1 GiB los bytes recibidos, no los expandidos, el número de entradas ni el almacenamiento acumulado. La comprobación completa del ZIP se ejecuta en una función asíncrona sin salir del hilo del bucle. Durante la subida se mantiene además el bloqueo global que comparten las escrituras (`backend/app/main.py:91–97`). Una cuenta activa puede perjudicar la disponibilidad por CPU, disco o espera; no se ha medido el umbral real.

**Acción y cierre.** Limitar entradas, bytes expandidos reales, duración y cuota total. Validar fuera del bucle y tomar el bloqueo solo para publicar el resultado. Verificar con límites pequeños en pruebas que el rechazo libera temporales y que una importación no bloquea un inicio de sesión independiente.

### 09 · Media · La restauración puede dejar base e imágenes en estados diferentes — `backup/partial-cutover` · A10

**Evidencia e impacto.** `backend/app/backups.py:245–257` aplica primero la base y después elimina y reemplaza directorios uno a uno. Un error de disco o permisos puede dejar la base nueva con imágenes antiguas o ausentes; el error de las líneas 87–92 no revierte los cambios. Es un riesgo residual previsto en [HU-012](../../historias-usuarios/HIT-002-copias-de-seguridad/HU-012-restaurar-copia-de-seguridad.md).

**Acción y cierre.** Preparar y verificar base y archivos en destinos independientes antes del cambio, guardar el estado anterior y definir una reversión comprobada. Simular un fallo de almacenamiento en una prueba aislada y verificar que solo se publica un conjunto coherente.

### 10 · Media · El secreto de recuperación viaja en la URL que reciben los servidores — `auth/reset-token-in-url` · A07, A09

**Evidencia e impacto.** `backend/app/auth.py:1024–1039` añade el token a la consulta; `frontend/src/App.tsx:106–115,224–228` limpia la URL solo al confirmar. La petición inicial ya llega al proxy y al frontend. No se define redacción en las rutas web de `deploy/nginx/tls.conf` ni `frontend/nginx.conf`; el [formato de acceso habitual de Nginx](https://nginx.org/en/docs/http/ngx_http_log_module.html) incluye la petición. Quien lea ese registro a tiempo podría recuperar la cuenta. No se consultaron logs ni se constató una fuga.

**Acción y cierre.** Entregar el token en el fragmento de la URL, retirarlo de la barra al leerlo y enviarlo únicamente en el cuerpo de confirmación sobre HTTPS. Excluir secretos de trazas y referencias. Verificar con un marcador ficticio que no aparece en los logs de ninguna capa.

### 11 · Media · Cambiar credenciales no invalida todos los enlaces de recuperación — `auth/reset-token-lifecycle` · A07

**Evidencia e impacto.** `backend/app/auth.py:1024–1035,1054–1084` permite varios tokens y consume únicamente el presentado. Cambiar contraseña o correo (líneas 867–879, 965–968) tampoco revoca los enlaces anteriores. El poseedor de un enlace aún vigente podría revertir la recuperación del titular durante la ventana restante, incluso tras cambiar el correo asociado.

**Acción y cierre.** Invalidar los tokens pendientes al cambiar correo o contraseña, al desactivar la cuenta y al completar una recuperación, dentro de la misma transacción. Verificar que tras usar un enlace, el otro ya no permite cambios.

### 12 · Media · El envío SMTP admite credenciales y enlaces sin TLS — `mail/optional-tls` · A04

**Evidencia e impacto.** `docker-compose.yml:53–58` desactiva STARTTLS por defecto para el entorno con Mailhog. En `backend/app/mailer.py:34–43,59–67`, desactivar TLS no impide autenticarse ni enviar el enlace de recuperación. **Condicional:** importa si se configura un relay real sobre una red no confiable sin cambiar ese ajuste; no se observó tráfico ni se verificó la configuración real.

**Acción y cierre.** Limitar SMTP sin TLS al perfil local sin credenciales. En producción exigir TLS verificado y rechazar una configuración insegura antes de enviar. Probar que se cancela el envío si el relay no ofrece el transporte requerido.

### 13 · Media · Tres escrituras de trucos omiten el control CSRF de la API — `csrf/kitchen-tip-writes` · A01

**Evidencia e impacto.** Crear, editar y borrar en `backend/app/kitchen_tips_api.py:29–58` solo exigen sesión; no llaman al control de origen y token de `backend/app/auth.py:166–190`. Una petición que llegue con la cookie se acepta sin demostrar la intención del usuario. SameSite=Lax, CORS y las restricciones del navegador para JSON, PATCH y DELETE reducen la exposición entre sitios; no se demuestra aquí un ataque desde un origen externo.

**Acción y cierre.** Aplicar la misma dependencia de escritura protegida a las tres rutas. Probar que cada una devuelve 403 y no cambia datos ante token ausente, token incorrecto u origen no permitido; conservar una prueba positiva.

### 14 · Media · Las compilaciones no fijan toda la cadena de suministro — `build/mutable-inputs` · A03

**Evidencia e impacto.** `backend/requirements.txt:1–11` contiene rangos; `backend/Dockerfile:1–7` instala sin archivo de bloqueo ni hashes. Los Dockerfiles y Compose referencian imágenes por etiquetas mutables, incluido Certbot con latest. Dos compilaciones del mismo commit pueden incorporar componentes diferentes. Esto es un riesgo de procedencia y reproducibilidad, **no** prueba de un paquete comprometido o una CVE presente. El frontend sí usa package-lock y npm ci.

**Acción y cierre.** Bloquear versiones transitivas y hashes de Python, fijar imágenes por digest, generar inventario de la imagen final y revisar actualizaciones periódicamente. Verificar que reconstruir el mismo commit resuelve los mismos componentes; fijar sin actualizar solo congelaría el riesgo.

### 15 · Media · Las operaciones administrativas no dejan un registro atribuible — `audit/admin-events` · A09

**Evidencia e impacto.** Los caminos de éxito al descargar, borrar y restaurar una copia (`backend/app/backups.py:54–92`) y al cambiar una contraseña ajena (`backend/app/auth.py:935–975`) no emiten un evento con actor, objeto afectado y resultado. Un log HTTP puede registrar la ruta, pero no acredita qué cuenta autorizó la acción. Ante una copia desaparecida o una cuenta modificada, la aplicación no permite reconstruir de forma fiable lo sucedido. No se descartó monitorización externa.

**Acción y cierre.** Registrar esos eventos fuera del alcance de borrado y restauración de la API, con fecha, identificadores internos, resultado y correlación; nunca incluir cookies, enlaces de recuperación ni contenido del volcado. Verificar que tanto una operación permitida como una denegada dejan un registro utilizable y que restaurar una copia no borra el historial.

## Cobertura y límites de la conclusión

Los identificadores cubren A01 (03, 13), A02 (02, 05), A03 (14), A04 (05, 12), A05 (01), A06 (03, 08), A07 (04, 06, 07, 10, 11), A08 (01, 06), A09 (10, 15) y A10 (08, 09). A05 se refiere a interpretar un volcado no confiable, no a una inyección demostrada en los filtros del catálogo. Se observaron controles útiles: hashes Argon2, tokens aleatorios persistidos como resúmenes y validación DNS con conexión a la IP validada para importar imágenes. No equivalen a una certificación del sistema.

**Pendiente de verificación operativa autorizada:** privilegios reales del rol desplegado, atributos efectivos de cookies, redacción y acceso a logs, TLS del relay, protección del almacenamiento de copias e inventario de versiones de producción. No es necesario esperar esa verificación para cerrar la entrada de copias no confiables.
