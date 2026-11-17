# Interfaz de copias de seguridad

La vista reutiliza los tokens CSS, botones, mensajes e iconos del proyecto.
Los diálogos nativos siguen el patrón de edición de la lista de la compra.

## Datos y contratos

- `GET /api/v1/backups`: archivos y tamaños reales. La fecha se obtiene del nombre UTC generado por el servidor y se presenta en la configuración regional del navegador. No se deducen tipos ni estados de integridad.
- `GET /api/v1/backups/schedule`: consulta autenticada de la configuración global. Sin programación devuelve `{"enabled": false, "frequency": null, "maximum": null}`; con programación devuelve `enabled`, `frequency` y `maximum` persistidos. No modifica datos.
- Se conservan los contratos existentes de creación, descarga, guardado de programación, eliminación y restauración, incluida la protección CSRF.

Las imágenes de recetas, comidas y productos se incluyen siempre. Solo se permiten frecuencias diaria y semanal. La retención se aplica al conjunto de copias al ejecutar la automatización; no hay opción para desactivarla mediante la API actual.

## Seguridad y limitaciones

La eliminación y restauración requieren confirmación explícita. Las operaciones de la vista se serializan para evitar envíos duplicados. Un fallo de consulta nunca se presenta como una lista vacía ni almacenamiento cero.

La restauración conserva sus mecanismos existentes: la base de datos y las imágenes no cuentan con una reversión conjunta. Un error permanece visible y advierte de la posible necesidad de recuperación manual. No se realizan restauraciones ni eliminaciones de datos reales como validación de la interfaz.

## Subir una copia

Se puede seleccionar desde el navegador un ZIP descargado anteriormente, conservando su nombre original `backup-YYYYMMDDTHHMMSSZ.zip`. La subida requiere sesión y CSRF, admite hasta 1 GiB, comprueba que sea un ZIP legible con `database.sql` y rechaza nombres duplicados sin sobrescribir. La subida no restaura datos: la restauración sigue siendo una acción separada y requiere confirmación. La validación completa del contenido se realiza durante la restauración. El proxy Nginx del proyecto permite hasta 1 GiB exclusivamente para esta ruta; otros proxies intermedios pueden imponer un límite inferior. Tras cambiar la configuración es necesario recargar o recrear el proxy.
