from __future__ import annotations

import unittest

from tracecontract.code_intelligence import normalize_code_facts, normalize_codebase_memory_result
from tracecontract import PolicyError


class CodeIntelligenceAdapterTests(unittest.TestCase):
    def test_codebase_memory_result_preserves_generation_coverage_and_raw_bytes_hash(self) -> None:
        import hashlib
        import json
        raw = json.dumps({
            "schema": "tracecontract.code-provider-result.v1",
            "project": "itrust-index", "generation": "gen-7", "pagination_complete": True,
            "coverage": {"state": "partial", "candidate_paths": ["src/Food.java"], "gaps": [{"path": "src/Food.java", "ranges": [[31, 40]], "reason": "parse_partial"}]},
            "facts": [{"qualified_symbol": "Food.create", "normalized_symbol_hash": "sym", "source_span": {"path": "src/Food.java", "start_line": 1, "end_line": 30, "loc": 30}}],
        }, separators=(",", ":")).encode("utf-8")
        result = normalize_codebase_memory_result(raw, {
            "repository": "itrust2", "commit": "abc", "project": "itrust-index", "generation": "gen-7",
            "provider_version": "2.0", "adapter_configuration": {"queries": ["Food"]},
        })
        self.assertEqual(hashlib.sha256(raw).hexdigest(), result["raw_result_hash"])
        self.assertEqual("gen-7", result["generation"])
        self.assertEqual("partial", result["coverage"]["state"])
        self.assertEqual([[31, 40]], result["coverage"]["gaps"][0]["ranges"])

    def test_codebase_memory_cannot_claim_complete_coverage_with_unread_pages(self) -> None:
        import json
        raw = json.dumps({
            "schema": "tracecontract.code-provider-result.v1", "project": "p", "generation": "g",
            "pagination_complete": False, "coverage": {"state": "complete", "candidate_paths": [], "gaps": []}, "facts": [],
        }).encode("utf-8")
        with self.assertRaisesRegex(PolicyError, "pagination"):
            normalize_codebase_memory_result(raw, {
                "repository": "r", "commit": "c", "project": "p", "generation": "g",
                "provider_version": "1", "adapter_configuration": {},
            })

    def test_observed_symbols_have_stable_commit_bound_identity_and_coverage(self) -> None:
        facts = [{
            "qualified_symbol": "example.FoodDiaryService.create",
            "normalized_symbol_hash": "sym-123",
            "source_span": {"path": "src/FoodDiaryService.java", "start_line": 10, "end_line": 30, "loc": 21},
        }]
        first = normalize_code_facts("itrust2", "abc123", "cbm", "1.2.0", {"language": "java"}, facts, 0.92)
        second = normalize_code_facts("itrust2", "abc123", "cbm", "1.2.0", {"language": "java"}, reversed(facts), 0.92)
        self.assertEqual(first, second)
        self.assertEqual(0.92, first["coverage"]["indexed_fraction"])
        self.assertEqual("abc123", first["facts"][0]["commit"])
        self.assertEqual(64, len(first["raw_result_hash"]))

    def test_adapter_rejects_unqualified_or_spanless_code_observation(self) -> None:
        with self.assertRaisesRegex(PolicyError, "qualified_symbol"):
            normalize_code_facts("repo", "abc", "provider", "1", {}, [{"normalized_symbol_hash": "x"}], 1.0)


if __name__ == "__main__":
    unittest.main()
