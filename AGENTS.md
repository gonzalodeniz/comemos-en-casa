# Guía del repositorio

Este archivo define reglas de comportamiento para contribuir al proyecto. La información operativa y cambiante se mantiene separada:

- Consulta [`INDICE.md`](INDICE.md) para conocer la estructura actual del repositorio.
- Consulta [`COMMANDOS.md`](COMMANDOS.md) para los comandos de instalación, desarrollo y verificación.
- Lee siempre [`docs/sdd/01-vision-producto.md`](docs/sdd/01-vision-producto.md) antes de trabajar para entender el contexto y el producto que se está construyendo.

## Reglas de contribución

- Mantén cada módulo centrado en una funcionalidad y sigue la organización existente.
- En Python usa cuatro espacios y convenciones PEP 8. En TypeScript usa dos espacios, `PascalCase` para componentes React y `camelCase` para variables y funciones.
- Añade pruebas de regresión para los cambios de comportamiento y mantenlas deterministas. Todo cambio debe incluir la verificación adecuada para su área.
- Usa Conventional Commits, por ejemplo `feat: add recipe editor` o `fix: validate calendar dates`. Mantén los commits pequeños y enfocados.
- Las pull requests deben describir el cambio, indicar cómo se verificó, enlazar la incidencia o tarea relacionada e incluir capturas o una grabación breve cuando cambie la interfaz.
- Señala explícitamente las migraciones de base de datos y los cambios de configuración en commits y pull requests.
- No subas credenciales, tokens, compilaciones generadas ni datos de bases de datos locales. Usa `.env` únicamente para configuración local y secretos.
- Revisa cuidadosamente los cambios de autenticación y migraciones porque afectan a todos los entornos.

## Consistencia de las instrucciones

`AGENTS.md` y `CLAUDE.md` deben ser siempre idénticos. Cualquier modificación de las reglas debe aplicarse a ambos archivos en el mismo cambio y verificarse con `cmp AGENTS.md CLAUDE.md`.
