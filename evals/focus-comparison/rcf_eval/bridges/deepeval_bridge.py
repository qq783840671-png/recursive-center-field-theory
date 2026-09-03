"""DeepEval bridge for supplementary LLM-judge and RAG metrics.

Deterministic protocol scores remain authoritative. DeepEval scores are stored
as a separate layer so judge-model variance cannot silently alter drift,
error, rework, or closure calculations.
"""

from __future__ import annotations

from typing import Any, Iterable

from ..models import task_by_id, validate_run, validate_suite


DEFAULT_METRICS = (
    "KnowledgeRetentionMetric",
    "ConversationCompletenessMetric",
    "TurnRelevancyMetric",
    "TurnFaithfulnessMetric",
)


def _deepeval_imports():
    try:
        import deepeval.metrics as metrics_module
        from deepeval import evaluate
        from deepeval.test_case import ConversationalTestCase, Turn
    except ImportError as exc:
        raise RuntimeError(
            "DeepEval is not installed; install optional requirements in an isolated environment"
        ) from exc
    return metrics_module, evaluate, ConversationalTestCase, Turn


def to_conversational_test_case(suite: dict[str, Any], run: dict[str, Any]):
    validate_suite(suite)
    validate_run(run, suite=suite)
    _, _, ConversationalTestCase, Turn = _deepeval_imports()
    task = task_by_id(suite, run["task_id"])
    event_by_id = {event["id"]: event for event in task["events"]}
    turns = []
    for step in run["steps"]:
        event = event_by_id[step["event_id"]]
        turns.append(Turn(role="user", content=event["prompt"]))
        turns.append(
            Turn(
                role="assistant",
                content=step["output"],
                retrieval_context=step.get("retrieval_context") or None,
            )
        )
    return ConversationalTestCase(
        name=run["run_id"],
        expected_outcome=task["title"],
        turns=turns,
        additional_metadata={
            "task_id": run["task_id"],
            "condition": run["condition"],
            "seed": run["seed"],
        },
    )


def evaluate_run(
    suite: dict[str, Any],
    run: dict[str, Any],
    *,
    metric_names: Iterable[str] = DEFAULT_METRICS,
):
    """Run selected DeepEval metrics and return DeepEval's native result."""

    metrics_module, evaluate, _, _ = _deepeval_imports()
    metrics = []
    for name in metric_names:
        metric_type = getattr(metrics_module, name, None)
        if metric_type is None:
            raise RuntimeError(f"installed DeepEval does not provide metric {name}")
        metrics.append(metric_type())
    return evaluate(
        test_cases=[to_conversational_test_case(suite, run)],
        metrics=metrics,
    )

