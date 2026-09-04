# Constructive loop

Read this reference when a new Focus invocation needs a live field, or when the next decision is unclear.

## Runtime chain

```text
init --mode constructive
→ frame
→ decide when an explicit model choice is needed
→ expand or execute
→ ingest-delta whenever a material difference appears
→ assess-impact
→ revise, reopen, reframe, split, unwind, or continue
→ fold
→ unwind for a child field
→ validate / summary
```

`frame` is FORM, the returned `active_decision` is DRIVE, `ingest-delta → assess-impact` is REVISE, and `fold → unwind` is FOLD.

## FORM payload

```json
{
  "field_id": "task-field",
  "contract": {
    "goal": "what must become true",
    "boundary": "what is in and out",
    "completion": "observable completion condition",
    "evidence_standard": "what evidence is sufficient",
    "constraints": []
  },
  "orientation": {
    "functional_position": "the subject or task's current binding in this field",
    "governing_question": "the one question whose answer can change the judgment",
    "evidence_needed": ["the evidence needed to answer it"],
    "reopen_triggers": ["a change that makes this position or question stale"]
  },
  "closure_gap": "the difference currently blocking completion",
  "centers": [
    {
      "center_id": "current-center",
      "status": "active",
      "closure_status": "open",
      "obligation": "the center's indispensable function",
      "nodes": [
        {
          "node_id": "necessary-step",
          "role": "functional role",
          "required_for_closure": true,
          "frontier_class": "none"
        }
      ]
    }
  ],
  "selected_center_id": "current-center",
  "peer_center_ids": [],
  "order": [],
  "center_relations": [],
  "join_rules": [],
  "projection_assumptions": [],
  "invalidation_triggers": []
}
```

Include `orientation` when the task is unclear, overloaded, or decision-bearing. It is optional for compatibility with earlier machine states, but when present the runtime keeps it in field identity, summaries, Focus return, and closure versions.

Use `frontier_class=expansion_required` only when the position cannot be legally realized without opening a child field. Use `expansion_latent` for a legal but currently unnecessary expansion. Neither class names a residual.

## DRIVE discipline

Return one decision, not a menu. `frame` deterministically prefers a required expansion, then a ready action, then `BLOCKED`. Use `decide` to record a different evidence-backed structural decision.

The parent agent consumes the decision by taking the matching action:

- `CONTINUE`: act on a ready address, then `execute` it with evidence;
- `EXPAND_REQUIRED`: open the target with `expand`;
- `REVISE_LOCAL`: replace or repair the nearest affected payload or relation;
- `REOPEN_INTERFACE`: reopen the failed compressed interface and its necessary dependents;
- `REFRAME_FIELD`: form a new contract/center projection because the current field cannot absorb the delta;
- `SPLIT_BRANCH`: preserve incomparable descendants;
- `UNWIND`: return to the nearest ancestor that can decide differently;
- `BLOCKED`: expose the actual evidence, authority, or structural gap;
- `NOOP`: continue the parent result without inventing field motion.

## When not to persist a field

For a simple, one-step request with no meaningful dependency, conflict, version, or recursion, perform the parent task and return `NOOP`. Do not create runtime state solely to produce a field note.
