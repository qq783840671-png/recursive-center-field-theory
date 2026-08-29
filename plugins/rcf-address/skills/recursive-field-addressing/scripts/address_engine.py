#!/usr/bin/env python3
"""Deterministic state validator and motion applier for Address Engine."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ADDRESS_RE = re.compile(r"^[A-Z](?:\d+(?:\.\d+)*)?$")
ENGINE_VERSION = "0.5-experimental"
SUPPORTED_ENGINE_VERSIONS = {"0.3-experimental", "0.4-experimental", ENGINE_VERSION}
MODALS = {"realized", "potential", "prohibited"}
LIFECYCLES = {"active", "historical", "retired"}
PREDECESSORS = {"satisfied", "valid-interface", "missing", "disputed"}
MOTIONS = {"INGEST", "FORM", "MAP", "GLOBAL", "FOCUS", "ABSORB", "REALIZE", "REBUILD", "ASCEND"}
STRUCTURE_STATUSES = {"forming", "tentative", "validated", "invalid"}
CENTER_STATUSES = {"candidate", "selected", "validated", "disputed", "invalid"}
REACH_KINDS = {"next", "finite-deep", "unknown", "unreachable"}
FIELD_OPENING_STATUSES = {"hypothesized", "forming", "validated"}
FRONTIER_KEYS = {"action", "expansion_required", "expansion_latent", "compressed"}
RELATION_ROLES = {
    "dependency",
    "support",
    "conflict",
    "coupling",
    "source",
    "structural-condition",
    "amplifier",
    "threshold",
    "trigger",
    "propagation",
}


def frontier_state(state: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Return typed frontiers; map legacy unified frontier to latent only."""
    frontiers = state.get("frontiers")
    if isinstance(frontiers, dict):
        return {
            key: value if isinstance(value, list) else []
            for key, value in frontiers.items()
            if key in FRONTIER_KEYS
        }
    legacy = state.get("frontier")
    return {
        "action": [],
        "expansion_required": [],
        "expansion_latent": legacy if isinstance(legacy, list) else [],
        "compressed": [],
    }


def snapshot_hash(snapshot: dict[str, Any]) -> str | None:
    try:
        payload = json.dumps(
            snapshot,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        return None
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def child_opening_issues(
    opening: dict[str, Any], address: dict[str, Any], evidence_ids: set[str]
) -> list[str]:
    status = address.get("field_opening_status")
    issues: list[str] = []
    if status not in FIELD_OPENING_STATUSES:
        return ["field_opening_status is invalid"]
    if status != "validated" and address.get("modal") != "potential":
        issues.append("an unvalidated child field must remain potential")
    snapshot = opening.get("state_snapshot")
    if not isinstance(snapshot, dict):
        return [*issues, "state_snapshot must be an inline restorable object"]
    digest = snapshot_hash(snapshot)
    if digest is None or opening.get("state_hash") != digest:
        issues.append("state_hash does not match state_snapshot")
    sections: dict[str, dict[str, Any]] = {}
    for name in ("field", "graph", "order", "center", "residual_audit", "return_interface"):
        value = snapshot.get(name)
        if not isinstance(value, dict):
            issues.append(f"state_snapshot.{name} must be an object")
            value = {}
        sections[name] = value
    frontiers = snapshot.get("frontiers")
    if not isinstance(frontiers, dict):
        issues.append("state_snapshot.frontiers must be an object")
        frontiers = {}
    for name in ("action", "expansion_required", "expansion_latent", "compressed"):
        if not isinstance(frontiers.get(name), list):
            issues.append(f"state_snapshot.frontiers.{name} must be a list")
    residuals = snapshot.get("residuals")
    if not isinstance(residuals, list) or not all(isinstance(item, dict) for item in residuals):
        issues.append("state_snapshot.residuals must be a list of objects")
        residuals = []

    field = sections["field"]
    graph = sections["graph"]
    order = sections["order"]
    center = sections["center"]
    residual_audit = sections["residual_audit"]
    return_interface = sections["return_interface"]
    roots = address.get("root_path_nodes") or []
    expected_parent = roots[-2] if len(roots) > 1 else None
    bindings = {
        "field_id": (field.get("field_id"), opening.get("field_id")),
        "local_root": (field.get("local_root"), "F0"),
        "parent_address": (field.get("parent_address"), expected_parent),
        "contract_status": (field.get("contract_status"), opening.get("contract_status")),
        "graph_status": (graph.get("status"), opening.get("graph_status")),
        "order_status": (order.get("status"), opening.get("order_status")),
        "center_status": (center.get("status"), opening.get("center_status")),
        "recursive_structure_status": (
            snapshot.get("recursive_structure_status"),
            opening.get("recursive_structure_status"),
        ),
        "residual_audit_status": (
            residual_audit.get("status"),
            opening.get("residual_audit_status"),
        ),
        "return_interface_status": (
            return_interface.get("status"),
            opening.get("return_interface_status"),
        ),
    }
    for name, (actual, expected) in bindings.items():
        if actual != expected:
            issues.append(f"state_snapshot {name} does not match its audit")
    if return_interface.get("parent_address") != expected_parent:
        issues.append("return interface does not bind back to the parent")

    allowed = {
        "hypothesized": {
            "contract_status": {"candidate", "provisional"},
            "graph_status": {"forming", "tentative"},
            "order_status": {"forming", "tentative"},
            "center_status": {"candidate", "selected"},
            "recursive_structure_status": {"hypothesized"},
            "residual_audit_status": {"performed"},
            "return_interface_status": {"tentative"},
        },
        "forming": {
            "contract_status": {"provisional", "stable"},
            "graph_status": {"forming", "tentative", "validated"},
            "order_status": {"forming", "tentative", "validated"},
            "center_status": {"candidate", "selected", "validated"},
            "recursive_structure_status": {"forming"},
            "residual_audit_status": {"performed"},
            "return_interface_status": {"tentative", "valid"},
        },
        "validated": {
            "contract_status": {"stable"},
            "graph_status": {"validated"},
            "order_status": {"validated"},
            "center_status": {"validated"},
            "recursive_structure_status": {"validated"},
            "residual_audit_status": {"performed"},
            "return_interface_status": {"valid"},
        },
    }
    for name, accepted in allowed[status].items():
        if opening.get(name) not in accepted:
            issues.append(f"{name} is incompatible with field_opening_status={status}")

    graph_nodes = graph.get("nodes")
    graph_addresses: list[str] = []
    if not isinstance(graph_nodes, list):
        issues.append("state_snapshot.graph.nodes must be a list")
    else:
        for item in graph_nodes:
            value = item.get("address") if isinstance(item, dict) else None
            if not isinstance(value, str) or not value:
                issues.append("child graph node needs a non-empty address")
            else:
                graph_addresses.append(value)
        if graph_addresses.count("F0") != 1 or len(graph_addresses) != len(set(graph_addresses)):
            issues.append("child graph needs one local F0 and unique addresses")
    graph_address_set = set(graph_addresses)
    graph_relation_map: dict[str, dict[str, Any]] = {}
    graph_relations = graph.get("relations")
    if not isinstance(graph_relations, list):
        issues.append("state_snapshot.graph.relations must be a list")
    else:
        for relation in graph_relations:
            if not isinstance(relation, dict) or not relation.get("id"):
                issues.append("child graph relation needs an id")
                continue
            graph_relation_map[relation["id"]] = relation
            if relation.get("source") not in graph_address_set or relation.get("target") not in graph_address_set:
                issues.append(f"child graph relation {relation['id']} has an unknown endpoint")

    order_nodes = order.get("nodes")
    order_addresses: list[str] = []
    if not isinstance(order_nodes, list):
        issues.append("state_snapshot.order.nodes must be a list")
    else:
        for item in order_nodes:
            value = item.get("address") if isinstance(item, dict) else item
            if not isinstance(value, str) or not value:
                issues.append("child order node needs a non-empty address")
            else:
                order_addresses.append(value)
        if set(order_addresses) - graph_address_set:
            issues.append("child order contains a node absent from the graph")
    order_address_set = set(order_addresses)
    adjacency: dict[str, set[str]] = {}
    order_relations = order.get("relations")
    if not isinstance(order_relations, list):
        issues.append("state_snapshot.order.relations must be a list")
    else:
        for relation in order_relations:
            if not isinstance(relation, dict) or not relation.get("id"):
                issues.append("child order relation needs an id")
                continue
            predecessor = relation.get("predecessor")
            successor = relation.get("successor")
            graph_relation = graph_relation_map.get(relation["id"])
            if predecessor not in order_address_set or successor not in order_address_set:
                issues.append(f"child order relation {relation['id']} has an unknown endpoint")
            elif not graph_relation or (
                graph_relation.get("source") != predecessor
                or graph_relation.get("target") != successor
                or graph_relation.get("relation_type") != "dependency"
                or graph_relation.get("necessity") != "required"
            ):
                issues.append(f"child order relation {relation['id']} lacks a matching required graph edge")
            adjacency.setdefault(str(predecessor), set()).add(str(successor))
    visiting: set[str] = set()
    visited: set[str] = set()

    def cyclic(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(cyclic(child) for child in adjacency.get(node, set())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    if any(cyclic(node) for node in order_address_set):
        issues.append("child necessary order contains a cycle")

    candidates = center.get("candidates")
    if not isinstance(candidates, list) or not all(isinstance(item, dict) for item in candidates):
        issues.append("state_snapshot.center.candidates must be a list of objects")
        candidates = []
    selected = next(
        (item for item in candidates if item.get("id") == center.get("selected")), None
    )
    if status == "validated":
        if not isinstance(selected, dict) or selected.get("minimality_status") != "validated":
            issues.append("validated child needs a selected minimality-validated center")
        elif set(selected.get("members") or []) - order_address_set:
            issues.append("validated center members must lie in the child order")
        if not (opening.get("evidence_refs") or []):
            issues.append("validated child opening needs evidence")
        for residual in residuals:
            relation = residual.get("address_relation") or {}
            reach = relation.get("reach") or {}
            if residual.get("absorption_status") == "absorbed":
                continue
            if (
                residual.get("modal_status") != "[◇]"
                or relation.get("kind") != "frontier"
                or relation.get("gate_status") != "legal"
                or reach.get("kind") not in {"next", "finite-deep"}
            ):
                issues.append("validated child contains a non-closing active residual")
                break
    refs = opening.get("evidence_refs") or []
    if not all(ref in evidence_ids for ref in refs):
        issues.append("field opening evidence does not resolve")
    return issues


def validate_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    engine_version = state.get("engine_version")
    if engine_version not in SUPPORTED_ENGINE_VERSIONS:
        errors.append("engine_version is unsupported")
    if engine_version == ENGINE_VERSION:
        frontiers_value = state.get("frontiers")
        if not isinstance(frontiers_value, dict):
            errors.append("frontiers must be a typed object in engine 0.5")
        elif set(frontiers_value) != FRONTIER_KEYS:
            errors.append("frontiers must contain exactly action, expansion_required, expansion_latent, compressed")
        if "frontier" in state:
            errors.append("legacy frontier cannot be mixed into engine 0.5 state")
        candidates = state.get("address_candidates")
        if not isinstance(candidates, list):
            errors.append("address_candidates must be a list in engine 0.5")
            candidates = []
        candidate_ids: set[str] = set()
        for index, candidate in enumerate(candidates):
            label = f"address_candidates[{index}]"
            candidate_id = candidate.get("candidate_address_id") if isinstance(candidate, dict) else None
            if not candidate_id or candidate_id in candidate_ids:
                errors.append(f"{label}.candidate_address_id is missing or duplicated")
            else:
                candidate_ids.add(candidate_id)
            if candidate.get("calibration_status") not in {
                "hypothesized", "calibrating", "calibrated", "rejected"
            }:
                errors.append(f"{label}.calibration_status is invalid")
            if "modal" in candidate:
                errors.append(f"{label} must not carry legal-address modal")
    field = state.get("field") or {}
    for key in (
        "field_id",
        "field_version",
        "f0_lineage",
        "contract_status",
        "graph_status",
        "order_status",
        "center_status",
        "formation_revision",
    ):
        if not field.get(key):
            errors.append(f"FIELD_CONTEXT_REQUIRED: field.{key} is missing")
    if field.get("graph_status") not in STRUCTURE_STATUSES:
        errors.append("field.graph_status is invalid")
    if field.get("order_status") not in STRUCTURE_STATUSES:
        errors.append("field.order_status is invalid")
    if field.get("center_status") not in CENTER_STATUSES:
        errors.append("field.center_status is invalid")
    if not isinstance(field.get("formation_revision"), int) or field.get("formation_revision", 0) < 1:
        errors.append("field.formation_revision must identify an audited forward FORM motion")

    evidence_ids = {
        item.get("id")
        for item in state.get("evidence") or []
        if isinstance(item, dict) and item.get("id")
    }
    if engine_version == ENGINE_VERSION:
        if field.get("formation_confirmation_status") not in {"confirmed", "reused"}:
            errors.append("field.formation_confirmation_status must be confirmed or reused")
        confirmation_refs = field.get("formation_confirmation_evidence_refs") or []
        if not confirmation_refs or not all(ref in evidence_ids for ref in confirmation_refs):
            errors.append("field.formation_confirmation_evidence_refs must resolve to stored evidence")
    dependency_by_id: dict[str, dict[str, Any]] = {}
    for index, relation in enumerate(state.get("dependency_relations") or []):
        label = f"dependency_relations[{index}]"
        relation_id = relation.get("id")
        if not relation_id:
            errors.append(f"{label}.id is missing")
            continue
        if relation_id in dependency_by_id:
            errors.append(f"duplicate dependency relation id: {relation_id}")
        dependency_by_id[relation_id] = relation
        if not relation.get("source") or not relation.get("target"):
            errors.append(f"{label} needs source and target")
        if relation.get("necessity") != "required":
            errors.append(f"{label}.necessity must be required")
        if relation.get("validity") != "valid":
            errors.append(f"{label}.validity must be valid")
        refs = relation.get("evidence_refs") or []
        if not refs or not all(ref in evidence_ids for ref in refs):
            errors.append(f"{label}.evidence_refs must resolve to stored evidence")

    objects = state.get("objects") or []
    object_ids = {item.get("object_id") for item in objects if item.get("object_id")}
    addresses = state.get("addresses") or []
    address_ids: set[str] = set()
    address_by_id: dict[str, dict[str, Any]] = {}

    for index, address in enumerate(addresses):
        label = f"addresses[{index}]"
        address_id = address.get("address_id")
        if not address_id:
            errors.append(f"{label}.address_id is missing")
        elif address_id in address_ids:
            errors.append(f"duplicate address_id: {address_id}")
        else:
            address_ids.add(address_id)
            address_by_id[address_id] = address

        if address.get("object_id") not in object_ids:
            errors.append(f"{label}.object_id does not reference a known object")
        path = address.get("display_path", "")
        if not ADDRESS_RE.fullmatch(path):
            errors.append(f"{label}.display_path is not a valid F0-facing path")
        roots = address.get("root_path_nodes") or []
        if not roots or roots[0] != field.get("f0_lineage"):
            errors.append(f"{label} is rootless or does not start at the current F0 lineage")
        if not all(isinstance(node, str) and node for node in roots):
            errors.append(f"{label}.root_path_nodes must be a non-empty string list")
        root_edges = address.get("root_path_relation_ids") or []
        if len(root_edges) != max(0, len(roots) - 1):
            errors.append(f"{label}.root_path_relation_ids must cover every adjacent root-path step")
        else:
            for step, relation_id in enumerate(root_edges):
                relation = dependency_by_id.get(relation_id)
                if relation is None:
                    errors.append(f"{label} references unknown root-path relation {relation_id}")
                elif relation.get("source") != roots[step] or relation.get("target") != roots[step + 1]:
                    errors.append(f"{label} root-path relation {relation_id} is reversed or leaves the path")
        address_evidence = address.get("evidence_refs") or []
        if not address_evidence or not all(ref in evidence_ids for ref in address_evidence):
            errors.append(f"{label}.evidence_refs must resolve to stored evidence")
        opening = address.get("field_opening_audit")
        recursive_address = bool(re.search(r"\d", path))
        parent_binding = address.get("parent_binding")
        if recursive_address:
            expected_parent = roots[-2] if len(roots) > 1 else field.get("f0_lineage")
            if not isinstance(parent_binding, dict):
                errors.append(f"{label}.parent_binding is required for a recursive address")
            else:
                if parent_binding.get("parent_address") != expected_parent:
                    errors.append(f"{label}.parent_binding.parent_address is invalid")
                for key in ("parent_field_id", "required_function", "parent_return"):
                    if not parent_binding.get(key):
                        errors.append(f"{label}.parent_binding.{key} is missing")
        relation_roles = address.get("relation_roles") or []
        if not isinstance(relation_roles, list) or any(role not in RELATION_ROLES for role in relation_roles):
            errors.append(f"{label}.relation_roles is invalid")
        contribution = address.get("contribution_annotation")
        if contribution is not None:
            if not isinstance(contribution, dict):
                errors.append(f"{label}.contribution_annotation must be an object")
            else:
                if not contribution.get("decomposition_contract_ref"):
                    errors.append(f"{label}.contribution_annotation needs a decomposition contract")
                refs = contribution.get("evidence_refs") or []
                if not refs or not all(ref in evidence_ids for ref in refs):
                    errors.append(f"{label}.contribution_annotation.evidence_refs is invalid")
                for interval_name in ("conditional_interval", "residual_share_interval"):
                    interval = contribution.get(interval_name)
                    if interval is None:
                        continue
                    if (
                        not isinstance(interval, list)
                        or len(interval) != 2
                        or any(not isinstance(value, (int, float)) for value in interval)
                        or not 0 <= interval[0] <= interval[1] <= 1
                    ):
                        errors.append(f"{label}.contribution_annotation.{interval_name} is invalid")
        if recursive_address and not isinstance(opening, dict):
            errors.append(f"{label}.field_opening_audit is required")
        elif isinstance(opening, dict):
            if not opening.get("field_id"):
                errors.append(f"{label}.field_opening_audit.field_id is missing")
            if opening.get("local_root") != "F0":
                errors.append(f"{label}.field_opening_audit.local_root must be F0")
            expected_parent = roots[-2] if len(roots) > 1 else field.get("f0_lineage")
            if opening.get("parent_address") != expected_parent:
                errors.append(f"{label}.field_opening_audit.parent_address is invalid")
            if not opening.get("state_ref"):
                errors.append(f"{label}.field_opening_audit.state_ref is missing")
            opening_evidence = opening.get("evidence_refs") or []
            if not isinstance(opening_evidence, list) or not all(
                ref in evidence_ids for ref in opening_evidence
            ):
                errors.append(f"{label}.field_opening_audit.evidence_refs is invalid")
            for issue in child_opening_issues(opening, address, evidence_ids):
                errors.append(f"{label}.field_opening_audit.{issue}")
        modal = address.get("modal")
        if modal not in MODALS:
            errors.append(f"{label}.modal is invalid")
        if engine_version == ENGINE_VERSION:
            if address.get("calibration_status") != "calibrated":
                errors.append(f"{label}.calibration_status must be calibrated")
            if modal not in {"realized", "potential"}:
                errors.append(f"{label} legal address modal must be realized or potential")
        if address.get("lifecycle") not in LIFECYCLES:
            errors.append(f"{label}.lifecycle is invalid")
        predecessor = (address.get("predecessor_state") or {}).get("status")
        if predecessor not in PREDECESSORS:
            errors.append(f"{label}.predecessor_state.status is invalid")
        if modal in {"realized", "potential"} and predecessor not in {"satisfied", "valid-interface"}:
            errors.append(f"{label} lacks satisfied predecessors or a valid interface")
        if modal == "realized" and field.get("contract_status") != "stable":
            errors.append(f"{label} is realized in a non-stable field")
        if (
            modal == "realized"
            and recursive_address
            and address.get("field_opening_status") != "validated"
        ):
            errors.append(f"{label} cannot be realized before its child field validates")

    typed_frontiers = frontier_state(state)
    expansion_required_ids: set[str] = set()
    expansion_latent_ids: set[str] = set()
    for frontier_name in FRONTIER_KEYS:
        entries = typed_frontiers.get(frontier_name, [])
        if not isinstance(entries, list):
            errors.append(f"frontiers.{frontier_name} must be a list")
            continue
        seen: set[str] = set()
        for index, item in enumerate(entries):
            label = f"frontiers.{frontier_name}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be an object")
                continue
            address_id = item.get("address_id")
            address = address_by_id.get(address_id)
            if not address:
                errors.append(f"{label} references an unknown address")
            elif frontier_name in {"action", "expansion_required", "expansion_latent"} and address.get("modal") != "potential":
                errors.append(f"{label} must reference a potential address")
            elif address.get("lifecycle") != "active":
                errors.append(f"{label} must reference an active address")
            if address_id in seen:
                errors.append(f"{label} duplicates an address in the same frontier")
            seen.add(address_id)
            refs = item.get("evidence_refs") or []
            if engine_version == ENGINE_VERSION and (not refs or not all(ref in evidence_ids for ref in refs)):
                errors.append(f"{label}.evidence_refs must resolve to stored evidence")
        if frontier_name == "expansion_required":
            expansion_required_ids = seen
        elif frontier_name == "expansion_latent":
            expansion_latent_ids = seen
    overlap = expansion_required_ids & expansion_latent_ids
    if overlap:
        errors.append("an address cannot be both expansion_required and expansion_latent")

    for index, item in enumerate(state.get("residual_links") or []):
        if engine_version == ENGINE_VERSION:
            binding = item.get("address_binding")
            if not isinstance(binding, dict):
                errors.append(f"residual_links[{index}].address_binding must be an object")
                continue
            kind = binding.get("kind")
            if kind not in {"bound", "candidate", "unaddressed"}:
                errors.append(f"residual_links[{index}].address_binding.kind is invalid")
            elif kind == "bound" and binding.get("address_id") not in address_ids:
                errors.append(f"residual_links[{index}] bound address is unknown")
            elif kind == "candidate" and binding.get("candidate_address_id") not in candidate_ids:
                errors.append(f"residual_links[{index}] candidate binding is unknown")
            if "modal" in item or "address_ref" in item:
                errors.append(f"residual_links[{index}] must not carry legacy address modality")
            if item.get("classification") not in {"latent-residual", "active-residual"}:
                errors.append(f"residual_links[{index}].classification is invalid")
            if item.get("classification") == "latent-residual" and not item.get(
                "activation_condition"
            ):
                errors.append(f"residual_links[{index}] latent residual needs activation_condition")
            result = item.get("addressing_result")
            if result is not None and (
                not isinstance(result, dict) or result.get("modality") not in {"[-]", "[∅]"}
            ):
                errors.append(f"residual_links[{index}].addressing_result is invalid")
            continue
        modal = item.get("modal")
        address_ref = item.get("address_ref")
        if modal == "no-address" and address_ref is not None:
            errors.append(f"residual_links[{index}] no-address must use address_ref null")
        if address_ref is not None and address_ref not in address_ids:
            errors.append(f"residual_links[{index}] references an unknown address")
        if modal == "potential":
            if item.get("relation_kind") not in {"frontier", "hypothesized"}:
                errors.append(f"residual_links[{index}].relation_kind is invalid")
            if item.get("gate_status") not in {"legal", "unverified", "illegal"}:
                errors.append(f"residual_links[{index}].gate_status is invalid")
            reach = item.get("reach") or {}
            if reach.get("kind") not in REACH_KINDS:
                errors.append(f"residual_links[{index}].reach.kind is invalid")
            estimate = reach.get("estimated_expansions")
            if estimate is not None and (not isinstance(estimate, int) or estimate < 1):
                errors.append(f"residual_links[{index}].reach.estimated_expansions must be positive")
            refs = reach.get("evidence_refs") or []
            if refs and not all(ref in evidence_ids for ref in refs):
                errors.append(f"residual_links[{index}].reach.evidence_refs is invalid")

    return errors


def addressability_issues(state: dict[str, Any]) -> list[str]:
    """Return structural blockers before an address-generating motion."""
    field = state.get("field") or {}
    issues: list[str] = []
    if field.get("contract_status") != "stable":
        issues.append("field contract is not stable")
    if field.get("graph_status") != "validated":
        issues.append("complete typed functional graph is not validated")
    if field.get("order_status") != "validated":
        issues.append("necessary partial order is not validated")
    if field.get("center_status") != "validated":
        issues.append("minimum-sufficient center is not validated")
    if not isinstance(field.get("formation_revision"), int) or field.get("formation_revision", 0) < 1:
        issues.append("no audited forward field formation exists")
    if state.get("engine_version") == ENGINE_VERSION and field.get(
        "formation_confirmation_status"
    ) not in {"confirmed", "reused"}:
        issues.append("field formation is not authorized")
    return issues


def provisional_closure_issues(state: dict[str, Any]) -> list[str]:
    """Reject fabricated potentials as support for provisional closure."""
    issues = addressability_issues(state)
    if state.get("engine_version") != ENGINE_VERSION:
        issues.append("legacy unified frontier cannot establish typed provisional closure")
    addresses = {
        item.get("address_id"): item
        for item in state.get("addresses") or []
        if isinstance(item, dict) and item.get("address_id")
    }
    frontiers = frontier_state(state)
    if frontiers.get("expansion_required"):
        issues.append("required expansion frontier is not empty")
    frontier_ids = {
        item.get("address_id")
        for name in ("expansion_required", "expansion_latent")
        for item in frontiers.get(name, [])
        if isinstance(item, dict)
    }
    for index, residual in enumerate(state.get("residual_links") or []):
        label = f"residual_links[{index}]"
        if state.get("engine_version") == ENGINE_VERSION:
            if residual.get("classification") == "active-residual" and residual.get(
                "blocking", True
            ):
                issues.append(f"{label} is a blocking active residual")
            # Latent differences are allowed at relative closure regardless of
            # whether they bind a legal address, a candidate, or no address.
            continue
        if residual.get("modal") != "potential":
            issues.append(f"{label} is not potential")
            continue
        if residual.get("relation_kind") != "frontier":
            issues.append(f"{label} is only hypothesized, not a verified frontier link")
        if residual.get("gate_status") != "legal":
            issues.append(f"{label} has no legal structural gate")
        reach = residual.get("reach") or {}
        if reach.get("kind") not in {"next", "finite-deep"}:
            issues.append(f"{label} has unknown or unreachable depth")
        if reach.get("kind") == "finite-deep" and not isinstance(
            reach.get("estimated_expansions"), int
        ):
            issues.append(f"{label} finite-deep reach has no bound")
        if not reach.get("evidence_refs"):
            issues.append(f"{label} reach has no evidence")
        address_id = residual.get("address_ref")
        address = addresses.get(address_id)
        if not address or address.get("modal") != "potential" or address.get("lifecycle") != "active":
            issues.append(f"{label} does not reference an active potential address")
        if address_id not in frontier_ids:
            issues.append(f"{label} address is not retained in an expansion frontier")
        if (
            address
            and re.search(r"\d", str(address.get("display_path", "")))
            and address.get("field_opening_status") != "validated"
        ):
            issues.append(f"{label} address is only a child-field hypothesis")
    return issues


def apply_motion(state: dict[str, Any], motion: dict[str, Any]) -> dict[str, Any]:
    current_errors = validate_state(state)
    if current_errors:
        raise ValueError("invalid source state: " + "; ".join(current_errors))
    if motion.get("motion_type") not in MOTIONS:
        raise ValueError("unsupported motion_type")
    if not motion.get("motion_id"):
        raise ValueError("motion_id is required")
    if motion.get("motion_type") in {"MAP", "GLOBAL", "FOCUS", "REALIZE"}:
        blockers = addressability_issues(state)
        if blockers:
            raise ValueError("address generation blocked: " + "; ".join(blockers))

    result = copy.deepcopy(state)
    result.setdefault("intake", []).extend(copy.deepcopy(motion.get("intake_births") or []))
    result.setdefault("objects", []).extend(copy.deepcopy(motion.get("object_births") or []))
    result.setdefault("address_candidates", []).extend(
        copy.deepcopy(motion.get("candidate_births") or [])
    )
    resolutions = motion.get("candidate_resolutions") or []
    if not isinstance(resolutions, list):
        raise ValueError("candidate_resolutions must be a list")
    candidate_map = {
        item.get("candidate_address_id"): item
        for item in result.get("address_candidates") or []
        if isinstance(item, dict)
    }
    for resolution in resolutions:
        candidate = candidate_map.get(resolution.get("candidate_address_id"))
        if candidate is None:
            raise ValueError("candidate resolution references an unknown candidate")
        status = resolution.get("calibration_status")
        if status not in {"calibrated", "rejected"}:
            raise ValueError("candidate resolution must be calibrated or rejected")
        candidate.update(copy.deepcopy(resolution))
    result.setdefault("addresses", []).extend(copy.deepcopy(motion.get("address_births") or []))
    frontier_births = motion.get("frontier_births") or {}
    if isinstance(frontier_births, list):
        frontier_births = {"expansion_latent": frontier_births}
    if not isinstance(frontier_births, dict) or set(frontier_births) - FRONTIER_KEYS:
        raise ValueError("frontier_births must be a typed frontier object")
    result_frontiers = result.setdefault(
        "frontiers",
        {"action": [], "expansion_required": [], "expansion_latent": [], "compressed": []},
    )
    for name in FRONTIER_KEYS:
        result_frontiers.setdefault(name, []).extend(copy.deepcopy(frontier_births.get(name) or []))
    frontier_removals = motion.get("frontier_removals") or {}
    if not isinstance(frontier_removals, dict) or set(frontier_removals) - FRONTIER_KEYS:
        raise ValueError("frontier_removals must be a typed frontier object")
    for name, ids in frontier_removals.items():
        removal_ids = set(ids or [])
        result_frontiers[name] = [
            item for item in result_frontiers.get(name, []) if item.get("address_id") not in removal_ids
        ]
    result.setdefault("residual_links", []).extend(copy.deepcopy(motion.get("residual_births") or []))

    retirements = set(motion.get("retirements") or [])
    for address in result.get("addresses") or []:
        if address.get("address_id") in retirements:
            address["lifecycle"] = "retired"

    field_patch = motion.get("field_patch") or {}
    if field_patch and motion.get("motion_type") not in {"FORM", "REBUILD", "ASCEND"}:
        raise ValueError("field_patch requires FORM, REBUILD, or ASCEND")
    result.setdefault("field", {}).update(copy.deepcopy(field_patch))

    source_revision = int(result.get("revision", 0))
    result["revision"] = source_revision + 1
    result.setdefault("history", []).append(
        {
            "motion_id": motion["motion_id"],
            "motion_type": motion["motion_type"],
            "source_revision": source_revision,
            "result_revision": result["revision"],
            "evidence_ref": motion.get("evidence_ref"),
        }
    )

    result_errors = validate_state(result)
    if result_errors:
        raise ValueError("motion produced invalid state: " + "; ".join(result_errors))
    return result


def load_json(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(data: dict[str, Any], output: str | None) -> None:
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if output:
        Path(output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)


def self_test() -> None:
    child_snapshot = {
        "field": {
            "field_id": "CF-F0-B1.2-v1",
            "local_root": "F0",
            "parent_address": "F0:B1",
            "contract_status": "stable",
        },
        "graph": {
            "status": "validated",
            "nodes": [
                {"address": "F0"},
                {"address": "F0:A"},
            ],
            "relations": [
                {
                    "id": "C-D1",
                    "source": "F0",
                    "target": "F0:A",
                    "relation_type": "dependency",
                    "necessity": "required",
                }
            ],
        },
        "order": {
            "status": "validated",
            "nodes": ["F0", "F0:A"],
            "relations": [
                {"id": "C-D1", "predecessor": "F0", "successor": "F0:A"}
            ],
        },
        "center": {
            "status": "validated",
            "selected": "K1",
            "candidates": [
                {
                    "id": "K1",
                    "members": ["F0", "F0:A"],
                    "minimality_status": "validated",
                }
            ],
        },
        "recursive_structure_status": "validated",
        "frontiers": {
            "action": [],
            "expansion_required": [],
            "expansion_latent": [],
            "compressed": [],
        },
        "residuals": [],
        "residual_audit": {"status": "performed"},
        "return_interface": {"status": "valid", "parent_address": "F0:B1"},
    }
    state = {
        "engine_version": ENGINE_VERSION,
        "revision": 1,
        "field": {
            "field_id": "F-demo",
            "field_version": "v1",
            "f0_lineage": "F0",
            "contract_status": "stable",
            "graph_status": "validated",
            "order_status": "validated",
            "center_status": "validated",
            "formation_revision": 1,
            "formation_confirmation_status": "confirmed",
            "formation_confirmation_evidence_refs": ["E1"],
        },
        "intake": [],
        "objects": [{"object_id": "O1"}],
        "evidence": [{"id": "E1", "source": "self-test"}],
        "dependency_relations": [
            {
                "id": "D1",
                "source": "F0",
                "target": "F0:B",
                "necessity": "required",
                "validity": "valid",
                "evidence_refs": ["E1"],
            },
            {
                "id": "D2",
                "source": "F0:B",
                "target": "F0:B1",
                "necessity": "required",
                "validity": "valid",
                "evidence_refs": ["E1"],
            },
            {
                "id": "D3",
                "source": "F0:B1",
                "target": "F0:B1.2",
                "necessity": "required",
                "validity": "valid",
                "evidence_refs": ["E1"],
            },
        ],
        "addresses": [],
        "address_candidates": [],
        "frontiers": {
            "action": [],
            "expansion_required": [],
            "expansion_latent": [],
            "compressed": [],
        },
        "residual_links": [],
        "history": [],
    }
    motion = {
        "motion_id": "M1",
        "motion_type": "MAP",
        "address_births": [
            {
                "address_id": "A1",
                "object_id": "O1",
                "display_path": "B1.2",
                "calibration_status": "calibrated",
                "modal": "potential",
                "lifecycle": "active",
                "root_path_nodes": ["F0", "F0:B", "F0:B1", "F0:B1.2"],
                "root_path_relation_ids": ["D1", "D2", "D3"],
                "parent_binding": {
                    "parent_field_id": "F-demo",
                    "parent_address": "F0:B1",
                    "required_function": "return a validated child interface",
                    "parent_return": "F0:B1.2 -> F0:B successor",
                },
                "relation_roles": ["dependency"],
                "predecessor_state": {"status": "satisfied", "refs": ["D1", "D2", "D3"]},
                "evidence_refs": ["E1"],
                "field_opening_status": "validated",
                "field_opening_audit": {
                    "field_id": "CF-F0-B1.2-v1",
                    "local_root": "F0",
                    "parent_address": "F0:B1",
                    "contract_status": "stable",
                    "graph_status": "validated",
                    "order_status": "validated",
                    "center_status": "validated",
                    "recursive_structure_status": "validated",
                    "residual_audit_status": "performed",
                    "return_interface_status": "valid",
                    "state_ref": "memory://CF-F0-B1.2-v1",
                    "state_snapshot": child_snapshot,
                    "state_hash": snapshot_hash(child_snapshot),
                    "evidence_refs": ["E1"],
                },
            }
        ],
        "frontier_births": {
            "expansion_latent": [{"address_id": "A1", "evidence_refs": ["E1"]}]
        },
    }
    updated = apply_motion(state, motion)
    assert updated["revision"] == 2
    tampered = copy.deepcopy(updated)
    tampered["addresses"][0]["field_opening_audit"]["state_snapshot"]["field"][
        "field_id"
    ] = "tampered"
    assert any("state_hash" in error for error in validate_state(tampered))
    forming = copy.deepcopy(updated)
    forming_address = forming["addresses"][0]
    forming_address["field_opening_status"] = "forming"
    forming_audit = forming_address["field_opening_audit"]
    forming_audit.update(
        {
            "contract_status": "provisional",
            "graph_status": "tentative",
            "order_status": "tentative",
            "center_status": "selected",
            "recursive_structure_status": "forming",
            "return_interface_status": "tentative",
        }
    )
    forming_snapshot = forming_audit["state_snapshot"]
    forming_snapshot["field"]["contract_status"] = "provisional"
    forming_snapshot["graph"]["status"] = "tentative"
    forming_snapshot["order"]["status"] = "tentative"
    forming_snapshot["center"]["status"] = "selected"
    forming_snapshot["recursive_structure_status"] = "forming"
    forming_snapshot["return_interface"]["status"] = "tentative"
    forming_audit["state_hash"] = snapshot_hash(forming_snapshot)
    assert validate_state(forming) == []
    broken = copy.deepcopy(updated)
    broken["addresses"][0]["root_path_relation_ids"] = ["D3", "D2", "D1"]
    assert any("reversed" in error for error in validate_state(broken))
    assert provisional_closure_issues(updated) == []
    required_open = copy.deepcopy(updated)
    required_open["frontiers"]["expansion_required"] = required_open["frontiers"][
        "expansion_latent"
    ]
    required_open["frontiers"]["expansion_latent"] = []
    assert any("required expansion frontier" in issue for issue in provisional_closure_issues(required_open))
    hypothesis = copy.deepcopy(updated)
    hypothesis["address_candidates"] = [
        {
            "candidate_address_id": "CAND-1",
            "calibration_status": "hypothesized",
            "proposed_structural_role": "possible future branch",
        }
    ]
    hypothesis["residual_links"] = [
        {
            "classification": "latent-residual",
            "description": "possible future mismatch",
            "activation_condition": "new evidence arrives",
            "address_binding": {"kind": "candidate", "candidate_address_id": "CAND-1"},
        }
    ]
    assert validate_state(hypothesis) == []
    assert provisional_closure_issues(hypothesis) == []
    print("Address Engine self-test passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("state")
    closure_parser = subparsers.add_parser("closure-audit")
    closure_parser.add_argument("state")
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("state")
    apply_parser.add_argument("motion")
    apply_parser.add_argument("--output")
    subparsers.add_parser("self-test")
    args = parser.parse_args()

    if args.command == "self-test":
        self_test()
        return 0
    if args.command == "validate":
        errors = validate_state(load_json(args.state))
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("Address Engine state is valid")
        return 0
    if args.command == "closure-audit":
        state = load_json(args.state)
        errors = validate_state(state)
        issues = provisional_closure_issues(state) if not errors else errors
        if issues:
            for issue in issues:
                print(issue, file=sys.stderr)
            return 1
        print("Address Engine provisional closure is ready")
        return 0
    if args.command == "apply":
        try:
            result = apply_motion(load_json(args.state), load_json(args.motion))
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 1
        write_json(result, args.output)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
