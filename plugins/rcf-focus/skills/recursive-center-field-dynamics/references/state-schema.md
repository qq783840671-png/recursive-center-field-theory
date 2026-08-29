# Dynamic Field State Schema

> Legacy schema reference: this file documents `field_state.py` and schema 2.2. The default two-stage Focus runtime uses `focus_runtime.py`; see `two-stage-runtime.md`. Do not mix the two state formats.

> v0.16 migration: schema-2.2 latent records with `modal_status=[◇]` and `address_relation` remain readable, but new records use `address_binding.kind=bound|candidate|unaddressed` and omit `modal_status`. Address hypotheses live in a candidate ledger; only calibrated legal addresses use `[◇]`. Activated `[-]`/`[∅]` values are addressing results, not addresses.

Use one JSON state for multi-turn or tool-using work. The state is operational memory, not a claim that the field is objectively complete.

Schema `2.2` is the current joint model. Its additive current profile preserves earlier 2.2 snapshots while new writes distinguish required/latent Expansion addresses and latent/active residuals. It also keeps address-motion maintenance and requires strict runs to commit confirmed `S0` plus auditable recursive Focus substitutions `S1...Sn`. Missing additive fields in an older 2.2 snapshot mean “legacy-unrecorded”; the helper treats an untyped Expansion item as `latent` for compatibility and never invents latent-residual history.

Schemas `1.0` through `2.1` remain readable, validatable, and summarizable. They are read-only compatibility formats: the helper must not mutate or silently upgrade their claims. Schema `2.1` lacks address-motion maintenance; schema `2.0` additionally used the legacy field name `ancestor_goal` and lacked field-formation state, `χ`, absorption history, and `D_t/Ready_t`.

## Contents

- [Schema 2.2 joint model](#schema-22-joint-model)
- [Field contract](#field-contract-22)
- [Presentation and terminology contract](#presentation-and-terminology-contract)
- [CLI mutation routes](#cli-mutation-routes)
- [Address-motion maintenance](#address-motion-maintenance)
- [General relation graph and necessary order](#general-relation-graph-and-necessary-order)
- [Center candidates and selection](#center-candidates-and-selection)
- [Frontiers, residual activity, and modal state](#frontiers-residual-activity-and-modal-state)
- [Global Expansion and Focus](#global-expansion-and-focus-22)
- [Execution audit and invalidation](#execution-audit-and-invalidation)
- [Residuals and SCC analysis](#residuals-and-scc-analysis)
- [Drift audit](#drift-audit)
- [Compatibility](#compatibility-22)
- [Legacy schemas 1.0 through 1.3](#legacy-schemas-10-through-13-read-only)

## Schema 2.2 joint model

The required top-level shape is:

```json
{
  "schema_version": "2.2",
  "version": 0,
  "field": {},
  "center": {},
  "focus": {},
  "panorama": {},
  "execution": {},
  "evidence": [],
  "drift": {},
  "address_dynamics": {},
  "recursive_focus": {},
  "history": []
}
```

The following schema-2.2 joint motions are atomic and residual-audited: `UPDATE_RECONCILE`, `FIELD_FORM`, `CENTER_ADJUST`, `HUMAN_CALIBRATE`, `SURVEY`, `GLOBAL_EXPAND`, `FOCUS`, `EXPAND`, `COMPRESS`, `PROMOTE`, `SPLIT`, `REBUILD`, `ADDRESS_MATERIALIZE`, `EXECUTE`, and `INVALIDATE`. `F0_CONFIRM` is an atomic drift-audited lock event, not an address-generating or formation event. The helper applies a payload to an in-memory copy, derives the necessary order and SCC ledger, rebuilds `D_t/Ready_t`, propagates invalidity when required, computes a drift audit, validates the complete next state, and only then atomically replaces the file. `UPDATE_INGEST`, `UPDATE_STRUCTURE`, `AUDIT`, `HANDOFF`, `PLAN_EXECUTION`, `STOP`, and `REMODEL_REQUIRED` are ordinary history events; they do not claim to generate theory addresses and therefore do not require a drift record.

Version `0` is the initialization exception: the root address `F0` is created as `[+]` with an `AUDIT` history event and no drift audit. All task addresses created after initialization begin as `[◇]`. In this implementation, only an audited `EXECUTE` may change them to `[+]`; Global Expansion, Focus, and all generic motion deltas must keep `realized_addresses` empty. `ADDRESS_MATERIALIZE` remains a reserved audited motion name but does not bypass this rule.

### Field contract 2.2

```json
{
  "id": "F0",
  "name": "task field",
  "root_goal": "the result this run ultimately serves",
  "boundary": {"included": [], "excluded": []},
  "success_criteria": [],
  "immutable_constraints": [],
  "allowed_changes": [],
  "legal_roots": ["F0"],
  "tolerance": {"criterion": null, "threshold": null},
  "status": "field_form",
  "phase": "forming",
  "contract_status": "provisional",
  "f0_confirmation": {
    "status": "required|confirmed",
    "confirmed_by": null,
    "confirmed_at_runtime_version": null,
    "checkpoint_hash": null
  },
  "f0_checkpoint": null,
  "ambiguities": [],
  "human_calibration": {"status": "not-required", "items": []}
}
```

The listed field keys except `f0_confirmation` are mandatory in schemas 2.1 and 2.2; `f0_confirmation` is mandatory in schema 2.2. `root_goal` is provisional content carried by the logical root address while the field forms; only the stable product becomes user-facing F0. Schema 2.2 requires `field.id` and `legal_roots` to preserve the address `F0`. A root rebuild may revise `root_goal` only through a `root-rebuild` address motion whose audit creates an explicit root field version. The same atomic commit advances the protected drift baseline, resets confirmation to `required`, and normally sets `FIELD_FORMATION_REQUIRED`; the rebuilt graph/order/center must form and pass the exit gate before `F0_CONFIRM` is legal. `ancestor_goal` is accepted only in read-only schema 2.0 and earlier files. `FIELD_FORM`, `CENTER_ADJUST`, `HUMAN_CALIBRATE`, and `SURVEY` are legal before confirmation because they construct or recalibrate the candidate. Global Expansion, Focus, planning, and Execute require a formed candidate plus explicit confirmation. A legacy stored `bypassed` value may be read for compatibility, but it is unconfirmed and authorizes only formation/calibration/remodel decisions.

The F0 provisional-closure gate is derived rather than persisted as another source of truth. A candidate is confirmable only when: `contract_status=stable-for-execution`; an earlier audited formation motion advanced `panorama.map_version`; graph/order and the minimum center are validated; human calibration is not pending; and no Expansion item has `expansion_requirement=required`. Ordinary latent Expansion addresses and `panorama.latent_residuals` may remain. `render-checkpoint` fingerprints the root contract and selected center; confirmation binds that hash. An empty active `panorama.residuals` ledger is valid with an audit reason. If active residuals exist, each must use `[◇]`, a legal retained frontier address, a validated finite-reach opening, and a nonblocking absorption state. A hypothesized/forming child or unknown reach cannot support closure. Any active `[-]`, `[∅]`, rootless, missing-predecessor, realized-but-unabsorbed, human-pending, or prohibited item leaves the gate open.

A later change to the selected center ID, members, or required relations resets `f0_confirmation` to `required`; the revised field must pass formation again before re-confirmation.

### Presentation and terminology contract

Before formation passes, render the root direction, blockers, and one decision; do not call it stable F0. After the gate passes, render F0, center axis, separate `P_req/P_latent` counts, separate `Λ_t/R_t^a` counts, and `F0_CONFIRMATION_REQUIRED`; generate no S-state. `F0_CONFIRM` commits `S0`, followed by the default `S0→S1→S2→S3`.

All detailed addresses remain persisted even when the ordinary response is compact. After confirmation and motion, only `render-result` emits the six lines. It derives the confirmed F0, actual profile, unique event-delta addresses, currently validated subset, legal Expansion frontier, active residual modal counts, and decision from state; callers supply only the domain result text. The answer to a question or delivered effect of an action is itself the result and must not be repeated under a second label. Full S0-S3 diffs, child-field opening audits, panorama, active addresses, root paths, motion deltas, frontiers, `D_t/Ready_t`, stable residual IDs, and the residual ledger are on-demand views. Task-irrelevant external information is hidden.

The JSON keys `root_ancestry`, `compressed_ancestor_addresses`, and legacy `ancestor_goal` remain unchanged for compatibility. They are not display vocabulary. Chinese output renders them as `根路径`, `根路径中的压缩接口`, and `根目标／F0`; it renders F0 as `根层`, an immediate parent as `上一层`, and a child as `下一层`. Never translate the compatibility field names literally in current user-facing text.

### CLI mutation routes

Payload arguments accept inline JSON or `@path/to/payload.json`; `@-` reads standard input.

```text
field_state.py init STATE --name NAME --goal GOAL [--success CRITERION ...]
field_state.py validate STATE
field_state.py summary STATE
field_state.py render-checkpoint STATE
field_state.py f0-confirm STATE --by CONFIRMER [--note NOTE]
field_state.py run-open STATE --mode action|inquiry|clarify [--global-count 0] [--focus-count 3]
field_state.py render-result STATE --result TEXT
field_state.py update-receive STATE --text TEXT [--source SOURCE] [--source-ref REF] [--evidence-id ID ...]
field_state.py update-structure STATE --update-id U1 --structure-json @motion.json
field_state.py update-apply STATE --motion-id AM1 --address-delta-json @delta.json
field_state.py update-show STATE [--update-id U1]

field_state.py transition STATE --type FIELD_FORM --note NOTE --motion-delta-json @delta.json
field_state.py transition STATE --type HUMAN_CALIBRATE --note NOTE --motion-delta-json @delta.json
field_state.py transition STATE --type GLOBAL_EXPAND --note NOTE --motion-delta-json @delta.json
field_state.py focus STATE --query QUERY --focus-delta-json @focus.json [--address ADDRESS] [--rationale TEXT]
field_state.py transition STATE --type EXECUTE --note NOTE --execution-audit-json @audit.json
field_state.py transition STATE --type INVALIDATE --note NOTE --invalidation-json @invalidation.json
```

`render-checkpoint` persists the displayed F0 fingerprint. `f0-confirm` binds explicit acceptance to that fingerprint. `run-open` records the mode and requested Global/Focus counts; Global, Focus, planning, and Execute are rejected without its open profile or in the wrong order. `render-result` rejects incomplete/unproven profiles, Action completion without an Execute event, `F0_COMPLETE` with active residuals or executable pending work, and repeated rendering. It writes `RUN_RENDER` with state-derived counts and a result digest. All mutations validate a deep copy before atomic replacement. Schemas `1.0`–`2.1` accept only `validate` and `summary`.

Schema 2.2 currently derives parallel contribution `P_t^∥` rather than persisting a new top-level object. A contributor is a valid graph node outside the selected center with a legal root path, any local required dependencies in `panorama.order`, a typed `support` or `coupling` attachment to a center/acceptance/join node, evidence-backed contribution scores, and—when selected—an optional Action path that returns through an explicit join. Multiple such Action paths may be incomparable and Ready together. The schema does not yet enforce a contribution threshold or expose separate `D_t^K/D_t^∥` and `Ready_t^K/Ready_t^∥` fields; the Skill and protocol must derive and audit those views without representing weight as necessity.

The current execution object may include:

```json
{
  "motion_profile": {
    "status": "unset|open|rendered",
    "mode": "action|inquiry|clarify|null",
    "global_count": 1,
    "focus_count": 3,
    "continue_until_terminal": true,
    "starting_recursive_round": 0,
    "confirmation_version": 3,
    "checkpoint_hash": "sha256:...",
    "opened_at_runtime_version": 4,
    "rendered_at_runtime_version": null
  }
}
```

New states initialize this profile as `unset`. Older schema-2.2 states remain readable, but a new strict run must open a profile and set `continue_until_terminal=true`. `F0_CHECKPOINT`, `RUN_OPEN`, and `RUN_RENDER` are runtime-proof events, not address-generating field motions.

### Recursive Focus S-states

New states initialize:

```json
{
  "recursive_focus": {
    "required_focus_rounds": 3,
    "child_center_width": 3,
    "s0_confirmation_version": null,
    "current_snapshot_id": null,
    "snapshots": []
  }
}
```

`F0_CONFIRM` atomically commits `S0` from the selected minimum-sufficient center. Every Focus delta then includes one or more simultaneous substitutions:

```json
{
  "recursive_replacements": [
    {
      "parent_address": "F0:C",
      "child_center_addresses": ["F0:C1", "F0:C2", "F0:C3"]
    },
    {
      "parent_address": "F0:E",
      "child_center_addresses": ["F0:E1", "F0:E2", "F0:E3"]
    }
  ]
}
```

The controller derives the next snapshot. A snapshot contains `state_id`, `focus_round`, `source_state_id`, `active_addresses`, `active_relations`, expanded parents, replacement records, `closure_status`, the F0 checkpoint hash, runtime version, and canonical `state_hash`.

Enforce:

- every replacement parent occurs in the immediately previous active sub-poset;
- one round may replace several parents, but cannot replace the same parent twice or share a child;
- every parent exposes exactly three directly bound, `validated` child-field centers;
- required dependency edges connect parent to child entry and order the three child-center positions;
- substitution preserves all predecessor/successor interfaces, incomparable branches, and joins;
- the protected parent interface hash is unchanged;
- the resulting active sub-poset is acyclic and `relative-closed`;
- for a chain view with `k` replacements, active length changes by `+2k`;
- S-state IDs are contiguous and their hashes recompute.

The parent remains the persistent field identity and reopen interface, but its three children replace it in the current active closure sub-poset. Hidden rendering never permits hidden or unverified state.

### Address-motion maintenance

Schema 2.2 requires:

```json
{
  "address_dynamics": {
    "root_address": "F0",
    "inbox": [],
    "motions": [],
    "lineage": [],
    "field_versions": {
      "active_branch_id": "main",
      "branches": [
        {"id": "main", "parent_branch_id": null, "status": "active"}
      ],
      "heads": [
        {
          "branch_id": "main",
          "field_address": "F0",
          "version_id": null,
          "working_closure": "open",
          "destabilized_by_motion_ids": []
        }
      ],
      "records": []
    }
  }
}
```

Top-level `version` remains the runtime event revision. `panorama.map_version` remains the current graph/order/frontier snapshot revision. `field_versions.records` stores only field-closure versions produced after an address motion restores relative closure. These three version axes must not substitute for one another.

`update-receive` stores the raw update without interpretation:

```json
{
  "id": "U1",
  "intake_address": "F0@U1",
  "raw_content": "unmodified update text",
  "source": {"kind": "user|evidence|agent-tentative|residual", "ref": null},
  "received_at_runtime_version": 1,
  "evidence_ids": [],
  "status": "pending|structured|resolved",
  "motion_ids": []
}
```

`structured` is also the durable unresolved state after an applied motion that has not absorbed the update—for example, a `no-address-residual` motion. A no-address motion must write at least one auditable residual and cannot claim relative closure. Such an update may receive another proposed motion after the previous one is applied or dismissed. Preserve the complete motion chain, allow at most one proposed motion at a time, and set `resolved` only when the update is terminally external/prohibited/local or a non-no-address motion restores the audited closure required by its scope.

Runtime revision, panorama `map_version`, and field-closure version are independent. Applying an address motion always advances runtime history. It advances `map_version` only when the panorama, field contract, graph/order, evidence, modal ledger, residual ledger, Focus paths, or frontiers actually change. A pure field-version branch may therefore create closure-version records without pretending that the current panorama map was rewritten.

`F0@U1` is an intake address in the maintenance field. It is not a legal theory address and must not appear in `panorama.graph`, `Π_t`, or a Focus path.

`update-structure` creates a proposed address motion:

```json
{
  "classification": "external|local-replace|legal-expansion|principle-conflict|no-address-residual|subfield-rebuild|root-rebuild|version-branch",
  "branch_id": "main",
  "source_field_version_ids": [],
  "assignment": {
    "kind": "external|existing|potential|new-child|negative|no-address|subtree",
    "anchor_addresses": ["F0:A2"],
    "from_addresses": [],
    "to_addresses": [],
    "modal_status": null,
    "rationale": "why the update belongs here"
  },
  "closure_audit": {
    "tested": [],
    "nearest_unstable_ancestor": null,
    "minimal_rebuild_root": null,
    "propagation_stop_address": null,
    "closure_before": "relative-closed|open|unstable|unknown",
    "closure_after": "relative-closed|open|unstable|unknown"
  },
  "residual_ids": [],
  "evidence_ids": []
}
```

The three propagation positions are distinct: `nearest_unstable_ancestor` is the first upper field that loses closure; `minimal_rebuild_root` is the smallest scope sufficient to absorb the residual and recover closure; `propagation_stop_address` is the next upper field whose interface remains stable. If evidence cannot establish these positions, retain `unknown` and do not claim a whole-field rebuild.

`update-apply` consumes the proposed motion and an atomic address delta. The delta uses the ordinary graph, frontier, evidence, modal, and residual fields and additionally accepts `address_dynamics_delta`:

```json
{
  "lineage": [
    {
      "id": "L1",
      "kind": "retain|payload-replace|expand|move|split|merge|retire|birth|externalize|prohibit",
      "from": [],
      "to": [],
      "reason": "",
      "evidence_ids": []
    }
  ],
  "new_field_versions": [],
  "head_updates": []
}
```

Each `from` or `to` endpoint contains `node_id`, `field_version_id`, `address`, and `payload_revision`. `retain` preserves the node, address, and payload revision; `payload-replace` preserves node and address while incrementing the payload revision; `move` preserves the node under a new address; `split` is one-to-many; `merge` is many-to-one; `retire` has no target; `birth` has no source; and `expand` retains its source while adding descendants. `externalize` and `prohibit` remove an existing positive address from the theory relation without erasing its evidence trail.

A field-version record contains `id`, `branch_id`, `field_address`, `ordinal`, `parent_ids`, `formed_at_runtime_version`, `formed_by_motion_id`, `closure_status`, `map_version`, `center_id`, absorbed update/residual IDs, lineage IDs, reused addresses, and optional paired `snapshot_ref`/`snapshot_hash`. A supplied hash is a lowercase `sha256:` digest. Only `closure_status=relative-closed` may enter `records`. Ordinals advance within one branch/address coordinate, every declared source version remains a parent, and every new record requires one matching relatively closed head update. A `root-rebuild` produces `F0`; a `subfield-rebuild` produces its `minimal_rebuild_root`; and a `version-branch` must start from an existing source version and create at least two relatively closed versions on explicit child branches at the same minimum rebuild root. Because the live panorama cannot stand in for two incomparable payloads, every branch result requires its own restorable snapshot reference and digest. A local payload replacement, external item, prohibited transition, or still-open residual may advance runtime state without producing a field version.

Schema 2.2 enforces these root invariants:

- `field.id == "F0"` and `field.legal_roots == ["F0"]`;
- exactly one graph node has address `F0`, with `node_id`, `parent_address: null`, and a positive `payload_revision`;
- every other graph node has one recursive `parent_address`, and the parent chain is acyclic and reaches `F0`;
- the dependency order remains separate from recursive containment;
- `F0` may be retained but never moved, split, merged, retired, or assigned a different root address inside the same lineage;
- old schemas are never given inferred inbox, lineage, or field-version records.

Schema 2.2 may carry `address_dynamics.legacy_display_addresses` only as an explicit migration quarantine for old numeric section labels that were created before recursive field-opening audits existed. Each listed item must be an F0-facing numeric label, remain `[◇]`, and stay out of Focus and every frontier. The exception prevents a fabricated child-field certificate; it does not legalize the label as a new recursive address. Reopening such content must generate a new audited child address from its validated parent binding.

Read [maintenance.md](maintenance.md) for classification, minimum upward propagation, closure, and counterexample rules.

### General relation graph and necessary order

`panorama.graph` stores the full relation graph `G`. It may contain semantic cycles.

```json
{
  "status": "unvalidated|tentative|validated|invalid",
  "nodes": [
    {
      "node_id": "N-F0-A1",
      "address": "F0:A1",
      "parent_address": "F0",
      "payload_revision": 1,
      "function": "load-bearing function",
      "evidence_status": "explicit|inferred|tentative|unknown",
      "evidence_ids": ["E1"],
      "validity": "valid|stale|invalid",
      "modal_status": "[+]|[◇]",
      "field_opening_status": "hypothesized|forming|validated",
      "field_opening_audit": {
        "field_id": "CF-F0-A1-v1",
        "local_root": "F0",
        "parent_address": "F0",
        "contract_status": "stable-for-execution",
        "graph_status": "validated",
        "order_status": "validated",
        "center_status": "validated",
        "recursive_structure_status": "validated",
        "residual_audit_status": "performed",
        "return_interface_status": "valid",
        "state_ref": "logical reference for the inline child snapshot",
        "state_snapshot": {
          "field": {"field_id": "CF-F0-A1-v1", "local_root": "F0", "parent_address": "F0", "contract_status": "stable-for-execution"},
          "graph": {"status": "validated", "nodes": [{"address": "F0"}], "relations": []},
          "order": {"status": "validated", "nodes": ["F0"], "relations": []},
          "center": {"status": "validated", "selected": "K1", "candidates": [{"id": "K1", "members": ["F0"], "minimality_status": "validated"}]},
          "recursive_structure_status": "validated",
          "frontiers": {"action": [], "expansion": [], "compressed": []},
          "residuals": [],
          "residual_audit": {"status": "performed"},
          "return_interface": {"status": "valid", "parent_address": "F0"}
        },
        "state_hash": "canonical sha256 of state_snapshot",
        "evidence_ids": ["E1"]
      }
    }
  ],
  "relations": [
    {
      "id": "g1",
      "source": "F0",
      "target": "F0:A1",
      "relation_type": "dependency|support|conflict|similarity|coupling|prohibition|condition-transition",
      "necessity": "required|conditional|null",
      "evidence_status": "explicit|inferred|tentative|unknown",
      "evidence_ids": ["E2"],
      "validity": "valid|stale|invalid"
    }
  ]
}
```

Only a valid `dependency` relation with `necessity: required` can enter `panorama.order`. Non-dependency relations must use `necessity: null`; conditional dependencies remain in `G` but are not order edges. When graph status is `validated`, every non-root valid node and every valid required dependency must carry non-empty `evidence_ids` that resolve in the top-level evidence ledger. Every numeric recursive node such as `F0:A1` must carry `field_opening_status` and `field_opening_audit`. Legacy schema 2.2 encoded `hypothesized` and `forming` as `[◇,d=?]`; migration treats them as address candidates without modality, so they may not enter a legal Frontier, Action/active Focus, support closure, or become `[+]`. `validated` requires the stable local contract, typed graph, acyclic necessary order, selected minimum-sufficient center, recursive parent/return interface, and residual audit to agree with an inline `state_snapshot`; the helper recomputes its canonical SHA-256 and rejects mismatch or malformed structure. This proves recorded structural consistency, not the truth of domain evidence.

```json
{
  "status": "unvalidated|tentative|validated|invalid",
  "derived_from_map_version": 0,
  "nodes": [],
  "relations": [],
  "explicit_incomparables": [],
  "scc_analysis": {
    "performed": true,
    "components": [],
    "non_poset_residual_ids": []
  }
}
```

An unresolved cyclic SCC in the required dependency projection is excluded from the order and recorded as a `non-poset` residual. Required descendants reachable through that unresolved SCC are also excluded; they cannot reappear as rootless order or Action nodes. Each current SCC record includes `required_descendants`. The helper must never delete the original graph nodes or relations merely to manufacture a DAG.

### Center candidates and selection

```json
{
  "status": "tentative|selected|remodel-required|invalid",
  "candidates": [
    {
      "id": "K1",
      "members": ["F0", "F0:A"],
      "relation_ids": ["g1"],
      "closure_targets": ["F0:A"],
      "minimality_status": "unvalidated|validated|invalid",
      "tests": {
        "deletion": {"status": "unvalidated|pass|fail|not-applicable", "rationale": "", "evidence_ids": []},
        "replacement": {"status": "unvalidated|pass|fail|not-applicable", "rationale": "", "evidence_ids": []},
        "reordering": {"status": "unvalidated|pass|fail|not-applicable", "rationale": "", "evidence_ids": []},
        "compression": {"status": "unvalidated|pass|fail|not-applicable", "rationale": "", "evidence_ids": []},
        "closure": {"status": "unvalidated|pass|fail|not-applicable", "rationale": "", "evidence_ids": []},
        "cycle": {"status": "unvalidated|pass|fail|not-applicable", "rationale": "", "evidence_ids": []},
        "hollow_abstraction": {"status": "unvalidated|pass|fail|not-applicable", "rationale": "", "evidence_ids": []}
      },
      "evidence_status": "explicit|inferred|tentative|unknown",
      "validity": "valid|stale|invalid"
    }
  ],
  "selected": "K1",
  "selection_reason": "why this candidate governs the current version",
  "selection_evidence": []
}
```

Candidates may remain incomparable. `selected` is nullable but, when non-null, must reference a valid candidate. Candidate members and relations must lie in the derived order; all selected relation IDs must be required dependency edges whose endpoints remain inside the candidate. A candidate cannot self-certify minimality: `minimality_status=validated` is legal only when the seven named tests are all `pass` or explicitly `not-applicable`, each has a rationale, and every `pass` references evidence already stored in `evidence`.

### Frontiers, residual activity, and modal state

Schema 2.1 uses three explicit frontiers:

```json
{
  "frontiers": {
    "action": [],
    "expansion": [],
    "compressed": []
  }
}
```

- `action`: legal and dependency-ready `[◇]` addresses eligible for execution. Every execution queue address must occur here.
- `expansion`: legal `[◇]` addresses eligible for Global Expansion or Focus penetration. Each current item carries `expansion_requirement: required|latent`; a missing value in an older 2.2 snapshot is read as `latent`.
- `compressed`: `[◇]` interfaces with a contract and `reopen_address`; their exposure is `compressed`, `locked`, or `reopen-required`.

Action and Expansion items use the structured path fields: canonical address, display address, complete root-path sub-DAG, required predecessors, structural necessity, dependency readiness, gate result, depth, scores, status, active `residual_ids`, and `latent_residual_ids`. A link does not turn the frontier node into a residual. A single address cannot occur in more than one frontier class.

```json
{
  "address": "F0:C3.1",
  "modal_status": "[◇]",
  "expansion_requirement": "required|latent",
  "residual_ids": [],
  "latent_residual_ids": []
}
```

`required` is `P_t^req`: current parent closure must open/realize it or replace it with a valid interface. `latent` is `P_t^latent`: legal and reopenable but not required this round. Relative closure requires `P_t^req=∅`, not an empty Expansion frontier.

Modal meanings are operational:

- `[+]`: realized legal address; it must occur in `panorama.explored` and not in a frontier.
- `[◇]`: legal potential, action candidate, expansion candidate, or compressed interface.
- `[-]`: prohibited result recorded in `panorama.modal_results` or a residual audit.
- `[∅]`: result that the field cannot independently generate or legally express; it is never an ordinary frontier.

Known prohibitions and impossibilities need not be misclassified as true residuals. `panorama.modal_results` stores stable `[-]` and `[∅]` findings separately from motion-produced residuals.

`panorama.latent_residuals` stores `Λ_t`, not active `R_t^a`:

```json
{
  "id": "LR1",
  "classification": "latent-residual",
  "residual_type": "structural",
  "description": "future material",
  "potential_effect_on_f0": "what changes if activated",
  "activation_condition": "upper-level goal or reality trigger",
  "produced_by": {"motion": "FOCUS", "address": "F0:C3.1"},
  "modal_status": "[◇]",
  "possible_destination": "downward-expansion",
  "evidence_status": "inferred",
  "activation_status": "latent",
  "address_relation": {
    "kind": "frontier",
    "address": "F0:C3.1",
    "gate_status": "legal",
    "reach": {
      "kind": "finite-deep",
      "estimated_expansions": 2,
      "evidence_status": "inferred"
    },
    "conflict_with": []
  }
}
```

An audited motion may add `latent_residuals`, activate entries with `activated_latent_residuals`, or disposition them with `absorbed_latent_residuals`. Activation names the new active residual ID. The helper moves the old record to `latent_residual_history` with transition version and provenance; it never deletes lineage. Latent records may remain at closure because their activation condition has not occurred.

### Global Expansion and Focus 2.2

Both operations consume a full motion delta:

```json
{
  "source_panorama_version": 0,
  "graph_nodes": [],
  "graph_relations": [],
  "realized_addresses": [],
  "frontiers_after": {"action": [], "expansion": [], "compressed": []},
  "residuals": [],
  "absorbed_residuals": [],
  "latent_residuals": [],
  "activated_latent_residuals": [],
  "absorbed_latent_residuals": [],
  "empty_residual_reason": "required when residuals is empty",
  "modal_results": [],
  "evidence": [],
  "center_update": null,
  "field_update": null
}
```

For every non-`EXECUTE` motion, `realized_addresses` must be an empty list. `GLOBAL_EXPAND` additionally requires:

```json
{
  "eligible_addresses": ["F0:A1"],
  "expanded_addresses": ["F0:A1"],
  "deferred": [
    {"address": "F0:B1", "reason": "budget|depth-bound|cost-bound|locked|precondition", "detail": ""}
  ]
}
```

`eligible_addresses` must equal the entire current Expansion frontier, not a caller-selected subset. Every eligible address must be expanded or explicitly deferred, and no address may occur in both sets. Every expanded source must leave the Expansion frontier and produce at least one traceable one-level child (`parent_address` or canonical next address segment); every deferred source stays in that frontier. A motion with an empty eligibility set or no structural/state change is rejected. A fully covered round advances `global_expansion.resolution_level`; a bounded round retains the level and its deferrals. Task scores cannot silently select Global Expansion branches.

For `FOCUS`, the same delta may open several paths to unequal depths. The command also supplies `active_paths`; every active address remains `[◇]`, belongs to the selected center root, and passes the recomputed structural ancestry gate. Focus selects legal potential routes; it does not claim that they have executed. Focus-generated nodes and supporting relations are written into `G`, the derived order, and the panorama in the same atomic transition. Focus weights decide only which already-legal address continues and how deeply; they never determine root legality, center necessity, or dependency priority.

### Execution audit and invalidation

An `EXECUTE` transition accepts:

```json
{
  "snapshot_version": 0,
  "completed": [],
  "blocked": [],
  "realized_addresses": [],
  "evidence": [],
  "residuals": [],
  "absorbed_residuals": [],
  "latent_residuals": [],
  "activated_latent_residuals": [],
  "absorbed_latent_residuals": [],
  "empty_residual_reason": "required when residuals is empty",
  "modal_results": [],
  "frontiers_after": {"action": [], "expansion": [], "compressed": []},
  "precondition_gaps": [],
  "absorbed_outcomes": [],
  "invalidations": [],
  "residual_driven_decision": "CONTINUE_EXECUTION"
}
```

Completion and blockage records must identify existing Action addresses, include evidence, and reference stored or supplied IDs. `realized_addresses` exactly equals completed addresses; blocked ones stay unrealized. Addressed items leave the Action frontier. Execution queue, panorama, active/latent residual transitions, and history update atomically. Execute is rejected while the F0 gate is open; an active `[-]` or `[∅]` must first be dispositioned.

Before execution, the helper derives an executable sub-poset from Action paths plus all required predecessors and preserved interfaces:

```json
{
  "subgraph": {"nodes": [], "relations": [], "join_nodes": []},
  "node_status": {"F0:A": "satisfied|locked|compressed-valid|pending|active|completed|blocked"},
  "ready": [],
  "queue": []
}
```

`F0` is the root-goal contract and numeric suffixes navigate task-relative recursive addresses. An Action or active Focus item with a numeric suffix additionally requires `field_opening_status=validated`. An Action item is ready only when each ordinary required predecessor is valid and `[+]`, or is preserved by a valid required compressed interface that is not marked `reopen-required`. Expansion items may be structurally legal while their child opening remains hypothesized/forming; they are not execution-ready. Execution follows the necessary partial order: all currently ready incomparable nodes may run in parallel, while multi-predecessor nodes remain explicit joins.

Each invalidation contains `address`, `reason`, a required existing `evidence_id`, and `result_modal` (`[◇]`, `[-]`, or `[∅]`). The helper:

1. invalidates the named address;
2. marks required dependency descendants stale;
3. removes affected nodes from the current necessary order without deleting them from `G`;
4. revokes affected `[+]` realizations;
5. blocks affected execution work;
6. marks affected center candidates stale and clears an affected selection;
7. changes affected compressed interfaces to `reopen-required`;
8. recomputes Focus gates and records the propagation in the event.

### Residuals, addresses, and SCC analysis

Residual types are `structural`, `non-poset`, `execution-failure`, `unexpected-result`, `unmet-premise`, and `invalidation`. `panorama.residuals` stores active `R_t^a`; `residual_history` stores absorbed active records; `latent_residuals` stores `Λ_t`; `latent_residual_history` preserves activation or disposition. Address state, frontier requirement, residual activity, and absorption are independent.

Each active residual additionally requires:

```json
{
  "address_relation": {
    "kind": "realized|frontier|hypothesized|negative|no-address",
    "address": null,
    "gate_status": "legal|unverified|conflicting|out-of-field",
    "reach": {
      "kind": "realized|next|finite-deep|unknown|unreachable",
      "estimated_expansions": null,
      "evidence_status": "explicit|inferred|tentative|unknown"
    },
    "conflict_with": []
  },
  "absorption_status": "unresolved|partially-absorbed|tolerated|human-pending|prohibited",
  "closure_condition": "what would actually absorb or disposition the difference"
}
```

`[◇, reach=next]` is likely to be absorbed by the next legal expansion; `finite-deep` requires more than one estimated expansion; `unknown` is only a hypothesis. `[-]` records a structural conflict or prohibition. `[∅]` means the current field has no legal expression, generation route, or guarantee; it is never a synonym for “not expanded yet.” When absorbed, the record moves to `residual_history` with `absorption_status=absorbed`, `absorbed_by` (motion, address, evidence IDs, reason), and `absorbed_at_version`.

SCC residual identifiers are deterministic for the same member set. Each cyclic component records its members, internal required-relation IDs, classification `non-poset`, and residual ID. Validation recomputes SCCs and rejects stale analysis or a missing residual.

### Drift audit

```json
{
  "baseline": {
    "root_goal": "...",
    "immutable_constraints": [],
    "version": 0
  },
  "policy": {
    "require_goal_identity": true,
    "require_immutable_constraint_retention": true,
    "min_address_retention": 0.8,
    "max_dependency_churn": 0.5
  },
  "audits": [
    {
      "id": "D1",
      "motion": "FOCUS",
      "source_version": 0,
      "target_version": 1,
      "changes": {
        "goal_changed": false,
        "dropped_immutable_constraints": [],
        "selected_center_changed": false,
        "added_addresses": [],
        "removed_addresses": [],
        "added_dependencies": [],
        "removed_dependencies": []
      },
      "metrics": {
        "goal_identity": 1.0,
        "immutable_constraint_retention": 1.0,
        "selected_center_retention": null,
        "address_retention": 1.0,
        "dependency_churn": 0.0,
        "invalidated_realized_count": 0,
        "stale_active_path_count": 0
      },
      "status": "pass|warn|fail",
      "reasons": [],
      "timestamp": "ISO-8601"
    }
  ]
}
```

Goal replacement or removal of an immutable constraint is a drift failure and blocks commit. Center replacement, address loss, dependency churn over policy, invalidated realizations, or stale active paths produces at least a warning. Each committed joint-motion event references exactly one drift audit whose motion, source version, and target version match that event; unbound audits and persisted `fail` audits are invalid.

### Compatibility 2.2

- `validate` and `summary` accept schemas `1.0`, `1.1`, `1.2`, `1.3`, `2.0`, `2.1`, and `2.2`.
- `focus`, update commands, and state-changing `transition` commands accept schema `2.2` only.
- The helper never inserts missing 2.2 address-dynamics fields into an older state and never writes an older state.
- Schemas `2.0` and `2.1` remain read-only; `2.0` retains `ancestor_goal` and `2.1` retains its field-formation surface without inferred maintenance history.
- Migration requires an explicit future migration tool and independent evidence reconstruction; it is not performed by this helper.

## Legacy schemas 1.0 through 1.3 (read-only)

The following sections retain the legacy schema contract for validation and interpretation. Schema `1.3` added mandatory post-motion residual audits and modal address states. Schema `1.2` distinguished Global Expansion from Focus Penetration and added F0-facing display addresses, panorama write-back, locked interfaces, and strict residual categories. Schema `1.1` retained the explicit dependency partial order and structural-legality gate.

## Required top-level keys

```json
{
  "schema_version": "1.3",
  "version": 0,
  "field": {},
  "center": {},
  "focus": {},
  "panorama": {},
  "execution": {},
  "evidence": [],
  "history": []
}
```

## Field

```json
{
  "id": "F0",
  "name": "task field",
  "ancestor_goal": "the result this run ultimately serves",
  "boundary": {
    "included": [],
    "excluded": []
  },
  "success_criteria": [],
  "immutable_constraints": [],
  "allowed_changes": [],
  "legal_roots": ["F0"],
  "tolerance": {
    "criterion": null,
    "threshold": null
  },
  "status": "survey"
}
```

`legal_roots` defines the permitted roots of task addresses. `tolerance` records the criterion under which a difference remains compressed or must return as a residual; it is not a task score.

## Dependency order

Store the explored dependency partial order in `panorama.order`:

```json
{
  "status": "unvalidated|tentative|validated|invalid",
  "nodes": [
    {"address": "F0", "function": "task root", "evidence_status": "explicit", "modal_status": "[+]"}
  ],
  "relations": [
    {
      "id": "r1",
      "predecessor": "F0",
      "successor": "F0:A",
      "necessity": "required|conditional",
      "evidence_status": "explicit|inferred|tentative|unknown"
    }
  ],
  "explicit_incomparables": [
    ["F0:M1", "F0:M2"]
  ]
}
```

Relations within one model version must form a directed acyclic graph. Absence of a relation means unknown or currently unrepresented, not proven incomparability; record known incomparable pairs explicitly. Feedback is versioned as `O_t -> ... -> O_(t+1)` and must not be inserted as a cycle in one version's order.

In schema `1.3`, order nodes use `[+]` when realized in `M_t` and `[◇]` when they are legal potential addresses retained in `Frontier_t`. Do not store `[-]` or `[∅]` as legal order nodes; those modal results belong in the residual audit or residual ledger.

## Center

```json
{
  "status": "tentative",
  "members": ["F0:A"],
  "relation_ids": [],
  "minimality_status": "unvalidated|validated|invalid",
  "spine": [
    {"id": "A", "function": "", "evidence_status": "unknown"}
  ],
  "branches": {
    "A": []
  }
}
```

The center is the non-deletable minimum load-bearing dependency sub-poset for the current field. `members` and `relation_ids` must reference nodes and relations in `panorama.order`. `spine` remains only as a schema-1.0-compatible display or simple-chain view; it must not be used to force incomparable center members into a linear sequence. Branches store implementations, conditions, variation axes, or compressed child fields. Do not use branch count as importance.

## F0-facing address convention

Store a canonical parent-facing address with the containing field prefix, for example `F0:B1.1.2.3`, and render it in that field's Focus view as `B1.1.2.3`. The root letter identifies a center-axis position; each numeric segment records one returned recursive penetration step. Several active addresses may share the same root letter. A fully opened child field keeps a unique `field_id`, parent binding, local letter center, internal breadcrumb, and `field_opening_audit`. While it is the current object of attention, render that child as the active local `F0`; when returning to the containing field, substitute its validated local center into the current S-state and retain the parent as the protected interface and reopen address. Never represent child fields as parallel F-layers; S0-Sn name active sub-poset states, not child identities.

## Focus

```json
{
  "query": null,
  "address": null,
  "rationale": null,
  "source": "user|evidence|agent-tentative",
  "active_paths": [
    {
      "address": "F0:B1.1.2.3",
      "display_address": "B1.1.2.3",
      "modal_status": "[+]",
      "root_ancestry": {
        "root_address": "F0",
        "node_addresses": ["F0", "F0:A", "F0:B", "F0:B1", "F0:B1.1", "F0:B1.1.2", "F0:B1.1.2.3"],
        "relation_ids": ["r1", "r2", "r3", "r4", "r5", "r6"],
        "compressed_ancestor_addresses": ["F0:A"]
      },
      "required_predecessors": ["F0", "F0:A", "F0:B", "F0:B1", "F0:B1.1", "F0:B1.1.2"],
      "structural_necessity": "center|required-predecessor|optional|unknown",
      "dependency_readiness": "ready|blocked|unknown",
      "focus_depth": 4,
      "gate_status": "legal|illegal|unverified",
      "gate_reasons": []
    }
  ],
  "penetration": {
    "source_panorama_version": 2,
    "written_panorama_version": 3,
    "new_addresses": ["F0:B1.1.2", "F0:B1.1.2.3"],
    "locked_interface_addresses": ["F0:A"]
  },
  "status": "unfocused"
}
```

`root_ancestry` stores the complete root-path sub-DAG, not a flattened chain. It must retain every required predecessor, including incomparable predecessors that meet at a join. A compressed predecessor remains in `compressed_ancestor_addresses` and keeps its structural role through the corresponding compressed-interface record. The helper recomputes `required_predecessors`, `dependency_readiness`, and `gate_status`; callers must not self-certify a path as legal.

For schema `1.2+`, the helper also derives `display_address` and `focus_depth` from the canonical F0 address. `penetration.new_addresses` is the address component of `ΔM_focus` for the round; supporting relations are written into `panorama.order.relations` by the same delta operation. Every listed address must be present in the written panorama order and `explored` set. `written_panorama_version` records the version produced by the latest Focus write-back: immediately after Focus it equals `panorama.map_version`, and it may remain lower after later Global Expansion. It must never exceed the current map version. Focus may list multiple active paths under the same root letter.

A plain legacy path carried into schema `1.1` additionally records `"ancestry_source": "legacy-plain"`; the helper keeps it `unverified` until a structured ancestry replaces it.

## Panorama

For every audited motion, interpret the panorama state as:

```text
S_t = M_t + R_t + Frontier_t
M_t        = panorama.explored plus its realized order nodes
R_t        = panorama.residuals
Frontier_t = panorama.frontier
```

`M_t` contains realized legal structure, not every conceivable candidate. `Frontier_t` contains legal but unexpanded, compressed, locked, or deprioritized addresses. `R_t` contains only motion-exposed differences that currently cannot be absorbed, explained, or resolved without distortion.

```json
{
  "map_version": 0,
  "global_expansion": {
    "resolution_level": 0,
    "status": "bounded|active|complete",
    "last_uniform_expansion_version": 0
  },
  "explored": [],
  "frontier": [],
  "compressed": [],
  "external": [],
  "residuals": [],
  "order": {
    "status": "unvalidated",
    "nodes": [],
    "relations": [],
    "explicit_incomparables": []
  }
}
```

`global_expansion.resolution_level` is a legacy numeric count of completed uniform panorama rounds. It does not define named field snapshots or redefine the root field. Global Expansion conceptually advances every legal expandable center node or current legal frontier one level; task or propagation weights must not select its branches. Depth and cost may bound the actual run.

Each schema-1.1+ frontier item uses the same canonical `address` and `root_ancestry` structure as an active path and separates four variables that must not substitute for one another. Schema 1.2+ additionally requires the derived F0-facing `display_address`; schema 1.3 requires modal status `[◇]`:

```json
{
  "address": "F0:C3.1",
  "display_address": "C3.1",
  "modal_status": "[◇]",
  "root_ancestry": {},
  "required_predecessors": [],
  "gate_status": "legal|illegal|unverified",
  "gate_reasons": [],
  "structural_necessity": "center|required-predecessor|optional|unknown",
  "dependency_readiness": "ready|blocked|unknown",
  "focus_depth": 0,
  "task_scores": {
    "relevance": null,
    "impact": null,
    "heat": null,
    "cost": null,
    "priority": null
  },
  "status": "candidate"
}
```

Only a candidate whose computed `gate_status` is `legal` may receive a non-null task `priority` or enter execution. Structural necessity, dependency readiness, Focus depth, and task scores are distinct variables.

Each compressed interface should include:

```json
{
  "address": "F0:A",
  "structural_status": "required-ancestor|optional",
  "exposure_status": "compressed|locked",
  "contract": {
    "inputs": [],
    "outputs": [],
    "conditions": [],
    "uncertainty": null
  },
  "reopen_address": "F0:A / child-field",
  "evidence_status": "explicit|inferred|tentative|unknown"
}
```

Compression changes visible depth, not structural priority. A required compressed predecessor/interface must still appear in every affected active path's stored root path.

`locked` means a hard constraint forbids current mutation or expansion while preserving the contract and `reopen_address`. It does not lower structural necessity or dependency priority and does not prevent a later Focus from reopening the interface.

Each schema-1.3 residual records:

```json
{
  "id": "R7",
  "classification": "true-residual",
  "residual_type": "structural|execution-failure|unexpected-result|unmet-premise",
  "description": "",
  "origin": "external-encounter|closure-produced|compression-return|unknown-origin",
  "produced_by": {
    "motion": "GLOBAL_EXPAND|FOCUS|EXECUTE",
    "address": "F0:C3.1"
  },
  "failing_address": null,
  "effect_on_f0": "",
  "representation_failure": "why the current center, boundary, or address grammar cannot absorb this without distortion",
  "modal_status": "[◇]|[-]|[∅]",
  "possible_destination": "downward-expansion|field-ascension|in-field-remodel|remain-external|prohibit",
  "changes_focus_or_execution": {
    "changes": true,
    "reason": ""
  },
  "tolerance_status": "below|near|above|unknown",
  "evidence_status": "explicit|inferred|tentative|unknown"
}
```

Do not place an existing address, a legal but unexpanded frontier, a Focus-deprioritized legal branch, or irrelevant external information in `residuals`. Store irrelevant external information in `panorama.external`. A schema-1.2 residual must have both a non-empty `effect_on_f0` and a non-empty `representation_failure`; schema 1.3 also requires the identifier, producing motion/address, modal status, possible destination, and scheduling effect. A temporarily missing input or execution prerequisite belongs in the motion audit's `precondition_gaps` unless evidence shows that the field cannot absorb it.

Modal semantics are:

- `[+]`: realized legal address in `M_t`;
- `[◇]`: compatible potential that may be absorbed through expansion, compression, or field ascension;
- `[-]`: result prohibited by an irreducible current-field principle;
- `[∅]`: result the current field cannot independently generate, guarantee, or yet express legally.

Never mark an ordinary unexpanded address `[∅]`; it is `[◇]` frontier.

## Execution

```json
{
  "snapshot_version": 0,
  "queue": [],
  "active": null,
  "completed": [],
  "blocked": [],
  "last_decision": null
}
```

Execution references a model version. After each coherent batch, update the model before choosing the next batch.

## Evidence levels

- `explicit`: directly present in code, data, source, observation, or verified result;
- `inferred`: supported by interfaces, dependency, or reliable comparison;
- `tentative`: testable working hypothesis with limited evidence;
- `unknown`: insufficient material.

## Event record

```json
{
  "version": 1,
  "type": "FOCUS",
  "address": "F0:C3.1",
  "note": "why this transition occurred",
  "residual_audit": {
    "performed": true,
    "motion": "FOCUS",
    "scope": "simple|complex",
    "delta_m_addresses": ["F0:C3.1"],
    "delta_r_ids": ["R7"],
    "frontier_after_addresses": ["F0:B2.1"],
    "compressed_frontier_addresses": ["F0:B2.1"],
    "precondition_gaps": [],
    "absorbed_outcomes": [],
    "checks": {
      "unexplained_omissions_checked": true,
      "flattening_checked": true,
      "external_misclassification_checked": true,
      "frontier_residual_confusion_checked": true
    },
    "empty_residual_reason": null,
    "residual_driven_decision": "FOCUS_REQUIRED"
  },
  "timestamp": "ISO-8601"
}
```

Allowed event types are `SURVEY`, `GLOBAL_EXPAND`, `FOCUS`, `EXPAND`, `COMPRESS`, `PROMOTE`, `SPLIT`, `REBUILD`, `EXECUTE`, `AUDIT`, `HANDOFF`, `STOP`, and `REMODEL_REQUIRED`.

Schema 1.3 requires `residual_audit` on every successful `GLOBAL_EXPAND`, `FOCUS`, and `EXECUTE` event. The command input may provide full `delta_r` records and a full `frontier_after`; the helper writes those into `panorama.residuals` and `panorama.frontier`, then stores only their identifiers or addresses in the event.

`precondition_gaps` distinguishes temporary missing inputs or execution prerequisites from residuals. `absorbed_outcomes` records failures, conflicts, or surprises that the existing field successfully explained or repaired and therefore did not enter `R_t`. All four checks must be explicit. For a complex motion with no `delta_r_ids`, `empty_residual_reason` must explain why the current structure and tolerance absorbed all relevant outcomes; this rule prevents silent closure but does not require inventing a residual.

Allowed decisions include `F0_CONFIRMATION_REQUIRED`, `FIELD_FORMATION_REQUIRED`, `HUMAN_CALIBRATION_REQUIRED`, `CONTINUE_EXECUTION`, `FOCUS_REQUIRED`, `EXPAND_REQUIRED`, `REMODEL_REQUIRED`, `FIELD_ASCENSION_REQUIRED`, `F0_COMPLETE`, and `BLOCKED`. A freshly initialized schema-2.2 field starts with `FIELD_FORMATION_REQUIRED`; only a candidate that passes formation changes to `F0_CONFIRMATION_REQUIRED`.

## Compatibility

- Read, validate, and summarize schema `1.0` without adding fields or changing the file.
- Do not infer a dependency order or complete root path from a legacy `spine` or string `active_paths`.
- A new `focus` request against schema `1.0` must record `REMODEL_REQUIRED`, not `FOCUS`; reconstruct the dependency order in schema `1.1+` before treating any path as active, use `1.2+` when Focus must generate and write back addresses, and use `1.3` when the run must also preserve residual audits and modal state.
- A legacy string path carried into schema `1.1` is `unverified`, never automatically `legal`.
- Reconstruct and validate the order before scoring or executing a legacy active path. If ancestry cannot be recovered, keep the candidate and emit `REMODEL_REQUIRED`.
- Read, validate, and summarize schema `1.1` with its order and gate semantics, but do not infer `ΔM_focus`, F0 display addresses, locked-interface state, or panorama write-back that it did not record.
- Read, validate, and summarize schema `1.2` with Focus generation and write-back semantics, but do not infer modal status or a post-motion residual audit that it did not record.
- `--focus-delta-json` requires schema `1.2` or `1.3`. Do not silently convert an earlier state.
- `--residual-audit-json` is required for successful Global Expansion, Focus, and Execute motions in schema `1.3`. It does not silently migrate schema 1.2.
