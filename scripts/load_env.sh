#!/usr/bin/env bash

# Carga las variables definidas en .env y las exporta al entorno actual.
# Debe invocarse con: source scripts/load_env.sh

_load_env_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
_load_env_file="${_load_env_dir}/../.env"

if [[ ! -f "${_load_env_file}" ]]; then
  printf 'No se ha encontrado el fichero .env: %s\n' "${_load_env_file}" >&2
  return 1 2>/dev/null || exit 1
fi

set -a
# shellcheck source=/dev/null
. "${_load_env_file}"
set +a

unset _load_env_dir _load_env_file
