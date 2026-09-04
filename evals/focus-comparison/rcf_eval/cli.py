"""Command-line interface for the Focus comparative evaluation harness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import load_run, load_suite
from .reporting import write_json, write_markdown
from .runner import parse_seeds, run_matrix
from .scoring import aggregate_scores, score_run


def _score_directory(suite_path: Path, runs_dir: Path) -> tuple[list[dict], dict]:
    suite = load_suite(suite_path)
    run_paths = sorted(runs_dir.glob("*.json"))
    if not run_paths:
        raise ValueError(f"no run JSON files found in {runs_dir}")
    scores = [score_run(suite, load_run(path, suite=suite)) for path in run_paths]
    return scores, aggregate_scores(scores, suite=suite)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate a task suite and optional runs")
    validate.add_argument("--suite", required=True, type=Path)
    validate.add_argument("--runs", type=Path)

    run = subparsers.add_parser("run", help="execute a task-condition-seed matrix")
    run.add_argument("--suite", required=True, type=Path)
    run.add_argument("--adapter-command", required=True)
    run.add_argument("--runs", required=True, type=Path)
    run.add_argument("--seeds", default="1,2,3")
    run.add_argument("--conditions", default="all")
    run.add_argument("--tasks", default="all")
    run.add_argument("--timeout", type=int, default=1800)

    score = subparsers.add_parser("score", help="score captured runs and produce reports")
    score.add_argument("--suite", required=True, type=Path)
    score.add_argument("--runs", required=True, type=Path)
    score.add_argument("--out", required=True, type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate":
        suite = load_suite(args.suite)
        run_count = 0
        if args.runs:
            for path in sorted(args.runs.glob("*.json")):
                load_run(path, suite=suite)
                run_count += 1
        print(f"validated {len(suite['tasks'])} tasks and {run_count} runs")
        return 0

    if args.command == "run":
        suite = load_suite(args.suite)
        conditions = None if args.conditions == "all" else args.conditions.split(",")
        tasks = None if args.tasks == "all" else args.tasks.split(",")
        paths = run_matrix(
            suite,
            adapter_command=args.adapter_command,
            output_dir=args.runs,
            seeds=parse_seeds(args.seeds),
            condition_ids=conditions,
            task_ids=tasks,
            timeout_seconds=args.timeout,
        )
        print(f"captured {len(paths)} runs in {args.runs}")
        return 0


    if args.command == "score":
        scores, summary = _score_directory(args.suite, args.runs)
        args.out.mkdir(parents=True, exist_ok=True)
        write_json({"schema_version": "focus-eval-scores-1.0", "scores": scores}, args.out / "scores.json")
        write_json(summary, args.out / "summary.json")
        write_markdown(summary, args.out / "report.md")
        print(json.dumps({"runs": len(scores), "out": str(args.out)}, ensure_ascii=False))
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
