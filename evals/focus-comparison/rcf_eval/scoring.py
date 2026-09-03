"""Deterministic scoring for drift, error, rework, and closure quality."""

from __future__ import annotations

import random
import statistics
from collections import defaultdict
from typing import Any, Iterable

from .models import CONDITIONS, task_by_id, validate_run, validate_suite


def _coverage(required: Iterable[str], actual: Iterable[str]) -> float:
    required_set = set(required)
    if not required_set:
        return 1.0
    return len(required_set & set(actual)) / len(required_set)


def score_run(suite: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    validate_suite(suite)
    validate_run(run, suite=suite)
    task = task_by_id(suite, run["task_id"])
    events = {event["id"]: event for event in task["events"]}

    drift_events = 0
    drift_details: list[dict[str, Any]] = []
    error_count = 0
    error_opportunities = 0
    error_details: list[dict[str, Any]] = []
    rework_refs: set[str] = set()
    failed_action_keys: set[str] = set()
    repeated_after_failure: set[str] = set()
    active_evidence: set[str] = set()
    invalid_evidence: set[str] = set()
    prior_rework_targets: set[str] = set()
    necessary_rework_events = 0
    missed_rework_events = 0
    avoidable_rework_refs: set[str] = set()

    for step_index, step in enumerate(run["steps"], start=1):
        oracle = events[step["event_id"]]["oracle"]
        active_evidence.update(oracle["valid_evidence_refs"])
        invalid_evidence.update(oracle["invalid_evidence_refs"])
        active_evidence.difference_update(invalid_evidence)
        state = step["state_snapshot"]
        action_key = step["action"]["key"]
        if action_key in failed_action_keys:
            repeated_after_failure.add(action_key)
        drift_reasons: list[str] = []
        missing_goals = set(oracle["required_goal_refs"]) - set(state["goal_refs"])
        missing_constraints = set(oracle["required_constraint_refs"]) - set(state["constraint_refs"])
        stale_evidence = set(state["evidence_refs"]) & invalid_evidence
        if missing_goals:
            drift_reasons.append(f"missing-goals:{','.join(sorted(missing_goals))}")
        if missing_constraints:
            drift_reasons.append(f"missing-constraints:{','.join(sorted(missing_constraints))}")
        if state["version_ref"] != oracle["current_version"]:
            drift_reasons.append(
                f"stale-version:{state['version_ref']}!={oracle['current_version']}"
            )
        if stale_evidence:
            drift_reasons.append(f"invalid-evidence:{','.join(sorted(stale_evidence))}")
        if drift_reasons:
            drift_events += 1
            drift_details.append({"event_id": step["event_id"], "reasons": drift_reasons})

        valid_evidence = active_evidence
        for claim in step["claims"]:
            error_opportunities += 1
            claim_evidence = set(claim["evidence_refs"])
            if not claim_evidence or not claim_evidence.issubset(valid_evidence):
                error_count += 1
                error_details.append(
                    {
                        "event_id": step["event_id"],
                        "type": "unsupported-claim",
                        "ref": claim["id"],
                    }
                )

        error_opportunities += 1
        required_predecessors = set(oracle["required_predecessor_refs"])
        completed = set(state["completed_refs"])
        declared_predecessors = set(step["action"]["predecessor_refs"])
        if not required_predecessors.issubset(completed) or not required_predecessors.issubset(
            declared_predecessors
        ):
            error_count += 1
            error_details.append(
                {
                    "event_id": step["event_id"],
                    "type": "illegal-action",
                    "ref": step["action"]["key"],
                }
            )

        for check in step["checks"]:
            error_opportunities += 1
            if not check["passed"]:
                error_count += 1
                failed_action_keys.add(action_key)
                error_details.append(
                    {
                        "event_id": step["event_id"],
                        "type": "failed-check",
                        "ref": check["id"],
                    }
                )
        valid_step_rework: set[str] = set()
        for rework_ref in step["rework_of"]:
            error_opportunities += 1
            if rework_ref in prior_rework_targets:
                rework_refs.add(rework_ref)
                valid_step_rework.add(rework_ref)
            else:
                error_count += 1
                error_details.append(
                    {
                        "event_id": step["event_id"],
                        "type": "invalid-rework-ref",
                        "ref": rework_ref,
                    }
                )
        requires_rework = bool(oracle.get("requires_rework", False))
        if requires_rework:
            necessary_rework_events += 1
            error_opportunities += 1
            if not valid_step_rework:
                missed_rework_events += 1
                error_count += 1
                error_details.append(
                    {
                        "event_id": step["event_id"],
                        "type": "missed-required-rework",
                        "ref": step["event_id"],
                    }
                )
        else:
            avoidable_rework_refs.update(valid_step_rework)
        prior_rework_targets.add(action_key)
        prior_rework_targets.add(f"{task['id']}:event-{step_index}")

    final = run["final"]
    closure = task["closure"]
    goal_coverage = _coverage(closure["required_goal_refs"], final["goal_refs"])
    completion_coverage = _coverage(
        closure["required_completion_refs"], final["completion_refs"]
    )
    goal_satisfaction = (goal_coverage + completion_coverage) / 2
    evidence_coverage = _coverage(closure["required_evidence_refs"], final["evidence_refs"])
    consistency = float(
        final["version_ref"] == closure["current_version"]
        and not final["invalid_evidence_refs"]
        and not final["contradictions"]
        and missed_rework_events == 0
    )
    residual_disclosure = _coverage(
        closure["required_residual_refs"], final["residual_refs"]
    )
    inheritance = final["inheritance"]
    inheritance_present = [
        field
        for field in closure["required_inheritance_fields"]
        if field in inheritance and inheritance[field] not in (None, "", [], {})
    ]
    inheritance_quality = _coverage(
        closure["required_inheritance_fields"], inheritance_present
    )
    closure_components = {
        "goal_satisfaction": goal_satisfaction,
        "evidence_coverage": evidence_coverage,
        "consistency": consistency,
        "residual_disclosure": residual_disclosure,
        "inheritance_quality": inheritance_quality,
    }
    closure_quality = statistics.fmean(closure_components.values())
    total_events = len(run["steps"])
    rework_count = len(rework_refs | repeated_after_failure)

    return {
        "run_id": run["run_id"],
        "task_id": run["task_id"],
        "condition": run["condition"],
        "seed": run["seed"],
        "synthetic": bool(run.get("synthetic", False)),
        "resources": {
            "tokens": float(run["provenance"]["usage"]["tokens"]),
            "elapsed_seconds": float(
                run["provenance"]["usage"]["elapsed_seconds"]
            ),
            "tool_calls": float(run["provenance"]["usage"]["tool_calls"]),
            "token_measurement": run["provenance"].get(
                "token_measurement", "provider-reported or adapter-defined"
            ),
        },
        "metrics": {
            "drift_rate": drift_events / total_events,
            "error_rate": error_count / error_opportunities if error_opportunities else 0.0,
            "rework_count": rework_count,
            "avoidable_rework_count": len(avoidable_rework_refs),
            "necessary_rework_recall": (
                (necessary_rework_events - missed_rework_events) / necessary_rework_events
                if necessary_rework_events
                else 1.0
            ),
            "closure_quality": closure_quality,
        },
        "counts": {
            "events": total_events,
            "drift_events": drift_events,
            "error_count": error_count,
            "error_opportunities": error_opportunities,
            "explicit_rework_refs": len(rework_refs),
            "repeated_failed_actions": len(repeated_after_failure),
            "necessary_rework_events": necessary_rework_events,
            "missed_rework_events": missed_rework_events,
            "avoidable_rework_refs": len(avoidable_rework_refs),
        },
        "closure_components": closure_components,
        "details": {"drift": drift_details, "errors": error_details},
    }


def _bootstrap_ci(values: list[float], *, seed: int, samples: int = 2000) -> list[float]:
    if not values:
        return [0.0, 0.0]
    if len(values) == 1:
        return [values[0], values[0]]
    rng = random.Random(seed)
    means = sorted(
        statistics.fmean(rng.choice(values) for _ in values) for _ in range(samples)
    )
    lower = means[int(0.025 * (samples - 1))]
    upper = means[int(0.975 * (samples - 1))]
    return [lower, upper]


def aggregate_scores(scores: list[dict[str, Any]]) -> dict[str, Any]:
    if not scores:
        raise ValueError("at least one score is required")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for score in scores:
        grouped[score["condition"]["id"]].append(score)
    metric_names = (
        "drift_rate",
        "error_rate",
        "rework_count",
        "avoidable_rework_count",
        "necessary_rework_recall",
        "closure_quality",
    )
    condition_rows: dict[str, Any] = {}
    for condition in CONDITIONS:
        condition_scores = grouped.get(condition["id"], [])
        if not condition_scores:
            continue
        metric_summary: dict[str, Any] = {}
        for index, metric_name in enumerate(metric_names):
            values = [float(item["metrics"][metric_name]) for item in condition_scores]
            metric_summary[metric_name] = {
                "mean": statistics.fmean(values),
                "ci95": _bootstrap_ci(values, seed=1701 + index),
                "n": len(values),
            }
        resource_summary: dict[str, Any] = {}
        for index, resource_name in enumerate(
            ("tokens", "elapsed_seconds", "tool_calls")
        ):
            values = [
                float(item["resources"][resource_name]) for item in condition_scores
            ]
            resource_summary[resource_name] = {
                "mean": statistics.fmean(values),
                "ci95": _bootstrap_ci(values, seed=2701 + index),
                "n": len(values),
            }
        token_measurements = sorted(
            {item["resources"]["token_measurement"] for item in condition_scores}
        )
        condition_rows[condition["id"]] = {
            "condition": condition,
            "metrics": metric_summary,
            "resources": resource_summary,
            "token_measurements": token_measurements,
        }

    effects: dict[str, Any] = {}
    for memory in ("none", "rag", "kg"):
        ordinary = condition_rows.get(f"ordinary-{memory}")
        focus = condition_rows.get(f"focus-{memory}")
        if ordinary is None or focus is None:
            continue
        effects[memory] = {
            metric: focus["metrics"][metric]["mean"] - ordinary["metrics"][metric]["mean"]
            for metric in metric_names
        }
        effects[memory]["resources"] = {
            resource: focus["resources"][resource]["mean"]
            - ordinary["resources"][resource]["mean"]
            for resource in ("tokens", "elapsed_seconds", "tool_calls")
        }

    return {
        "schema_version": "focus-eval-summary-1.0",
        "run_count": len(scores),
        "contains_synthetic_runs": any(score.get("synthetic") for score in scores),
        "conditions": condition_rows,
        "focus_effect_by_memory": effects,
        "interpretation": {
            "lower_is_better": ["drift_rate", "error_rate", "avoidable_rework_count"],
            "higher_is_better": ["necessary_rework_recall", "closure_quality"],
            "descriptive": ["rework_count"],
            "warning": "Synthetic runs validate the harness only and are not empirical evidence.",
        },
    }
