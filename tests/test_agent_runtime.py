from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tracecontract import PolicyError
from tracecontract.agent_runtime import AgentInvocation, SubprocessAgentRunner


SCHEMA = {
    "type": "object",
    "required": ["ok"],
    "properties": {"ok": {"type": "boolean"}, "cwd": {"type": "string"}},
    "additionalProperties": False,
}


class AgentRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.assignment = self.root / "input.json"
        self.assignment.write_text('{"task":"review"}', encoding="utf-8")
        self.input_hash = hashlib.sha256(self.assignment.read_bytes()).hexdigest()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invocation(self, code: str, **changes: object) -> AgentInvocation:
        values = {
            "role": "forward",
            "input_artifact": self.assignment,
            "input_hash": self.input_hash,
            "expected_output_schema": SCHEMA,
            "command": [sys.executable, "-c", code],
            "timeout_seconds": 2,
            "max_stdout_bytes": 4096,
        }
        values.update(changes)
        return AgentInvocation(**values)  # type: ignore[arg-type]

    def test_each_run_uses_a_fresh_disposable_directory(self) -> None:
        code = "import json,os; print(json.dumps({'ok':True,'cwd':os.getcwd()}))"
        runner = SubprocessAgentRunner(self.root)
        first = runner.run(self.invocation(code))
        second = runner.run(self.invocation(code))
        self.assertTrue(first.accepted)
        self.assertTrue(second.accepted)
        self.assertNotEqual(first.workdir, second.workdir)
        self.assertFalse(Path(first.workdir).exists())
        self.assertFalse(Path(second.workdir).exists())

    def test_hash_mismatch_is_rejected_before_process_spawn(self) -> None:
        marker = self.root / "spawned"
        code = f"from pathlib import Path; Path({str(marker)!r}).touch()"
        with self.assertRaisesRegex(PolicyError, "input artifact hash mismatch"):
            SubprocessAgentRunner(self.root).run(self.invocation(code, input_hash="0" * 64))
        self.assertFalse(marker.exists())

    def test_malformed_and_schema_mismatched_outputs_are_rejected(self) -> None:
        malformed = SubprocessAgentRunner(self.root).run(self.invocation("print('not-json')"))
        self.assertIsNone(malformed.output)
        self.assertIn("malformed_json_output", malformed.protocol_deviations)
        mismatch = SubprocessAgentRunner(self.root).run(self.invocation("print('{\"ok\": 1}')"))
        self.assertIsNone(mismatch.output)
        self.assertIn("output_schema_mismatch", mismatch.protocol_deviations)

    def test_timeout_kills_the_agent(self) -> None:
        result = SubprocessAgentRunner(self.root).run(
            self.invocation("import time; time.sleep(5)", timeout_seconds=0.05)
        )
        self.assertIn("time_budget_exhausted", result.protocol_deviations)
        self.assertLess(result.elapsed_seconds, 2)

    def test_only_assignment_is_visible_not_hidden_input_siblings(self) -> None:
        (self.root / "hidden-tests.json").write_text("secret", encoding="utf-8")
        code = (
            "import json,os,pathlib; "
            "names=sorted(p.name for p in pathlib.Path('.').iterdir()); "
            "print(json.dumps({'ok': names == ['assignment.json']}))"
        )
        result = SubprocessAgentRunner().run(self.invocation(code))
        self.assertTrue(result.accepted)
        self.assertEqual({"ok": True}, result.output)
        self.assertIn("raw sockets", result.telemetry["network_control"])

    def test_exactly_one_json_document_and_stdout_limit(self) -> None:
        multiple = SubprocessAgentRunner(self.root).run(
            self.invocation("print('{}'); print('{}')", expected_output_schema={"type": "object"})
        )
        self.assertIn("multiple_json_documents", multiple.protocol_deviations)
        large = SubprocessAgentRunner(self.root).run(
            self.invocation("print('x' * 10000)", max_stdout_bytes=64)
        )
        self.assertEqual(64, large.stdout_bytes)
        self.assertIn("stdout_limit_exceeded", large.protocol_deviations)


if __name__ == "__main__":
    unittest.main()
