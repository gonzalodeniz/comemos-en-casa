# Manual de usuario

> La interfaz incorpora planificación semanal y mensual de comidas con etiquetas del catálogo predeterminado. HU-002 completó su verificación local: escenarios de navegador y registro/login/logout contra FastAPI y SQLite temporal. Esto no indica que la aplicación esté publicada ni sustituye la verificación PostgreSQL aislada.

## Acceso y cuentas

1. Abre la dirección de la aplicación que te haya proporcionado quien la instaló.
2. Si aún no hay cuentas, aparecerá **Crear la primera cuenta**. Introduce nombre, correo y contraseña (8–128 caracteres). Tras crearla, inicia sesión: el registro inicial no inicia sesión automáticamente.
3. En adelante, inicia sesión con correo y contraseña. Usa **¿Olvidaste tu contraseña?** para solicitar un enlace; el sistema muestra el mismo aviso exista o no la cuenta. Si el correo está configurado y la cuenta existe, recibirás un enlace de un solo uso que caduca a los 30 minutos.
4. Para salir, pulsa **Cerrar sesión**. Una sesión también caduca tras 30 minutos de inactividad o 8 horas como máximo.

## Gestión familiar

Cualquier usuario autenticado y activo puede ver, crear y administrar las cuentas familiares: editar nombre/correo, cambiar contraseñas, activar/desactivar cuentas y eliminarlas. No hay un rol administrador separado: los permisos de gestión son iguales para los usuarios activos.

- Al cambiar tu propia contraseña, debes introducir la contraseña actual; el cambio cierra tu sesión. Al cambiar la de otra persona, no se pide la contraseña de esa persona y sus sesiones se revocan.
- No puedes desactivar tu propia cuenta ni dejar el sistema sin cuentas activas. No elimines una cuenta si es la última activa.
- La eliminación es definitiva. No hay función de restauración disponible en la interfaz.
- Si se rechaza el acceso tras varios intentos, espera a que expire el límite temporal (15 minutos) antes de volver a intentarlo.

## Planificación de comidas

En la pantalla autenticada, la planificación abre por defecto la semana actual según la fecha comunicada por el servidor en la zona `Atlantic/Canary`. La semana va de lunes a domingo y cada día presenta almuerzo y cena. Usa las flechas para avanzar o retroceder una semana; cambia a vista mensual para consultar o navegar por meses. Al alternar las vistas se conserva la fecha de referencia.

Selecciona una franja para abrir el editor. Puedes asignar o sustituir una etiqueta del catálogo, o elegir eliminar la etiqueta actual. La repetición está desactivada inicialmente. Si la activas, indica un intervalo entero positivo en semanas y una fecha final válida; la operación afecta únicamente a las fechas calculadas desde la fecha inicial. El final se incluye solo si coincide con una repetición. También se admiten fechas pasadas.

Antes de modificar franjas ocupadas o eliminar asignaciones, revisa la previsualización y confirma para guardar. Cancelar la previsualización o la confirmación no guarda cambios. Cada fecha se guarda como asignación independiente; modificar una copia no cambia las demás. El borrado repetido solo elimina la misma etiqueta. La planificación es compartida: otro usuario activo verá los cambios al volver a consultar o actualizar la vista; no hay actualización en tiempo real.

Estos flujos se recorrieron en Chrome contra la API real en un entorno local efímero con SQLite. Esta comprobación no sustituye la validación PostgreSQL ni cierra la verificación general; consulta los límites y la matriz del [estado de HU-002](../../odd/tasks/hu-002-planificacion-de-comidas.md).

## Ayuda y alcance

Si no puedes entrar, confirma que la dirección de correo y la contraseña sean correctas; para problemas de acceso o recuperación, contacta a quien administra el servicio. La aplicación no verifica la titularidad del correo. La creación/edición de etiquetas, recetas y listas no forma parte de esta funcionalidad.

**Mantenimiento del manual:** actualízalo junto con cualquier cambio en los flujos de cuenta, permisos, seguridad o funciones visibles.

**Referencias:** [HU-001](../historias-usuarios/HU-001-gestion-de-usuarios.md), [HU-002](../historias-usuarios/HU-002-planificacion-de-comidas.md), [estado de HU-002](../../odd/tasks/hu-002-planificacion-de-comidas.md), [README del proyecto](../../README.md).
