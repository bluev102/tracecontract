from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import CertificationError, PolicyError, TraceContract
from .workflow import run_workflow


def _default_fixture() -> Path:
    return Path(__file__).resolve().parent.parent / "examples" / "uc19.json"


def run_demo(fixture_path: Path, output_dir: Path) -> dict[str, object]:
    fixture = TraceContract.load_fixture(fixture_path)
    graph = TraceContract.from_fixture(fixture)
    for edge in fixture["edges"]:
        graph.approve(edge["id"], edge["required_role"], edge["approver"])

    rtm = graph.canonical_rtm_bytes()
    context = graph.context_contract_bytes(
        fixture["migration_unit"], fixture.get("constraints", ()), fixture.get("unknowns", ()),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "certified-rtm.json").write_bytes(rtm)
    (output_dir / "migration-context.json").write_bytes(context)
    (output_dir / "evidence-state.json").write_bytes(graph.state_bytes())
    return {
        "status": "certified",
        "project_id": graph.project_id,
        "artifacts": len(graph.artifacts),
        "verified_edges": len(graph.edges),
        "output_dir": str(output_dir.resolve()),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tracecontract", description="TraceContract executable MVP")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="run the complete UC19 certification workflow")
    demo.add_argument("--fixture", type=Path, default=_default_fixture())
    demo.add_argument("--output-dir", type=Path, default=Path("build/tracecontract-demo"))
    run = subparsers.add_parser("run", help="run a pinned TraceContract workflow manifest")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "demo":
            print(json.dumps(run_demo(args.fixture, args.output_dir), ensure_ascii=False, sort_keys=True))
            return 0
        if args.command == "run":
            manifest_path = args.manifest.resolve()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            print(json.dumps(
                run_workflow(manifest, manifest_path.parent, args.output_dir),
                ensure_ascii=False,
                sort_keys=True,
            ))
            return 0
    except (OSError, KeyError, json.JSONDecodeError, PolicyError, CertificationError) as exc:
        code = "input_invalid" if args.command == "run" else "workflow_failed"
        print(json.dumps({"status": "failed", "code": code, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 10 if args.command == "run" else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
