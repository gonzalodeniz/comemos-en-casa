# Frontend

Minimal React + TypeScript application built with Vite. It intentionally contains no user or meal functionality.

## Start locally

From this directory, install the declared npm dependencies and start the Vite development server:

```sh
npm install
npm run dev
```

## Smoke test and production build

```sh
npm test
npm run build
```

## Ruta de publicación

El build de despliegue define `VITE_BASE=/comemos/` y publica la interfaz bajo `/comemos/`; las llamadas API usan `/comemos/api/v1`. Para desarrollo local, Vite mantiene su servidor HMR separado y no se expone en el proxy público.

## Instalación móvil

Con la aplicación disponible por HTTPS, usa la opción de instalación o de añadir a la pantalla de inicio del navegador móvil. La aplicación instalada necesita conexión; las notificaciones push no forman parte de esta funcionalidad.

En iPhone, la página declara el logo como `apple-touch-icon` para la pantalla de inicio. Si una instalación anterior sigue mostrando una inicial, retira ese icono y vuelve a añadir la aplicación desde Safari.
