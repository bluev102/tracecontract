# TraceContract Executable MVP Spec

## Problem Statement

Delivery teams working on legacy systems have requirements, design claims, source symbols, and tests, but the links between them are usually scattered, unversioned, and hard to trust. The existing TraceContract materials explain and simulate the desired lifecycle, but they do not provide an executable system that proves role-based approval, freshness invalidation, deterministic certification, and context-contract compilation.

## Solution

Build a dependency-free Python MVP of the TraceContract Evidence Core. It ingests versioned artifacts, records typed candidate trace edges with evidence and provenance, enforces accountable-role approval, propagates staleness across the affected subgraph, certifies the graph with deterministic gates, and compiles byte-stable RTM and Migration Context Contract JSON. A CLI runs the complete UC19 Food Diary slice so the behavior can be demonstrated and tested without external services.

## User Stories

1. As a BA, I want requirement claims stored with stable identity and content hashes, so that approvals refer to an exact version.
2. As an Architect, I want architecture and design claims represented as versioned artifacts, so that downstream traces can be invalidated when design changes.
3. As a Tech Lead, I want code symbols bound to a repository commit and normalized content hash, so that line-number movement is not treated as semantic identity.
4. As a QA, I want test cases and results represented as artifacts and evidence, so that verified behavior is executable rather than prose-only.
5. As a discovery agent, I want to propose typed trace edges, so that high-recall findings remain candidates rather than certified facts.
6. As a reviewer, I want each edge to retain independent evidence kinds and provenance, so that I can understand why a link was proposed.
7. As an accountable approver, I want corroborated edges routed to the role required by policy, so that responsibility is explicit.
8. As a governance owner, I want approval by the wrong role rejected, so that AI or unrelated roles cannot self-certify a trace.
9. As a reviewer, I want under-corroborated edges blocked from approval, so that a single weak signal is not promoted to verified.
10. As an adversarial reviewer, I want to dispute a link, so that a counterexample stops certification until resolved.
11. As an artifact owner, I want a changed artifact to invalidate only its affected subgraph, so that unrelated evidence remains reusable.
12. As a reviewer, I want stale edges to retain their audit history, so that staleness is not confused with rejection.
13. As a release owner, I want certification to reject candidate, stale, disputed, wrongly approved, or hash-mismatched edges, so that the RTM cannot hide unresolved risk.
14. As a release owner, I want test-related links to require passing executable evidence, so that the behavior envelope has a runnable basis.
15. As an auditor, I want a canonical RTM ordered by stable keys, so that repeated compilation from identical inputs is byte-identical.
16. As a coding agent, I want a task-specific Migration Context Contract, so that I receive verified artifacts, edges, constraints, tests, and unknowns instead of a knowledge dump.
17. As a coding agent, I want context compilation blocked until certification succeeds, so that uncertified candidates cannot silently become instructions.
18. As a prototype evaluator, I want a bundled UC19 Food Diary fixture, so that the complete lifecycle can be demonstrated without private data.
19. As a developer, I want a CLI that runs the complete happy path, so that I can produce inspectable RTM and context outputs with one command.
20. As a developer, I want behavior-level automated tests, so that role policy, freshness, certification, and determinism remain stable as the MVP evolves.
21. As a security reviewer, I want the MVP to run locally without network access or third-party dependencies, so that source-derived evidence does not leave the local data plane.
22. As a benchmark author, I want generated outputs separated from fixture inputs, so that evidence inputs are not mutated to make a run pass.

## Implementation Decisions

- Implement an in-process Evidence Core in Python using only the standard library.
- Keep the graph as the source model; RTM and context contracts are deterministic projections.
- Calculate artifact versions from canonical JSON content with SHA-256 rather than trusting caller-supplied timestamps or row IDs.
- Store endpoint hashes on every trace edge and compare them with current artifact versions during certification.
- Model lifecycle status (`candidate`, `verified`, `stale`, `disputed`, `rejected`) independently from evidence maturity (`E1` through `E4`).
- Derive E2 from at least two distinct evidence kinds, E3 from valid accountable approval, and E4 from valid approval plus passing executable evidence.
- Resolve approval authority from the edge policy; the actor cannot override the required role.
- Propagate artifact changes forward through active typed edges and mark only previously verified affected edges stale.
- Exclude rejected edges from certification and certified projections while retaining them in state/audit data.
- Require all active edges to be verified and current; require `verified_by` edges to carry passing executable evidence.
- Canonicalize output with stable key ordering, deterministic list ordering, UTF-8, and no volatile timestamps.
- Compile a Migration Context Contract only after successful certification.
- Provide state import/export as JSON and a one-command UC19 demo through a public CLI.
- Keep candidate discovery and human interaction out of the MVP core; fixtures or callers supply candidate edges and accountable approvals.

## Testing Decisions

- Good tests assert externally observable policy outcomes and serialized products, not internal helper calls or storage layout.
- The primary seam is the CLI: a subprocess runs the bundled UC19 workflow and must emit a certified RTM and Migration Context Contract.
- Core API tests cover role rejection, evidence thresholds, dispute blocking, affected-subgraph freshness, unrelated-artifact stability, and certification gates.
- Determinism is tested by compiling the same certified graph twice and comparing raw UTF-8 bytes.
- Prior art comes from the pure state machines embedded in the existing interactive prototypes and the freshness mutation suite in the validation plan.
- Tests use only temporary directories and bundled fixtures; they do not require network access or external services.

## Out of Scope

- LLM-based candidate discovery, semantic retrieval, Codebase Memory MCP integration, DOCX/Jira/XLSX adapters, and production persistence.
- Fully autonomous approval, waivers, SSO/RBAC integration, multi-tenant ACL enforcement, or a production web UI.
- General semantic impact analysis across arbitrary languages, dynamic dispatch, runtime tracing, and OCR.
- The controlled A/B migration benchmark and any claim of FSOFT-wide effectiveness.
- Proving zero regression or automatically identifying/deleting dead code.

## Further Notes

- The bundled UC19 slice is demonstration data, not a research result.
- The issue tracker and triage-label vocabulary were not configured in this workspace, so this spec is stored as a local project artifact rather than published with `ready-for-agent`.
- The implementation deliberately exposes unknowns and certification failures instead of converting model confidence into correctness.
