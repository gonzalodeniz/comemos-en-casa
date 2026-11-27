"""Valida una selección puntual con el catálogo local de Codex."""

import json
import os
import sys
from pathlib import Path


# Lee la última caché local; no realiza consultas de red ni garantiza acceso actual.
def modelos_locales():
    directorio = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    datos = json.loads((directorio / "models_cache.json").read_text())
    return {
        entrada["slug"]: [nivel["effort"] for nivel in entrada["supported_reasoning_levels"]]
        for entrada in datos["models"]
        if entrada.get("visibility") == "list" and entrada.get("slug")
    }


# Comprueba la pareja modelo-esfuerzo e informa de las alternativas locales.
def principal():
    try:
        modelos = modelos_locales()
        if not modelos:
            raise ValueError("catálogo vacío")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"ERROR: no se puede consultar la caché local de modelos de Codex: {error}", file=sys.stderr)
        return 1

    modelo, esfuerzo = sys.argv[1:]
    if modelo not in modelos or esfuerzo not in modelos[modelo]:
        print(f"ERROR: modelo o esfuerzo no válido: {modelo} / {esfuerzo}", file=sys.stderr)
        print("Modelos y esfuerzos en la caché local de Codex (puede estar desactualizada):", file=sys.stderr)
        for nombre, niveles in sorted(modelos.items()):
            print(f"  {nombre}: {', '.join(niveles)}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(principal())
