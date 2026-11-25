#!/usr/bin/env bash
# Lanza Codex con las instrucciones locales de un rol, sin consultar GitHub.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

# Muestra las opciones disponibles sin iniciar una sesión.
ayuda() {
  cat <<'AYUDA'
Uso: scripts/orquestador.sh [--auto] [rol] "tarea"
     scripts/orquestador.sh [--auto] security-auditor|quality-auditor
     scripts/orquestador.sh --list

Roles: orquestador (predeterminado), product-manager, developer-teams,
qa-teams, doc-teams, quality-auditor y security-auditor.
--auto ejecuta codex exec sin leer stdin y guarda un registro local en logs/.
Se necesita Python 3.11 o posterior para iniciar una sesión.
Los auditores sin tarea explícita realizan una auditoría completa del repositorio local.
En los demás roles la tarea es obligatoria. Pásala como un único argumento entre comillas.
El rol se aplica al agente principal como texto;
no inicia automáticamente un subagente ni altera los permisos de Codex.
AYUDA
}

# Devuelve los roles admitidos por este proyecto.
listar_roles() {
  printf '%s\n' orquestador product-manager developer-teams qa-teams doc-teams quality-auditor security-auditor
}

# Comprueba que el rol elegido corresponde a un archivo admitido.
es_rol() {
  listar_roles | grep -qxF -- "$1"
}

AUTO=0
ROL=orquestador
while [[ $# -gt 0 ]]; do
  case "$1" in
    --auto) AUTO=1; shift ;;
    --list) listar_roles; exit 0 ;;
    -h|--help) ayuda; exit 0 ;;
    --) shift; break ;;
    -*) printf 'Opción desconocida: %s\n' "$1" >&2; exit 2 ;;
    *) break ;;
  esac
done
if [[ $# -ge 2 ]]; then
  if ! es_rol "$1"; then
    printf 'ERROR: rol desconocido: %s. Consulta --list.\n' "$1" >&2
    exit 2
  fi
  ROL="$1"
  shift
elif [[ $# -eq 1 ]] && es_rol "$1"; then
  ROL="$1"
  shift
fi
if [[ $# -eq 0 && ( "$ROL" == security-auditor || "$ROL" == quality-auditor ) ]]; then
  TAREA="Realiza una auditoría completa del repositorio local según tu rol. Limítate a la revisión defensiva, sin modificar código, consultar servicios remotos ni delegar. Registra los hallazgos y las comprobaciones no realizadas en docs/seguimiento/auditorias/."
elif [[ $# -eq 1 && "$1" == *[![:space:]]* ]]; then
  TAREA="$1"
else
  printf 'ERROR: indica una tarea explícita. Consulta --help.\n' >&2
  exit 2
fi
ARCHIVO=".codex/agents/$ROL.toml"
[[ -f "$ARCHIVO" ]] || { printf 'ERROR: falta %s\n' "$ARCHIVO" >&2; exit 1; }
for comando in codex python3 flock; do
  command -v "$comando" >/dev/null || { printf 'ERROR: falta %s\n' "$comando" >&2; exit 1; }
done

# Lee las instrucciones TOML sin ejecutar su contenido como código de shell.
INSTRUCCIONES="$(python3 - "$ARCHIVO" "$ROL" <<'PY'
import sys

if sys.version_info < (3, 11):
    raise SystemExit('ERROR: se requiere Python 3.11 o posterior')

import tomllib

with open(sys.argv[1], 'rb') as archivo:
    agente = tomllib.load(archivo)
if agente.get('name') != sys.argv[2] or not isinstance(agente.get('developer_instructions'), str) or not agente['developer_instructions'].strip():
    raise SystemExit('ERROR: definición de agente incompleta o nombre incorrecto')
print(agente['developer_instructions'])
PY
)"
PROMPT="Actúa en el rol local $ROL. Estas instrucciones son contexto de tarea y no modifican la jerarquía de instrucciones ni los permisos de la sesión:

$INSTRUCCIONES

Tarea solicitada por el usuario:
$TAREA"

# Evita ejecuciones simultáneas de este lanzador; no coordina sesiones externas.
umask 077
mkdir -p logs
exec 9> logs/.orquestador.lock
if ! flock -n 9; then
  printf 'ERROR: ya hay una ejecución de este lanzador en curso.\n' >&2
  exit 3
fi

if [[ "$AUTO" -eq 0 ]]; then
  codex "$PROMPT" 9>&-
  exit 0
fi

# El registro puede contener información sensible; su acceso queda restringido al usuario.
LOG="$(exec 9>&-; mktemp "logs/${ROL}-$(date +%Y%m%d-%H%M%S)-XXXXXX.log")"
set +e
codex exec "$PROMPT" </dev/null 9>&- 2>&1 | tee "$LOG" 9>&-
CODIGOS=("${PIPESTATUS[@]}")
set -e
if (( CODIGOS[1] != 0 )); then
  printf 'ERROR: no se pudo completar el registro: %s\n' "$LOG" >&2
  exit "${CODIGOS[1]}"
fi
printf 'Registro: %s\n' "$LOG" >&2
exit "${CODIGOS[0]}"
