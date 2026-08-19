from __future__ import annotations

import copy
import hashlib
from typing import Any, Iterable

from .core import PolicyError, _canonical_bytes


CLASSIFICATION_LEVELS = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}


def prepare_retrieval(artifacts: Iterable[dict[str, Any]], subject: str, project_id: str) -> list[dict[str, Any]]:
    authorized: list[dict[str, Any]] = []
    for artifact in artifacts:
        if artifact.get("project_id") != project_id or subject not in artifact.get("acl", []):
            raise PolicyError(f"access denied for artifact {artifact.get('id', '<unknown>')}")
        authorized.append(copy.deepcopy(artifact))
    return authorized


def prepare_inference_context(
    artifacts: Iterable[dict[str, Any]],
    provider: str,
    model: str,
    provider_allowlist: dict[str, str],
    prompt_id: str,
    configuration: dict[str, Any],
) -> dict[str, Any]:
    if provider not in provider_allowlist:
        raise PolicyError("cloud provider is not allowlisted")
    maximum = provider_allowlist[provider]
    if maximum not in CLASSIFICATION_LEVELS:
        raise PolicyError(f"unknown provider classification limit: {maximum}")
    minimized: list[dict[str, Any]] = []
    artifact_ids: list[str] = []
    for artifact in artifacts:
        classification = artifact.get("classification", "restricted")
        if classification not in CLASSIFICATION_LEVELS:
            raise PolicyError(f"unknown artifact classification: {classification}")
        if CLASSIFICATION_LEVELS[classification] > CLASSIFICATION_LEVELS[maximum]:
            raise PolicyError(f"provider policy denies {classification} artifact {artifact.get('id')}")
        artifact_ids.append(artifact["id"])
        minimized.append({"id": artifact["id"], "content": copy.deepcopy(artifact["content"])})
    context_hash = hashlib.sha256(_canonical_bytes(minimized)).hexdigest()
    audit = {
        "provider": provider,
        "model": model,
        "prompt_id": prompt_id,
        "configuration_hash": hashlib.sha256(_canonical_bytes(configuration)).hexdigest(),
        "context_hash": context_hash,
        "artifact_ids": sorted(artifact_ids),
    }
    return {"context": minimized, "audit": audit}
