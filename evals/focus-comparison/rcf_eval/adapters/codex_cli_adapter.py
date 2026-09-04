"""Run one long-horizon evaluation cell through isolated Codex CLI turns.

This is the first empirical adapter. Every event starts a fresh ephemeral turn,
which makes the supplied memory mechanism observable. The environment derives
a public delta from the hidden oracle but never exposes the full expected state.
"""

from __future__ import annotations

import json
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


STEP_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "state_snapshot",
        "action",
        "claims",
        "rework_of",
        "output",
        "inheritance",
    ],
    "properties": {
        "state_snapshot": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "goal_refs",
                "constraint_refs",
                "version_ref",
                "evidence_refs",
                "completed_refs",
                "residual_refs",
            ],
            "properties": {
                "goal_refs": {"type": "array", "items": {"type": "string"}},
                "constraint_refs": {"type": "array", "items": {"type": "string"}},
                "version_ref": {"type": "string", "minLength": 1},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "completed_refs": {"type": "array", "items": {"type": "string"}},
                "residual_refs": {"type": "array", "items": {"type": "string"}},
            },
        },
        "action": {
            "type": "object",
            "additionalProperties": False,
            "required": ["key", "predecessor_refs"],
            "properties": {
                "key": {"type": "string", "minLength": 1},
                "predecessor_refs": {"type": "array", "items": {"type": "string"}},
            },
        },
        "claims": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "evidence_refs"],
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "evidence_refs": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "rework_of": {"type": "array", "items": {"type": "string"}},
        "output": {"type": "string"},
        "inheritance": {
            "type": "object",
            "additionalProperties": False,
            "required": ["contract_version", "evidence_map", "open_residuals", "reopen_condition"],
            "properties": {
                "contract_version": {"type": "string"},
                "evidence_map": {"type": "string"},
                "open_residuals": {"type": "string"},
                "reopen_condition": {"type": "string"},
            },
        },
    },
}

TOKEN_RE = re.compile(r"[\w:-]+", re.UNICODE)
ADAPTER_VERSION = "0.4"


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(value) if len(token) > 1}


def public_event_delta(task: dict[str, Any], event_index: int) -> dict[str, Any]:
    """Expose only newly introduced refs and invalidations at this checkpoint."""

    event = task["events"][event_index]
    current = event["oracle"]
    previous = task["events"][event_index - 1]["oracle"] if event_index else None

    def newly_added(key: str) -> list[str]:
        old = set(previous[key]) if previous else set()
        return sorted(set(current[key]) - old)

    current_evidence = set(current["valid_evidence_refs"]) | set(current["invalid_evidence_refs"])
    previous_evidence = (
        set(previous["valid_evidence_refs"]) | set(previous["invalid_evidence_refs"])
        if previous
        else set()
    )
    return {
        "event_id": event["id"],
        "completion_ref": f"{task['id']}:event-{event_index + 1}",
        "prompt": event["prompt"],
        "introduced_goal_refs": newly_added("required_goal_refs"),
        "introduced_constraint_refs": newly_added("required_constraint_refs"),
        "introduced_evidence_refs": sorted(current_evidence - previous_evidence),
        "invalidated_evidence_refs": newly_added("invalid_evidence_refs"),
        "introduced_residual_refs": newly_added("required_residual_refs"),
        "version_update": (
            current["current_version"]
            if previous is None or current["current_version"] != previous["current_version"]
            else None
        ),
    }


def lexical_memory(history: list[dict[str, Any]], query: str, *, limit: int = 3) -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    ranked = []
    for index, item in enumerate(history):
        text = json.dumps(item, ensure_ascii=False)
        overlap = len(query_tokens & _tokens(text))
        ranked.append((overlap, index, item))
    ranked.sort(key=lambda row: (row[0], row[1]), reverse=True)
    selected = [item for overlap, _, item in ranked if overlap > 0][:limit]
    if not selected:
        selected = [item for _, _, item in ranked[:limit]]
    return selected


def graph_memory(history: list[dict[str, Any]], current_delta: dict[str, Any], *, limit: int = 24) -> dict[str, Any]:
    graph: dict[str, set[str]] = defaultdict(set)
    labels: dict[str, str] = {}
    for item in history:
        response = item["response"]
        state = response["state_snapshot"]
        refs = (
            state["goal_refs"]
            + state["constraint_refs"]
            + state["evidence_refs"]
            + state["completed_refs"]
            + state["residual_refs"]
            + [state["version_ref"], response["action"]["key"]]
        )
        refs = list(dict.fromkeys(refs))
        for ref in refs:
            labels[ref] = ref
        for left in refs:
            for right in refs:
                if left != right:
                    graph[left].add(right)
    seeds = set(
        current_delta["introduced_goal_refs"]
        + current_delta["introduced_constraint_refs"]
        + current_delta["introduced_evidence_refs"]
        + current_delta["invalidated_evidence_refs"]
        + current_delta["introduced_residual_refs"]
    )
    selected = set(seeds)
    for seed in list(seeds):
        selected.update(graph.get(seed, set()))
    if not selected:
        selected.update(
            node for node, _ in Counter({node: len(edges) for node, edges in graph.items()}).most_common(limit)
        )
    selected = set(sorted(selected)[:limit])
    return {
        "nodes": sorted(selected),
        "edges": [
            [left, right]
            for left in sorted(selected)
            for right in sorted(graph.get(left, set()) & selected)
            if left < right
        ],
    }


def state_ledger(history: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not history:
        return None
    response = history[-1]["response"]
    state = response["state_snapshot"]
    return {
        "current_state": state,
        "action_lineage": [item["response"]["action"] for item in history],
        "rework_lineage": [
            ref for item in history for ref in item["response"].get("rework_of", [])
        ],
        "inheritance": response["inheritance"],
    }


def memory_payload(condition: dict[str, str], history: list[dict[str, Any]], delta: dict[str, Any]):
    payload: dict[str, Any] = {}
    if history:
        payload["recent_window"] = history[-1]
    if condition["memory"] == "rag":
        payload["retrieved_history"] = lexical_memory(history, delta["prompt"])
    elif condition["memory"] == "kg":
        payload["knowledge_graph"] = graph_memory(history, delta)
    if condition["workflow"] in {"focus", "stateful"}:
        payload["state_ledger"] = state_ledger(history)
    return payload


def build_prompt(
    task: dict[str, Any],
    condition: dict[str, str],
    delta: dict[str, Any],
    memory: dict[str, Any],
    focus_protocol: str,
) -> str:
    workflow_rules = {
        "focus": "Apply the supplied Focus protocol and let the live field state determine the next action.",
        "stateful": "Use a conventional stateful workflow. Read the supplied state ledger, preserve current state, and choose a legal next action without applying Focus concepts.",
        "ordinary": "Use an ordinary best-effort workflow without a Focus state machine or persistent state ledger.",
    }
    workflow = workflow_rules[condition["workflow"]]
    protocol = focus_protocol if condition["workflow"] == "focus" else ""
    return f"""You are the subject in a blinded long-horizon evaluation.

Task title: {task['title']}
Task family: {task['family']}
Condition: {condition['id']}
Workflow rule: {workflow}

Never invent a reference identifier. Use only identifiers visible in the current event or supplied memory. Preserve still-active goals, constraints, versions, evidence, completed predecessors, and residuals. A new version replaces the active version while earlier lineage remains historical. An invalidated evidence ref must not support a current claim. The current completion ref may be added to completed_refs after choosing the action.

Current public event delta:
{json.dumps(delta, ensure_ascii=False, indent=2)}

Condition-allowed memory:
{json.dumps(memory, ensure_ascii=False, indent=2)}

Focus protocol (empty for ordinary workflow):
{protocol}

Return the required JSON object. In action.predecessor_refs, cite only completed event refs genuinely needed before this action. In claims, cite currently valid evidence refs. The output field should concisely state the task result for this event. Keep inheritance fields semantically useful; use an explicit value such as 'none currently known' when a field is genuinely empty.
The rework_of array may contain only a prior completion ref or prior action key that this event actually repeats, replaces, or invalidates. Never put a version id, evidence id, goal id, or constraint id in rework_of.
"""


def _find_project_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "plugin" / "skills" / "focus" / "SKILL.md").is_file():
            return candidate
        if (candidate / "AGENTS.md").is_file() and (candidate / "40_能力组件").is_dir():
            return candidate
    raise RuntimeError("cannot locate Focus Field project root")


def _load_focus_protocol(project_root: Path) -> str:
    configured = os.environ.get("RCF_EVAL_FOCUS_SKILL")
    candidates = [
        Path(configured) if configured else None,
        project_root / "plugin" / "skills" / "focus" / "SKILL.md",
        project_root / "40_能力组件" / "skills" / "focus" / "SKILL.md",
    ]
    for path in candidates:
        if path is not None and path.is_file():
            return path.read_text(encoding="utf-8")
    raise RuntimeError("cannot locate the Focus SKILL.md")


def normalize_response(response: dict[str, Any]) -> dict[str, Any]:
    """Remove schema-unsupported duplicates without changing semantic order."""

    state = response["state_snapshot"]
    for key in (
        "goal_refs",
        "constraint_refs",
        "evidence_refs",
        "completed_refs",
        "residual_refs",
    ):
        state[key] = list(dict.fromkeys(state[key]))
    response["action"]["predecessor_refs"] = list(
        dict.fromkeys(response["action"]["predecessor_refs"])
    )
    response["rework_of"] = list(dict.fromkeys(response["rework_of"]))
    for claim in response["claims"]:
        claim["evidence_refs"] = list(dict.fromkeys(claim["evidence_refs"]))
    return response


def _checkpoint_path(request: dict[str, Any]) -> Path | None:
    root = os.getenv("RCF_EVAL_CHECKPOINT_DIR")
    if not root:
        return None
    task = request["task"]
    condition = request["condition"]
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{task['id']}__{condition['id']}__seed-{request['seed']}.json"


def _checkpoint_key(request: dict[str, Any], focus_protocol: str) -> str:
    material = {
        "adapter_version": ADAPTER_VERSION,
        "model": os.getenv("RCF_EVAL_MODEL", "codex-config-default"),
        "request": request,
        "focus_protocol_sha256": hashlib.sha256(focus_protocol.encode("utf-8")).hexdigest(),
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _run_codex(prompt: str, *, schema_path: Path, output_path: Path, workdir: Path) -> tuple[dict[str, Any], float]:
    command = [
        os.getenv("RCF_EVAL_CODEX", "codex"),
        "exec",
        "--ephemeral",
        "--skip-git-repo-check",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(output_path),
        "--color",
        "never",
        "-C",
        str(workdir),
    ]
    model = os.getenv("RCF_EVAL_MODEL")
    if model:
        command.extend(["--model", model])
    command.append("-")
    started = time.monotonic()
    completed = subprocess.run(
        command,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=int(os.getenv("RCF_EVAL_TURN_TIMEOUT", "600")),
        check=False,
    )
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        raise RuntimeError(f"Codex turn failed: {completed.stderr[-2000:]}")
    try:
        response = json.loads(output_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Codex emitted no valid structured response: {completed.stdout[-2000:]}") from exc
    return response, elapsed


def run_request(request: dict[str, Any]) -> dict[str, Any]:
    task = request["task"]
    condition = request["condition"]
    project_root = _find_project_root()
    focus_protocol = _load_focus_protocol(project_root)
    checkpoint_path = _checkpoint_path(request)
    checkpoint_key = _checkpoint_key(request, focus_protocol)
    history: list[dict[str, Any]] = []
    if checkpoint_path and checkpoint_path.is_file():
        cached = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if cached.get("checkpoint_key") == checkpoint_key:
            history = cached.get("history", [])
    steps = []
    total_elapsed = 0.0
    estimated_tokens = 0
    with tempfile.TemporaryDirectory(prefix="rcf-eval-") as directory:
        temp_root = Path(directory)
        schema_path = temp_root / "step-schema.json"
        schema_path.write_text(json.dumps(STEP_SCHEMA, ensure_ascii=False), encoding="utf-8")
        for index, event in enumerate(task["events"]):
            delta = public_event_delta(task, index)
            memory = memory_payload(condition, history, delta)
            if index < len(history) and history[index].get("event") == delta:
                response = normalize_response(history[index]["response"])
            else:
                if index < len(history):
                    history = history[:index]
                prompt = build_prompt(task, condition, delta, memory, focus_protocol)
                output_path = temp_root / f"step-{index + 1}.json"
                response, elapsed = _run_codex(
                    prompt, schema_path=schema_path, output_path=output_path, workdir=temp_root
                )
                response = normalize_response(response)
                total_elapsed += elapsed
                estimated_tokens += (len(prompt) + len(json.dumps(response, ensure_ascii=False))) // 4
            completion_ref = delta["completion_ref"]
            completed_refs = response["state_snapshot"]["completed_refs"]
            if completion_ref not in completed_refs:
                completed_refs.append(completion_ref)
            response["state_snapshot"]["completed_refs"] = sorted(set(completed_refs))
            step = {
                "event_id": event["id"],
                "state_snapshot": response["state_snapshot"],
                "action": response["action"],
                "claims": response["claims"],
                "checks": [],
                "rework_of": response["rework_of"],
                "retrieval_context": [
                    json.dumps(item, ensure_ascii=False)
                    for item in memory.get("retrieved_history", [])
                ],
                "output": response["output"],
            }
            steps.append(step)
            if index < len(history):
                history[index] = {"event": delta, "response": response}
            else:
                history.append({"event": delta, "response": response})
            if checkpoint_path:
                checkpoint_path.write_text(
                    json.dumps(
                        {"checkpoint_key": checkpoint_key, "history": history},
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )

    latest = history[-1]["response"]
    state = latest["state_snapshot"]
    last_oracle = task["events"][-1]["oracle"]
    invalid_used = sorted(set(state["evidence_refs"]) & set(last_oracle["invalid_evidence_refs"]))
    codex_version = subprocess.run(
        [os.getenv("RCF_EVAL_CODEX", "codex"), "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout.strip() or "unknown"
    model = os.getenv("RCF_EVAL_MODEL", "codex-config-default")
    memory_implementation = {
        "none": "one-step recent window",
        "rag": "lexical overlap retrieval over prior public events and outputs; top_k=3",
        "kg": "co-occurrence reference graph over prior structured states; node_limit=24",
    }[condition["memory"]]
    return {
        "schema_version": "focus-eval-run-1.0",
        "run_id": f"codex__{task['id']}__{condition['id']}__seed-{request['seed']}",
        "suite_id": request["suite_id"],
        "contract_version": request["contract_version"],
        "task_id": task["id"],
        "condition": condition,
        "seed": int(request["seed"]),
        "synthetic": False,
        "provenance": {
            "model": "codex-cli",
            "model_version": model,
            "adapter": "rcf-eval-codex-cli",
            "adapter_version": ADAPTER_VERSION,
            "corpus_version": request["contract_version"],
            "budget": {
                "token_limit": int(os.getenv("RCF_EVAL_TOKEN_LIMIT", "200000")),
                "time_limit_seconds": int(os.getenv("RCF_EVAL_RUN_TIMEOUT", "7200")),
                "tool_call_limit": 0,
            },
            "usage": {
                "tokens": estimated_tokens,
                "elapsed_seconds": round(total_elapsed, 3),
                "tool_calls": 0,
            },
            "codex_version": codex_version,
            "token_measurement": "character-based estimate",
            "focus_execution": (
                "canonical skill text plus external live ledger; runtime transitions not invoked"
                if condition["workflow"] == "focus"
                else "not applied"
            ),
            "state_ledger": (
                "external structured ledger supplied"
                if condition["workflow"] in {"focus", "stateful"}
                else "not supplied"
            ),
            "memory_implementation": memory_implementation,
        },
        "steps": steps,
        "final": {
            "goal_refs": state["goal_refs"],
            "completion_refs": state["completed_refs"],
            "evidence_refs": state["evidence_refs"],
            "residual_refs": state["residual_refs"],
            "version_ref": state["version_ref"],
            "invalid_evidence_refs": invalid_used,
            "contradictions": [],
            "inheritance": latest["inheritance"],
        },
    }


def main() -> None:
    request = json.load(sys.stdin)
    json.dump(run_request(request), sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
