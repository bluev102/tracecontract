# TraceContract Validated MVP

Status: ready-for-agent

## Problem Statement

Các delivery team thay đổi hoặc migration legacy system phải ghép nối requirement, Architecture, Basic Design (BD), Detail Design (DD), source code, Git history và test từ nhiều nguồn không đồng nhất. Trace thường không gắn với phiên bản artifact, provenance, accountable approval hoặc freshness, nên coding agent phải khám phá lại context cho từng task và reviewer vẫn phải tự xác minh phần lớn kết quả.

Repository hiện có một Evidence Core Python in-memory và UC19 fixture nhỏ chứng minh được một phần lifecycle: versioned artifact, typed edge, evidence maturity, role-based approval, freshness propagation, deterministic RTM và Migration Context Contract. Tuy nhiên, nó chưa ingest artifact thực, chưa index/link/review bằng workflow độc lập, chưa hỗ trợ Change Context Contract, chưa chạy migration fixture, và chưa thực thi controlled validation plan. Vì vậy, các tuyên bố về trace quality, migration correctness, engineering efficiency và governance vẫn là giả thuyết chưa được kiểm chứng.

Nhóm cần một MVP end-to-end có thể tái lập, không biến AI confidence thành correctness, phân biệt rõ candidate với certified evidence, và đánh giá được TraceContract trên phạm vi iTrust2 UC19 mà không suy rộng kết quả sang mọi ngôn ngữ, hệ thống hay FSOFT.

## Solution

Mở rộng Evidence Core hiện có thành TraceContract Validated MVP: một workflow local-first ingest các snapshot SDLC và observed code facts, đề xuất typed candidate trace, thu thập các verdict forward/reverse/adversarial độc lập, route accountable approval, tính freshness theo typed affected subgraph, và chỉ compile canonical RTM cùng Migration/Change Context Contract khi deterministic policy gates đều pass.

MVP dùng iTrustFull cho trace-recovery benchmark và iTrust2 v7 UC19 Food Diary sang v8 Spring Boot cho migration fixture. Sau migration, workflow thêm date-range nutrition summary trong khi bảo toàn verified UC19 behavior envelope. Một experiment runner chạy baseline và treatment trong process cô lập với cùng model, tools và budget; hidden acceptance/regression tests là primary endpoint. Mọi input, phiên bản, policy, prompt/config, output, chi phí và protocol deviation được ghi lại trong run manifest để kết quả có thể audit và tái lập.

## User Stories

1. As a Delivery Manager, I want a repeatable end-to-end TraceContract run, so that I can evaluate the workflow rather than a collection of disconnected demos.
2. As a benchmark author, I want every repository, document, dataset, parser, adapter, policy and experiment configuration pinned, so that a result refers to an exact input snapshot.
3. As a benchmark author, I want the iTrustFull counting method and metadata discrepancy recorded, so that evaluation does not silently select favorable corpus counts.
4. As a benchmark author, I want gold manifests and hidden tests frozen before agent runs, so that output cannot influence the acceptance target.
5. As a benchmark author, I want benchmark-authored Architecture/BD/DD and symbol-level gold clearly identified, so that they are not misrepresented as upstream truth.
6. As a document owner, I want requirements, Architecture, BD, DD and test assets normalized into atomic versioned artifacts, so that trace endpoints have stable identities.
7. As a Tech Lead, I want code artifacts identified by repository, commit, adapter version, qualified symbol and normalized symbol hash, so that line-number movement is not mistaken for semantic identity.
8. As an auditor, I want source spans and LOC retained as commit-bound evidence, so that every code citation can be checked against its original snapshot.
9. As an integrator, I want code intelligence consumed through a version-pinned adapter contract, so that TraceContract does not depend on a provider's private storage layout.
10. As an integrator, I want index coverage and raw result hashes recorded, so that missing parser support cannot be hidden behind a successful tool call.
11. As a reviewer, I want unsupported, partially parsed, excluded and unknown regions represented explicitly, so that absence of evidence is not labeled as dead or orphaned code.
12. As a Candidate Linker, I want to combine explicit IDs, semantic retrieval, Git, static graph, test and runtime signals, so that candidate discovery can optimize recall.
13. As a governance owner, I want every agent-discovered link to begin as a candidate, so that discovery cannot certify its own output.
14. As a reviewer, I want each edge to retain origin, evidence references, endpoint hashes, proposer, verdicts, approver, policy version and status reason, so that the trace has a complete audit trail.
15. As a reviewer, I want retrieved context distinguished from evidence actually cited for a link, so that irrelevant context does not inflate evidence maturity.
16. As a reviewer, I want E0 through E4 evidence maturity represented separately from lifecycle and parsing states, so that trust, freshness and coverage are not collapsed into one score.
17. As a Forward Trace Reviewer, I want to inspect requirement-to-design-to-code-to-test paths, so that missing or partial implementation and missing tests are exposed.
18. As a Reverse Trace Reviewer, I want to trace changed business code back to design and requirement, so that speculative code, scope creep and undecided legacy behavior are exposed.
19. As an Adversarial Trace Reviewer, I want to search for contradictions, boundary cases, stale evidence and concrete counterexamples, so that plausible but false universal claims are challenged.
20. As a governance owner, I want reviewers isolated from candidate creation and from one another's verdicts until their review is submitted, so that review independence is preserved.
21. As an accountable BA or Product Owner, I want to approve business requirements only on current artifact versions, so that responsibility for business truth is explicit.
22. As an accountable Architect, I want to approve Architecture/BD traces, so that design authority is enforced by policy.
23. As an accountable Tech Lead or Developer, I want to approve DD/code traces, so that implementation mapping is confirmed by the responsible role.
24. As an accountable QA or BA, I want to approve requirement-test links and test adequacy, so that executable evidence has an accountable owner.
25. As a reviewer, I want a valid counterexample to defeat a universal claim regardless of majority opinion, so that correctness is evidence-driven.
26. As a reviewer, I want unresolved conflicts kept as disputed and routed to the accountable role, so that uncertainty is not averaged away.
27. As a policy owner, I want waivers to be explicit, scoped, expiring and auditable, so that exceptions never silently become verified evidence.
28. As an artifact owner, I want a changed artifact to stale the typed affected subgraph, so that evidence tied to old endpoint hashes cannot remain current.
29. As an artifact owner, I want unrelated artifacts and trace paths to remain current, so that a local change does not force full-system re-review.
30. As a reviewer, I want an uncertain impact boundary to widen review scope and emit `impact_boundary_uncertain`, so that incomplete graph coverage is not presented as complete impact analysis.
31. As a reviewer, I want move/rename-only changes distinguished from behavior changes when evidence permits, so that harmless churn does not cause unnecessary invalidation.
32. As a release owner, I want deterministic certification to reject candidate, stale, disputed, wrongly approved, hash-mismatched or policy-invalid edges, so that unresolved risk cannot enter the certified RTM.
33. As a release owner, I want executable claims bound to passing test evidence at the correct commit and environment, so that E4 has a reproducible meaning.
34. As an auditor, I want canonical RTM output to be byte-identical for identical pinned inputs, so that governance output is repeatable.
35. As a coding agent, I want a task-specific Migration Context Contract containing verified behavior, design, symbols, tests, dependencies, constraints and unknowns, so that I do not rediscover the entire codebase.
36. As a coding agent, I want a Change Context Contract containing the changed requirement, impacted graph, regression surface and release gates, so that a subsequent feature preserves the verified behavior envelope.
37. As a coding agent, I want context compilation blocked when certification fails, so that candidate or stale information cannot silently become implementation instruction.
38. As a security owner, I want artifact ACL and project classification enforced before retrieval, so that an agent never receives unauthorized source-derived context.
39. As a security owner, I want cloud egress allowlisted and minimized with provider, model, prompt/config and context hashes audited, so that model execution follows project policy.
40. As a security owner, I want local providers usable when source-derived text cannot leave the environment, so that the Evidence Core remains local-first without claiming all inference is offline.
41. As an evaluator, I want baseline and treatment runs to use fresh isolated agent processes, so that history, cache and cross-run memory do not contaminate the comparison.
42. As an evaluator, I want baseline and treatment to share the same raw artifacts, model, tool access and fixed budget, so that verified TraceContract is the intended treatment difference.
43. As an evaluator, I want treatment labels blinded and A/B order randomized or counterbalanced, so that evaluator and order effects are reduced.
44. As an evaluator, I want the coding agent unable to read hidden tests or judge its own work, so that the primary endpoint remains independent.
45. As an evaluator, I want every prompt, tool call, token count, elapsed time and produced artifact recorded subject to data policy, so that cost and protocol compliance can be audited.
46. As an evaluator, I want hidden acceptance and regression pass rate within fixed budget to be the primary endpoint, so that correctness is not delegated to an LLM preference score.
47. As an evaluator, I want trace Precision/Recall/F1 reported by hop and type, so that a single aggregate does not hide weak portions of the graph.
48. As an Engineering Manager, I want cold-start and steady-state costs reported as raw components, so that human verification and reviewer-agent cost are visible.
49. As an Engineering Manager, I want the subsequent nutrition-summary change to reuse certified evidence, so that the steady-state value proposition can be measured.
50. As an evaluator, I want repeated trials, per-task results, effect sizes and confidence intervals reported, so that a best-run demo is not mistaken for evidence.
51. As an evaluator, I want failures categorized as retrieval, bad link, stale evidence, coding error, test gap, reviewer error or environment failure, so that a failed hypothesis yields actionable learning.
52. As an evaluator, I want negative trials, exclusions and protocol deviations preserved, so that reporting is not biased toward successful runs.
53. As a decision maker, I want conclusions constrained by the preregistered H1–H4 decision table, so that failed efficiency or determinism claims are withdrawn rather than reframed.
54. As a developer, I want the workflow to fail with machine-readable diagnostics, so that broken prerequisites and certification gates can be automated and debugged.
55. As a developer, I want a single top-level command to reproduce ingest, certification, context compilation, evaluation and reporting for a pinned run, so that the highest test seam matches actual user operation.

## Implementation Decisions

- Extend the current dependency-light Python implementation instead of replacing its working policy core. Preserve backward compatibility for the existing demonstration workflow while introducing explicit schema versions and migrations for persisted artifacts.
- Organize the system into deep modules with narrow contracts: ingestion and normalization, code-intelligence adapter, candidate discovery, Evidence Core, review orchestration, deterministic validation, context compilation, experiment execution and reporting. The Evidence Core remains the sole system of record; agents and adapters submit observations and verdicts through its public operations.
- Use a run manifest as the root identity for every reproducible operation. It records project and task IDs, repository/document/dataset snapshots, adapter/parser/provider versions, policy and configuration hashes, model and prompt identifiers, tool inventory, environment identity, budgets, randomization assignment and references to immutable inputs/outputs.
- Normalize requirement, user story, acceptance criterion, Architecture decision/constraint/component, BD claim, DD claim, code symbol/source span, test specification/case/result, runtime observation, migration/change unit, approval and waiver as typed versioned artifacts.
- Derive non-code artifact versions from canonical UTF-8 content. Derive code identity from repository identity, commit, adapter version, qualified symbol and normalized symbol hash; treat source span/LOC as evidence scoped to that commit.
- Provide a stable adapter interface that emits observed code facts plus repository identity, commit, provider name/version, adapter configuration hash, qualified symbol, normalized symbol hash, source span, index coverage and raw result hash. Integration uses the provider's supported MCP or export boundary and never its private database.
- Implement Markdown/text and structured JSON ingestion for the benchmark path. Keep DOCX, Jira and XLSX behind the same adapter boundary; XLSX is an RTM interchange projection rather than the canonical store. Text PDF may be added through an adapter, while scanned PDF/OCR remains outside this MVP.
- Make normalization deterministic and idempotent. Re-ingesting identical pinned input yields identical artifact identities and no duplicate active records; unsupported or partially parsed regions are emitted as coverage states with provenance.
- Keep the typed graph as the canonical model and RTM/context contracts as projections. Support the edge vocabulary `derived_into`, `constrained_by`, `detailed_by`, `implemented_by`, `verified_by`, `depends_on`, `calls`, `imports`, `implements`, `migrates_to`, `supersedes`, `contradicts` and `approved_by`.
- Separate lifecycle (`candidate`, `verified`, `rejected`, `stale`, `reverified`, `disputed`) from evidence maturity (E0–E4) and orthogonal coverage/conflict states. State transitions are policy-controlled, append-only in audit history and always scoped to explicit artifact versions.
- Require at least two independent evidence kinds for E2, accountable approval on current endpoints for E3, and passing executable evidence bound to the pinned commit/environment for E4. The policy evaluates independence by evidence origin/type, not merely by record count.
- Treat LLM confidence as advisory metadata only. Candidate discovery may rank work, but confidence cannot promote lifecycle or maturity and is excluded from deterministic certification.
- Candidate Linker combines explicit identifiers, retrieval, Git history, static code relationships, tests and optional runtime observations. It optimizes candidate recall and always outputs candidates with cited evidence rather than mutating certified projections.
- Run Forward, Reverse and Adversarial review as separate roles with fresh review contexts. Each reviewer consumes the candidate plus pinned source evidence, returns a structured verdict with claim, evidence, rule and optional reproducer, and cannot approve its own proposal.
- Normalize conflicting verdicts to the same claim and artifact versions. Discard verdicts that lack evidence or use stale inputs, run deterministic reproducers when present, allow one valid counterexample to reject a universal claim, and route unresolved disputes to the accountable human role without majority-vote correctness.
- Resolve approval authority from versioned project policy. Business requirements belong to Product Owner/BA; Architecture/BD to Architect with BA where applicable; DD/code traces to Tech Lead/Developer; requirement-test/test adequacy to BA/QA; retire/rewrite decisions to Tech Lead/System Owner.
- Model waivers as versioned, scoped artifacts with owner, rationale, severity, affected gate and expiry. A waiver does not change evidence maturity and is visible in certified output wherever policy permits it.
- Compute freshness from artifact hash changes and typed graph traversal. Invalidate direct endpoint links and affected downstream paths, retain unrelated current subgraphs, and emit `impact_boundary_uncertain` when coverage cannot establish a safe boundary. Reverification binds a new endpoint hash and creates an audit event rather than overwriting history.
- Make deterministic validation independent of LLM output. It checks schema, stable identity, endpoint hashes, mandatory paths, approval authority, lifecycle policy, waiver policy, executable-evidence binding, coverage rules and canonical ordering before certification.
- Produce canonical UTF-8 JSON with stable key/list ordering and without timestamps, database row IDs, generated prose or other volatile fields. Identical pinned inputs, configuration and approved evidence must compile to byte-identical RTM output.
- Compile Migration Context Contract only from certified current evidence. Include verified requirements and as-is behavior, design claims, source identities/spans/hashes, contracts/invariants, executable tests, dependencies, bounded impact, contradictions/unknowns, forbidden/deprecated behavior, approvals and release gates.
- Add Change Context Contract as a separate deterministic projection. Include new or changed requirement, impacted design claims and code symbols, required test changes, regression surface, approvals and release gates while retaining links to the prior verified behavior envelope.
- Enforce data classification and artifact ACL before retrieval and context assembly. Keep Evidence Core state, code index references and canonical RTM in the local-first data plane. Cloud inference is policy-configurable, uses allowlisted providers and minimal context, and records provider/model/prompt/config/context hashes.
- Build the iTrustFull trace-recovery benchmark from a pinned dataset commit and a published deterministic counting procedure. Keep upstream gold links distinct from benchmark-authored design/symbol gold and report known manifest/README count discrepancies.
- Build the migration fixture from exact pinned iTrust2 v7/v8 commits. The feasibility gate must reproduce isolated build/test environments, inventory database/email/runtime dependencies and deviations, verify code-index coverage, and either pass within the preregistered time budget or select a preregistered fallback without changing evaluation rules after seeing results.
- Scope the verified behavior envelope to 5–10 requirement/acceptance claims, provenance-bearing Architecture/BD/DD artifacts, 20–50 relevant symbols, 10–20 executable/hidden tests, 3–5 known inconsistencies, one UC19 migration unit and one subsequent date-range nutrition-summary change.
- Freeze and hash requirement claims, gold manifests, rubrics and hidden tests before agent execution. Use two independent human reviewers for authored requirement/design-to-symbol/test links, retain disagreement history and report inter-reviewer agreement only as a diagnostic.
- Hidden behavior covers self-service creation, HCP authorization and patient isolation, date and enum validation, non-empty food name, serving/nutrient bounds, duplicate meal retention, verified ordering, daily totals and decimal boundaries, empty state, transaction codes 1901/1902/1903, atomic failure behavior, and trace from every approved UC19 claim to new symbols and executable tests.
- Implement an experiment runner that launches fresh isolated baseline and treatment processes, disables internet and cross-run memory during evaluation, controls raw inputs/model/tools/budgets, randomizes or counterbalances order, blinds evaluator-facing labels, and prevents builders from accessing hidden tests or reviewer verdicts.
- Baseline receives raw pinned documents/repository plus the same code-intelligence and build/test tools. Treatment receives the same capabilities plus the verified TraceContract. Both stop under identical preregistered token, tool-call and time budgets.
- Capture structured telemetry for prompts, tool calls, tokens, latency, context preparation, context-pack size, repair cycles, human verification time and all produced artifacts, subject to data policy. Store protocol deviations, exclusions and environment failures explicitly.
- Treat the proportion of hidden acceptance/regression tests passed by the final submission within fixed budget as the primary endpoint. Secondary endpoints include approved behavior coverage, trace Precision/Recall/F1 by hop/type, citation precision, elapsed and human time, token/tool cost, repair cycles, reviewer findings, certified RTM completeness and evidence reuse.
- Report cold-start and steady-state cost components separately. Do not claim acceleration if correctness improves but total steady-state effort, including ingest/review/human verification, does not improve.
- Select final-run sample size from pilot variance and budget-aware power analysis before final execution. Report all task/trial distributions, effect sizes, confidence intervals, negative results and failure categories; do not optimize prompts or thresholds on final held-out artifacts.
- Generate a decision report that maps evidence to H1 trace recovery, H2 migration correctness, H3 engineering efficiency and H4 governance. Allowed conclusions follow the preregistered decision table; one evaluated Java slice cannot justify universal or FSOFT-wide claims.
- Expose machine-readable success/failure summaries and stable exit codes for every workflow stage. The top-level workflow supports resuming from immutable successful stages but rejects reuse when an input, policy, adapter or configuration hash differs.

## Testing Decisions

- Good tests assert externally observable contracts: normalized artifacts, policy decisions, audit records, certified projections, process isolation, executable behavior and reports. They do not assert private helper calls, in-memory collection layout, exact agent prose or a specific retrieval algorithm.
- The primary acceptance seam is the top-level experiment workflow. Given a pinned run manifest and frozen benchmark assets, one command executes or resumes ingest, linking, review import, accountable approval, certification, context compilation, isolated A/B runs, hidden evaluation and reporting. Its output bundle and exit status are the main system contract.
- A smaller end-to-end certification seam runs from normalized artifact snapshot through certified RTM and Migration/Change Context Contracts without model execution. This seam must remain fast and deterministic enough for every change.
- Existing CLI subprocess tests are prior art for the top-level seam. Existing policy tests are prior art for wrong-role rejection, insufficient evidence, dispute blocking, affected-subgraph freshness and byte-identical output.
- Evidence Core contract tests cover all valid and invalid lifecycle transitions, E0–E4 derivation, independent-evidence counting, endpoint version binding, accountable authority, waiver expiry, conflict resolution and audit preservation.
- Adapter contract tests run the same conformance suite against each adapter: pinned identity, deterministic normalization, stable raw-result hash, coverage reporting, unsupported input behavior and no access to private provider storage.
- Candidate/reviewer tests use frozen small corpora and structured fake model/tool responses. They verify that all discoveries remain candidates, citations refer to retrieved pinned evidence, reviewers are isolated, self-approval is impossible and malformed/stale verdicts are rejected.
- Graph invariant tests verify mandatory Requirement → Architecture/BD → DD → Code → Test paths for the scoped claims, while permitting explicit unknown/disputed states before certification and rejecting them at gates required by policy.
- Freshness mutation tests seed requirement, Architecture/BD/DD, symbol behavior, move/rename, test/evidence, unrelated same-file, unrelated-module and parser-failure changes. They measure relevant stale-edge recall and unrelated invalidation rate against preregistered tolerance.
- Determinism tests compile the same graph repeatedly and across fresh processes, permute legal input ordering, and compare canonical bytes. They also prove that volatile audit timestamps or generated prose do not alter the canonical projection.
- Security tests verify authorization before retrieval, deny unapproved cloud egress, minimize and audit allowed context, keep hidden tests outside builder access and redact protected payloads from telemetry while retaining hashes and policy evidence.
- Migration acceptance tests execute the frozen UC19 hidden behavior set in the isolated pinned environment. They validate authorization, patient isolation, input boundaries, multiple entries, ordering where verified, totals, empty state, transaction logging, atomic failure and trace completeness.
- Subsequent-change acceptance tests add date-range nutrition summary and rerun the complete verified UC19 regression envelope, proving that Change Context Contract identifies required additions without dropping prior behavior.
- Experiment-harness tests verify fresh processes, no shared cache/history, identical budgets/tool inventories, blinded labels, randomized/counterbalanced order, stopping rules, immutable hidden assets and complete telemetry.
- Metric tests use synthetic known confusion matrices and run records to validate Precision/Recall/F1, hidden-test pass rate, cost components, evidence reuse, exclusions and confidence-interval inputs. Reports must expose raw observations behind every aggregate.
- Feasibility-gate tests are operational checks, not product correctness tests. They must fail closed with a recorded reason or activate only the preregistered fallback when build dependencies, container reproduction or code-index coverage cannot be established within budget.
- Research acceptance requires H1–H4 results to be reported even when they fail. No automated test can turn a failed hypothesis into a favorable conclusion; the decision-report validator rejects conclusions that violate the decision table.

## Out of Scope

- Production rollout across FSOFT, organization-wide savings claims or proof that the workflow generalizes to every language, framework and legacy architecture.
- Fully autonomous approval, removal of accountable humans, or use of LLM confidence/majority vote as a correctness authority.
- Zero-regression guarantees, formal proof of semantic equivalence or complete transitive impact analysis under incomplete static/runtime coverage.
- Automatic conclusions that unsupported, unindexed or untraced code is dead, followed by deletion or retirement without accountable decision.
- Scanned PDF/OCR, a full document-management suite, or polished enterprise UI.
- Direct coupling to Codebase Memory's private SQLite/storage schema or an assumption that one code-intelligence provider is complete.
- Claiming byte-identical natural-language explanations or generated code; determinism applies only to canonical structured projections for identical pinned inputs.
- Claiming fully offline AI inference. The MVP is local-first and policy-controlled, but model execution may use an approved endpoint.
- Treating iTrustFull file-level gold as complete symbol/LOC truth or treating iTrust2 as a production hospital system.
- Changing hidden tests, gold, budgets, exclusions, stopping rules or evaluation thresholds after observing final A/B output.
- Production-grade SSO, multi-tenant administration, high-availability persistence, disaster recovery or enterprise-scale performance engineering.

## Further Notes

- This spec synthesizes the idea submission, technical blueprint and scientific validation plan into an implementation target. Quantitative benefits remain hypotheses until the controlled evaluation produces evidence.
- The existing Evidence Core and UC19 demonstration fixture are the starting baseline, not the completed Validated MVP. They already provide useful prior art for artifact hashing, typed edges, role checks, freshness, canonical RTM, Migration Context Contract and CLI-level testing.
- The highest-value test seam is the top-level reproducible workflow because it crosses every critical trust boundary. Lower-level tests exist to localize failures, but passing them alone is not evidence for H1–H4.
- If iTrust2 v7/v8 cannot be reproduced within the preregistered feasibility budget, implementation must record the failure and use only the predeclared fallback. It must not quietly weaken hidden behavior or alter comparison rules.
- Research papers motivate the architecture but do not validate TraceContract's extensions. Reports must preserve the limitations stated in the source documents and separate demonstrated mechanism from measured outcome.
