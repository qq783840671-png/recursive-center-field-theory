# Focus Field

**Know where you are. Ask what matters. Make the next valid move.**

Focus is an executable orientation layer for thought and action. It turns an overloaded, unclear, or changing situation into a current field, a functional position, a governing question, and one valid next move. As evidence changes, it revises that position without silently losing earlier reasoning.

```text
FORM → DRIVE → REVISE → FOLD
locate   act      reopen    return
```

Use it when information has become larger than the decision you need to make, when you do not yet know what to ask, when several directions compete, or when a changing project has lost its structural next step.

## Install

The shortest path is a direct Skill install. Ask Codex:

```text
$skill-installer install https://github.com/qq783840671-png/recursive-center-field-theory/tree/main/plugin/skills/focus
```

Restart Codex or open a new task so the new Skill catalog is loaded.

The repository also contains a one-Skill plugin package for marketplace distribution:

```text
codex plugin marketplace add qq783840671-png/recursive-center-field-theory
```

Open `/plugins`, find **Focus Field**, and install it.

## Try it

```text
Use Focus: I am considering changing jobs, learning a new field, and protecting my income. I have too many directions and do not know what to decide first.
```

Focus locates the decision before trying to solve it:

```text
Focus field return
Field: a career-direction decision under an income floor and learning goal
Effect: formed a workable position from competing directions
Position / governing question: employed learner / which option preserves the income floor while opening a credible learning path?
Center / next move: sustainable transition / compare the three options against those two constraints
Closure / version: field formed; decision remains open
Open residue: actual income floor and time horizon
```

The same structure can frame a research question, locate the center of a project, or maintain a long-running task when evidence invalidates an earlier conclusion:

```text
Use Focus: this research topic is too broad. Locate the field and find the smallest question that can change the conclusion.

Use Focus: finish this release. Keep the acceptance criteria, and reopen only the work affected by new test evidence.
```

For a simple request such as `Use Focus: what is 2 + 2?`, it answers `4` and returns `NOOP`. It does not manufacture a field when none is needed.

## What Focus does

- locates the active task field and its completion contract;
- locates the subject or task's current functional position;
- selects one current center without erasing relevant peer centers;
- derives the governing question from the smallest unresolved difference that can change the center, legal frontier, or closure;
- follows necessary partial order instead of a flat priority list;
- opens detail only where the parent task requires it;
- invalidates dependent conclusions when their support fails;
- preserves closure versions, branches, evidence, and reopen points;
- folds child results back into the parent task.

## Where Focus sits

| Mechanism | Primary question | Typical result |
|---|---|---|
| Prompt framework | How should the request be expressed? | an instruction pattern |
| Workflow | What known steps should run? | a sequence and status |
| RAG | What relevant material can be retrieved? | document fragments |
| Knowledge graph | What entities and relations are connected? | nodes, relations, and paths |
| **Focus** | Where am I in this field, what question matters, and what move is valid now? | position, center, governing question, next move, and reopenable version |

Focus does not discover truth automatically. It does not replace retrieval, knowledge graphs, domain tools, permissions, or the parent model. Its runtime validates recorded structure; domain claims still require domain evidence.

## The theory

[Focus Field Theory](THEORY.md) is the compact English statement of the full system. Its central proposal is that a finite subject can act within unbounded information by constructing a task-relative field, locating a functional center, moving through necessary relations, and revising that location when reality changes.

“Motion is absolute; stability is relative” remains the philosophical orientation. The engineering claim is narrower and falsifiable: explicit field, center, dependency, evidence, and version state may reduce drift, stale conclusions, illegal jumps, and rework under equal budgets.

## Evidence

The current implementation covers field formation, one-next-decision control, typed knowledge deltas, dependency-scoped invalidation, immutable closure versions, branches, and recursive fold/unwind.

Automated tests establish runtime and package invariants. They do **not** establish that Focus outperforms an ordinary workflow, RAG, or a knowledge graph. The reproducible comparison protocol and harness are in [Evaluation](EVALUATION.md).

## Repository

```text
plugin/       the Focus Field plugin and its single Skill
evals/        behavior cases and the comparison harness
tests/        public package and runtime tests
THEORY.md     the complete concise theory
EVALUATION.md claims, metrics, and evidence limits
```

Everything else is release, legal, or contribution infrastructure. Internal conversation records and the larger Chinese research archive are intentionally excluded.

## Status

This is an experimental, source-available alpha. It is not a natural law, a complete ontology, or evidence of universal performance gains.

Version: `0.5.0-alpha.2` · License: [CC BY-NC 4.0](LICENSE)

Contributions should provide a reproducible failure, counterexample, comparison, or narrowly scoped improvement. See [Contributing](CONTRIBUTING.md), [Security](SECURITY.md), and [Legal](LEGAL.md).
