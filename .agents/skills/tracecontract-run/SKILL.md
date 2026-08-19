---
name: tracecontract-run
description: "Run the full pinned TraceContract workflow with isolated linker and reviewer agents. Invoke explicitly for an end-to-end governed run."
---

# TraceContract run

Orchestrate; do not collapse independent roles into one context.

Read [the shared contract](references/contract.md) before dispatching work. Treat its packet formats and invariants as completion gates.

1. Pin the run manifest, policy, inputs, adapter configuration, model/tool inventory, and endpoint hashes. Reject mutable or hash-mismatched inputs.
2. In the parent, establish current codebase-memory project/generation, query the relevant seams, and check coverage for every candidate path. Read source for all reported stale, partial, skipped, excluded, or unknown ranges. Record this evidence in every delegated packet.
3. Spawn a fresh Candidate Linker agent with `$tracecontract-link`. Give it only pinned inputs, retrieved context, graph/coverage evidence, and output location. Wait for a complete `tracecontract.candidate-batch.v1`, then propose its candidates into Evidence Core.
4. Freeze the graph with `candidate_snapshot_hash`. Spawn three fresh agents concurrently with `$tracecontract-forward-review`, `$tracecontract-reverse-review`, and `$tracecontract-adversarial-review`. Give each the same frozen candidate batch, snapshot hash, and pinned evidence, but no other reviewer's context or verdict. Assign a unique `isolation_id` to each agent.
5. Wait for all three agents. Require one `tracecontract.review-batch.v1` per role with `peer_verdicts_visible` set to `false`. Import each complete batch atomically through `import_review_batch`; the importer validates project, role, isolation, frozen snapshot, endpoint hashes, evidence, and duplicate verdicts before it calls `TraceContract.submit_verdict`.
6. Run `review_gate_failures`. Route missing, disputed, or uncertain claims and required approvals to the policy-defined accountable human role. An agent never substitutes for that approval. Import the returned `tracecontract.approval-batch.v1` atomically through `import_approval_batch`.
7. Invoke `$tracecontract-certify` only after all review batches and the approval batch import, review gates pass, and accountable approval is recorded. Certification must compile from Evidence Core state, not agent prose.

Finish only when every dispatched agent has returned, every review batch is imported atomically or rejected with a machine-readable reason, and certification either emits a hash-addressed canonical bundle or fails closed with diagnostics.
