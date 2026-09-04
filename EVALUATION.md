# Evaluation

Focus makes an empirical proposal, not a proven performance claim:

> Under equal model, tools, information, and budget, explicit field, center, dependency, evidence, and version state may reduce drift, stale conclusions, illegal jumps, and avoidable rework while improving reopenable closure.

The personal alpha keeps validation in two lightweight layers:

- [submission cases](evals/submission-cases.json) check whether Focus can locate an overloaded situation, derive one governing question, choose a valid next move, maintain a changing task, and avoid unnecessary activation;
- the comparison harness checks long-horizon state maintenance under controlled information conditions.

For the two orientation cases, inspect three observable qualities: whether the field fits the user's actual constraints, whether the governing question can change the current judgment, and whether the next move can obtain the evidence needed to answer it. This release records expected behavior rather than adding a separate judge service or claiming a numerical question-quality score.

## Comparison matrix

The public harness evaluates nine conditions on the same long-horizon tasks:

| Workflow | No retrieval | RAG | Knowledge graph |
|---|---|---|---|
| Ordinary | `ordinary-none` | `ordinary-rag` | `ordinary-kg` |
| Equal-ledger stateful baseline | `stateful-none` | `stateful-rag` | `stateful-kg` |
| Focus | `focus-none` | `focus-rag` | `focus-kg` |

The ordinary row measures the complete bundled effect, including Focus state maintenance. The stateful row receives the same external ledger as Focus and isolates the additional effect of the Focus protocol more closely. This separates workflow effects from information-retrieval effects. RAG and knowledge graphs may complement Focus; they are not treated as mutually exclusive products.

## Function-matched comparison

Focus is a composite Skill, so the aggregate matrix is also stratified by function:

| Focus function | Traditional counterpart | Current evidence route |
|---|---|---|
| field orientation and governing-question derivation | direct prompting, prompt templates, requirements checklists | submission cases plus semantic review |
| center selection and next-frontier choice | planner or state-machine workflow | `multi-file-repair`, `multi-center-merge` |
| necessary partial-order navigation | DAG or directed workflow graph | predecessor errors and rework on repair/merge tasks |
| dynamic retrieval addressing | RAG retriever-selected context | `focus-rag` versus `ordinary-rag` on evidence-heavy tasks |
| relation-aware addressing | knowledge graph or GraphRAG context construction | `focus-kg` versus `ordinary-kg` on relational tasks |
| typed revision and minimal reopening | checkpointed state plus application-specific invalidation rules | revision, evidence, source-conflict, and interface-change tasks |
| versioned handoff and reopenable closure | durable execution, checkpoints, persistent memory | `cross-task-handoff` |
| incomparable branches and contract-gated merge | conditional branches, parallel subgraphs, join nodes | evidence, source-conflict, and multi-center tasks |

The machine-readable map, GitHub project references, primary metrics, and claim boundaries live in `datasets/pilot_tasks.json`. Capability rows are profiles of the full Focus workflow on relevant tasks. A profile becomes evidence for one component only after that component is independently ablated.

## Measures

- `drift_rate`: checkpoints that lose the goal, constraints, valid evidence, or current version;
- `error_rate`: unsupported claims, illegal dependency jumps, and failed checks;
- `rework_count`: repeated or replaced actions;
- `closure_quality`: goal satisfaction, evidence coverage, consistency, explicit residuals, and inheritance quality;
- maintenance cost: tokens, latency, storage, retrieval, and human correction.

## Pre-release calibration: typed revision

On 2026-09-04, the Codex adapter ran one eight-event theory-revision task with three seeds under `ordinary-none`, `stateful-none`, and `focus-none`. All conditions used `gpt-5.6-luna`, the same event stream, no retrieval, no tools, and the same structural scorer.

| Condition | Drift | Structural error | Rework | Avoidable rework | Necessary-rework recall | Closure | Mean estimated tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ordinary | 0.00% | 4.01% | 1.00 | 0.00 | 50.00% | 86.67% | 10,073 |
| Equal-ledger stateful | 0.00% | 4.06% | 1.00 | 0.00 | 50.00% | 80.00% | 13,294 |
| Focus | 0.00% | 3.25% | 1.33 | 0.00 | 66.67% | 86.67% | 25,196 |

This is a narrow calibration, not a benchmark or superiority claim. It gives a small positive signal for typed revision against the equal-ledger baseline, no observed drift advantage, no closure gain over the ordinary workflow, and a substantial protocol cost. The adapter starts an ephemeral model turn for every event and injects the complete Focus Skill each time, so the reported character-based token estimate includes repeated protocol text. More tasks, independent semantic judges, component ablations, and retrieval-matched runs are still required.

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
6. compute effects from matched task-and-seed pairs, then report task-level failures, uncertainty, and error-lock persistence—not only averages;
7. add component ablations before attributing an observed full-workflow effect to one specific Focus function.

Current automated tests validate software and scoring invariants. The calibration above is too small and narrow to establish general performance; superiority remains unproven.
