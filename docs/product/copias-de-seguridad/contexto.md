# Copias de seguridad y restauración

## Contexto

Nueva vista para que los usuarios puedan proteger y recuperar la base de datos y las imágenes de la aplicación.

## Alcance confirmado

- Crear manualmente copias de seguridad de la base de datos y las imágenes desde una nueva vista.
- Descargar las copias en el equipo local del usuario.
- Restaurar la base de datos y las imágenes desde una copia de seguridad.
- Automatizar las copias de seguridad en el servidor.
- Permitir al usuario indicar la frecuencia de las copias automatizadas y el número máximo de copias almacenadas.

## Decisiones de producto

- Todos los usuarios podrán crear, descargar y restaurar copias, así como configurar su automatización; no se limita esta funcionalidad a administradores.

## Stack

Se utilizará el stack actual del proyecto, sin introducir decisiones técnicas adicionales en esta definición de producto.

## Backlog

El [backlog](backlog.md) recoge el hito HIT-002 y sus historias. Esta documentación no incluye criterios de aceptación ni autoriza la implementación.
