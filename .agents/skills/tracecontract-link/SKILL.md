---
name: tracecontract-link
description: "Propose pinned, provenance-bearing trace candidates from requirements, design, code, tests, Git, static graph, or runtime observations. Use for TraceContract candidate discovery, not approval or certification."
---

# Candidate Linker

Read [the shared contract](../tracecontract-run/references/contract.md), especially the evidence protocol and candidate packet.

Work for recall while preserving trust boundaries:

1. Verify the input hashes and code-intelligence coverage record. Use graph discovery and call traces, then inspect exact source for material claims and every missed/stale coverage range.
2. Combine explicit IDs, semantic retrieval, Git, static relationships, tests, and runtime observations. Record all material retrieved context separately from the exact evidence cited by each proposed edge.
3. Bind each endpoint to its artifact ID and current content or normalized-symbol hash. Include provenance and coverage for every citation.
4. Emit only typed `candidate` edges in a canonical `tracecontract.candidate-batch.v1`. Include each edge's `required_role`; advisory ranking is allowed, while promotion, maturity assignment, reviewer verdicts, and approval remain outside this role.

Finish when every candidate is reproducible from pinned citations and every unsupported region is represented as uncertainty rather than an inferred negative.
