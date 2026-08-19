from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import time
from pathlib import Path
from typing import Any

from .core import PolicyError, _canonical_bytes


def run_experiment(configuration: dict[str, Any], output_root: Path) -> dict[str, Any]:
    """Run blinded arms in fresh processes with a shared declared budget."""
    arms = configuration.get("arms", {})
    if set(arms) != {"baseline", "treatment"}:
        raise PolicyError("experiment requires exactly baseline and treatment arms")
    budget = configuration.get("budget", {})
    if not all(key in budget for key in ("time_seconds", "tool_calls", "tokens")):
        raise PolicyError("experiment budget requires time_seconds, tool_calls, and tokens")
    output_root.mkdir(parents=True, exist_ok=True)
    arm_names = ["baseline", "treatment"]
    random.Random(configuration.get("seed", 0)).shuffle(arm_names)
    labels = {arm_name: label for arm_name, label in zip(arm_names, ("X", "Y"))}
    assignment = {label: arm_name for arm_name, label in labels.items()}
    assignment_bytes = _canonical_bytes(assignment)
    (output_root / "assignment.private.json").write_bytes(assignment_bytes)

    trials: list[dict[str, Any]] = []
    for sequence, arm_name in enumerate(arm_names, 1):
        label = labels[arm_name]
        run_dir = (output_root / f"trial-{sequence}-{label}").resolve()
        run_dir.mkdir()
        command = arms[arm_name].get("command")
        if not isinstance(command, list) or not command:
            raise PolicyError("each experiment arm requires a non-empty command list")
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "TEMP": str(run_dir),
            "TMP": str(run_dir),
            "HOME": str(run_dir),
            "USERPROFILE": str(run_dir),
            "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "NO_PROXY": "",
            "TRACECONTRACT_RUN_LABEL": label,
        }
        started = time.monotonic()
        try:
            completed = subprocess.run(
                [str(part) for part in command], cwd=run_dir, env=environment,
                text=True, capture_output=True, check=False,
                timeout=float(budget["time_seconds"]),
            )
            elapsed = time.monotonic() - started
            output_lines = [line for line in completed.stdout.splitlines() if line.strip()]
            result = json.loads(output_lines[-1]) if output_lines else {}
            protocol_deviations = [] if completed.returncode == 0 else ["arm_process_nonzero_exit"]
            returncode = completed.returncode
        except subprocess.TimeoutExpired as exc:
            elapsed = time.monotonic() - started
            result = {"passed": 0, "total": 0, "failure_category": "environment_failure"}
            protocol_deviations = ["time_budget_exhausted"]
            returncode = 124
            completed = exc
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        trials.append({
            "label": label,
            "sequence": sequence,
            "budget": budget,
            "returncode": returncode,
            "elapsed_seconds": elapsed,
            "result": result,
            "stdout_hash": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
            "stderr_hash": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
            "protocol_deviations": protocol_deviations,
        })
    return {
        "schema": "tracecontract.experiment-result.v1",
        "budget": budget,
        "model": configuration.get("model"),
        "tools": configuration.get("tools", []),
        "assignment_hash": hashlib.sha256(assignment_bytes).hexdigest(),
        "network_control": "proxy-deny; raw socket isolation must be supplied by the configured executor",
        "trials": trials,
    }
