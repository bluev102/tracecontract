# TraceContract MVP

This repository includes an executable, local-first Evidence Core for the
TraceContract UC19 vertical slice. It demonstrates versioned artifacts, typed
trace edges, independent evidence and review, accountable approval,
deterministic certification, freshness/reverification, canonical RTM output,
and Migration and Change Context Contracts.

Run the backward-compatible demo:

```powershell
py -m tracecontract demo --output-dir build/tracecontract-demo
```

Run the hash-pinned reproducible workflow:

```powershell
py -m tracecontract run --manifest examples/run-manifest.json --output-dir build/tracecontract-run
```

The pinned command writes:

- `certified-rtm.json` — deterministic certified graph projection
- `migration-context.json` — certified task context for the migration agent
- `evidence-state.json` — full lifecycle and append-only audit state
- `run-manifest.json` — canonical pinned inputs and configuration
- `bundle-manifest.json` — hashes for every immutable workflow output
- `report.json` — conservative H1–H4 status; unmeasured hypotheses remain `not_evaluated`

Run all tests:

```powershell
py -m unittest discover -s tests -v
```

The package also exposes deterministic Markdown/text/JSON normalization, a
provider-neutral code-observation adapter contract, isolated and blinded
experiment processes, trace metrics, ACL-first retrieval, allowlisted
inference-context assembly, structured independent review verdicts, and
Migration/Change Context Contract compilation.

## Agent workflow

Project-scoped Codex configuration lives under `.codex/` and defines five
specialized agents: Candidate Linker, Forward Reviewer, Reverse Reviewer,
Adversarial Reviewer, and Experiment Evaluator. Invoke `$tracecontract-run` to
orchestrate the matching skills under `.agents/skills/tracecontract-*`.

The orchestrator uses Codebase Memory MCP for graph discovery and coverage,
imports and freezes a candidate batch, dispatches three blind reviewer
contexts, imports their `tracecontract.review-batch.v1` artifacts atomically,
then imports a pinned accountable approval batch before deterministic
certification. The Python workflow supports precomputed
`reviewed-certification`, reviewer-only `agent-reviewed-certification`, and
end-to-end `agent-orchestrated-certification`, which executes the Candidate
Linker followed by the three reviewers through the fresh-process `AgentRunner`
boundary.

Codebase Memory payloads enter through `normalize_codebase_memory_result`.
That adapter records the MCP project/generation, exact raw-result hash,
pagination completeness, source spans, and partial/unknown coverage without
reading provider-private storage.

The implementation target is in
[`.scratch/tracecontract-validated-mvp/spec.md`](.scratch/tracecontract-validated-mvp/spec.md).
The bundled UC19 data remains a mechanism fixture; it is not experimental
evidence for migration effectiveness or general applicability.
