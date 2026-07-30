---
name: recursive-field-addressing
description: "Use only for `$recursive-field-addressing`, Address／动态寻址／地址引擎／把信息地址化, or delegation from another explicitly invoked Skill. Generate field-relative identities and dynamic addresses, but do not execute the external domain task. Do not use for postal, memory, URL, or database addresses."
---

# Address Engine

## Outcome and boundary

Transform identity-poor input into a field-relative structural identity and dynamic address:

```text
raw information or residual
→ need/superior purpose and candidate field contract
→ complete typed graph, necessary partial order, and tested center
→ recursive field motion
→ field-relative identity and address
→ potential or executable structural position
→ residual-driven next field version
```

Address ends at an auditable address graph and executable-address view. It may form a candidate field and run address-generating motion, but it does not perform the external domain action. Focus supplies task priority, penetration policy, and execution; Distill supplies preservation intent and knowledge destination.

Read [references/engine.md](references/engine.md) for the mapping and motion rules. Read [references/schema.md](references/schema.md) and use [scripts/address_engine.py](scripts/address_engine.py) when persisting or exchanging engine state.

## Two entry modes

- **Standalone:** form the candidate field from raw input first: complete typed graph, necessary order, tested center, and residual audit. Resolve material ambiguity before confirmation. Show `FIELD_CONFIRMATION_REQUIRED` only when the stable product and its validated axis exist; confirmation locks that product for address motion.
- **Client:** accept a confirmed field, center/order, motion request, and residual state from Focus, Distill, or another caller. Do not repeat field confirmation unless the supplied field is unstable or contradictory.

## Engine loop

1. `INGEST`: preserve each raw item and source before interpretation; assign an intake identity, not yet a structural address.
2. `FORM`: move forward from need/superior purpose to the candidate contract, complete typed relation graph, validated necessary partial order, and tested minimum-sufficient center. Persist evidence and the audited formation revision. Do not assume a unique center or backfill structure from a desired address.
3. `MAP`: bind an item to a field-relative role only when a typed root path and necessary predecessors exist.
4. `MOVE`: use one Global Expansion and one Focused Penetration as the caller-independent default, or the minimum structural expansion needed to test addressability. Add rounds only for residuals, unresolved frontier, explicit depth, or caller instruction. Write generated addresses back to the panorama.
5. `ABSORB`: use later expansion, compression, rebuild, or ascent to absorb residuals when legal; preserve unsuccessful attempts and history.
6. `REALIZE`: mark an address `[+]` only after its structural prerequisites and required evidence hold. Produce an executable-address view without executing the domain task.
7. `AUDIT`: update `S_t=(M_t,Frontier_t,R_t,χ_t)`, address lineage, and one next decision.

Support `VALIDATE`, `COMPARE`, and `REOPEN` as inspection operations. Treat legacy `CREATE/LOCATE/UPDATE` as aliases for `MAP/MAP/MOVE` when reading older callers.

## Non-negotiable invariants

1. Generate identity from field-relative role and typed relations, not from the token, word, label, embedding similarity, or suffix alone.
2. Keep stable `object_id` separate from changing `address_id`; one object may have several role addresses across fields and versions.
3. Require an F0 root path, necessary predecessors or valid interfaces, boundary compliance, compatible version, and allowed modal state.
4. Preserve the complete relation graph before projecting necessary partial order; keep incomparable branches and explicit joins.
5. Treat Global and Focused motion as address-generating field motion. Address may execute the supplied structural motion; Focus decides task priority and whether to act on the result.
6. Treat suffix length as recursive exposure depth, not importance, causality, execution order, or quality.
7. Keep realized map, legal Frontier, and residual ledger distinct. A legal unexpanded node is not automatically a residual.
8. Use `[+]` realized, `[◇]` legal potential, `[-]` prohibited/conflicting, and `[∅]` current-field no-address. Never force every input into the field.
9. Preserve migrations, retired addresses, compressed interfaces, reopen references, and field versions; never reuse an old address for a new meaning.
10. Let a task-relevant `[∅]` result trigger rebuild or field ascent rather than hiding it behind a fabricated address.
11. A potential address supports provisional closure only when its complete root path is made of valid evidence-bound required edges, it remains in Frontier, and reach is evidence-supported as `next` or bounded `finite-deep`. A hypothesized path or unknown depth remains `[◇,d=?]` and cannot be promoted to a closing or executable address.
12. Give every numeric recursive node `field_opening_status=hypothesized|forming|validated` plus `field_opening_audit`. Hypothesized/forming nodes are `[◇,d=?]` address hypotheses and may remain in Frontier/residuals, but cannot support closure, executable views, or realization. A validated address requires the local contract, typed graph, order, center, recursive structure, residual audit, parent/return interface, evidence, and an inline restorable snapshot whose canonical hash is recomputed. A suffix or digest-shaped string is not proof.

## Compact output

```text
F0/field: <confirmed or candidate field>
Center axis: <A → ... → A′ or multiple candidates>
Motion result: <new identities and dynamic addresses>
Executable-address view: <ready positions or none>
Residuals: <[◇] / [-] / [∅] summary>
Decision: <FIELD_CONFIRMATION_REQUIRED | ADDRESS_READY | EXPAND_REQUIRED |
           REMODEL_REQUIRED | FIELD_ASCENSION_REQUIRED | COMPLETE>
```

Hide the full panorama, root-path graph, motion ledger, and JSON state unless requested.

## Evidence boundary

Treat the engine as an experimental operationalization of recursive center-field theory. The claim that it organizes information better than token, etymological, embedding, taxonomy, or knowledge-graph methods is a hypothesis requiring direct comparison. Do not claim universal addressability, cross-analyst agreement, drift reduction, or token savings without evidence.
