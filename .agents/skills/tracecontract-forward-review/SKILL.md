---
name: tracecontract-forward-review
description: "Independently review TraceContract candidates from requirement through design, code, and tests. Use to expose missing, partial, stale, or untested implementation without certifying it."
---

# Forward Trace Reviewer

Read [the shared contract](../tracecontract-run/references/contract.md), especially review isolation and batch shape. Accept only a frozen candidate batch, its `candidate_snapshot_hash`, a unique `isolation_id`, and pinned source evidence; do not request linker reasoning or other reviewer verdicts.

For each candidate, walk requirement or acceptance claim toward Architecture/BD, DD, code symbol, and executable test as applicable. Check semantic scope, endpoint hashes, source spans, behavior boundaries, and commit/environment binding. Use graph paths as retrieval context and exact pinned artifacts as cited evidence. Check coverage and widen the boundary when it cannot support a complete path claim.

Return one `tracecontract.review-batch.v1` with `reviewer_role: forward` and `peer_verdicts_visible: false`. Put only cited evidence in each verdict's `evidence` field; keep retrieval audit separate. Each verdict carries endpoint hashes, a precise claim, `supports`, `contradicts`, or `uncertain`, and an optional reproducible counterexample. Never approve, promote, or assign maturity.

Finish when every assigned edge has one schema-valid verdict in the batch or an explicit machine-readable rejection reason.
