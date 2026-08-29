# Closure and invalidation

Read this reference before accepting a fold after prior closure, or whenever new evidence can defeat a realized position.

## Closure certificate

A complete-field fold creates:

- an immutable field-closure version;
- a snapshot digest;
- parent-version links;
- an active closure certificate containing its evidence and invalidation triggers.

Closure is relative to the recorded contract, selected-center projection, evidence standard, assumptions, and unresolved residuals. It is never universal finality.

## Failure propagation

For `REFINE` or `CONTRADICT`:

```text
locate nearest affected address
→ invalidate it
→ invalidate every necessary descendant and affected join target
→ withdraw unsupported [+]
→ reopen compressed exposure
→ invalidate active closure certificates
→ mark the old closure version invalidated or superseded by branch
→ refresh legal action frontiers
→ return one revision decision
```

Support, conflict, competition, or chronological succession do not propagate invalidation unless a necessary dependency or interface is recorded.

## Upward propagation

Test the nearest child-to-parent interface first:

1. Did the child payload change?
2. Does it still satisfy the same required function and output?
3. Does the parent order, boundary, tolerance, and closure condition still hold?
4. If yes, stop locally.
5. If not, invalidate the compressed parent address and repeat at the next ancestor.

`interface` opens the nearest failed return. `field` reaches the current root contract. `branch` preserves incomparable descendants from the same source version.

## Reclosure

Do not reactivate an invalidated certificate. After repair, acquire fresh evidence and call `fold`; this creates a new certificate and, when the complete field closes, a new field-closure version linked to its predecessor.

Old versions remain read-only. Never overwrite a contradicted conclusion so that the earlier evidence relationship disappears.
