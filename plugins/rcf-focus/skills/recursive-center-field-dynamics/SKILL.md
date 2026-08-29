---
name: recursive-center-field-dynamics
description: "Use when the user explicitly invokes `$recursive-center-field-dynamics`, `$focus`, `Use Focus`, `用Focus`, `focus一下`, or command-like `fous`. Maintain a live recursive center-field while the task proceeds: select one current center, drive the necessary frontier, revise obsolete closure when evidence changes, preserve versions, and fold or unwind with evidence. Do not trigger for ordinary discussion that merely uses the word focus."
---

# Constructive Recursive Field Focus

Current semantic binding: Focus Skill v0.18 with runtime schema `focus-constructive-2.0`.

## Quick start

For `Use Focus: <task>`, perform the task through the live loop `FORM → DRIVE → REVISE → FOLD`. The parent model retains execution authority; Focus supplies structural decisions that must affect what the parent does next.

Do not add a Focus-only preamble, approval gate, or confirmation pause. Ask the user only when the parent task itself needs clarification, new authority, an irreversible choice, or a materially different scope.

## Operating identity

Treat the LLM's ordinary task work as the parent field. Focus participates inside that work as a structural observation, navigation, revision, and inheritance layer without becoming an authorization gate.

Focus must do more than label a finished answer. During a material task it must produce at least one of these effects:

- select or revise the current center;
- choose the next necessary frontier;
- prevent an illegal or premature action;
- invalidate obsolete closure after a new difference;
- preserve a version branch instead of forcing a false merge;
- fold a child result or unwind to an ancestor that can decide differently.

If no structural difference or decision exists, return `NOOP`. Never manufacture addresses or symbols to make the invocation look useful.

## Core loop

### 1. FORM — recover enough field to act

Before the first significant action, recover the task contract from the request and available evidence:

- goal, boundary, completion condition, evidence standard, and constraints;
- current closure gap;
- the complete set of materially irreducible candidate centers;
- one selected center for the current local projection;
- necessary order, joins, peer interfaces, invalidation triggers, and frontiers.

Do not seek exhaustive knowledge before acting. Form only enough structure to identify one legal next step. A complete field may contain multiple peer centers, but one local Focus projection selects exactly one center.

For tool-capable work, initialize task-local state with `focus_runtime.py init --mode constructive`, then call `frame`. Read [constructive-loop.md](references/constructive-loop.md) when forming payloads or choosing between modes.

### 2. DRIVE — return one next decision

Use the current contract, selected center, ready action frontier, and required expansion frontier to return exactly one next state:

```text
CONTINUE
EXPAND_REQUIRED
REVISE_LOCAL
REOPEN_INTERFACE
REFRAME_FIELD
SPLIT_BRANCH
UNWIND
BLOCKED
NOOP
```

The parent task must consume this decision. Use `execute` only for a ready address with evidence. Use `expand` when a required position needs a child field. Use `decide` when the model must record a deliberate choice that is not already derived by `frame` or `assess-impact`.

An address is justified only when it performs navigation, constraint, evidence, memory, or reopen/audit work. Tool calls, paragraphs, and decorative categories are not automatically addresses.

### 3. REVISE — let new differences change the structure

Treat any new source, failed test, counterexample, user correction, changed constraint, or changed goal as a possible field delta.

1. Preserve it without reinterpretation using `ingest-delta`.
2. Classify it as `ADD`, `REFINE`, `CONTRADICT`, `OUTSIDE`, or `NOOP`.
3. Locate the nearest affected legal addresses.
4. Use `assess-impact` to derive the minimum propagation scope and next decision.
5. If it invalidates a necessary predecessor or compressed interface, withdraw dependent `[+]`, invalidate the old closure certificate, block affected actions, and reopen only the minimum required upper scope.
6. Preserve old closure versions as history. When supported descendants are incomparable, use `SPLIT_BRANCH`; never merge them by chronology or weight alone.

Read [knowledge-revision.md](references/knowledge-revision.md) for classification and address motion. Read [closure-and-invalidation.md](references/closure-and-invalidation.md) whenever old conclusions, closed interfaces, or versions may become invalid.

Potential residuals are differences, not addresses. A latent difference receives no modality until activation and legal calibration binds it to an address, creates an address, leaves it active and unaddressed, or externalizes it.

### 4. FOLD — close relatively, preserve reopening

Call `fold` only after required nodes have evidence and required expansions have returned. Separate selected-center closure from complete-field closure. A successful complete-field fold creates an immutable field-closure version and an active closure certificate.

For a child field, call `unwind` after folding. The child realizes its parent address only when the complete child field closed. If evidence gain stalls, addresses repeat, or the child no longer affects the parent, fold what is known and unwind to the nearest ancestor that can choose differently.

Read [field-stack.md](references/field-stack.md) for recursive expansion, stall detection, Fold, and Unwind. Read [state-contract.md](references/state-contract.md) when constructing runtime payloads, validating state, or resuming work.

## Evidence and address invariants

- `[+]` requires observed, cited, implemented, or freshly verified evidence.
- `[◇]` denotes a calibrated legal route, not every conceivable future item.
- `[-]` is a prohibited transition; `[∅]` is a relevant difference with no legal address in the current grammar.
- Necessary order remains acyclic. Support, conflict, competition, aggregation, and shared position do not become precedence automatically.
- One shared functional position keeps one address with multiple center memberships.
- Validation proves recorded structural consistency, not metaphysical or domain truth.
- Never overwrite raw deltas, old address meanings, closure certificates, or field-closure versions.

## Sidecar compatibility

Use `init --mode sidecar → observe → reconstruct → fold` only when importing an already completed external trace, auditing historical work, or resuming a v0.17 sidecar record. It is not the default workflow for a new Focus invocation. Read [sidecar-runtime.md](references/sidecar-runtime.md) only for that compatibility path.

Use [two-stage-runtime.md](references/two-stage-runtime.md), legacy [field_state.py](scripts/field_state.py), [protocol.md](references/protocol.md), and [state-schema.md](references/state-schema.md) only to validate or migrate historical schema-2.2/S0-S3 or v0.17 records.

## Response surface

Lead with the requested result. Append only a compact field return:

```text
Focus 场域返回
当前场：<本轮真正维护的契约>
实际作用：<Focus 改变了哪一个决定；没有则 NOOP>
当前中心／下一步：<一个中心与一个决定>
闭合与版本：<相对闭合、失效、重开或版本分支>
剩余：<仍阻断的差异或可重新打开的位置>
```

Do not expose private chain-of-thought. Report concise decisions, evidence, effects, and unresolved gaps.

If the runtime rejects a transition, keep any valid parent-task result, report the exact invariant failure, and leave the affected field open. Do not invent a repaired state.
