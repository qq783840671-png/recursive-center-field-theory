# Knowledge revision

Read this reference when a new source, failure, counterexample, correction, changed constraint, or changed goal enters an active field.

## Intake before interpretation

Use `ingest-delta` to preserve raw content, source, evidence, and kind. Intake creates a delta record, not an address. Do not rewrite the source claim or merge it into an earlier delta before impact assessment.

Kinds are `evidence`, `failure`, `correction`, `constraint-change`, and `goal-change`.

## Classification

- `ADD`: supplies new support or a compatible position without breaking an interface;
- `REFINE`: replaces or narrows a payload while preserving enough identity to remain in the current field;
- `CONTRADICT`: defeats a necessary claim, relation, interface, or closure condition;
- `OUTSIDE`: reliable but outside the current field contract;
- `NOOP`: duplicates known material or produces no task-relevant structural difference.

Classify relative to the current version. A later reframe may change an earlier `OUTSIDE` result, but the old assessment remains auditable.

## Propagation scope

- `none`: no address is affected;
- `local`: the nearest payload or relation can absorb the delta;
- `interface`: a compressed child-to-parent return or its dependents must reopen;
- `field`: the current contract or selected-center projection must be formed again;
- `branch`: two or more supported descendants are currently incomparable.

Use the smallest scope that can absorb the difference and regain relative closure. Do not declare whole-field change merely because a descendant changed.

## Address motion after assessment

Represent an actual repair using the existing maintenance vocabulary:

`retain`, `payload-replace`, `expand`, `move`, `split`, `merge`, `retire`, `birth`, `externalize`, or `prohibit`.

An unchanged name does not prove unchanged function. Preserve old address meanings and store migration as a relation. Reliable external evidence that the grammar cannot locate is `[∅]`, not a prohibited `[-]` transition.

## Version rule

Intake and assessment change runtime revision. They do not by themselves create a field-closure version. A new field-closure version is created only after the affected scope regains relative closure through `fold`.

Document wording or citation changes belong to the document revision axis unless they also change field structure.
