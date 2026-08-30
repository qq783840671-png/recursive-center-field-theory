# Address Engine State

Use this compact JSON-compatible shape for persisted or exchanged engine state. Do not invent missing semantic evidence merely to satisfy the shape.

```yaml
engine_version: "0.5-experimental"
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
  formation_confirmation_status: "confirmed | reused"
  formation_confirmation_evidence_refs: ["evidence identity"]

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

address_candidates:
  - candidate_address_id: "candidate identity"
    calibration_status: "hypothesized | calibrating | calibrated | rejected"
    proposed_structural_role: "role hypothesis"
    evidence_refs: []
    counterevidence_refs: []
    resulting_address_id: null

addresses:
  - address_id: "version-specific-address-identity"
    object_id: "stable-object-identity"
    display_path: "B1.2"
    path_tokens: ["B", "1", "2"]
    role: "field-relative identity"
    calibration_status: "calibrated"
    modal: "realized | potential"
    lifecycle: "active | historical | retired"
    root_path_nodes: ["F0", "F0:B", "F0:B1", "F0:B1.2"]
    root_path_relation_ids: ["D1", "D2", "D3"]
    predecessor_state:
      status: "satisfied | valid-interface | missing | disputed"
      refs: []
    parent_binding: null
    # Recursive addresses require:
    # parent_binding: {parent_field_id, parent_address, required_function, parent_return}
    relation_roles: ["dependency"]
    contribution_annotation: null
    # Optional only with a decomposition contract and evidence:
    # {decomposition_contract_ref, conditional_interval: [0.0, 0.2],
    #  residual_share_interval: [0.0, 0.1], evidence_refs: [...]}
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
        frontiers: {action: [], expansion_required: [], expansion_latent: [], compressed: []}
        residuals: []
        residual_audit: {status: "performed"}
        return_interface: {status: "valid", parent_address: "F0:B1"}
      state_hash: "canonical sha256 of state_snapshot"
      evidence_refs: ["evidence identity"]

frontiers:
  action:
    - {address_id: "potential-address-id", evidence_refs: ["evidence identity"]}
  expansion_required: []
  expansion_latent:
    - {address_id: "potential-address-id", evidence_refs: ["evidence identity"]}
  compressed: []

residual_links:
  - residual_id: "residual identity"
    classification: "latent-residual | active-residual"
    address_binding:
      kind: "bound | candidate | unaddressed"
      address_id: null
      candidate_address_id: null
    activation_condition: null
    addressing_result: null  # when present, modality is [-] or [∅]
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
- `[◇]` may live in a typed action or expansion frontier only after calibration. A candidate carries calibration state, not modality. A residual may bind the address, but the residual itself is not `[◇]`.
- `expansion_required` records current parent-field obligations; provisional closure requires it to be empty. `expansion_latent` may remain non-empty and is not automatically a latent residual.
- Engine 0.3 unified `frontier` states and 0.4 states remain readable for migration, but only 0.5 states can establish the current candidate／residual partition and typed provisional closure.
- A realized address requires a stable field and `satisfied` or `valid-interface` predecessors.
- Engine 0.5 address motion requires an evidence-bound `confirmed` or `reused` field-formation authorization.
- `MAP`, `GLOBAL`, `FOCUS`, and `REALIZE` require stable contract plus validated graph, order, center, and a positive audited `formation_revision`.
- Every adjacent root-path step must be covered in forward direction by a valid required dependency relation whose evidence resolves in `evidence`.
- Every proposed numeric recursive node starts in `address_candidates`. `hypothesized`/`forming` carry no legal-address modality and cannot support closure, execution, or realization. `validated` creates a legal `[◇]` address and requires an evidence-bound inline `state_snapshot`; validators recompute its canonical hash and check the child graph, order, center, residual audit, and return binding.
- Relative closure requires `expansion_required` to be empty and blocking active residuals to be absent. Latent residuals may remain with `bound`, `candidate`, or `unaddressed` bindings.
- Conditional contribution annotations never legalize an address. They require a decomposition contract, evidence, and bounded intervals; serial necessity, interactions, thresholds, and causal amplification stay separate.
- `display_path` is a view; exchange `path_tokens`, typed root-path edges, identities, and versions.
- Preserve retired addresses and old revisions as lineage.

Use `address_engine.py closure-audit STATE` to derive the provisional-closure gate. `validate` checks state consistency; neither command proves that the cited domain evidence is true.
