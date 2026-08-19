from __future__ import annotations

import copy
import hashlib
import json
from collections import deque
from pathlib import Path
from typing import Any, Iterable


class PolicyError(ValueError):
    """Raised when a lifecycle transition violates TraceContract policy."""


class CertificationError(PolicyError):
    """Raised when certified output is requested from an uncertified graph."""


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


class TraceContract:
    """In-memory Evidence Core with deterministic JSON persistence."""

    POLICY_VERSION = "tracecontract-policy-v1"
    ALLOWED_EDGE_TYPES = {
        "derived_into",
        "constrained_by",
        "detailed_by",
        "implemented_by",
        "verified_by",
        "depends_on",
        "calls",
        "imports",
        "implements",
        "migrates_to",
        "supersedes",
        "contradicts",
        "approved_by",
    }

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.artifacts: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, Any]] = {}
        self.review_sessions: list[dict[str, Any]] = []
        self.audit_log: list[dict[str, Any]] = []

    def add_artifact(self, artifact_id: str, kind: str, content: dict[str, Any]) -> dict[str, Any]:
        if artifact_id in self.artifacts:
            existing = self.artifacts[artifact_id]
            if existing["kind"] == kind and existing["version_hash"] == _hash(content):
                self._audit("artifact_reingested", artifact_id=artifact_id, version_hash=existing["version_hash"])
                return copy.deepcopy(existing)
            raise PolicyError(f"artifact identity collision: {artifact_id}")
        artifact = {
            "id": artifact_id,
            "kind": kind,
            "content": copy.deepcopy(content),
            "version_hash": _hash(content),
        }
        self.artifacts[artifact_id] = artifact
        self._audit("artifact_added", artifact_id=artifact_id, version_hash=artifact["version_hash"])
        return copy.deepcopy(artifact)

    def propose_edge(
        self,
        edge_id: str,
        edge_type: str,
        source: str,
        target: str,
        required_role: str,
        evidence: Iterable[dict[str, Any]] = (),
        *,
        proposer: str = "fixture",
        origin: str = "declared",
        retrieved_context: Iterable[str] = (),
        review_required: bool = False,
        coverage: dict[str, Any] | None = None,
        advisory_rank: float | None = None,
    ) -> dict[str, Any]:
        if edge_id in self.edges:
            raise PolicyError(f"edge already exists: {edge_id}")
        if edge_type not in self.ALLOWED_EDGE_TYPES:
            raise PolicyError(f"unsupported edge type: {edge_type}")
        if source not in self.artifacts or target not in self.artifacts:
            raise PolicyError("both edge endpoints must exist")
        edge = {
            "id": edge_id,
            "type": edge_type,
            "source": source,
            "target": target,
            "source_hash": self.artifacts[source]["version_hash"],
            "target_hash": self.artifacts[target]["version_hash"],
            "required_role": required_role,
            "status": "candidate",
            "status_reason": "awaiting independent review and accountable approval",
            "maturity": "E0",
            "evidence": [],
            "origin": origin,
            "proposer": proposer,
            "retrieved_context": sorted(set(retrieved_context)),
            "review_required": review_required,
            "coverage": copy.deepcopy(coverage) if coverage is not None else {"state": "unknown", "details": []},
            "advisory_rank": advisory_rank,
            "verdicts": [],
            "reverification_history": [],
            "approved_by": None,
            "stale_reason": None,
            "policy_version": self.POLICY_VERSION,
        }
        self.edges[edge_id] = edge
        for item in evidence:
            self.attach_evidence(edge_id, item)
        self._audit("edge_proposed", edge_id=edge_id)
        return copy.deepcopy(edge)

    def reverify(
        self,
        edge_id: str,
        evidence: Iterable[dict[str, Any]],
        role: str,
        subject: str,
    ) -> dict[str, Any]:
        edge = self._edge(edge_id)
        if edge["status"] != "stale":
            raise PolicyError(f"only stale edges can be reverified, got {edge['status']}")
        edge["reverification_history"].append({
            "source_hash": edge["source_hash"],
            "target_hash": edge["target_hash"],
            "evidence": copy.deepcopy(edge["evidence"]),
            "approved_by": copy.deepcopy(edge["approved_by"]),
            "status": edge["status"],
        })
        edge["source_hash"] = self.artifacts[edge["source"]]["version_hash"]
        edge["target_hash"] = self.artifacts[edge["target"]]["version_hash"]
        edge["evidence"] = []
        edge["approved_by"] = None
        edge["status"] = "candidate"
        edge["status_reason"] = "reverification pending"
        self._refresh_maturity(edge)
        for item in evidence:
            self.attach_evidence(edge_id, item)
        self.approve(edge_id, role, subject)
        edge["status"] = "reverified"
        edge["status_reason"] = "reverified on current endpoint hashes"
        self._audit("edge_reverified", edge_id=edge_id, role=role, subject=subject)
        return copy.deepcopy(edge)

    def submit_verdict(
        self,
        edge_id: str,
        reviewer_role: str,
        reviewer: str,
        verdict: str,
        claim: str,
        evidence: Iterable[dict[str, Any]],
        *,
        reproducer: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record an independent structured review without certifying discovery."""
        edge = self._edge(edge_id)
        if edge["status"] not in {"candidate", "disputed"} and not (
            edge["status"] == "rejected" and edge["verdicts"]
        ):
            raise PolicyError(f"cannot review {edge['status']} edge")
        if reviewer == edge["proposer"]:
            raise PolicyError("candidate proposer cannot review its own proposal")
        if reviewer_role not in {"forward", "reverse", "adversarial"}:
            raise PolicyError(f"unsupported reviewer role: {reviewer_role}")
        if verdict not in {"supports", "contradicts", "uncertain"}:
            raise PolicyError(f"unsupported verdict: {verdict}")
        cited = list(evidence)
        if not cited:
            raise PolicyError("review verdict requires cited evidence")
        verdict_record = {
            "reviewer_role": reviewer_role,
            "reviewer": reviewer,
            "verdict": verdict,
            "claim": claim,
            "source_hash": edge["source_hash"],
            "target_hash": edge["target_hash"],
            "evidence_hashes": [],
            "reproducer": copy.deepcopy(reproducer),
        }
        for item in cited:
            evidence_hash = _hash(item)
            if not item.get("kind") or not item.get("provenance"):
                raise PolicyError("evidence requires kind and provenance")
            normalized = copy.deepcopy(item)
            normalized["evidence_hash"] = evidence_hash
            if not any(existing["evidence_hash"] == evidence_hash for existing in edge["evidence"]):
                edge["evidence"].append(normalized)
            self._refresh_maturity(edge)
            self._audit("evidence_attached", edge_id=edge_id, evidence_hash=evidence_hash)
            verdict_record["evidence_hashes"].append(evidence_hash)
        edge["verdicts"].append(verdict_record)
        confirmed_counterexample = any(
            item["verdict"] == "contradicts"
            and item.get("reproducer")
            and item["reproducer"].get("outcome") == "counterexample_confirmed"
            for item in edge["verdicts"]
        )
        has_contradiction = any(item["verdict"] == "contradicts" for item in edge["verdicts"])
        has_uncertainty = any(item["verdict"] == "uncertain" for item in edge["verdicts"])
        if confirmed_counterexample:
            edge["status"] = "rejected"
            edge["status_reason"] = "valid counterexample confirmed"
        elif has_contradiction:
            edge["status"] = "disputed"
            edge["status_reason"] = "unresolved contradictory review"
        else:
            edge["status"] = "candidate"
        if has_uncertainty and not has_contradiction:
            edge["status_reason"] = "review uncertainty requires accountable resolution"
        self._audit("verdict_submitted", edge_id=edge_id, reviewer_role=reviewer_role, reviewer=reviewer, verdict=verdict)
        return copy.deepcopy(edge)

    def attach_evidence(self, edge_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
        edge = self._edge(edge_id)
        if edge["status"] in {"stale", "disputed", "rejected"}:
            raise PolicyError(f"cannot attach evidence to {edge['status']} edge")
        if not evidence.get("kind") or not evidence.get("provenance"):
            raise PolicyError("evidence requires kind and provenance")
        normalized = copy.deepcopy(evidence)
        normalized["evidence_hash"] = _hash(evidence)
        if not any(item["evidence_hash"] == normalized["evidence_hash"] for item in edge["evidence"]):
            edge["evidence"].append(normalized)
        self._refresh_maturity(edge)
        self._audit("evidence_attached", edge_id=edge_id, evidence_hash=normalized["evidence_hash"])
        return copy.deepcopy(edge)

    def approve(self, edge_id: str, role: str, subject: str) -> dict[str, Any]:
        edge = self._edge(edge_id)
        if edge["status"] != "candidate":
            raise PolicyError(f"only candidate edges can be approved, got {edge['status']}")
        if role != edge["required_role"]:
            raise PolicyError(f"edge requires role {edge['required_role']}, got {role}")
        if edge["maturity"] in {"E0", "E1"}:
            raise PolicyError("edge requires at least two independent evidence kinds")
        if edge["review_required"]:
            verdicts = {verdict["reviewer_role"]: verdict for verdict in edge["verdicts"]}
            for reviewer_role in ("forward", "reverse", "adversarial"):
                if reviewer_role not in verdicts:
                    raise PolicyError(f"edge is missing {reviewer_role} review")
                if verdicts[reviewer_role]["verdict"] != "supports":
                    raise PolicyError(f"edge has unresolved {reviewer_role} review")
            reviewer_subjects = {verdict["reviewer"] for verdict in edge["verdicts"]}
            if len(reviewer_subjects) != 3:
                raise PolicyError("review lanes require distinct reviewer subjects")
            if subject in reviewer_subjects:
                raise PolicyError("reviewer cannot approve an edge it reviewed")
            if subject == edge["proposer"]:
                raise PolicyError("candidate proposer cannot approve its own edge")
        edge["status"] = "verified"
        edge["status_reason"] = "accountable approval accepted on current endpoints"
        edge["approved_by"] = {"role": role, "subject": subject}
        self._refresh_maturity(edge)
        self._audit("edge_approved", edge_id=edge_id, role=role, subject=subject)
        return copy.deepcopy(edge)

    def dispute(self, edge_id: str, reason: str) -> dict[str, Any]:
        edge = self._edge(edge_id)
        if edge["status"] == "rejected":
            raise PolicyError("rejected edge cannot be disputed")
        edge["status"] = "disputed"
        edge["status_reason"] = reason
        edge["dispute_reason"] = reason
        self._audit("edge_disputed", edge_id=edge_id, reason=reason)
        return copy.deepcopy(edge)

    def reject(self, edge_id: str, reason: str) -> dict[str, Any]:
        edge = self._edge(edge_id)
        edge["status"] = "rejected"
        edge["status_reason"] = reason
        edge["rejection_reason"] = reason
        self._audit("edge_rejected", edge_id=edge_id, reason=reason)
        return copy.deepcopy(edge)

    def change_artifact(self, artifact_id: str, content: dict[str, Any]) -> list[str]:
        artifact = self._artifact(artifact_id)
        old_hash = artifact["version_hash"]
        new_hash = _hash(content)
        if old_hash == new_hash:
            return []
        artifact["content"] = copy.deepcopy(content)
        artifact["version_hash"] = new_hash

        affected: list[str] = []
        visited_artifacts = {artifact_id}
        queue = deque([artifact_id])
        while queue:
            current = queue.popleft()
            for edge in sorted(self.edges.values(), key=lambda item: item["id"]):
                if edge["status"] == "rejected" or edge["source"] != current:
                    continue
                if edge["status"] in {"verified", "reverified"}:
                    edge["status"] = "stale"
                    edge["stale_reason"] = f"affected by {artifact_id} changing from {old_hash} to {new_hash}"
                    affected.append(edge["id"])
                if edge["target"] not in visited_artifacts:
                    visited_artifacts.add(edge["target"])
                    queue.append(edge["target"])
            # Only the changed artifact invalidates inbound edges. Descendants are
            # traversed forward; walking inbound at every hop would spill into
            # independent paths that merely converge on the same test artifact.
            if current == artifact_id:
                for edge in sorted(self.edges.values(), key=lambda item: item["id"]):
                    if edge["status"] != "rejected" and edge["target"] == current and edge["status"] in {"verified", "reverified"}:
                        edge["status"] = "stale"
                        edge["stale_reason"] = f"endpoint {artifact_id} changed from {old_hash} to {new_hash}"
                        if edge["id"] not in affected:
                            affected.append(edge["id"])
        self._audit("artifact_changed", artifact_id=artifact_id, old_hash=old_hash, new_hash=new_hash, affected=affected)
        return affected

    def certification_failures(self) -> list[str]:
        failures: list[str] = []
        for edge in sorted(self.edges.values(), key=lambda item: item["id"]):
            if edge["status"] == "rejected":
                continue
            prefix = edge["id"]
            if edge["status"] not in {"verified", "reverified"}:
                failures.append(f"{prefix}: status is {edge['status']}")
                continue
            if edge["approved_by"] is None or edge["approved_by"]["role"] != edge["required_role"]:
                failures.append(f"{prefix}: accountable approval is missing")
            if self.artifacts[edge["source"]]["version_hash"] != edge["source_hash"]:
                failures.append(f"{prefix}: source endpoint is stale")
            if self.artifacts[edge["target"]]["version_hash"] != edge["target_hash"]:
                failures.append(f"{prefix}: target endpoint is stale")
            if edge["type"] == "verified_by" and not self._has_passing_executable(edge):
                if any(item["kind"] == "test_result" and item.get("outcome") == "pass" for item in edge["evidence"]):
                    failures.append(f"{prefix}: executable evidence does not match pinned commit/environment")
                else:
                    failures.append(f"{prefix}: passing executable evidence is missing")
        if not self.edges:
            failures.append("graph has no trace edges")
        return failures

    def canonical_rtm_bytes(self) -> bytes:
        failures = self.certification_failures()
        if failures:
            raise CertificationError("; ".join(failures))
        active = [self._canonical_edge(edge) for edge in self.edges.values() if edge["status"] != "rejected"]
        output = {
            "schema": "tracecontract.rtm.v1",
            "project_id": self.project_id,
            "policy_version": self.POLICY_VERSION,
            "artifacts": [self._canonical_artifact(item) for item in sorted(self.artifacts.values(), key=lambda item: item["id"])],
            "edges": sorted(active, key=lambda item: item["id"]),
        }
        return _canonical_bytes(output)

    def context_contract_bytes(
        self,
        migration_unit: str,
        constraints: Iterable[str] = (),
        unknowns: Iterable[str] = (),
    ) -> bytes:
        rtm = json.loads(self.canonical_rtm_bytes())
        executable_tests = sorted({
            edge["target"]
            for edge in rtm["edges"]
            if edge["type"] == "verified_by" and edge["maturity"] == "E4"
        })
        contract = {
            "schema": "tracecontract.migration-context.v1",
            "migration_unit": migration_unit,
            "project_id": self.project_id,
            "artifacts": rtm["artifacts"],
            "verified_edges": rtm["edges"],
            "executable_tests": executable_tests,
            "constraints": sorted(set(constraints)),
            "unknowns": sorted(set(unknowns)),
            "release_gates": ["canonical_rtm_certified", "executable_evidence_passes"],
        }
        return _canonical_bytes(contract)

    def change_context_contract_bytes(
        self,
        changed_artifacts: Iterable[str],
        change_id: str,
    ) -> bytes:
        """Compile a bounded change projection from the current certified graph."""
        rtm = json.loads(self.canonical_rtm_bytes())
        changed = sorted(set(changed_artifacts))
        for artifact_id in changed:
            self._artifact(artifact_id)
        reached = set(changed)
        queue = deque(changed)
        while queue:
            current = queue.popleft()
            for edge in rtm["edges"]:
                if edge["source"] == current and edge["target"] not in reached:
                    reached.add(edge["target"])
                    queue.append(edge["target"])
        by_id = {artifact["id"]: artifact for artifact in rtm["artifacts"]}
        design_kinds = {"architecture_claim", "basic_design_claim", "design_claim", "detail_design_claim"}
        test_kinds = {"test_specification", "test_case", "test_result"}
        contract = {
            "schema": "tracecontract.change-context.v1",
            "project_id": self.project_id,
            "change_id": change_id,
            "changed_artifacts": changed,
            "impacted_design_claims": sorted(
                artifact_id for artifact_id in reached if by_id[artifact_id]["kind"] in design_kinds
            ),
            "impacted_code_symbols": sorted(
                artifact_id for artifact_id in reached if by_id[artifact_id]["kind"] == "code_symbol"
            ),
            "required_test_changes": sorted(
                artifact_id for artifact_id in reached if by_id[artifact_id]["kind"] in test_kinds
            ),
            "regression_surface": sorted(
                artifact_id for artifact_id in reached if by_id[artifact_id]["kind"] in test_kinds
            ),
            "prior_behavior_envelope": sorted(reached - set(changed)),
            "release_gates": [
                "change_trace_certified",
                "prior_verified_behavior_preserved",
                "required_tests_pass_at_pinned_commit",
            ],
        }
        return _canonical_bytes(contract)

    def state_bytes(self) -> bytes:
        return _canonical_bytes({
            "project_id": self.project_id,
            "artifacts": sorted(self.artifacts.values(), key=lambda item: item["id"]),
            "edges": sorted(self.edges.values(), key=lambda item: item["id"]),
            "review_sessions": sorted(self.review_sessions, key=lambda item: (item["reviewer_role"], item["reviewer"])),
            "audit_log": self.audit_log,
        })

    @classmethod
    def from_fixture(cls, fixture: dict[str, Any]) -> "TraceContract":
        graph = cls(fixture["project_id"])
        for artifact in fixture["artifacts"]:
            graph.add_artifact(artifact["id"], artifact["kind"], artifact["content"])
        for edge in fixture["edges"]:
            graph.propose_edge(
                edge["id"], edge["type"], edge["source"], edge["target"],
                edge["required_role"], edge.get("evidence", ()),
            )
        return graph

    @staticmethod
    def load_fixture(path: str | Path) -> dict[str, Any]:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def _refresh_maturity(self, edge: dict[str, Any]) -> None:
        evidence_kinds = {item["kind"] for item in edge["evidence"]}
        edge["maturity"] = "E2" if len(evidence_kinds) >= 2 else ("E1" if evidence_kinds else "E0")
        if edge["approved_by"]:
            edge["maturity"] = "E4" if edge["type"] == "verified_by" and self._has_passing_executable(edge) else "E3"

    def _has_passing_executable(self, edge: dict[str, Any]) -> bool:
        endpoint_contents = [
            self.artifacts[edge[endpoint]]["content"]
            for endpoint in ("source", "target")
        ]
        commits = {content["commit"] for content in endpoint_contents if content.get("commit")}
        environments = {content["environment"] for content in endpoint_contents if content.get("environment")}
        for item in edge["evidence"]:
            if item["kind"] != "test_result" or item.get("outcome") != "pass":
                continue
            if commits and item.get("commit") not in commits:
                continue
            if environments and item.get("environment") not in environments:
                continue
            return True
        return False

    @staticmethod
    def _canonical_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
        return {key: copy.deepcopy(artifact[key]) for key in ("id", "kind", "version_hash", "content")}

    @staticmethod
    def _canonical_edge(edge: dict[str, Any]) -> dict[str, Any]:
        keys = ("id", "type", "source", "target", "source_hash", "target_hash", "status", "status_reason", "maturity", "required_role", "approved_by", "policy_version", "origin", "proposer", "review_required", "coverage", "verdicts", "reverification_history", "evidence")
        result = {key: copy.deepcopy(edge[key]) for key in keys}
        result["evidence"] = sorted(result["evidence"], key=lambda item: item["evidence_hash"])
        return result

    def _artifact(self, artifact_id: str) -> dict[str, Any]:
        try:
            return self.artifacts[artifact_id]
        except KeyError as exc:
            raise PolicyError(f"unknown artifact: {artifact_id}") from exc

    def _edge(self, edge_id: str) -> dict[str, Any]:
        try:
            return self.edges[edge_id]
        except KeyError as exc:
            raise PolicyError(f"unknown edge: {edge_id}") from exc

    def _audit(self, event: str, **details: Any) -> None:
        self.audit_log.append({"sequence": len(self.audit_log) + 1, "event": event, **details})
