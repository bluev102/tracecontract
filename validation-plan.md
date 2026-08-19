# TraceContract — Scientific Validation Plan

## 1. Research questions and falsifiable hypotheses

### H1 — Trace recovery

TraceContract candidate discovery và review workflow cải thiện trace quality so với baseline retrieval trên public gold links.

Failure condition: không có improvement có ý nghĩa thực tiễn về Precision/Recall/F1 hoặc improvement chỉ xuất hiện do leakage/tuning trên test set.

### H2 — Migration correctness

Trong cùng model/tool/budget, coding agent nhận verified Migration Context Contract đạt hidden acceptance/regression pass rate cao hơn agent nhận raw artifacts.

Failure condition: treatment không tốt hơn baseline trên primary endpoint hoặc advantage biến mất qua repeated trials/tasks.

### H3 — Engineering efficiency

Sau khi tính ingest, agent review và human verification, TraceContract giảm steady-state time/effort cho approved migration/change tasks.

Failure condition: net effort/cost không giảm. Nếu H1/H2 pass nhưng H3 fail, không claim migration accelerator.

### H4 — Governance mechanism

Với cùng pinned inputs/configuration, canonical RTM repeatable; seeded artifact changes làm stale đúng affected trace paths.

Failure condition: canonical outputs khác nhau, seeded relevant change bị bỏ sót hoặc unrelated artifacts bị invalid quá mức vượt preregistered tolerance.

## 2. Evaluation assets

### 2.1 Trace benchmark: iTrustFull

- [Dataset](https://github.com/tobhey/finegrained-traceability/tree/main/datasets/iTrustFull)
- [Gold solution links](https://raw.githubusercontent.com/tobhey/finegrained-traceability/main/datasets/iTrustFull/itrust_solution_links.txt)
- [Method call graph](https://github.com/tobhey/finegrained-traceability/blob/main/datasets/iTrustFull/itrust_method_callgraph.json)

Observed manifests in the referenced package contain 131 requirement fragments, 367 targets (226 Java + 141 JSP) and 399 gold links. The included README appears to repeat the non-JSP counts 226/286. Evaluation must pin the dataset commit, publish the counting script/method and report this metadata discrepancy rather than silently choosing favorable counts.

iTrustFull is a flattened traceability corpus, not a runnable migration application. Gold links are mainly artifact/file level, not complete symbol/LOC truth.

### 2.2 Migration fixture: iTrust2 v7 UC19 → v8

The [official iTrust2 README](https://github.com/ncsu-csc326/iTrust2#technical-info) describes v8 as a significant rewrite to Spring Boot 2.3.7 and notes that about half of the v7 use cases were lost.

Pinned source artifacts:

- [UC19 requirement](https://github.com/ncsu-csc326/iTrust2/blob/v7/docs/UC19.md)
- [v7 API controller](https://github.com/ncsu-csc326/iTrust2/blob/v7/iTrust2/src/main/java/edu/ncsu/csc/itrust2/controllers/api/APIFoodDiaryController.java)
- [v7 Cucumber feature](https://github.com/ncsu-csc326/iTrust2/blob/v7/iTrust2/src/test/resources/edu/ncsu/csc/itrust/cucumber/FoodDiaryEntry.feature)
- [v7 developer guide](https://github.com/ncsu-csc326/iTrust2/blob/v7/docs/Developers-Guide.md)
- [v8 requirement directory without UC19](https://github.com/ncsu-csc326/iTrust2/tree/v8/docs)
- [iTrust2 license](https://github.com/ncsu-csc326/iTrust2/blob/main/LICENSE)

Exact claim: Spring MVC/Java EE WAR to Spring Boot restoration, not JSP-only to Spring Boot. iTrust2 is an educational EHR, not a production hospital system.

Feasibility gate before experiment:

1. Pin exact v7/v8 commits.
2. Reproduce build/test environments in isolated containers.
3. Record DB/email/runtime dependencies and deviations from guides.
4. Confirm Codebase Memory coverage for relevant Java/resources.
5. If reproducibility fails under predefined time budget, switch to preregistered fallback rather than modifying evaluation rules.

### 2.3 Subsequent feature task

After restoring UC19, add a date-range nutrition summary. The feature is required to preserve the previously verified UC19 behavior envelope.

## 3. Gold and hidden-test construction

Architecture/BD/DD and symbol-level gold are benchmark-authored artifacts, because upstream does not supply complete gold at those levels.

Protocol:

1. Author requirement claims and expected behavior before agent runs.
2. Two independent reviewers label requirement/design → old symbol/test links.
3. Resolve disagreement using artifact version, evidence and executable reproducer; retain audit trail.
4. Hash/freeze gold manifests, rubrics and hidden tests.
5. Builder agents cannot read hidden tests or reviewer verdicts.
6. Report inter-reviewer agreement as diagnostic, not proof of truth.

Hidden behavior set should cover:

- Patient creates entries only for self; HCP cannot create.
- Authorized HCP can view patient diary; no cross-patient data leakage.
- Future date rejected; today/past accepted.
- Meal type constrained to valid enum.
- Food name non-empty.
- Servings > 0; nutrient fields >= 0.
- Multiple entries for same meal type retained.
- Results ordered newest-first if required by verified claim.
- Per-day totals including decimal/boundary cases.
- Correct empty state.
- Transaction logging codes 1901/1902/1903 with correct actors.
- Validation failure leaves no partial persistence/audit artifact.
- Every approved UC19 claim traces to new symbol and executable test.

## 4. Controlled A/B design

| Control | Baseline | Treatment |
|---|---:|---:|
| Model/version/config | same | same |
| Fresh isolated agent process | yes | yes |
| Raw repository/documents | yes | yes |
| Codebase Memory MCP | yes | yes |
| Build/test tools | yes | yes |
| Token/tool/time budget | same | same |
| Verified TraceContract | no | yes |

“Same agent” means same model/configuration, not shared conversation or memory.

Controls:

- Randomize/counterbalance A/B order.
- Blind treatment labels as X/Y for evaluator-facing artifacts.
- No shared caches, chat history or agent memory between runs.
- Independent evaluator; generated-code agent cannot judge its own output.
- Pin prompts, tools, model and dependency versions.
- Record every prompt, tool call, token count, elapsed time and produced artifact, subject to data policy.
- Preregister task list, budgets, exclusion rule and stopping rule.

## 5. Metrics

### Primary endpoint

Proportion of hidden acceptance and regression tests passed by the final submission within fixed budget.

Do not use LLM preference/judge score as primary correctness endpoint.

### Secondary endpoints

- Approved behavior coverage.
- Precision/Recall/F1 by trace hop/type.
- Citation/evidence precision for reported IDs/LOC.
- End-to-end elapsed time.
- Human evidence-search and verification minutes.
- Input/output tokens and tool calls.
- Context preparation time and context-pack size.
- Number of repair/review cycles.
- Reviewer findings by severity.
- Certified RTM completeness.
- Evidence reuse rate across subsequent change tasks.

### Cost views

```text
Cold-start cost
= ingest + candidate linking + agent review
  + human verification + implementation

Steady-state change cost
= impact analysis + affected-subgraph re-verification
  + implementation + release review

Net agent cost per approved change
= discovery tokens + reviewer tokens + tool latency
  - reusable verified-context benefit
```

Report raw components; do not hide human or reviewer-agent cost inside an aggregate.

## 6. Repeatability and freshness tests

### Canonical repeatability

Run canonical RTM compilation repeatedly with identical:

- Repository/document snapshots.
- Provider/parser/adapter versions.
- Configuration and policy hashes.
- Approved evidence set.

Exclude volatile timestamps, auto-increment IDs and generated prose; sort all canonical nodes/edges. Expected result is byte-identical canonical output. This claim does not apply to natural-language explanations or generated code.

### Freshness mutation suite

Seed changes at different layers:

- Requirement claim change.
- Architecture/BD/DD change.
- Code-symbol behavior change.
- Code move/rename with and without semantic change.
- Test/evidence change.
- Unrelated same-file and unrelated-module controls.
- Parser failure/unsupported region.

Measure relevant stale-edge recall and unrelated invalidation rate. If the graph cannot bound impact, the expected state is `impact_boundary_uncertain`, not a false claim of completeness.

## 7. Leakage and bias controls

- Public benchmark results demonstrate reproducibility, not proof the model never saw the corpus.
- Disable internet and cross-run memory during evaluation.
- Create a held-out mutation/task set after pinning the public corpus.
- Do not tune thresholds/prompts on final test artifacts.
- Freeze hidden tests before observing A/B output.
- Separate benchmark author, contract builder, coding agent and evaluator duties.
- Publish negative trials and protocol deviations.

## 8. Analysis and reporting

- Choose sample size using pilot variance and budget-aware power analysis before final runs.
- With small samples, emphasize per-task results, effect sizes and confidence intervals rather than overstated p-values.
- Report distributions, not only the best/average demo.
- Record failures by category: retrieval, bad link, stale evidence, coding error, test gap, reviewer error or environment failure.
- Do not extrapolate one Java slice to all languages or FSOFT-wide savings.

## 9. Decision table

| Outcome | Allowed conclusion |
|---|---|
| H1/H4 pass only | Traceability/governance mechanism shows value |
| H2 pass, H3 fail | Context may improve correctness but is not yet an accelerator |
| H2/H3 pass | Evidence supports migration/change acceleration on evaluated scope |
| H4 fail | Deterministic certification claim must be withdrawn/fixed |
| No hypothesis passes | Pivot or stop; do not reframe the same data as success |

