"""Schema validation for Focus comparative evaluation artifacts.

The core deliberately uses only the Python standard library. Inspect AI and
DeepEval are optional bridges, so captured runs remain scoreable even when
those packages or a judge-model credential are unavailable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TASK_SCHEMA = "focus-eval-suite-1.0"
RUN_SCHEMA = "focus-eval-run-1.0"

CONDITIONS: tuple[dict[str, str], ...] = (
    {"id": "ordinary-none", "workflow": "ordinary", "memory": "none"},
    {"id": "ordinary-rag", "workflow": "ordinary", "memory": "rag"},
    {"id": "ordinary-kg", "workflow": "ordinary", "memory": "kg"},
    {"id": "focus-none", "workflow": "focus", "memory": "none"},
    {"id": "focus-rag", "workflow": "focus", "memory": "rag"},
    {"id": "focus-kg", "workflow": "focus", "memory": "kg"},
)
CONDITION_BY_ID = {condition["id"]: condition for condition in CONDITIONS}


class EvalDataError(ValueError):
    """Raised when a suite or captured run violates the public schema."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvalDataError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvalDataError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvalDataError(f"top-level JSON must be an object: {path}")
    return value


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvalDataError(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str, *, non_empty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise EvalDataError(f"{label} must be an array")
    if non_empty and not value:
        raise EvalDataError(f"{label} must not be empty")
    return value


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvalDataError(f"{label} must be a non-empty string")
    return value


def _require_string_list(value: Any, label: str) -> list[str]:
    values = _require_list(value, label)
    if any(not isinstance(item, str) or not item for item in values):
        raise EvalDataError(f"{label} must contain only non-empty strings")
    if len(values) != len(set(values)):
        raise EvalDataError(f"{label} must not contain duplicates")
    return values


def validate_suite(suite: dict[str, Any]) -> dict[str, Any]:
    if suite.get("schema_version") != TASK_SCHEMA:
        raise EvalDataError(f"schema_version must be {TASK_SCHEMA!r}")
    _require_string(suite.get("suite_id"), "suite_id")
    _require_string(suite.get("contract_version"), "contract_version")
    tasks = _require_list(suite.get("tasks"), "tasks", non_empty=True)
    task_ids: set[str] = set()
    for task_index, task_value in enumerate(tasks):
        label = f"tasks[{task_index}]"
        task = _require_mapping(task_value, label)
        task_id = _require_string(task.get("id"), f"{label}.id")
        if task_id in task_ids:
            raise EvalDataError(f"duplicate task id: {task_id}")
        task_ids.add(task_id)
        _require_string(task.get("title"), f"{label}.title")
        _require_string(task.get("family"), f"{label}.family")
        events = _require_list(task.get("events"), f"{label}.events", non_empty=True)
        if len(events) < 8:
            raise EvalDataError(f"{label}.events must contain at least 8 long-horizon events")
        event_ids: set[str] = set()
        for event_index, event_value in enumerate(events):
            event_label = f"{label}.events[{event_index}]"
            event = _require_mapping(event_value, event_label)
            event_id = _require_string(event.get("id"), f"{event_label}.id")
            if event_id in event_ids:
                raise EvalDataError(f"duplicate event id in {task_id}: {event_id}")
            event_ids.add(event_id)
            _require_string(event.get("prompt"), f"{event_label}.prompt")
            oracle = _require_mapping(event.get("oracle"), f"{event_label}.oracle")
            for key in (
                "required_goal_refs",
                "required_constraint_refs",
                "valid_evidence_refs",
                "invalid_evidence_refs",
                "required_predecessor_refs",
                "required_residual_refs",
            ):
                _require_string_list(oracle.get(key), f"{event_label}.oracle.{key}")
            _require_string(oracle.get("current_version"), f"{event_label}.oracle.current_version")
            if "requires_rework" in oracle and not isinstance(oracle["requires_rework"], bool):
                raise EvalDataError(f"{event_label}.oracle.requires_rework must be boolean")
        closure = _require_mapping(task.get("closure"), f"{label}.closure")
        for key in (
            "required_goal_refs",
            "required_completion_refs",
            "required_evidence_refs",
            "required_residual_refs",
            "required_inheritance_fields",
        ):
            _require_string_list(closure.get(key), f"{label}.closure.{key}")
        _require_string(closure.get("current_version"), f"{label}.closure.current_version")
    return suite


def validate_run(run: dict[str, Any], suite: dict[str, Any] | None = None) -> dict[str, Any]:
    if run.get("schema_version") != RUN_SCHEMA:
        raise EvalDataError(f"run schema_version must be {RUN_SCHEMA!r}")
    _require_string(run.get("run_id"), "run_id")
    _require_string(run.get("suite_id"), "suite_id")
    _require_string(run.get("contract_version"), "contract_version")
    task_id = _require_string(run.get("task_id"), "task_id")
    condition = _require_mapping(run.get("condition"), "condition")
    condition_id = _require_string(condition.get("id"), "condition.id")
    expected_condition = CONDITION_BY_ID.get(condition_id)
    if expected_condition is None:
        raise EvalDataError(f"unknown condition id: {condition_id}")
    if any(condition.get(key) != expected_condition[key] for key in ("workflow", "memory")):
        raise EvalDataError(f"condition fields do not match canonical condition {condition_id}")
    seed = run.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise EvalDataError("seed must be an integer")
    provenance = _require_mapping(run.get("provenance"), "provenance")
    for key in (
        "model",
        "model_version",
        "adapter",
        "adapter_version",
        "corpus_version",
    ):
        _require_string(provenance.get(key), f"provenance.{key}")
    budget = _require_mapping(provenance.get("budget"), "provenance.budget")
    for key in ("token_limit", "time_limit_seconds", "tool_call_limit"):
        if not isinstance(budget.get(key), int) or isinstance(budget.get(key), bool) or budget[key] < 0:
            raise EvalDataError(f"provenance.budget.{key} must be a non-negative integer")
    usage = _require_mapping(provenance.get("usage"), "provenance.usage")
    for key in ("tokens", "elapsed_seconds", "tool_calls"):
        value = usage.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            raise EvalDataError(f"provenance.usage.{key} must be a non-negative number")
    steps = _require_list(run.get("steps"), "steps", non_empty=True)
    seen_events: set[str] = set()
    for step_index, step_value in enumerate(steps):
        label = f"steps[{step_index}]"
        step = _require_mapping(step_value, label)
        event_id = _require_string(step.get("event_id"), f"{label}.event_id")
        if event_id in seen_events:
            raise EvalDataError(f"duplicate step event_id: {event_id}")
        seen_events.add(event_id)
        state = _require_mapping(step.get("state_snapshot"), f"{label}.state_snapshot")
        for key in (
            "goal_refs",
            "constraint_refs",
            "evidence_refs",
            "completed_refs",
            "residual_refs",
        ):
            _require_string_list(state.get(key), f"{label}.state_snapshot.{key}")
        _require_string(state.get("version_ref"), f"{label}.state_snapshot.version_ref")
        action = _require_mapping(step.get("action"), f"{label}.action")
        _require_string(action.get("key"), f"{label}.action.key")
        _require_string_list(action.get("predecessor_refs"), f"{label}.action.predecessor_refs")
        claims = _require_list(step.get("claims"), f"{label}.claims")
        for claim_index, claim_value in enumerate(claims):
            claim_label = f"{label}.claims[{claim_index}]"
            claim = _require_mapping(claim_value, claim_label)
            _require_string(claim.get("id"), f"{claim_label}.id")
            _require_string_list(claim.get("evidence_refs"), f"{claim_label}.evidence_refs")
        checks = _require_list(step.get("checks"), f"{label}.checks")
        for check_index, check_value in enumerate(checks):
            check_label = f"{label}.checks[{check_index}]"
            check = _require_mapping(check_value, check_label)
            _require_string(check.get("id"), f"{check_label}.id")
            if not isinstance(check.get("passed"), bool):
                raise EvalDataError(f"{check_label}.passed must be boolean")
        _require_string_list(step.get("rework_of"), f"{label}.rework_of")
        if not isinstance(step.get("output"), str):
            raise EvalDataError(f"{label}.output must be a string")
        retrieval_context = step.get("retrieval_context", [])
        _require_string_list(retrieval_context, f"{label}.retrieval_context")
    final = _require_mapping(run.get("final"), "final")
    for key in (
        "goal_refs",
        "completion_refs",
        "evidence_refs",
        "residual_refs",
        "invalid_evidence_refs",
        "contradictions",
    ):
        _require_string_list(final.get(key), f"final.{key}")
    _require_string(final.get("version_ref"), "final.version_ref")
    _require_mapping(final.get("inheritance"), "final.inheritance")

    if suite is not None:
        validate_suite(suite)
        tasks = {task["id"]: task for task in suite["tasks"]}
        if task_id not in tasks:
            raise EvalDataError(f"run references unknown task: {task_id}")
        if run["suite_id"] != suite["suite_id"]:
            raise EvalDataError("run suite_id does not match suite")
        if run["contract_version"] != suite["contract_version"]:
            raise EvalDataError("run contract_version does not match suite")
        expected_events = [event["id"] for event in tasks[task_id]["events"]]
        actual_events = [step["event_id"] for step in steps]
        if actual_events != expected_events:
            raise EvalDataError(
                f"run events must match task order exactly; expected {expected_events}, got {actual_events}"
            )
    return run


def load_suite(path: str | Path) -> dict[str, Any]:
    return validate_suite(_read_json(Path(path)))


def load_run(path: str | Path, suite: dict[str, Any] | None = None) -> dict[str, Any]:
    return validate_run(_read_json(Path(path)), suite=suite)


def task_by_id(suite: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in suite["tasks"]:
        if task["id"] == task_id:
            return task
    raise EvalDataError(f"unknown task id: {task_id}")
