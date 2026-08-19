---
name: tracecontract-certify
description: "Apply deterministic TraceContract gates and compile canonical RTM and context projections. Use only after independent verdict import and accountable approvals."
---

# TraceContract Certifier

Read [the shared contract](../tracecontract-run/references/contract.md), especially certification handoff. Certification consumes Evidence Core state; it does not reinterpret reviewer prose.

1. Verify manifest/input/policy hashes, schema versions, endpoint hashes, imported review-batch identities, unique isolation sessions, frozen candidate snapshot, and current coverage records.
2. Fail closed on candidate, stale, disputed, wrong-role or missing approval, invalid/expired waiver, hash mismatch, mandatory-path gap, or executable evidence bound to another commit/environment. Unsupported coverage remains an explicit uncertainty and blocks any gate that requires complete impact or path coverage.
3. Require `review_gate_failures` to be empty, then apply lifecycle and E0-E4 policy deterministically. Ignore model confidence and majority opinion. Honor one deterministically confirmed counterexample against a universal claim.
4. Compile canonical UTF-8 JSON with stable key/list ordering and no volatile fields. Generate RTM and requested Migration/Change Context Contracts only from current certified evidence.
5. Emit content hashes and stable failure codes. Identical pinned inputs and approved evidence must produce byte-identical canonical projections.

Finish with a hash-addressed certified bundle or machine-readable failures; never downgrade a failed gate into prose-only caution.
