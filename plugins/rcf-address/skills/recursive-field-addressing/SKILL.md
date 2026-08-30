---
name: recursive-field-addressing
description: "Use only for `$recursive-field-addressing`, Address／动态寻址／地址引擎／把信息地址化, or delegation from another explicitly invoked Skill. Turn identity-poor or changing information into field-relative roles, traceable dynamic addresses, and an auditable executable-address view. Do not execute the external domain task or use for postal, memory, URL, or database addresses."
---

# Address Engine

Current semantic binding: Address Skill v0.6 with persisted-state engine `0.5-experimental`.

## Quick start

Accept `Use Address Engine: map these changing concepts into traceable identities and addresses.` Form/confirm the field in Standalone mode; reuse the caller's valid field in Client mode. Return the address result and one decision, never external task completion.

## Outcome and ownership

Address is a stateful partial mapping:

`raw item/residual → candidate role/address → calibrated legal address or addressing result → frontier/execution → next field version`

Inputs may remain external, prohibited, or no-address. Address ends at an address graph/executable view; it **does not perform the external domain action**. Focus owns execution; Distill owns preservation intent/destination.

## Entry and loading

- **Standalone:** form `contract → typed graph → necessary order → tested center → residual gate`; require `FIELD_CONFIRMATION_REQUIRED` when the intended field affects identity or legality.
- **Client:** reuse the supplied field/order/motion/residual state; reconfirm only if it is missing, stale, unstable, or contradictory.

Read [references/engine.md](references/engine.md) only for disputed identity, complex motion, revision/ascent, or raw audit. Read [references/schema.md](references/schema.md) and use [scripts/address_engine.py](scripts/address_engine.py) only for persisted-state work. A normal Client call loads neither.

The model owns semantic field recovery and evidence judgment. The engine validates recorded identities, candidates, frontiers, residual bindings, address motion, and closure gates; an engine-valid state is structural evidence, not proof that the chosen field or domain claims are true.

## Engine loop

1. **Ingest:** preserve raw item/source under an intake ID, not a structural address.
2. **Form/reuse:** reuse a valid field; otherwise derive `need → contract → G_t → Π_t → tested center → residual audit`. Never backfill from a desired suffix/result.
3. **Map:** bind a role only with a typed root path and required predecessors/interfaces.
4. **Move:** use minimum expansion for simple addressability; otherwise default to one Global plus one Focus. Add motion only for residual/frontier/depth/caller need.
5. **Absorb:** record later expansion, compression, rebuild, or ascent and preserve failed attempts/version history.
6. **Realize/audit:** mark `[+]` only with prerequisites/evidence; return the executable sub-poset and Ready wave, then update typed action/required-expansion/latent-expansion frontiers, compressed interfaces, latent/active residuals, lineage, and one decision.

Support `VALIDATE`, `COMPARE`, and `REOPEN`. Read legacy `CREATE/LOCATE/UPDATE` as aliases for `MAP/MAP/MOVE`.

## Address gate and invariants

Require every address to satisfy:

`confirmed F0 + parent binding/return + typed root path + predecessors/interfaces + boundary/permission + compatible version + allowed modal state`

Then preserve these rules:

- Generate identity from field-relative role/typed relations, never labels, embeddings, popularity, or suffixes alone.
- Keep intake ID, stable `object_id`, and changing `address_id` distinct; one object may have several role addresses.
- Preserve the complete graph before its necessary-order projection, including incomparable branches and joins.
- Let weight, contribution, uncertainty, interaction risk, and cost rank only legal and ready peers; none can create roots, skip predecessors, or certify centers.
- Treat suffix length as exposure depth, not importance, causality, quality, or execution order.
- Preserve migrations, retired addresses, compressed/reopen interfaces, and versions; never reuse an old address for a new meaning.
- Let relevant `[∅]` trigger rebuild/ascent instead of a fabricated address.

Every proposed numeric child first lives in `address_candidates` with `field_opening_status=hypothesized|forming` and no address modality. It cannot support closure, readiness, or realization. Only `validated` openings become legal `[◇]` addresses and require a local contract, graph, order, tested center, parent/return interface, residual audit, evidence, inline restorable snapshot, and recomputed hash. A suffix or digest-shaped string is not proof.

## Motion, residuals, and readiness

- **Global:** expand every eligible required item one uniform level within budget and preserve legal latent items; record deferrals instead of weight-selecting branches.
- **Focus:** open one or more legal paths to unequal depths, prioritizing parent obligations or active residual handling before optional scores; keep unselected legal branches as latent Frontier/interfaces and write generated addresses back to the panorama. Never skip required predecessors.

Keep `A_t^cand`, legal panorama `M_t=A_t^legal`, `ActionFrontier_t`, `ExpansionFrontier_t.required`, `ExpansionFrontier_t.latent`, compressed interfaces, latent residuals `Λ_t`, active residuals `R_t`, and residual-address bindings `χ_t` distinct. Use `[+]` realized and `[◇]` calibrated legal but unrealized. `[-]` prohibited/conflicting and `[∅]` current-field no-address are addressing results, not stored addresses. An unexpanded legal node is Frontier, not residual.

Provisional closure requires an empty required-expansion frontier and no blocking active residual. A latent residual may bind a legal address, a candidate, or no address and may coexist with relative closure. When activated, route it to local absorption, required frontier, address birth, active residual with `[-]`/`[∅]`, or externalization; do not mutate a fictional residual modality.

An address is executable only when its field/version is stable, predecessors are realized or interfaced, permissions/safety/inputs hold, and no active prohibition or blocking `[∅]` applies. `ADDRESS_READY` certifies structural readiness, not domain completion.

## State and token discipline

Pay formation and proof cost once per unchanged version:

- reuse confirmed field, object identities, root paths, validated openings, evidence, and lineage until explicit invalidation;
- process each raw item once under its intake ID; do not repeat raw text in the panorama, ledger, and final output;
- load full snapshots, graph bodies, or references only for validation, mutation, dispute, migration, or requested audit;
- keep the panorama and JSON state hidden by default; render only the compact delta.

These are representation optimizations, not a weaker addressing mode.

## Compact output

```text
F0/field: <confirmed or candidate field>
Center axis: <A → ... → A′ or multiple candidates>
Motion result: <new identities and dynamic addresses>
Executable-address view: <ready positions or none>
Residuals: <latent binding / active residual / [-] or [∅] addressing-result summary>
Decision: <FIELD_CONFIRMATION_REQUIRED | ADDRESS_READY | EXPAND_REQUIRED |
           REMODEL_REQUIRED | FIELD_ASCENSION_REQUIRED | COMPLETE>
```

Hide full panorama, root-path graph, motion ledger, and JSON unless requested.

## Evidence boundary

Treat Address as experimental. Comparative advantage, universal addressability, cross-analyst agreement, drift reduction, and token savings require direct evidence.
