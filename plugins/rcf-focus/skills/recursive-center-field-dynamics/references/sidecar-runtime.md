# Focus sidecar runtime

Use this reference when constructing v0.17 post-execution payloads or debugging `observe` and `reconstruct`.

## Runtime chain

```text
parent task executes normally
→ init --mode sidecar
→ observe
→ reconstruct
→ fold when closure auditing is useful
→ validate / summary
```

The sidecar never authorizes or re-executes the parent task. It records a concise evidence trace and reconstructs addresses after the result exists.

## Initialize

```powershell
python scripts/focus_runtime.py init STATE --task "task summary" --mode sidecar
```

## Observe

```json
{
  "raw_request": "the user's original task",
  "events": [
    {
      "event_id": "optional-stable-id",
      "kind": "read",
      "summary": "inspected the relevant configuration",
      "evidence": ["path-or-result-reference"]
    },
    {
      "kind": "write",
      "summary": "updated the configuration",
      "evidence": ["diff-or-artifact-reference"]
    },
    {
      "kind": "result",
      "summary": "validation passed",
      "evidence": ["test-output-reference"]
    }
  ],
  "result": "the parent-facing result",
  "evidence": ["result-level evidence"]
}
```

Allowed event kinds are `analysis`, `read`, `write`, `tool`, `external`, and `result`. Record concise decision or action summaries, not private chain-of-thought. At least one event is required.

## Reconstruct

Use the same contract, center, order, relation, and join structure accepted by historical `frame`, plus trace bindings:

```json
{
  "field_id": "actual-task-field",
  "contract": {
    "goal": "the goal actually pursued",
    "boundary": "what the execution included and excluded",
    "completion": "what counted as complete",
    "evidence_standard": "what evidence supports the result",
    "constraints": []
  },
  "closure_gap": "remaining difference after execution, or the gap that was cleared",
  "centers": [
    {
      "center_id": "actual-main",
      "label": "actual main contribution",
      "status": "active",
      "obligation": "the contribution this center carried",
      "nodes": [
        {"node_id": "inspect", "role": "inspect the current state"},
        {"node_id": "change", "role": "perform the requested change"},
        {"node_id": "verify", "role": "verify the result"}
      ]
    }
  ],
  "selected_center_id": "actual-main",
  "peer_center_ids": [],
  "order": [
    {"before": "inspect", "after": "change"},
    {"before": "change", "after": "verify"}
  ],
  "center_relations": [],
  "join_rules": [],
  "trace_observation_ids": ["obs-id-returned-by-observe"],
  "realized_nodes": ["inspect", "change", "verify"],
  "node_evidence": {
    "inspect": ["read evidence"],
    "change": ["write evidence"],
    "verify": ["test evidence"]
  }
}
```

Every realized node requires non-empty evidence. Unobserved nodes remain unrealized and must not be marked `[+]`. `reconstruct` derives canonical addresses, binds the referenced observations, and returns `FOLD_OR_REPORT`.

## Fold

Use the existing `fold` payload after reconstruction when the response needs an explicit closure audit. Keep latent and active residuals separate. A peer center that remains active and open prevents complete-field closure even when the selected center closes.

## Failure boundary

If `observe`, `reconstruct`, `fold`, or validation fails:

- keep the parent task result;
- report the exact rejected invariant in the Focus field note;
- do not invent an address or claim closure;
- retain the task-local state and payload as a reopen point.

The historical `frame → expand/execute → fold/unwind` path remains available only for old states and deliberate compatibility work.
