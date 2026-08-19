# TraceContract agent instructions

The implementation specification is `.scratch/tracecontract-validated-mvp/spec.md`.

Project-scoped Codex agents are defined in `.codex/agents`. TraceContract's
project skills are the six `.agents/skills/tracecontract-*` directories. Keep
candidate discovery, independent review, accountable approval, and
certification as separate trust boundaries.

Use Codebase Memory project `D-workspace-hackathon-tracecontract-mvp` for
structural discovery. Verify the current generation and call
`check_index_coverage` for material paths; read exact source whenever coverage
is stale, partial, skipped, excluded, or unknown.

Run the complete local suite with:

```powershell
py -3 -m unittest discover -s tests -v
```
