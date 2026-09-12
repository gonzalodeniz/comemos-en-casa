# Ejecución autónoma

## Arranque

Ejecuta únicamente el lanzador del orquestador:

```bash
bash run-orquestador.sh "Construir el alcance de la visión del producto"
```

Necesita Bash, Git, jq, flock, Codex autenticado y acceso a GitHub desde Codex
para leer y actualizar issues y PR. Ese acceso puede proceder del conector
configurado o de una herramienta autenticada disponible en el entorno.
No presupone que esté instalado GitHub CLI.

El script carga el archivo local `.env`, si existe, sin mostrar su contenido.
Ese archivo se interpreta como shell: solo debe contener configuración de
confianza. Conserva el modo sin sandbox del lanzador anterior; ejecútalo en
un entorno aislado con permisos y credenciales limitados al repositorio.
No ejecutes esta automatización con credenciales de producción.

El lanzador solicita una decisión estructurada al orquestador, ejecuta el
archivo del rol seleccionado y espera a que termine. A continuación vuelve
a invocar al orquestador para comprobar el resultado en GitHub y decidir.
No requiere ejecutar manualmente Producto, Desarrollo, QA ni los demás roles.

## Coordinación y continuidad

La issue de coordinación conserva objetivo, exclusiones, entregas, decisiones,
resultados y límites. El orquestador la crea si no existe y Producto concreta
el alcance antes de empezar. La fuente del avance son las issues; los archivos
locales y las respuestas de procesos no sustituyen su evidencia.

Hay una entrega activa por defecto y un solo agente ejecutándose a la vez.
El bloqueo local evita dos lanzadores simultáneos sobre el mismo repositorio,
incluidos sus worktrees. No coordina clones en otras máquinas: utiliza un único
ejecutor por repositorio y no arranques agentes manuales durante la ejecución.

El procedimiento está en [ORQUESTADOR.md](../ORQUESTADOR.md); estados, revisiones,
seguridad y recuperación están en [FLUJO.md](../FLUJO.md).

## Límites y recuperación

El límite predeterminado es de 30 delegaciones, más una evaluación final que
solo comprueba el resultado y registra la terminación:

```bash
ORQUESTADOR_MAX_ITERACIONES=60 bash run-orquestador.sh "Retomar la coordinación"
```

| Código de salida | Significado |
| --- | --- |
| 0 | Producto confirmó el objetivo y el orquestador comprobó el cierre |
| 1 | Falló un proceso, dependencia o contrato de respuesta |
| 2 | Bloqueo externo sin un siguiente paso interno ejecutable |
| 3 | Límite de delegaciones alcanzado; el objetivo puede seguir pendiente |
| 4 | Ya existe un lanzador activo en este repositorio |

El script no reinicia automáticamente procesos fallidos ni transforma el límite
en éxito. Tras resolver la causa, ejecuta el mismo comando con la URL de la
coordinación. El orquestador relee las issues, comprueba operaciones incompletas
y retoma las ramas y PR existentes. No necesita el historial local de Codex.

Si un proceso se interrumpe antes de publicar en GitHub, la siguiente ejecución
debe comprobar los efectos reales antes de repetirlo. Los diagnósticos locales
se conservan con permisos privados en `tmp/orquestador.*/`, excluido de Git.
El lanzador no publica esos archivos, que pueden contener información privada.
Un bloqueo del sistema o un proceso que no responde requiere intervención del
operador; el límite cuenta delegaciones, no establece un tiempo máximo.

## Verificación del lanzador

Las pruebas usan un ejecutable Codex simulado en un repositorio temporal.
No llaman a modelos ni escriben en GitHub:

```bash
bash -n run-orquestador.sh
python3 -m unittest discover -s tests -p 'test_orquestador.py' -v
markdownlint AGENTS.md FLUJO.md ORQUESTADOR.md agentes/*.md
markdownlint docs/ejecucion-autonoma.md
```

La versión instalada de markdownlint debe ser compatible con la versión de Node.
El lanzador usa `--output-schema` y `--output-last-message`, documentados en
el [modo no interactivo de Codex][codex-exec].
Las pruebas locales comprueban el control de procesos; una ejecución real con
GitHub sigue siendo necesaria para verificar permisos e integraciones.

[codex-exec]: https://developers.openai.com/codex/noninteractive/
