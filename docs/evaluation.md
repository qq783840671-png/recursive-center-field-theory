# Evaluation Protocol

**Artifact:** source-available `v0.1.0-alpha.3` · **Theory:** `v0.5-draft` · **State schema:** `2.2`

This document turns the engineering claims around Focus into falsifiable studies. It does not treat conceptual coherence, a working Skill, GitHub attention, or a single successful demonstration as evidence of performance.

## 1. Claim discipline

The project uses three evidence labels:

- `[D]` is a definition or protocol rule in the current release.
- `[H]` is a working hypothesis that requires controlled evaluation.
- `[O]` is an unresolved question.

The first evaluation program targets three hypotheses:

| ID | Hypothesis | Appropriate evidence |
|---|---|---|
| `H-DRIFT` | Explicit root-goal, dependency, modal-state, evidence, and version anchors may reduce unsupported drift or improve its detectability. | Longitudinal controlled tasks with eventual ground truth and change logs |
| `H-CONTEXT` | Under a fixed resource budget, Focus Context may recover more task-necessary state than recency, summary, or retrieval-only baselines. | Forced-resume and handoff experiments with prerequisite and version probes |
| `H-RL` | When a correct necessary partial order excludes many structurally illegal actions, a Focus legality gate may reduce invalid exploration. | RL experiments against masking and hierarchy baselines, including wrong-structure controls |

No experiment should use success on one hypothesis to establish the others. In particular, improved explanation quality is not automatically improved task accuracy, and reduced action-space size is not automatically better final return.

## 2. Hypothesis-generating anecdote: `40% → 75%`

`[H]` In one internal long-running workflow, an unstructured estimate placed completion near `40%`. After the task was reconstructed as an explicit field with addresses and concrete completed items, the estimate was revised to roughly `75%`, and the revision could be tied to named work units.

This observation is useful only for generating a hypothesis. It is **not** evidence that the second estimate was more accurate because:

- the denominator called “completion” was not fixed in advance;
- no independent ground truth or final outcome was available at the time of revision;
- the intervention changed both representation and the evidence inspected;
- the observation is a single, anonymous workflow with no control;
- a more detailed justification can still rationalize an incorrect estimate.

The defensible inference is therefore limited to: explicit structure made the estimate revision more inspectable. Accuracy, calibration, and causal attribution remain unknown.

## 3. Shared experimental rules

Every comparison should follow these rules.

### 3.1 Freeze the task contract

Before a run, define:

- the root goal and success criteria;
- immutable constraints;
- completion units and, if weighted, the weights before seeing results;
- accepted evidence for each completed unit;
- permitted actions and side effects;
- token, wall-clock, compute, retrieval, and human-maintenance budgets;
- stopping and failure conditions.

If the contract changes, open a new version and score the change separately. Do not let a method improve its apparent completion rate by shrinking the denominator.

### 3.2 Hold the base system constant

Use the same model version, tool access, data snapshot, retrieval corpus, random-seed policy, temperature, maximum context, and total inference budget across conditions. If Focus adds preprocessing or state maintenance, include those costs rather than comparing only generation tokens.

### 3.3 Separate structure extraction from structure use

Measure at least three stages:

1. **Recovery:** Was the field contract, relation graph, partial order, and candidate center reconstructed correctly?
2. **Control:** Given the same correct structure, did the protocol choose legal and useful context or actions?
3. **Outcome:** Did the complete system improve final task quality under the full cost budget?

This prevents a strong hand-authored structure from being mistaken for an automatic modeling result.

### 3.4 Use an adjudicated set of acceptable structures

Center candidates and necessary partial orders are not assumed to have one hidden, uniquely correct annotation. Before scoring structural recovery:

- give at least two independent annotators the same frozen contract and evidence while blinding them to system condition and outcome;
- let annotators return multiple acceptable center candidates and partial orders when the task permits non-unique but functionally equivalent structures;
- define equivalence operationally—for example, by preserving the same immutable constraints, legal/illegal action distinctions, required joins, and closure conditions under the task contract;
- use a third adjudicator for unresolved disagreements and report agreement before and after adjudication;
- construct an oracle condition only from this preregistered adjudicated set, never by editing the structure after seeing a method's outcome;
- score a recovered structure against every accepted equivalent, or report lower and upper bounds when equivalence remains uncertain.

Metrics such as necessary-predecessor omission are uninterpretable unless this annotation and equivalence procedure is stated. Low agreement is itself evidence that automatic center formation is not yet a stable operation for that task family.

### 3.5 Score both benefit and failure locking

An explicit structure can preserve a correct constraint, but it can also stabilize an incorrect center or missing predecessor. Every study must measure both unsupported drift and persistence of introduced structural errors.

### 3.6 Preserve run artifacts

Archive the contract version, state file, model and retrieval versions, prompts, tool traces, address deltas, evidence, invalidations, residuals, budgets, and evaluator decisions. An evaluation result without these materials is not a reproducible Focus claim.

## 4. Drift and state-estimation study

### 4.1 Tasks

Use long-running tasks with observable intermediate dependencies and an eventual outcome, such as:

- repairing a public software defect;
- reproducing a public computational result;
- updating a versioned technical comparison after new evidence;
- completing a multi-stage data-processing workflow with injected requirement changes.

Each task should last long enough to require multiple context resets or agent handoffs.

### 4.2 Conditions

At minimum compare:

1. recent-window context only;
2. recent window plus free-form running summary;
3. retrieval over the complete trace;
4. the same base retrieval plus Focus state and Focus Context;
5. an oracle-structure condition, used only to separate structure-use quality from automatic structure recovery.

GraphRAG or another graph-memory baseline should be added when the corpus and setup make it a credible baseline. It must receive the same underlying material and budget.

### 4.3 Controlled perturbations

Inject events whose correct treatment is known:

- a new request that is locally relevant but conflicts with an immutable constraint;
- an old, semantically similar result from an obsolete version;
- a proposed action whose necessary predecessor is incomplete;
- two incomparable tasks that can execute in parallel;
- new evidence that invalidates an already-realized predecessor;
- a detail hidden inside a compressed segment that later becomes decision-relevant.

### 4.4 Metrics

Report distributions and uncertainty, not only mean scores.

| Metric | Operational meaning |
|---|---|
| Root-goal retention | Fraction of checkpoints preserving the frozen root goal and acceptance criteria |
| Immutable-constraint violation | Count and severity of proposed or executed violations |
| Necessary-predecessor omission | Required predecessors missing from the recovered state or next-action justification |
| Illegal jump rate | Actions attempted before their required predecessors are satisfied |
| Stale-version use | Decisions supported by evidence invalid for the current version |
| Unsupported estimate revision | Progress, remaining-work, confidence, or delivery changes without a traceable evidence/address delta |
| State-estimation error | Difference between estimated completion and completion computed from preregistered audited units |
| Calibration | Brier score or calibration error for probabilistic completion or success predictions |
| Invalidation propagation recall | Fraction of dependent results correctly reopened after a prerequisite is invalidated |
| Error-lock persistence | Time or number of transitions before an intentionally wrong center/predecessor is detected and repaired |
| Maintenance cost | Added tokens, latency, compute, storage, and human correction time |

The primary outcome should be selected before the experiment. A method should not be declared better because one secondary metric improved while task quality or total cost degraded materially.

## 5. Focus Context resume study

### 5.1 Public test construction

Extend the [open-source defect-repair example](../examples/open-source-defect-repair/README.md) into approximately 20–30 interactions. The trace should include:

- current and obsolete evidence that use similar vocabulary;
- incomplete predecessors;
- legal but currently irrelevant branches;
- incomparable branches;
- a compressed subfield with a later reopen trigger;
- evidence that invalidates an earlier result;
- at least one true residual and one ordinary unexpanded frontier item.

At fixed checkpoints, clear the working context and give the next agent only the representation allowed by its condition.

### 5.2 Baselines

- most recent context window;
- BM25 over the trace;
- dense retrieval over the trace;
- free-form summary memory;
- GraphRAG when implemented under a comparable corpus and budget;
- the same underlying retriever plus Focus Context.

Focus must not receive privileged source material. Its state-extraction and maintenance tokens count toward the shared budget.

### 5.3 Resume probes

Ask the resumed system to recover:

- root goal and immutable constraints;
- current field and contract version;
- selected center and unresolved alternatives;
- audited realized down-set;
- legal action frontier;
- expansion frontier and compressed interfaces;
- stale or invalidated results;
- reopen address for the compressed subfield;
- true residuals and their address relations;
- the next legal action and its necessary predecessors.

### 5.4 Outcomes

Measure exact or adjudicated recovery accuracy, unsupported additions, illegal next actions, final repair quality, evidence traceability, total context tokens, retrieval calls, preprocessing time, state-maintenance time, and end-to-end latency.

`H-CONTEXT` is supported only if improvements replicate across tasks and remain after the full overhead is counted. It is weakened if a simpler summary or graph representation matches the result at lower cost.

## 6. Reinforcement-learning study

Focus Policy is a proposed explicit structural prior around a learned policy, not a replacement for neural weights.

### 6.1 Suitable environments

Start with environments where necessary prerequisites and illegal combinations are observable, but include conditions where the supplied structure is incomplete or wrong. Useful task families include:

- compositional tasks with prerequisite actions;
- resource-constrained scheduling with partial-order structure;
- multi-stage control tasks with legal action masks;
- multi-agent tasks with explicit joins and incomparable branches.

Avoid using only trivial chains; they do not exercise candidate centers, parallel readiness, invalidation, or residual-driven rebuilding.

### 6.2 Required baselines

1. flat PPO;
2. PPO plus the environment's native invalid-action mask;
3. hierarchical or modular PPO;
4. PPO plus Focus-derived legality and state protocol;
5. Focus with an intentionally perturbed center or predecessor set.

The native-mask and hierarchical baselines are essential. Otherwise a gain caused by action masking or hierarchy could be mislabeled as a contribution of Focus.

### 6.3 Measurements

- sample efficiency and learning curves;
- final return and success rate;
- invalid-action and illegal-jump rate;
- time to convergence under predefined thresholds;
- generalization or transfer to changed tasks;
- recovery after prerequisite invalidation;
- proportion of policy decisions traceable to explicit legal gates;
- structure extraction, inference, memory, and maintenance cost;
- performance loss under wrong or incomplete centers.

### 6.4 Interpretation

`H-RL` receives narrow support if, in environments with a recoverable necessary order, Focus reduces illegal exploration beyond an ordinary mask or hierarchy while preserving or improving final return under comparable total cost. A result in one task family does not establish a general RL architecture advantage.

If the wrong-structure control sharply degrades performance or blocks necessary exploration, that is a central limitation, not a secondary implementation issue.

## 7. Component ablations

To test the proposed *combination* rather than a branded package, remove one component at a time:

- no explicit field contract;
- inferred F0 without the explicit user-confirmation checkpoint;
- one fixed center instead of candidate centers;
- general relation graph without the necessary partial-order projection;
- no distinction among action, expansion, and compressed frontiers;
- equal-depth expansion only, without Focus;
- Focus only, without Global Expansion;
- lossy summary instead of a reopenable compression contract;
- no modal address states;
- no Execute/Audit evidence gate;
- no invalidation propagation;
- no residual-to-address relation or absorption history;
- no versioned drift audit.
- eager loading of the full protocol and schema versus progressive loading;
- fixed 2+2 motion for every task versus the standard profile plus the decision-invariance light stop.

Pairwise combinations with HTN, workflow execution, GraphRAG, and ordinary action masks are also important. If a simpler combination reproduces the result, the claim should be narrowed accordingly.

## 8. Reporting template

Every public result should state:

```text
hypothesis tested:
task and frozen contract:
model, retriever, tools, and versions:
comparison conditions:
resource budget and full overhead:
structure source: manual / automatic / hybrid
primary outcome and preregistered threshold:
secondary outcomes:
failure-lock and wrong-structure results:
number of tasks, runs, and seeds:
uncertainty or confidence interval:
artifacts and state traces:
supported claim:
unsupported broader claims:
```

## 9. Current limitations and stop conditions

- There is no completed controlled benchmark in this release.
- The public example tests protocol behavior, not comparative task performance.
- Center existence, uniqueness, and analyst agreement have not been established.
- Automatic relation and center recovery may dominate total error.
- The state schema makes assumptions inspectable; it does not make them true.
- Explicit structure adds computation, storage, and maintenance cost.
- Tasks with weak stable dependencies may receive little benefit.
- Cyclic or feedback-dominant systems may require a representation beyond the current necessary partial-order projection.
- A result should remain `[H]` if the benchmark, artifacts, or total-cost comparison cannot be independently inspected.

The evaluation program should stop short of a performance claim whenever the task contract drifts without versioning, the comparison budget is unequal, the baseline is materially weaker than the relevant established method, or the measured outcome does not distinguish explanation quality from actual correctness.
