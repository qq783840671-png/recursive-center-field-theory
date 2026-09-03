"""Run all evaluation cells through a process adapter.

An adapter receives one JSON request on stdin and must emit exactly one run
object on stdout. This keeps the harness independent from model vendors and
lets Inspect AI, Codex, a RAG service, or a local script own execution.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any, Iterable

from .models import CONDITION_BY_ID, CONDITIONS, validate_run, validate_suite


def split_adapter_command(value: str) -> list[str]:
    """Split a command without damaging Windows backslashes or quoted paths."""

    if os.name != "nt":
        return shlex.split(value)
    parts = shlex.split(value, posix=False)
    return [
        part[1:-1]
        if len(part) >= 2 and part[0] == part[-1] and part[0] in {'"', "'"}
        else part
        for part in parts
    ]


def parse_seeds(value: str) -> list[int]:
    try:
        seeds = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise ValueError("seeds must be comma-separated integers") from exc
    if not seeds:
        raise ValueError("at least one seed is required")
    return seeds


def select_conditions(ids: Iterable[str] | None) -> list[dict[str, str]]:
    if ids is None:
        return [dict(condition) for condition in CONDITIONS]
    result: list[dict[str, str]] = []
    for condition_id in ids:
        condition = CONDITION_BY_ID.get(condition_id)
        if condition is None:
            raise ValueError(f"unknown condition: {condition_id}")
        result.append(dict(condition))
    if not result:
        raise ValueError("at least one condition is required")
    return result


def select_tasks(suite: dict[str, Any], ids: Iterable[str] | None) -> list[dict[str, Any]]:
    if ids is None:
        return list(suite["tasks"])
    wanted = list(ids)
    by_id = {task["id"]: task for task in suite["tasks"]}
    unknown = [task_id for task_id in wanted if task_id not in by_id]
    if unknown:
        raise ValueError(f"unknown tasks: {', '.join(unknown)}")
    if not wanted:
        raise ValueError("at least one task is required")
    return [by_id[task_id] for task_id in wanted]


def run_matrix(
    suite: dict[str, Any],
    *,
    adapter_command: str,
    output_dir: Path,
    seeds: Iterable[int],
    condition_ids: Iterable[str] | None = None,
    task_ids: Iterable[str] | None = None,
    timeout_seconds: int = 1800,
) -> list[Path]:
    validate_suite(suite)
    output_dir.mkdir(parents=True, exist_ok=True)
    command = split_adapter_command(adapter_command)
    if not command:
        raise ValueError("adapter command must not be empty")
    written: list[Path] = []
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    for task in select_tasks(suite, task_ids):
        for condition in select_conditions(condition_ids):
            for seed in seeds:
                request = {
                    "schema_version": "focus-eval-adapter-request-1.0",
                    "suite_id": suite["suite_id"],
                    "contract_version": suite["contract_version"],
                    "task": task,
                    "condition": condition,
                    "seed": seed,
                }
                completed = subprocess.run(
                    command,
                    input=json.dumps(request, ensure_ascii=False),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout_seconds,
                    check=False,
                    env=child_env,
                )
                if completed.returncode != 0:
                    stderr = completed.stderr or completed.stdout or "adapter emitted no diagnostics"
                    raise RuntimeError(
                        f"adapter failed for {task['id']}/{condition['id']}/{seed}: "
                        f"{stderr.strip()}"
                    )
                try:
                    run = json.loads(completed.stdout)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        f"adapter emitted invalid JSON for {task['id']}/{condition['id']}/{seed}"
                    ) from exc
                validate_run(run, suite=suite)
                if run["task_id"] != task["id"] or run["condition"] != condition or run["seed"] != seed:
                    raise RuntimeError("adapter response identity does not match request")
                target = output_dir / f"{task['id']}__{condition['id']}__seed-{seed}.json"
                target.write_text(
                    json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                written.append(target)
    return written
