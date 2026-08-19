from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracecontract.ingestion import normalize_input


class IngestionContractTests(unittest.TestCase):
    def test_markdown_normalization_is_atomic_deterministic_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "requirements.md"
            source.write_text(
                "# UC19\n\n## R1 Future dates\nFuture dates are rejected.\n\n"
                "## R2 Ownership\nPatients create entries for themselves.\n",
                encoding="utf-8",
            )

            first = normalize_input(source, "requirement_claim", "markdown-v1")
            second = normalize_input(source, "requirement_claim", "markdown-v1")

            self.assertEqual(first, second)
            self.assertEqual("complete", first["coverage"]["state"])
            self.assertEqual(3, len(first["artifacts"]))
            self.assertEqual("R1 Future dates", first["artifacts"][1]["content"]["heading"])
            self.assertEqual(64, len(first["raw_result_hash"]))

    def test_unsupported_input_is_coverage_not_absence_of_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "scan.pdf"
            source.write_bytes(b"not a text pdf")

            result = normalize_input(source, "requirement_claim", "markdown-v1")

            self.assertEqual([], result["artifacts"])
            self.assertEqual("unsupported", result["coverage"]["state"])
            self.assertEqual(".pdf", result["coverage"]["region"])


if __name__ == "__main__":
    unittest.main()
