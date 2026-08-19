---
name: tracecontract-reverse-review
description: "Independently review changed business code back to design and requirements. Use to find speculative code, scope creep, stale links, and undecided legacy behavior."
---

# Reverse Trace Reviewer

Read [the shared contract](../tracecontract-run/references/contract.md), especially review isolation and batch shape. Accept only a frozen candidate batch, its `candidate_snapshot_hash`, a unique `isolation_id`, and pinned evidence; remain blind to linker reasoning and peer verdicts.

Start from each changed or claimed code symbol and trace inbound to DD, Architecture/BD, requirement, and accountable decision. Verify repository/commit, qualified symbol and normalized hash, then test whether cited design and requirements actually authorize the observed behavior. Inspect inbound graph relations and exact source; treat incomplete impact coverage as `uncertain`, never as absence of upstream intent.

Return one `tracecontract.review-batch.v1` with `reviewer_role: reverse` and `peer_verdicts_visible: false`. Put only cited evidence in each verdict's `evidence` field and keep retrieval audit separate. Include endpoint hashes, an evidence-backed `supports`, `contradicts`, or `uncertain` decision, and optional reproducer. Never approve, promote, or assign maturity.

Finish when every code-side claim is accounted for as supported, contradictory, or explicitly uncertain.
