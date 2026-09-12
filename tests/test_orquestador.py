"""Comprueba el lanzador sin llamadas a modelos ni cambios en GitHub."""

import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/example/project/issues/1"

# El doble de Codex consume decisiones predefinidas y registra cada invocación.
FAKE_CODEX = r"""#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

root = Path(os.environ["FAKE_ROOT"])
args = sys.argv[1:]
prompt = sys.stdin.read()
is_orchestrator = "--output-schema" in args
with (root / "calls.jsonl").open("a") as stream:
    stream.write(json.dumps({"orchestrator": is_orchestrator,
                             "prompt": prompt, "args": args}) + "\n")
counter = root / "counter"
index = int(counter.read_text()) if counter.exists() else 0
if is_orchestrator:
    counter.write_text(str(index + 1))
    decision = json.loads((root / "decisions.json").read_text())[index]
    if decision == "FAIL":
        sys.exit(9)
    output = json.dumps(decision)
else:
    if os.environ.get("FAIL_AGENT") == "1":
        sys.exit(8)
    output = "Resultado publicado en la issue."
Path(args[args.index("-o") + 1]).write_text(output)
"""


def decision(action="completado", role=""):
    """Construye una respuesta del contrato, sin simular evidencia de GitHub."""
    return {
        "accion": action,
        "rol": role,
        "issue": ISSUE,
        "asignacion": ISSUE + "#issuecomment-123" if action == "delegar" else "",
        "objetivo": "Atender la entrega",
        "resumen": "Resultado de prueba",
    }


class OrchestratorTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="test-orquestador-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("scripts", "agentes", "bin"):
            (self.root / directory).mkdir()
        shutil.copy(PROJECT / "run-orquestador.sh", self.root)
        shutil.copy(
            PROJECT / "scripts/orquestador-decision.schema.json",
            self.root / "scripts",
        )
        for source in (PROJECT / "agentes").glob("*.md"):
            shutil.copy(source, self.root / "agentes")
        subprocess.run(
            ["git", "init", "-q", str(self.root)], check=True, capture_output=True
        )
        fake = self.root / "bin/codex"
        fake.write_text(FAKE_CODEX)
        fake.chmod(0o700)
        self.env = {
            **os.environ,
            "PATH": str(self.root / "bin") + os.pathsep + os.environ["PATH"],
            "FAKE_ROOT": str(self.root),
            "ORQUESTADOR_MAX_ITERACIONES": "3",
        }
        self.env.pop("FAIL_AGENT", None)

    def run_launcher(self, decisions, objective="Construir la entrega"):
        (self.root / "decisions.json").write_text(json.dumps(decisions))
        return subprocess.run(
            ["bash", str(self.root / "run-orquestador.sh"), objective],
            env=self.env,
            text=True,
            capture_output=True,
            timeout=15,
        )

    def calls(self):
        path = self.root / "calls.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()]

    def test_delegates_and_checks_result_before_finishing(self):
        result = self.run_launcher([
            decision("delegar", "developer-teams"),
            decision("delegar", "qa-teams"),
            decision(),
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        self.assertEqual(
            [call["orchestrator"] for call in calls],
            [True, False, True, False, True],
        )
        self.assertIn("Actúa como `developer-teams`", calls[1]["prompt"])
        self.assertIn(ISSUE + "#issuecomment-123", calls[1]["prompt"])
        self.assertIn("Comprueba su resultado", calls[2]["prompt"])
        self.assertIn("Actúa como `qa-teams`", calls[3]["prompt"])

    def test_final_evaluation_after_last_allowed_delegation(self):
        self.env["ORQUESTADOR_MAX_ITERACIONES"] = "1"
        result = self.run_launcher([
            decision("delegar", "product-manager"), decision()
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Delegaciones restantes: 0", self.calls()[-1]["prompt"])

    def test_refuses_extra_delegation(self):
        self.env["ORQUESTADOR_MAX_ITERACIONES"] = "1"
        result = self.run_launcher([
            decision("delegar", "product-manager"),
            decision("delegar", "developer-teams"),
        ])
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(len(self.calls()), 3)

    def test_terminal_results_have_distinct_exit_codes(self):
        for action, code in (("bloqueado", 2), ("limite", 3)):
            with self.subTest(action=action):
                counter = self.root / "counter"
                counter.unlink(missing_ok=True)
                result = self.run_launcher([decision(action)])
                self.assertEqual(result.returncode, code, result.stderr)

    def test_failed_agent_is_not_retried(self):
        self.env["FAIL_AGENT"] = "1"
        result = self.run_launcher([decision("delegar", "developer-teams")])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(self.calls()), 2)
        self.assertIn("comprueba la asignación", result.stderr)

    def test_failed_orchestrator_is_not_retried(self):
        result = self.run_launcher(["FAIL"])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(self.calls()), 1)

    def test_invalid_role_never_executes(self):
        result = self.run_launcher([decision("delegar", "../../unexpected")])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(self.calls()), 1)

    def test_assignment_must_belong_to_issue(self):
        invalid = decision("delegar", "qa-teams")
        invalid["asignacion"] = ISSUE + "2#issuecomment-123"
        result = self.run_launcher([invalid])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(self.calls()), 1)

    def test_malformed_decision_never_executes(self):
        invalid = decision("delegar", "qa-teams")
        del invalid["resumen"]
        result = self.run_launcher([invalid])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(self.calls()), 1)

    def test_completion_requires_coordination_reference(self):
        invalid = decision()
        invalid["issue"] = ""
        result = self.run_launcher([invalid])
        self.assertEqual(result.returncode, 1, result.stderr)

    def test_unavailable_github_can_report_block_without_issue(self):
        blocked = decision("bloqueado")
        blocked["issue"] = ""
        result = self.run_launcher([blocked])
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_prompt_is_literal_not_shell(self):
        objective = "$(touch INJECTED) `touch ALSO_INJECTED`\nSegunda línea"
        result = self.run_launcher([decision()], objective)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(objective, self.calls()[0]["prompt"])
        self.assertFalse((self.root / "INJECTED").exists())
        self.assertFalse((self.root / "ALSO_INJECTED").exists())

    def test_invalid_iteration_limit(self):
        self.env["ORQUESTADOR_MAX_ITERACIONES"] = "0"
        result = self.run_launcher([])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse((self.root / "calls.jsonl").exists())

    def test_concurrent_launcher_is_rejected(self):
        with (self.root / ".git/orquestador.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_launcher([])
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertFalse((self.root / "calls.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
