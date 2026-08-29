# Address-Motion Maintenance Protocol

Use this protocol when the user supplies a correction, new claim, counterexample, replacement example, new evidence, or proposed theory revision to an already persisted field.

Under the v0.17 sidecar semantics, first preserve the parent task's actual update and evidence, then decide whether it binds a calibrated legal address, only an address candidate, or no current address. Do not assign `[◇]` while calibration is pending. Preserve `[-]` and `[∅]` as addressing results, and preserve latent differences independently from frontiers until an activation event routes them.

## 1. Preserve the root and separate three version axes

- Keep `F0` as the stable logical root address and lineage anchor of the current field.
- Allow the contract, center, order, payloads, and closure conditions carried by `F0` to change across field versions.
- Create a distinct root field such as `F0′` only when the constitutive identity of the old field is no longer traceably preserved.
- When an authorized parent task changes the root goal or its acceptance contract, reconstruct a relatively closed `root-rebuild` with an explicit new F0 field version and advance the protected drift baseline to that audited version. If completing the rebuild would require authority or scope not present in the parent task, keep it as a reopen residual and let the parent workflow request that decision; Focus must not create an additional confirmation gate.
- Keep these version axes separate:
  - runtime state revision: every persisted state event;
  - field-closure version: a new relatively closed field produced by address motion;
  - document or presentation revision: wording, layout, citation, or example changes that may not produce a field version.

Never increment a field-closure version merely because time passed or a file changed.

## 2. Ingest before interpretation

Record every raw update without rewriting it. Assign it an intake address such as `F0@U1`. The intake address belongs to the maintenance inbox; it is not evidence that the update already has a legal theory address.

Store:

- raw content;
- source and source reference;
- evidence status;
- intake timestamp;
- pending status.

Do not overwrite an earlier update or silently merge two updates with different evidence or implications.

## 3. Locate the update

Classify the update relative to the current field version:

- `external`: outside the current F0 boundary and not a task-relevant residual;
- `local-replace`: replaces the payload of the same functional address while preserving its role and interfaces;
- `legal-expansion`: enters an existing `[◇]` route or opens a legal child field;
- `principle-conflict`: requests a direct transition prohibited by the current contract or necessary order;
- `no-address-residual`: task-relevant and evidenced, but `[∅]` in the current address grammar or destructive of current closure;
- `subfield-rebuild`: requires reconstruction below a non-root field position;
- `root-rebuild`: reaches `F0` and produces a new version under the same root lineage;
- `version-branch`: produces two or more currently incomparable relatively closed descendants.

Do not classify a reliable external counterexample as `principle-conflict` merely because it contradicts the current theory. A prohibited internal derivation may be `[-]`; an evidenced fact that the field cannot express must remain a residual.

Classification is stage-sensitive. `no-address-residual` records the point at which the current field cannot yet locate an evidenced update; it is not a permanent verdict on the update. That motion must persist at least one auditable residual and cannot claim relative closure. Keep the update `structured` and unresolved after the no-address motion. The same raw update may then acquire a later motion—such as legal expansion, subfield rebuild, root rebuild, or externalization—after the minimum upward audit finds its destination. Allow at most one proposed motion for an update at a time, and preserve every applied motion in order.

## 4. Treat the update as address motion

Use one or more explicit address operations:

- `retain`: keep an address and its functional payload;
- `payload-replace`: keep the node identity and address but increment and preserve the payload revision;
- `expand`: create legal descendant addresses;
- `move`: migrate a function to another address;
- `split`: map one old address to several new addresses;
- `merge`: map several old addresses to one new address;
- `retire`: stop using an old address without reusing it for another meaning;
- `birth`: create an address with no old-version predecessor;
- `externalize`: keep the update outside the theory field;
- `prohibit`: record a prohibited transition without deleting its evidence trail.

Preserve address migration as a relation, not a one-to-one rename. Every non-null source and target address must retain the `F0` root in the same lineage.

## 5. Audit the smallest propagation scope

Start at the nearest affected address. After a local change, test the child-to-parent compressed interface:

```text
payload or child field changed
→ test functional role and parent interface equivalence
→ test parent necessary order, closure end, boundary, and tolerance
→ if preserved, stop at this level
→ if broken, compress the unabsorbed difference as a residual and move one level upward
```

Continue only to the nearest upper position that can absorb the residual, regain relative closure, and preserve its own parent interface. Record the complete ascent path. Do not declare the whole field changed merely because a descendant changed.

Treat a nominally same-address replacement as structural when its role, dependencies, scope, or interface changed. An unchanged label does not prove an unchanged address function.

## 6. Generate a field version only after relative closure

Create a field-closure version only when:

1. the triggering update and residuals are traceable;
2. the relevant address motion is explicit;
3. the affected scope has passed a closure audit;
4. every unresolved remainder remains in the residual ledger;
5. old versions and old address meanings remain read-only;
6. the address migration relation is stored.

A local replacement, rejected conflict, external item, or still-open expansion may change runtime state without creating a new field-closure version.

Allow multiple current field versions when two descendants are supported but incomparable. A `version-branch` starts from at least one explicit source field version, names its minimum rebuild root, creates at least two distinct child branches and relatively closed result versions at that same field address, retains the source version(s) as parents, stores a restorable snapshot reference and SHA-256 digest for every result, and updates each branch head. Do not force a merge by weight or chronology. A later version may inherit both only through explicit parent-version and address-migration relations.

## 7. Required update-resolution record

For every reconciled update, expose:

```text
update id and intake address
raw source and evidence state
source field version(s)
classification
nearest target or related address(es)
motion operator
affected scope
nearest unstable upper position
ascent path
interface-equivalence result
address changes
new or absorbed residuals
closure audit
result field version(s), if any
one next-state decision
```

Reject a resolution that changes `F0` to a different root address inside the same lineage, overwrites an old address meaning, hides a reliable counterexample behind `[-]`, claims a new field version without relative closure, or reports a whole-field rebuild without a traceable ascent from the affected position.
