from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Iterable

from .core import PolicyError, _canonical_bytes


def normalize_codebase_memory_result(raw_result: bytes, request: dict[str, Any]) -> dict[str, Any]:
    """Adapt a supported Codebase Memory MCP/export result without private-store access."""
    try:
        provider_result = json.loads(raw_result.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PolicyError("Codebase Memory result must be one UTF-8 JSON document") from exc
    if provider_result.get("schema") != "tracecontract.code-provider-result.v1":
        raise PolicyError(f"unsupported code provider result schema: {provider_result.get('schema')}")
    for field in ("repository", "commit", "project", "generation", "provider_version", "adapter_configuration"):
        if field not in request:
            raise PolicyError(f"code observation request requires {field}")
    if provider_result.get("project") != request["project"]:
        raise PolicyError("Codebase Memory project mismatch")
    if provider_result.get("generation") != request["generation"]:
        raise PolicyError("Codebase Memory generation mismatch")
    coverage = provider_result.get("coverage", {})
    if coverage.get("state") not in {"complete", "partial", "unknown"}:
        raise PolicyError(f"unsupported Codebase Memory coverage state: {coverage.get('state')}")
    if not provider_result.get("pagination_complete") and coverage["state"] == "complete":
        raise PolicyError("Codebase Memory pagination is incomplete; coverage cannot be complete")
    facts = provider_result.get("facts")
    if not isinstance(facts, list):
        raise PolicyError("Codebase Memory result requires facts")
    seen: dict[str, str] = {}
    for fact in facts:
        symbol = fact.get("qualified_symbol")
        symbol_hash = fact.get("normalized_symbol_hash")
        if symbol in seen and seen[symbol] != symbol_hash:
            raise PolicyError(f"conflicting Codebase Memory facts for {symbol}")
        seen[symbol] = symbol_hash
        span = fact.get("source_span", {})
        if not all(isinstance(span.get(key), int) for key in ("start_line", "end_line", "loc")):
            raise PolicyError(f"Codebase Memory fact requires an integer source span: {symbol}")
        if span["start_line"] < 1 or span["end_line"] < span["start_line"] or span["loc"] != span["end_line"] - span["start_line"] + 1:
            raise PolicyError(f"invalid Codebase Memory source span: {symbol}")
    normalized = normalize_code_facts(
        request["repository"], request["commit"], "codebase-memory-mcp",
        request["provider_version"], request["adapter_configuration"], facts,
        1.0 if coverage["state"] == "complete" else 0.0,
    )
    normalized["project"] = request["project"]
    normalized["generation"] = request["generation"]
    normalized["coverage"] = copy.deepcopy(coverage)
    normalized["pagination_complete"] = bool(provider_result.get("pagination_complete"))
    normalized["raw_result_hash"] = hashlib.sha256(raw_result).hexdigest()
    return normalized


def normalize_code_facts(
    repository: str,
    commit: str,
    provider: str,
    provider_version: str,
    adapter_configuration: dict[str, Any],
    facts: Iterable[dict[str, Any]],
    indexed_fraction: float,
) -> dict[str, Any]:
    """Normalize supported provider output without depending on private storage."""
    if not 0.0 <= indexed_fraction <= 1.0:
        raise PolicyError("indexed_fraction must be between 0 and 1")
    configuration_hash = hashlib.sha256(_canonical_bytes(adapter_configuration)).hexdigest()
    normalized: list[dict[str, Any]] = []
    for fact in facts:
        for required in ("qualified_symbol", "normalized_symbol_hash", "source_span"):
            if not fact.get(required):
                raise PolicyError(f"code observation requires {required}")
        identity_material = {
            "repository": repository,
            "commit": commit,
            "provider": provider,
            "provider_version": provider_version,
            "adapter_configuration_hash": configuration_hash,
            "qualified_symbol": fact["qualified_symbol"],
            "normalized_symbol_hash": fact["normalized_symbol_hash"],
        }
        normalized.append({
            "id": f"code_symbol:{hashlib.sha256(_canonical_bytes(identity_material)).hexdigest()}",
            **identity_material,
            "source_span": copy.deepcopy(fact["source_span"]),
            "relationships": sorted(copy.deepcopy(fact.get("relationships", [])), key=lambda item: _canonical_bytes(item)),
        })
    result = {
        "schema": "tracecontract.code-observations.v1",
        "repository": repository,
        "commit": commit,
        "provider": {"name": provider, "version": provider_version},
        "adapter_configuration_hash": configuration_hash,
        "coverage": {
            "state": "complete" if indexed_fraction == 1.0 else "partial",
            "indexed_fraction": indexed_fraction,
        },
        "facts": sorted(normalized, key=lambda item: item["id"]),
    }
    result["raw_result_hash"] = hashlib.sha256(_canonical_bytes(result)).hexdigest()
    return result
