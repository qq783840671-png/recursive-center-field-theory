#!/usr/bin/env python3
"""Constructive Focus runtime for the recursive multi-center field model.

The language model retains semantic judgment and execution authority. This helper
persists the live field, validates decisions, invalidates obsolete closure when new
evidence arrives, preserves versions, and controls recursive return. The v0.17
sidecar commands remain available as a compatibility/audit mode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _configure_utf8_stdio() -> None:
    """Keep JSON output writable on Windows runners with legacy code pages."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


_configure_utf8_stdio()


SCHEMA_VERSION = "focus-constructive-2.0"
LEGACY_SCHEMA_VERSION = "focus-two-stage-1.1"
CENTER_STATUSES = {"candidate", "active", "blocked", "closed", "invalid"}
CENTER_RELATIONS = {
    "requires",
    "co_required",
    "constrains",
    "supports",
    "competes",
    "conflicts",
    "aggregates_with",
    "shares_position",
}
JOIN_TYPES = {"ALL", "ANY", "K_OF_N", "AGGREGATE"}
PHASES = {
    "initialized",
    "observed",
    "reconstructed",
    "framed",
    "expanded",
    "executing",
    "folded",
    "closed",
    "blocked",
    "revising",
}
OBSERVATION_KINDS = {"analysis", "read", "write", "tool", "external", "result"}
FRONTIER_KEYS = {"action", "expansion_required", "expansion_latent", "compressed"}
STATIC_FRONTIERS = {"expansion_required", "expansion_latent", "compressed", "none"}
ADDRESS_BINDING_KINDS = {"bound", "candidate", "unaddressed"}
RESIDUAL_DISPOSITIONS = {
    "absorbed-local",
    "required-frontier",
    "address-birth",
    "active-residual",
    "externalized",
}
MODES = {"constructive", "clarify", "action", "sidecar"}
DECISIONS = {
    "CONTINUE",
    "EXPAND_REQUIRED",
    "REVISE_LOCAL",
    "REOPEN_INTERFACE",
    "REFRAME_FIELD",
    "SPLIT_BRANCH",
    "UNWIND",
    "BLOCKED",
    "NOOP",
}
DELTA_KINDS = {"evidence", "failure", "correction", "constraint-change", "goal-change"}
DELTA_CLASSIFICATIONS = {"ADD", "REFINE", "CONTRADICT", "OUTSIDE", "NOOP"}
PROPAGATION_SCOPES = {"none", "local", "interface", "field", "branch"}


class FocusRuntimeError(ValueError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(prefix: str, value: Any, size: int = 16) -> str:
    digest = hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()[:size]
    return f"{prefix}_{digest}"


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FocusRuntimeError(f"{label} must be a non-empty string")
    return value.strip()


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise FocusRuntimeError(f"{label} must be a list")
    return value


def load_json_value(raw: str, label: str) -> dict[str, Any]:
    if raw.startswith("@"):
        path = Path(raw[1:])
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise FocusRuntimeError(f"cannot read {label} file {path}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise FocusRuntimeError(f"invalid JSON in {label} file {path}: {exc}") from exc
    else:
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise FocusRuntimeError(f"invalid {label} JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise FocusRuntimeError(f"{label} must be a JSON object")
    return value


def normalize_observation(payload: dict[str, Any], sequence: int) -> dict[str, Any]:
    raw_request = require_text(payload.get("raw_request"), "observe.raw_request")
    result = require_text(payload.get("result"), "observe.result")
    evidence = require_list(payload.get("evidence", []), "observe.evidence")
    raw_events = require_list(payload.get("events"), "observe.events")
    if not raw_events:
        raise FocusRuntimeError("observe.events must not be empty")
    events: list[dict[str, Any]] = []
    for index, raw_event in enumerate(raw_events):
        if not isinstance(raw_event, dict):
            raise FocusRuntimeError(f"observe.events[{index}] must be an object")
        kind = require_text(raw_event.get("kind"), f"observe.events[{index}].kind")
        if kind not in OBSERVATION_KINDS:
            raise FocusRuntimeError(
                f"observe.events[{index}].kind must be one of {sorted(OBSERVATION_KINDS)}"
            )
        summary = require_text(raw_event.get("summary"), f"observe.events[{index}].summary")
        event_evidence = require_list(
            raw_event.get("evidence", []), f"observe.events[{index}].evidence"
        )
        event_id = raw_event.get("event_id") or stable_hash(
            "traceevt", {"sequence": sequence, "index": index, "kind": kind, "summary": summary}
        )
        events.append(
            {
                "event_id": require_text(event_id, f"observe.events[{index}].event_id"),
                "kind": kind,
                "summary": summary,
                "evidence": event_evidence,
            }
        )
    observation_id = payload.get("observation_id") or stable_hash(
        "obs",
        {
            "sequence": sequence,
            "raw_request": raw_request,
            "events": events,
            "result": result,
            "evidence": evidence,
        },
    )
    return {
        "observation_id": require_text(observation_id, "observe.observation_id"),
        "raw_request": raw_request,
        "events": events,
        "result": result,
        "evidence": evidence,
        "observed_at": now_iso(),
    }


def upgrade_state_in_memory(state: dict[str, Any]) -> dict[str, Any]:
    """Add constructive ledgers to a v0.17 state without rewriting its evidence."""
    if state.get("schema_version") == LEGACY_SCHEMA_VERSION:
        state["schema_version"] = SCHEMA_VERSION
        state["migrated_from"] = LEGACY_SCHEMA_VERSION
    if state.get("schema_version") != SCHEMA_VERSION:
        return state
    state.setdefault("knowledge_deltas", {})
    state.setdefault("decision_history", [])
    state.setdefault("active_decision", None)
    state.setdefault("field_closure_versions", [])
    state.setdefault("version_branches", [])
    state.setdefault("document_revisions", [])
    for address in state.get("addresses", {}).values():
        if isinstance(address, dict):
            address.setdefault("invalidated_by", [])
    for field in state.get("fields", {}).values():
        if isinstance(field, dict):
            field.setdefault("closure_certificates", [])
            field.setdefault("current_closure_version_id", None)
            field.setdefault("invalidation_history", [])
            field.setdefault("claims", {})
    return state


def read_state(path: Path) -> dict[str, Any]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FocusRuntimeError(f"cannot read state {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise FocusRuntimeError(f"invalid state JSON {path}: {exc}") from exc
    if not isinstance(state, dict):
        raise FocusRuntimeError("state root must be an object")
    return upgrade_state_in_memory(state)


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def append_event(state: dict[str, Any], event_type: str, payload: dict[str, Any]) -> None:
    state["revision"] += 1
    state["updated_at"] = now_iso()
    state["history"].append(
        {
            "revision": state["revision"],
            "type": event_type,
            "time": state["updated_at"],
            "payload": payload,
        }
    )


def is_acyclic(nodes: set[str], edges: list[tuple[str, str]]) -> bool:
    incoming = {node: 0 for node in nodes}
    outgoing = {node: [] for node in nodes}
    for before, after in edges:
        if before == after:
            return False
        outgoing[before].append(after)
        incoming[after] += 1
    queue = [node for node, degree in incoming.items() if degree == 0]
    visited = 0
    while queue:
        node = queue.pop()
        visited += 1
        for after in outgoing[node]:
            incoming[after] -= 1
            if incoming[after] == 0:
                queue.append(after)
    return visited == len(nodes)


def normalize_contract(payload: dict[str, Any], label: str) -> dict[str, Any]:
    contract = payload.get("contract")
    if not isinstance(contract, dict):
        raise FocusRuntimeError(f"{label}.contract must be an object")
    normalized = {
        "goal": require_text(contract.get("goal"), f"{label}.contract.goal"),
        "boundary": require_text(contract.get("boundary"), f"{label}.contract.boundary"),
        "completion": require_text(
            contract.get("completion"), f"{label}.contract.completion"
        ),
        "evidence_standard": require_text(
            contract.get("evidence_standard"),
            f"{label}.contract.evidence_standard",
        ),
        "scale": contract.get("scale"),
        "tolerance": contract.get("tolerance"),
        "constraints": require_list(contract.get("constraints", []), f"{label}.contract.constraints"),
    }
    return normalized


def normalize_centers(payload: dict[str, Any], label: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    raw_centers = require_list(payload.get("centers"), f"{label}.centers")
    if not raw_centers:
        raise FocusRuntimeError(f"{label}.centers must not be empty")
    centers: list[dict[str, Any]] = []
    node_defs: dict[str, dict[str, Any]] = {}
    center_ids: set[str] = set()
    for index, raw_center in enumerate(raw_centers):
        if not isinstance(raw_center, dict):
            raise FocusRuntimeError(f"{label}.centers[{index}] must be an object")
        center_id = require_text(raw_center.get("center_id"), f"{label}.centers[{index}].center_id")
        if center_id in center_ids:
            raise FocusRuntimeError(f"duplicate center_id {center_id}")
        center_ids.add(center_id)
        status = raw_center.get("status", "candidate")
        if status not in CENTER_STATUSES:
            raise FocusRuntimeError(f"center {center_id} has invalid status {status!r}")
        obligation = require_text(raw_center.get("obligation"), f"center {center_id}.obligation")
        raw_nodes = require_list(raw_center.get("nodes"), f"center {center_id}.nodes")
        if not raw_nodes:
            raise FocusRuntimeError(f"center {center_id} must contain at least one node")
        node_ids: list[str] = []
        for node_index, raw_node in enumerate(raw_nodes):
            if not isinstance(raw_node, dict):
                raise FocusRuntimeError(f"center {center_id}.nodes[{node_index}] must be an object")
            node_id = require_text(raw_node.get("node_id"), f"center {center_id}.nodes[{node_index}].node_id")
            role = require_text(raw_node.get("role"), f"node {node_id}.role")
            object_id = require_text(raw_node.get("object_id", node_id), f"node {node_id}.object_id")
            frontier_class = raw_node.get("frontier_class", "none")
            if frontier_class not in STATIC_FRONTIERS:
                raise FocusRuntimeError(
                    f"node {node_id}.frontier_class must be expansion_required, "
                    "expansion_latent, compressed, or none"
                )
            normalized_node = {
                "node_id": node_id,
                "role": role,
                "object_id": object_id,
                "claim_id": raw_node.get("claim_id"),
                "claim_content": raw_node.get("claim_content"),
                "claim_status": raw_node.get("claim_status", "provisional"),
                "required_for_closure": bool(raw_node.get("required_for_closure", True)),
                "parallel_binding": raw_node.get("parallel_binding"),
                "evidence": require_list(raw_node.get("evidence", []), f"node {node_id}.evidence"),
                "frontier_class": frontier_class,
            }
            previous = node_defs.get(node_id)
            if previous and (previous["role"], previous["object_id"]) != (role, object_id):
                raise FocusRuntimeError(
                    f"shared node {node_id} must keep the same role and object_id across centers"
                )
            node_defs[node_id] = previous or normalized_node
            node_ids.append(node_id)
        centers.append(
            {
                "center_id": center_id,
                "label": require_text(raw_center.get("label", center_id), f"center {center_id}.label"),
                "status": status,
                "obligation": obligation,
                "closure_status": raw_center.get("closure_status", "open"),
                "interface": raw_center.get("interface"),
                "fail_condition": raw_center.get("fail_condition"),
                "reopen_condition": raw_center.get("reopen_condition"),
                "lineage": raw_center.get("lineage", []),
                "node_ids": node_ids,
                "evidence": require_list(raw_center.get("evidence", []), f"center {center_id}.evidence"),
            }
        )
    return centers, node_defs


def normalize_order(payload: dict[str, Any], node_ids: set[str], label: str) -> list[dict[str, str]]:
    raw_order = require_list(payload.get("order", []), f"{label}.order")
    order: list[dict[str, str]] = []
    edges: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw_edge in enumerate(raw_order):
        if not isinstance(raw_edge, dict):
            raise FocusRuntimeError(f"{label}.order[{index}] must be an object")
        before = require_text(raw_edge.get("before"), f"{label}.order[{index}].before")
        after = require_text(raw_edge.get("after"), f"{label}.order[{index}].after")
        if before not in node_ids or after not in node_ids:
            raise FocusRuntimeError(f"order edge {before}->{after} references an unknown node")
        if (before, after) in seen:
            continue
        seen.add((before, after))
        edges.append((before, after))
        order.append({"before": before, "after": after})
    if not is_acyclic(node_ids, edges):
        raise FocusRuntimeError("required node order must be acyclic")
    return order


def normalize_center_relations(
    payload: dict[str, Any], center_ids: set[str], label: str
) -> list[dict[str, Any]]:
    raw_relations = require_list(payload.get("center_relations", []), f"{label}.center_relations")
    relations: list[dict[str, Any]] = []
    required_edges: list[tuple[str, str]] = []
    for index, raw_relation in enumerate(raw_relations):
        if not isinstance(raw_relation, dict):
            raise FocusRuntimeError(f"{label}.center_relations[{index}] must be an object")
        source = require_text(raw_relation.get("source"), f"center relation {index}.source")
        target = require_text(raw_relation.get("target"), f"center relation {index}.target")
        relation_type = require_text(raw_relation.get("type"), f"center relation {index}.type")
        if source not in center_ids or target not in center_ids:
            raise FocusRuntimeError(f"center relation {source}->{target} references an unknown center")
        if relation_type not in CENTER_RELATIONS:
            raise FocusRuntimeError(f"unsupported center relation type {relation_type!r}")
        if relation_type == "requires":
            required_edges.append((source, target))
        relations.append(
            {
                "source": source,
                "target": target,
                "type": relation_type,
                "evidence": require_list(raw_relation.get("evidence", []), f"center relation {index}.evidence"),
            }
        )
    if required_edges and not is_acyclic(center_ids, required_edges):
        raise FocusRuntimeError("center-level required order must be acyclic")
    return relations


def normalize_join_rules(payload: dict[str, Any], node_ids: set[str], label: str) -> list[dict[str, Any]]:
    raw_rules = require_list(payload.get("join_rules", []), f"{label}.join_rules")
    rules: list[dict[str, Any]] = []
    for index, raw_rule in enumerate(raw_rules):
        if not isinstance(raw_rule, dict):
            raise FocusRuntimeError(f"{label}.join_rules[{index}] must be an object")
        rule_type = require_text(raw_rule.get("type"), f"join rule {index}.type").upper()
        if rule_type not in JOIN_TYPES:
            raise FocusRuntimeError(f"unsupported join rule type {rule_type!r}")
        branches = [require_text(item, f"join rule {index}.branches") for item in require_list(raw_rule.get("branches"), f"join rule {index}.branches")]
        target = require_text(raw_rule.get("target"), f"join rule {index}.target")
        if not branches or any(node not in node_ids for node in branches) or target not in node_ids:
            raise FocusRuntimeError(f"join rule {index} references unknown or empty branches")
        k_value = raw_rule.get("k")
        if rule_type == "K_OF_N":
            if not isinstance(k_value, int) or not 1 <= k_value <= len(branches):
                raise FocusRuntimeError(f"join rule {index}.k must be between 1 and branch count")
        rules.append(
            {
                "join_rule_id": raw_rule.get("join_rule_id") or stable_hash("join", {"type": rule_type, "branches": branches, "target": target}),
                "type": rule_type,
                "branches": branches,
                "target": target,
                "k": k_value,
                "time_policy": raw_rule.get("time_policy"),
                "tolerance": raw_rule.get("tolerance"),
                "satisfied": bool(raw_rule.get("satisfied", False)),
                "evidence": require_list(raw_rule.get("evidence", []), f"join rule {index}.evidence"),
            }
        )
    return rules


def build_field(
    state: dict[str, Any],
    payload: dict[str, Any],
    *,
    field_id: str,
    depth: int,
    parent_binding: dict[str, Any] | None,
    recursive_path: list[str],
    label: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    contract = normalize_contract(payload, label)
    centers, node_defs = normalize_centers(payload, label)
    center_ids = {center["center_id"] for center in centers}
    selected_center_id = require_text(payload.get("selected_center_id"), f"{label}.selected_center_id")
    if selected_center_id not in center_ids:
        raise FocusRuntimeError("selected_center_id must reference a declared center")
    selected = next(center for center in centers if center["center_id"] == selected_center_id)
    if selected["status"] not in {"active", "closed"}:
        raise FocusRuntimeError("selected center must be active or closed")
    order = normalize_order(payload, set(node_defs), label)
    center_relations = normalize_center_relations(payload, center_ids, label)
    join_rules = normalize_join_rules(payload, set(node_defs), label)
    closure_gap = require_text(payload.get("closure_gap"), f"{label}.closure_gap")
    confidence = payload.get("confidence", "provisional")
    if confidence not in {"confirmed", "provisional", "ambiguous"}:
        raise FocusRuntimeError("confidence must be confirmed, provisional, or ambiguous")

    goal_contract_id = stable_hash("contract", contract)
    field_version_id = stable_hash(
        "fieldv",
        {
            "field_id": field_id,
            "contract": contract,
            "centers": centers,
            "order": order,
            "center_relations": center_relations,
            "join_rules": join_rules,
        },
    )
    root_path = [] if parent_binding is None else list(parent_binding["root_path"])
    root_address_payload = {
        "global_root_id": "F0",
        "global_depth": depth,
        "field_id": field_id,
        "goal_contract_id": goal_contract_id,
        "primary_parent": parent_binding,
        "structural_role": "field-root",
        "root_path": root_path,
        "recursive_path": recursive_path,
    }
    root_address_id = stable_hash("addr", root_address_payload)
    field_root_path = root_path + [root_address_id]

    node_predecessors: dict[str, list[str]] = {node_id: [] for node_id in node_defs}
    for edge in order:
        node_predecessors[edge["after"]].append(edge["before"])

    node_addresses: dict[str, str] = {}
    addresses: list[dict[str, Any]] = [
        {
            "address_id": root_address_id,
            "address_revision_id": stable_hash(
                "addrrev", {"address_id": root_address_id, "contract": contract}
            ),
            "global_root_id": "F0",
            "global_depth": depth,
            "field_id": field_id,
            "goal_contract_id": goal_contract_id,
            "primary_parent": parent_binding,
            "object_id": field_id,
            "address_kind": "root",
            "structural_role": "field-root",
            "node_id": None,
            "parallel_binding": None,
            "root_path": field_root_path,
            "relation_path": [],
            "recursive_path": recursive_path,
            "center_membership": [],
            "field_version_id": field_version_id,
            "panorama_version": state["panorama_version"] + 1,
            "calibration_status": "calibrated",
            "modality": "[◇]",
            "frontier_membership": [],
            "exposure_state": "visible",
            "evidence": require_list(payload.get("evidence", []), f"{label}.evidence"),
            "provenance": {
                "producing_motion": "FIELD_FORM" if depth == 0 else "FOCUS_EXPAND",
                "source_addresses": [] if parent_binding is None else [parent_binding["parent_address"]],
            },
            "reopen_address": root_address_id,
            "display_address": f"F{depth}@{field_id}:root",
            "local_display_address": "local_F0",
        }
    ]
    center_by_node: dict[str, list[dict[str, Any]]] = {node_id: [] for node_id in node_defs}
    for center in centers:
        for node_id in center["node_ids"]:
            center_by_node[node_id].append(center)

    for node_id, node in node_defs.items():
        membership = [
            {
                "center_id": center["center_id"],
                "center_role": "selected" if center["center_id"] == selected_center_id else "member",
                "obligation_ref": center["obligation"],
                "status": center["status"],
                "obligation_status": "satisfied" if center["closure_status"] == "closed" else "pending",
                "evidence_ref": center["evidence"],
                "closure_effect": "required" if node["required_for_closure"] else "contributes",
            }
            for center in center_by_node[node_id]
        ]
        address_payload = {
            "global_root_id": "F0",
            "global_depth": depth,
            "field_id": field_id,
            "goal_contract_id": goal_contract_id,
            "primary_parent": parent_binding,
            "structural_role": {"node_id": node_id, "role": node["role"]},
            "parallel_binding": node.get("parallel_binding"),
            "root_path": field_root_path,
            "relation_path": sorted(node_predecessors[node_id]),
            "recursive_path": recursive_path,
        }
        address_id = stable_hash("addr", address_payload)
        node_addresses[node_id] = address_id
        addresses.append(
            {
                "address_id": address_id,
                "address_revision_id": stable_hash("addrrev", {"address_id": address_id, "evidence": node["evidence"]}),
                "global_root_id": "F0",
                "global_depth": depth,
                "field_id": field_id,
                "goal_contract_id": goal_contract_id,
                "primary_parent": parent_binding,
                "object_id": node["object_id"],
                "address_kind": "structural" if depth == 0 else "recursive",
                "structural_role": node["role"],
                "node_id": node_id,
                "parallel_binding": node.get("parallel_binding"),
                "root_path": field_root_path,
                "relation_path": sorted(node_predecessors[node_id]),
                "recursive_path": recursive_path,
                "center_membership": membership,
                "field_version_id": field_version_id,
                "panorama_version": state["panorama_version"] + 1,
                "calibration_status": "calibrated",
                "modality": "[◇]",
                "frontier_membership": (
                    [] if node["frontier_class"] == "none" else [node["frontier_class"]]
                ),
                "exposure_state": "visible",
                "evidence": node["evidence"],
                "invalidated_by": [],
                "provenance": {
                    "producing_motion": "FIELD_FORM" if depth == 0 else "FOCUS_EXPAND",
                    "source_addresses": [] if parent_binding is None else [parent_binding["parent_address"]],
                },
                "reopen_address": address_id,
                "display_address": f"F{depth}@{field_id}:{node_id}",
                "local_display_address": f"local_F0:{node_id}",
            }
        )

    for address in addresses:
        if address.get("node_id") is not None:
            address["relation_path"] = [
                node_addresses[node_id] for node_id in address["relation_path"]
            ]

    all_unselected_centers = [
        center["center_id"]
        for center in centers
        if center["center_id"] != selected_center_id and center["status"] != "invalid"
    ]
    requested_peers = payload.get("peer_center_ids")
    if requested_peers is None:
        peer_centers = all_unselected_centers
    else:
        peer_centers = [
            require_text(item, f"{label}.peer_center_ids[]")
            for item in require_list(requested_peers, f"{label}.peer_center_ids")
        ]
        if selected_center_id in peer_centers or not set(peer_centers).issubset(
            set(all_unselected_centers)
        ):
            raise FocusRuntimeError(
                "peer_center_ids must be a subset of non-invalid unselected centers"
            )
    projection_certificate = {
        "certificate_id": stable_hash(
            "projection",
            {
                "field_version_id": field_version_id,
                "selected_center_id": selected_center_id,
                "peer_centers": peer_centers,
                "assumptions": payload.get("projection_assumptions", []),
            },
        ),
        "source_field_version": field_version_id,
        "source_center_system_version": stable_hash("centersv", centers),
        "selected_center_ref": selected_center_id,
        "required_peer_interfaces": peer_centers,
        "omitted_obligations": [
            center["obligation"]
            for center in centers
            if center["center_id"] in all_unselected_centers
        ],
        "assumptions": require_list(payload.get("projection_assumptions", []), f"{label}.projection_assumptions"),
        "invalidation_triggers": require_list(payload.get("invalidation_triggers", []), f"{label}.invalidation_triggers"),
    }
    field = {
        "field_id": field_id,
        "global_depth": depth,
        "primary_parent": parent_binding,
        "goal_contract_id": goal_contract_id,
        "contract": contract,
        "closure_gap": closure_gap,
        "remaining_closure_gap": closure_gap,
        "confidence": confidence,
        "centers": centers,
        "center_relations": center_relations,
        "join_rules": join_rules,
        "selected_center_ref": selected_center_id,
        "peer_center_refs": peer_centers,
        "projection_certificate": projection_certificate,
        "order": order,
        "node_addresses": node_addresses,
        "root_address_id": root_address_id,
        "root_path": field_root_path,
        "recursive_path": recursive_path,
        "field_version_id": field_version_id,
        "frontiers": {
            "action": [],
            "expansion_required": [
                node_addresses[node_id]
                for node_id, node in node_defs.items()
                if node["frontier_class"] == "expansion_required"
            ],
            "expansion_latent": [
                node_addresses[node_id]
                for node_id, node in node_defs.items()
                if node["frontier_class"] == "expansion_latent"
            ],
            "compressed": [
                node_addresses[node_id]
                for node_id, node in node_defs.items()
                if node["frontier_class"] == "compressed"
            ],
        },
        "claims": {
            (node.get("claim_id") or node_id): {
                "claim_id": node.get("claim_id") or node_id,
                "node_id": node_id,
                "content": node.get("claim_content"),
                "status": node.get("claim_status", "provisional"),
                "evidence": list(node.get("evidence", [])),
                "invalidated_by": [],
            }
            for node_id, node in node_defs.items()
        },
        "closure_certificates": [],
        "current_closure_version_id": None,
        "invalidation_history": [],
        "closure_audit": {
            "selected_center_closure": False,
            "field_closure": False,
            "active_residuals": [],
            "latent_openness": [],
        },
        "focus_return": None,
        "fold_summary": None,
    }
    refresh_action_frontier(state, field, addresses=addresses)
    return field, addresses


def refresh_action_frontier(
    state: dict[str, Any], field: dict[str, Any], *, addresses: list[dict[str, Any]] | None = None
) -> None:
    """Derive the action frontier from legal modality and predecessor readiness."""
    local = {item["address_id"]: item for item in (addresses or [])}

    def address_for(address_id: str) -> dict[str, Any]:
        return local.get(address_id) or state.get("addresses", {}).get(address_id, {})

    realized_nodes = {
        node_id
        for node_id, address_id in field["node_addresses"].items()
        if address_for(address_id).get("modality") == "[+]"
    }
    predecessor_map: dict[str, set[str]] = {
        node_id: set() for node_id in field["node_addresses"]
    }
    for edge in field["order"]:
        predecessor_map[edge["after"]].add(edge["before"])
    action: list[str] = []
    for node_id, address_id in field["node_addresses"].items():
        address = address_for(address_id)
        memberships = address.setdefault("frontier_membership", [])
        if "action" in memberships:
            memberships.remove("action")
        in_selected_center = any(
            item.get("center_id") == field["selected_center_ref"]
            for item in address.get("center_membership", [])
        )
        if (
            in_selected_center
            and
            address.get("calibration_status") == "calibrated"
            and address.get("modality") == "[◇]"
            and predecessor_map[node_id].issubset(realized_nodes)
        ):
            action.append(address_id)
            memberships.append("action")
    field["frontiers"]["action"] = action


def find_field(state: dict[str, Any], field_id: str) -> dict[str, Any]:
    field = state.get("fields", {}).get(field_id)
    if not isinstance(field, dict):
        raise FocusRuntimeError(f"unknown field_id {field_id}")
    return field


def current_field(state: dict[str, Any]) -> dict[str, Any]:
    stack = state.get("field_stack")
    if not isinstance(stack, list) or not stack:
        raise FocusRuntimeError("field stack is empty")
    return find_field(state, stack[-1]["field_id"])


def resolve_address(state: dict[str, Any], field: dict[str, Any], value: str) -> str:
    if value in state["addresses"]:
        return value
    address_id = field["node_addresses"].get(value)
    if address_id:
        return address_id
    raise FocusRuntimeError(f"unknown address or node {value!r} in field {field['field_id']}")


def record_decision(
    state: dict[str, Any],
    decision: str,
    reason: str,
    *,
    target_address: str | None = None,
    evidence: list[Any] | None = None,
    delta_id: str | None = None,
) -> dict[str, Any]:
    if decision not in DECISIONS:
        raise FocusRuntimeError(f"unsupported Focus decision: {decision}")
    record = {
        "decision_id": stable_hash(
            "decision",
            {
                "run_id": state.get("run_id"),
                "revision": state.get("revision", 0) + 1,
                "decision": decision,
                "target_address": target_address,
                "delta_id": delta_id,
                "reason": reason,
            },
        ),
        "decision": decision,
        "reason": require_text(reason, "decision.reason"),
        "target_address": target_address,
        "evidence": list(evidence or []),
        "delta_id": delta_id,
        "status": "pending",
        "created_at": now_iso(),
    }
    state["decision_history"].append(record)
    state["active_decision"] = record
    return record


def suggested_drive_decision(state: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    ready_required = [
        address_id
        for address_id in field["frontiers"]["expansion_required"]
        if address_id in field["frontiers"]["action"]
    ]
    if ready_required:
        return record_decision(
            state,
            "EXPAND_REQUIRED",
            "a required frontier must be opened before its address can be realized",
            target_address=ready_required[0],
        )
    ready_action = [
        address_id
        for address_id in field["frontiers"]["action"]
        if address_id not in field["frontiers"]["expansion_required"]
    ]
    if ready_action:
        return record_decision(
            state,
            "CONTINUE",
            "the next necessary address is ready for parent-field action",
            target_address=ready_action[0],
        )
    selected = next(
        center
        for center in field["centers"]
        if center["center_id"] == field["selected_center_ref"]
    )
    if all(
        state["addresses"].get(field["node_addresses"][node_id], {}).get("modality") == "[+]"
        for node_id in selected["node_ids"]
    ) and not field["frontiers"]["expansion_required"]:
        return record_decision(
            state,
            "CONTINUE",
            "the selected center is ready for a FOLD closure audit",
        )
    return record_decision(
        state,
        "BLOCKED",
        "no legal action frontier is currently ready",
    )


def necessary_descendant_addresses(
    state: dict[str, Any], field: dict[str, Any], seeds: set[str]
) -> set[str]:
    node_by_address = {
        address_id: node_id for node_id, address_id in field["node_addresses"].items()
    }
    seed_nodes = {node_by_address[address_id] for address_id in seeds}
    adjacency: dict[str, set[str]] = {
        node_id: set() for node_id in field["node_addresses"]
    }
    for edge in field["order"]:
        adjacency[edge["before"]].add(edge["after"])
    for rule in field["join_rules"]:
        for branch in rule["branches"]:
            adjacency[branch].add(rule["target"])
    impacted_nodes = set(seed_nodes)
    queue = list(seed_nodes)
    while queue:
        node_id = queue.pop()
        for child in adjacency[node_id]:
            if child not in impacted_nodes:
                impacted_nodes.add(child)
                queue.append(child)
    return {field["node_addresses"][node_id] for node_id in impacted_nodes}


def invalidate_field_addresses(
    state: dict[str, Any],
    field: dict[str, Any],
    seed_addresses: set[str],
    delta_id: str,
) -> set[str]:
    impacted = necessary_descendant_addresses(state, field, seed_addresses)
    impacted_nodes = {
        state["addresses"][address_id].get("node_id") for address_id in impacted
    }
    for address_id in impacted:
        address = state["addresses"][address_id]
        address["modality"] = "[◇]"
        if delta_id not in address["invalidated_by"]:
            address["invalidated_by"].append(delta_id)
        if address.get("exposure_state") == "compressed":
            address["exposure_state"] = "visible"
        address["address_revision_id"] = stable_hash(
            "addrrev",
            {
                "address_id": address_id,
                "modality": address["modality"],
                "invalidated_by": address["invalidated_by"],
            },
        )
    for claim in field.get("claims", {}).values():
        if claim.get("node_id") in impacted_nodes:
            claim["status"] = "invalidated"
            if delta_id not in claim["invalidated_by"]:
                claim["invalidated_by"].append(delta_id)
    for certificate in field.get("closure_certificates", []):
        if certificate.get("status") == "active":
            certificate["status"] = "invalidated"
            certificate["invalidated_by"] = delta_id
            certificate["invalidated_at"] = now_iso()
    field["closure_audit"]["selected_center_closure"] = False
    field["closure_audit"]["field_closure"] = False
    field["remaining_closure_gap"] = state["knowledge_deltas"][delta_id]["raw_content"]
    field["invalidation_history"].append(
        {
            "delta_id": delta_id,
            "seed_addresses": sorted(seed_addresses),
            "invalidated_addresses": sorted(impacted),
            "time": now_iso(),
        }
    )
    refresh_action_frontier(state, field)
    return impacted


def propagate_invalidation(
    state: dict[str, Any],
    field: dict[str, Any],
    seed_addresses: set[str],
    delta_id: str,
    scope: str,
) -> dict[str, set[str]]:
    """Invalidate the local necessary closure and, when requested, parent returns."""
    impacted_by_field = {
        field["field_id"]: invalidate_field_addresses(
            state, field, seed_addresses, delta_id
        )
    }
    if scope not in {"interface", "field", "branch"}:
        return impacted_by_field
    child = field
    while child.get("primary_parent"):
        binding = child["primary_parent"]
        parent = find_field(state, binding["parent_field_id"])
        parent_address_id = binding["parent_address"]
        parent_address = state["addresses"][parent_address_id]
        if parent_address.get("returned_interface") is not None:
            parent_address["returned_interface_invalidated_by"] = delta_id
        impacted_by_field[parent["field_id"]] = invalidate_field_addresses(
            state, parent, {parent_address_id}, delta_id
        )
        if scope == "interface":
            break
        child = parent
    return impacted_by_field


def current_versions_for_field(state: dict[str, Any], field_id: str) -> list[dict[str, Any]]:
    return [
        version
        for version in state["field_closure_versions"]
        if version.get("field_id") == field_id and version.get("status") == "current"
    ]


def cmd_decide(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    if not state.get("field_stack"):
        raise FocusRuntimeError("drive requires a formed field")
    payload = load_json_value(args.payload, "drive payload")
    decision = require_text(payload.get("decision"), "drive.decision").upper()
    if decision not in DECISIONS:
        raise FocusRuntimeError(f"drive.decision must be one of {sorted(DECISIONS)}")
    field = current_field(state)
    target_value = payload.get("target_address")
    target = None
    if target_value is not None:
        target = resolve_address(state, field, require_text(target_value, "drive.target_address"))
    if target in field["frontiers"]["expansion_required"] and decision != "EXPAND_REQUIRED":
        raise FocusRuntimeError("target requires EXPAND_REQUIRED before parent action")
    if decision == "EXPAND_REQUIRED" and target not in field["frontiers"]["expansion_required"]:
        raise FocusRuntimeError("EXPAND_REQUIRED must target a required expansion frontier")
    if decision == "CONTINUE" and target is not None and target not in field["frontiers"]["action"]:
        raise FocusRuntimeError("CONTINUE target must be on the ready action frontier")
    if decision == "UNWIND" and len(state["field_stack"]) <= 1:
        raise FocusRuntimeError("UNWIND requires an open child field")
    record = record_decision(
        state,
        decision,
        require_text(payload.get("reason"), "drive.reason"),
        target_address=target,
        evidence=require_list(payload.get("evidence", []), "drive.evidence"),
        delta_id=payload.get("delta_id"),
    )
    append_event(state, "FOCUS_DECISION", record)
    require_valid(state)
    write_state(path, state)
    print(canonical_json(record))
    return 0


def cmd_ingest_delta(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    payload = load_json_value(args.payload, "delta intake payload")
    delta_id = require_text(
        payload.get("delta_id")
        or stable_hash("delta", {"revision": state["revision"], "payload": payload}),
        "delta.delta_id",
    )
    if delta_id in state["knowledge_deltas"]:
        raise FocusRuntimeError(f"delta already exists: {delta_id}")
    kind = require_text(payload.get("kind"), "delta.kind")
    if kind not in DELTA_KINDS:
        raise FocusRuntimeError(f"delta.kind must be one of {sorted(DELTA_KINDS)}")
    record = {
        "delta_id": delta_id,
        "kind": kind,
        "raw_content": require_text(payload.get("raw_content"), "delta.raw_content"),
        "source": require_text(payload.get("source"), "delta.source"),
        "evidence": require_list(payload.get("evidence", []), "delta.evidence"),
        "status": "pending",
        "classification": None,
        "assessment": None,
        "ingested_at": now_iso(),
    }
    state["knowledge_deltas"][delta_id] = record
    append_event(
        state,
        "DELTA_INGESTED",
        {"delta_id": delta_id, "kind": kind, "source": record["source"]},
    )
    require_valid(state)
    write_state(path, state)
    print(canonical_json({"delta_id": delta_id, "status": "pending", "decision": "ASSESS_IMPACT"}))
    return 0


def cmd_assess_impact(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    if not state.get("field_stack"):
        raise FocusRuntimeError("impact assessment requires a formed field")
    payload = load_json_value(args.payload, "impact assessment payload")
    delta_id = require_text(payload.get("delta_id"), "impact.delta_id")
    delta = state["knowledge_deltas"].get(delta_id)
    if not isinstance(delta, dict):
        raise FocusRuntimeError(f"unknown delta: {delta_id}")
    if delta.get("status") != "pending":
        raise FocusRuntimeError(f"delta {delta_id} has already been assessed")
    classification = require_text(payload.get("classification"), "impact.classification").upper()
    if classification not in DELTA_CLASSIFICATIONS:
        raise FocusRuntimeError(
            f"impact.classification must be one of {sorted(DELTA_CLASSIFICATIONS)}"
        )
    scope = require_text(payload.get("propagation_scope"), "impact.propagation_scope")
    if scope not in PROPAGATION_SCOPES:
        raise FocusRuntimeError(
            f"impact.propagation_scope must be one of {sorted(PROPAGATION_SCOPES)}"
        )
    requested_field_id = payload.get("field_id")
    field = (
        current_field(state)
        if requested_field_id is None
        else find_field(state, require_text(requested_field_id, "impact.field_id"))
    )
    affected: set[str] = set()
    for item in require_list(payload.get("affected_addresses", []), "impact.affected_addresses"):
        address_id = resolve_address(
            state, field, require_text(item, "impact.affected_addresses[]")
        )
        address = state["addresses"][address_id]
        if address.get("field_id") != field["field_id"] or address.get("node_id") is None:
            raise FocusRuntimeError("affected addresses must be structural nodes in impact.field_id")
        affected.add(address_id)
    if classification in {"NOOP", "OUTSIDE"} and (affected or scope != "none"):
        raise FocusRuntimeError(f"{classification} must use no affected addresses and scope none")
    if classification == "CONTRADICT" and (not affected or scope == "none"):
        raise FocusRuntimeError("CONTRADICT requires affected addresses and a propagation scope")
    decision_map = {
        "NOOP": "NOOP",
        "OUTSIDE": "CONTINUE",
        "ADD": "CONTINUE",
        "REFINE": "REVISE_LOCAL" if scope in {"none", "local"} else "REOPEN_INTERFACE",
    }
    if classification == "CONTRADICT":
        decision = {
            "local": "REVISE_LOCAL",
            "interface": "REOPEN_INTERFACE",
            "field": "REFRAME_FIELD",
            "branch": "SPLIT_BRANCH",
        }[scope]
    else:
        decision = decision_map[classification]
    invalidated: set[str] = set()
    invalidated_by_field: dict[str, list[str]] = {}
    source_versions = [item["version_id"] for item in current_versions_for_field(state, field["field_id"])]
    if classification in {"REFINE", "CONTRADICT"} and affected:
        propagated = propagate_invalidation(state, field, affected, delta_id, scope)
        invalidated_by_field = {
            field_id: sorted(addresses) for field_id, addresses in propagated.items()
        }
        invalidated = set().union(*propagated.values())
        version_status = "superseded-by-branch" if scope == "branch" else "invalidated"
        for impacted_field_id in propagated:
            for version in current_versions_for_field(state, impacted_field_id):
                version["status"] = version_status
                version["invalidated_by"] = delta_id
        if scope == "branch":
            state["version_branches"].append(
                {
                    "branch_id": stable_hash(
                        "branch",
                        {"field_id": field["field_id"], "delta_id": delta_id, "sources": source_versions},
                    ),
                    "field_id": field["field_id"],
                    "delta_id": delta_id,
                    "source_versions": source_versions,
                    "result_versions": [],
                    "status": "open",
                    "created_at": now_iso(),
                }
            )
        state["phase"] = "revising"
    assessment = {
        "classification": classification,
        "propagation_scope": scope,
        "affected_addresses": sorted(affected),
        "invalidated_addresses": sorted(invalidated),
        "invalidated_by_field": invalidated_by_field,
        "reason": require_text(payload.get("reason"), "impact.reason"),
        "evidence": require_list(payload.get("evidence", []), "impact.evidence"),
        "decision": decision,
        "assessed_at": now_iso(),
    }
    delta["classification"] = classification
    delta["assessment"] = assessment
    delta["status"] = "assessed"
    record = record_decision(
        state,
        decision,
        assessment["reason"],
        evidence=assessment["evidence"],
        delta_id=delta_id,
    )
    append_event(
        state,
        "DELTA_ASSESSED",
        {
            "delta_id": delta_id,
            "classification": classification,
            "scope": scope,
            "invalidated_addresses": sorted(invalidated),
            "decision_id": record["decision_id"],
        },
    )
    require_valid(state)
    write_state(path, state)
    print(canonical_json({"delta_id": delta_id, **assessment}))
    return 0


def validate_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if state.get("phase") not in PHASES:
        errors.append("phase is invalid")
    if state.get("mode") not in MODES:
        errors.append("mode is invalid")
    if not isinstance(state.get("fields"), dict):
        errors.append("fields must be an object")
        return errors
    if not isinstance(state.get("addresses"), dict):
        errors.append("addresses must be an object")
        return errors
    for key in ("address_candidates", "latent_residuals", "active_residuals"):
        if not isinstance(state.get(key), dict):
            errors.append(f"{key} must be an object")
    for key in ("residual_history", "addressing_results"):
        if not isinstance(state.get(key), list):
            errors.append(f"{key} must be a list")
    for key in ("decision_history", "field_closure_versions", "version_branches", "document_revisions"):
        if not isinstance(state.get(key), list):
            errors.append(f"{key} must be a list")
    if not isinstance(state.get("knowledge_deltas"), dict):
        errors.append("knowledge_deltas must be an object")
    active_decision = state.get("active_decision")
    if active_decision is not None and (
        not isinstance(active_decision, dict)
        or active_decision.get("decision") not in DECISIONS
    ):
        errors.append("active_decision is invalid")
    observations = state.get("observations", [])
    if not isinstance(observations, list):
        errors.append("observations must be a list")
        observations = []
    observation_ids: set[str] = set()
    for index, observation in enumerate(observations):
        if not isinstance(observation, dict):
            errors.append(f"observation {index} must be an object")
            continue
        observation_id = observation.get("observation_id")
        if not isinstance(observation_id, str) or not observation_id:
            errors.append(f"observation {index} has invalid observation_id")
        elif observation_id in observation_ids:
            errors.append(f"observation {observation_id} is duplicated")
        else:
            observation_ids.add(observation_id)
        if not isinstance(observation.get("events"), list) or not observation.get("events"):
            errors.append(f"observation {observation_id or index} must contain events")
    if state.get("phase") in {"observed", "reconstructed"} and not observations:
        errors.append(f"phase {state.get('phase')} requires at least one observation")
    for candidate_id, candidate in state.get("address_candidates", {}).items():
        if candidate.get("candidate_address_id") != candidate_id:
            errors.append(f"candidate key {candidate_id} does not match candidate_address_id")
        if candidate.get("calibration_status") not in {
            "hypothesized",
            "calibrating",
            "calibrated",
            "rejected",
        }:
            errors.append(f"candidate {candidate_id} has invalid calibration_status")
        if "modality" in candidate:
            errors.append(f"candidate {candidate_id} must not carry address modality")
    for address_id, address in state["addresses"].items():
        if address.get("address_id") != address_id:
            errors.append(f"address key {address_id} does not match address_id")
        if address.get("calibration_status") != "calibrated":
            errors.append(f"legal address {address_id} must be calibrated")
        if address.get("modality") not in {"[◇]", "[+]"}:
            errors.append(f"legal address {address_id} must use [◇] or [+]")
        if not isinstance(address.get("invalidated_by", []), list):
            errors.append(f"legal address {address_id} invalidated_by must be a list")
    for field_id, field in state["fields"].items():
        if field.get("field_id") != field_id:
            errors.append(f"field key {field_id} does not match field_id")
        centers = field.get("centers", [])
        center_ids = {item.get("center_id") for item in centers if isinstance(item, dict)}
        if field.get("selected_center_ref") not in center_ids:
            errors.append(f"field {field_id} selected center is missing")
        peers = set(field.get("peer_center_refs", []))
        if field.get("selected_center_ref") in peers:
            errors.append(f"field {field_id} selected center cannot also be a peer")
        if not peers.issubset(center_ids):
            errors.append(f"field {field_id} has unknown peer centers")
        node_addresses = field.get("node_addresses", {})
        frontiers = field.get("frontiers")
        if not isinstance(frontiers, dict) or set(frontiers) != FRONTIER_KEYS:
            errors.append(f"field {field_id} must contain four typed frontiers")
            frontiers = {key: [] for key in FRONTIER_KEYS}
        for frontier_name, entries in frontiers.items():
            if not isinstance(entries, list):
                errors.append(f"field {field_id} frontier {frontier_name} must be a list")
                continue
            for address_id in entries:
                if address_id not in node_addresses.values():
                    errors.append(
                        f"field {field_id} frontier {frontier_name} references unknown address {address_id}"
                    )
        for node_id, address_id in node_addresses.items():
            address = state["addresses"].get(address_id)
            if not isinstance(address, dict):
                errors.append(f"field {field_id} node {node_id} has missing address")
                continue
            if address.get("field_id") != field_id or address.get("node_id") != node_id:
                errors.append(f"address {address_id} does not match field/node binding")
            expected_depth = field.get("global_depth")
            if address.get("global_depth") != expected_depth:
                errors.append(f"address {address_id} has wrong global_depth")
        certificate = field.get("projection_certificate", {})
        if certificate.get("selected_center_ref") != field.get("selected_center_ref"):
            errors.append(f"field {field_id} projection certificate is stale")
        root_address = state["addresses"].get(field.get("root_address_id"))
        if not isinstance(root_address, dict) or root_address.get("address_kind") != "root":
            errors.append(f"field {field_id} root address is missing")
        parent = field.get("primary_parent")
        if parent:
            parent_address = state["addresses"].get(parent.get("parent_address"))
            if not parent_address:
                errors.append(f"field {field_id} primary parent address is missing")
            elif field.get("global_depth") != parent_address.get("global_depth", -1) + 1:
                errors.append(f"field {field_id} depth is not parent depth + 1")
        if not isinstance(field.get("closure_certificates", []), list):
            errors.append(f"field {field_id} closure_certificates must be a list")
        if not isinstance(field.get("invalidation_history", []), list):
            errors.append(f"field {field_id} invalidation_history must be a list")
    stack = state.get("field_stack", [])
    for frame in stack:
        if frame.get("field_id") not in state["fields"]:
            errors.append("field stack references an unknown field")
    return errors


def require_valid(state: dict[str, Any]) -> None:
    errors = validate_state(state)
    if errors:
        raise FocusRuntimeError("state validation failed: " + "; ".join(errors))


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.state)
    if path.exists():
        raise FocusRuntimeError(f"state already exists: {path}")
    task = require_text(args.task, "--task")
    if args.mode not in MODES:
        raise FocusRuntimeError(
            "--mode must be constructive, clarify, action, or sidecar"
        )
    state = {
        "schema_version": SCHEMA_VERSION,
        "run_id": f"run_{uuid.uuid4().hex}",
        "task": task,
        "mode": args.mode,
        "phase": "initialized",
        "revision": 0,
        "panorama_version": 0,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "root_field_id": None,
        "fields": {},
        "addresses": {},
        "address_candidates": {},
        "latent_residuals": {},
        "active_residuals": {},
        "residual_history": [],
        "addressing_results": [],
        "observations": [],
        "field_stack": [],
        "knowledge_deltas": {},
        "decision_history": [],
        "active_decision": None,
        "field_closure_versions": [],
        "version_branches": [],
        "document_revisions": [],
        "history": [],
    }
    append_event(state, "INIT", {"task": task, "mode": args.mode})
    write_state(path, state)
    print(canonical_json({"run_id": state["run_id"], "phase": state["phase"]}))
    return 0


def cmd_register_candidate(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    payload = load_json_value(args.payload, "candidate payload")
    candidate_id = require_text(
        payload.get("candidate_address_id"), "candidate.candidate_address_id"
    )
    if candidate_id in state["address_candidates"]:
        raise FocusRuntimeError(f"candidate already exists: {candidate_id}")
    record = {
        "candidate_address_id": candidate_id,
        "calibration_status": "hypothesized",
        "field_id": payload.get("field_id"),
        "proposed_parent_binding": payload.get("proposed_parent_binding"),
        "proposed_structural_role": require_text(
            payload.get("proposed_structural_role"), "candidate.proposed_structural_role"
        ),
        "evidence": require_list(payload.get("evidence", []), "candidate.evidence"),
        "counterevidence": [],
        "resulting_address_id": None,
    }
    state["address_candidates"][candidate_id] = record
    append_event(state, "ADDRESS_CANDIDATE_REGISTERED", record)
    write_state(path, state)
    print(canonical_json(record))
    return 0


def cmd_resolve_candidate(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    payload = load_json_value(args.payload, "candidate resolution payload")
    candidate_id = require_text(
        payload.get("candidate_address_id"), "candidate.candidate_address_id"
    )
    record = state["address_candidates"].get(candidate_id)
    if not isinstance(record, dict):
        raise FocusRuntimeError(f"unknown candidate: {candidate_id}")
    disposition = payload.get("disposition")
    if disposition == "rejected":
        record["calibration_status"] = "rejected"
        record["counterevidence"] = require_list(
            payload.get("counterevidence"), "candidate.counterevidence"
        )
        if not record["counterevidence"]:
            raise FocusRuntimeError("rejected candidate requires counterevidence")
    elif disposition == "calibrated":
        address_id = require_text(payload.get("resulting_address_id"), "candidate.resulting_address_id")
        if address_id not in state["addresses"]:
            raise FocusRuntimeError("calibrated candidate must link an existing legal address")
        record["calibration_status"] = "calibrated"
        record["resulting_address_id"] = address_id
        record["evidence"] = list(record.get("evidence", [])) + require_list(
            payload.get("evidence", []), "candidate.evidence"
        )
    else:
        raise FocusRuntimeError("candidate disposition must be calibrated or rejected")
    append_event(state, "ADDRESS_CANDIDATE_RESOLVED", {"candidate_address_id": candidate_id, "disposition": disposition})
    write_state(path, state)
    print(canonical_json(record))
    return 0


def cmd_observe(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    if state["mode"] != "sidecar":
        raise FocusRuntimeError("observe requires a state initialized with --mode sidecar")
    if state["phase"] not in {"initialized", "observed"}:
        raise FocusRuntimeError("observation is only legal before sidecar reconstruction")
    payload = load_json_value(args.payload, "observe payload")
    observation = normalize_observation(payload, len(state.get("observations", [])))
    if any(
        item.get("observation_id") == observation["observation_id"]
        for item in state.get("observations", [])
    ):
        raise FocusRuntimeError(
            f"observation_id already exists: {observation['observation_id']}"
        )
    state.setdefault("observations", []).append(observation)
    state["phase"] = "observed"
    append_event(
        state,
        "TRACE_OBSERVED",
        {
            "observation_id": observation["observation_id"],
            "event_ids": [item["event_id"] for item in observation["events"]],
        },
    )
    require_valid(state)
    write_state(path, state)
    print(
        canonical_json(
            {
                "observation_id": observation["observation_id"],
                "events": len(observation["events"]),
                "decision": "RECONSTRUCT_FROM_TRACE",
            }
        )
    )
    return 0


def cmd_reconstruct(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    if state["mode"] != "sidecar":
        raise FocusRuntimeError("reconstruct requires a state initialized with --mode sidecar")
    if state["phase"] != "observed":
        raise FocusRuntimeError("sidecar reconstruction requires an observed execution trace")
    payload = load_json_value(args.payload, "reconstruct payload")
    known_observations = {
        item["observation_id"]: item for item in state.get("observations", [])
    }
    trace_refs = require_list(
        payload.get("trace_observation_ids", list(known_observations)),
        "reconstruct.trace_observation_ids",
    )
    trace_refs = [
        require_text(item, "reconstruct.trace_observation_ids[]") for item in trace_refs
    ]
    if not trace_refs:
        raise FocusRuntimeError("reconstruct.trace_observation_ids must not be empty")
    unknown_refs = sorted(set(trace_refs) - set(known_observations))
    if unknown_refs:
        raise FocusRuntimeError(f"unknown trace observations: {unknown_refs}")
    field_id = require_text(payload.get("field_id", "field-root"), "reconstruct.field_id")
    if field_id in state["fields"]:
        raise FocusRuntimeError(f"field_id already exists: {field_id}")
    field, addresses = build_field(
        state,
        payload,
        field_id=field_id,
        depth=0,
        parent_binding=None,
        recursive_path=[field_id],
        label="reconstruct",
    )
    realized_nodes = [
        require_text(item, "reconstruct.realized_nodes[]")
        for item in require_list(payload.get("realized_nodes"), "reconstruct.realized_nodes")
    ]
    if not realized_nodes:
        raise FocusRuntimeError("reconstruct.realized_nodes must not be empty")
    unknown_nodes = sorted(set(realized_nodes) - set(field["node_addresses"]))
    if unknown_nodes:
        raise FocusRuntimeError(f"reconstruct references unknown realized nodes: {unknown_nodes}")
    node_evidence = payload.get("node_evidence")
    if not isinstance(node_evidence, dict):
        raise FocusRuntimeError("reconstruct.node_evidence must be an object")
    state["panorama_version"] += 1
    for address in addresses:
        address["panorama_version"] = state["panorama_version"]
        state["addresses"][address["address_id"]] = address
    for node_id in realized_nodes:
        evidence = require_list(
            node_evidence.get(node_id), f"reconstruct.node_evidence.{node_id}"
        )
        if not evidence:
            raise FocusRuntimeError(
                f"reconstruct.node_evidence.{node_id} must not be empty"
            )
        address = state["addresses"][field["node_addresses"][node_id]]
        address["modality"] = "[+]"
        address["evidence"] = evidence
        address["address_revision_id"] = stable_hash(
            "addrrev",
            {"address_id": address["address_id"], "evidence": evidence, "modality": "[+]"},
        )
    field["trace_observation_refs"] = trace_refs
    field["reconstruction_basis"] = "observed-execution"
    refresh_action_frontier(state, field)
    state["fields"][field_id] = field
    state["root_field_id"] = field_id
    state["field_stack"].append(
        {
            "field_id": field_id,
            "parent_field_id": None,
            "parent_address": None,
            "opened_for": field["closure_gap"],
            "reopen": field["root_address_id"],
        }
    )
    state["phase"] = "reconstructed"
    append_event(
        state,
        "TRACE_RECONSTRUCTED",
        {
            "field_id": field_id,
            "trace_observation_refs": trace_refs,
            "selected_center_ref": field["selected_center_ref"],
            "realized_nodes": realized_nodes,
        },
    )
    require_valid(state)
    write_state(path, state)
    print(
        canonical_json(
            {
                "field_id": field_id,
                "selected_center": field["selected_center_ref"],
                "peer_centers": field["peer_center_refs"],
                "addresses": field["node_addresses"],
                "realized_nodes": realized_nodes,
                "decision": "FOLD_OR_REPORT",
            }
        )
    )
    return 0


def cmd_frame(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    if state["phase"] != "initialized":
        raise FocusRuntimeError("Focus-1 frame requires an initialized state")
    payload = load_json_value(args.payload, "frame payload")
    field_id = require_text(payload.get("field_id", "field-root"), "frame.field_id")
    if field_id in state["fields"]:
        raise FocusRuntimeError(f"field_id already exists: {field_id}")
    field, addresses = build_field(
        state,
        payload,
        field_id=field_id,
        depth=0,
        parent_binding=None,
        recursive_path=[field_id],
        label="frame",
    )
    state["panorama_version"] += 1
    for address in addresses:
        address["panorama_version"] = state["panorama_version"]
        state["addresses"][address["address_id"]] = address
    state["fields"][field_id] = field
    state["root_field_id"] = field_id
    state["field_stack"].append(
        {
            "field_id": field_id,
            "parent_field_id": None,
            "parent_address": None,
            "opened_for": field["closure_gap"],
            "reopen": field["root_address_id"],
        }
    )
    state["phase"] = "framed"
    drive = suggested_drive_decision(state, field) if state["mode"] == "constructive" else None
    append_event(
        state,
        "FOCUS_1_FRAME",
        {
            "field_id": field_id,
            "selected_center_ref": field["selected_center_ref"],
            "peer_center_refs": field["peer_center_refs"],
            "projection_certificate": field["projection_certificate"]["certificate_id"],
        },
    )
    require_valid(state)
    write_state(path, state)
    print(
        canonical_json(
            {
                "field_id": field_id,
                "selected_center": field["selected_center_ref"],
                "peer_centers": field["peer_center_refs"],
                "closure_gap": field["closure_gap"],
                "addresses": field["node_addresses"],
                "decision": (
                    drive["decision"] if drive is not None else "FOCUS_2_EXPAND_OR_EXECUTE"
                ),
                "target_address": None if drive is None else drive["target_address"],
            }
        )
    )
    return 0


def cmd_expand(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    if state["phase"] not in {"framed", "expanded", "executing", "folded", "revising"}:
        raise FocusRuntimeError("Focus-2 expansion is not legal in the current phase")
    payload = load_json_value(args.payload, "expand payload")
    parent_field = current_field(state)
    parent_address_id = resolve_address(
        state,
        parent_field,
        require_text(payload.get("parent_address"), "expand.parent_address"),
    )
    parent_address = state["addresses"][parent_address_id]
    if state["mode"] == "constructive":
        if parent_address_id not in parent_field["frontiers"]["expansion_required"]:
            raise FocusRuntimeError("constructive expansion requires an expansion_required address")
        if parent_address_id not in parent_field["frontiers"]["action"]:
            raise FocusRuntimeError("cannot expand the address before its necessary predecessors")
        active = state.get("active_decision")
        if not isinstance(active, dict) or active.get("decision") != "EXPAND_REQUIRED":
            raise FocusRuntimeError("constructive expansion requires an active EXPAND_REQUIRED decision")
        if active.get("target_address") != parent_address_id:
            raise FocusRuntimeError("expansion target does not match the active Focus decision")
        active["status"] = "consumed"
        active["consumed_by"] = "FOCUS_2_EXPAND"
    selected_center = parent_field["selected_center_ref"]
    if not any(
        membership.get("center_id") == selected_center
        for membership in parent_address.get("center_membership", [])
    ):
        raise FocusRuntimeError("Focus-2 may only expand an address in the selected center")
    child_field_id = require_text(payload.get("field_id"), "expand.field_id")
    if child_field_id in state["fields"]:
        raise FocusRuntimeError(f"field_id already exists: {child_field_id}")
    parent_return = payload.get("parent_return")
    if not isinstance(parent_return, dict):
        raise FocusRuntimeError("expand.parent_return must be an object")
    parent_binding = {
        "parent_field_id": parent_field["field_id"],
        "parent_address": parent_address_id,
        "required_function": require_text(parent_return.get("required_function"), "parent_return.required_function"),
        "required_output": require_text(parent_return.get("required_output"), "parent_return.required_output"),
        "closure_requirement": require_text(parent_return.get("closure_requirement"), "parent_return.closure_requirement"),
        "parent_return": require_text(parent_return.get("parent_return"), "parent_return.parent_return"),
        "root_path": parent_address["root_path"] + [parent_address_id],
    }
    recursive_path = parent_field["recursive_path"] + [child_field_id]
    child_field, addresses = build_field(
        state,
        payload,
        field_id=child_field_id,
        depth=parent_field["global_depth"] + 1,
        parent_binding=parent_binding,
        recursive_path=recursive_path,
        label="expand",
    )
    state["panorama_version"] += 1
    for address in addresses:
        address["panorama_version"] = state["panorama_version"]
        state["addresses"][address["address_id"]] = address
    parent_address["child_field_id"] = child_field_id
    parent_address["exposure_state"] = "expanded"
    for frontier_name in ("action", "expansion_required", "expansion_latent"):
        if parent_address_id in parent_field["frontiers"][frontier_name]:
            parent_field["frontiers"][frontier_name].remove(parent_address_id)
    parent_address["frontier_membership"] = []
    parent_address["address_revision_id"] = stable_hash(
        "addrrev", {"address_id": parent_address_id, "child_field_id": child_field_id}
    )
    parent_address["panorama_version"] = state["panorama_version"]
    state["fields"][child_field_id] = child_field
    state["field_stack"].append(
        {
            "field_id": child_field_id,
            "parent_field_id": parent_field["field_id"],
            "parent_address": parent_address_id,
            "opened_for": child_field["closure_gap"],
            "reopen": child_field["root_address_id"],
        }
    )
    state["phase"] = "expanded"
    drive = suggested_drive_decision(state, child_field) if state["mode"] == "constructive" else None
    append_event(
        state,
        "FOCUS_2_EXPAND",
        {
            "parent_address": parent_address_id,
            "child_field_id": child_field_id,
            "selected_center_ref": child_field["selected_center_ref"],
            "projection_certificate": child_field["projection_certificate"]["certificate_id"],
        },
    )
    require_valid(state)
    write_state(path, state)
    print(
        canonical_json(
            {
                "field_id": child_field_id,
                "global_depth": child_field["global_depth"],
                "selected_center": child_field["selected_center_ref"],
                "peer_centers": child_field["peer_center_refs"],
                "addresses": child_field["node_addresses"],
                "decision": (
                    drive["decision"] if drive is not None else "EXECUTE_OR_EXPAND_ONE_MORE_LAYER"
                ),
                "target_address": None if drive is None else drive["target_address"],
            }
        )
    )
    return 0


def join_is_satisfied(field: dict[str, Any], rule: dict[str, Any], realized_nodes: set[str]) -> bool:
    count = sum(1 for node in rule["branches"] if node in realized_nodes)
    if rule["type"] == "ALL":
        return count == len(rule["branches"])
    if rule["type"] == "ANY":
        return count >= 1
    if rule["type"] == "K_OF_N":
        return count >= rule["k"]
    return bool(rule.get("satisfied") and rule.get("evidence"))


def cmd_execute(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    payload = load_json_value(args.payload, "execute payload")
    field = current_field(state)
    requested = [
        resolve_address(state, field, require_text(item, "execute.addresses[]"))
        for item in require_list(payload.get("addresses"), "execute.addresses")
    ]
    if not requested:
        raise FocusRuntimeError("execute.addresses must not be empty")
    evidence = require_list(payload.get("evidence"), "execute.evidence")
    if not evidence:
        raise FocusRuntimeError("execution requires non-empty evidence")
    if state["mode"] == "constructive":
        active = state.get("active_decision")
        if not isinstance(active, dict) or active.get("decision") != "CONTINUE":
            raise FocusRuntimeError("constructive execution requires an active CONTINUE decision")
        if active.get("target_address") is not None and active["target_address"] not in requested:
            raise FocusRuntimeError("execution does not consume the active Focus target")
        for address_id in requested:
            if address_id in field["frontiers"]["expansion_required"]:
                raise FocusRuntimeError("required expansion must be opened before execution")
            if address_id not in field["frontiers"]["action"]:
                raise FocusRuntimeError("constructive execution requires a ready action address")
        active["status"] = "consumed"
        active["consumed_by"] = "EXECUTE_AUDIT"
    state["panorama_version"] += 1
    node_by_address = {address_id: node_id for node_id, address_id in field["node_addresses"].items()}
    realized_nodes = {
        node_by_address[address_id]
        for address_id in node_by_address
        if state["addresses"][address_id]["modality"] == "[+]"
    }
    predecessor_map: dict[str, set[str]] = {node_id: set() for node_id in field["node_addresses"]}
    for edge in field["order"]:
        predecessor_map[edge["after"]].add(edge["before"])
    for address_id in requested:
        address = state["addresses"][address_id]
        node_id = node_by_address[address_id]
        if address["modality"] == "[+]":
            continue
        missing = predecessor_map[node_id] - realized_nodes
        if missing:
            raise FocusRuntimeError(f"cannot execute {node_id}; missing predecessors {sorted(missing)}")
        for rule in field["join_rules"]:
            if rule["target"] == node_id and not join_is_satisfied(field, rule, realized_nodes):
                raise FocusRuntimeError(f"cannot execute {node_id}; join rule {rule['join_rule_id']} is unsatisfied")
        address["modality"] = "[+]"
        address["evidence"] = list(address.get("evidence", [])) + evidence
        address["address_revision_id"] = stable_hash(
            "addrrev", {"address_id": address_id, "evidence": address["evidence"], "modality": "[+]"}
        )
        address["panorama_version"] = state["panorama_version"]
        for claim in field.get("claims", {}).values():
            if claim.get("node_id") == node_id:
                claim["status"] = "supported"
                claim["evidence"] = list(claim.get("evidence", [])) + evidence
        realized_nodes.add(node_id)
    refresh_action_frontier(state, field)
    state["phase"] = "executing"
    drive = suggested_drive_decision(state, field) if state["mode"] == "constructive" else None
    append_event(
        state,
        "EXECUTE_AUDIT",
        {
            "field_id": field["field_id"],
            "addresses": requested,
            "evidence": evidence,
            "result": payload.get("result"),
        },
    )
    require_valid(state)
    write_state(path, state)
    print(
        canonical_json(
            {
                "realized": requested,
                "decision": drive["decision"] if drive is not None else "CONTINUE_OR_FOLD",
                "target_address": None if drive is None else drive["target_address"],
            }
        )
    )
    return 0


def normalize_address_binding(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FocusRuntimeError(f"{label} must be an object")
    kind = value.get("kind")
    if kind not in ADDRESS_BINDING_KINDS:
        raise FocusRuntimeError(f"{label}.kind must be bound, candidate, or unaddressed")
    result = {"kind": kind}
    if kind == "bound":
        result["address_id"] = require_text(value.get("address_id"), f"{label}.address_id")
    elif kind == "candidate":
        result["candidate_address_id"] = require_text(
            value.get("candidate_address_id"), f"{label}.candidate_address_id"
        )
    return result


def normalize_residual(item: Any, label: str, *, latent: bool) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise FocusRuntimeError(f"{label} must be an object")
    residual_id = require_text(item.get("residual_id", item.get("id")), f"{label}.residual_id")
    result = {
        "residual_id": residual_id,
        "classification": "latent-residual" if latent else "active-residual",
        "description": require_text(item.get("description"), f"{label}.description"),
        "address_binding": normalize_address_binding(
            item.get("address_binding", {"kind": "unaddressed"}),
            f"{label}.address_binding",
        ),
        "evidence": require_list(item.get("evidence", []), f"{label}.evidence"),
        "source": item.get("source"),
    }
    if latent:
        result["activation_condition"] = require_text(
            item.get("activation_condition"), f"{label}.activation_condition"
        )
        result["blocking"] = False
    else:
        result["blocking"] = bool(item.get("blocking", True))
        addressing_result = item.get("addressing_result")
        if addressing_result is not None:
            if not isinstance(addressing_result, dict) or addressing_result.get("modality") not in {
                "[-]",
                "[∅]",
            }:
                raise FocusRuntimeError(
                    f"{label}.addressing_result must use result modality [-] or [∅]"
                )
            result["addressing_result"] = addressing_result
    return result


def cmd_fold(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    payload = load_json_value(args.payload, "fold payload")
    field = current_field(state)
    if state["mode"] == "constructive":
        active = state.get("active_decision")
        if not isinstance(active, dict) or active.get("decision") != "CONTINUE":
            raise FocusRuntimeError("constructive fold requires an active CONTINUE decision")
        if active.get("target_address") is not None:
            raise FocusRuntimeError("complete the active target before folding")
        active["status"] = "consumed"
        active["consumed_by"] = "FOLD"
    state["panorama_version"] += 1
    selected_id = field["selected_center_ref"]
    selected = next(center for center in field["centers"] if center["center_id"] == selected_id)
    required_nodes = {
        node_id
        for node_id in selected["node_ids"]
        if any(
            membership.get("center_id") == selected_id
            and membership.get("closure_effect") == "required"
            for membership in state["addresses"][field["node_addresses"][node_id]]["center_membership"]
        )
    }
    realized_nodes = {
        node_id
        for node_id, address_id in field["node_addresses"].items()
        if state["addresses"][address_id]["modality"] == "[+]"
    }
    legacy_residuals = require_list(payload.get("residuals", []), "fold.residuals")
    latent_residuals = [
        normalize_residual(item, f"fold.latent_residuals[{index}]", latent=True)
        for index, item in enumerate(require_list(payload.get("latent_residuals", []), "fold.latent_residuals"))
    ]
    active_residuals = [
        normalize_residual(item, f"fold.active_residuals[{index}]", latent=False)
        for index, item in enumerate(require_list(payload.get("active_residuals", []), "fold.active_residuals"))
    ]
    # Empty legacy lists remain accepted so existing two-stage states can be folded.
    if legacy_residuals:
        raise FocusRuntimeError(
            "fold.residuals is legacy-only; use latent_residuals and active_residuals"
        )
    for item in latent_residuals:
        state["latent_residuals"][item["residual_id"]] = item
    for item in active_residuals:
        state["active_residuals"][item["residual_id"]] = item
        if item.get("addressing_result"):
            state["addressing_results"].append(item["addressing_result"])
    blocking = [item for item in active_residuals if item.get("blocking")]
    selected_closed = (
        required_nodes.issubset(realized_nodes)
        and not field["frontiers"]["expansion_required"]
        and not blocking
    )
    selected["closure_status"] = "closed" if selected_closed else "open"
    field_closed = selected_closed and all(
        center["status"] != "active" or center["closure_status"] == "closed"
        for center in field["centers"]
    )
    conclusion = require_text(payload.get("conclusion"), "fold.conclusion")
    evidence = require_list(payload.get("evidence", []), "fold.evidence")
    focus_return = {
        "selected_center_closure": selected_closed,
        "outputs": payload.get("outputs", []),
        "evidence": evidence,
        "peer_interface_effects": payload.get("peer_interface_effects", []),
        "latent_residuals": latent_residuals,
        "active_residuals": active_residuals,
        "reprojection_request": payload.get("reprojection_request"),
    }
    fold_summary = {
        "conclusion": conclusion,
        "evidence": evidence,
        "best": payload.get("best"),
        "upper": payload.get("upper"),
        "latent_residuals": latent_residuals,
        "active_residuals": active_residuals,
        "assumptions": payload.get("assumptions", []),
        "reopen": field["root_address_id"],
    }
    field["focus_return"] = focus_return
    field["fold_summary"] = fold_summary
    field["closure_audit"] = {
        "selected_center_closure": selected_closed,
        "field_closure": field_closed,
        "active_residuals": active_residuals,
        "latent_openness": latent_residuals,
    }
    if field_closed:
        field["remaining_closure_gap"] = None
        address_snapshot = {
            node_id: {
                "address_id": address_id,
                "modality": state["addresses"][address_id]["modality"],
                "address_revision_id": state["addresses"][address_id]["address_revision_id"],
            }
            for node_id, address_id in field["node_addresses"].items()
        }
        snapshot_hash = stable_hash(
            "snapshot",
            {
                "field_id": field["field_id"],
                "contract": field["contract"],
                "selected_center": field["selected_center_ref"],
                "addresses": address_snapshot,
                "conclusion": conclusion,
                "evidence": evidence,
            },
            size=64,
        )
        previous_versions = [
            item
            for item in state["field_closure_versions"]
            if item.get("field_id") == field["field_id"]
        ]
        current_same = next(
            (
                item
                for item in reversed(previous_versions)
                if item.get("status") == "current" and item.get("snapshot_hash") == snapshot_hash
            ),
            None,
        )
        if current_same is None:
            parent_versions = [previous_versions[-1]["version_id"]] if previous_versions else []
            version = {
                "version_id": stable_hash(
                    "closurev",
                    {
                        "field_id": field["field_id"],
                        "snapshot_hash": snapshot_hash,
                        "parents": parent_versions,
                    },
                ),
                "field_id": field["field_id"],
                "field_version_id": field["field_version_id"],
                "parent_versions": parent_versions,
                "snapshot_hash": snapshot_hash,
                "status": "current",
                "conclusion": conclusion,
                "evidence": evidence,
                "created_at": now_iso(),
            }
            for previous in current_versions_for_field(state, field["field_id"]):
                previous["status"] = "superseded"
            state["field_closure_versions"].append(version)
            field["current_closure_version_id"] = version["version_id"]
            for branch in reversed(state["version_branches"]):
                if branch.get("field_id") == field["field_id"] and branch.get("status") == "open":
                    branch["result_versions"].append(version["version_id"])
                    break
        else:
            field["current_closure_version_id"] = current_same["version_id"]
        certificate = {
            "certificate_id": stable_hash(
                "closurecert",
                {
                    "field_id": field["field_id"],
                    "version_id": field["current_closure_version_id"],
                    "evidence": evidence,
                },
            ),
            "field_id": field["field_id"],
            "version_id": field["current_closure_version_id"],
            "status": "active",
            "selected_center_closure": selected_closed,
            "field_closure": field_closed,
            "evidence": evidence,
            "invalidation_triggers": list(
                field["projection_certificate"].get("invalidation_triggers", [])
            ),
            "created_at": now_iso(),
        }
        field["closure_certificates"].append(certificate)
    elif payload.get("remaining_closure_gap"):
        field["remaining_closure_gap"] = require_text(
            payload.get("remaining_closure_gap"), "fold.remaining_closure_gap"
        )
    elif blocking:
        field["remaining_closure_gap"] = "; ".join(
            str(item.get("description", "blocking residual")) for item in blocking
        )
    else:
        field["remaining_closure_gap"] = "selected center returned; peer or field obligations remain open"
    state["phase"] = "closed" if field_closed and field["global_depth"] == 0 else "folded"
    drive = None
    if state["mode"] == "constructive":
        if field["global_depth"] > 0:
            drive = record_decision(
                state,
                "UNWIND",
                "the child field has folded and must return through its parent interface",
            )
        elif field_closed:
            drive = record_decision(
                state,
                "NOOP",
                "the current field is relatively closed; no further Focus motion is required",
            )
        elif blocking:
            drive = record_decision(
                state,
                "BLOCKED",
                "an active residual still blocks relative closure",
            )
        else:
            drive = record_decision(
                state,
                "REFRAME_FIELD",
                "the selected center returned but peer or field obligations remain open",
            )
    append_event(
        state,
        "FOLD",
        {
            "field_id": field["field_id"],
            "selected_center_closure": selected_closed,
            "field_closure": field_closed,
            "reprojection_request": focus_return["reprojection_request"],
            "decision_id": None if drive is None else drive["decision_id"],
        },
    )
    require_valid(state)
    write_state(path, state)
    print(
        canonical_json(
            {
                "field_id": field["field_id"],
                "selected_center_closed": selected_closed,
                "field_closed": field_closed,
                "decision": (
                    drive["decision"]
                    if drive is not None
                    else (
                        "UNWIND"
                        if field["global_depth"] > 0
                        else ("F0_COMPLETE" if field_closed else "REFOCUS_OR_REMODEL")
                    )
                ),
            }
        )
    )
    return 0


def cmd_activate_residual(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    payload = load_json_value(args.payload, "residual activation payload")
    residual_id = require_text(payload.get("residual_id"), "activation.residual_id")
    latent = state["latent_residuals"].get(residual_id)
    if not isinstance(latent, dict):
        raise FocusRuntimeError(f"unknown latent residual: {residual_id}")
    disposition = payload.get("disposition")
    if disposition not in RESIDUAL_DISPOSITIONS:
        raise FocusRuntimeError(f"invalid residual disposition: {disposition}")
    evidence = require_list(payload.get("evidence", []), "activation.evidence")
    if not evidence:
        raise FocusRuntimeError("residual activation requires evidence")
    binding = latent["address_binding"]
    transition: dict[str, Any] = {
        "residual_id": residual_id,
        "disposition": disposition,
        "evidence": evidence,
        "from_binding": binding,
        "time": now_iso(),
    }
    if disposition == "required-frontier":
        if binding.get("kind") != "bound":
            raise FocusRuntimeError("required-frontier needs a bound legal address")
        address_id = binding["address_id"]
        field = current_field(state)
        if address_id not in field["node_addresses"].values():
            raise FocusRuntimeError("bound address is not in the current Focus field")
        if address_id not in field["frontiers"]["expansion_required"]:
            field["frontiers"]["expansion_required"].append(address_id)
        address = state["addresses"][address_id]
        if "expansion_required" not in address["frontier_membership"]:
            address["frontier_membership"].append("expansion_required")
        field["closure_audit"]["selected_center_closure"] = False
        field["closure_audit"]["field_closure"] = False
        field["remaining_closure_gap"] = latent["description"]
        state["phase"] = "framed" if field["global_depth"] == 0 else "expanded"
    elif disposition == "address-birth":
        if binding.get("kind") != "candidate":
            raise FocusRuntimeError("address-birth needs a candidate binding")
        candidate = state["address_candidates"].get(binding["candidate_address_id"])
        resulting = require_text(payload.get("resulting_address_id"), "activation.resulting_address_id")
        if not isinstance(candidate, dict) or resulting not in state["addresses"]:
            raise FocusRuntimeError("address-birth needs a registered candidate and legal resulting address")
        candidate["calibration_status"] = "calibrated"
        candidate["resulting_address_id"] = resulting
        transition["resulting_address_id"] = resulting
        field = current_field(state)
        field["closure_audit"]["selected_center_closure"] = False
        field["closure_audit"]["field_closure"] = False
        state["phase"] = "framed" if field["global_depth"] == 0 else "expanded"
    elif disposition == "active-residual":
        result = payload.get("addressing_result")
        if not isinstance(result, dict) or result.get("modality") not in {"[-]", "[∅]"}:
            raise FocusRuntimeError("active-residual requires addressing_result modality [-] or [∅]")
        active_id = require_text(payload.get("active_residual_id"), "activation.active_residual_id")
        active = {
            "residual_id": active_id,
            "classification": "active-residual",
            "description": latent["description"],
            "address_binding": binding,
            "blocking": bool(payload.get("blocking", True)),
            "evidence": evidence,
            "source_latent_residual_id": residual_id,
            "addressing_result": result,
        }
        state["active_residuals"][active_id] = active
        state["addressing_results"].append(result)
        transition["active_residual_id"] = active_id
        if active["blocking"]:
            field = current_field(state)
            field["closure_audit"]["selected_center_closure"] = False
            field["closure_audit"]["field_closure"] = False
            field["closure_audit"].setdefault("active_residuals", []).append(active)
            field["remaining_closure_gap"] = active["description"]
            state["phase"] = "blocked"
    state["residual_history"].append({**latent, "transition": transition})
    del state["latent_residuals"][residual_id]
    append_event(state, "LATENT_RESIDUAL_ACTIVATED", transition)
    require_valid(state)
    write_state(path, state)
    print(canonical_json(transition))
    return 0


def cmd_unwind(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = read_state(path)
    require_valid(state)
    if len(state["field_stack"]) <= 1:
        raise FocusRuntimeError("cannot unwind above the root field")
    if state["mode"] == "constructive":
        active = state.get("active_decision")
        if not isinstance(active, dict) or active.get("decision") != "UNWIND":
            raise FocusRuntimeError("constructive unwind requires an active UNWIND decision")
        active["status"] = "consumed"
        active["consumed_by"] = "UNWIND"
    child_frame = state["field_stack"][-1]
    child_field = find_field(state, child_frame["field_id"])
    if child_field.get("fold_summary") is None:
        raise FocusRuntimeError("fold the current child field before unwinding")
    state["field_stack"].pop()
    parent_field = current_field(state)
    parent_address = state["addresses"][child_frame["parent_address"]]
    state["panorama_version"] += 1
    parent_address["returned_interface"] = child_field["focus_return"]
    parent_address["exposure_state"] = "compressed"
    for frontier_name in ("action", "expansion_required", "expansion_latent"):
        if parent_address["address_id"] in parent_field["frontiers"][frontier_name]:
            parent_field["frontiers"][frontier_name].remove(parent_address["address_id"])
    if parent_address["address_id"] not in parent_field["frontiers"]["compressed"]:
        parent_field["frontiers"]["compressed"].append(parent_address["address_id"])
    parent_address["frontier_membership"] = ["compressed"]
    if child_field["closure_audit"]["field_closure"]:
        parent_address["modality"] = "[+]"
        parent_address["evidence"] = list(parent_address.get("evidence", [])) + child_field["focus_return"]["evidence"]
    parent_address["address_revision_id"] = stable_hash(
        "addrrev",
        {
            "address_id": parent_address["address_id"],
            "returned_interface": parent_address["returned_interface"],
            "modality": parent_address["modality"],
        },
    )
    parent_address["panorama_version"] = state["panorama_version"]
    refresh_action_frontier(state, parent_field)
    state["phase"] = "framed" if parent_field["global_depth"] == 0 else "expanded"
    drive = suggested_drive_decision(state, parent_field) if state["mode"] == "constructive" else None
    append_event(
        state,
        "UNWIND",
        {
            "from_field": child_field["field_id"],
            "to_field": parent_field["field_id"],
            "parent_address": parent_address["address_id"],
            "interface_realized": parent_address["modality"] == "[+]",
        },
    )
    require_valid(state)
    write_state(path, state)
    print(
        canonical_json(
            {
                "current_field": parent_field["field_id"],
                "returned_from": child_field["field_id"],
                "parent_address": parent_address["address_id"],
                "decision": drive["decision"] if drive is not None else "CONTINUE_OR_FOLD",
                "target_address": None if drive is None else drive["target_address"],
            }
        )
    )
    return 0


def state_summary(state: dict[str, Any]) -> dict[str, Any]:
    field = current_field(state) if state.get("field_stack") else None
    return {
        "run_id": state.get("run_id"),
        "phase": state.get("phase"),
        "revision": state.get("revision"),
        "panorama_version": state.get("panorama_version"),
        "stack_depth": max(0, len(state.get("field_stack", [])) - 1),
        "current_field": None if field is None else field["field_id"],
        "goal": None if field is None else field["contract"]["goal"],
        "closure_gap": None if field is None else field["remaining_closure_gap"],
        "selected_center": None if field is None else field["selected_center_ref"],
        "peer_centers": [] if field is None else field["peer_center_refs"],
        "current_addresses": {} if field is None else field["node_addresses"],
        "frontiers": None if field is None else field["frontiers"],
        "address_candidates": len(state.get("address_candidates", {})),
        "latent_residuals": len(state.get("latent_residuals", {})),
        "active_residuals": len(state.get("active_residuals", {})),
        "pending_deltas": sum(
            1 for item in state.get("knowledge_deltas", {}).values() if item.get("status") == "pending"
        ),
        "active_decision": state.get("active_decision"),
        "closure_versions": [
            item.get("version_id")
            for item in state.get("field_closure_versions", [])
            if field is not None and item.get("field_id") == field.get("field_id")
        ],
        "open_version_branches": [
            item.get("branch_id")
            for item in state.get("version_branches", [])
            if item.get("status") == "open"
        ],
        "observations": len(state.get("observations", [])),
        "trace_observation_refs": [] if field is None else field.get("trace_observation_refs", []),
        "closure_audit": None if field is None else field["closure_audit"],
    }


def cmd_validate(args: argparse.Namespace) -> int:
    state = read_state(Path(args.state))
    errors = validate_state(state)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"valid": True, "schema_version": SCHEMA_VERSION}, ensure_ascii=False))
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    state = read_state(Path(args.state))
    require_valid(state)
    print(json.dumps(state_summary(state), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a new constructive Focus state")
    init.add_argument("state")
    init.add_argument("--task", required=True)
    init.add_argument(
        "--mode",
        default="constructive",
        choices=["constructive", "clarify", "action", "sidecar"],
    )
    init.set_defaults(func=cmd_init)

    decide = sub.add_parser("decide", help="record and validate the next Focus decision")
    decide.add_argument("state")
    decide.add_argument("--payload", required=True, help="JSON object or @path")
    decide.set_defaults(func=cmd_decide)

    ingest = sub.add_parser("ingest-delta", help="preserve a raw evidence or correction delta")
    ingest.add_argument("state")
    ingest.add_argument("--payload", required=True, help="JSON object or @path")
    ingest.set_defaults(func=cmd_ingest_delta)

    assess = sub.add_parser(
        "assess-impact", help="classify a delta and invalidate the minimum affected scope"
    )
    assess.add_argument("state")
    assess.add_argument("--payload", required=True, help="JSON object or @path")
    assess.set_defaults(func=cmd_assess_impact)

    candidate = sub.add_parser("register-candidate", help="register an uncalibrated address candidate")
    candidate.add_argument("state")
    candidate.add_argument("--payload", required=True, help="JSON object or @path")
    candidate.set_defaults(func=cmd_register_candidate)

    resolve_candidate = sub.add_parser("resolve-candidate", help="calibrate or reject an address candidate")
    resolve_candidate.add_argument("state")
    resolve_candidate.add_argument("--payload", required=True, help="JSON object or @path")
    resolve_candidate.set_defaults(func=cmd_resolve_candidate)

    observe = sub.add_parser("observe", help="record an already executed task trace")
    observe.add_argument("state")
    observe.add_argument("--payload", required=True, help="JSON object or @path")
    observe.set_defaults(func=cmd_observe)

    reconstruct = sub.add_parser(
        "reconstruct", help="derive a Focus field from observed execution evidence"
    )
    reconstruct.add_argument("state")
    reconstruct.add_argument("--payload", required=True, help="JSON object or @path")
    reconstruct.set_defaults(func=cmd_reconstruct)

    frame = sub.add_parser("frame", help="run Focus-1 field/problem framing")
    frame.add_argument("state")
    frame.add_argument("--payload", required=True, help="JSON object or @path")
    frame.set_defaults(func=cmd_frame)

    expand = sub.add_parser("expand", help="run one Focus-2 recursive expansion")
    expand.add_argument("state")
    expand.add_argument("--payload", required=True, help="JSON object or @path")
    expand.set_defaults(func=cmd_expand)

    execute = sub.add_parser("execute", help="realize ready addresses with evidence")
    execute.add_argument("state")
    execute.add_argument("--payload", required=True, help="JSON object or @path")
    execute.set_defaults(func=cmd_execute)

    fold = sub.add_parser("fold", help="audit and fold the current Focus field")
    fold.add_argument("state")
    fold.add_argument("--payload", required=True, help="JSON object or @path")
    fold.set_defaults(func=cmd_fold)

    activate = sub.add_parser("activate-residual", help="activate and route one latent residual")
    activate.add_argument("state")
    activate.add_argument("--payload", required=True, help="JSON object or @path")
    activate.set_defaults(func=cmd_activate_residual)

    unwind = sub.add_parser("unwind", help="return one folded child field to its parent")
    unwind.add_argument("state")
    unwind.set_defaults(func=cmd_unwind)

    validate = sub.add_parser("validate", help="validate a constructive Focus state")
    validate.add_argument("state")
    validate.set_defaults(func=cmd_validate)

    summary = sub.add_parser("summary", help="show the compact active Focus state")
    summary.add_argument("state")
    summary.set_defaults(func=cmd_summary)
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        return int(args.func(args))
    except FocusRuntimeError as exc:
        print(f"focus-runtime: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
