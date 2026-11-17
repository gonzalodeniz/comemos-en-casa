# HU-012 — Restaurar una copia de seguridad

**Estado:** Implementada; validación local completada el 2026-11-17.

## Historia

Como usuario, quiero restaurar la base de datos y las imágenes desde una copia de seguridad, para recuperar un estado anterior.

## Criterios de aceptación

- [x] Dada una copia disponible, cuando el usuario confirma su restauración, entonces se recuperan la base de datos y las imágenes de esa copia y se informa que terminó correctamente.
- [x] Dada una copia inválida o una restauración que falla, cuando el usuario intenta restaurarla, entonces se informa del fallo y se indica que la recuperación debe realizarse manualmente; no se comunica éxito.
- [x] Dado un usuario en la vista de copias, cuando selecciona restaurar, entonces debe confirmar la operación antes de que comience.

## Plan aplicado

- Seleccionar una copia y confirmar la restauración desde la vista.
- Restaurar base de datos e imágenes conjuntamente desde la copia seleccionada.
- Informar el resultado; ante fallos, indicar recuperación manual.
- Probar restauración exitosa, fallos y confirmación en API y vista.

## Decisión de producto

- No se revierte automáticamente al estado anterior si falla la restauración; se informa del fallo y la recuperación se hace manualmente.

## Validación

- `backend .venv/bin/python -m pytest -q`: 184 pasaron, 15 omitidas.
- `frontend npm test -- --run`: suite completa pasada.
- `frontend npm run build`: compilación de producción correcta.
