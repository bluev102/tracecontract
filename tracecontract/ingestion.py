from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .core import _canonical_bytes


SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt", ".json"}


def _artifact(kind: str, parser_version: str, source: Path, heading: str, body: str, start: int, end: int) -> dict[str, Any]:
    content = {
        "heading": heading,
        "text": body.strip(),
        "source": source.name,
        "source_span": {"start_line": start, "end_line": end},
    }
    identity = hashlib.sha256(_canonical_bytes({
        "kind": kind,
        "parser_version": parser_version,
        "content": content,
    })).hexdigest()
    return {"id": f"{kind}:{identity}", "kind": kind, "content": content, "version_hash": identity}


def _markdown_artifacts(path: Path, kind: str, parser_version: str) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    starts = [index for index, line in enumerate(lines) if re.match(r"^#{1,6}\s+\S", line)]
    if not starts and any(line.strip() for line in lines):
        starts = [0]
    artifacts: list[dict[str, Any]] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        heading_line = lines[start].strip()
        heading = re.sub(r"^#{1,6}\s+", "", heading_line) if heading_line.startswith("#") else path.stem
        body_start = start + 1 if heading_line.startswith("#") else start
        artifacts.append(_artifact(kind, parser_version, path, heading, "\n".join(lines[body_start:end]), start + 1, end))
    return artifacts


def _json_artifacts(path: Path, kind: str, parser_version: str) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    records = value if isinstance(value, list) else value.get("artifacts", [value])
    artifacts = []
    for index, record in enumerate(records, 1):
        content = record.get("content", record) if isinstance(record, dict) else {"value": record}
        record_kind = record.get("kind", kind) if isinstance(record, dict) else kind
        identity = hashlib.sha256(_canonical_bytes({
            "kind": record_kind,
            "parser_version": parser_version,
            "content": content,
        })).hexdigest()
        artifacts.append({
            "id": record.get("id", f"{record_kind}:{identity}") if isinstance(record, dict) else f"{record_kind}:{identity}",
            "kind": record_kind,
            "content": content,
            "version_hash": identity,
            "provenance": {"source": path.name, "record": index},
        })
    return artifacts


def normalize_input(path: str | Path, kind: str, parser_version: str) -> dict[str, Any]:
    """Normalize one pinned input through the public ingestion adapter contract."""
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        result = {
            "schema": "tracecontract.normalized-snapshot.v1",
            "parser_version": parser_version,
            "artifacts": [],
            "coverage": {"state": "unsupported", "region": suffix or "unknown"},
        }
    else:
        artifacts = _json_artifacts(source, kind, parser_version) if suffix == ".json" else _markdown_artifacts(source, kind, parser_version)
        result = {
            "schema": "tracecontract.normalized-snapshot.v1",
            "parser_version": parser_version,
            "artifacts": artifacts,
            "coverage": {"state": "complete", "region": source.name},
        }
    result["raw_result_hash"] = hashlib.sha256(_canonical_bytes(result)).hexdigest()
    return result
