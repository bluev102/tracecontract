from __future__ import annotations

import unittest
import hashlib
import json
import tempfile
from pathlib import Path

from tracecontract import PolicyError
from tracecontract.orchestration import (
    candidate_snapshot_hash,
    import_candidate_batch,
    import_approval_batch,
    import_review_batch,
    review_gate_failures,
    run_review_cycle,
)
from tracecontract.agent_runtime import AgentInvocation, FixtureAgentRunner
from tests.test_tracecontract import candidate_graph


def review_batch(graph, role: str, reviewer: str) -> dict:
    return {
        "schema": "tracecontract.review-batch.v1",
        "project_id": graph.project_id,
        "reviewer_role": role,
        "reviewer": reviewer,
        "isolation_id": f"isolated-{role}",
        "candidate_snapshot_hash": candidate_snapshot_hash(graph),
        "peer_verdicts_visible": False,
        "verdicts": [
            {
                "edge_id": edge["id"],
                "source_hash": edge["source_hash"],
                "target_hash": edge["target_hash"],
                "verdict": "supports",
                "claim": f"{role} trace supports {edge['id']}",
                "evidence": [{"kind": f"{role}_review", "provenance": f"{reviewer}/pinned-snapshot"}],
            }
            for edge in graph.edges.values()
        ],
    }


def approval_batch(graph) -> dict:
    return {
        "schema": "tracecontract.approval-batch.v1", "project_id": graph.project_id,
        "approvals": [{
            "edge_id": edge["id"], "source_hash": edge["source_hash"], "target_hash": edge["target_hash"],
            "role": edge["required_role"], "subject": f"human:{edge['required_role']}",
        } for edge in graph.edges.values() if edge["status"] != "rejected"],
    }


class ReviewOrchestrationTests(unittest.TestCase):
    def test_accountable_approval_batch_is_hash_bound_and_cannot_use_reviewer_identity(self) -> None:
        graph, _ = candidate_graph()
        for role in ("forward", "reverse", "adversarial"):
            import_review_batch(graph, review_batch(graph, role, f"reviewer:{role}"))
        approvals = {
            "schema": "tracecontract.approval-batch.v1", "project_id": graph.project_id,
            "approvals": [{
                "edge_id": edge["id"], "source_hash": edge["source_hash"], "target_hash": edge["target_hash"],
                "role": edge["required_role"], "subject": f"human:{edge['required_role']}",
            } for edge in graph.edges.values()],
        }
        imported = import_approval_batch(graph, approvals)
        self.assertEqual(4, len(imported))
        self.assertTrue(all(edge["status"] == "verified" for edge in graph.edges.values()))

    def test_review_cycle_runs_all_roles_then_imports_atomically(self) -> None:
        graph, _ = candidate_graph()
        responses = {role: review_batch(graph, role, f"reviewer:{role}") for role in ("forward", "reverse", "adversarial")}
        with tempfile.TemporaryDirectory() as temp_dir:
            assignment = Path(temp_dir) / "assignment.json"
            assignment.write_text(json.dumps({"candidate_snapshot_hash": candidate_snapshot_hash(graph)}), encoding="utf-8")
            digest = hashlib.sha256(assignment.read_bytes()).hexdigest()
            invocations = [AgentInvocation(
                role=role, input_artifact=assignment, input_hash=digest,
                expected_output_schema={"type": "object"}, command=("fixture", role),
            ) for role in responses]
            result = run_review_cycle(graph, invocations, FixtureAgentRunner(responses))
        self.assertEqual([], review_gate_failures(graph))
        self.assertEqual(["adversarial", "forward", "reverse"], [item["role"] for item in result["agents"]])
        self.assertTrue(all(edge["status"] == "candidate" for edge in graph.edges.values()))

    def test_linker_batch_imports_only_review_required_candidates_and_ignores_confidence_for_maturity(self) -> None:
        from tracecontract import TraceContract
        graph = TraceContract("linker-test")
        source = graph.add_artifact("R", "requirement_claim", {"text": "claim"})
        target = graph.add_artifact("D", "design_claim", {"text": "design"})
        imported = import_candidate_batch(graph, {
            "schema": "tracecontract.candidate-batch.v1", "project_id": graph.project_id,
            "proposer": "agent:linker", "origin": "agent-discovered",
            "coverage": {"state": "partial", "project": "cbm", "generation": "g1", "gaps": ["x.py:4-8"]},
            "candidates": [{
                "edge_id": "E", "type": "detailed_by", "source": "R", "target": "D",
                "source_hash": source["version_hash"], "target_hash": target["version_hash"],
                "required_role": "architect", "retrieved_context": ["span:all"],
                "cited_evidence": [
                    {"kind": "explicit_id", "provenance": "manifest"},
                    {"kind": "document_span", "provenance": "design"},
                ],
                "advisory_rank": 0.999,
            }],
        })
        self.assertEqual(["E"], imported)
        self.assertEqual("candidate", graph.edges["E"]["status"])
        self.assertEqual("E2", graph.edges["E"]["maturity"])
        self.assertTrue(graph.edges["E"]["review_required"])
        self.assertEqual(0.999, graph.edges["E"]["advisory_rank"])
        self.assertEqual("partial", graph.edges["E"]["coverage"]["state"])

    def test_three_blind_review_lanes_are_required_before_approval(self) -> None:
        graph, _ = candidate_graph()
        self.assertIn("EDGE-01: missing forward review", review_gate_failures(graph))
        for role in ("forward", "reverse", "adversarial"):
            import_review_batch(graph, review_batch(graph, role, f"reviewer:{role}"))
        self.assertEqual([], review_gate_failures(graph))
        self.assertTrue(all(edge["status"] == "candidate" for edge in graph.edges.values()))

    def test_review_import_rejects_peer_visibility_and_stale_endpoint_hashes(self) -> None:
        graph, _ = candidate_graph()
        visible = review_batch(graph, "forward", "reviewer:fwd")
        visible["peer_verdicts_visible"] = True
        with self.assertRaisesRegex(PolicyError, "peer verdicts"):
            import_review_batch(graph, visible)

        stale = review_batch(graph, "forward", "reviewer:fwd")
        stale["verdicts"][0]["source_hash"] = "stale"
        with self.assertRaisesRegex(PolicyError, "endpoint hash"):
            import_review_batch(graph, stale)

    def test_malformed_batch_is_rejected_atomically(self) -> None:
        graph, _ = candidate_graph()
        batch = review_batch(graph, "reverse", "reviewer:reverse")
        batch["verdicts"][-1]["target_hash"] = "stale"
        with self.assertRaises(PolicyError):
            import_review_batch(graph, batch)
        self.assertTrue(all(edge["verdicts"] == [] for edge in graph.edges.values()))

    def test_confirmed_counterexample_does_not_prevent_blind_peer_verdict_import(self) -> None:
        graph, _ = candidate_graph()
        adversarial = review_batch(graph, "adversarial", "reviewer:adv")
        adversarial["verdicts"][0]["verdict"] = "contradicts"
        adversarial["verdicts"][0]["reproducer"] = {"outcome": "counterexample_confirmed"}
        import_review_batch(graph, adversarial)
        import_review_batch(graph, review_batch(graph, "forward", "reviewer:fwd"))
        import_review_batch(graph, review_batch(graph, "reverse", "reviewer:rev"))
        edge = graph.edges["EDGE-01"]
        self.assertEqual("rejected", edge["status"])
        self.assertEqual(3, len(edge["verdicts"]))


if __name__ == "__main__":
    unittest.main()
