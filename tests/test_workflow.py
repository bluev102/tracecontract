from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tracecontract.workflow import run_workflow
from tracecontract import PolicyError
from tracecontract.orchestration import candidate_snapshot_hash
from tracecontract.orchestration import import_candidate_batch
from tracecontract import TraceContract
from tracecontract.agent_runtime import FixtureAgentRunner
from tests.test_orchestration import approval_batch, review_batch
from tests.test_tracecontract import candidate_graph


ROOT = Path(__file__).resolve().parents[1]


class WorkflowAcceptanceTests(unittest.TestCase):
    def test_agent_orchestrated_mode_runs_linker_reviewers_and_approval_import(self) -> None:
        _, fixture_data = candidate_graph()
        empty_fixture = {**fixture_data, "edges": []}
        candidate_batch = {
            "schema": "tracecontract.candidate-batch.v1", "project_id": fixture_data["project_id"],
            "proposer": "agent:linker", "origin": "agent-discovered",
            "coverage": {"state": "complete", "project": "cbm", "generation": "g1", "gaps": []},
            "candidates": [{
                "edge_id": edge["id"], "type": edge["type"], "source": edge["source"], "target": edge["target"],
                "source_hash": next(a for a in candidate_graph()[0].artifacts.values() if a["id"] == edge["source"])["version_hash"],
                "target_hash": next(a for a in candidate_graph()[0].artifacts.values() if a["id"] == edge["target"])["version_hash"],
                "required_role": edge["required_role"], "retrieved_context": [],
                "cited_evidence": edge["evidence"], "advisory_rank": 0.5,
            } for edge in fixture_data["edges"]],
        }
        staged = TraceContract.from_fixture(empty_fixture)
        import_candidate_batch(staged, candidate_batch)
        responses = {"candidate_linker": candidate_batch}
        responses.update({role: review_batch(staged, role, f"agent:{role}") for role in ("forward", "reverse", "adversarial")})
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fixture_payload = json.dumps(empty_fixture, sort_keys=True).encode()
            (root / "fixture.json").write_bytes(fixture_payload)
            assignment_payload = json.dumps({"task": "link"}, sort_keys=True).encode()
            (root / "candidate-assignment.json").write_bytes(assignment_payload)
            review_payload = json.dumps({"snapshot": candidate_snapshot_hash(staged)}, sort_keys=True).encode()
            (root / "review-assignment.json").write_bytes(review_payload)
            approvals_payload = json.dumps(approval_batch(staged), sort_keys=True).encode()
            (root / "approvals.json").write_bytes(approvals_payload)
            digest = lambda payload: __import__("hashlib").sha256(payload).hexdigest()
            manifest = {
                "schema": "tracecontract.run-manifest.v1", "run_id": "orchestrated-1",
                "project_id": staged.project_id, "task_id": "restore",
                "inputs": {
                    "fixture": {"path": "fixture.json", "sha256": digest(fixture_payload)},
                    "candidate_assignment": {"path": "candidate-assignment.json", "sha256": digest(assignment_payload), "command": ["fixture", "candidate_linker"]},
                    "review_assignments": [{"role": role, "path": "review-assignment.json", "sha256": digest(review_payload), "command": ["fixture", role]} for role in ("forward", "reverse", "adversarial")],
                    "approvals": {"path": "approvals.json", "sha256": digest(approvals_payload)},
                },
                "policy_version": "tracecontract-policy-v1", "configuration": {"mode": "agent-orchestrated-certification"},
            }
            summary = run_workflow(manifest, root, root / "out", agent_runner=FixtureAgentRunner(responses))
            self.assertEqual("complete", summary["stages"]["candidate_linking"])
            self.assertEqual("complete", summary["stages"]["agent_execution"])
            self.assertTrue((root / "out" / "candidate-agent.json").is_file())

    def test_workflow_persists_pinned_codebase_memory_observations(self) -> None:
        _, fixture_data = candidate_graph()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fixture_payload = json.dumps(fixture_data, sort_keys=True).encode()
            (root / "fixture.json").write_bytes(fixture_payload)
            provider_payload = json.dumps({
                "schema": "tracecontract.code-provider-result.v1", "project": "itrust-index", "generation": "g1",
                "pagination_complete": True, "coverage": {"state": "complete", "candidate_paths": ["Food.java"], "gaps": []},
                "facts": [{"qualified_symbol": "Food.create", "normalized_symbol_hash": "sym", "source_span": {"path": "Food.java", "start_line": 1, "end_line": 2, "loc": 2}}],
            }, separators=(",", ":")).encode()
            (root / "cbm.json").write_bytes(provider_payload)
            manifest = {
                "schema": "tracecontract.run-manifest.v1", "run_id": "cbm-1", "project_id": "itrust2-uc19", "task_id": "restore",
                "inputs": {
                    "fixture": {"path": "fixture.json", "sha256": __import__("hashlib").sha256(fixture_payload).hexdigest()},
                    "code_provider_result": {"path": "cbm.json", "sha256": __import__("hashlib").sha256(provider_payload).hexdigest()},
                },
                "policy_version": "tracecontract-policy-v1",
                "configuration": {"mode": "certification-only", "code_intelligence_request": {
                    "repository": "itrust2", "commit": "abc", "project": "itrust-index", "generation": "g1",
                    "provider_version": "2", "adapter_configuration": {"mode": "full"},
                }},
            }
            summary = run_workflow(manifest, root, root / "out")
            observations = json.loads((root / "out" / "code-observations.json").read_text(encoding="utf-8"))
            self.assertEqual("complete", summary["stages"]["code_observation"])
            self.assertEqual("g1", observations["generation"])
            self.assertEqual(__import__("hashlib").sha256(provider_payload).hexdigest(), observations["raw_result_hash"])

    def test_agent_reviewed_mode_executes_role_runner_before_certification(self) -> None:
        graph, fixture_data = candidate_graph()
        responses = {role: review_batch(graph, role, f"agent:{role}") for role in ("forward", "reverse", "adversarial")}
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fixture_payload = json.dumps(fixture_data, sort_keys=True).encode()
            (root / "fixture.json").write_bytes(fixture_payload)
            assignment_payload = json.dumps({"snapshot": candidate_snapshot_hash(graph)}, sort_keys=True).encode()
            (root / "assignment.json").write_bytes(assignment_payload)
            digest = __import__("hashlib").sha256(assignment_payload).hexdigest()
            approval_payload = json.dumps(approval_batch(graph), sort_keys=True).encode()
            (root / "approvals.json").write_bytes(approval_payload)
            manifest = {
                "schema": "tracecontract.run-manifest.v1", "run_id": "agent-reviewed-1",
                "project_id": graph.project_id, "task_id": "restore-uc19",
                "inputs": {
                    "fixture": {"path": "fixture.json", "sha256": __import__("hashlib").sha256(fixture_payload).hexdigest()},
                    "review_assignments": [{"role": role, "path": "assignment.json", "sha256": digest, "command": ["fixture", role]} for role in responses],
                    "approvals": {"path": "approvals.json", "sha256": __import__("hashlib").sha256(approval_payload).hexdigest()},
                },
                "policy_version": "tracecontract-policy-v1",
                "configuration": {"mode": "agent-reviewed-certification"},
            }
            summary = run_workflow(manifest, root, root / "out", agent_runner=FixtureAgentRunner(responses))
            cycle = json.loads((root / "out" / "review-cycle.json").read_text(encoding="utf-8"))
            self.assertEqual("complete", summary["stages"]["agent_execution"])
            self.assertEqual(["adversarial", "forward", "reverse"], [agent["role"] for agent in cycle["agents"]])

    def test_reviewed_mode_imports_three_isolated_agent_artifacts_before_certification(self) -> None:
        graph, fixture_data = candidate_graph()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fixture_path = root / "fixture.json"
            fixture_bytes = json.dumps(fixture_data, ensure_ascii=False, sort_keys=True).encode("utf-8")
            fixture_path.write_bytes(fixture_bytes)
            review_descriptors = []
            for role in ("forward", "reverse", "adversarial"):
                batch = {
                    "schema": "tracecontract.review-batch.v1",
                    "project_id": graph.project_id,
                    "reviewer_role": role,
                    "reviewer": f"agent:{role}",
                    "isolation_id": f"session:{role}",
                    "candidate_snapshot_hash": candidate_snapshot_hash(graph),
                    "peer_verdicts_visible": False,
                    "verdicts": [{
                        "edge_id": edge["id"], "source_hash": edge["source_hash"], "target_hash": edge["target_hash"],
                        "verdict": "supports", "claim": f"{role} supports {edge['id']}",
                        "evidence": [{"kind": f"{role}_review", "provenance": f"agent:{role}/pinned"}],
                    } for edge in graph.edges.values()],
                }
                path = root / f"{role}.json"
                payload = json.dumps(batch, ensure_ascii=False, sort_keys=True).encode("utf-8")
                path.write_bytes(payload)
                review_descriptors.append({"path": path.name, "sha256": __import__("hashlib").sha256(payload).hexdigest()})
            approval_payload = json.dumps(approval_batch(graph), ensure_ascii=False, sort_keys=True).encode("utf-8")
            (root / "approvals.json").write_bytes(approval_payload)
            manifest = {
                "schema": "tracecontract.run-manifest.v1", "run_id": "reviewed-1",
                "project_id": graph.project_id, "task_id": "restore-uc19",
                "inputs": {
                    "fixture": {"path": fixture_path.name, "sha256": __import__("hashlib").sha256(fixture_bytes).hexdigest()},
                    "reviews": review_descriptors,
                    "approvals": {"path": "approvals.json", "sha256": __import__("hashlib").sha256(approval_payload).hexdigest()},
                },
                "policy_version": "tracecontract-policy-v1",
                "configuration": {"mode": "reviewed-certification"},
            }
            summary = run_workflow(manifest, root, root / "out")
            state = json.loads((root / "out" / "evidence-state.json").read_text(encoding="utf-8"))
            self.assertEqual("complete", summary["stages"]["independent_review"])
            self.assertEqual(3, len(state["review_sessions"]))
            self.assertTrue(all(edge["status"] == "verified" for edge in state["edges"]))

    def test_successful_run_bundle_rejects_manifest_reuse_with_changed_identity(self) -> None:
        manifest = {
            "schema": "tracecontract.run-manifest.v1", "run_id": "run-1",
            "project_id": "itrust2-uc19", "task_id": "restore-uc19",
            "inputs": {"fixture": {"path": "examples/uc19.json", "sha256": "4850d9a4d797b07919f6d5fe7d33d6fb325afcac54f4fa2a7736742e7995a09a"}},
            "policy_version": "tracecontract-policy-v1", "configuration": {},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "run"
            run_workflow(manifest, ROOT, output)
            changed = {**manifest, "run_id": "run-2"}
            with self.assertRaisesRegex(PolicyError, "immutable successful run"):
                run_workflow(changed, ROOT, output)

    def test_pinned_manifest_runs_certification_and_context_compilation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            manifest = {
                "schema": "tracecontract.run-manifest.v1",
                "run_id": "uc19-acceptance-001",
                "project_id": "itrust2-uc19",
                "task_id": "restore-uc19",
                "inputs": {
                    "fixture": {
                        "path": "examples/uc19.json",
                        "sha256": "4850d9a4d797b07919f6d5fe7d33d6fb325afcac54f4fa2a7736742e7995a09a",
                    }
                },
                "policy_version": "tracecontract-policy-v1",
                "configuration": {"mode": "certification-only"},
            }

            summary = run_workflow(manifest, ROOT, output_dir)

            self.assertEqual("certified", summary["status"])
            self.assertEqual("uc19-acceptance-001", summary["run_id"])
            self.assertEqual(
                ["certification", "context_compilation", "ingest", "reporting"],
                sorted(summary["stages"]),
            )
            self.assertTrue((output_dir / "certified-rtm.json").is_file())
            self.assertTrue((output_dir / "migration-context.json").is_file())
            self.assertTrue((output_dir / "run-manifest.json").is_file())
            report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual("not_evaluated", report["hypotheses"]["H2"])

    def test_cli_rejects_a_changed_pinned_input_with_machine_readable_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fixture = temp / "fixture.json"
            fixture.write_text("{}", encoding="utf-8")
            manifest = temp / "manifest.json"
            manifest.write_text(json.dumps({
                "schema": "tracecontract.run-manifest.v1",
                "run_id": "bad-pin",
                "project_id": "itrust2-uc19",
                "task_id": "restore-uc19",
                "inputs": {"fixture": {"path": "fixture.json", "sha256": "0" * 64}},
                "policy_version": "tracecontract-policy-v1",
                "configuration": {},
            }), encoding="utf-8")
            result = __import__("subprocess").run(
                [__import__("sys").executable, "-m", "tracecontract", "run", "--manifest", str(manifest), "--output-dir", str(temp / "out")],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(10, result.returncode)
            diagnostic = json.loads(result.stdout)
            self.assertEqual("input_invalid", diagnostic["code"])
            self.assertIn("hash mismatch", diagnostic["error"])

    def test_controlled_mode_adds_blinded_evaluation_and_raw_observations(self) -> None:
        command = [__import__("sys").executable, "-c", "import json; print(json.dumps({'passed': 1, 'total': 2, 'costs': {'implementation': 1}}))"]
        manifest = {
            "schema": "tracecontract.run-manifest.v1", "run_id": "experiment-1",
            "project_id": "itrust2-uc19", "task_id": "restore-uc19",
            "inputs": {"fixture": {"path": "examples/uc19.json", "sha256": "4850d9a4d797b07919f6d5fe7d33d6fb325afcac54f4fa2a7736742e7995a09a"}},
            "policy_version": "tracecontract-policy-v1",
            "configuration": {
                "mode": "controlled-experiment",
                "experiment": {
                    "seed": 1, "budget": {"time_seconds": 5, "tool_calls": 1, "tokens": 100},
                    "model": {"provider": "local-test", "name": "fixture"}, "tools": ["python"],
                    "arms": {"baseline": {"command": command}, "treatment": {"command": command}},
                },
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "run"
            summary = run_workflow(manifest, ROOT, output)
            self.assertEqual("complete", summary["stages"]["evaluation"])
            experiment = json.loads((output / "experiment-result.json").read_text(encoding="utf-8"))
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(0.5, report["metrics"]["hidden_test_pass_rate"])
            self.assertEqual("insufficient_trials", report["hypotheses"]["H2"])
            self.assertEqual({"X", "Y"}, {trial["label"] for trial in experiment["trials"]})


if __name__ == "__main__":
    unittest.main()
