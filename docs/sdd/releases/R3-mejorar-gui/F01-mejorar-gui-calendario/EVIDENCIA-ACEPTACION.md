# Evidencia de aceptación — F01 Mejorar GUI del calendario

**Fecha:** 2026-09-17  
**Estado:** parcial; pendiente de revisión manual y de comprobaciones de repositorio bloqueadas.  
**Alcance revisado:** presentación de calendario en `frontend/src/App.tsx`, `frontend/src/styles.css` y sus pruebas. Esta implementación no modificó API, reducer, tipos de contrato, backend, infraestructura ni configuración de despliegue. El árbol de trabajo también contiene `requirements.lock` y `requirements-dev.lock` sin seguimiento: son cambios preexistentes/no relacionados y no forman parte de esta aceptación.

## Entorno

- Node: `v22.23.2`.
- Frontend: React 19, TypeScript 5.8, Vite 6.4.3 y Vitest 3.2.7.
- Referencia visual: `prototipos/calendario-01.png`.

## Verificación automatizada

| Comando | Resultado | Evidencia |
| --- | --- | --- |
| `npm --prefix frontend run test` | Correcto | 1 archivo, 8 pruebas superadas. Cubre composición, navegación, alta global/contextual, tarjetas con/sin imagen, receta no disponible, edición/eliminación, carga y error. |
| `npm --prefix frontend run typecheck` | Correcto | `tsc --noEmit` sin errores. |
| `npm --prefix frontend run build` | Correcto | `tsc --noEmit && vite build`; 43 módulos transformados. |
| `git diff --check` | Correcto | Sin espacios finales ni errores de parche. |
| Diff de `frontend/src/api.ts`, `frontend/src/calendarReducer.ts`, `frontend/src/types.ts` | Correcto | Sin cambios. |
| `make test` | Bloqueada | La ejecución actual alcanzó el smoke inicial y emitió `.`; el límite del entorno interrumpió el proceso a los 30 s sin resultado final. La evidencia previa reproducible con `timeout 90s` identifica el bloqueo en `backend/tests/auth/test_auth_api.py::test_login_callback_me_and_logout_preserve_the_cookie_and_route_contracts` y código 124. No se considera aprobada. |
| `make build` | No ejecutable en este entorno | Sale con código 2: no hay permiso para conectar al socket Docker (`/var/run/docker.sock`). No se atribuye a la feature. |

## Cobertura entregada

- Tarjetas de asignación con portada alternativa útil, reserva visual decorativa si falta imagen, título visible y estado de receta no disponible.
- Acciones existentes de ver, editar y eliminar conservadas; las pruebas verifican la actualización/eliminación contra los dobles de API existentes.
- Celdas vacías diferenciadas y botón contextual con turno y fecha en el nombre accesible.
- Región de calendario con `aria-busy` durante carga, error existente visible, foco visible y contenedor de cuadrícula desplazable horizontalmente y enfocable. El contenedor es una región nombrada y describe cómo recorrer los siete días.
- En viewport estrecho se muestra una indicación visible de desplazamiento horizontal; la columna de turno queda fija y cada celda referencia sus encabezados de turno y día. Los botones contextuales alcanzan 44 CSS px.

## Revisión visual y manual pendiente

No se realizó una comparación visual interactiva ni recorrido con lector de pantalla porque este entorno no proporciona navegador ni lector de pantalla. Antes de cerrar T04/T05 debe registrarse una matriz con:

1. Escritorio y móvil frente a `prototipos/calendario-01.png`, con datos, huecos, carga y error.
2. Scroll horizontal y columna de turnos en móvil.
3. Teclado, zoom y foco visible.
4. Lector de pantalla disponible y medición de objetivos táctiles.

## Límites y siguiente acción

- Mantener `GUI-CAL-T01` bloqueada: investigar o clasificar formalmente el timeout de autenticación antes de aprobar `make test`.
- Ejecutar `make build` en un entorno autorizado para Docker.
- Completar la revisión manual anterior y actualizar este informe y `TASKS.md` con los resultados reales.
