# TraceContract — Judge Defense Sheet

## One-sentence position

TraceContract is a local-first evidence and certification layer that turns versioned SDLC artifacts and code observations into human-governed trace contracts which coding agents can consume and deterministic tools can audit.

## 1. “Is this just GraphRAG plus workflow?”

No. RAG/graph retrieval is used only to discover candidate evidence. TraceContract adds versioned artifact identity, candidate/verified/stale lifecycle, role approval, bidirectional/adversarial trace review, deterministic RTM compilation and executable context contracts. A candidate retrieved by AI cannot silently become certified truth.

The distinction is motivated by the finding that retrieval architecture depends on corpus/query complexity and LLM-judge verdicts are not sufficiently stable to serve as sole authority: [Triple-Robustness paper](https://arxiv.org/abs/2608.00705).

## 2. “What does Codebase Memory already solve?”

[Codebase Memory MCP](https://github.com/DeusData/codebase-memory-mcp) supplies code indexing, symbols/LOC, call/import/test edges, search, trace paths, change detection and optional runtime observations.

It does not supply first-class Requirement/Architecture/BD/DD artifacts, role-based approval, trace lifecycle, contradiction workflow, certified RTM or migration correctness evaluation. TraceContract treats it as a version-pinned code-intelligence provider, not the system of record.

## 3. “Why not let the coding agent search the repository each time?”

It can, but repeated discovery consumes tokens/tool latency and returns observations without persistent human approval/freshness state. TraceContract tests the hypothesis that verified evidence can be reused and incrementally revalidated. Net benefit is measured after charging all linker/reviewer/human costs; it is not assumed.

## 4. “If humans still verify, where is the saving?”

The proposed saving comes from evidence collection, prioritization, reuse and affected-subgraph re-verification. Humans remain accountable for domain decisions. If measured total effort does not decrease, the accelerator claim fails even if traceability improves.

## 5. “How are multiple AI reviewers independent?”

They run in fresh isolated contexts, use different charters and review artifacts/evidence without seeing proposer reasoning or peer verdicts. Forward review finds missing requirement coverage; reverse review finds untraced code; adversarial review searches for counterexamples. Multiple instances of one model are not claimed to be statistically independent human experts. Deterministic tests and accountable humans remain final gates.

## 6. “What if reviewers disagree?”

No majority vote for correctness. Normalize to the same claim/version, reject verdicts without evidence, run a deterministic reproducer where possible and give valid counterexamples priority against universal claims. Unresolved cases remain `disputed` and go to the accountable role.

## 7. “How can the RTM be deterministic when LLMs are stochastic?”

LLMs propose/explain; they do not compile the canonical RTM. Given identical pinned artifacts, adapter versions, policies and approved evidence, a deterministic compiler sorts canonical nodes/edges and excludes volatile timestamps, row IDs and prose. The byte-identical claim applies only to canonical RTM, not generated language or code.

## 8. “Why reference Executable Code Knowledge?”

[Executable Code Knowledge](https://arxiv.org/abs/2608.16295) motivates knowledge tied to source identity/span, executable evidence and freshness instead of detached prose. TraceContract extends that concept to Requirement/Architecture/BD/DD/Code/Test trace edges and human governance. The paper does not prove this extension or enterprise migration outcome; those are evaluated separately.

## 9. “What if documents are wrong or contradict code?”

No source is automatically treated as semantic truth. Code records as-is behavior; approved requirements define intended behavior. Contradictions are explicit graph artifacts. AI may draft an as-is specification, but BA/Architect/Tech Lead/System Owner decides whether a behavior is preserved, corrected or retired.

## 10. “How do you identify garbage/dead code?”

The system does not label code as garbage. It reports orthogonal states such as untraced, uncovered, stale, runtime-not-observed, partially parsed and dead-code candidate. Static absence/runtime non-observation cannot authorize deletion because reflection, DI, callbacks, rare paths and external callers may be invisible. Tech Lead/System Owner owns retire decisions.

## 11. “What if the parser or code graph misses something?”

Index coverage is evidence. Unsupported or partially parsed regions become `unknown/partially_parsed`; the RTM Validator prevents them from being presented as orphaned or complete. Where graph evidence cannot bound an impact radius, the system exposes `impact_boundary_uncertain` and broadens review.

## 12. “Can this guarantee no regression?”

No. The defensible claim is improved regression detection within a verified behavior envelope consisting of approved claims, acceptance tests, differential/golden-master tests and known constraints. Unknown areas stay visible. Hidden-test pass rate is the primary experimental endpoint.

## 13. “Is the A/B comparison fair?”

Both arms use the same model/configuration, raw artifacts, Codebase Memory, build/test tools and budgets. Runs are fresh and isolated. Treatment adds verified TraceContract. Hidden tests/rubric are frozen before runs, the evaluator is independent and all trial logs—including negative results—are reported.

## 14. “Could a public benchmark already be in model training?”

Yes; this cannot be disproved. Public iTrustFull is used for reproducibility, not an unseen-data claim. Evaluation disables internet/memory and adds a held-out mutation/task set created after the pinned corpus. Prompt/threshold tuning is separated from final evaluation.

## 15. “Why iTrust2?”

The [official iTrust2 README](https://github.com/ncsu-csc326/iTrust2#technical-info) describes v8 as a Spring Boot rewrite that lost about half the v7 use cases. UC19 Food Diary exists in [v7 requirements](https://github.com/ncsu-csc326/iTrust2/blob/v7/docs/UC19.md), [legacy API code](https://github.com/ncsu-csc326/iTrust2/blob/v7/iTrust2/src/main/java/edu/ncsu/csc/itrust2/controllers/api/APIFoodDiaryController.java) and [Cucumber scenarios](https://github.com/ncsu-csc326/iTrust2/blob/v7/iTrust2/src/test/resources/edu/ncsu/csc/itrust/cucumber/FoodDiaryEntry.feature), but not in [v8 requirements](https://github.com/ncsu-csc326/iTrust2/tree/v8/docs). This is a real documented modernization regression, not an injected demo bug.

Limits: iTrust2 is educational, not a production hospital system; v7 already used Spring; build reproducibility still needs a feasibility gate; symbol-level gold and Architecture/BD/DD fixtures are benchmark-authored.

## 16. “How does this generalize beyond Java?”

The core artifact/edge/review schema is language-neutral, while code/build adapters are not. One Java experiment demonstrates the workflow on that scope only. Each new adapter must publish index coverage and pass contract/evaluation tests. The proposal claims extensibility, not proven universal accuracy.

## 17. “Is the system fully local?”

The evidence plane, source index and canonical RTM are local-first. Model execution is policy-controlled and may use an approved cloud endpoint. Any egress must be minimal, authorized and audited. The MVP does not claim all AI functions run offline or that local and cloud models have equal quality.

## 18. “What is the business value without FSOFT numbers?”

At idea stage it is a falsifiable hypothesis: reduce repeated evidence discovery/review and approved migration/change lead time while improving trace coverage. A pilot measures cold-start cost, steady-state cost, human minutes, tokens/tool calls, test pass rate and repair cycles. No company-wide saving is asserted before data exists.

## 19. “What happens if the experiment fails?”

- H1/H4 only: position as traceability/governance, not migration accelerator.
- Correctness improves but total effort does not: optimize workflow; withdraw speed claim.
- Determinism/freshness fails: certification claim is invalid until fixed.
- No material improvement: pivot or stop rather than re-labeling metrics.

## 20. “Where is AI essential rather than decorative?”

AI plans multi-tool discovery across incomplete artifacts, drafts atomic claims, proposes semantic/multi-hop traces, finds contradictions, generates counterexamples, compiles task-specific context and performs implementation. Deterministic systems and humans bound AI authority; they do not replace the discovery/reasoning workload.

## Red-line claims to avoid

- “Zero regression” or “guaranteed correct migration.”
- “Fully automated RTM.”
- “Works on every language/project.”
- “All data/model processing is local.”
- “Unlinked code is dead or garbage.”
- “Multiple LLM reviewers are objective ground truth.”
- “Paper results prove effectiveness at FSOFT.”
- Any time/token/saving percentage not measured under the preregistered protocol.

