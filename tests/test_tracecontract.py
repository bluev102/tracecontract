from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tracecontract import CertificationError, PolicyError, TraceContract


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "uc19.json"


def candidate_graph() -> tuple[TraceContract, dict]:
    fixture = TraceContract.load_fixture(FIXTURE)
    return TraceContract.from_fixture(fixture), fixture


def verified_graph() -> tuple[TraceContract, dict]:
    graph, fixture = candidate_graph()
    for edge in fixture["edges"]:
        graph.approve(edge["id"], edge["required_role"], edge["approver"])
    return graph, fixture


class TraceContractPolicyTests(unittest.TestCase):
    def test_identical_artifact_reingest_is_idempotent_but_identity_collision_fails(self) -> None:
        graph = TraceContract("ingest-test")
        first = graph.add_artifact("R", "requirement_claim", {"text": "same"})
        second = graph.add_artifact("R", "requirement_claim", {"text": "same"})
        self.assertEqual(first, second)
        self.assertEqual(1, len(graph.artifacts))
        with self.assertRaisesRegex(PolicyError, "identity collision"):
            graph.add_artifact("R", "requirement_claim", {"text": "changed"})

    def test_executable_evidence_must_match_pinned_commit_and_environment(self) -> None:
        graph = TraceContract("binding-test")
        graph.add_artifact("C", "code_symbol", {"symbol": "Service.run", "commit": "abc"})
        graph.add_artifact("T", "test_case", {"name": "run", "commit": "abc", "environment": "jdk17"})
        graph.propose_edge("E", "verified_by", "C", "T", "qa", [
            {"kind": "static_span", "provenance": "adapter-v1"},
            {"kind": "test_result", "outcome": "pass", "commit": "wrong", "environment": "jdk17", "provenance": "runner-v1"},
        ])
        graph.approve("E", "qa", "qa:1")
        with self.assertRaisesRegex(CertificationError, "pinned commit/environment"):
            graph.canonical_rtm_bytes()

    def test_discovery_and_review_are_auditable_and_separated(self) -> None:
        graph = TraceContract("review-test")
        graph.add_artifact("R", "requirement_claim", {"text": "future dates rejected"})
        graph.add_artifact("D", "design_claim", {"text": "validate before save"})
        graph.propose_edge(
            "E", "detailed_by", "R", "D", "architect",
            proposer="linker:1", origin="semantic_retrieval",
            retrieved_context=["span:1", "span:2"],
        )

        with self.assertRaisesRegex(PolicyError, "cannot review its own proposal"):
            graph.submit_verdict(
                "E", "forward", "linker:1", "supports", "requirement is detailed",
                [{"kind": "document_span", "provenance": "design-v1"}],
            )
        edge = graph.submit_verdict(
            "E", "forward", "reviewer:fwd", "supports", "requirement is detailed",
            [{"kind": "document_span", "provenance": "design-v1"}],
        )
        self.assertEqual("candidate", edge["status"])
        self.assertEqual(1, len(edge["verdicts"]))
        self.assertEqual(["span:1", "span:2"], edge["retrieved_context"])
        self.assertEqual(1, len(edge["evidence"]))

    def test_agent_discovered_edge_cannot_be_approved_before_three_independent_reviews(self) -> None:
        graph = TraceContract("agent-policy")
        graph.add_artifact("R", "requirement_claim", {"text": "claim"})
        graph.add_artifact("D", "design_claim", {"text": "design"})
        graph.propose_edge("E", "detailed_by", "R", "D", "architect", [
            {"kind": "explicit_id", "provenance": "manifest"},
            {"kind": "document_span", "provenance": "design"},
        ], proposer="agent:linker", origin="agent-discovered", review_required=True)
        with self.assertRaisesRegex(PolicyError, "missing forward review"):
            graph.approve("E", "architect", "architect:1")
        for role in ("forward", "reverse", "adversarial"):
            graph.submit_verdict("E", role, f"agent:{role}", "supports", "supported", [
                {"kind": f"{role}_review", "provenance": f"{role}/pinned"}
            ])
        with self.assertRaisesRegex(PolicyError, "reviewer cannot approve"):
            graph.approve("E", "architect", "agent:forward")
        self.assertEqual("verified", graph.approve("E", "architect", "architect:1")["status"])

    def test_wrong_role_and_single_source_cannot_approve(self) -> None:
        graph = TraceContract("policy-test")
        graph.add_artifact("R", "requirement_claim", {"text": "servings > 0"})
        graph.add_artifact("D", "design_claim", {"text": "validate servings"})
        graph.propose_edge("E", "detailed_by", "R", "D", "architect", [
            {"kind": "document_span", "provenance": "design-v1"}
        ])
        with self.assertRaisesRegex(PolicyError, "requires role architect"):
            graph.approve("E", "project_manager", "pm:1")
        with self.assertRaisesRegex(PolicyError, "two independent"):
            graph.approve("E", "architect", "architect:1")

    def test_dispute_blocks_certification(self) -> None:
        graph, _ = verified_graph()
        graph.dispute("EDGE-01", "design does not cover timezone boundary")
        with self.assertRaisesRegex(CertificationError, "disputed"):
            graph.canonical_rtm_bytes()

    def test_design_change_stales_only_affected_subgraph(self) -> None:
        graph, _ = verified_graph()
        affected = graph.change_artifact("DD-19.7", {"text": "Validate in patient timezone", "component": "FoodDiaryService"})
        self.assertEqual(["EDGE-02", "EDGE-01", "EDGE-03"], affected)
        self.assertEqual("stale", graph.edges["EDGE-01"]["status"])
        self.assertEqual("stale", graph.edges["EDGE-02"]["status"])
        self.assertEqual("stale", graph.edges["EDGE-03"]["status"])
        self.assertEqual("verified", graph.edges["EDGE-04"]["status"])
        self.assertEqual("requirement_claim", graph.artifacts["REQ-UNRELATED"]["kind"])

    def test_reverification_binds_new_endpoint_hash_without_overwriting_history(self) -> None:
        graph, _ = verified_graph()
        old_hash = graph.edges["EDGE-01"]["target_hash"]
        graph.change_artifact("DD-19.7", {"text": "Validate in patient timezone", "component": "FoodDiaryService"})

        edge = graph.reverify("EDGE-01", [
            {"kind": "explicit_id", "value": "UC19/R-19.4", "provenance": "new manifest"},
            {"kind": "document_span", "value": "DD section 8", "provenance": "new design snapshot"},
        ], "architect", "architect:demo")

        self.assertEqual("reverified", edge["status"])
        self.assertNotEqual(old_hash, edge["target_hash"])
        self.assertEqual(old_hash, edge["reverification_history"][0]["target_hash"])

    def test_canonical_outputs_are_byte_identical(self) -> None:
        graph, fixture = verified_graph()
        first = graph.canonical_rtm_bytes()
        second = graph.canonical_rtm_bytes()
        self.assertEqual(first, second)
        contract_a = graph.context_contract_bytes(fixture["migration_unit"], fixture["constraints"], fixture["unknowns"])
        contract_b = graph.context_contract_bytes(fixture["migration_unit"], reversed(fixture["constraints"]), fixture["unknowns"])
        self.assertEqual(contract_a, contract_b)

    def test_change_context_preserves_verified_regression_surface(self) -> None:
        graph, _ = verified_graph()

        contract = json.loads(graph.change_context_contract_bytes(
            changed_artifacts=["REQ-19.4"],
            change_id="nutrition-summary",
        ))

        self.assertEqual("tracecontract.change-context.v1", contract["schema"])
        self.assertEqual(["REQ-19.4"], contract["changed_artifacts"])
        self.assertEqual(["CODE-19.12"], contract["impacted_code_symbols"])
        self.assertEqual(["TEST-19.9"], contract["regression_surface"])
        self.assertIn("prior_verified_behavior_preserved", contract["release_gates"])


class TraceContractCliTests(unittest.TestCase):
    def test_demo_runs_complete_certification_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [sys.executable, "-m", "tracecontract", "demo", "--fixture", str(FIXTURE), "--output-dir", temp_dir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr or result.stdout)
            summary = json.loads(result.stdout)
            self.assertEqual("certified", summary["status"])
            rtm = json.loads((Path(temp_dir) / "certified-rtm.json").read_text(encoding="utf-8"))
            context = json.loads((Path(temp_dir) / "migration-context.json").read_text(encoding="utf-8"))
            self.assertEqual(4, len(rtm["edges"]))
            self.assertEqual(["TEST-19.9"], context["executable_tests"])


if __name__ == "__main__":
    unittest.main()
