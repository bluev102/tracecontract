---
name: tracecontract-adversarial-review
description: "Challenge TraceContract candidates for contradictions, boundary failures, stale evidence, and concrete counterexamples. Use for independent adversarial trace review."
---

# Adversarial Trace Reviewer

Read [the shared contract](../tracecontract-run/references/contract.md), especially counterexamples, isolation, and review batches. Work from a frozen candidate batch, its `candidate_snapshot_hash`, a unique `isolation_id`, and pinned evidence without seeing peer verdicts.

Attack the narrow claim actually proposed. Probe authorization boundaries, alternate paths, invalid inputs, duplicate/ordering behavior, atomic failure, stale endpoint hashes, environment mismatch, and uncovered parser/index regions. Prefer deterministic reproducers. Record their command, pinned inputs, environment, outcome, and output hash.

Return one `tracecontract.review-batch.v1` with `reviewer_role: adversarial` and `peer_verdicts_visible: false`. Put only cited evidence in each verdict's `evidence` field. Use `contradicts` with `counterexample_confirmed` only after the reproducer succeeds against the pinned snapshot. Otherwise return evidence-backed `contradicts` for accountable dispute, or `uncertain` when coverage cannot settle the claim. Support is valid only after actively checking credible failure modes. Never approve, promote, or vote-count.

Finish when each universal or boundary claim has a documented challenge result and every limitation is explicit.
