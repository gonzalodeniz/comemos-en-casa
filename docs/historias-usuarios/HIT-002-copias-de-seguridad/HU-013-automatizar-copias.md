# HU-013 — Automatizar copias de seguridad

**Estado:** Implementada; validación local completada el 2026-11-17.

## Historia

Como usuario, quiero automatizar las copias en el servidor indicando su frecuencia y el máximo de copias almacenadas, para mantener respaldos periódicos con retención limitada.

## Criterios de aceptación

- [x] Dado un usuario que configura la automatización, cuando elige una frecuencia diaria o semanal y un máximo de copias, entonces la configuración queda guardada.
- [x] Dada una automatización configurada, cuando llega la frecuencia establecida, entonces se crea una copia de la base de datos y las imágenes.
- [x] Dado que se alcanza el máximo configurado, cuando se crea una nueva copia automática, entonces se elimina la copia más antigua para respetar el límite.

## Decisiones

- Las frecuencias son diaria y semanal; no se configura una hora específica.
- La primera ejecución ocurre en la primera comprobación del planificador tras guardar la configuración; el planificador consulta cada minuto.
- La configuración es global y compartida por todos los usuarios.

## Validación

- `backend .venv/bin/python -m pytest -q`: 188 pasaron, 15 omitidas.
- `frontend npm test -- --run`: suite completa pasada.
- `frontend npm run build`: compilación de producción correcta.
