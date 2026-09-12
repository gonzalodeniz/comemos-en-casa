#!/usr/bin/env bash
set -euo pipefail

# Un proceso por rol; las issues conservan el avance entre iteraciones.
# Mantiene el modo sin sandbox del lanzador original: requiere aislamiento externo.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [[ "${1:-}" == "--help" ]]; then
  printf '%s\n' \
    'Uso: bash run-orquestador.sh [objetivo o URL de coordinación]' \
    'ORQUESTADOR_MAX_ITERACIONES: máximo de delegaciones (por defecto 30).' \
    'Salidas: 0 completado; 2 bloqueado; 3 límite; 1 fallo; 4 ya en ejecución.' \
    'Requiere Codex autenticado, GitHub accesible y un entorno aislado.'
  exit 0
fi

if [[ -f "${SCRIPT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${SCRIPT_DIR}/.env"
  set +a
fi

for dependency in codex git jq flock; do
  if ! command -v "${dependency}" >/dev/null 2>&1; then
    printf 'Falta la dependencia: %s\n' "${dependency}" >&2
    exit 1
  fi
done

max_iterations="${ORQUESTADOR_MAX_ITERACIONES:-30}"
if [[ ! "${max_iterations}" =~ ^[1-9][0-9]{0,3}$ ]]; then
  printf '%s\n' 'ORQUESTADOR_MAX_ITERACIONES debe estar entre 1 y 9999.' >&2
  exit 1
fi

# El directorio común comparte el bloqueo incluso entre worktrees.
git_common_dir="$(git rev-parse --path-format=absolute --git-common-dir)"
exec 9>"${git_common_dir}/orquestador.lock"
if ! flock -n 9; then
  printf '%s\n' 'Ya hay un orquestador ejecutándose en este repositorio.' >&2
  exit 4
fi

schema_file="${SCRIPT_DIR}/scripts/orquestador-decision.schema.json"
prompt_file="${SCRIPT_DIR}/agentes/orquestador.md"
[[ -r "${schema_file}" && -r "${prompt_file}" ]] || {
  printf '%s\n' 'Faltan el esquema o las instrucciones del orquestador.' >&2
  exit 1
}

# tmp/ está excluido de Git. Los diagnósticos locales no sustituyen las issues.
umask 077
mkdir -p "${SCRIPT_DIR}/tmp"
run_dir="$(mktemp -d "${SCRIPT_DIR}/tmp/orquestador.XXXXXXXX")"
run_id="${run_dir##*/}"
objective="${*:-Retomar la coordinación activa o delimitar la primera entrega de la visión.}"
previous_result="No hay agente anterior en esta ejecución; comprueba recuperación en GitHub."
printf 'Registro local: %s\n' "${run_dir}"

run_codex() {
  codex exec \
    --cd "${SCRIPT_DIR}" \
    --dangerously-bypass-approvals-and-sandbox \
    --dangerously-bypass-hook-trust \
    "$@" -
}

# Se reserva una evaluación final para verificar al último agente sin delegar.
for ((iteration = 1; iteration <= max_iterations + 1; iteration++)); do
  remaining=$((max_iterations - iteration + 1))
  assignment_id="${run_id}-${iteration}"
  decision_file="${run_dir}/decision-${iteration}.json"
  orchestration_prompt="$(<"${prompt_file}")

Petición del usuario:
${objective}

Modo de ejecución: lanzador secuencial con salida estructurada.
Identificador de asignación: ${assignment_id}
Delegaciones restantes: ${remaining}
${previous_result}
Lee ORQUESTADOR.md y reconstruye el estado desde las issues.
Registra la asignación antes de devolver delegar. No ejecutes tú al agente.
Si no quedan delegaciones, verifica el último resultado y devuelve únicamente
completado, bloqueado o limite. No registres una asignación que no se ejecutará."

  if ! printf '%s\n' "${orchestration_prompt}" |
    run_codex --output-schema "${schema_file}" -o "${decision_file}"; then
    printf 'Falló el orquestador. Reanuda desde las issues. Registro: %s\n' \
      "${run_dir}" >&2
    exit 1
  fi

  # Valida también la salida recibida; nunca se convierte texto del modelo en shell.
  if ! jq -e '
    def issue_url:
      test("^https://[^/ ]+/[^/ ]+/[^/ ]+/issues/[0-9]+$");
    type == "object" and
    (keys == ["accion", "asignacion", "issue", "objetivo", "resumen", "rol"]) and
    (all(.[]; type == "string")) and
    (.accion | IN("delegar", "completado", "bloqueado", "limite")) and
    (.resumen | length > 0) and
    (if .accion == "delegar" then
      (.rol | IN("developer-teams", "doc-teams", "product-manager",
                 "qa-teams", "quality-auditor", "security-auditor")) and
      (.issue | issue_url) and
      (.asignacion | test("#issuecomment-[0-9]+$")) and
      (.asignacion | split("#") | length == 2) and
      ((.asignacion | split("#")[0]) == .issue) and
      (.objetivo | length > 0)
    else .rol == "" and .asignacion == "" and
      (if .accion == "completado" then (.issue | issue_url)
       else .issue == "" or (.issue | issue_url) end)
    end)
  ' "${decision_file}" >/dev/null; then
    printf 'Decisión inválida; no se ejecuta ningún agente. Revisa %s\n' \
      "${decision_file}" >&2
    exit 1
  fi

  action="$(jq -r '.accion' "${decision_file}")"
  jq -r '.resumen' "${decision_file}"
  case "${action}" in
    completado) exit 0 ;;
    bloqueado) exit 2 ;;
    limite) exit 3 ;;
  esac
  if ((remaining == 0)); then
    printf '%s\n' 'Límite alcanzado; se rechaza la delegación adicional.' >&2
    exit 3
  fi

  role="$(jq -r '.rol' "${decision_file}")"
  issue="$(jq -r '.issue' "${decision_file}")"
  assignment="$(jq -r '.asignacion' "${decision_file}")"
  agent_prompt_file="${SCRIPT_DIR}/agentes/${role}.md"
  agent_result_file="${run_dir}/resultado-${iteration}.txt"
  agent_prompt="$(<"${agent_prompt_file}")

Asignación: ${assignment_id}
Issue asignada: ${issue}
Comentario de asignación: ${assignment}
Consulta la issue para obtener el objetivo, restricciones y evidencia.
Ejecuta solo esta asignación según AGENTS.md, FLUJO.md y tu rol.
Publica el resultado y siguiente paso en la issue antes de terminar.
No invoques otros agentes ni el lanzador. Devuelve los enlaces a tu resultado."

  if ! printf '%s\n' "${agent_prompt}" |
    run_codex -o "${agent_result_file}"; then
    printf 'Falló %s; comprueba la asignación %s antes de reintentar.\n' \
      "${role}" "${assignment}" >&2
    exit 1
  fi
  previous_result="El proceso de ${role} terminó para ${assignment_id}.
Issue: ${issue}
Asignación: ${assignment}
Comprueba su resultado y evidencia en GitHub; la salida cero no acredita éxito."
done
