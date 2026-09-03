# Evaluation

Focus makes an empirical proposal, not a proven performance claim:

> Under equal model, tools, information, and budget, explicit field, center, dependency, evidence, and version state may reduce drift, stale conclusions, illegal jumps, and avoidable rework while improving reopenable closure.

The personal alpha keeps validation in two lightweight layers:

- [submission cases](evals/submission-cases.json) check whether Focus can locate an overloaded situation, derive one governing question, choose a valid next move, maintain a changing task, and avoid unnecessary activation;
- the comparison harness checks long-horizon state maintenance under controlled information conditions.

For the two orientation cases, inspect three observable qualities: whether the field fits the user's actual constraints, whether the governing question can change the current judgment, and whether the next move can obtain the evidence needed to answer it. This release records expected behavior rather than adding a separate judge service or claiming a numerical question-quality score.

## Comparison matrix

The public harness evaluates six conditions on the same long-horizon tasks:

| Workflow | No retrieval | RAG | Knowledge graph |
|---|---|---|---|
| Ordinary | `ordinary-none` | `ordinary-rag` | `ordinary-kg` |
| Focus | `focus-none` | `focus-rag` | `focus-kg` |

This separates a workflow effect from an information-retrieval effect. RAG and knowledge graphs may complement Focus; they are not treated as mutually exclusive products.

## Measures

- `drift_rate`: checkpoints that lose the goal, constraints, valid evidence, or current version;
- `error_rate`: unsupported claims, illegal dependency jumps, and failed checks;
- `rework_count`: repeated or replaced actions;
- `closure_quality`: goal satisfaction, evidence coverage, consistency, explicit residuals, and inheritance quality;
- maintenance cost: tokens, latency, storage, retrieval, and human correction.

## Run the harness

```bash
cd evals/focus-comparison
python run.py validate --suite datasets/pilot_tasks.json
python -m unittest discover -s tests -v
```

The synthetic adapter verifies the experiment and scoring infrastructure:

```bash
python run.py run --suite datasets/pilot_tasks.json --adapter-command "python -m rcf_eval.reference_adapter" --runs runs/synthetic --seeds 1,2,3 --conditions all
python run.py score --suite datasets/pilot_tasks.json --runs runs/synthetic --out reports/synthetic
```

Synthetic results are never performance evidence. The Codex adapter provides an early real-execution smoke path; its lexical RAG and local co-reference graph are transparent baselines, not production retrieval systems.

## Evidence required for a performance claim

Before claiming that Focus performs better:

1. freeze tasks, success criteria, evidence, and budgets before running;
2. use the same base model, tools, material snapshot, and randomization policy;
3. keep Focus maintenance costs inside the shared budget;
4. preserve raw trajectories and score them offline;
5. use blinded evaluation and at least three repetitions;
6. report task-level failures, uncertainty, and error-lock persistence—not only averages.

Current automated tests validate software and scoring invariants. Controlled comparative results are still pending, so superiority remains unproven.
