from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from .core import PolicyError, _canonical_bytes


DENY_PROXY = "http://127.0.0.1:9"


@dataclass(frozen=True)
class AgentInvocation:
    """A hash-bound assignment for one independently executed agent role."""

    role: str
    input_artifact: Path
    input_hash: str
    expected_output_schema: Mapping[str, Any]
    command: Sequence[str]
    command_identity_hash: str | None = None
    timeout_seconds: float = 60.0
    max_stdout_bytes: int = 1_000_000

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_artifact", Path(self.input_artifact).resolve())
        object.__setattr__(self, "command", tuple(str(part) for part in self.command))
        if not self.role or not self.command:
            raise ValueError("agent invocation requires a role and non-empty command")
        if self.timeout_seconds <= 0 or self.max_stdout_bytes <= 0:
            raise ValueError("agent timeout and stdout limit must be positive")

    @property
    def derived_command_hash(self) -> str:
        return hashlib.sha256(_canonical_bytes(list(self.command))).hexdigest()


@dataclass(frozen=True)
class AgentResult:
    role: str
    output: Any | None
    returncode: int
    elapsed_seconds: float
    input_hash: str
    command_hash: str
    stdout_hash: str
    stderr_hash: str
    stdout_bytes: int
    workdir: str
    protocol_deviations: tuple[str, ...] = ()
    telemetry: Mapping[str, Any] = field(default_factory=dict)

    @property
    def accepted(self) -> bool:
        return self.returncode == 0 and not self.protocol_deviations and self.output is not None


@runtime_checkable
class AgentRunner(Protocol):
    def run(self, invocation: AgentInvocation) -> AgentResult: ...


class SubprocessAgentRunner:
    """Run one assignment in a new process and disposable working directory.

    Proxy variables are set to a deny endpoint. This prevents compliant HTTP
    clients from using the ambient proxy, but is not a raw-socket sandbox; a
    production executor must add OS/container network isolation.
    """

    def __init__(self, work_root: str | Path | None = None) -> None:
        self._work_root = Path(work_root).resolve() if work_root is not None else None
        if self._work_root is not None:
            self._work_root.mkdir(parents=True, exist_ok=True)

    def run(self, invocation: AgentInvocation) -> AgentResult:
        source_bytes = invocation.input_artifact.read_bytes()
        actual_input_hash = hashlib.sha256(source_bytes).hexdigest()
        if actual_input_hash != invocation.input_hash:
            raise PolicyError("agent input artifact hash mismatch")
        command_hash = invocation.derived_command_hash
        if invocation.command_identity_hash not in (None, command_hash):
            raise PolicyError("agent command identity hash mismatch")

        run_dir = Path(tempfile.mkdtemp(prefix="tracecontract-agent-", dir=self._work_root))
        assignment = run_dir / "assignment.json"
        assignment.write_bytes(source_bytes)
        environment = _isolated_environment(run_dir, invocation.role)
        started = time.monotonic()
        stdout = b""
        stderr = b""
        returncode = 125
        deviations: list[str] = []
        try:
            process = subprocess.Popen(
                list(invocation.command),
                cwd=run_dir,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout_buffer = _BoundedBuffer(invocation.max_stdout_bytes)
            stderr_buffer = _BoundedBuffer(invocation.max_stdout_bytes)
            stdout_thread = threading.Thread(target=_drain, args=(process.stdout, stdout_buffer), daemon=True)
            stderr_thread = threading.Thread(target=_drain, args=(process.stderr, stderr_buffer), daemon=True)
            stdout_thread.start()
            stderr_thread.start()
            deadline = started + invocation.timeout_seconds
            while process.poll() is None:
                if stdout_buffer.exceeded:
                    deviations.append("stdout_limit_exceeded")
                    process.kill()
                    break
                if time.monotonic() >= deadline:
                    deviations.append("time_budget_exhausted")
                    process.kill()
                    break
                time.sleep(0.005)
            returncode = process.wait()
            stdout_thread.join()
            stderr_thread.join()
            stdout = stdout_buffer.value
            stderr = stderr_buffer.value
            if stdout_buffer.exceeded and "stdout_limit_exceeded" not in deviations:
                deviations.append("stdout_limit_exceeded")
            if stderr_buffer.exceeded:
                deviations.append("stderr_limit_exceeded")
            if returncode != 0 and not deviations:
                deviations.append("agent_process_nonzero_exit")

            output: Any | None = None
            if "stdout_limit_exceeded" not in deviations:
                output, parse_error = _parse_and_validate(stdout, invocation.expected_output_schema)
                if parse_error:
                    deviations.append(parse_error)
            elapsed = time.monotonic() - started
            return AgentResult(
                role=invocation.role,
                output=output,
                returncode=returncode,
                elapsed_seconds=elapsed,
                input_hash=actual_input_hash,
                command_hash=command_hash,
                stdout_hash=hashlib.sha256(stdout).hexdigest(),
                stderr_hash=hashlib.sha256(stderr).hexdigest(),
                stdout_bytes=len(stdout),
                workdir=str(run_dir),
                protocol_deviations=tuple(deviations),
                telemetry={
                    "fresh_process": True,
                    "input_materialized_as": "assignment.json",
                    "network_control": (
                        "deny proxy variables; raw sockets require OS/container isolation"
                    ),
                },
            )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


class FixtureAgentRunner:
    """Deterministic in-process runner for contract tests and frozen fixtures."""

    def __init__(self, responses: Mapping[str, Any]) -> None:
        self._responses = dict(responses)

    def run(self, invocation: AgentInvocation) -> AgentResult:
        source_hash = hashlib.sha256(invocation.input_artifact.read_bytes()).hexdigest()
        if source_hash != invocation.input_hash:
            raise PolicyError("agent input artifact hash mismatch")
        command_hash = invocation.derived_command_hash
        if invocation.command_identity_hash not in (None, command_hash):
            raise PolicyError("agent command identity hash mismatch")
        output = self._responses.get(invocation.role)
        deviations: tuple[str, ...] = ()
        error = _schema_error(output, invocation.expected_output_schema)
        if error:
            output = None
            deviations = ("output_schema_mismatch",)
        encoded = _canonical_bytes(self._responses.get(invocation.role))
        return AgentResult(
            role=invocation.role,
            output=output,
            returncode=0,
            elapsed_seconds=0.0,
            input_hash=source_hash,
            command_hash=command_hash,
            stdout_hash=hashlib.sha256(encoded).hexdigest(),
            stderr_hash=hashlib.sha256(b"").hexdigest(),
            stdout_bytes=len(encoded),
            workdir="fixture",
            protocol_deviations=deviations,
            telemetry={"fresh_process": False, "fixture": True},
        )


class _BoundedBuffer:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.data = bytearray()
        self.exceeded = False

    @property
    def value(self) -> bytes:
        return bytes(self.data)

    def append(self, chunk: bytes) -> None:
        remaining = self.limit - len(self.data)
        if remaining > 0:
            self.data.extend(chunk[:remaining])
        if len(chunk) > remaining:
            self.exceeded = True


def _drain(pipe: Any, buffer: _BoundedBuffer) -> None:
    try:
        while True:
            chunk = pipe.read(8192)
            if not chunk:
                return
            buffer.append(chunk)
    finally:
        pipe.close()


def _isolated_environment(run_dir: Path, role: str) -> dict[str, str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "WINDIR": os.environ.get("WINDIR", ""),
        "PATHEXT": os.environ.get("PATHEXT", ""),
        "HOME": str(run_dir),
        "USERPROFILE": str(run_dir),
        "TEMP": str(run_dir),
        "TMP": str(run_dir),
        "HTTP_PROXY": DENY_PROXY,
        "HTTPS_PROXY": DENY_PROXY,
        "ALL_PROXY": DENY_PROXY,
        "NO_PROXY": "",
        "TRACECONTRACT_AGENT_ROLE": role,
        "TRACECONTRACT_INPUT_PATH": str(run_dir / "assignment.json"),
    }
    return environment


def _parse_and_validate(payload: bytes, schema: Mapping[str, Any]) -> tuple[Any | None, str | None]:
    try:
        text = payload.decode("utf-8")
        decoder = json.JSONDecoder()
        value, end = decoder.raw_decode(text.lstrip())
        if text.lstrip()[end:].strip():
            return None, "multiple_json_documents"
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "malformed_json_output"
    if _schema_error(value, schema):
        return None, "output_schema_mismatch"
    return value, None


def _schema_error(value: Any, schema: Mapping[str, Any], path: str = "$") -> str | None:
    """Validate the dependency-light JSON Schema subset used by agent contracts."""
    if "const" in schema and value != schema["const"]:
        return f"{path}: const mismatch"
    if "enum" in schema and value not in schema["enum"]:
        return f"{path}: enum mismatch"
    expected_type = schema.get("type")
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "null": type(None),
    }
    if expected_type in type_map:
        expected = type_map[expected_type]
        if not isinstance(value, expected) or expected_type in {"number", "integer"} and isinstance(value, bool):
            return f"{path}: expected {expected_type}"
    if isinstance(value, dict):
        required = schema.get("required", ())
        missing = [key for key in required if key not in value]
        if missing:
            return f"{path}: missing {missing[0]}"
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = set(value) - set(properties)
            if extras:
                return f"{path}: unexpected {sorted(extras)[0]}"
        for key, child_schema in properties.items():
            if key in value:
                error = _schema_error(value[key], child_schema, f"{path}.{key}")
                if error:
                    return error
    if isinstance(value, list) and isinstance(schema.get("items"), Mapping):
        for index, child in enumerate(value):
            error = _schema_error(child, schema["items"], f"{path}[{index}]")
            if error:
                return error
    return None
