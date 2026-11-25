"""Comprueba el lanzador sin abrir sesiones reales de Codex."""

import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# Prueba argumentos, aislamiento y errores con dobles locales.
class PruebasOrquestador(unittest.TestCase):
    # Prepara una copia desechable del lanzador y de un rol de prueba.
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.raiz = Path(temporal.name)
        origen = Path(__file__).resolve().parents[1] / "orquestador.sh"
        self.lanzador = self.raiz / "scripts" / origen.name
        self.lanzador.parent.mkdir()
        shutil.copy2(origen, self.lanzador)
        agentes = self.raiz / ".codex" / "agents"
        agentes.mkdir(parents=True)
        for rol in ("orquestador", "qa-teams", "security-auditor", "quality-auditor"):
            (agentes / f"{rol}.toml").write_text(
                f'name = "{rol}"\ndeveloper_instructions = "Instrucciones de prueba"\n'
            )
        self.binarios = self.raiz / "bin"
        self.binarios.mkdir()
        self.entorno = {**os.environ, "PATH": f"{self.binarios}:{os.environ['PATH']}"}
        self.doble(
            "codex",
            'if { : <&9; } 2>/dev/null; then exit 89; fi\n'
            'printf "%s\\n" "$@"\n'
            'if [[ "$1" == exec ]]; then cat; fi\n'
            'exit "${CODIGO_CODEX:-0}"\n',
        )

    # Instala un ejecutable controlado antes de los binarios reales en PATH.
    def doble(self, nombre, cuerpo):
        archivo = self.binarios / nombre
        archivo.write_text("#!/bin/bash\n" + cuerpo)
        archivo.chmod(0o700)

    # Ejecuta el lanzador en el entorno aislado y captura el resultado.
    def lanzar(self, *argumentos, entrada=""):
        return subprocess.run(
            [str(self.lanzador), *argumentos],
            input=entrada,
            capture_output=True,
            text=True,
            env=self.entorno,
            timeout=5,
        )

    # Un rol mal escrito y una tarea en blanco no arrancan Codex.
    def test_rechaza_argumentos_invalidos(self):
        for argumentos in ((), ("qa-team", "Revisar"), ("\t\n ",), ("qa-teams",), ("security-auditor", " ")):
            with self.subTest(argumentos=argumentos):
                resultado = self.lanzar(*argumentos)
                self.assertEqual(resultado.returncode, 2)
                self.assertFalse(resultado.stdout)

    # Ambos auditores tienen una tarea predeterminada en los dos modos.
    def test_auditores_sin_tarea_inician_auditoria_completa(self):
        for modo in ((), ("--auto",)):
            for rol in ("security-auditor", "quality-auditor"):
                with self.subTest(modo=modo, rol=rol):
                    resultado = self.lanzar(*modo, rol)
                    self.assertEqual(resultado.returncode, 0, resultado.stderr)
                    self.assertIn(f"rol local {rol}", resultado.stdout)
                    self.assertIn("auditoría completa", resultado.stdout)

    # Una tarea explícita no se sustituye por la auditoría completa.
    def test_auditor_respeta_tarea_explicita(self):
        resultado = self.lanzar("security-auditor", "Revisa solo la autenticación")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("Revisa solo la autenticación", resultado.stdout)
        self.assertNotIn("auditoría completa", resultado.stdout)

    # Una tarea sin rol explícito usa el orquestador y no hereda el bloqueo.
    def test_interactivo_usa_rol_predeterminado(self):
        resultado = self.lanzar("Revisar planificación")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("rol local orquestador", resultado.stdout)
        self.entorno["CODIGO_CODEX"] = "7"
        self.assertEqual(self.lanzar("Revisar planificación").returncode, 7)

    # El modo automático registra la salida sin incorporar stdin ni heredar el bloqueo.
    def test_automatico_ignora_stdin(self):
        resultado = self.lanzar("--auto", "qa-teams", "Revisar", entrada="Dato ajeno")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        (registro,) = (self.raiz / "logs").glob("qa-teams-*.log")
        salida = registro.read_text()
        self.assertIn("rol local qa-teams", salida)
        self.assertNotIn("Dato ajeno", salida)

    # Un fallo de tee se distingue del código de salida de Codex.
    def test_fallo_al_escribir_registro(self):
        self.doble("tee", 'if { : <&9; } 2>/dev/null; then exit 89; fi\ncat >/dev/null\nexit 6\n')
        resultado = self.lanzar("--auto", "Revisar")
        self.assertEqual(resultado.returncode, 6)
        self.assertIn("no se pudo completar el registro", resultado.stderr)

    # Un error de Codex no se convierte en éxito aunque tee guarde la salida.
    def test_preserva_fallo_de_codex(self):
        self.entorno["CODIGO_CODEX"] = "7"
        resultado = self.lanzar("--auto", "Revisar")
        self.assertEqual(resultado.returncode, 7)
        self.assertIn("Registro:", resultado.stderr)

    # Un intérprete antiguo recibe un diagnóstico antes de importar tomllib.
    def test_rechaza_python_anterior_a_311(self):
        codigo = "import sys; sys.version_info = (3, 10); exec(sys.stdin.read())"
        self.doble("python3", f'exec {shlex.quote(sys.executable)} -c {shlex.quote(codigo)} "$@"\n')
        resultado = self.lanzar("Revisar")
        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn("se requiere Python 3.11 o posterior", resultado.stderr)
        self.assertNotIn("Traceback", resultado.stderr)
