---
name: focus
description: "Use when the user explicitly invokes `$focus`, `Use Focus`, `用Focus`, `focus一下`, or command-like `fous`. Locate an unclear, overloaded, or changing situation: form its field, identify the current position and center, derive the governing question, choose one valid next move, and revise that position when evidence changes. Do not trigger for an ordinary use of the word focus."
---

# Focus

Focus is an orientation layer for thought and action. It helps the parent model answer six questions while doing the actual work:

1. What field am I in?
2. What functional position does the subject or task occupy here?
3. What must remain true, and what is the current center?
4. What governing question can change the current judgment?
5. What is the next necessary move?
6. What must reopen when the evidence changes?

The parent model retains execution authority, tool choice, permissions, and safety duties. Focus changes task structure and navigation; it does not add a second approval gate.

## Decide whether a field is needed

For a simple one-step request with no meaningful dependency, conflict, revision, or recursion, perform the task and return `NOOP`. Do not create state or addresses merely to display the method.

For a material task, run `FORM → DRIVE → REVISE → FOLD` inside the parent work.

## FORM — locate the task

Recover only enough structure to act:

- contract: goal, boundary, completion, evidence, and constraints;
- current position: the subject or task's functional binding under that contract;
- closure gap: what prevents completion now;
- materially irreducible center candidates;
- one selected center for the current projection;
- necessary predecessors, joins, peer interfaces, frontiers, and invalidation triggers.

When the request is vague, overloaded, or begins with “I do not know what to ask,” derive one governing question from the closure gap. It is the smallest unresolved difference whose answer can change the selected center, legal frontier, or closure judgment. Ask the user only when that answer requires their choice or unavailable information; otherwise investigate or act on it inside the parent task. Do not generate a list of generic clarifying questions.

A complete field may have several centers. One Focus projection operates one selected center and keeps only the peer interfaces needed to return safely.

When persistent state is useful, initialize `scripts/focus_runtime.py` in constructive mode and call `frame`. Read [constructive-loop.md](references/constructive-loop.md) for payloads.

## DRIVE — choose one next move

Return exactly one structural decision:

```text
CONTINUE | EXPAND_REQUIRED | REVISE_LOCAL | REOPEN_INTERFACE
REFRAME_FIELD | SPLIT_BRANCH | UNWIND | BLOCKED | NOOP
```

The next parent action must consume that decision. It may ask the governing question, inspect the evidence needed to answer it, or act on an already located route. Do not turn every tool call, paragraph, or possible future idea into an address.

## REVISE — let differences matter

Treat a new source, failed test, counterexample, correction, or changed constraint as a typed delta:

```text
ADD | REFINE | CONTRADICT | OUTSIDE | NOOP
```

Preserve the raw delta, locate the nearest affected position, and reopen only the smallest sound scope. If a necessary predecessor or interface fails, withdraw unsupported realization, invalidate dependent closure, and preserve the old version. Keep incomparable supported outcomes as branches rather than merging them by recency.

Read [knowledge-revision.md](references/knowledge-revision.md) when classifying deltas and [closure-and-invalidation.md](references/closure-and-invalidation.md) when prior closure may fail.

## FOLD — close relatively and remain reopenable

Fold only when required positions have evidence, required child fields have returned, and active residuals fit the contract tolerance. A closure is always bound to a field, scale, version, evidence set, and tolerance.

For a child field, return its conclusion, evidence, assumptions, residuals, and reopen condition to the parent. If deeper work stops changing the parent outcome, fold what is known and `UNWIND` to the nearest ancestor that can decide differently. Read [field-stack.md](references/field-stack.md) for recursive return.

## Invariants

- `[+]` requires observed, cited, implemented, or freshly verified evidence.
- `[◇]` marks a calibrated legal route that is not yet realized.
- A latent residual is a difference record, not an address and not `[◇]`.
- Only strict functional precedence enters the necessary partial order.
- A complex center may contain parallel branches; complexity alone does not make a field multi-center.
- Selected-center closure does not imply complete-field closure.
- Old meanings, evidence, closures, and versions are never silently overwritten.
- Structural validation does not prove domain truth or performance superiority.

Read [state-contract.md](references/state-contract.md) when constructing or debugging runtime state. Historical state import remains compatibility behavior, not the default workflow.

## Return

Lead with the requested result. Then append a compact Focus return in the user's language:

```text
Focus field return
Field: <the contract maintained this turn>
Effect: <the decision Focus changed, or NOOP>
Position / governing question: <current binding and the one question that can change the judgment, or none>
Center / next move: <one center and one decision>
Closure / version: <closed, invalidated, reopened, or branched>
Open residue: <remaining blocker or reopenable position>
```

If the runtime rejects a transition, preserve any valid parent result, report the failed invariant, and leave the field open. Never invent a repaired state.
