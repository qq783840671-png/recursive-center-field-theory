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


def _delta(effects: dict[str, Any], metric: str) -> float:
    return float(effects["metrics"][metric]["mean_delta"])


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
    ordinary_effects = summary["focus_effect_by_memory"]
    if ordinary_effects:
        lines.extend(["", "## Within-memory Focus effect versus ordinary workflow", ""])
        lines.extend(
            [
                "| Information mechanism | Drift delta | Error delta | Rework delta | Avoidable rework delta | Necessary rework recall delta | Closure delta | Paired n |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for memory, effects in ordinary_effects.items():
            lines.append(
                "| {memory} | {drift:+.4f} | {error:+.4f} | {rework:+.4f} | {avoidable:+.4f} | {recall:+.4f} | {closure:+.4f} | {paired_n} |".format(
                    memory=memory,
                    drift=_delta(effects, "drift_rate"),
                    error=_delta(effects, "error_rate"),
                    rework=_delta(effects, "rework_count"),
                    avoidable=_delta(effects, "avoidable_rework_count"),
                    recall=_delta(effects, "necessary_rework_recall"),
                    closure=_delta(effects, "closure_quality"),
                    paired_n=effects["paired_n"],
                )
            )
        lines.extend(
            [
                "",
                "| Information mechanism | Token delta | Seconds delta | Tool-call delta |",
                "|---|---:|---:|---:|",
            ]
        )
        for memory, effects in ordinary_effects.items():
            resources = effects["resources"]
            lines.append(
                "| {memory} | {tokens:+.0f} | {elapsed:+.2f} | {tools:+.2f} |".format(
                    memory=memory,
                    tokens=resources["tokens"]["mean_delta"],
                    elapsed=resources["elapsed_seconds"]["mean_delta"],
                    tools=resources["tool_calls"]["mean_delta"],
                )
            )
    stateful_effects = summary.get("focus_effect_vs_stateful_by_memory", {})
    if stateful_effects:
        lines.extend(
            [
                "",
                "## Focus effect versus equal-ledger stateful workflow",
                "",
                "| Information mechanism | Drift delta | Error delta | Avoidable rework delta | Necessary rework recall delta | Closure delta | Paired n |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for memory, effects in stateful_effects.items():
            lines.append(
                "| {memory} | {drift:+.4f} | {error:+.4f} | {avoidable:+.4f} | {recall:+.4f} | {closure:+.4f} | {paired_n} |".format(
                    memory=memory,
                    drift=_delta(effects, "drift_rate"),
                    error=_delta(effects, "error_rate"),
                    avoidable=_delta(effects, "avoidable_rework_count"),
                    recall=_delta(effects, "necessary_rework_recall"),
                    closure=_delta(effects, "closure_quality"),
                    paired_n=effects["paired_n"],
                )
            )
        lines.extend(
            [
                "",
                "| Information mechanism | Token delta | Seconds delta | Tool-call delta |",
                "|---|---:|---:|---:|",
            ]
        )
        for memory, effects in stateful_effects.items():
            resources = effects["resources"]
            lines.append(
                "| {memory} | {tokens:+.0f} | {elapsed:+.2f} | {tools:+.2f} |".format(
                    memory=memory,
                    tokens=resources["tokens"]["mean_delta"],
                    elapsed=resources["elapsed_seconds"]["mean_delta"],
                    tools=resources["tool_calls"]["mean_delta"],
                )
            )
    capabilities = summary.get("capabilities", {})
    if capabilities:
        lines.extend(
            [
                "",
                "## Function-matched comparison map",
                "",
                "| Focus capability | Traditional counterpart | GitHub reference | Evidence layer | Current status |",
                "|---|---|---|---|---|",
            ]
        )
        for capability_id, result in capabilities.items():
            definition = result["definition"]
            references = ", ".join(
                f"[project]({url})" for url in definition["github_references"]
            ) or "none"
            lines.append(
                f"| `{capability_id}` | {definition['traditional_baseline']} (`{definition['baseline_workflow']}`) | {references} | "
                f"{definition['evaluation_layer']} | {result['status']} |"
            )
        lines.extend(
            [
                "",
                "## Capability-level paired effects",
                "",
                "| Capability | Memory-matched pair | Drift delta | Error delta | Avoidable rework delta | Necessary rework recall delta | Closure delta | Paired n |",
                "|---|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for capability_id, result in capabilities.items():
            for memory, effects in result["focus_effect_by_memory"].items():
                lines.append(
                    "| `{capability}` | {memory} | {drift:+.4f} | {error:+.4f} | {avoidable:+.4f} | {recall:+.4f} | {closure:+.4f} | {paired_n} |".format(
                        capability=capability_id,
                        memory=f"{effects['baseline_workflow']}→focus / {memory}",
                        drift=_delta(effects, "drift_rate"),
                        error=_delta(effects, "error_rate"),
                        avoidable=_delta(effects, "avoidable_rework_count"),
                        recall=_delta(effects, "necessary_rework_recall"),
                        closure=_delta(effects, "closure_quality"),
                        paired_n=effects["paired_n"],
                    )
                )
        lines.extend(
            [
                "",
                "Capability rows are task profiles of the complete Focus workflow. They become component-causal evidence only after the named Focus component is independently ablated while all other inputs remain fixed.",
            ]
        )
    lines.extend(
        [
            "",
            "Lower drift, error, and avoidable rework are better; higher necessary-rework recall and closure quality are better. Deltas are Focus minus the named baseline workflow for the same task and seed. Total rework is descriptive and must be interpreted by necessity. Rework necessity is annotated per event, so multi-event revision chains require raw-trajectory or human review before an avoidable-rework label is treated as semantic failure. Deterministic error scoring checks structural support and does not detect every semantic misunderstanding in natural language. Interpret tokens by the recorded measurement method; adapter estimates are not provider-billed tokens. Any formal conclusion also requires 95% intervals, task-stratified results, and raw-trajectory audit.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(summary), encoding="utf-8")
