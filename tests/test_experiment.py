from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from tracecontract.experiment import run_experiment


class ExperimentHarnessTests(unittest.TestCase):
    def test_arms_run_in_fresh_blinded_process_directories_with_identical_budget(self) -> None:
        command = [sys.executable, "-c", "import json,os; print(json.dumps({'passed': 1, 'total': 1, 'cwd': os.getcwd()}))"]
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_experiment({
                "seed": 17,
                "budget": {"time_seconds": 5, "tool_calls": 1, "tokens": 100},
                "model": {"provider": "local-test", "name": "fixture"},
                "tools": ["python"],
                "arms": {"baseline": {"command": command}, "treatment": {"command": command}},
            }, Path(temp_dir))

        self.assertEqual({"X", "Y"}, {trial["label"] for trial in result["trials"]})
        self.assertEqual(2, len({trial["result"]["cwd"] for trial in result["trials"]}))
        self.assertTrue(all(trial["budget"] == result["budget"] for trial in result["trials"]))
        self.assertNotIn("baseline", str(result["trials"]))
        self.assertNotIn("treatment", str(result["trials"]))


if __name__ == "__main__":
    unittest.main()
