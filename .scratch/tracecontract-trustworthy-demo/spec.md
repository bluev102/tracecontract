# TraceContract Trustworthy Demo

Status: ready-for-agent

## Problem Statement

TraceContract hiện đã có một Evidence Core Python, workflow orchestration, reviewer roles, deterministic RTM output, context-contract projections và một local test suite tốt. Tuy nhiên, audit đối chiếu với Technical Blueprint và Judge Defense cho thấy đường certification vẫn có thể fail open: candidate có thể ảnh hưởng authority policy, verdict của artifact version cũ có thể được dùng lại khi reverify version mới, coverage `unknown/partial` không chặn affected certification path, và mode không hợp lệ hoặc fixture-only path vẫn có thể trả về `certified`.

Demo UC19 hiện tại chỉ là một mechanism fixture nhỏ. Nó không chứa một pinned, locally reproducible iTrust2 trace slice với requirement, true code call path, Codebase Memory observations và official executable test evidence. Vì vậy, việc 43 contract tests hiện tại pass chứng minh nhiều cơ chế nội bộ nhưng chưa đủ để bảo vệ claim về trustworthy certification, real-data provenance, E4 evidence hoặc completed migration.

Nhóm cần một Tier 1 Trustworthy Demo hoàn thành trong năm ngày làm việc. Demo phải fail closed tại mọi trust boundary, dùng database làm system of record, bind policy/review/approval/certificate vào immutable artifact and edge revisions, certify theo explicit claim scope, chạy real isolated AI reviewer processes, và tạo E4 evidence trên một pinned iTrust2 UC19 slice. Blueprint vẫn là kiến trúc đích; acceptance spec này là hợp đồng thực thi của Tier 1; Judge Defense chỉ được claim điều đã có evidence.

## Solution

Xây dựng lại certification path thành một policy-bound, revision-aware workflow với SQLite là system of record. Mỗi artifact version, policy version, edge revision, evidence item, reviewer verdict, approval assertion và certificate là immutable record. Lifecycle changes được ghi bằng append-only events. Một policy JSON canonical và versioned sẽ resolve approval roles, review requirements, evidence maturity, coverage rules và mandatory-path participation; candidate agents không được tự khai báo authority.

Certification được thực hiện theo explicit claim scope. Mỗi claim nhận trạng thái `certified`, `blocked` hoặc `uncertain`; bundle tổng nhận `fully_certified`, `partially_certified` hoặc `not_certified`. Affected coverage uncertainty phải chặn đúng certification path, trong khi claim độc lập có evidence đầy đủ vẫn có thể certify. Policy changes hoặc artifact version changes tạo edge revision mới và làm revision cũ stale; review/approval cũ chỉ còn giá trị audit.

Recorded demo dùng UC19/E2 của iTrust2 v7 tại full commit `d5a08a08884009b1ddb41dba312ab8cb563b3769`: invalid servings phải bị từ chối. Sparse local snapshot giữ upstream requirement, Java model constructor, `setServings`, API controller và official API test. Architecture/DD và gold trace artifacts do benchmark author tạo phải được gắn provenance rõ ràng. Codebase Memory phải index declared snapshot scope và xuất pinned provider evidence. Candidate Linker cùng Forward, Reverse và Adversarial reviewers chạy trong fresh isolated containers. Official iTrust2 test phải pass trong pinned environment để Tier 1 đạt E4; nếu environment hoặc test không đạt, run kết thúc bằng machine-readable failure thay vì hạ chuẩn sang fixture evidence.

Một top-level command là acceptance seam chính. Command bootstrap/migrate database, ingest pinned inputs and policy, normalize provider observations, run candidate discovery and isolated review, import accountable approval, certify claim scope, compile context, persist canonical certificate bytes, và export an auditable evidence bundle. Fixture-only demo được giữ như một mechanism demonstration nhưng không bao giờ được phát nhãn `certified`.

## User Stories

1. As a Delivery Manager, I want one reproducible top-level TraceContract run, so that I can evaluate a complete trust-boundary workflow instead of disconnected demos.
2. As a Delivery Manager, I want Tier 1, Tier 2, and Tier 3 outcomes distinguished, so that a trustworthy demo is not misrepresented as a validated MVP or production system.
3. As a Judge, I want every defense claim labelled by evidence status, so that implemented mechanisms are not confused with demonstrated or measured outcomes.
4. As a Release Owner, I want fixture-only runs prevented from emitting certified status, so that synthetic evidence cannot masquerade as real certification.
5. As an Operator, I want unsupported or misspelled workflow modes rejected, so that configuration errors fail closed.
6. As a Policy Owner, I want approval and certification rules defined in a versioned canonical policy, so that authority is not scattered through Python conditionals.
7. As a Policy Owner, I want policy rules selected by source kind, edge type, and target kind, so that different trace relationships can enforce different governance.
8. As a Policy Owner, I want policy versions hash-bound to runs and certificates, so that the rules used for certification are reproducible.
9. As a Policy Owner, I want policy changes to stale affected edge revisions, so that old authority rules cannot silently survive a governance change.
10. As a Candidate Linker, I want to propose endpoints, edge type, evidence, and coverage without selecting the approver role, so that discovery cannot lower its own approval bar.
11. As an Artifact Owner, I want every artifact content change to create an immutable artifact version, so that evidence remains tied to exact content.
12. As an Auditor, I want logical edge identity separated from edge revision identity, so that the history of one conceptual trace remains navigable across artifact changes.
13. As an Auditor, I want edge revision identity to include endpoint versions and policy version, so that review and approval cannot cross version boundaries.
14. As a Reviewer, I want a changed endpoint to require a fresh edge revision, so that previous verdicts cannot certify new behavior.
15. As a Reviewer, I want stale verdicts retained only as immutable history, so that auditability does not imply continued authority.
16. As a Candidate Linker, I want every agent-discovered relationship to begin as a candidate revision, so that discovery cannot certify its own output.
17. As a Forward Reviewer, I want a fresh assignment containing the scoped candidate and pinned evidence, so that I can find missing requirement coverage independently.
18. As a Reverse Reviewer, I want a fresh assignment containing changed or relevant code facts, so that I can find untraced behavior and scope creep independently.
19. As an Adversarial Reviewer, I want a fresh assignment focused on contradictions and counterexamples, so that plausible but false claims are challenged.
20. As a Governance Owner, I want reviewers unable to see proposer reasoning or peer verdicts, so that review lanes preserve protocol independence.
21. As a Governance Owner, I want reviewer identities distinct from one another, the proposer, and the approver, so that one actor cannot occupy incompatible trust roles.
22. As an Accountable Approver, I want the required role resolved from trusted policy, so that approval authority cannot be candidate-controlled.
23. As an Accountable Approver, I want my approval assertion bound to the exact edge revision and policy hash, so that it cannot be replayed against another revision.
24. As an Auditor, I want Tier 1 approval identity described as a reproducible assertion rather than cryptographically authenticated identity, so that the system does not overclaim identity assurance.
25. As a Code Intelligence Integrator, I want provider output pinned by project, generation, provider version, adapter configuration, raw-result hash, and pagination state, so that observed facts are reproducible.
26. As a Code Intelligence Integrator, I want coverage scoped to declared paths and line ranges, so that sparse-snapshot completeness is not confused with repository-wide completeness.
27. As a Reviewer, I want `partial`, `unknown`, `unsupported`, and `excluded` regions represented explicitly, so that missing coverage cannot be approved away.
28. As a Release Owner, I want coverage uncertainty to block only affected certification paths, so that fail-closed behavior does not cause unrelated claims to fail.
29. As a Release Owner, I want any uncertain mandatory path reported as `impact_boundary_uncertain`, so that bounded impact is never implied without evidence.
30. As a System Owner, I want the product prohibited from inferring dead or orphaned code from sparse coverage, so that incomplete observations cannot authorize retirement.
31. As a Project Owner, I want one SQLite project database to contain multiple immutable runs, so that evidence history is retained across attempts.
32. As an Operator, I want each run and attempt to have immutable identity, so that retries never overwrite previous outcomes.
33. As an Operator, I want failed runs and protocol deviations preserved, so that negative evidence remains auditable.
34. As an Operator, I want batch imports and certification writes transactionally atomic, so that partial governance state cannot be committed.
35. As an Operator, I want completed stages reusable only when all input, policy, and output hashes match, so that resume cannot cross run identities.
36. As an Operator, I want in-progress agent subprocesses treated as non-resumable, so that a crashed external process cannot be assumed complete.
37. As a Database Maintainer, I want deterministic schema bootstrap and forward-only migrations, so that database state can be reproduced and upgraded safely.
38. As a Database Maintainer, I want older binaries to reject newer schema versions, so that unsupported data is not silently misread.
39. As an Auditor, I want canonical certificate bytes stored in the database, so that filesystem exports are not mistaken for the system of record.
40. As an Auditor, I want exports regenerated deterministically from committed database records, so that lost build artifacts can be reproduced without recertification.
41. As a Security Owner, I want large evidence stored as immutable content-addressed blobs with hashes and classification, so that the database remains minimal and auditable.
42. As a Security Owner, I want code observations stored as identity, span, hash, coverage, and provenance rather than unrestricted source copies, so that source-derived data is minimized.
43. As a Release Owner, I want certification requested for explicit claim IDs, so that certificate scope is never implicit.
44. As a Release Owner, I want each scoped claim reported as certified, blocked, or uncertain, so that partial outcomes remain precise.
45. As a Release Owner, I want the overall bundle reported as fully certified, partially certified, or not certified, so that claim-level results are not flattened.
46. As a Release Owner, I want invalid revisions visible in the report rather than silently omitted from canonical output, so that gaps cannot disappear during export.
47. As a Coding Agent, I want context compilation limited to certified current claims, so that stale or disputed evidence cannot become implementation instruction.
48. As a Coding Agent, I want related unknowns retained as limitations in the context contract, so that certified scope does not hide adjacent uncertainty.
49. As a Benchmark Author, I want the upstream iTrust2 repository pinned by full commit SHA, so that a mutable branch cannot change benchmark evidence.
50. As a Benchmark Author, I want a sparse immutable local snapshot with per-file hashes, so that recorded runs do not fetch mutable remote content.
51. As a Benchmark Author, I want upstream and benchmark-authored artifacts labelled separately, so that authored Architecture/DD interpretations are not presented as official iTrust2 documentation.
52. As a Domain Reviewer, I want UC19/E2 represented as an atomic requirement that non-positive servings are rejected, so that the certificate has a precise behavioral claim.
53. As a Developer, I want the real code path to include the API controller, model constructor, and `setServings`, so that the graph does not invent a direct call absent from source.
54. As a QA Reviewer, I want the official invalid-entry API test bound to the pinned source snapshot, so that test evidence refers to the same version as code evidence.
55. As an Auditor, I want test-source existence distinguished from passing test execution, so that E3 evidence cannot be mislabeled E4.
56. As an Evaluator, I want the official iTrust2 test executed in a pinned environment, so that the Trustworthy Demo produces E4 executable evidence.
57. As an Evaluator, I want environment failure reported as `environment_blocked`, so that the workflow never substitutes a fixture pass for missing executable evidence.
58. As an Infrastructure Owner, I want agent and test containers pinned by image digest, so that runtime identity is reproducible.
59. As a Security Owner, I want evaluation containers launched without network access when network is unnecessary, so that external retrieval cannot contaminate the run.
60. As a Security Owner, I want container inputs read-only and outputs isolated, so that agents cannot alter evidence or hidden assets.
61. As an Infrastructure Owner, I want container time, memory, and process limits, so that runs obey declared resource boundaries.
62. As an Agent Operator, I want real Candidate Linker and reviewer subprocesses used in the recorded demo, so that the AI workflow is demonstrated rather than simulated.
63. As a Test Author, I want deterministic fixture agent responses for contract tests, so that protocol correctness can be tested without stochastic failures.
64. As an Auditor, I want every agent assignment, command identity, output, and protocol deviation hash-recorded, so that the recorded run can be inspected.
65. As a CLI User, I want one top-level command to bootstrap, ingest, review, approve, certify, compile, and report, so that the highest test seam matches real usage.
66. As a CLI User, I want stable machine-readable failure codes, so that policy, coverage, environment, review, and certification failures can be automated.
67. As a Demo User, I want the legacy fixture path explicitly labelled `mechanism_demonstrated`, so that backward compatibility does not weaken certification semantics.
68. As a Test Author, I want adversarial regression tests for every audited bypass, so that trust-boundary failures cannot return unnoticed.
69. As a Test Author, I want fresh-database runs to produce byte-identical canonical certificate output, so that determinism is proven independently of row IDs and timestamps.
70. As a Technical Writer, I want the blueprint, acceptance contract, and defense claims separated, so that architecture goals, release gates, and current evidence remain distinct.
71. As a Technical Writer, I want defense claims labelled implemented, demonstrated, measured, planned, or unsupported, so that readers can verify the maturity of every statement.
72. As a Judge, I want demonstrated and measured claims linked to evidence bundle records, so that assertions can be checked without trusting prose.
73. As an Engineering Manager, I want Tier 2 migration and controlled evaluation work excluded from Tier 1, so that the five-day milestone stays focused on trustworthy certification.
74. As a Platform Owner, I want production identity, PostgreSQL, enterprise policy administration, and high availability deferred to Tier 3, so that the demo does not pretend to be production-ready.
75. As a Delivery Manager, I want E4 convenience work cut before trust-boundary correctness if the schedule slips, so that the team never trades fail-closed governance for presentation polish.

## Implementation Decisions

- Deliver the product in three explicit tiers. Tier 1 is the Trustworthy Demo in this spec. Tier 2 is the Validated MVP covering real v7-to-v8 migration, subsequent feature change, hidden tests, controlled comparison, and measured outcomes. Tier 3 covers production deployment and enterprise controls.
- Treat the Technical Blueprint as target architecture, this acceptance spec as Tier 1's executable contract, and the Judge Defense as an evidence-indexed claim sheet. Every defense claim uses one of: implemented, demonstrated, measured, planned, or unsupported.
- Use one top-level run as the primary product and acceptance seam. Lower-level commands may exist for diagnosis, but no alternate path may bypass the same policy and certification gates.
- Use SQLite as Tier 1's local-first system of record. Enable foreign keys and write-ahead logging. Use explicit transactions around batch imports, lifecycle changes, stage checkpoints, and certificate creation.
- Use a relational immutable-record model with append-only lifecycle events rather than a generic event-sourcing framework. Persist runs, attempts, checkpoints, artifact versions, policy versions, logical edges, edge revisions, evidence, verdicts, approvals, certificates, lifecycle events, and export records as separate domain concepts.
- Make successful records immutable. Content changes create new versions or revisions. Stale, rejected, disputed, superseded, and failed outcomes are expressed by subsequent lifecycle events rather than destructive updates.
- Support multiple immutable runs in one project database. A retry creates a new attempt. Failed runs and protocol deviations remain queryable.
- Make stage resume hash-bound. Reuse only a completed stage whose manifest, input, policy, command, and output identities match. Never resume an agent process that was in progress when execution stopped.
- Use deterministic forward-only database migrations with an explicit schema version. Bootstrap a new database deterministically, migrate in a transaction, back up before migration, and reject database versions newer than the running binary supports.
- Store canonical certificate bytes in SQLite. Treat external JSON artifacts as deterministic exports, not certification authority. Store large evidence as immutable content-addressed blobs referenced by URI, hash, media type, and classification.
- Define a versioned canonical policy schema. A rule is selected using source artifact kind, edge type, and target artifact kind and supplies allowed approver roles, required reviewer roles, minimum independent evidence, accepted coverage states, executable-evidence requirements, and mandatory-path participation.
- Exclude candidate-selected roles from the candidate contract. Evidence Core resolves policy from trusted policy input. Bind the policy hash to the run, edge revision, reviewer batches, approval assertions, and certificates.
- Separate logical edge identity from immutable edge revision identity. Compute revision identity from the logical edge, source artifact version, target artifact version, and policy hash.
- When an endpoint or relevant policy changes, mark the previous revision stale through a lifecycle event and create a new candidate revision. Keep previous evidence, verdicts, and approval as immutable history, but never count them toward the new revision.
- Require a fresh Forward, Reverse, and Adversarial verdict for every review-required Tier 1 revision after endpoint or policy change. Incremental reviewer selection is a Tier 2 optimization.
- Bind each reviewer verdict to the exact edge revision, endpoint hashes, policy hash, candidate snapshot hash, reviewer role, reviewer identity, evidence hashes, isolation identity, and structured outcome.
- Require reviewer subjects to be distinct from each other, the proposer, and the accountable approver for the same edge revision. Do not use majority vote as correctness authority.
- Resolve one accountable approval role per edge revision from policy. Business requirement authority belongs to BA/Product Owner; Architecture/BD authority to Architect; DD-to-code authority to Tech Lead/Developer; requirement-test adequacy to QA/BA. Multi-party quorum and delegation are deferred.
- Treat Tier 1 approval subject as a hash-pinned assertion, not cryptographically authenticated human identity. Preserve this limitation in all reports and defense claims.
- Keep lifecycle, evidence maturity, coverage, and conflict orthogonal. Human review or approval cannot convert unknown parser coverage into complete coverage.
- Define coverage relative to an explicit snapshot scope of repository commit, included paths and line ranges, provider generation, pagination state, parse gaps, and excluded paths. Always report repository-wide coverage as false for the sparse Tier 1 snapshot.
- Apply coverage gates per affected claim path. Coverage-sensitive code and impact edges require policy-accepted coverage. Partial, unknown, unsupported, or excluded coverage produces uncertainty and blocks the affected mandatory path without blocking independent complete claims.
- Certify explicit claim scopes rather than the whole graph implicitly. Return certified, blocked, or uncertain for each claim and fully certified, partially certified, or not certified for the bundle. Never silently omit invalid edges or revisions.
- Validate schema, identity, endpoint freshness, policy hash, mandatory paths, coverage, review independence, accountable approval, evidence maturity, executable binding, and canonical ordering before certificate creation.
- Compile Migration or Change Context only from certified current claims. Preserve adjacent unknowns and contradictions as limitations, and prevent blocked or uncertain claims from becoming implementation instructions.
- Pin the Tier 1 benchmark to the official iTrust2 v7 full commit `d5a08a08884009b1ddb41dba312ab8cb563b3769`. Use UC19/E2 non-positive servings rejection as the primary claim.
- Use a sparse local snapshot of the upstream requirement, model constructor, `setServings` validation, API controller, and official invalid-entry API test. Record upstream repository identity, full commit, original path, content hash, and classification for every snapshot item. Runtime must not fetch mutable remote content.
- Model the scoped graph with an upstream requirement, benchmark-authored Architecture claim, benchmark-authored DD claim, model constructor symbol, `setServings` symbol, API controller symbol, and official API test artifact.
- Preserve the real call path from API controller to model constructor to `setServings`. Do not fabricate a direct controller-to-setter call. Require both the observable API path and the domain-invariant path in scoped certification.
- Clearly mark Architecture/DD artifacts and gold trace mappings as benchmark-authored interpretations. They remain candidates subject to independent review and accountable approval rather than trusted upstream truth.
- Require Codebase Memory in the recorded demo. Pin provider project/generation/version/configuration, raw-result hash, pagination state, resolution evidence, and scoped coverage. Provider observations remain evidence and candidates, not RTM authority.
- Permit complete, pinned observed code edges to reach corroborated maturity, but require Tech Lead/Developer approval when those edges participate in a mandatory certified path. Heuristic or partial-resolution edges remain uncertain.
- Require E4 for Tier 1 success. Execute the official iTrust2 test in a pinned environment and bind its passing result, exact command, environment identity, repository commit, test-source hash, and output hashes to the certificate. If the environment or test is unavailable, fail with environment-blocked status rather than using fixture evidence.
- Run Candidate Linker, Forward Reviewer, Reverse Reviewer, Adversarial Reviewer, and official tests in fresh containers. Pin images by digest, disable network when unnecessary, mount inputs read-only, isolate outputs, withhold peer verdicts and hidden assets, and apply resource limits.
- Use real agent subprocesses for the recorded acceptance run and deterministic fixture runners for contract tests. Hash-bind agent assignments, commands, inputs, outputs, telemetry, and protocol deviations.
- Rename and demote the legacy fixture workflow to a mechanism demonstration. It may emit mechanism-demonstrated but can never emit certified. Reject every workflow mode outside an explicit allowlist.
- Preserve stable machine-readable statuses and errors for invalid input, unsupported mode, policy failure, coverage uncertainty, review failure, approval failure, environment failure, certification failure, and successful scoped certification.
- Exclude timestamps, database row IDs, temporary paths, generated prose, and process ordering from canonical certificate material. Prove deterministic certificate bytes across fresh databases with identical pinned inputs.
- Keep the implementation dependency-light where that does not weaken the agreed environment contract. Database access remains standard SQLite; container and Java build dependencies are explicit run prerequisites rather than hidden Python dependencies.

## Testing Decisions

- Prefer the highest externally observable seam: one top-level run starting with a pinned manifest and empty database and ending with persisted certificate records, context output, report, evidence bundle, and exit status. This is the primary acceptance seam.
- Keep lower-level seams only where they localize failures: policy resolution, immutable revision creation, coverage classification, review/approval import, scoped certification, SQLite repository transactions, migrations, deterministic serialization, provider normalization, and agent/container execution.
- Good tests assert observable policy decisions, persisted immutable records, lifecycle events, certificate status, canonical bytes, process/container boundaries, and machine-readable failures. They do not assert private helper calls, SQL statement order, in-memory dictionary layout, exact agent prose, or a particular retrieval algorithm.
- Preserve the existing policy, workflow, adapter, process isolation, security, metrics, ingestion, orchestration, and deterministic-output tests as prior art. Update expectations only where the accepted breaking changes intentionally remove fail-open behavior.
- Add a regression test proving candidate-provided or arbitrary approver roles cannot influence policy resolution or certify an edge revision.
- Add a regression test proving an unknown workflow mode fails before artifact approval or certificate creation.
- Add a regression test proving fixture-only execution emits mechanism-demonstrated and never writes a certificate.
- Add a regression test proving reviewer verdicts bound to an old endpoint or policy hash cannot approve or reverify a new edge revision.
- Add a regression test proving a policy change stales affected revisions and requires fresh review and approval.
- Add coverage tests proving partial, unknown, unsupported, or excluded coverage blocks the affected mandatory path, emits impact-boundary-uncertain, and leaves independent complete claims certifiable.
- Add graph invariant tests proving the required UC19 API path and domain-invariant path are present and that the controller-to-constructor-to-setter relationship is not shortened incorrectly.
- Add SQLite tests for atomic batch rollback, immutable record constraints, failed-run preservation, exact-hash stage reuse, new-attempt creation, and deterministic schema bootstrap.
- Add migration tests proving forward migration is transactional and that an older binary rejects a database with a newer schema version.
- Add fresh-database determinism tests proving identical pinned inputs produce byte-identical canonical certificate output regardless of row IDs, event insertion timing, or legal input ordering.
- Add provider contract tests proving sparse snapshot coverage remains scoped, repository-wide completeness stays false, pagination gaps cannot claim completeness, and heuristic relationships cannot satisfy complete mandatory-path policy.
- Add reviewer protocol tests proving each role receives a fresh isolated assignment, cannot see peer verdicts, returns schema-valid evidence-bound output, and cannot reuse isolation or command identity.
- Add container acceptance tests proving image digest pinning, read-only inputs, isolated outputs, unavailable hidden assets, disabled network where configured, and enforced time/resource limits.
- Add executable-evidence tests proving source-level test presence only reaches E3 and that E4 requires a passing official test result bound to the same commit and environment. Environment failure must produce environment-blocked, not fixture-backed success.
- Add export tests proving canonical certificate data is loaded from SQLite, filesystem exports can be deleted and regenerated, and modified exports cannot be re-imported as authority without full validation.
- Record one real-agent, real-Codebase-Memory, real-iTrust2 E4 demonstration run. Preserve its manifest, database identity, environment/image digests, agent artifacts, executable test result, certificate, report, and bundle hashes as reviewable acceptance evidence.

## Out of Scope

- The full iTrust2 v7-to-v8 UC19 migration, v8 implementation, and subsequent date-range nutrition-summary feature. These belong to Tier 2.
- Expanding Tier 1 to 5–10 requirements, 20–50 symbols, 10–20 hidden tests, or 3–5 known inconsistencies. Tier 1 proves one real scoped E4 claim and its trust boundaries.
- Controlled baseline-versus-treatment experiments, repeated trials, power analysis, confidence intervals, efficiency conclusions, and FSOFT-wide business-value measurements. These belong to Tier 2.
- Treating iTrust2 test existence or fixture output as executable pass evidence. Tier 1 E4 requires a real pinned test run.
- Incremental selection of only some reviewers after change. Tier 1 reruns all three independent review lanes for a changed review-required revision.
- Multi-party approval quorum, delegated authority, cryptographic human identity, SSO, key rotation, and non-repudiation. These belong to Tier 3.
- PostgreSQL, multi-writer distributed concurrency, high availability, backup orchestration, disaster recovery, and enterprise-scale performance engineering. These belong to Tier 3.
- Encryption at rest, production secrets management, enterprise policy administration UI, and organization-wide ACL administration.
- Additional document adapters such as DOCX, Jira, XLSX, PDF, or OCR and additional language/build adapters beyond the pinned Java slice.
- Repository-wide completeness, complete transitive impact analysis, automatic dead-code classification, or deletion/retirement decisions based on missing observations.
- Production deployment, universal language/framework claims, zero-regression guarantees, autonomous approval, or LLM majority vote as correctness authority.
- Maintaining backward compatibility for any behavior that lets fixture, unknown mode, candidate-selected authority, stale review, or insufficient coverage reach certified output.

## Further Notes

- Tier 1 is planned as a five-working-day milestone. The implementation order is: acceptance and adversarial red tests; SQLite schema and sparse snapshot; policy and immutable revisions; scoped certification and coverage; workflow/container agents and E4 execution; then hardening, recorded demo, exports, and defense-document updates.
- If schedule pressure appears, presentation polish, convenience commands, secondary claims, and extra benchmark paths should be cut before any trust-boundary gate, database transaction, or fail-closed regression test.
- The user will prepare the required Java, build, database, container, Codex, and iTrust2 execution environment. Environment readiness must still be checked by the top-level workflow and captured as pinned evidence rather than assumed.
- The official iTrust2 repository supplies requirement, code, and test sources, but it does not supply the complete semantic trace asserted by this benchmark. Co-location is evidence, not an author-declared link. Benchmark-authored Architecture/DD and gold mappings must remain visibly distinct.
- The official invalid-entry API test asserts HTTP 400 for invalid input but does not by itself prove every error-message or causality detail. The scoped claim and reviewers must not extend beyond what the evidence supports.
- Passing Tier 1 proves a trustworthy certification mechanism on one real E4 slice. It does not prove completed migration, comparative engineering benefit, repository-wide trace quality, or production readiness.
