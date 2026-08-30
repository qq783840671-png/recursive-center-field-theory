# Distill merge and audit contract

Read this reference for persisted, compacted, disputed, or high-risk knowledge merges.

## Responsibility split

The model extracts durable candidates, chooses the canonical destination, compares meaning, and performs the minimum file edit. `distill_ledger.py` validates the declared plan and preserves an audit trail. It does not infer semantic equivalence, verify domain truth, or rewrite Markdown.

## Candidate plan

Each candidate requires:

- `candidate_id`: immutable intake identity;
- `semantic_key`: stable identity for the idea within the selected destination;
- `title` and `statement`;
- `classification`: `ADD | REFINE | REPLACE | CONTRADICT | NOOP`;
- `status`: `用户明确 | 已验证 | 工作假设 | 模型推断 | 待确认 | 已替代 | 已否定`;
- `source_kind`: `user-explicit | verified-artifact | model-inference | conversation-summary`;
- non-empty `basis`;
- `target_id` for every non-`ADD` comparison;
- optional `relations` and `open_edge`.

`conversation-summary` and `model-inference` sources cannot be promoted to `用户明确` or `已验证`. `ADD` creates a new semantic route and therefore has no `target_id`; all other classifications must identify the canonical item they compare against.

## Finalization

After the model edits and rereads the destination, finalize the ledger with:

- `destination_hash_before` and `destination_hash_after`;
- `applied_candidate_ids`;
- `deferred_candidate_ids` and a reason when work remains open;
- changed `section_refs` and audit `evidence`.

Every candidate except `NOOP` must be applied or explicitly deferred. Finalization records what happened; it does not prove that the semantic comparison was correct.

## Commands

```bash
python scripts/distill_ledger.py init STATE --destination PATH --source-scope DESCRIPTION
python scripts/distill_ledger.py apply STATE --payload @plan.json
python scripts/distill_ledger.py finalize STATE --payload @audit.json
python scripts/distill_ledger.py validate STATE
python scripts/distill_ledger.py summary STATE
python scripts/distill_ledger.py self-test
```

