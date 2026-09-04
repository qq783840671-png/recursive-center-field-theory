# Constructive state contract

Read this reference when constructing JSON payloads, debugging a rejected transition, resuming state, or writing tests.

## Schema

New states use `focus-constructive-2.0`. Loading `focus-two-stage-1.1` adds the constructive ledgers in memory while preserving old fields, addresses, observations, and history.

The runtime maintains three separate version axes:

- `revision`: every persisted runtime event;
- `field_closure_versions`: immutable relatively closed field states;
- `document_revisions`: optional external presentation revisions.

It also maintains `knowledge_deltas`, `decision_history`, `active_decision`, `version_branches`, `closure_certificates`, and `invalidation_history`.

A field may carry one `orientation` object containing its `functional_position`, `governing_question`, `evidence_needed`, and `reopen_triggers`. The runtime preserves this object in field and closure versions. The model remains responsible for whether the position and question are semantically correct.

## Delta intake

```json
{
  "delta_id": "paper-2026-result",
  "kind": "evidence",
  "raw_content": "the source claim without reinterpretation",
  "source": "paper.pdf#p4",
  "evidence": ["paper.pdf#p4"]
}
```

## Impact assessment

```json
{
  "delta_id": "paper-2026-result",
  "classification": "CONTRADICT",
  "propagation_scope": "interface",
  "affected_addresses": ["premise-node"],
  "reason": "the experiment defeats a necessary predecessor",
  "evidence": ["impact-audit"]
}
```

`affected_addresses` accepts current-field node IDs or canonical address IDs. `NOOP` and `OUTSIDE` require an empty list and `propagation_scope=none`. `CONTRADICT` requires at least one affected address and a non-none scope.

## Explicit decision

```json
{
  "decision": "EXPAND_REQUIRED",
  "target_address": "current-node",
  "reason": "the parent position cannot be realized without a child field",
  "evidence": ["decision-audit"]
}
```

`CONTINUE` targets a ready action frontier. `EXPAND_REQUIRED` targets a required expansion frontier. `UNWIND` requires an open child frame.

## Validation boundary

The runtime validates recorded structure: identities, legal modalities, acyclic necessary order, frontier references, child depth, evidence-bearing closure, invalidation ledgers, and decision vocabulary. The model remains responsible for semantic truth, evidence quality, center recovery, scope selection, and whether centers are genuinely irreducible.
