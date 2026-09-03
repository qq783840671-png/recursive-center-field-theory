# Focus comparison harness

This harness compares two workflow mechanisms and three information mechanisms:

| Condition | Workflow | Information access |
|---|---|---|
| `ordinary-none` | ordinary agent workflow | recent context only |
| `ordinary-rag` | ordinary agent workflow | lightweight retrieval |
| `ordinary-kg` | ordinary agent workflow | lightweight graph retrieval |
| `focus-none` | Focus | recent context only |
| `focus-rag` | Focus | lightweight retrieval |
| `focus-kg` | Focus | lightweight graph retrieval |

The factorial design separates the effect of Focus from the effect of retrieval. See [EVALUATION.md](../../EVALUATION.md) for the claim boundary and experimental requirements.

The pilot event prompts are intentionally Chinese while the harness and report surface are English. This preserves the original long-horizon task set and exercises cross-language state retention; task IDs and oracle references remain language-neutral.

## What it measures

- `drift_rate`: events with a lost goal, lost constraint, stale version, or invalid evidence.
- `error_rate`: unsupported claims, illegal predecessor actions, and failed checks per opportunity.
- `rework_count`: distinct declared or detected repeated actions.
- `avoidable_rework_count`: rework not required by the oracle.
- `necessary_rework_recall`: required rework that was actually performed.
- `closure_quality`: mean of goal satisfaction, evidence coverage, consistency, explicit residue, and inheritance quality.

Deterministic scoring does not infer every semantic misunderstanding from natural language. Add preregistered semantic assertions, blinded judges, or human audit for that layer. Cost, run failure, deterministic metrics, and judge metrics must remain separate.

## Validate the protocol

```powershell
python run.py validate --suite datasets/pilot_tasks.json
python -m unittest discover -s tests -v
```

## Run the synthetic reference matrix

```powershell
python run.py run `
  --suite datasets/pilot_tasks.json `
  --adapter-command "python -m rcf_eval.reference_adapter" `
  --runs runs/synthetic `
  --seeds 1,2,3 `
  --conditions all

python run.py score `
  --suite datasets/pilot_tasks.json `
  --runs runs/synthetic `
  --out reports/synthetic
```

Synthetic results validate the harness only. They are not evidence that Focus outperforms an ordinary workflow, RAG, or a knowledge graph.

## Run the Codex CLI adapter

The included adapter can perform a one-task, six-condition smoke run:

```powershell
$env:RCF_EVAL_TASK_IDS = "theory-revision"
$env:RCF_EVAL_CODEX_MODEL = "gpt-5.6-luna"
$env:RCF_EVAL_CHECKPOINT_DIR = "runs/checkpoints"
python run.py run `
  --suite datasets/pilot_tasks.json `
  --adapter-command "python -m rcf_eval.adapters.codex_cli_adapter" `
  --runs runs/codex-smoke `
  --seeds 17 `
  --conditions all
python run.py score `
  --suite datasets/pilot_tasks.json `
  --runs runs/codex-smoke `
  --out reports/codex-smoke
```

Here, `none` supplies only recent context, `rag` performs auditable lexical top-3 retrieval over prior public events and outputs, and `kg` traverses a local graph derived from reference co-occurrence. These are calibration baselines, not production vector RAG or GraphRAG systems.

## Connect another executor

An adapter reads one `focus-eval-adapter-request-1.0` JSON object from standard input and writes one `focus-eval-run-1.0` object to standard output. Each captured run must record the actual model, adapter, corpus version, budget, and usage. Keep those controls equal across conditions or disclose the difference.

Optional Inspect AI and DeepEval bridges are available under `rcf_eval/bridges/`. Install their dependencies in an isolated environment from `requirements-optional.txt`; the core validator and deterministic scorer require no third-party packages.

## Before making a performance claim

Use equal models, tools, snapshots, budgets, and seed policy; hide the oracle from the executor; preserve raw trajectories; score offline; calibrate at least two independent annotators; repeat each condition at least three times; and count all Focus, retrieval, and judging cost.
