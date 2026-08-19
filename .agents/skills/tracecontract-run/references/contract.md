# TraceContract agent contract

This is the single source of truth for packets and trust invariants shared by all TraceContract skills.

## Trust model

- **Retrieved context** is material exposed to an agent for discovery. **Cited evidence** is the exact, pinned subset used to support or contradict a claim. Only cited evidence affects a verdict or maturity.
- Every discovered relation begins as `candidate`. Model confidence may rank review work; it never changes lifecycle, maturity, approval, or certification.
- Lifecycle (`candidate`, `verified`, `rejected`, `stale`, `reverified`, `disputed`), evidence maturity (`E0`-`E4`), coverage, and conflict are independent fields.
- Missing, partial, skipped, excluded, stale, or unknown coverage is uncertainty. Widen the review boundary and emit `impact_boundary_uncertain`; absence from a graph is not evidence that code is dead, orphaned, or unaffected.
- Every claim binds explicit source and target artifact IDs plus their current hashes. Every evidence item carries `kind`, immutable `provenance`, content hash, and source span or observation identity when applicable.
- Evidence maturity comes from deterministic policy: E2 needs independent evidence kinds, E3 needs accountable approval on current endpoints, and E4 needs passing executable evidence bound to the pinned commit and environment.
- One confirmed counterexample defeats a universal claim. Other contradictions remain disputed until accountable resolution; correctness is not a majority vote.

## Evidence protocol

For code facts, record repository identity, commit, adapter/provider name and version, adapter configuration hash, qualified symbol, normalized symbol hash, commit-bound source span, coverage state, and raw result hash. Use the provider's supported MCP/export boundary, never private storage.

With codebase-memory, record project, generation/index time, query and pagination state, qualified symbols and paths, relevant inbound/outbound traces, and `check_index_coverage` results. Read exact source for any reported missed range or freshness problem. A clean best-effort coverage result is not proof of completeness.

## Candidate batch

Emit canonical JSON containing:

```json
{
  "schema": "tracecontract.candidate-batch.v1",
  "project_id": "...",
  "proposer": "candidate-linker-id",
  "origin": "agent",
  "coverage": {"state": "complete|partial|unsupported|excluded|unknown", "details": []},
  "candidates": [{
    "edge_id": "...", "type": "implemented_by", "source": "...", "target": "...",
    "source_hash": "...", "target_hash": "...", "required_role": "...",
    "retrieved_context": [{"ref": "...", "hash": "...", "provenance": {}}],
    "cited_evidence": [{"kind": "...", "provenance": {}, "evidence_hash": "..."}],
    "advisory_rank": null
  }]
}
```

Keep retrieved context in `retrieved_context` and outside `cited_evidence`; it cannot affect a verdict or maturity until cited. The importer always sets `review_required: true`, verifies endpoint hashes against Evidence Core rather than trusting agent-authored values, and ignores model ranking for lifecycle decisions. After importing the batch, compute `candidate_snapshot_hash` from the graph; reviewers bind to that frozen value.

## Review batch

Each isolated reviewer emits one batch. The runtime accepts this exact envelope:

```json
{
  "schema": "tracecontract.review-batch.v1",
  "project_id": "...",
  "reviewer_role": "forward|reverse|adversarial",
  "reviewer": "...",
  "isolation_id": "unique-per-review-session",
  "candidate_snapshot_hash": "...",
  "peer_verdicts_visible": false,
  "verdicts": [{
    "edge_id": "...", "source_hash": "...", "target_hash": "...",
    "verdict": "supports|contradicts|uncertain", "claim": "...",
    "evidence": [{"kind": "...", "provenance": {}}],
    "reproducer": null
  }]
}
```

The `evidence` array is cited evidence; retrieved-only material stays in the review audit sidecar and never enters this array. A verdict without cited evidence is invalid. A reproducer records pinned command/environment/input hashes and observed outcome; `counterexample_confirmed` is accepted only after deterministic execution. `import_review_batch` imports the batch atomically and rejects reused isolation IDs, visible peer verdicts, stale snapshots, endpoint mismatches, duplicate edge verdicts, or malformed evidence.

## Approval batch

Approval is a separate accountable artifact, never a linker or reviewer output. Import this exact envelope after the review gate succeeds:

```json
{
  "schema": "tracecontract.approval-batch.v1",
  "project_id": "...",
  "approvals": [{
    "edge_id": "...", "source_hash": "...", "target_hash": "...",
    "role": "policy-required-role", "subject": "accountable-human-id"
  }]
}
```

The batch must cover every non-rejected edge exactly once. `import_approval_batch` rejects endpoint mismatches, missing subjects, wrong roles, duplicate or incomplete coverage, and any subject that proposed or reviewed the edge. Import is atomic.

## Certification handoff

The handoff contains the immutable run manifest, current Evidence Core state hash, imported verdict hashes, imported accountable approvals/waivers, coverage record, and requested projection names. Certification output contains canonical bytes and their SHA-256 hashes, or stable machine-readable failures. Generated prose, timestamps, database row IDs, confidence scores, and retrieval-only context stay outside canonical projections.
