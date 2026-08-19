from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .core import PolicyError, TraceContract, _canonical_bytes
from .experiment import run_experiment
from .metrics import summarize_trials
from .orchestration import candidate_snapshot_hash, import_approval_batch, import_candidate_batch, import_review_batch, review_gate_failures, run_review_cycle
from .agent_runtime import AgentInvocation, AgentRunner, SubprocessAgentRunner
from .code_intelligence import normalize_codebase_memory_result


RUN_MANIFEST_SCHEMA = "tracecontract.run-manifest.v1"


def _pinned_input(root: Path, descriptor: dict[str, Any]) -> Path:
    try:
        relative_path = descriptor["path"]
        expected_hash = descriptor["sha256"]
    except KeyError as exc:
        raise PolicyError(f"pinned input is missing {exc.args[0]}") from exc
    path = (root / relative_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PolicyError(f"input escapes workspace root: {relative_path}") from exc
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise PolicyError(
            f"input hash mismatch for {relative_path}: expected {expected_hash}, got {actual_hash}"
        )
    return path


def run_workflow(
    manifest: dict[str, Any],
    root: Path,
    output_dir: Path,
    *,
    agent_runner: AgentRunner | None = None,
) -> dict[str, Any]:
    """Run the pinned TraceContract acceptance seam, optionally with isolated agents."""
    if manifest.get("schema") != RUN_MANIFEST_SCHEMA:
        raise PolicyError(f"unsupported run manifest schema: {manifest.get('schema')}")
    required = ("run_id", "project_id", "task_id", "inputs", "policy_version", "configuration")
    missing = [field for field in required if field not in manifest]
    if missing:
        raise PolicyError(f"run manifest missing fields: {', '.join(missing)}")
    if manifest["policy_version"] != TraceContract.POLICY_VERSION:
        raise PolicyError(f"unsupported policy version: {manifest['policy_version']}")
    manifest_bytes = _canonical_bytes(manifest)
    persisted_manifest = output_dir / "run-manifest.json"
    if (output_dir / "report.json").exists() and persisted_manifest.exists():
        if persisted_manifest.read_bytes() != manifest_bytes:
            raise PolicyError("immutable successful run cannot be reused with a changed manifest")

    fixture_path = _pinned_input(root, manifest["inputs"]["fixture"])
    fixture = TraceContract.load_fixture(fixture_path)
    if fixture["project_id"] != manifest["project_id"]:
        raise PolicyError("manifest project_id does not match fixture")
    graph = TraceContract.from_fixture(fixture)
    configuration = manifest["configuration"]
    code_observations: dict[str, Any] | None = None
    if "code_provider_result" in manifest["inputs"]:
        provider_path = _pinned_input(root, manifest["inputs"]["code_provider_result"])
        request = configuration.get("code_intelligence_request")
        if not isinstance(request, dict):
            raise PolicyError("code_provider_result requires code_intelligence_request configuration")
        code_observations = normalize_codebase_memory_result(provider_path.read_bytes(), request)
    mode = configuration.get("mode", "certification-only")
    agent_orchestrated = mode == "agent-orchestrated-certification"
    reviewed = mode in {"reviewed-certification", "agent-reviewed-certification", "agent-orchestrated-certification"}
    review_cycle_result: dict[str, Any] | None = None
    candidate_agent_result: dict[str, Any] | None = None
    active_runner = agent_runner
    if mode in {"agent-reviewed-certification", "agent-orchestrated-certification"}:
        active_runner = active_runner or SubprocessAgentRunner(output_dir / ".agent-work")
    if agent_orchestrated:
        descriptor = manifest["inputs"].get("candidate_assignment")
        if not isinstance(descriptor, dict):
            raise PolicyError("agent-orchestrated-certification requires a pinned candidate assignment")
        assignment_path = _pinned_input(root, descriptor)
        invocation = AgentInvocation(
            role="candidate_linker", input_artifact=assignment_path, input_hash=descriptor["sha256"],
            expected_output_schema={"type": "object"}, command=descriptor.get("command", ()),
            command_identity_hash=descriptor.get("command_identity_hash"),
            timeout_seconds=float(descriptor.get("timeout_seconds", 60)),
            max_stdout_bytes=int(descriptor.get("max_stdout_bytes", 1_000_000)),
        )
        result = active_runner.run(invocation)  # type: ignore[union-attr]
        if not result.accepted:
            raise PolicyError("candidate linker failed: " + ", ".join(result.protocol_deviations))
        imported = import_candidate_batch(graph, result.output)
        candidate_agent_result = {
            "schema": "tracecontract.candidate-agent-result.v1",
            "role": result.role,
            "input_hash": result.input_hash,
            "command_hash": result.command_hash,
            "stdout_hash": result.stdout_hash,
            "stderr_hash": result.stderr_hash,
            "candidate_snapshot_hash": candidate_snapshot_hash(graph),
            "imported_edges": imported,
            "protocol_deviations": list(result.protocol_deviations),
        }
    if mode == "reviewed-certification":
        review_descriptors = manifest["inputs"].get("reviews")
        if not isinstance(review_descriptors, list) or not review_descriptors:
            raise PolicyError("reviewed-certification mode requires pinned review inputs")
        for descriptor in review_descriptors:
            review_path = _pinned_input(root, descriptor)
            import_review_batch(graph, json.loads(review_path.read_text(encoding="utf-8")))
        failures = review_gate_failures(graph)
        if failures:
            raise PolicyError("independent review gate failed: " + "; ".join(failures))
    elif mode in {"agent-reviewed-certification", "agent-orchestrated-certification"}:
        assignment_descriptors = manifest["inputs"].get("review_assignments")
        if not isinstance(assignment_descriptors, list) or not assignment_descriptors:
            raise PolicyError("agent-reviewed-certification mode requires pinned review assignments")
        invocations = []
        for descriptor in assignment_descriptors:
            assignment_path = _pinned_input(root, descriptor)
            invocations.append(AgentInvocation(
                role=descriptor.get("role", ""),
                input_artifact=assignment_path,
                input_hash=descriptor["sha256"],
                expected_output_schema={"type": "object"},
                command=descriptor.get("command", ()),
                command_identity_hash=descriptor.get("command_identity_hash"),
                timeout_seconds=float(descriptor.get("timeout_seconds", 60)),
                max_stdout_bytes=int(descriptor.get("max_stdout_bytes", 1_000_000)),
            ))
        review_cycle_result = run_review_cycle(graph, invocations, active_runner)  # type: ignore[arg-type]
    if reviewed:
        approval_descriptor = manifest["inputs"].get("approvals")
        if not isinstance(approval_descriptor, dict):
            raise PolicyError("reviewed certification requires a pinned accountable approval batch")
        approval_path = _pinned_input(root, approval_descriptor)
        import_approval_batch(graph, json.loads(approval_path.read_text(encoding="utf-8")))
    else:
        # Backward-compatible mechanism fixture only. Validated modes import a
        # separate accountable approval artifact above.
        for edge in fixture["edges"]:
            if graph.edges[edge["id"]]["status"] == "candidate":
                graph.approve(edge["id"], edge["required_role"], edge["approver"])

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "certified-rtm.json").write_bytes(graph.canonical_rtm_bytes())
    (output_dir / "migration-context.json").write_bytes(
        graph.context_contract_bytes(
            fixture["migration_unit"], fixture.get("constraints", ()), fixture.get("unknowns", ())
        )
    )
    (output_dir / "evidence-state.json").write_bytes(graph.state_bytes())
    (output_dir / "run-manifest.json").write_bytes(manifest_bytes)
    if code_observations is not None:
        (output_dir / "code-observations.json").write_bytes(_canonical_bytes(code_observations))
    if review_cycle_result is not None:
        (output_dir / "review-cycle.json").write_bytes(_canonical_bytes(review_cycle_result))
    if candidate_agent_result is not None:
        (output_dir / "candidate-agent.json").write_bytes(_canonical_bytes(candidate_agent_result))
    hypotheses = {"H1": "not_evaluated", "H2": "not_evaluated", "H3": "not_evaluated", "H4": "mechanism_passed"}
    limitations = ["certification-only run; no controlled A/B results were supplied"]
    metrics = None
    stages = {
        "ingest": "complete",
        "certification": "complete",
        "context_compilation": "complete",
        "reporting": "complete",
    }
    if reviewed:
        stages["candidate_linking"] = "complete"
        stages["independent_review"] = "complete"
    if review_cycle_result is not None:
        stages["agent_execution"] = "complete"
    if code_observations is not None:
        stages["code_observation"] = "complete"
    output_names = [
        "certified-rtm.json", "migration-context.json", "evidence-state.json", "run-manifest.json",
    ]
    if review_cycle_result is not None:
        output_names.append("review-cycle.json")
    if candidate_agent_result is not None:
        output_names.append("candidate-agent.json")
    if code_observations is not None:
        output_names.append("code-observations.json")
    if configuration.get("mode") == "controlled-experiment":
        experiment_configuration = configuration.get("experiment")
        if not isinstance(experiment_configuration, dict):
            raise PolicyError("controlled-experiment mode requires experiment configuration")
        experiment = run_experiment(experiment_configuration, output_dir / "experiment")
        (output_dir / "experiment-result.json").write_bytes(_canonical_bytes(experiment))
        metric_trials = []
        for trial in experiment["trials"]:
            observation = dict(trial["result"])
            observation["label"] = trial["label"]
            metric_trials.append(observation)
        metrics = summarize_trials(metric_trials)
        hypotheses["H2"] = "insufficient_trials"
        hypotheses["H3"] = "insufficient_trials"
        limitations = [
            "pilot observations are recorded, but repeated trials, power analysis, and held-out evaluation are required for H2/H3 conclusions",
            experiment["network_control"],
        ]
        stages["evaluation"] = "complete"
        output_names.append("experiment-result.json")
    report = {
        "schema": "tracecontract.decision-report.v1",
        "run_id": manifest["run_id"],
        "hypotheses": hypotheses,
        "limitations": limitations,
    }
    if metrics is not None:
        report["metrics"] = metrics
    (output_dir / "report.json").write_bytes(_canonical_bytes(report))
    output_names.append("report.json")
    bundle = {
        "schema": "tracecontract.output-bundle.v1",
        "run_id": manifest["run_id"],
        "outputs": {
            name: hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
            for name in output_names
        },
    }
    (output_dir / "bundle-manifest.json").write_bytes(_canonical_bytes(bundle))
    return {
        "status": "certified",
        "run_id": manifest["run_id"],
        "project_id": graph.project_id,
        "stages": stages,
        "output_dir": str(output_dir.resolve()),
    }
