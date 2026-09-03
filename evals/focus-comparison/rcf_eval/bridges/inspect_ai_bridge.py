"""Inspect AI dataset bridge.

The custom solver remains responsible for executing the event sequence. Each
Inspect sample carries one complete task/condition/seed request in metadata,
so all six experimental cells use the same frozen contract.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

from ..models import CONDITIONS, validate_suite


def _inspect_imports():
    try:
        from inspect_ai.dataset import MemoryDataset, Sample
    except ImportError as exc:
        raise RuntimeError(
            "Inspect AI is not installed; install optional requirements in an isolated environment"
        ) from exc
    return MemoryDataset, Sample


def build_dataset(
    suite: dict[str, Any], *, seeds: Iterable[int] = (1, 2, 3)
):
    """Return an Inspect MemoryDataset spanning task × condition × seed."""

    validate_suite(suite)
    MemoryDataset, Sample = _inspect_imports()
    samples = []
    for task in suite["tasks"]:
        for condition in CONDITIONS:
            for seed in seeds:
                request = {
                    "schema_version": "focus-eval-adapter-request-1.0",
                    "suite_id": suite["suite_id"],
                    "contract_version": suite["contract_version"],
                    "task": task,
                    "condition": condition,
                    "seed": int(seed),
                }
                samples.append(
                    Sample(
                        id=f"{task['id']}__{condition['id']}__seed-{seed}",
                        input=(
                            "Execute every event in metadata.eval_request.task.events in order. "
                            "Return one focus-eval-run-1.0 JSON object as the final answer."
                        ),
                        target=json.dumps(task["closure"], ensure_ascii=False),
                        metadata={"eval_request": request},
                    )
                )
    return MemoryDataset(samples=samples, name=suite["suite_id"])


def build_task(suite: dict[str, Any], *, solver, scorer, seeds: Iterable[int] = (1, 2, 3)):
    """Build an Inspect Task from caller-supplied solver and scorer components."""

    try:
        from inspect_ai import Task
    except ImportError as exc:
        raise RuntimeError(
            "Inspect AI is not installed; install optional requirements in an isolated environment"
        ) from exc
    return Task(dataset=build_dataset(suite, seeds=seeds), solver=solver, scorer=scorer)
