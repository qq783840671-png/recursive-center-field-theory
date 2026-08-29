# Recursive Center-Field Partial-Order Dynamics Protocol

> Legacy strict protocol: this file documents the schema-2.2/S0-S3 runtime retained for compatibility and regression comparison. It is not the default two-stage Focus runtime. Use `two-stage-runtime.md` for current invocations.

> Migration rule (v0.16): legacy `modal_status=[◇]` on a latent residual is historical encoding only. New state represents `Λ_t` as a difference record with `address_binding=bound|candidate|unaddressed`; `[◇]` belongs only to calibrated legal addresses. `[-]` and `[∅]` are addressing results.

## Contents

1. Field contract
2. Complete relations and center candidates
3. Recursive addresses and scale
4. Runtime state and modal semantics
5. Legality and typed frontiers
6. Global Expansion and Focus Penetration
7. Execute, Audit, and invalidation
8. Residual and drift audits
9. Transitions and stopping
10. Public two-level example

## 1. Field contract

Begin with a provisional contract and stabilize it through field formation before execution:

The user may supply only one natural-language task sentence. The Skill is responsible for inferring the provisional fields below and must not require the user to translate the task into this notation.

Every new field has a mandatory F0 checkpoint, but confirmation follows formation. Preserve the task, recover need/superior purpose and a provisional contract, run Survey or other field-formation motion, build the complete typed graph, derive and validate the necessary order, test candidate centers, and audit residuals. If blocking ambiguity, `[-]`, `[∅]`, unknown reach, or a disputed center remains, continue formation or stop at calibration/remodeling; do not call the product F0 yet. Once this forward construction is provisionally closed, use the state helper's `render-checkpoint` output to display the formed candidate F0 plus its validated task-specific center/partial-order axis such as `A → B → C → D → E → A′`, then stop with `F0_CONFIRMATION_REQUIRED`. Corrections or changed intent re-enter formation/calibration, produce a revised candidate, and require another rendered checkpoint. Global Expansion, Focus Penetration, planning, and Execute require explicit acceptance cryptographically bound to the currently displayed candidate. Resume without a new checkpoint only when the formed field is already confirmed and unchanged.

```text
field_id:
goal_contract_id:
field_version:
F0 root goal:
F0 confirmation: required | confirmed
current need or problem direction:
subject and superior purpose:
definition domain and scale:
start condition:
terminal and acceptance conditions:
explicit failure conditions:
included boundary:
excluded boundary:
immutable constraints:
allowed local changes:
tolerance criterion and threshold:
evidence sources and required confidence:
external dependencies:
permission and safety boundary:
depth, time, and cost budget:
```

Infer an item from reliable context when alternative values would not change the center or outcome. Keep material ambiguity in the field as an address hypothesis or residual. Send task-irrelevant input outside the field instead of displaying it as a residual. F0 confirmation is required even when the formed candidate is clear; it verifies that the agent located the intended stable problem field. Confirmation locks the formed result; it is not permission to begin formation. Use the separate human-calibration gate when different interpretations, contradictions, negative/no-address results, boundary choices, or high-risk actions would materially change the root goal, center, permission, or irreversible direction.

#### F0 provisional-closure exit gate

Derive the F0 exit audit before offering normal confirmation, then require the recorded confirmation again before Global Expansion, Focus Penetration, planning, or execution. The gate passes only when:

- at least one audited pre-confirmation formation motion changed the panorama in the forward sequence `need/superior purpose → field contract → complete typed graph → necessary order → minimum-sufficient center`; a declaration-only confirmation is insufficient;
- the candidate contract is `stable-for-execution`, graph and necessary order are `validated`, the selected center is `valid` with `minimality_status=validated`, and no human calibration is pending; after display, address motion additionally requires confirmation `confirmed`;
- the active F0 residual ledger may be empty only when the current motion audit explains why no relevant unabsorbed difference remains;
- if active residuals remain, every one is `[◇]` with `address_relation.kind=frontier`, `gate_status=legal`, a valid `[◇]` graph node retained in the Expansion frontier, a complete legal root path, and evidence-supported reach `next` or bounded `finite-deep`; no active residual is `[-]`, `[∅]`, rootless, missing-predecessor, already realized-but-unabsorbed, human-pending, or prohibited.

Passing means only **provisional closure**: either no relevant unabsorbed difference remains, or every unresolved difference has a verified finite absorption route, and the field is stable enough for the next bounded motion. Legacy `[◇,d=?]` hypotheses migrate to address candidates without modality and remain formation work; they cannot support closure. It does not mean the field is finally complete. If `[-]` remains, use calibration, center repair, split, prohibition audit, or remodeling; if `[∅]` remains, remodel or ascend the field. Never fabricate a `[◇]` residual merely to make the ledger non-empty. A resolved `[-]` or `[∅]` may move to addressing results or residual history only through an audited disposition.

The forward sequence is constitutive, not a presentation preference. Do not begin with a desired conclusion, media/user category, score, or proposed address and then reverse-engineer dependencies. Evidence may revise any earlier position, but a downstream result cannot certify its own missing predecessor. The helper verifies recorded structure and provenance; it does not independently prove that domain evidence is true, so semantic evidence review remains mandatory.

Keep identities separate:

- `F0` is the user-facing **root goal F0** together with its acceptance contract.
- `field_id` identifies a field object and remains distinct from the root goal. A child field uses a persistent identity such as `CF-F0-C3-v1`, not `F1`. When that child is the current object of attention, its own contract and local letter center are rendered as the active local `F0`; the containing field is compressed into the preserved root path and return interface.
- `goal_contract_id` identifies the current F0 contract.
- runtime `version` identifies a persisted state event revision.
- `v_t^F` identifies a relatively closed field version produced by address motion; it must not advance for every runtime edit.
- `L_t` records uniform Global Expansion resolution and is not an `F1/F2` label.

Keep `F0` as the logical root address throughout one field lineage. A root rebuild may change the contract, center, order, or closure conditions carried by `F0`; changing those contents does not rename the root. If the constitutive identity is no longer traceable, create a distinct root field such as `F0′` and preserve the branch relation.

After the user confirms F0 and field formation is stable enough to govern motion, the default initial modeling cycle is:

```text
formed F0 checkpoint
→ explicit confirmation commits S0
→ Focus #1 recursively substitutes one or more active center positions and commits S1
→ Focus #2 opens only current S1 positions and commits S2
→ Focus #3 opens only current S2 positions and commits S3
```

This is a bounded standard profile, not a universal optimum. S0 is the first relatively closed active center sub-poset. One Focus round may substitute one, two, three, or more current active positions; target count comes from F0-sensitive variation, uncertainty, residuals, and evidence. Each selected parent is replaced in the active closure sub-poset by a validated three-position child center. Unselected center positions remain mandatory compressed interfaces. An explicit user motion count or stop request overrides the profile but never legalizes a skipped predecessor, cross-level opening, unvalidated child field, or parent-interface drift.

Interpret explicit task intent after the audited S3 snapshot. `Clarify mode` (for example `理清`, `定位`, or `分析`) returns the audited handoff without external task execution. `Action mode` (for example `做`, `执行`, or `完成`) compiles the S3 activity sub-poset into `D_t/Ready_t` and continues until a terminal state. A material ambiguity still uses the human-calibration gate rather than guessing a different F0.

A Focus change selects a different view inside the same contract. A change to the root goal, subject, superior purpose, acceptance criteria, or constitutive selected-center sub-poset requires a new goal-contract/field version as appropriate and resets F0 confirmation; re-confirm only after the revised field passes formation again.

#### Mandatory runtime evidence chain

In a tool-capable invocation, `field_state.py` is the execution controller, not optional documentation. The only legal chain is:

`init/load → formation event(s) → render-checkpoint → F0_CONFIRM/S0 → run-open → recorded S1/S2/S3 Focus substitutions → audited Execute when Action mode requires it → render-result`

`run-open` defaults to `Global×0, Focus×3`, records the requested counts, and sets `continue_until_terminal=true`. The controller rejects stale confirmation, extra rounds, premature execution, cross-level replacement, parent-interface drift, a motion without state change/residual audit, and Focus without one or more verified recursive substitutions. Relative closure requires `P_req=∅`; `P_latent` and `Λ_t` may remain. If a motion replaces an address referenced by an unresolved legal `[◇]` residual, that same atomic motion must retain a reopenable Expansion interface or explicitly archive and migrate the residual to a retained child address; validation rejects a dangling `χ_t` link before the state is written. In Action mode, `CONTINUE_EXECUTION`, a plan, or remaining authorized Ready work is not terminal. `render-result` verifies the chain and derives counts and decision from state. If this controller cannot run or refuses the state, the Agent must report that Focus did not run and use `REMODEL_REQUIRED` or `BLOCKED`; it may not imitate the surface from context.

## 2. Complete relations and center candidates

### 2.1 Preserve the complete relation structure

Recover `G_t` before deriving an order. Use this canonical storage vocabulary:

- `dependency` with `necessity=required|conditional`;
- `support`;
- `conflict`;
- `similarity`;
- `coupling`;
- `prohibition`;
- `condition-transition`.

Narrative terms such as `necessary-predecessor`, `evidence-for`, `incompatible-with`, `similar-to`, `feedback`, `coupled-with`, `prohibits`, `part-of`, `implements`, and `observes` are interpretation aliases. Map them to the canonical type plus provenance or node metadata; do not invent an unsupported stored relation type.

`G_t` may contain bidirectional edges and cycles. Do not flatten all relations into causality or precedence.

Derive `Π_t` only from necessary functional precedence. `Π_t` must be a strict partial order within one version. Absence of a path means unknown or currently unrepresented unless incomparability has been explicitly established.

### 2.2 Handle cycles before claiming a partial order

For every cycle or strongly connected component:

1. check whether different scales or phases were collapsed;
2. check whether unfolding time or version removes the same-version cycle;
3. check whether the component can be justified as one cooperative function at the current scale;
4. compress it only when the compound function, boundary, interface, and evidence are explicit;
5. otherwise record a `non-poset` residual and do not manufacture a linear order.

Use version transitions for genuine cross-cycle feedback, such as `O_t → … → O_(t+1)`. Do not use a later result to reverse a prerequisite inside the same version.

### 2.3 Recover center candidates, not a guaranteed unique center

Let `𝒦_t` contain every candidate minimum sufficient load-bearing dependency sub-poset supported by current evidence. Each candidate records:

- candidate ID and status;
- member addresses and required relation IDs;
- entry and closure positions;
- deletion, replacement, reordering, compression, closure, cycle, and hollow-abstraction test results;
- evidence and confidence;
- known alternatives and incompatibilities.

Select `K_t^v` for the current version only with a stated reason. Do not delete unselected candidates. If several incomparable candidates remain viable, preserve them or split the field. If none survives, emit `REMODEL_REQUIRED`.

Do not mistake any of these for the center:

- the first category in a taxonomy;
- the most popular or high-weight node;
- the main agent or the user;
- the longest branch;
- a language label shared by otherwise hollow objects.

### 2.4 Derive parallel contribution without bloating the center

Let `P_t^∥` contain legal tasks whose removal does not break the selected minimum center or F0 structural closure, but whose evidence-backed benefit to F0 exceeds the field's contribution threshold. A contributor needs: a legal root path; any local required dependencies; a typed `support` or `coupling` attachment to a center position, acceptance condition, or explicit join; an observable contribution signal; and a join that returns its result to F0. Missing attachment or join leaves it external, hypothesized, or residual rather than executable.

Do not force incomparable contributors into the center axis. Their local required edges remain in `Π_t`; between components, preserve incomparability unless evidence establishes dependency. Benefit, popularity, or weight cannot create necessity. If F0 acceptance later requires a contributor, re-run center tests and create a new field version. If acceptance requires only an aggregate threshold or redundancy count, put that aggregate interface in the center while keeping substitutable contributors in `P_t^∥`.

Schema 2.2 represents this derived view with valid graph nodes outside the selected center, typed `support/coupling` relations, local required dependencies, optional Action paths, task scores, and explicit join nodes. It has no first-class `P_t^∥` or dual-Ready field yet; the Agent must derive and audit the view rather than claim dedicated scheduler enforcement.

## 3. Recursive addresses and scale

Use a full field view and an F0-facing address view together.

```text
F0 center: A → B → C → D → E → A′
first branches: A1, A2; B1, B2; C1, C2, C3; D1, D2; E1, E2
```

Every center position or relation may open as a child field with its own contract, complete relation structure, center candidates, selected partial order, first branches, frontiers, residuals, and closure condition. Opening changes the current viewpoint, not the persistent identity: the opened field becomes local `F0`, while its parent-facing address and `field_id` preserve where it must compress back.

An address suffix is not evidence that this opening occurred. Every numeric recursive node records `field_opening_status=hypothesized|forming|validated`. A hypothesized or forming node is an address hypothesis: it remains `[◇]` in Expansion Frontier or the residual ledger and cannot enter an active/action path, support closure, or execute. A validated address retains `field_opening_audit` proving a stable local contract, validated typed graph and necessary order, validated minimum-sufficient center, recursive parent binding and return interface, and performed residual audit. The audit includes an evidence-bound inline restorable `state_snapshot`, logical `state_ref`, and canonical hash; validators recompute the hash and inspect the snapshot rather than accepting a digest-shaped string. The ordinary response may hide child fields, but internal state may not replace them with labels or certificate fields alone.

When a child field is returned to the F0 view:

- keep its full local structure in state;
- preserve semantic breadcrumbs and provenance;
- append numeric selections to the governing root letter;
- allow unequal address lengths and several active paths under the same root.

Examples: `F0:A1.2`, `F0:B1.1.2.3`, `F0:C3.2.1`.

The numeric suffix is constructed through actual field openings. It is not an arbitrary category code. A branch remains meaningful only through its field contract, complete root path, relation types, modal state, and version.

Compression may hide a complete child field, but must preserve:

- inputs and outputs;
- conditions and scope;
- evidence and uncertainty;
- structural obligations;
- validity version;
- reopen address;
- invalidation triggers.

Compression changes display depth, not structural necessity or dependency priority.

## 4. Runtime state and modal semantics

Represent the joint state as:

```text
Σ_t =
<F0, field_id, goal_contract_id, v_t, Γ_t,
 G_t, Π_t, 𝒦_t, K_t^v, P_t^∥,
 M_t, H_t, L_t,
 ActionFrontier_t, ExpansionFrontier_t, Compressed_t,
 R_t, χ_t, q_t, V_t, D_t^K, D_t^∥, Ready_t^K, Ready_t^∥, E_t, O_t,
 U_t, A_t, 𝒱_t^F>
```

Key distinctions:

- `M_t` is the represented panorama map. It contains provenance-tagged `[+]` and `[◇]` addresses.
- `H_t` is the audited realized down-set. Every member is `[+]`; necessary predecessors must also be realized or preserved by valid interfaces.
- `L_t` is Global Expansion resolution and must not be reused as execution progress.
- `q_t` is the current Focus request and policy, not the center.
- `V_t` is an unequal-depth view, not the whole field.
- `P_t^∥` is the derived non-center contribution view; it retains attachment, local order, contribution evidence, and explicit joins.
- `χ_t` links each unresolved structural difference to a realized, frontier, hypothesized, negative, or no-address position, with reach and absorption state.
- `D_t^K/Ready_t^K` preserve the center execution closure; `D_t^∥/Ready_t^∥` contain selected contributors whose local predecessors and attachment prerequisites hold.
- `E_t` is a finite execution snapshot, not a frozen task ontology.
- `U_t` is the preserved update inbox; its `F0@U<n>` intake addresses are not legal theory addresses.
- `A_t` is the address-motion ledger containing location, propagation, and old-to-new address relations.
- `𝒱_t^F` is the field-version DAG. Its order is version-lineage reachability, not the same-version functional order `Π_t` or simple chronology.

Use modal marks relative to field and version:

- `[+]`: realized and Audit-verified;
- `[◇]`: legal potential address not yet realized;
- `[-]`: prohibited by a current irreducible rule or locked contract;
- `[∅]`: the current field has no legal way to generate, guarantee, or express the result.

Modal address state, frontier requirement, and residual activity/absorption are independent. Split Expansion positions into `P_t^req` (the parent contract currently requires opening, realization, or an effective interface) and `P_t^latent` (a calibrated legal address that is reopenable but not required this round). Split residual material into `Λ_t` (an inactive difference record whose address binding may be `bound`, `candidate`, or `unaddressed`) and `R_t^a` (an exposed or activated F0-relevant difference). `Λ_t` is not an address and never inherits `[◇]`; an ordinary `[◇]` frontier is not a residual. An active residual may link to `[◇]` or `[+]` until absorption. A temporary missing input is an operational gap, not automatically `[∅]` or a residual.

## 5. Legality and typed frontiers

Use three frontiers:

### 5.1 ActionFrontier

A position may enter `ActionFrontier_t` only when:

- its address and complete root path are legal;
- every necessary predecessor is in `H_t` or represented by a valid compressed interface;
- permissions and safety conditions permit execution;
- it is not stale, invalidated, prohibited, or already completed.

### 5.2 ExpansionFrontier

`ExpansionFrontier_t` contains legal `[◇]` positions or relations that can open as child fields. Mark each as `required` (`P_t^req`) or `latent` (`P_t^latent`). Relative closure clears `required`, not `latent`. A branch deferred by budget or Focus remains with its reason and requirement class; nonselection does not make it residual.

### 5.3 Compressed

`Compressed_t` contains closed or stable child fields represented by reopenable interfaces. `locked` is an exposure state: it prohibits current mutation or expansion while preserving the contract. It does not create another frontier and does not prove that every downstream representation preserves fidelity.

Before task scoring, apply the structural-legality gate. Only legal peers may be ranked by relevance, expected impact, uncertainty value, propagation heat, or cost. Weight cannot legalize a rootless item, remove a predecessor, or certify a candidate center.

## 6. Global Expansion and Focus Penetration

### 6.1 Survey

Use Survey when the provisional root goal is meaningful but the important paths are not yet known. Recover several shallow legal directions and label evidence as explicit, inferred, tentative, or unknown.

### 6.2 Global Expansion

Global Expansion increases panorama resolution:

```text
L_t → L_(t+1)
```

For one bounded motion:

1. snapshot every eligible `ExpansionFrontier_t` item;
2. expand every eligible item one level;
3. if a depth or cost budget prevents an expansion, retain that item and record a specific deferral reason;
4. write new addresses and relations atomically into `M_(t+1)` as `[◇]`;
5. recompute typed frontiers;
6. run residual and drift audits.

Do not use propagation weight to choose branches during Global Expansion. A Global Expansion event that changes only a history label and not the panorama is invalid.

### 6.3 Focus Penetration

Focus is center-preserving, partial-order-constrained, multi-path, unequal-depth penetration.

For one bounded motion:

1. gate candidates by ancestry, predecessors, permissions, modal state, and version;
2. rank only legal peers;
3. select one or more current active positions; one round may select several positions;
4. for every selected parent, validate a local three-position child center and its entry, internal order, exit, return interface, evidence, and residual audit;
5. substitute all selected parents atomically in the active sub-poset, preserving incoming/outgoing dependencies, incomparable branches, and joins;
6. preserve unselected required positions as compressed valid interfaces;
7. write `ΔM_focus` and the new S-state atomically into `M_(t+1)`;
8. run residual and drift audits.

Focus may materialize several child fields in one round without prior uniform Global expansion, but it cannot skip a necessary predecessor, jump across an unformed level, alter the protected parent interface, or declare the resulting address realized. In a chain-shaped view, replacing `k` parents with three child-center positions each changes length by `+2k`. The final unequal-depth activity view must remain an acyclic, relatively closed partial order consistent with F0.

## 7. Execute, Audit, and invalidation

### 7.1 Stabilize, derive the executable sub-poset, and execute atomically

Before execution, require the same F0 provisional-closure exit gate. `R_t` may be empty with an audited reason; if it is non-empty, its active items must all be addressable `[◇]` residuals. An unresolved `[-]` or `[∅]` blocks execution rather than being hidden by a scheduling decision.

When the invocation assigns an action task, modeling is an internal motion rather than the default deliverable: continue from the stable field into legal Ready execution unless acceptance is already met or a calibration, authority, safety, or genuine-blocker gate requires a stop.

Induce `D_t^K` from center-active addresses and their necessary predecessors or valid compressed interfaces. Derive `D_t^∥` from selected contributors, local predecessors, typed attachments, and joins. Mark nodes `satisfied`, `locked`, `compressed-valid`, `pending`, `active`, `completed`, or `blocked`; form `Ready_t^K` and `Ready_t^∥` separately. Preserve the `A→B→C→…` center order, run safe incomparable contributors in parallel, and retain joins explicitly. A `support/coupling` edge carries contribution but is not a required causal edge unless separately certified as `dependency`.

Freeze a finite `E_t` from `Ready_t^K ∪ Ready_t^∥`. Record expected evidence, permissions, side-effect constraints, contribution signals, joins, and rollback or failure handling. Center work retains structural priority. A resource queue may serialize incomparable contributors, but that serialization must not be written back as a causal edge.

Audit center closure and contribution completion separately. One failed optional contributor does not fail F0 unless an explicit aggregate acceptance interface remains unmet. When that interface is unmet, block the center acceptance position; do not retroactively relabel every contributor as necessary.

After execution, atomically update:

- queue, active, completed, blocked, and snapshot version;
- evidence and provenance;
- result modal states;
- `H_(t+1)`;
- typed frontiers;
- absorbed outcomes, prerequisite gaps, and residuals;
- event history and next-state decision.

Only verified results become `[+]`. Failed or incomplete work does not enter `H_t` merely because an action was attempted.

### 7.2 Propagate invalidation

If evidence invalidates a necessary predecessor, contract, relation, or compressed interface:

1. mark the source stale or invalid with evidence;
2. traverse necessary-order descendants;
3. remove or mark stale every dependent `[+]` whose support no longer holds;
4. block affected ActionFrontier and execution items;
5. re-audit Focus paths and center candidates;
6. reopen affected compressed interfaces;
7. preserve the old version and append an invalidation event.

Never keep a descendant unconditionally `[+]` after its required support has failed.

## 8. Residual and drift audits

### 8.1 Classify before calling something a residual

Classify address position, activation, and unresolved difference separately:

- existing represented address;
- legal unexpanded frontier;
- compressed interface;
- temporary prerequisite or input gap;
- task-irrelevant external information;
- prohibited result;
- unresolved structural difference (true residual).

A true residual must materially affect F0 and remain unabsorbed under the current contract, center, boundary, relation grammar, address system, or current execution result. Having a potential address does not by itself absorb it.

Keep `Λ_t` outside the active residual ledger. In new records each latent residual stores a `bound`, `candidate`, or `unaddressed` address binding, potential F0 effect, activation condition, evidence, and destination; it does not carry `[◇]`. When an upper-level goal or reality change activates it, archive the latent record and route the transition to local absorption, a required frontier, candidate calibration/address birth, a new `R_t^a` with `[-]`/`[∅]` addressing result, or externalization. Merely existing does not trigger expansion or block closure.

For every residual, store:

- stable ID and type;
- producing motion and address;
- origin: external encounter, closure-produced, compression-return, or unknown;
- effect on F0;
- representation failure;
- modal state;
- address relation: `realized`, `frontier`, `hypothesized`, `negative`, or `no-address`;
- address reach: `realized`, `next`, `finite-deep`, `unknown`, or `unreachable`, with estimated expansion count and evidence status;
- absorption state: `unresolved`, `partially-absorbed`, `tolerated`, `human-pending`, `absorbed`, or `prohibited`;
- closure condition and, when absorbed, absorbing motion/address/evidence/version;
- proposed destination: downward expansion, field ascension, in-field remodel, remain external, or prohibit;
- effect on Focus or execution;
- tolerance and evidence status.

Do not invent residuals for formal symmetry. If a complex motion has none, record why all relevant outcomes were absorbed at the current tolerance.

### 8.2 Audit drift

Record residual and drift audits after every address-generating motion: field formation, center adjustment, human calibration, Survey, Global Expansion, Focus, expansion, compression, promotion, split, rebuild, address materialization, and Execute. A no-residual result needs a reason showing that relevant outcomes were absorbed within tolerance rather than omitted or flattened.

Then audit drift:

```text
goal_drift:
  Did F0, success criteria, or immutable constraints change without versioning?
structural_drift:
  Did G_t, Π_t, selected center, or direction change without evidence and REMODEL?
semantic_drift:
  Did an address or term change functional role without a field/address change?
version_drift:
  Was evidence consumed from an incompatible version, or was history overwritten?
state_estimation_drift:
  Was a [◇], invalidated, or unaudited item reported as [+]?
estimate_revision:
  Did progress, remaining work, confidence, or delivery estimate change without a traceable address/evidence delta?
```

Useful measurements include violation count, stale-address rate, lost-constraint count, unsupported estimate revisions, recovery time, and calibration against eventual outcomes. These metrics test the drift hypothesis; the protocol does not assume improvement.

### 8.3 Reconcile updates as address motion

When the user supplies an update to a persisted field:

1. append the raw update unchanged to the update inbox and assign an intake address `F0@U<n>`;
2. identify the source field version(s) and nearest related represented address(es);
3. classify the update as `external`, `local-replace`, `legal-expansion`, `principle-conflict`, `no-address-residual`, `subfield-rebuild`, `root-rebuild`, or `version-branch`;
4. choose explicit address operations from `retain`, `payload-replace`, `expand`, `move`, `split`, `merge`, `retire`, `birth`, `externalize`, and `prohibit`;
5. audit the changed child-to-parent interface and move an unabsorbed residual upward only while the next field cannot close;
6. stop at the nearest upper position that can absorb the residual, regain relative closure, and preserve its own parent interface;
7. store every old-to-new address relation, including unchanged, split, merged, new, and retired addresses;
8. create a field version only after a closure audit succeeds; otherwise retain an open motion or unresolved residual without inventing a version;
9. preserve incomparable field-version heads when different residuals produce incompatible but supported closures.

A raw update may require more than one sequential address motion. In particular, `[∅]` is an unresolved stage: first persist the no-address residual, then continue the same update through expansion, reconstruction, branching, or externalization. Never mark the update resolved merely because its absence of address was recorded.

An unchanged address label does not prove a local replacement: role, dependency, scope, and interface equivalence must still hold. Conversely, a deeper legal expansion does not change every upper field version when its compressed interface remains equivalent.

Never treat a reliable counterexample as `[-]` solely because it conflicts with the current theory. `[-]` prohibits a transition under the current contract. An evidenced difference that the field cannot express is `[∅]` plus a residual and may trigger upward reconstruction.

For each reconciliation, persist the update ID and intake address, source field version(s), classification, target or nearest related addresses, motion operator, affected scope, nearest unstable upper position, ascent path, interface-equivalence result, address changes, residual links, closure audit, result field version(s), and one next-state decision. Read [maintenance.md](maintenance.md) for the complete maintenance contract.

## 9. Transitions and stopping

Allowed structural transitions:

- `UPDATE_INGEST`
- `UPDATE_STRUCTURE`
- `UPDATE_RECONCILE`
- `F0_CONFIRM`
- `FIELD_FORM`
- `CENTER_ADJUST`
- `HUMAN_CALIBRATE`
- `SURVEY`
- `GLOBAL_EXPAND`
- `FOCUS`
- `EXPAND`
- `COMPRESS`
- `PROMOTE`
- `SPLIT`
- `REBUILD`
- `ADDRESS_MATERIALIZE`
- `PLAN_EXECUTION`
- `EXECUTE`
- `AUDIT`
- `INVALIDATE`
- `HANDOFF`
- `STOP`
- `REMODEL_REQUIRED`

After Audit, emit exactly one decision. `F0_COMPLETE` and provisional closure require `P_req=∅`; `P_latent≠∅` and `Λ_t≠∅` are allowed:

- `F0_CONFIRMATION_REQUIRED`
- `FIELD_FORMATION_REQUIRED`
- `HUMAN_CALIBRATION_REQUIRED`
- `CONTINUE_EXECUTION`
- `FOCUS_REQUIRED`
- `EXPAND_REQUIRED`
- `REMODEL_REQUIRED`
- `FIELD_ASCENSION_REQUIRED`
- `F0_COMPLETE`
- `BLOCKED`

Stop a branch when further depth cannot change the next decision, result, verification, or tolerance; evidence is insufficient; the branch is outside F0; or the current budget is exhausted. A budget stop is a Handoff, not completion.

Stop the run when F0 acceptance is met with evidence, the user stops or changes authority, permissions or safety boundaries prevent continuation, or a genuine blocker remains. Preserve the final version, three frontiers, compressed interfaces, and unresolved residuals.

### Default rendering contract

Always persist the panorama, S0-S3 active sub-posets, active addresses, root-path sub-DAGs, child-field opening audits, replacement records, interface hashes, motion deltas, typed frontiers, execution sub-poset, stable residual IDs, and full residual ledger. Before a stable product exists, render the candidate root direction, material formation blockers, and one formation/calibration/remodel decision. Once the exit gate passes but confirmation is pending, render only: `F0: <one sentence>`; the validated task-specific center axis with short labels; the legal Expansion-frontier count; material true residual counts; and `F0_CONFIRMATION_REQUIRED`. Frontier counts and residual counts are distinct: an unopened legal potential is not itself a residual. Do not fabricate activity addresses before S0.

After confirmation, the default motion profile is `Focus ×3 (S0→S3)` with no mandatory Global round. An explicit request may set different counts, targets, depth, budget, or stop point. It cannot authorize a missing predecessor, unvalidated address, reversed dependency, cross-level replacement, or omitted required motion; stop with `EXPAND_REQUIRED` while `P_req` is nonempty.

After confirmed-F0 motion, only `render-result` may emit this compact surface:

```text
F0：<确认后的根层>
运动：Focus ×3（S0→S3）
地址：生成 6 条，验证 3 条，必要待展开 0 条，普通待展开 3 条
结果：<答案或执行成果>
剩余：潜在Λ1 / 活动R2（绑定◇2） / 禁止结果-0 / 无地址结果∅0
决策：CONTINUE_EXECUTION
```

These numbers are illustrative. The renderer obtains `生成` from event deltas, `验证` from current proofs, splits legal Expansion addresses by `required/latent`, and counts `Λ_t` and `R_t^a` separately. The Agent cannot supply them. For an inquiry, the answer is the result; for an action task, the delivered effect is the result. `[◇]` counts calibrated legal but unrealized addresses; an active residual remains an `R_t^a` record even when it binds such an address. `[-]` and `[∅]` count addressing results, not stored addresses or residual modalities. Reveal details on request.

Chinese terminology is normative: F0 is `根层`; a complete path from F0 is `根路径`; the immediately containing level is `上一层`; an opened child is `下一层`. The JSON compatibility key `root_ancestry` must render as `根路径`, and legacy `ancestor_goal` must render as `根目标` or `F0`; never translate compatibility field names literally.

## 10. Public two-level example: open-source software defect repair

This example demonstrates construction, not a universal taxonomy.

### 10.1 Parent field F0

Field contract: repair a reproducible defect in an open-source project and deliver an auditable change without silently changing the requested behavior.

```text
A Receive and delimit the defect
  A1 functional error
  A2 performance regression
  A3 compatibility problem
→ B Reproduce and form evidence
  B1 local environment
  B2 continuous integration
  B3 user-reported environment
→ C Locate the first structural cause
  C1 data path
  C2 state transition
  C3 interface contract
→ D Complete the repair
  D1 local patch
  D2 structural modification
  D3 compatibility strategy
→ E Validate and deliver
  E1 regression test
  E2 integration test
  E3 review and merge
→ A′ New project version after the repair
```

One selected object path is:

```text
F0:A1 → B1 → C3 → D1 → E1 → A′
```

This path does not delete A2/A3, B2/B3, or other legal branches. They remain represented, compressed, or on `ExpansionFrontier` according to the current Focus and evidence.

### 10.2 Focus on `F0:C3`

Open `C3 interface contract` as child field `CF-F0-C3-v1`:

```text
CF-F0-C3-v1:A Capture the interface anomaly
  A1 input-format mismatch
  A2 response mismatch
  A3 lifecycle or timing mismatch
→ B Restore the responsibility relation
  B1 caller obligation
  B2 provider obligation
  B3 shared invariant
→ C Locate the contract violation
  C1 precondition
  C2 postcondition
  C3 compatibility or version contract
→ D Repair the contract
  D1 caller adaptation
  D2 provider implementation
  D3 explicit migration
→ E Validate upstream and downstream
  E1 caller test
  E2 provider test
  E3 integration regression
→ A′ Restored interaction in a new version
```

If the selected local route is `A2→B3→C3→D1→E3→A′`, retain that full local structure and return an F0-facing constructed address such as:

```text
F0:C3.2.3.3.1.3[◇]
```

The address remains `[◇]` until the repair is executed and its required tests pass Audit. A failed integration test may invalidate D1, reopen the compressed child field, or expose a residual that requires D2/D3 or a parent-field rebuild.

### 10.3 Two motions on the same example

- **Global Expansion** opens one more branch layer under every eligible A–E expansion position within budget.
- **Focus Penetration** may open `C3` deeply, `E1` moderately, leave `A1/B1` compressed after evidence is stable, and keep other legal branches shallow.

The first produces a higher-resolution panorama. The second produces an unequal-depth action view. Both write addresses back, preserve provenance, and run residual plus drift audits.
