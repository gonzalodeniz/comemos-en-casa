# HU-018 — Identificar comidas con recordatorio

## Historia

Como usuario, quiero ver un icono informativo junto a «Editar» en las comidas con recordatorio activado, para identificarlas sin abrirlas.

[Contexto de producto](../../product/recordatorios-de-comidas/contexto.md) · [Backlog](../../product/recordatorios-de-comidas/backlog.md)

## Criterios de aceptación

- [ ] Dada una comida con un recordatorio activado, cuando consulto la planificación semanal, entonces veo un icono pequeño junto a «Editar» que no parece un botón ni ofrece ninguna acción.
- [ ] Dada una comida sin recordatorio o con el recordatorio desactivado, cuando consulto la planificación semanal, entonces no se muestra el icono.

## Plan propuesto

- Incluir el estado del recordatorio en los datos de las comidas planificadas.
- Mostrar el icono no interactivo junto a «Editar» solo cuando el recordatorio esté activado.
- Verificar en la interfaz que el indicador aparece únicamente para comidas con recordatorio activado y no se comporta como un control.

## Fuera de alcance

- Acciones o edición desde el icono.
