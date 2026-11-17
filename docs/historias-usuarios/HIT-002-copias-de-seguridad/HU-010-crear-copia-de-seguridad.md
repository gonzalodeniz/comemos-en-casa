# HU-010 — Crear una copia de seguridad

**Estado:** Implementada; validación local completada el 2026-11-17.

## Historia

Como usuario, quiero crear desde una nueva vista una copia de la base de datos y las imágenes, para conservar su estado.

Contexto y permisos confirmados en [contexto de producto](../../product/copias-de-seguridad/contexto.md). Seguimiento en el [backlog de HIT-002](../../product/copias-de-seguridad/backlog.md).

## Criterios de aceptación

- [x] Dado un usuario con sesión iniciada, cuando accede desde la navegación a la vista de copias de seguridad, entonces puede iniciar una copia manual, sin necesitar permisos de administrador.
- [x] Dado un usuario en esa vista, cuando solicita una copia y la operación termina correctamente, entonces obtiene una copia guardada en el servidor que incluye conjuntamente la base de datos y las imágenes de un estado coherente, y ve la confirmación de su creación.
- [x] Dado un usuario que solicita una copia, cuando la creación falla, entonces ve un mensaje de error y la copia incompleta no se presenta como creada correctamente.

**Validación:** `frontend npm test -- --run` (174 pruebas), `frontend npm run build`, `backend .venv/bin/python -m pytest -q` (176 pasaron, 15 omitidas), y construcción Docker `comemos-backend-hu010:local` completadas correctamente.

## Plan propuesto

- Incorporar la vista de copias de seguridad a la navegación disponible para todos los usuarios autenticados.
- Conectar la acción manual con una operación autenticada que respalde conjuntamente los datos y las imágenes.
- Guardar la copia en el servidor, preservando la coherencia entre datos e imágenes y evitando presentar resultados incompletos como válidos.
- Mostrar el resultado de la operación en la vista.
- Verificar el acceso, la creación conjunta y el tratamiento de errores con pruebas de interfaz y backend.

## Fuera de alcance

- Descargar copias al equipo local: HU-011.
- Restaurar copias: HU-012.
- Automatizar copias y configurar frecuencia y retención máxima: HU-013.

## Contexto técnico revisado

- La navegación actual centraliza las vistas en `frontend/src/AppWorkspace.tsx`.
- La API incorpora sus rutas en `backend/app/main.py`; no incluye actualmente rutas de copias de seguridad.
- El [plan de gestión de comidas](../../planes/hu-003-gestion-comidas.md) ya exige respaldar conjuntamente la base de datos y `data/`, con una ventana sin escrituras o un mecanismo equivalente de consistencia, y evitar limpieza sobre copias incompletas. El mecanismo concreto se decidirá al preparar la implementación.
- No existe `CLAUDE.md` en la raíz del repositorio; se han consultado las instrucciones de `AGENTS.md`.
