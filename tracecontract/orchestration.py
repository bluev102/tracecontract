from __future__ import annotations

import copy
import hashlib
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Iterable

from .core import PolicyError, TraceContract, _canonical_bytes
from .agent_runtime import AgentInvocation, AgentRunner


REVIEW_BATCH_SCHEMA = "tracecontract.review-batch.v1"
REQUIRED_REVIEW_ROLES = ("forward", "reverse", "adversarial")


def import_approval_batch(graph: TraceContract, batch: dict[str, Any]) -> list[str]:
    """Atomically import accountable, endpoint-bound approvals after review."""
    if batch.get("schema") != "tracecontract.approval-batch.v1":
        raise PolicyError(f"unsupported approval batch schema: {batch.get('schema')}")
    if batch.get("project_id") != graph.project_id:
        raise PolicyError("approval batch project_id does not match graph")
    approvals = batch.get("approvals")
    if not isinstance(approvals, list):
        raise PolicyError("approval batch requires approvals")
    active_ids = {edge["id"] for edge in graph.edges.values() if edge["status"] != "rejected"}
    approval_ids = {approval.get("edge_id") for approval in approvals}
    if approval_ids != active_ids or len(approval_ids) != len(approvals):
        raise PolicyError("approval batch must cover each non-rejected edge exactly once")
    staged = copy.deepcopy(graph)
    imported: list[str] = []
    for approval in sorted(approvals, key=lambda item: item["edge_id"]):
        edge = staged._edge(approval["edge_id"])
        if approval.get("source_hash") != edge["source_hash"] or approval.get("target_hash") != edge["target_hash"]:
            raise PolicyError(f"{edge['id']}: approval endpoint hash mismatch")
        subject = approval.get("subject")
        if not subject:
            raise PolicyError(f"{edge['id']}: approval subject is missing")
        if subject == edge["proposer"] or subject in {item["reviewer"] for item in edge["verdicts"]}:
            raise PolicyError(f"{edge['id']}: proposer or reviewer cannot provide accountable approval")
        staged.approve(edge["id"], approval.get("role"), subject)
        imported.append(edge["id"])
    graph.edges = staged.edges
    graph.audit_log = staged.audit_log
    return imported


def run_review_cycle(
    graph: TraceContract,
    invocations: Iterable[AgentInvocation],
    runner: AgentRunner,
) -> dict[str, Any]:
    """Run three isolated roles concurrently, then atomically import their batches."""
    invocation_list = list(invocations)
    roles = [invocation.role for invocation in invocation_list]
    if set(roles) != set(REQUIRED_REVIEW_ROLES) or len(roles) != len(REQUIRED_REVIEW_ROLES):
        raise PolicyError("review cycle requires one forward, reverse, and adversarial invocation")
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="tracecontract-review") as executor:
        futures = {invocation.role: executor.submit(runner.run, invocation) for invocation in invocation_list}
        results = {role: future.result() for role, future in futures.items()}
    failures = [
        f"{role}: {', '.join(result.protocol_deviations) or 'agent result rejected'}"
        for role, result in sorted(results.items()) if not result.accepted
    ]
    if failures:
        raise PolicyError("review agents failed: " + "; ".join(failures))

    staged = copy.deepcopy(graph)
    for role in sorted(results):
        output = results[role].output
        if output.get("reviewer_role") != role:
            raise PolicyError(f"{role}: output reviewer_role mismatch")
        import_review_batch(staged, output)
    gate_failures = review_gate_failures(staged)
    if gate_failures:
        raise PolicyError("independent review gate failed: " + "; ".join(gate_failures))
    graph.edges = staged.edges
    graph.review_sessions = staged.review_sessions
    graph.audit_log = staged.audit_log
    return {
        "schema": "tracecontract.review-cycle.v1",
        "candidate_snapshot_hash": candidate_snapshot_hash(graph),
        "agents": [
            {
                "role": role,
                "input_hash": results[role].input_hash,
                "command_hash": results[role].command_hash,
                "stdout_hash": results[role].stdout_hash,
                "stderr_hash": results[role].stderr_hash,
                "protocol_deviations": list(results[role].protocol_deviations),
            }
            for role in sorted(results)
        ],
        "review_sessions": copy.deepcopy(graph.review_sessions),
        "evidence_state_hash": hashlib.sha256(graph.state_bytes()).hexdigest(),
    }


def import_candidate_batch(graph: TraceContract, batch: dict[str, Any]) -> list[str]:
    """Atomically validate and import agent discoveries as review-required candidates."""
    if batch.get("schema") != "tracecontract.candidate-batch.v1":
        raise PolicyError(f"unsupported candidate batch schema: {batch.get('schema')}")
    if batch.get("project_id") != graph.project_id:
        raise PolicyError("candidate batch project_id does not match graph")
    candidates = batch.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise PolicyError("candidate batch requires candidates")
    proposer = batch.get("proposer") or candidates[0].get("proposer")
    if not proposer:
        raise PolicyError("candidate batch requires proposer")
    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        edge_id = candidate.get("edge_id")
        if not edge_id or edge_id in seen or edge_id in graph.edges:
            raise PolicyError(f"candidate edge identity collision: {edge_id}")
        seen.add(edge_id)
        source = graph._artifact(candidate.get("source"))
        target = graph._artifact(candidate.get("target"))
        if candidate.get("source_hash") != source["version_hash"] or candidate.get("target_hash") != target["version_hash"]:
            raise PolicyError(f"{edge_id}: candidate endpoint hash mismatch")
        evidence = candidate.get("cited_evidence")
        if not isinstance(evidence, list):
            raise PolicyError(f"{edge_id}: candidate cited_evidence must be a list")
        normalized_evidence = []
        for item in evidence:
            if not item.get("kind") or not item.get("provenance"):
                raise PolicyError(f"{edge_id}: candidate evidence requires kind and provenance")
            normalized_evidence.append({key: copy.deepcopy(value) for key, value in item.items() if key != "evidence_hash"})
        advisory_rank = candidate.get("advisory_rank")
        if advisory_rank is not None and (isinstance(advisory_rank, bool) or not isinstance(advisory_rank, (int, float))):
            raise PolicyError(f"{edge_id}: advisory_rank must be numeric or null")
        candidate_coverage = candidate.get("coverage", batch.get("coverage", {}))
        if candidate_coverage.get("state") not in {"complete", "partial", "unsupported", "excluded", "unknown"}:
            raise PolicyError(f"{edge_id}: unsupported candidate coverage state: {candidate_coverage.get('state')}")
        candidate_proposer = candidate.get("proposer", proposer)
        if candidate_proposer != proposer:
            raise PolicyError(f"{edge_id}: candidate proposer does not match batch proposer")
        validated.append({**candidate, "cited_evidence": normalized_evidence, "coverage": candidate_coverage})
    imported: list[str] = []
    for candidate in validated:
        graph.propose_edge(
            candidate["edge_id"], candidate["type"], candidate["source"], candidate["target"],
            candidate["required_role"], candidate["cited_evidence"], proposer=proposer,
            origin=candidate.get("origin", batch.get("origin", "agent-discovered")),
            retrieved_context=candidate.get("retrieved_context", ()), review_required=True,
            coverage=candidate["coverage"], advisory_rank=candidate.get("advisory_rank"),
        )
        imported.append(candidate["edge_id"])
    return imported


def candidate_snapshot_hash(graph: TraceContract) -> str:
    """Hash only immutable candidate identity, not verdicts added during review."""
    candidates = [
        {
            "id": edge["id"],
            "type": edge["type"],
            "source": edge["source"],
            "target": edge["target"],
            "source_hash": edge["source_hash"],
            "target_hash": edge["target_hash"],
            "origin": edge["origin"],
            "proposer": edge["proposer"],
        }
        for edge in sorted(graph.edges.values(), key=lambda item: item["id"])
    ]
    return hashlib.sha256(_canonical_bytes({"project_id": graph.project_id, "candidates": candidates})).hexdigest()


def import_review_batch(graph: TraceContract, batch: dict[str, Any]) -> list[str]:
    """Import one blind reviewer artifact against the frozen candidate snapshot."""
    if batch.get("schema") != REVIEW_BATCH_SCHEMA:
        raise PolicyError(f"unsupported review batch schema: {batch.get('schema')}")
    if batch.get("project_id") != graph.project_id:
        raise PolicyError("review batch project_id does not match graph")
    role = batch.get("reviewer_role")
    if role not in REQUIRED_REVIEW_ROLES:
        raise PolicyError(f"unsupported reviewer role: {role}")
    reviewer = batch.get("reviewer")
    isolation_id = batch.get("isolation_id")
    if not reviewer or not isolation_id:
        raise PolicyError("review batch requires reviewer and isolation_id")
    if batch.get("peer_verdicts_visible") is not False:
        raise PolicyError("reviewer isolation violated: peer verdicts were visible")
    if batch.get("candidate_snapshot_hash") != candidate_snapshot_hash(graph):
        raise PolicyError("review batch candidate snapshot hash mismatch")
    if any(session["isolation_id"] == isolation_id for session in graph.review_sessions):
        raise PolicyError(f"review isolation_id was reused: {isolation_id}")

    verdicts = batch.get("verdicts")
    if not isinstance(verdicts, list) or not verdicts:
        raise PolicyError("review batch requires verdicts")
    validated: list[tuple[dict[str, Any], dict[str, Any]]] = []
    seen_edges: set[str] = set()
    for verdict in verdicts:
        edge = graph._edge(verdict.get("edge_id"))
        if edge["id"] in seen_edges:
            raise PolicyError(f"{edge['id']}: duplicate verdict in review batch")
        seen_edges.add(edge["id"])
        if verdict.get("source_hash") != edge["source_hash"] or verdict.get("target_hash") != edge["target_hash"]:
            raise PolicyError(f"{edge['id']}: review endpoint hash mismatch")
        if verdict.get("verdict") not in {"supports", "contradicts", "uncertain"}:
            raise PolicyError(f"{edge['id']}: unsupported verdict")
        if not verdict.get("claim") or not verdict.get("evidence"):
            raise PolicyError(f"{edge['id']}: verdict requires claim and evidence")
        for evidence in verdict["evidence"]:
            if not evidence.get("kind") or not evidence.get("provenance"):
                raise PolicyError(f"{edge['id']}: evidence requires kind and provenance")
        validated.append((edge, verdict))
    imported: list[str] = []
    for edge, verdict in validated:
        graph.submit_verdict(
            edge["id"], role, reviewer, verdict.get("verdict"), verdict.get("claim", ""),
            verdict.get("evidence", ()), reproducer=verdict.get("reproducer"),
        )
        imported.append(edge["id"])
    graph.review_sessions.append({
        "reviewer_role": role,
        "reviewer": reviewer,
        "isolation_id": isolation_id,
        "candidate_snapshot_hash": batch["candidate_snapshot_hash"],
        "batch_hash": hashlib.sha256(_canonical_bytes(batch)).hexdigest(),
    })
    return imported


def review_gate_failures(
    graph: TraceContract,
    required_roles: Iterable[str] = REQUIRED_REVIEW_ROLES,
) -> list[str]:
    required = tuple(required_roles)
    failures: list[str] = []
    for edge in sorted(graph.edges.values(), key=lambda item: item["id"]):
        by_role = {verdict["reviewer_role"]: verdict for verdict in edge["verdicts"]}
        for role in required:
            if role not in by_role:
                failures.append(f"{edge['id']}: missing {role} review")
            elif by_role[role]["verdict"] == "uncertain":
                failures.append(f"{edge['id']}: {role} review is uncertain")
    return failures
