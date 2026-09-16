# Comandos del proyecto

Ejecuta los comandos desde la raíz del repositorio. Este documento contiene operativa que puede cambiar con la configuración del proyecto.

## Instalación

- `make install`: instala las dependencias de desarrollo de Python y frontend.
- `make frontend-install`: instala únicamente las dependencias del frontend.

## Docker Compose

- `make up`: compila e inicia PostgreSQL, backend y frontend en segundo plano.
- `make build`: compila las imágenes sin iniciar los servicios.
- `make down`: detiene los servicios y conserva los volúmenes.
- `make restart`: reinicia todos los servicios.
- `make ps`: muestra el estado de los servicios.
- `make logs`: muestra los registros de todos los servicios.
- `make backend`: sigue los registros del backend.
- `make frontend`: sigue los registros del frontend.
- `make db-shell`: abre una consola `psql` dentro del contenedor de PostgreSQL.

## Desarrollo local

- `npm --prefix frontend run dev`: inicia el servidor de desarrollo de Vite.
- `npm --prefix frontend run typecheck`: comprueba los tipos de TypeScript.
- `npm --prefix frontend run build`: ejecuta el typecheck y genera la compilación de producción.

## Verificación

- `make test`: ejecuta todas las comprobaciones del proyecto.
- `make test-backend`: ejecuta la suite Python con Pytest.
- `make test-frontend`: ejecuta el typecheck y la compilación del frontend.
