# Dynamic Field-Addressing Engine

## 1. Engine definition

Address is a stateful partial mapping, not a numbering convention:

```text
Φ_t(x, F_t, Γ_t, G_t, Π_t, K_t, P_t^req, P_t^latent, R_t)
  ⇀ (F_(t+1), identity_F(x), address_(t+1)(x), R_(t+1))
```

`x` may be raw information, a concept, relation, action, evidence item, external encounter, or residual. The mapping is partial: some inputs obtain realized or potential addresses, some are prohibited, some remain no-address, and irrelevant inputs stay external.

The engine changes state while mapping. Field formation, Global Expansion, Focused Penetration, compression, absorption, rebuild, and ascent may generate new relations, identities, addresses, frontiers, and residuals.

## 2. Identity generation

Do not infer structural identity from a label alone. For an input such as “you / me / them,” preserve the raw lexical item, then recover its role in a supplied or candidate relation field—for example requester, receiver, executor, witness, or affected party. Bind identity only after its role, typed relations, field, and version are traceable.

Keep three identities separate:

- raw/intake identity: preserves what entered and its source;
- object identity: tracks the same object across address changes;
- field-relative address identity: records the object's current role, path, and version.

Semantic similarity may propose a relation; it cannot certify a structural address.

## 3. Field formation

When no confirmed client field exists:

1. recover the current need and superior purpose, then infer a candidate F0, boundary, subject, success/closure condition, and tolerance;
2. recover the complete typed relation graph `G_t` and bind valid nodes/required edges to evidence;
3. derive necessary dependency partial order `Π_t` from `G_t` without linearizing incomparable nodes;
4. extract candidate centers from `Π_t` and test deletion, replacement, reordering, compression, closure, cycle, and hollow abstraction;
5. preserve multiple viable centers or return `REMODEL_REQUIRED` when none survives;
6. resolve material ambiguity during formation; show the stable product and require confirmation before address motion when identity or address legality depends on the user's intended field.

In engine 0.4, confirmation is persisted as an evidence-bound formation state (`confirmed` or traceably `reused`). A candidate field is not an active root merely because its contract text is syntactically complete.

Field formation itself may produce residuals. Do not continue while an active `[-]` or `[∅]` blocks a coherent field; split, calibrate, rebuild, or ascend first.

This order is constitutive. Do not start from a requested result, guessed identity, suffix, or similarity match and then reverse-engineer a root path. An address is downstream of the field, graph, order, and tested center; it cannot certify the structure that was invented to justify it.

## 4. Address generation gate

For candidate address `a` in field version `F_t`, require:

```text
Legal(a, F_t) =
  rooted_in_F0(a)
  AND parent_binding_and_return_valid(a)
  AND typed_root_path_present(a)
  AND predecessors_satisfied_or_interfaced(a)
  AND boundary_and_permission_compliant(a)
  AND version_compatible(a, F_t)
  AND modal_state_allowed(a)
```

Heat, relevance, contribution, uncertainty, interaction risk, cost, popularity, suffix length, lexical frequency, or embedding proximity can rank legal peers but cannot repair a missing root or predecessor. Contribution metadata requires an explicit decomposition contract and evidence; it does not imply that deeper addresses have monotonically smaller empirical effects.

The root path is a typed subgraph, not necessarily a list. Preserve incomparable branches, joins, compressed interfaces, and cross-version feedback.

Every proposed numeric recursive node starts in `address_candidates` with `field_opening_status=hypothesized|forming` and no address modality. Never place it in a legal Frontier or use it for provisional closure, executable views, or realization. A validated endpoint is born as a calibrated legal `[◇]` address and stores `field_opening_audit` for its local F0 contract, complete typed graph, necessary order, tested center, recursive parent/return interface, residual audit, evidence, and an inline restorable `state_snapshot`. Recompute its canonical hash and validate the snapshot graph/order/center rather than trusting the certificate shell.

## 5. Address-generating motion

### Global Expansion

Expand every eligible legal frontier item one uniform level within budget. Generate new `[◇]` identities/addresses, update the panorama, preserve explicit deferrals, and audit residual production or absorption. Do not use task weight to choose branches.

### Focused Penetration

Accept a focus request from the caller or an explicit standalone target. Select only legal and ready peers, first prioritizing current parent obligations or active-residual handling; only then use contribution intervals, uncertainty, interaction risk, cost, and evidence value. Permit several paths and unequal depths, preserve unselected legal branches as latent Frontier/interfaces, generate deep addresses, and write them back to the panorama. Focused motion cannot skip necessary predecessors.

### Minimum structural expansion

When the standalone request is only “address this information,” expand only enough to decide whether a legal identity/address exists. Do not optimize task priority or execute the external task.

The default bounded motion is one Global round followed by one Focus round. Because each new node opens another field, extra rounds require a residual, unresolved frontier, explicit depth, or caller instruction; depth is not a completeness score.

## 6. Residual absorption and field revision

Keep:

```text
S_t = (M_t, ActionFrontier_t, ExpansionFrontier_t^req,
       ExpansionFrontier_t^latent, Compressed_t, Λ_t, R_t, χ_t)
```

- `A_t^cand`: uncalibrated or rejected address candidates;
- `M_t=A_t^legal`: represented calibrated legal address graph;
- `ActionFrontier_t`: legal, predecessor-ready positions available to execute;
- `ExpansionFrontier_t^req`: legal positions the current parent contract requires before closure;
- `ExpansionFrontier_t^latent`: legal positions that may remain unopened this round;
- `Compressed_t`: valid, reopenable child-field interfaces;
- `Λ_t`: latent residual material, distinct from ordinary latent frontier entries;
- `R_t`: F0-relevant differences not absorbed or legally disposed;
- `χ_t`: `bound|candidate|unaddressed` bindings from residual difference records to address ledgers.

A residual may later be absorbed at the next expansion, at a finite deeper expansion, after rebuild, or only after field ascent. Record the absorption motion and version; never delete its history. A legal Frontier is not a residual merely because it is unexpanded.

For provisional closure, the required expansion frontier must be empty and no blocking active residual may remain. A latent residual may bind a legal address, candidate address, or no address and still coexist with relative closure. When activated, route it to local absorption, required frontier, address birth, an active residual with `[-]`/`[∅]`, or externalization. A hypothesis remains a candidate without modality and cannot support closure or execution.

## 7. From address to executable position

An address becomes executable only when:

- its field and version are stable enough for action;
- all necessary predecessors are realized or preserved by valid interfaces;
- permission, safety, and input conditions hold;
- it is not stale, prohibited, or blocked by active `[∅]` residuals.

Active addresses are induced only from current required expansion, ready action, or active-residual handling scope. A high score alone cannot activate an otherwise latent or structurally illegal address.

The engine returns the induced executable-address sub-poset and Ready wave. It does not call domain tools or claim task completion; the client decides and performs execution.

## 8. Relationship to clients

- **Focus:** provides root goal, task priority, motion depth/policy, and external execution. Address performs structural mapping and returns executable addresses.
- **Distill:** provides conversation scope and preservation intent. Address generates identities and relations among idea nodes; Distill chooses the canonical knowledge destination.
- **Research map:** provides the research field and evidence objects. Address tracks functional position, evidence change, innovation/target roles, and version lineage.
- **Multi-Agent work:** provides shared task field and authority. Address supplies comparable identities, predecessors, handoff locations, and reopened context.

## 9. Comparative boundary

Tokenization, etymology, embeddings, taxonomies, and knowledge graphs solve different representation problems. Address may combine with them as input evidence. Its proposed distinction is field-relative identity generated through recursive motion and residual-driven revision, not lexical segmentation or static similarity. Comparative advantage remains unverified.
