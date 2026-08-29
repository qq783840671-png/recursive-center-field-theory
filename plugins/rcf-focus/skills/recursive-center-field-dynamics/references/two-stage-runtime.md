# Two-stage Focus runtime

Use this reference only when constructing payloads for `scripts/focus_runtime.py`, debugging a rejected transition, or inspecting persisted `focus-two-stage-1.1` state.

## Runtime chain

```text
init
→ register-candidate → resolve-candidate   # optional calibration ledger
→ frame                         # Focus-1: contract, full field, center projection
→ expand | execute              # Focus-2: open one necessary position or act
→ execute | expand              # continue only when the current gap requires it
→ fold
→ activate-residual             # when a latent difference is triggered
→ unwind                        # required before returning a child to its parent
→ summary | validate
```

`Focus-1/Focus-2` are operating phases, not global `F1/F2` depths. Every successful `expand` increases the child field's global depth by exactly one. There is no fixed round count or fixed child-center width.

Pass a JSON object directly or use `@path/to/payload.json`.

## Initialize

```powershell
python scripts/focus_runtime.py init STATE --task "任务" --mode clarify
```

Modes are `clarify` and `action`.

## Focus-1 `frame`

Minimum payload:

```json
{
  "field_id": "task-field",
  "contract": {
    "goal": "当前要闭合的目标",
    "boundary": "包含与排除的范围",
    "completion": "什么算完成",
    "evidence_standard": "什么证据足够",
    "constraints": []
  },
  "closure_gap": "当前真正阻断闭合的差异",
  "centers": [
    {
      "center_id": "c-main",
      "label": "当前活动中心",
      "status": "active",
      "obligation": "该中心承担的不可替代义务",
      "nodes": [
        {"node_id": "n1", "role": "必要功能位置", "frontier_class": "none"}
      ]
    },
    {
      "center_id": "c-peer",
      "status": "candidate",
      "obligation": "平级候选义务",
      "nodes": [
        {"node_id": "p1", "role": "平级功能位置"}
      ]
    }
  ],
  "selected_center_id": "c-main",
  "peer_center_ids": ["c-peer"],
  "order": [],
  "center_relations": [],
  "join_rules": [],
  "confidence": "provisional",
  "projection_assumptions": [],
  "invalidation_triggers": []
}
```

Center statuses: `candidate | active | blocked | closed | invalid`. The selected center must be `active` or `closed`. `peer_center_ids` lists only the unselected centers whose interfaces the current projection must carry; every other center remains in the complete field record but outside the Focus context. If the field omits `peer_center_ids`, the helper conservatively references every non-invalid unselected center.

Node `frontier_class` is `none | expansion_required | expansion_latent | compressed`. The action frontier is derived from calibrated `[◇]` addresses whose predecessors are satisfied; it is independent of expansion and compression classification.

Use `order` only for unconditional necessary precedence:

```json
{"before": "n1", "after": "n2"}
```

Store support, conflict, competition, constraint, aggregation, shared positions and center-level requirements in `center_relations`. The helper rejects cycles in node and center-level required orders.

## Focus-2 `expand`

Open exactly one selected-center address into a complete child field:

```json
{
  "field_id": "child-field",
  "parent_address": "n1",
  "parent_return": {
    "required_function": "父场为什么打开这里",
    "required_output": "子场必须返回什么",
    "closure_requirement": "什么算子场满足父义务",
    "parent_return": "返回父场的接口形式"
  },
  "contract": {
    "goal": "子场目标",
    "boundary": "子场边界",
    "completion": "子场完成条件",
    "evidence_standard": "子场证据标准",
    "constraints": []
  },
  "closure_gap": "子场尚未闭合的差异",
  "centers": [],
  "selected_center_id": "child-center",
  "order": []
}
```

Populate `centers` using the same structure as `frame`. The child may contain one or many candidate/active centers, but the child Focus again selects only one center.

The helper derives:

- `global_depth = parent_depth + 1`;
- unique `primary_parent` and root path;
- stable canonical address IDs;
- full/display/local address views;
- `selected_center_ref`, `peer_center_refs`, and `ProjectionCertificate`;
- field, panorama and address revision identities.

## Execute

```json
{
  "addresses": ["n1"],
  "evidence": ["test-or-analysis-evidence"],
  "result": "executed result"
}
```

The helper accepts node IDs or canonical address IDs. It rejects missing necessary predecessors and unsatisfied joins. Only successful `execute` changes `[◇]` to `[+]`.

Every legal address has `calibration_status=calibrated`. An address hypothesis belongs in `address_candidates`, carries no modality, and can be registered/resolved explicitly with `register-candidate` and `resolve-candidate`.

Supported join types are `ALL`, `ANY`, `K_OF_N`, and evidence-backed `AGGREGATE`.

## Fold and unwind

```json
{
  "conclusion": "当前场的压缩结论",
  "evidence": ["audit evidence"],
  "outputs": ["parent-facing output"],
  "latent_residuals": [
    {
      "residual_id": "lambda-1",
      "description": "尚未激活的差异",
      "activation_condition": "新证据进入",
      "address_binding": {"kind": "unaddressed"}
    }
  ],
  "active_residuals": [
    {
      "residual_id": "r-1",
      "description": "当前阻断差异",
      "blocking": true,
      "address_binding": {"kind": "unaddressed"},
      "addressing_result": {"modality": "[∅]", "reason": "当前场无合法表达路线"}
    }
  ],
  "best": null,
  "upper": null,
  "assumptions": [],
  "peer_interface_effects": [],
  "reprojection_request": null
}
```

`fold` separately computes selected-center closure and full-field closure. The legacy `residuals` field is accepted only when empty; new records must separate latent and active residuals. A latent residual never carries `[◇]`. Use `activate-residual` to route it to `absorbed-local | required-frontier | address-birth | active-residual | externalized`; the active-residual route requires a `[-]` or `[∅]` addressing result. An open peer center prevents full-field closure. For a child field, run `unwind` after `fold`; the helper returns the `FocusReturn`, compresses the child interface, and realizes the parent address only if the complete child field closed.

## Validation boundary

The runtime validates recorded structural consistency, not domain truth. The agent remains responsible for evidence quality, center recovery, boundary choice, and whether an apparent multi-center field passes the theory's irreducibility tests.

Use the legacy `field_state.py` only to validate or reproduce schema-2.2/S0-S3 records. Do not feed a v2 state to the legacy helper.
