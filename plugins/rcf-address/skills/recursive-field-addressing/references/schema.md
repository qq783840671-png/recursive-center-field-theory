# Address Engine State

Use this compact JSON-compatible shape for persisted or exchanged engine state. Do not invent missing semantic evidence merely to satisfy the shape.

```yaml
engine_version: "0.3-experimental"
revision: 1

field:
  field_id: "stable-field-identity"
  field_version: "closure-qualified-version"
  f0_lineage: "logical-root-lineage"
  contract_status: "candidate | confirmed | stable"
  graph_status: "forming | tentative | validated | invalid"
  order_status: "forming | tentative | validated | invalid"
  center_status: "candidate | selected | validated | disputed | invalid"
  formation_revision: 1

evidence:
  - id: "evidence identity"
    source: "source reference"

dependency_relations:
  - id: "D1"
    source: "F0"
    target: "F0:B"
    necessity: "required"
    validity: "valid"
    evidence_refs: ["evidence identity"]
  - id: "D2"
    source: "F0:B"
    target: "F0:B1"
    necessity: "required"
    validity: "valid"
    evidence_refs: ["evidence identity"]
  - id: "D3"
    source: "F0:B1"
    target: "F0:B1.2"
    necessity: "required"
    validity: "valid"
    evidence_refs: ["evidence identity"]

intake:
  - intake_id: "raw-item-identity"
    raw_content: "unaltered input"
    source: "source reference"
    status: "pending | mapped | external | residual"

objects:
  - object_id: "stable-object-identity"
    intake_refs: []
    object_type: "concept | relation | action | evidence | interface"
    provenance: "source reference"
    evidence_status: "explicit | inferred | hypothesized | disputed"

addresses:
  - address_id: "version-specific-address-identity"
    object_id: "stable-object-identity"
    display_path: "B1.2"
    path_tokens: ["B", "1", "2"]
    role: "field-relative identity"
    modal: "realized | potential | prohibited"
    lifecycle: "active | historical | retired"
    root_path_nodes: ["F0", "F0:B", "F0:B1", "F0:B1.2"]
    root_path_relation_ids: ["D1", "D2", "D3"]
    predecessor_state:
      status: "satisfied | valid-interface | missing | disputed"
      refs: []
    parent_binding: null
    interface_contract_ref: null
    reopen_ref: null
    evidence_refs: ["evidence identity"]
    field_opening_status: "hypothesized | forming | validated"
    field_opening_audit:
      field_id: "child-field identity"
      local_root: "F0"
      parent_address: "F0:B1"
      contract_status: "stable"
      graph_status: "validated"
      order_status: "validated"
      center_status: "validated"
      recursive_structure_status: "validated"
      residual_audit_status: "performed"
      return_interface_status: "valid"
      state_ref: "logical reference for the inline child state"
      state_snapshot:
        field: {field_id: "child-field identity", local_root: "F0", parent_address: "F0:B1", contract_status: "stable"}
        graph: {status: "validated", nodes: [{address: "F0"}], relations: []}
        order: {status: "validated", nodes: ["F0"], relations: []}
        center: {status: "validated", selected: "K1", candidates: [{id: "K1", members: ["F0"], minimality_status: "validated"}]}
        recursive_structure_status: "validated"
        frontiers: {action: [], expansion: [], compressed: []}
        residuals: []
        residual_audit: {status: "performed"}
        return_interface: {status: "valid", parent_address: "F0:B1"}
      state_hash: "canonical sha256 of state_snapshot"
      evidence_refs: ["evidence identity"]

frontier:
  - address_id: "potential-address-id"
    reach: "next | finite-deep | unknown"
    compression_state: "compressed | locked | deferred"

residual_links:
  - residual_id: "residual identity"
    address_ref: null
    modal: "realized | potential | prohibited | no-address"
    relation_kind: "frontier | hypothesized"
    gate_status: "legal | unverified | illegal"
    reach:
      kind: "next | finite-deep | unknown | unreachable"
      estimated_expansions: null
      evidence_refs: []
    absorption_state: "unabsorbed | partial | tolerated | absorbed | prohibited"
    reason: "current representation failure"
    possible_destination: "expand | rebuild | ascend | external | prohibit"

history:
  - motion_id: "engine motion identity"
    motion_type: "INGEST | FORM | MAP | GLOBAL | FOCUS | ABSORB | REALIZE | REBUILD | ASCEND"
    source_revision: 0
    result_revision: 1
    evidence_ref: "source of the state change"
```

Rules:

- `[∅]` uses `modal: no-address` and `address_ref: null`; never fabricate an address record.
- `[◇]` lives in `frontier`; an unresolved residual may also point to it until absorption is verified.
- A realized address requires a stable field and `satisfied` or `valid-interface` predecessors.
- `MAP`, `GLOBAL`, `FOCUS`, and `REALIZE` require stable contract plus validated graph, order, center, and a positive audited `formation_revision`.
- Every adjacent root-path step must be covered in forward direction by a valid required dependency relation whose evidence resolves in `evidence`.
- Every numeric recursive node requires `field_opening_status` and `field_opening_audit`. `hypothesized`/`forming` remain potential Frontier hypotheses and cannot support closure, execution, or realization. `validated` requires an evidence-bound inline `state_snapshot`; validators recompute its canonical hash and check the child graph, order, center, residual audit, and return binding.
- A potential supports provisional closure only when `relation_kind=frontier`, `gate_status=legal`, reach is evidence-supported `next` or bounded `finite-deep`, and the active address remains in Frontier. `hypothesized` or `unknown` is `[◇,d=?]` and remains open.
- `display_path` is a view; exchange `path_tokens`, typed root-path edges, identities, and versions.
- Preserve retired addresses and old revisions as lineage.

Use `address_engine.py closure-audit STATE` to derive the provisional-closure gate. `validate` checks state consistency; neither command proves that the cited domain evidence is true.
