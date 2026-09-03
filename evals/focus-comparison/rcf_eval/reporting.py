"""JSON and Markdown reporting for Focus comparative evaluations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(value: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Focus comparative evaluation report",
        "",
        f"- Runs: {summary['run_count']}",
        f"- Contains synthetic runs: {'yes' if summary['contains_synthetic_runs'] else 'no'}",
        "",
    ]
    if summary["contains_synthetic_runs"]:
        lines.extend(
            [
                "> Synthetic runs validate the protocol, scorer, and reporting path only. They are not performance evidence for Focus.",
                "",
            ]
        )
    minimum_n = min(
        row["metrics"]["drift_rate"]["n"] for row in summary["conditions"].values()
    )
    if minimum_n < 3:
        lines.extend(
            [
                "> Fewer than three samples exist per condition. This report is suitable for smoke calibration only, not a performance conclusion.",
                "",
            ]
        )
    lines.extend(
        [
            "| Condition | Drift rate | Error rate | Rework | Avoidable rework | Necessary rework recall | Closure quality | n |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for condition_id, row in summary["conditions"].items():
        metrics = row["metrics"]
        lines.append(
            "| {condition} | {drift} | {error} | {rework:.2f} | {avoidable:.2f} | {recall} | {closure} | {n} |".format(
                condition=condition_id,
                drift=_percent(metrics["drift_rate"]["mean"]),
                error=_percent(metrics["error_rate"]["mean"]),
                rework=metrics["rework_count"]["mean"],
                avoidable=metrics["avoidable_rework_count"]["mean"],
                recall=_percent(metrics["necessary_rework_recall"]["mean"]),
                closure=_percent(metrics["closure_quality"]["mean"]),
                n=metrics["drift_rate"]["n"],
            )
        )
    lines.extend(
        [
            "",
            "## Resource use",
            "",
            "| Condition | Mean tokens | Mean seconds | Mean tool calls | Token measurement |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for condition_id, row in summary["conditions"].items():
        resources = row["resources"]
        measurements = "; ".join(row["token_measurements"])
        lines.append(
            "| {condition} | {tokens:.0f} | {elapsed:.2f} | {tools:.2f} | {measurement} |".format(
                condition=condition_id,
                tokens=resources["tokens"]["mean"],
                elapsed=resources["elapsed_seconds"]["mean"],
                tools=resources["tool_calls"]["mean"],
                measurement=measurements,
            )
        )
    lines.extend(["", "## Within-memory Focus effect versus ordinary workflow", ""])
    lines.extend(
        [
            "| Information mechanism | Drift delta | Error delta | Rework delta | Avoidable rework delta | Necessary rework recall delta | Closure delta |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for memory, effects in summary["focus_effect_by_memory"].items():
        lines.append(
            "| {memory} | {drift:+.4f} | {error:+.4f} | {rework:+.4f} | {avoidable:+.4f} | {recall:+.4f} | {closure:+.4f} |".format(
                memory=memory,
                drift=effects["drift_rate"],
                error=effects["error_rate"],
                rework=effects["rework_count"],
                avoidable=effects["avoidable_rework_count"],
                recall=effects["necessary_rework_recall"],
                closure=effects["closure_quality"],
            )
        )
    lines.extend(
        [
            "",
            "| Information mechanism | Token delta | Seconds delta | Tool-call delta |",
            "|---|---:|---:|---:|",
        ]
    )
    for memory, effects in summary["focus_effect_by_memory"].items():
        resources = effects["resources"]
        lines.append(
            "| {memory} | {tokens:+.0f} | {elapsed:+.2f} | {tools:+.2f} |".format(
                memory=memory,
                tokens=resources["tokens"],
                elapsed=resources["elapsed_seconds"],
                tools=resources["tool_calls"],
            )
        )
    lines.extend(
        [
            "",
            "Lower drift, error, and avoidable rework are better; higher necessary-rework recall and closure quality are better. Total rework is descriptive and must be interpreted by necessity. Deterministic error scoring checks structural support and does not detect every semantic misunderstanding in natural language. Interpret tokens by the recorded measurement method; adapter estimates are not provider-billed tokens. Any formal conclusion also requires 95% intervals, task-stratified results, and raw-trajectory audit.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(summary), encoding="utf-8")
