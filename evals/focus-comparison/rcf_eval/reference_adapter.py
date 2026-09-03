"""Synthetic reference adapter used only to verify the harness end to end."""

from __future__ import annotations

import json
import sys
from typing import Any


def build_reference_run(request: dict[str, Any]) -> dict[str, Any]:
    task = request["task"]
    condition = request["condition"]
    seed = int(request["seed"])
    steps = []
    all_completed: list[str] = []
    active_evidence: set[str] = set()
    invalid_evidence: set[str] = set()
    for index, event in enumerate(task["events"], start=1):
        oracle = event["oracle"]
        completion_ref = f"{task['id']}:event-{index}"
        all_completed.append(completion_ref)
        all_completed.extend(oracle["required_predecessor_refs"])
        active_evidence.update(oracle["valid_evidence_refs"])
        invalid_evidence.update(oracle["invalid_evidence_refs"])
        active_evidence.difference_update(invalid_evidence)
        evidence = sorted(active_evidence)
        claims = []
        if evidence:
            claims.append({"id": f"claim:{event['id']}", "evidence_refs": [evidence[-1]]})
        steps.append(
            {
                "event_id": event["id"],
                "state_snapshot": {
                    "goal_refs": list(oracle["required_goal_refs"]),
                    "constraint_refs": list(oracle["required_constraint_refs"]),
                    "version_ref": oracle["current_version"],
                    "evidence_refs": evidence,
                    "completed_refs": sorted(set(all_completed)),
                    "residual_refs": list(oracle["required_residual_refs"]),
                },
                "action": {
                    "key": f"act:{event['id']}",
                    "predecessor_refs": list(oracle["required_predecessor_refs"]),
                },
                "claims": claims,
                "checks": [{"id": f"check:{event['id']}", "passed": True}],
                "rework_of": (
                    [f"{task['id']}:event-{index - 1}"]
                    if oracle.get("requires_rework") and index > 1
                    else []
                ),
                "retrieval_context": evidence if condition["memory"] != "none" else [],
                "output": f"Synthetic reference response for {event['id']}",
            }
        )
    closure = task["closure"]
    inheritance = {
        field: f"synthetic:{field}" for field in closure["required_inheritance_fields"]
    }
    return {
        "schema_version": "focus-eval-run-1.0",
        "run_id": f"synthetic__{task['id']}__{condition['id']}__seed-{seed}",
        "suite_id": request["suite_id"],
        "contract_version": request["contract_version"],
        "task_id": task["id"],
        "condition": condition,
        "seed": seed,
        "synthetic": True,
        "provenance": {
            "model": "synthetic-reference",
            "model_version": "1",
            "adapter": "rcf-eval-reference",
            "adapter_version": "1.0",
            "corpus_version": request["contract_version"],
            "budget": {
                "token_limit": 0,
                "time_limit_seconds": 0,
                "tool_call_limit": 0,
            },
            "usage": {"tokens": 0, "elapsed_seconds": 0, "tool_calls": 0},
        },
        "steps": steps,
        "final": {
            "goal_refs": list(closure["required_goal_refs"]),
            "completion_refs": list(closure["required_completion_refs"]),
            "evidence_refs": list(closure["required_evidence_refs"]),
            "residual_refs": list(closure["required_residual_refs"]),
            "version_ref": closure["current_version"],
            "invalid_evidence_refs": [],
            "contradictions": [],
            "inheritance": inheritance,
        },
    }


def main() -> None:
    request = json.load(sys.stdin)
    json.dump(build_reference_run(request), sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
