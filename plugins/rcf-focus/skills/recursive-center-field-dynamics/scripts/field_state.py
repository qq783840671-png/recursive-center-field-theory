#!/usr/bin/env python3
"""Initialize and maintain recursive center-field dynamic state."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVENT_TYPES = {
    "UPDATE_INGEST",
    "UPDATE_STRUCTURE",
    "UPDATE_RECONCILE",
    "F0_CONFIRM",
    "FIELD_FORM",
    "CENTER_ADJUST",
    "HUMAN_CALIBRATE",
    "SURVEY",
    "GLOBAL_EXPAND",
    "FOCUS",
    "EXPAND",
    "COMPRESS",
    "PROMOTE",
    "SPLIT",
    "REBUILD",
    "ADDRESS_MATERIALIZE",
    "PLAN_EXECUTION",
    "EXECUTE",
    "INVALIDATE",
    "AUDIT",
    "HANDOFF",
    "STOP",
    "REMODEL_REQUIRED",
}

SCHEMA_LEGACY = "1.0"
SCHEMA_ORDERED = "1.1"
SCHEMA_FOCUS = "1.2"
SCHEMA_AUDITED = "1.3"
SCHEMA_JOINT_20 = "2.0"
SCHEMA_JOINT_21 = "2.1"
SCHEMA_JOINT = "2.2"
SCHEMA_CURRENT = SCHEMA_JOINT
FIELD_FORM_SCHEMAS = {SCHEMA_JOINT_21, SCHEMA_JOINT}
JOINT_SCHEMAS = {SCHEMA_JOINT_20, *FIELD_FORM_SCHEMAS}
FOCUS_SCHEMAS = {SCHEMA_FOCUS, SCHEMA_AUDITED, *JOINT_SCHEMAS}
ORDERED_SCHEMAS = {SCHEMA_ORDERED, *FOCUS_SCHEMAS}
SUPPORTED_SCHEMAS = {SCHEMA_LEGACY, *ORDERED_SCHEMAS}
MODAL_SCHEMAS = {SCHEMA_AUDITED, *JOINT_SCHEMAS}
LEGACY_SCHEMAS = {
    SCHEMA_LEGACY,
    SCHEMA_ORDERED,
    SCHEMA_FOCUS,
    SCHEMA_AUDITED,
    SCHEMA_JOINT_20,
    SCHEMA_JOINT_21,
}

ORDER_STATUSES = {"unvalidated", "tentative", "validated", "invalid"}
EVIDENCE_STATUSES = {"explicit", "inferred", "tentative", "unknown"}
STRUCTURAL_NECESSITIES = {"center", "required-predecessor", "optional", "unknown"}
DEPENDENCY_READINESS = {"ready", "blocked", "unknown"}
GATE_STATUSES = {"legal", "illegal", "unverified"}
FIELD_OPENING_STATUSES = {"hypothesized", "forming", "validated"}
FOCUS_DISPLAY_PATTERN = re.compile(r"^[A-Z]\d+(?:\.\d+)*$")
MODAL_STATUSES = {"[+]", "[◇]", "[-]", "[∅]"}
RESIDUAL_MODAL_STATUSES = {"[+]", "[◇]", "[-]", "[∅]"}
RESIDUAL_TYPES = {
    "structural",
    "non-poset",
    "execution-failure",
    "unexpected-result",
    "unmet-premise",
    "invalidation",
}
RESIDUAL_DESTINATIONS = {
    "downward-expansion",
    "field-ascension",
    "in-field-remodel",
    "remain-external",
    "prohibit",
}
RESIDUAL_AUDIT_EVENT_TYPES = {
    "UPDATE_RECONCILE",
    "FIELD_FORM",
    "CENTER_ADJUST",
    "HUMAN_CALIBRATE",
    "SURVEY",
    "GLOBAL_EXPAND",
    "FOCUS",
    "EXPAND",
    "COMPRESS",
    "PROMOTE",
    "SPLIT",
    "REBUILD",
    "ADDRESS_MATERIALIZE",
    "EXECUTE",
}
JOINT_MOTION_TYPES = {*RESIDUAL_AUDIT_EVENT_TYPES, "F0_CONFIRM", "INVALIDATE"}
F0_GATED_EVENT_TYPES = {
    "GLOBAL_EXPAND",
    "FOCUS",
    "EXPAND",
    "COMPRESS",
    "PROMOTE",
    "SPLIT",
    "REBUILD",
    "ADDRESS_MATERIALIZE",
    "PLAN_EXECUTION",
    "EXECUTE",
}
F0_PROVISIONAL_CLOSURE_GATED_EVENT_TYPES = {
    "GLOBAL_EXPAND",
    "FOCUS",
    "ADDRESS_MATERIALIZE",
    "PLAN_EXECUTION",
    "EXECUTE",
}
NEXT_DECISIONS = {
    "F0_CONFIRMATION_REQUIRED",
    "FIELD_FORMATION_REQUIRED",
    "HUMAN_CALIBRATION_REQUIRED",
    "CONTINUE_EXECUTION",
    "FOCUS_REQUIRED",
    "EXPAND_REQUIRED",
    "REMODEL_REQUIRED",
    "FIELD_ASCENSION_REQUIRED",
    "F0_COMPLETE",
    "BLOCKED",
}
RESIDUAL_AUDIT_CHECKS = {
    "unexplained_omissions_checked",
    "flattening_checked",
    "external_misclassification_checked",
    "frontier_residual_confusion_checked",
}

REQUIRED_KEYS = {
    "schema_version",
    "version",
    "field",
    "center",
    "focus",
    "panorama",
    "execution",
    "evidence",
    "history",
}
JOINT_REQUIRED_KEYS = {*REQUIRED_KEYS, "drift"}

GENERAL_RELATION_TYPES = {
    "dependency",
    "support",
    "conflict",
    "similarity",
    "coupling",
    "prohibition",
    "condition-transition",
}
VALIDITY_STATUSES = {"valid", "stale", "invalid"}
CENTER_STATUSES = {"tentative", "selected", "remodel-required", "invalid"}
CENTER_VALIDITIES = {"valid", "stale", "invalid"}
CENTER_TEST_NAMES = {
    "deletion",
    "replacement",
    "reordering",
    "compression",
    "closure",
    "cycle",
    "hollow_abstraction",
}
CENTER_TEST_STATUSES = {"unvalidated", "pass", "fail", "not-applicable"}
FRONTIER_TYPES = {"action", "expansion", "compressed"}
COMPRESSED_EXPOSURES = {"compressed", "locked", "reopen-required"}
GLOBAL_DEFER_REASONS = {
    "budget",
    "depth-bound",
    "cost-bound",
    "locked",
    "precondition",
}
DRIFT_STATUSES = {"pass", "warn", "fail"}
FIELD_PHASES = {
    "forming",
    "stabilizing",
    "execution-stable",
    "executing",
    "review",
    "complete",
    "blocked",
}
CONTRACT_STATUSES = {
    "provisional",
    "stable-for-execution",
    "human-calibration-required",
    "invalid",
}
CALIBRATION_STATUSES = {"not-required", "required", "resolved"}
F0_CONFIRMATION_STATUSES = {"required", "confirmed", "bypassed"}
ROOT_CONTRACT_FIELDS = {
    "root_goal",
    "boundary",
    "success_criteria",
    "immutable_constraints",
    "allowed_changes",
    "tolerance",
}
ADDRESS_RELATION_KINDS = {
    "realized",
    "frontier",
    "hypothesized",
    "negative",
    "no-address",
}
ADDRESS_RELATION_GATES = {"legal", "unverified", "conflicting", "out-of-field"}
ADDRESS_REACH_KINDS = {"realized", "next", "finite-deep", "unknown", "unreachable"}
ABSORPTION_STATUSES = {
    "unresolved",
    "partially-absorbed",
    "tolerated",
    "human-pending",
    "absorbed",
    "prohibited",
}
EXECUTION_NODE_STATUSES = {
    "satisfied",
    "locked",
    "compressed-valid",
    "pending",
    "active",
    "completed",
    "blocked",
}

UPDATE_SOURCE_KINDS = {"user", "evidence", "agent-tentative", "residual"}
UPDATE_STATUSES = {"pending", "structured", "resolved"}
UPDATE_CLASSIFICATIONS = {
    "external",
    "local-replace",
    "legal-expansion",
    "principle-conflict",
    "no-address-residual",
    "subfield-rebuild",
    "root-rebuild",
    "version-branch",
}
UPDATE_MOTION_OPERATORS = {
    "UPDATE_RECONCILE",
    "EXPAND",
    "REBUILD",
    "SPLIT",
    "ADDRESS_MATERIALIZE",
}
UPDATE_ASSIGNMENT_KINDS = {
    "external",
    "existing",
    "potential",
    "new-child",
    "negative",
    "no-address",
    "subtree",
}
ADDRESS_MOTION_STATUSES = {"proposed", "applied", "dismissed"}
ADDRESS_LINEAGE_KINDS = {
    "retain",
    "payload-replace",
    "expand",
    "move",
    "split",
    "merge",
    "retire",
    "birth",
    "externalize",
    "prohibit",
}
WORKING_CLOSURE_STATUSES = {"relative-closed", "open", "unstable", "unknown"}
FIELD_CLOSURE_STATUSES = {"relative-closed"}
BRANCH_STATUSES = {"active", "inactive", "merged"}
STRICT_THEORY_ADDRESS_PATTERN = re.compile(
    r"^F0(?::[A-Z](?:\d+(?:\.\d+)*)?)?$"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"state file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("state root must be a JSON object")
    return data


def write_state(path: Path, state: dict[str, Any]) -> None:
    """Atomically replace a state file so failed writes leave the old state intact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass


def schema_version(state: dict[str, Any]) -> str:
    return str(state.get("schema_version", ""))


def has_field_formation_schema(state: dict[str, Any]) -> bool:
    return schema_version(state) in FIELD_FORM_SCHEMAS


def is_current_schema(state: dict[str, Any]) -> bool:
    return schema_version(state) == SCHEMA_JOINT


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def legal_roots(state: dict[str, Any]) -> list[str]:
    field = state.get("field", {})
    roots = field.get("legal_roots", []) if isinstance(field, dict) else []
    return [root for root in roots if nonempty_string(root)]


def address_has_legal_root(address: Any, roots: list[str]) -> bool:
    if not nonempty_string(address):
        return False
    return any(
        address == root
        or any(address.startswith(root + separator) for separator in (":", "/", " ", "@"))
        for root in roots
    )


def is_strict_theory_address(address: Any) -> bool:
    return nonempty_string(address) and bool(
        STRICT_THEORY_ADDRESS_PATTERN.fullmatch(address)
    )


def focus_display_address(state: dict[str, Any], address: Any) -> str | None:
    """Return the F0-facing root-letter + numeric-suffix display address."""
    field = state.get("field", {})
    field_id = field.get("id") if isinstance(field, dict) else None
    if not nonempty_string(field_id) or not nonempty_string(address):
        return None
    prefix = f"{field_id}:"
    if not address.startswith(prefix):
        return None
    display = address[len(prefix) :]
    return display if FOCUS_DISPLAY_PATTERN.fullmatch(display) else None


def focus_depth_from_display(display: str | None) -> int | None:
    if display is None:
        return None
    return len(display[1:].split("."))


def child_snapshot_hash(snapshot: dict[str, Any]) -> str | None:
    """Return a canonical digest for an inline, restorable child-field snapshot."""
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


def child_state_snapshot_issues(
    audit: dict[str, Any], node: dict[str, Any], opening_status: str
) -> list[str]:
    """Validate the embedded state instead of trusting a certificate shell."""
    snapshot = audit.get("state_snapshot")
    if not isinstance(snapshot, dict):
        return ["child state_snapshot must be an inline restorable object"]
    issues: list[str] = []
    expected_hash = child_snapshot_hash(snapshot)
    if expected_hash is None:
        issues.append("child state_snapshot is not canonically serializable")
    elif audit.get("state_hash") != expected_hash:
        issues.append("child state_hash does not match the embedded state_snapshot")

    sections: dict[str, dict[str, Any]] = {}
    for name in ("field", "graph", "order", "center", "residual_audit", "return_interface"):
        value = snapshot.get(name)
        if not isinstance(value, dict):
            issues.append(f"child state_snapshot.{name} must be an object")
            value = {}
        sections[name] = value
    frontiers = snapshot.get("frontiers")
    if not isinstance(frontiers, dict):
        issues.append("child state_snapshot.frontiers must be an object")
        frontiers = {}
    for name in ("action", "expansion", "compressed"):
        if not isinstance(frontiers.get(name), list):
            issues.append(f"child state_snapshot.frontiers.{name} must be a list")
    residuals = snapshot.get("residuals")
    if not isinstance(residuals, list) or not all(isinstance(item, dict) for item in residuals):
        issues.append("child state_snapshot.residuals must be a list of objects")
        residuals = []

    field = sections["field"]
    graph = sections["graph"]
    order = sections["order"]
    center = sections["center"]
    residual_audit = sections["residual_audit"]
    return_interface = sections["return_interface"]
    bindings = {
        "field_id": (field.get("field_id"), audit.get("field_id")),
        "local_root": (field.get("local_root"), "F0"),
        "parent_address": (field.get("parent_address"), node.get("parent_address")),
        "contract_status": (field.get("contract_status"), audit.get("contract_status")),
        "graph_status": (graph.get("status"), audit.get("graph_status")),
        "order_status": (order.get("status"), audit.get("order_status")),
        "center_status": (center.get("status"), audit.get("center_status")),
        "recursive_structure_status": (
            snapshot.get("recursive_structure_status"),
            audit.get("recursive_structure_status"),
        ),
        "residual_audit_status": (
            residual_audit.get("status"),
            audit.get("residual_audit_status"),
        ),
        "return_interface_status": (
            return_interface.get("status"),
            audit.get("return_interface_status"),
        ),
    }
    for name, (actual, expected) in bindings.items():
        if actual != expected:
            issues.append(f"child state_snapshot {name} does not match its audit")
    if return_interface.get("parent_address") != node.get("parent_address"):
        issues.append("child return interface does not bind back to parent_address")

    allowed = {
        "hypothesized": {
            "contract_status": {"candidate", "provisional"},
            "graph_status": {"forming", "tentative", "unvalidated"},
            "order_status": {"forming", "tentative", "unvalidated"},
            "center_status": {"candidate", "selected", "tentative", "unvalidated"},
            "recursive_structure_status": {"hypothesized"},
            "residual_audit_status": {"performed"},
            "return_interface_status": {"tentative", "unvalidated"},
        },
        "forming": {
            "contract_status": {"provisional", "stable-for-execution"},
            "graph_status": {"forming", "tentative", "validated"},
            "order_status": {"forming", "tentative", "validated"},
            "center_status": {"candidate", "selected", "tentative", "validated"},
            "recursive_structure_status": {"forming"},
            "residual_audit_status": {"performed"},
            "return_interface_status": {"tentative", "valid"},
        },
        "validated": {
            "contract_status": {"stable-for-execution"},
            "graph_status": {"validated"},
            "order_status": {"validated"},
            "center_status": {"validated"},
            "recursive_structure_status": {"validated"},
            "residual_audit_status": {"performed"},
            "return_interface_status": {"valid"},
        },
    }
    for name, accepted in allowed.get(opening_status, {}).items():
        if audit.get(name) not in accepted:
            issues.append(
                f"child {name} is incompatible with field_opening_status={opening_status}"
            )

    graph_nodes = graph.get("nodes")
    graph_addresses: list[str] = []
    if not isinstance(graph_nodes, list):
        issues.append("child state_snapshot.graph.nodes must be a list")
    else:
        for item in graph_nodes:
            address = item.get("address") if isinstance(item, dict) else None
            if not nonempty_string(address):
                issues.append("child graph node needs a non-empty address")
            else:
                graph_addresses.append(address)
        if len(graph_addresses) != len(set(graph_addresses)):
            issues.append("child graph contains duplicate addresses")
        if graph_addresses.count("F0") != 1:
            issues.append("child graph must contain exactly one local F0 root")
    graph_address_set = set(graph_addresses)
    graph_relations = graph.get("relations")
    graph_relation_map: dict[str, dict[str, Any]] = {}
    if not isinstance(graph_relations, list):
        issues.append("child state_snapshot.graph.relations must be a list")
    else:
        for relation in graph_relations:
            if not isinstance(relation, dict) or not nonempty_string(relation.get("id")):
                issues.append("child graph relation needs a non-empty id")
                continue
            relation_id = relation["id"]
            if relation_id in graph_relation_map:
                issues.append(f"child graph contains duplicate relation {relation_id}")
            graph_relation_map[relation_id] = relation
            if relation.get("source") not in graph_address_set or relation.get("target") not in graph_address_set:
                issues.append(f"child graph relation {relation_id} has an unknown endpoint")

    order_nodes = order.get("nodes")
    order_addresses: list[str] = []
    if not isinstance(order_nodes, list):
        issues.append("child state_snapshot.order.nodes must be a list")
    else:
        for item in order_nodes:
            address = item.get("address") if isinstance(item, dict) else item
            if not nonempty_string(address):
                issues.append("child order node needs a non-empty address")
            else:
                order_addresses.append(address)
        if len(order_addresses) != len(set(order_addresses)):
            issues.append("child order contains duplicate addresses")
        if set(order_addresses) - graph_address_set:
            issues.append("child order contains nodes absent from the complete graph")
    order_address_set = set(order_addresses)
    order_relations = order.get("relations")
    adjacency: dict[str, set[str]] = {}
    if not isinstance(order_relations, list):
        issues.append("child state_snapshot.order.relations must be a list")
    else:
        for relation in order_relations:
            if not isinstance(relation, dict) or not nonempty_string(relation.get("id")):
                issues.append("child order relation needs a non-empty id")
                continue
            relation_id = relation["id"]
            predecessor = relation.get("predecessor")
            successor = relation.get("successor")
            if predecessor not in order_address_set or successor not in order_address_set:
                issues.append(f"child order relation {relation_id} has an unknown endpoint")
                continue
            graph_relation = graph_relation_map.get(relation_id)
            if not isinstance(graph_relation, dict):
                issues.append(f"child order relation {relation_id} is absent from the complete graph")
            elif (
                graph_relation.get("source") != predecessor
                or graph_relation.get("target") != successor
                or graph_relation.get("relation_type") != "dependency"
                or graph_relation.get("necessity") != "required"
            ):
                issues.append(f"child order relation {relation_id} is not a matching required dependency")
            adjacency.setdefault(predecessor, set()).add(successor)
    visiting: set[str] = set()
    visited: set[str] = set()

    def has_cycle(address: str) -> bool:
        if address in visiting:
            return True
        if address in visited:
            return False
        visiting.add(address)
        if any(has_cycle(successor) for successor in adjacency.get(address, set())):
            return True
        visiting.remove(address)
        visited.add(address)
        return False

    if any(has_cycle(address) for address in order_address_set):
        issues.append("child necessary order contains a cycle")

    candidates = center.get("candidates")
    if not isinstance(candidates, list) or not all(isinstance(item, dict) for item in candidates):
        issues.append("child state_snapshot.center.candidates must be a list of objects")
        candidates = []
    selected_id = center.get("selected")
    selected = next(
        (item for item in candidates if item.get("id") == selected_id), None
    )
    if opening_status == "validated":
        if not isinstance(selected, dict):
            issues.append("validated child snapshot needs a selected center candidate")
        else:
            if selected.get("minimality_status") != "validated":
                issues.append("validated child center has not passed minimality tests")
            members = selected.get("members")
            if not isinstance(members, list) or set(members) - order_address_set:
                issues.append("validated child center members must lie in its necessary order")
        for residual in residuals:
            if residual.get("absorption_status") == "absorbed":
                continue
            relation = residual.get("address_relation", {})
            reach = relation.get("reach", {}) if isinstance(relation, dict) else {}
            if (
                residual.get("modal_status") != "[◇]"
                or relation.get("kind") != "frontier"
                or relation.get("gate_status") != "legal"
                or reach.get("kind") not in {"next", "finite-deep"}
            ):
                issues.append("validated child snapshot contains a non-closing active residual")
                break
    return issues


def child_field_opening_issues(
    state: dict[str, Any], node: dict[str, Any]
) -> list[str]:
    """Validate the compact certificate behind a generated recursive address."""
    address = node.get("address")
    if focus_display_address(state, address) is None:
        return []
    opening_status = node.get("field_opening_status")
    if opening_status not in FIELD_OPENING_STATUSES:
        return ["generated recursive address needs a valid field_opening_status"]
    audit = node.get("field_opening_audit")
    if not isinstance(audit, dict):
        return ["generated recursive address lacks field_opening_audit"]
    issues: list[str] = []
    if opening_status != "validated" and node.get("modal_status") != "[◇]":
        issues.append("an unvalidated child-field hypothesis must remain [◇]")
    if not nonempty_string(audit.get("field_id")):
        issues.append("child field_id is missing")
    if audit.get("local_root") != "F0":
        issues.append("child local_root must be F0")
    if audit.get("parent_address") != node.get("parent_address"):
        issues.append("child parent binding does not match parent_address")
    if not nonempty_string(audit.get("state_ref")):
        issues.append("child state_ref is missing")
    refs = audit.get("evidence_ids")
    if not isinstance(refs, list) or not all(
        nonempty_string(item) for item in refs
    ):
        issues.append("child field opening evidence_ids must be a string list")
    else:
        evidence_ids = {
            item.get("id")
            for item in state.get("evidence", [])
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        if set(refs) - evidence_ids:
            issues.append("child field opening references unknown evidence")
        if opening_status == "validated" and not refs:
            issues.append("validated child field opening needs evidence_ids")
    issues.extend(child_state_snapshot_issues(audit, node, opening_status))
    return issues


def selected_center_record(state: dict[str, Any]) -> dict[str, Any] | None:
    """Return the selected joint-schema center or the legacy single center."""
    center = state.get("center", {})
    if not isinstance(center, dict):
        return None
    if schema_version(state) not in JOINT_SCHEMAS:
        return center
    selected_id = center.get("selected")
    candidates = center.get("candidates", [])
    if not nonempty_string(selected_id) or not isinstance(candidates, list):
        return None
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("id") == selected_id:
            return candidate
    return None


def selected_center_signature(state: dict[str, Any]) -> tuple[Any, tuple[str, ...], tuple[str, ...]] | None:
    """Return only the constitutive selected-center identity and sub-poset."""
    center = selected_center_record(state)
    if not isinstance(center, dict):
        return None
    return (
        center.get("id"),
        tuple(sorted(item for item in center.get("members", []) if nonempty_string(item))),
        tuple(
            sorted(item for item in center.get("relation_ids", []) if nonempty_string(item))
        ),
    )


def order_indexes(
    state: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    panorama = state.get("panorama", {})
    order = panorama.get("order", {}) if isinstance(panorama, dict) else {}
    nodes = order.get("nodes", []) if isinstance(order, dict) else []
    relations = order.get("relations", []) if isinstance(order, dict) else []
    node_map = {
        item["address"]: item
        for item in nodes
        if isinstance(item, dict) and nonempty_string(item.get("address"))
    }
    relation_map = {
        item["id"]: item
        for item in relations
        if isinstance(item, dict) and nonempty_string(item.get("id"))
    }
    return node_map, relation_map


def reachable(start: str, adjacency: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    stack = [start]
    while stack:
        current = stack.pop()
        for successor in adjacency.get(current, set()):
            if successor not in seen:
                seen.add(successor)
                stack.append(successor)
    return seen


def required_closure(
    target: str,
    relation_map: dict[str, dict[str, Any]],
    selected_relation_ids: set[str] | None = None,
) -> tuple[set[str], set[str]]:
    selected_relation_ids = selected_relation_ids or set()
    incoming: dict[str, list[tuple[str, str]]] = {}
    for relation_id, relation in relation_map.items():
        if (
            relation.get("necessity") != "required"
            and relation_id not in selected_relation_ids
        ):
            continue
        predecessor = relation.get("predecessor")
        successor = relation.get("successor")
        if not nonempty_string(predecessor) or not nonempty_string(successor):
            continue
        incoming.setdefault(successor, []).append((predecessor, relation_id))

    predecessors: set[str] = set()
    relation_ids: set[str] = set()
    stack = [target]
    while stack:
        current = stack.pop()
        for predecessor, relation_id in incoming.get(current, []):
            relation_ids.add(relation_id)
            if predecessor not in predecessors:
                predecessors.add(predecessor)
                stack.append(predecessor)
    predecessors.discard(target)
    return predecessors, relation_ids


def compressed_indexes(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    panorama = state.get("panorama", {})
    if schema_version(state) in JOINT_SCHEMAS and isinstance(panorama, dict):
        frontiers = panorama.get("frontiers", {})
        compressed = (
            frontiers.get("compressed", []) if isinstance(frontiers, dict) else []
        )
    else:
        compressed = panorama.get("compressed", []) if isinstance(panorama, dict) else []
    return {
        item["address"]: item
        for item in compressed
        if isinstance(item, dict) and nonempty_string(item.get("address"))
    }


def audit_path(
    state: dict[str, Any],
    item: dict[str, Any],
    *,
    legacy_plain: bool = False,
    require_action_ready: bool = False,
) -> dict[str, Any]:
    """Return a copy with helper-computed ancestry and gate fields."""
    result = dict(item)
    legacy_plain = legacy_plain or result.get("ancestry_source") == "legacy-plain"
    address = result.get("address")
    result.setdefault("structural_necessity", "unknown")
    result.setdefault("focus_depth", 0)

    if legacy_plain:
        result["ancestry_source"] = "legacy-plain"
        result["root_ancestry"] = {
            "root_address": legal_roots(state)[0] if legal_roots(state) else None,
            "node_addresses": [],
            "relation_ids": [],
            "compressed_ancestor_addresses": [],
        }
        result["required_predecessors"] = []
        result["dependency_readiness"] = "unknown"
        result["gate_status"] = "unverified"
        result["gate_reasons"] = [
            "plain active path has no auditable root ancestry"
        ]
        return result

    hard_reasons: list[str] = []
    uncertain_reasons: list[str] = []
    roots = legal_roots(state)
    node_map, relation_map = order_indexes(state)
    compressed_map = compressed_indexes(state)
    panorama = state.get("panorama", {})
    order = panorama.get("order", {}) if isinstance(panorama, dict) else {}

    if schema_version(state) in FOCUS_SCHEMAS:
        expected_display = focus_display_address(state, address)
        expected_depth = focus_depth_from_display(expected_display)
        if expected_display is None:
            hard_reasons.append(
                "schema 1.2+ active address must use canonical F0:<letter><numeric suffix> form"
            )
        else:
            if result.get("display_address") not in {None, expected_display}:
                hard_reasons.append(
                    "display_address does not match the canonical F0 address"
                )
            result["display_address"] = expected_display
            result["focus_depth"] = expected_depth
            center = selected_center_record(state)
            members = center.get("members", []) if isinstance(center, dict) else []
            field = state.get("field", {})
            field_id = field.get("id") if isinstance(field, dict) else None
            center_root = f"{field_id}:{expected_display[0]}"
            if center_root not in members:
                hard_reasons.append(
                    "active address root letter is absent from the current center"
                )

    if not address_has_legal_root(address, roots):
        hard_reasons.append("active address has no legal field root")
    if address not in node_map:
        hard_reasons.append("active address is absent from the dependency order")

    ancestry = result.get("root_ancestry")
    if not isinstance(ancestry, dict):
        ancestry = {}
        hard_reasons.append("root_ancestry must be an object")

    root_address = ancestry.get("root_address")
    node_addresses = ancestry.get("node_addresses", [])
    relation_ids = ancestry.get("relation_ids", [])
    compressed_addresses = ancestry.get("compressed_ancestor_addresses", [])

    if root_address not in roots:
        hard_reasons.append("root_ancestry.root_address is not a legal field root")
    if not isinstance(node_addresses, list) or not all(
        nonempty_string(value) for value in node_addresses
    ):
        hard_reasons.append("root_ancestry.node_addresses must be a string list")
        node_addresses = []
    if not isinstance(relation_ids, list) or not all(
        nonempty_string(value) for value in relation_ids
    ):
        hard_reasons.append("root_ancestry.relation_ids must be a string list")
        relation_ids = []
    if not isinstance(compressed_addresses, list) or not all(
        nonempty_string(value) for value in compressed_addresses
    ):
        hard_reasons.append(
            "root_ancestry.compressed_ancestor_addresses must be a string list"
        )
        compressed_addresses = []

    unknown_nodes = sorted(set(node_addresses) - set(node_map))
    if unknown_nodes:
        hard_reasons.append(
            "root ancestry has unknown nodes: " + ", ".join(unknown_nodes)
        )
    unknown_relations = sorted(set(relation_ids) - set(relation_map))
    if unknown_relations:
        hard_reasons.append(
            "root ancestry has unknown relations: " + ", ".join(unknown_relations)
        )
    unknown_compressed = sorted(set(compressed_addresses) - set(compressed_map))
    if unknown_compressed:
        hard_reasons.append(
            "root ancestry has unknown compressed interfaces: "
            + ", ".join(unknown_compressed)
        )

    covered = set(node_addresses) | set(compressed_addresses)
    if root_address not in covered:
        hard_reasons.append("root ancestry does not retain its root")
    if address not in covered:
        hard_reasons.append("root ancestry does not retain its active address")

    required_predecessors, required_relation_ids = required_closure(
        str(address), relation_map, set(relation_ids)
    )
    missing_predecessors = sorted(required_predecessors - covered)
    if missing_predecessors:
        hard_reasons.append(
            "missing required predecessors: " + ", ".join(missing_predecessors)
        )
    missing_required_relations = sorted(required_relation_ids - set(relation_ids))
    if missing_required_relations:
        hard_reasons.append(
            "missing required ancestry relations: "
            + ", ".join(missing_required_relations)
        )

    selected_adjacency: dict[str, set[str]] = {}
    for relation_id in relation_ids:
        relation = relation_map.get(relation_id)
        if relation is None:
            continue
        predecessor = relation.get("predecessor")
        successor = relation.get("successor")
        if not nonempty_string(predecessor) or not nonempty_string(successor):
            hard_reasons.append(
                f"ancestry relation {relation_id} has incomplete endpoints"
            )
            continue
        if predecessor not in covered or successor not in covered:
            hard_reasons.append(
                f"ancestry relation {relation_id} leaves the retained sub-DAG"
            )
        selected_adjacency.setdefault(predecessor, set()).add(successor)
    if (
        nonempty_string(root_address)
        and nonempty_string(address)
        and address != root_address
        and address not in reachable(root_address, selected_adjacency)
    ):
        hard_reasons.append("active address is not reachable from its root ancestry")

    order_status = order.get("status") if isinstance(order, dict) else None
    if order_status == "invalid":
        hard_reasons.append("dependency order is marked invalid")
    elif order_status != "validated":
        uncertain_reasons.append("dependency order is not validated")
    center = selected_center_record(state)
    if isinstance(center, dict):
        if center.get("minimality_status") == "invalid":
            hard_reasons.append("center sub-poset is marked invalid")
        elif center.get("minimality_status") != "validated":
            uncertain_reasons.append("center sub-poset is not validated")
        if schema_version(state) in JOINT_SCHEMAS and center.get("validity") != "valid":
            hard_reasons.append("selected center candidate is not valid")
    elif schema_version(state) in JOINT_SCHEMAS:
        hard_reasons.append("joint schema has no selected center candidate")

    for compressed_address in required_predecessors & set(compressed_addresses):
        interface = compressed_map.get(compressed_address, {})
        if interface.get("structural_status") != "required-ancestor":
            hard_reasons.append(
                f"compressed required predecessor {compressed_address} lost structural priority"
            )
        if interface.get("exposure_status") == "reopen-required":
            hard_reasons.append(
                f"compressed required predecessor {compressed_address} must be reopened"
            )

    if require_action_ready:
        active_node = node_map.get(str(address), {})
        if (
            focus_display_address(state, str(address)) is not None
            and active_node.get("field_opening_status") != "validated"
        ):
            hard_reasons.append(
                "active recursive address has no validated child-field opening"
            )
        for predecessor in sorted(required_predecessors):
            if predecessor in compressed_addresses:
                interface = compressed_map.get(predecessor, {})
                if (
                    interface.get("structural_status") != "required-ancestor"
                    or interface.get("exposure_status") == "reopen-required"
                    or not isinstance(interface.get("contract"), dict)
                ):
                    hard_reasons.append(
                        f"required predecessor {predecessor} has no valid compressed interface"
                    )
                continue
            predecessor_node = node_map.get(predecessor, {})
            if (
                predecessor_node.get("validity") != "valid"
                or predecessor_node.get("modal_status") != "[+]"
            ):
                hard_reasons.append(
                    f"required predecessor {predecessor} is not realized"
                )

    if hard_reasons:
        gate_status = "illegal"
        dependency_readiness = "blocked"
    elif uncertain_reasons:
        gate_status = "unverified"
        dependency_readiness = "unknown"
    else:
        gate_status = "legal"
        dependency_readiness = "ready"

    result["root_ancestry"] = {
        "root_address": root_address,
        "node_addresses": node_addresses,
        "relation_ids": relation_ids,
        "compressed_ancestor_addresses": compressed_addresses,
    }
    result["required_predecessors"] = sorted(required_predecessors)
    result["dependency_readiness"] = dependency_readiness
    result["gate_status"] = gate_status
    result["gate_reasons"] = hard_reasons + uncertain_reasons
    return result


def validate_residual_audit(event_type: str, audit: Any) -> list[str]:
    errors: list[str] = []
    label = f"{event_type} residual_audit"
    if not isinstance(audit, dict):
        return [f"{label} must be an object"]
    if audit.get("performed") is not True:
        errors.append(f"{label}.performed must be true")
    if audit.get("motion") != event_type:
        errors.append(f"{label}.motion must match the event type")
    if audit.get("scope") not in {"simple", "complex"}:
        errors.append(f"{label}.scope must be simple or complex")

    list_fields = (
        "delta_m_addresses",
        "delta_r_ids",
        "frontier_after_addresses",
        "compressed_frontier_addresses",
    )
    normalized_lists: dict[str, list[str]] = {}
    for field_name in list_fields:
        values = audit.get(field_name)
        if not isinstance(values, list) or not all(
            nonempty_string(value) for value in values
        ):
            errors.append(f"{label}.{field_name} must be a string list")
            normalized_lists[field_name] = []
        else:
            normalized_lists[field_name] = values
            if len(values) != len(set(values)):
                errors.append(f"{label}.{field_name} contains duplicates")

    compressed = set(normalized_lists["compressed_frontier_addresses"])
    frontier = set(normalized_lists["frontier_after_addresses"])
    if compressed - frontier:
        errors.append(
            f"{label}.compressed_frontier_addresses must be retained in frontier_after_addresses"
        )

    for field_name in ("precondition_gaps", "absorbed_outcomes"):
        values = audit.get(field_name)
        if not isinstance(values, list) or not all(
            isinstance(value, dict) for value in values
        ):
            errors.append(f"{label}.{field_name} must be a list of objects")

    checks = audit.get("checks")
    if not isinstance(checks, dict):
        errors.append(f"{label}.checks must be an object")
    else:
        for check_name in sorted(RESIDUAL_AUDIT_CHECKS):
            if checks.get(check_name) is not True:
                errors.append(f"{label}.checks.{check_name} must be true")

    if (
        audit.get("scope") == "complex"
        and not normalized_lists["delta_r_ids"]
        and not nonempty_string(audit.get("empty_residual_reason"))
    ):
        errors.append(
            f"{label}.empty_residual_reason is required when a complex motion reports no residual"
        )
    if audit.get("residual_driven_decision") not in NEXT_DECISIONS:
        errors.append(f"{label}.residual_driven_decision is invalid")
    return errors


def joint_graph_indexes(
    state: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    panorama = state.get("panorama", {})
    graph = panorama.get("graph", {}) if isinstance(panorama, dict) else {}
    nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
    relations = graph.get("relations", []) if isinstance(graph, dict) else []
    node_map = {
        item["address"]: item
        for item in nodes
        if isinstance(item, dict) and nonempty_string(item.get("address"))
    }
    relation_map = {
        item["id"]: item
        for item in relations
        if isinstance(item, dict) and nonempty_string(item.get("id"))
    }
    return node_map, relation_map


def required_dependency_relations(state: dict[str, Any]) -> list[dict[str, Any]]:
    node_map, relation_map = joint_graph_indexes(state)
    valid_nodes = {
        address
        for address, node in node_map.items()
        if node.get("validity") == "valid"
    }
    return [
        relation
        for relation in relation_map.values()
        if relation.get("relation_type") == "dependency"
        and relation.get("necessity") == "required"
        and relation.get("validity") == "valid"
        and relation.get("source") in valid_nodes
        and relation.get("target") in valid_nodes
    ]


def strongly_connected_components(
    nodes: set[str], relations: list[dict[str, Any]]
) -> list[list[str]]:
    """Return deterministic Tarjan SCCs for a directed graph."""
    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    for relation in relations:
        source = relation.get("source")
        target = relation.get("target")
        if source in nodes and target in nodes:
            adjacency[source].add(target)

    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for successor in sorted(adjacency.get(node, set())):
            if successor not in indices:
                visit(successor)
                lowlinks[node] = min(lowlinks[node], lowlinks[successor])
            elif successor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[successor])
        if lowlinks[node] == indices[node]:
            component: list[str] = []
            while stack:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            components.append(sorted(component))

    for node in sorted(nodes):
        if node not in indices:
            visit(node)
    return sorted(components, key=lambda component: tuple(component))


def joint_scc_snapshot(state: dict[str, Any]) -> list[dict[str, Any]]:
    node_map, _ = joint_graph_indexes(state)
    valid_nodes = {
        address
        for address, node in node_map.items()
        if node.get("validity") == "valid"
    }
    relations = required_dependency_relations(state)
    adjacency: dict[str, set[str]] = {address: set() for address in valid_nodes}
    for relation in relations:
        adjacency.setdefault(relation["source"], set()).add(relation["target"])
    self_loops = {
        relation.get("source")
        for relation in relations
        if relation.get("source") == relation.get("target")
    }
    components: list[dict[str, Any]] = []
    for members in strongly_connected_components(valid_nodes, relations):
        if len(members) == 1 and members[0] not in self_loops:
            continue
        member_set = set(members)
        relation_ids = sorted(
            relation["id"]
            for relation in relations
            if relation.get("source") in member_set
            and relation.get("target") in member_set
        )
        required_descendants = sorted(
            reachable(members[0], adjacency) - member_set
            if len(members) == 1
            else set().union(*(reachable(member, adjacency) for member in members))
            - member_set
        )
        digest = hashlib.sha256("\0".join(members).encode("utf-8")).hexdigest()[:12]
        components.append(
            {
                "id": f"SCC-{digest}",
                "members": members,
                "relation_ids": relation_ids,
                **(
                    {"required_descendants": required_descendants}
                    if has_field_formation_schema(state)
                    else {}
                ),
                "classification": "non-poset",
                "residual_id": f"R-SCC-{digest}",
            }
        )
    return components


def make_scc_residual(component: dict[str, Any], motion: str) -> dict[str, Any]:
    members = component["members"]
    joined = ", ".join(members)
    return {
        "id": component["residual_id"],
        "classification": "true-residual",
        "residual_type": "non-poset",
        "description": f"required dependency SCC cannot enter the selected order: {joined}",
        "origin": "closure-produced",
        "produced_by": {"motion": motion, "address": members[0] if members else None},
        "failing_address": members[0] if members else None,
        "effect_on_f0": "the required dependency projection cannot certify a legal partial order",
        "representation_failure": "mutually required addresses cannot be represented as an antisymmetric necessary-predecessor order without quotient evidence",
        "modal_status": "[∅]",
        "possible_destination": "in-field-remodel",
        "changes_focus_or_execution": {
            "changes": True,
            "reason": "exclude the unresolved SCC from legal Focus and execution gates",
        },
        "tolerance_status": "above",
        "evidence_status": "inferred",
        "address_relation": {
            "kind": "no-address",
            "address": None,
            "gate_status": "out-of-field",
            "reach": {
                "kind": "unreachable",
                "estimated_expansions": None,
                "evidence_status": "inferred",
            },
            "conflict_with": list(members),
        },
        "absorption_status": "unresolved",
        "closure_condition": "resolve or quotient the required SCC with explicit evidence, then rebuild the necessary order",
    }


def rebuild_joint_order(
    state: dict[str, Any], motion: str, *, order_status: str = "tentative"
) -> None:
    """Derive the joint-schema necessary order and preserve cyclic failures."""
    panorama = state["panorama"]
    graph = panorama["graph"]
    components = joint_scc_snapshot(state)
    cyclic_nodes = {
        address for component in components for address in component["members"]
    }
    blocked_descendants = {
        address
        for component in components
        for address in component.get("required_descendants", [])
    }
    excluded_nodes = cyclic_nodes | blocked_descendants
    existing_residuals = {
        item.get("id"): item
        for item in panorama.get("residuals", [])
        if isinstance(item, dict) and nonempty_string(item.get("id"))
    }
    for component in components:
        residual_id = component["residual_id"]
        generated = make_scc_residual(component, motion)
        if residual_id not in existing_residuals:
            panorama["residuals"].append(generated)
            existing_residuals[residual_id] = generated
        elif has_field_formation_schema(state):
            for field_name in (
                "address_relation",
                "absorption_status",
                "closure_condition",
            ):
                existing_residuals[residual_id].setdefault(
                    field_name, copy.deepcopy(generated[field_name])
                )

    retained_nodes = [
        node
        for node in graph["nodes"]
        if isinstance(node, dict)
        and node.get("validity") == "valid"
        and node.get("address") not in excluded_nodes
    ]
    retained_addresses = {node["address"] for node in retained_nodes}
    retained_relations = [
        relation
        for relation in required_dependency_relations(state)
        if relation.get("source") in retained_addresses
        and relation.get("target") in retained_addresses
    ]
    old_order = panorama.get("order", {})
    incomparables = (
        old_order.get("explicit_incomparables", [])
        if isinstance(old_order, dict)
        else []
    )
    filtered_incomparables = [
        pair
        for pair in incomparables
        if isinstance(pair, list)
        and len(pair) == 2
        and pair[0] in retained_addresses
        and pair[1] in retained_addresses
    ]
    panorama["order"] = {
        "status": order_status,
        "derived_from_map_version": panorama["map_version"],
        "nodes": [
            {
                "address": node["address"],
                "function": node.get("function", ""),
                "evidence_status": node.get("evidence_status", "unknown"),
                "modal_status": node.get("modal_status"),
                "validity": node.get("validity"),
            }
            for node in retained_nodes
        ],
        "relations": [
            {
                "id": relation["id"],
                "predecessor": relation["source"],
                "successor": relation["target"],
                "necessity": "required",
                "evidence_status": relation.get("evidence_status", "unknown"),
                "validity": relation.get("validity"),
            }
            for relation in retained_relations
        ],
        "explicit_incomparables": filtered_incomparables,
        "scc_analysis": {
            "performed": True,
            "components": components,
            "non_poset_residual_ids": [
                component["residual_id"] for component in components
            ],
        },
    }
    panorama["explored"] = sorted(
        node["address"]
        for node in graph["nodes"]
        if isinstance(node, dict)
        and node.get("validity") == "valid"
        and node.get("modal_status") == "[+]"
    )

    center = state.get("center", {})
    if isinstance(center, dict):
        selected = center.get("selected")
        for candidate in center.get("candidates", []):
            if not isinstance(candidate, dict):
                continue
            if any(member not in retained_addresses for member in candidate.get("members", [])):
                candidate["validity"] = "stale"
                candidate["minimality_status"] = "unvalidated"
                if candidate.get("id") == selected:
                    center["selected"] = None
                    center["status"] = "remodel-required"


def normalize_joint_path(
    state: dict[str, Any],
    item: dict[str, Any],
    *,
    modal_status: str,
    require_action_ready: bool = False,
) -> dict[str, Any]:
    result = audit_path(
        state, item, require_action_ready=require_action_ready
    )
    result["modal_status"] = modal_status
    result.setdefault(
        "task_scores",
        {
            "relevance": None,
            "impact": None,
            "heat": None,
            "cost": None,
            "priority": None,
        },
    )
    result.setdefault("status", "candidate")
    return result


def normalize_joint_frontiers(
    state: dict[str, Any], frontiers: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(frontiers, dict):
        raise ValueError("frontiers_after must be an object")
    normalized: dict[str, list[dict[str, Any]]] = {}
    for frontier_type in sorted(FRONTIER_TYPES):
        items = frontiers.get(frontier_type)
        if not isinstance(items, list) or not all(
            isinstance(item, dict) for item in items
        ):
            raise ValueError(f"frontiers_after.{frontier_type} must be a list of objects")
        if frontier_type == "compressed":
            normalized[frontier_type] = [copy.deepcopy(item) for item in items]
    audit_state = copy.deepcopy(state)
    audit_state["panorama"]["frontiers"]["compressed"] = normalized["compressed"]
    for frontier_type in ("action", "expansion"):
        normalized[frontier_type] = [
            normalize_joint_path(
                audit_state,
                item,
                modal_status="[◇]",
                require_action_ready=frontier_type == "action",
            )
            for item in frontiers[frontier_type]
        ]
    return normalized


def validate_joint_residual_record(
    residual: Any, label: str, *, current: bool = False, archived: bool = False
) -> list[str]:
    errors: list[str] = []
    if not isinstance(residual, dict):
        return [f"{label} must be an object"]
    if not nonempty_string(residual.get("id")):
        errors.append(f"{label}.id must be non-empty")
    if residual.get("classification") != "true-residual":
        errors.append(f"{label}.classification must be true-residual")
    if residual.get("residual_type") not in RESIDUAL_TYPES:
        errors.append(f"{label}.residual_type is invalid")
    for field_name in ("description", "effect_on_f0", "representation_failure"):
        if not nonempty_string(residual.get(field_name)):
            errors.append(f"{label}.{field_name} must be non-empty")
    produced_by = residual.get("produced_by")
    if not isinstance(produced_by, dict):
        errors.append(f"{label}.produced_by must be an object")
    else:
        if produced_by.get("motion") not in JOINT_MOTION_TYPES:
            errors.append(f"{label}.produced_by.motion is invalid")
        if produced_by.get("address") is not None and not nonempty_string(
            produced_by.get("address")
        ):
            errors.append(f"{label}.produced_by.address must be null or non-empty")
    if residual.get("modal_status") not in RESIDUAL_MODAL_STATUSES:
        errors.append(f"{label}.modal_status must be [+], [◇], [-], or [∅]")
    if residual.get("possible_destination") not in RESIDUAL_DESTINATIONS:
        errors.append(f"{label}.possible_destination is invalid")
    scheduling = residual.get("changes_focus_or_execution")
    if not isinstance(scheduling, dict) or not isinstance(
        scheduling.get("changes"), bool
    ):
        errors.append(f"{label}.changes_focus_or_execution needs boolean changes")
    elif scheduling.get("changes") and not nonempty_string(scheduling.get("reason")):
        errors.append(
            f"{label}.changes_focus_or_execution.reason is required when changes is true"
        )
    if residual.get("tolerance_status") not in {"below", "near", "above", "unknown"}:
        errors.append(f"{label}.tolerance_status is invalid")
    if residual.get("evidence_status") not in EVIDENCE_STATUSES:
        errors.append(f"{label}.evidence_status is invalid")
    if current:
        relation = residual.get("address_relation")
        if not isinstance(relation, dict):
            errors.append(f"{label}.address_relation must be an object")
        else:
            kind = relation.get("kind")
            if kind not in ADDRESS_RELATION_KINDS:
                errors.append(f"{label}.address_relation.kind is invalid")
            address = relation.get("address")
            if kind in {"realized", "frontier", "hypothesized"} and not nonempty_string(address):
                errors.append(f"{label}.address_relation.address is required for {kind}")
            if kind in {"negative", "no-address"} and address is not None and not nonempty_string(address):
                errors.append(f"{label}.address_relation.address must be null or non-empty")
            if relation.get("gate_status") not in ADDRESS_RELATION_GATES:
                errors.append(f"{label}.address_relation.gate_status is invalid")
            reach = relation.get("reach")
            if not isinstance(reach, dict):
                errors.append(f"{label}.address_relation.reach must be an object")
            else:
                if reach.get("kind") not in ADDRESS_REACH_KINDS:
                    errors.append(f"{label}.address_relation.reach.kind is invalid")
                estimate = reach.get("estimated_expansions")
                if estimate is not None and (not isinstance(estimate, int) or estimate < 0):
                    errors.append(
                        f"{label}.address_relation.reach.estimated_expansions must be null or non-negative"
                    )
                if reach.get("evidence_status") not in EVIDENCE_STATUSES:
                    errors.append(f"{label}.address_relation.reach.evidence_status is invalid")
            conflicts = relation.get("conflict_with")
            if not isinstance(conflicts, list) or not all(nonempty_string(item) for item in conflicts):
                errors.append(f"{label}.address_relation.conflict_with must be a string list")
        absorption = residual.get("absorption_status")
        if absorption not in ABSORPTION_STATUSES:
            errors.append(f"{label}.absorption_status is invalid")
        if archived:
            if absorption != "absorbed":
                errors.append(f"{label}.absorption_status must be absorbed in residual_history")
            if not isinstance(residual.get("absorbed_by"), dict):
                errors.append(f"{label}.absorbed_by must be an object")
            if not isinstance(residual.get("absorbed_at_version"), int):
                errors.append(f"{label}.absorbed_at_version must be an integer")
        elif absorption == "absorbed":
            errors.append(f"{label} must move to residual_history when absorbed")
        if not nonempty_string(residual.get("closure_condition")):
            errors.append(f"{label}.closure_condition must be non-empty")
    return errors


def validate_address_dynamics_22(
    state: dict[str, Any], evidence_ids: set[str], residual_ids: set[str]
) -> list[str]:
    errors: list[str] = []
    dynamics = state.get("address_dynamics")
    if not isinstance(dynamics, dict):
        return ["address_dynamics must be an object"]
    required = {"root_address", "inbox", "motions", "lineage", "field_versions"}
    missing = sorted(required - set(dynamics))
    if missing:
        errors.append("address_dynamics missing keys: " + ", ".join(missing))
    if dynamics.get("root_address") != "F0":
        errors.append("address_dynamics.root_address must remain F0")

    inbox = dynamics.get("inbox")
    if not isinstance(inbox, list):
        errors.append("address_dynamics.inbox must be a list")
        inbox = []
    update_map: dict[str, dict[str, Any]] = {}
    for index, update in enumerate(inbox):
        label = f"address_dynamics.inbox[{index}]"
        if not isinstance(update, dict) or not nonempty_string(update.get("id")):
            errors.append(f"{label}.id must be non-empty")
            continue
        update_id = update["id"]
        if update_id in update_map:
            errors.append(f"duplicate update id: {update_id}")
        update_map[update_id] = update
        if update.get("intake_address") != f"F0@{update_id}":
            errors.append(f"{label}.intake_address must equal F0@{update_id}")
        if not nonempty_string(update.get("raw_content")):
            errors.append(f"{label}.raw_content must be non-empty")
        source = update.get("source")
        if not isinstance(source, dict) or source.get("kind") not in UPDATE_SOURCE_KINDS:
            errors.append(f"{label}.source.kind is invalid")
        elif source.get("ref") is not None and not nonempty_string(source.get("ref")):
            errors.append(f"{label}.source.ref must be null or non-empty")
        if not isinstance(update.get("received_at_runtime_version"), int):
            errors.append(f"{label}.received_at_runtime_version must be an integer")
        refs = update.get("evidence_ids")
        if not isinstance(refs, list) or not all(nonempty_string(item) for item in refs):
            errors.append(f"{label}.evidence_ids must be a string list")
        elif set(refs) - evidence_ids:
            errors.append(f"{label}.evidence_ids references unknown evidence")
        if update.get("status") not in UPDATE_STATUSES:
            errors.append(f"{label}.status is invalid")
        if not isinstance(update.get("motion_ids"), list) or not all(
            nonempty_string(item) for item in update.get("motion_ids", [])
        ):
            errors.append(f"{label}.motion_ids must be a string list")

    motions = dynamics.get("motions")
    if not isinstance(motions, list):
        errors.append("address_dynamics.motions must be a list")
        motions = []
    motion_map: dict[str, dict[str, Any]] = {}
    for index, motion in enumerate(motions):
        label = f"address_dynamics.motions[{index}]"
        if not isinstance(motion, dict) or not nonempty_string(motion.get("id")):
            errors.append(f"{label}.id must be non-empty")
            continue
        motion_id = motion["id"]
        if motion_id in motion_map:
            errors.append(f"duplicate address motion id: {motion_id}")
        motion_map[motion_id] = motion
        if motion.get("update_id") not in update_map:
            errors.append(f"{label}.update_id references an unknown update")
        if motion.get("classification") not in UPDATE_CLASSIFICATIONS:
            errors.append(f"{label}.classification is invalid")
        if motion.get("motion_operator") not in UPDATE_MOTION_OPERATORS:
            errors.append(f"{label}.motion_operator is invalid")
        if motion.get("status") not in ADDRESS_MOTION_STATUSES:
            errors.append(f"{label}.status is invalid")
        if not nonempty_string(motion.get("branch_id")):
            errors.append(f"{label}.branch_id must be non-empty")
        if not isinstance(motion.get("structured_at_runtime_version"), int):
            errors.append(f"{label}.structured_at_runtime_version must be an integer")
        applied = motion.get("applied_at_runtime_version")
        if applied is not None and not isinstance(applied, int):
            errors.append(f"{label}.applied_at_runtime_version must be null or integer")
        source_versions = motion.get("source_field_version_ids")
        if not isinstance(source_versions, list) or not all(
            nonempty_string(item) for item in source_versions
        ):
            errors.append(f"{label}.source_field_version_ids must be a string list")
        assignment = motion.get("assignment")
        if not isinstance(assignment, dict):
            errors.append(f"{label}.assignment must be an object")
        else:
            if assignment.get("kind") not in UPDATE_ASSIGNMENT_KINDS:
                errors.append(f"{label}.assignment.kind is invalid")
            for name in ("anchor_addresses", "from_addresses", "to_addresses"):
                addresses = assignment.get(name)
                if not isinstance(addresses, list) or not all(
                    is_strict_theory_address(item) for item in addresses or []
                ):
                    errors.append(f"{label}.assignment.{name} must use F0 addresses")
            if assignment.get("modal_status") not in {None, *MODAL_STATUSES}:
                errors.append(f"{label}.assignment.modal_status is invalid")
            if not nonempty_string(assignment.get("rationale")):
                errors.append(f"{label}.assignment.rationale must be non-empty")
        closure = motion.get("closure_audit")
        if not isinstance(closure, dict):
            errors.append(f"{label}.closure_audit must be an object")
        else:
            if closure.get("closure_before") not in WORKING_CLOSURE_STATUSES:
                errors.append(f"{label}.closure_audit.closure_before is invalid")
            if closure.get("closure_after") not in WORKING_CLOSURE_STATUSES:
                errors.append(f"{label}.closure_audit.closure_after is invalid")
            for name in (
                "nearest_unstable_ancestor",
                "minimal_rebuild_root",
                "propagation_stop_address",
            ):
                value = closure.get(name)
                if value is not None and not is_strict_theory_address(value):
                    errors.append(f"{label}.closure_audit.{name} must be null or F0 address")
            tested = closure.get("tested")
            if not isinstance(tested, list) or not all(
                isinstance(item, dict) for item in tested or []
            ):
                errors.append(f"{label}.closure_audit.tested must be an object list")
        for ref_name in ("lineage_ids", "result_closure_version_ids", "residual_ids", "evidence_ids"):
            refs = motion.get(ref_name)
            if not isinstance(refs, list) or not all(nonempty_string(item) for item in refs):
                errors.append(f"{label}.{ref_name} must be a string list")
        if isinstance(motion.get("residual_ids"), list) and set(motion["residual_ids"]) - residual_ids:
            errors.append(f"{label}.residual_ids references unknown active residuals")
        if isinstance(motion.get("evidence_ids"), list) and set(motion["evidence_ids"]) - evidence_ids:
            errors.append(f"{label}.evidence_ids references unknown evidence")

    for update_id, update in update_map.items():
        refs = update.get("motion_ids", [])
        if isinstance(refs, list) and set(refs) - set(motion_map):
            errors.append(f"update {update_id} references unknown motion ids")
        if update.get("status") == "pending" and refs:
            errors.append(f"pending update {update_id} cannot already reference motions")
        if update.get("status") == "structured" and not refs:
            errors.append(f"structured update {update_id} needs at least one motion")
        referenced_motions = [motion_map[item] for item in refs if item in motion_map]
        proposed_count = sum(
            item.get("status") == "proposed" for item in referenced_motions
        )
        if proposed_count > 1:
            errors.append(f"update {update_id} cannot have multiple proposed motions")
        if update.get("status") == "resolved":
            if not referenced_motions:
                errors.append(f"resolved update {update_id} needs a motion history")
            if proposed_count:
                errors.append(f"resolved update {update_id} cannot retain a proposed motion")

    lineage = dynamics.get("lineage")
    if not isinstance(lineage, list):
        errors.append("address_dynamics.lineage must be a list")
        lineage = []
    lineage_map: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(lineage):
        label = f"address_dynamics.lineage[{index}]"
        if not isinstance(record, dict) or not nonempty_string(record.get("id")):
            errors.append(f"{label}.id must be non-empty")
            continue
        lineage_id = record["id"]
        if lineage_id in lineage_map:
            errors.append(f"duplicate lineage id: {lineage_id}")
        lineage_map[lineage_id] = record
        if record.get("motion_id") not in motion_map:
            errors.append(f"{label}.motion_id references an unknown motion")
        kind = record.get("kind")
        if kind not in ADDRESS_LINEAGE_KINDS:
            errors.append(f"{label}.kind is invalid")
        endpoints: dict[str, list[dict[str, Any]]] = {}
        for side in ("from", "to"):
            items = record.get(side)
            if not isinstance(items, list) or not all(isinstance(item, dict) for item in items or []):
                errors.append(f"{label}.{side} must be an object list")
                items = []
            endpoints[side] = items
            for endpoint in items:
                if not nonempty_string(endpoint.get("node_id")):
                    errors.append(f"{label}.{side}.node_id must be non-empty")
                address = endpoint.get("address")
                if not is_strict_theory_address(address):
                    errors.append(f"{label}.{side}.address must retain the F0 root")
                if not isinstance(endpoint.get("payload_revision"), int) or endpoint.get("payload_revision", 0) < 1:
                    errors.append(f"{label}.{side}.payload_revision must be positive")
        source_count = len(endpoints["from"])
        target_count = len(endpoints["to"])
        expected_shapes = {
            "retain": (1, 1),
            "payload-replace": (1, 1),
            "move": (1, 1),
            "split": (1, None),
            "merge": (None, 1),
            "retire": (None, 0),
            "birth": (0, None),
            "externalize": (1, 0),
            "prohibit": (1, 0),
        }
        if kind in expected_shapes:
            expected_from, expected_to = expected_shapes[kind]
            if expected_from is not None and source_count != expected_from:
                errors.append(f"{label} has invalid source cardinality for {kind}")
            if expected_to is not None and target_count != expected_to:
                errors.append(f"{label} has invalid target cardinality for {kind}")
            if kind == "split" and target_count < 2:
                errors.append(f"{label}.split needs at least two targets")
            if kind == "merge" and source_count < 2:
                errors.append(f"{label}.merge needs at least two sources")
            if kind == "retire" and source_count < 1:
                errors.append(f"{label}.retire needs at least one source")
            if kind == "birth" and target_count < 1:
                errors.append(f"{label}.birth needs at least one target")
        if kind == "expand" and (source_count != 1 or target_count < 2):
            errors.append(f"{label}.expand must retain one source and add descendants")
        if kind in {"retain", "payload-replace", "move"} and source_count == 1 and target_count == 1:
            source_endpoint = endpoints["from"][0]
            target_endpoint = endpoints["to"][0]
            if kind == "retain" and any(
                source_endpoint.get(name) != target_endpoint.get(name)
                for name in ("node_id", "address", "payload_revision")
            ):
                errors.append(f"{label}.retain must preserve node, address, and payload revision")
            if kind == "payload-replace":
                if source_endpoint.get("node_id") != target_endpoint.get("node_id") or source_endpoint.get("address") != target_endpoint.get("address"):
                    errors.append(f"{label}.payload-replace must preserve node id and address")
                if target_endpoint.get("payload_revision") != source_endpoint.get("payload_revision", 0) + 1:
                    errors.append(f"{label}.payload-replace must increment payload revision by one")
            if kind == "move" and source_endpoint.get("node_id") != target_endpoint.get("node_id"):
                errors.append(f"{label}.move must preserve node id")
        if kind in {"move", "split", "merge", "retire", "externalize", "prohibit"} and any(
            item.get("address") == "F0" for side in endpoints.values() for item in side
        ):
            errors.append(f"{label} cannot {kind} the F0 root address")
        if not nonempty_string(record.get("reason")):
            errors.append(f"{label}.reason must be non-empty")
        refs = record.get("evidence_ids")
        if not isinstance(refs, list) or not all(nonempty_string(item) for item in refs):
            errors.append(f"{label}.evidence_ids must be a string list")
        elif set(refs) - evidence_ids:
            errors.append(f"{label}.evidence_ids references unknown evidence")

    versions = dynamics.get("field_versions")
    if not isinstance(versions, dict):
        errors.append("address_dynamics.field_versions must be an object")
        return errors
    branches = versions.get("branches")
    if not isinstance(branches, list):
        errors.append("field_versions.branches must be a list")
        branches = []
    branch_ids: list[str] = []
    for index, branch in enumerate(branches):
        label = f"field_versions.branches[{index}]"
        if not isinstance(branch, dict) or not nonempty_string(branch.get("id")):
            errors.append(f"{label}.id must be non-empty")
            continue
        branch_ids.append(branch["id"])
        if branch.get("parent_branch_id") is not None and not nonempty_string(branch.get("parent_branch_id")):
            errors.append(f"{label}.parent_branch_id must be null or non-empty")
        if branch.get("status") not in BRANCH_STATUSES:
            errors.append(f"{label}.status is invalid")
    if len(branch_ids) != len(set(branch_ids)):
        errors.append("field_versions.branches contains duplicate ids")
    branch_map = {
        item.get("id"): item
        for item in branches
        if isinstance(item, dict) and nonempty_string(item.get("id"))
    }
    for branch_id, branch in branch_map.items():
        parent_branch_id = branch.get("parent_branch_id")
        if parent_branch_id is not None and parent_branch_id not in branch_map:
            errors.append(
                f"field version branch {branch_id} references unknown parent branch"
            )
    branch_visiting: set[str] = set()
    branch_visited: set[str] = set()

    def visit_branch(branch_id: str) -> None:
        if branch_id in branch_visited:
            return
        if branch_id in branch_visiting:
            errors.append(f"field-version branch lineage contains a cycle at {branch_id}")
            return
        branch_visiting.add(branch_id)
        parent_branch_id = branch_map.get(branch_id, {}).get("parent_branch_id")
        if parent_branch_id in branch_map:
            visit_branch(parent_branch_id)
        branch_visiting.remove(branch_id)
        branch_visited.add(branch_id)

    for branch_id in branch_map:
        visit_branch(branch_id)
    if versions.get("active_branch_id") not in set(branch_ids):
        errors.append("field_versions.active_branch_id references an unknown branch")

    records = versions.get("records")
    if not isinstance(records, list):
        errors.append("field_versions.records must be a list")
        records = []
    version_map: dict[str, dict[str, Any]] = {}
    version_coordinates: set[tuple[str, str, int]] = set()
    for index, record in enumerate(records):
        label = f"field_versions.records[{index}]"
        if not isinstance(record, dict) or not nonempty_string(record.get("id")):
            errors.append(f"{label}.id must be non-empty")
            continue
        version_id = record["id"]
        if version_id in version_map:
            errors.append(f"duplicate field version id: {version_id}")
        version_map[version_id] = record
        if record.get("branch_id") not in set(branch_ids):
            errors.append(f"{label}.branch_id references an unknown branch")
        if not is_strict_theory_address(record.get("field_address")):
            errors.append(f"{label}.field_address must retain F0 root")
        if not isinstance(record.get("ordinal"), int) or record.get("ordinal", 0) < 1:
            errors.append(f"{label}.ordinal must be positive")
        elif nonempty_string(record.get("branch_id")) and is_strict_theory_address(
            record.get("field_address")
        ):
            coordinate = (
                record["branch_id"],
                record["field_address"],
                record["ordinal"],
            )
            if coordinate in version_coordinates:
                errors.append(
                    f"duplicate field-version coordinate: {coordinate}"
                )
            version_coordinates.add(coordinate)
        if record.get("closure_status") not in FIELD_CLOSURE_STATUSES:
            errors.append(f"{label}.closure_status must be relative-closed")
        if record.get("root_address") != "F0":
            errors.append(f"{label}.root_address must remain F0")
        for name in (
            "parent_ids",
            "absorbed_update_ids",
            "absorbed_residual_ids",
            "lineage_ids",
            "reused_addresses",
        ):
            refs = record.get(name)
            if not isinstance(refs, list) or not all(nonempty_string(item) for item in refs):
                errors.append(f"{label}.{name} must be a string list")
        if isinstance(record.get("absorbed_update_ids"), list) and set(record["absorbed_update_ids"]) - set(update_map):
            errors.append(f"{label}.absorbed_update_ids references unknown updates")
        if isinstance(record.get("absorbed_residual_ids"), list) and set(record["absorbed_residual_ids"]) - residual_ids:
            errors.append(f"{label}.absorbed_residual_ids references unknown residuals")
        if isinstance(record.get("lineage_ids"), list) and set(record["lineage_ids"]) - set(lineage_map):
            errors.append(f"{label}.lineage_ids references unknown lineage")
        if isinstance(record.get("reused_addresses"), list) and not all(
            is_strict_theory_address(item) for item in record["reused_addresses"]
        ):
            errors.append(f"{label}.reused_addresses must retain F0 root")
        if not isinstance(record.get("formed_at_runtime_version"), int):
            errors.append(f"{label}.formed_at_runtime_version must be an integer")
        if record.get("formed_by_motion_id") not in motion_map:
            errors.append(f"{label}.formed_by_motion_id references unknown motion")
        if not isinstance(record.get("map_version"), int):
            errors.append(f"{label}.map_version must be an integer")
        snapshot_ref = record.get("snapshot_ref")
        snapshot_hash = record.get("snapshot_hash")
        if (snapshot_ref is None) != (snapshot_hash is None):
            errors.append(
                f"{label}.snapshot_ref and snapshot_hash must be provided together"
            )
        if snapshot_ref is not None and not nonempty_string(snapshot_ref):
            errors.append(f"{label}.snapshot_ref must be non-empty when provided")
        if snapshot_hash is not None and not re.fullmatch(
            r"sha256:[0-9a-f]{64}", str(snapshot_hash)
        ):
            errors.append(f"{label}.snapshot_hash must be a lowercase sha256 digest")

    for version_id, record in version_map.items():
        parents = record.get("parent_ids", [])
        if isinstance(parents, list) and set(parents) - set(version_map):
            errors.append(f"field version {version_id} references unknown parents")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(version_id: str) -> None:
        if version_id in visited:
            return
        if version_id in visiting:
            errors.append(f"field-version lineage contains a cycle at {version_id}")
            return
        visiting.add(version_id)
        for parent_id in version_map.get(version_id, {}).get("parent_ids", []):
            if parent_id in version_map:
                visit(parent_id)
        visiting.remove(version_id)
        visited.add(version_id)

    for version_id in version_map:
        visit(version_id)

    for lineage_id, record in lineage_map.items():
        for side in ("from", "to"):
            for endpoint in record.get(side, []):
                field_version_id = endpoint.get("field_version_id")
                if field_version_id is not None and field_version_id not in version_map:
                    errors.append(
                        f"lineage {lineage_id} references unknown field version {field_version_id}"
                    )

    heads = versions.get("heads")
    if not isinstance(heads, list):
        errors.append("field_versions.heads must be a list")
        heads = []
    head_keys: set[tuple[str, str]] = set()
    for index, head in enumerate(heads):
        label = f"field_versions.heads[{index}]"
        if not isinstance(head, dict):
            errors.append(f"{label} must be an object")
            continue
        branch_id = head.get("branch_id")
        field_address = head.get("field_address")
        if branch_id not in set(branch_ids):
            errors.append(f"{label}.branch_id references an unknown branch")
        if not is_strict_theory_address(field_address):
            errors.append(f"{label}.field_address must retain F0 root")
        key = (branch_id, field_address)
        if key in head_keys:
            errors.append(f"duplicate field-version head: {key}")
        head_keys.add(key)
        version_id = head.get("version_id")
        if version_id is not None and version_id not in version_map:
            errors.append(f"{label}.version_id references an unknown field version")
        elif version_id is not None:
            pointed = version_map[version_id]
            if pointed.get("branch_id") != branch_id or pointed.get("field_address") != field_address:
                errors.append(
                    f"{label}.version_id must match the head branch and field address"
                )
        if head.get("working_closure") not in WORKING_CLOSURE_STATUSES:
            errors.append(f"{label}.working_closure is invalid")
        if not isinstance(head.get("destabilized_by_motion_ids"), list):
            errors.append(f"{label}.destabilized_by_motion_ids must be a list")

    for motion_id, motion in motion_map.items():
        if isinstance(motion.get("source_field_version_ids"), list) and set(
            motion["source_field_version_ids"]
        ) - set(version_map):
            errors.append(f"motion {motion_id} references unknown source field versions")
        if isinstance(motion.get("lineage_ids"), list) and set(motion["lineage_ids"]) - set(lineage_map):
            errors.append(f"motion {motion_id} references unknown lineage ids")
        if isinstance(motion.get("result_closure_version_ids"), list) and set(motion["result_closure_version_ids"]) - set(version_map):
            errors.append(f"motion {motion_id} references unknown field versions")
    return errors


def validate_joint_state(state: dict[str, Any]) -> list[str]:
    """Validate every schema-2.0+ joint-model surface."""
    errors: list[str] = []
    current = has_field_formation_schema(state)
    current_22 = is_current_schema(state)
    raw_evidence = state.get("evidence", [])
    evidence_id_set = {
        item.get("id")
        for item in raw_evidence
        if isinstance(item, dict) and nonempty_string(item.get("id"))
    }
    missing = sorted(JOINT_REQUIRED_KEYS - set(state))
    if missing:
        errors.append(f"joint schema missing top-level keys: {', '.join(missing)}")
    if current_22 and "address_dynamics" not in state:
        errors.append("schema 2.2 missing top-level key: address_dynamics")

    def string_list(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
        if not isinstance(value, list) or not all(nonempty_string(item) for item in value):
            errors.append(f"{label} must be a string list")
            return []
        if nonempty and not value:
            errors.append(f"{label} must not be empty")
        if len(value) != len(set(value)):
            errors.append(f"{label} contains duplicates")
        return value

    field = state.get("field")
    if not isinstance(field, dict):
        return [*errors, "field must be an object"]
    required_field_keys = {
        "id",
        "name",
        "root_goal" if current else "ancestor_goal",
        "boundary",
        "success_criteria",
        "immutable_constraints",
        "allowed_changes",
        "legal_roots",
        "tolerance",
        "status",
    }
    if current:
        required_field_keys.update(
            {"phase", "contract_status", "ambiguities", "human_calibration"}
        )
    if current_22:
        required_field_keys.add("f0_confirmation")
    missing_field = sorted(required_field_keys - set(field))
    if missing_field:
        errors.append("field missing keys: " + ", ".join(missing_field))
    root_goal_key = "root_goal" if current else "ancestor_goal"
    for field_name in ("id", "name", root_goal_key, "status"):
        if not nonempty_string(field.get(field_name)):
            errors.append(f"field.{field_name} must be non-empty")
    boundary = field.get("boundary")
    if not isinstance(boundary, dict):
        errors.append("field.boundary must be an object")
    else:
        string_list(boundary.get("included"), "field.boundary.included")
        string_list(boundary.get("excluded"), "field.boundary.excluded")
    string_list(field.get("success_criteria"), "field.success_criteria")
    string_list(field.get("immutable_constraints"), "field.immutable_constraints")
    string_list(field.get("allowed_changes"), "field.allowed_changes")
    roots = string_list(field.get("legal_roots"), "field.legal_roots", nonempty=True)
    if field.get("id") not in roots:
        errors.append("field.id must be included in field.legal_roots")
    if current_22:
        if field.get("id") != "F0":
            errors.append("schema 2.2 field.id must remain F0")
        if roots != ["F0"]:
            errors.append("schema 2.2 field.legal_roots must equal [F0]")
    tolerance = field.get("tolerance")
    if not isinstance(tolerance, dict):
        errors.append("field.tolerance must be an object")
    elif set(tolerance) < {"criterion", "threshold"}:
        errors.append("field.tolerance needs criterion and threshold")
    if current:
        if field.get("phase") not in FIELD_PHASES:
            errors.append("field.phase is invalid")
        if field.get("contract_status") not in CONTRACT_STATUSES:
            errors.append("field.contract_status is invalid")
        string_list(field.get("ambiguities"), "field.ambiguities")
        calibration = field.get("human_calibration")
        if not isinstance(calibration, dict):
            errors.append("field.human_calibration must be an object")
        else:
            if calibration.get("status") not in CALIBRATION_STATUSES:
                errors.append("field.human_calibration.status is invalid")
            if not isinstance(calibration.get("items"), list) or not all(
                isinstance(item, dict) for item in calibration.get("items", [])
            ):
                errors.append("field.human_calibration.items must be a list of objects")
        if current_22:
            confirmation = field.get("f0_confirmation")
            if not isinstance(confirmation, dict):
                errors.append("field.f0_confirmation must be an object")
            else:
                status = confirmation.get("status")
                if status not in F0_CONFIRMATION_STATUSES:
                    errors.append("field.f0_confirmation.status is invalid")
                confirmed_by = confirmation.get("confirmed_by")
                confirmed_at = confirmation.get("confirmed_at_runtime_version")
                if status == "required":
                    if confirmed_by is not None or confirmed_at is not None:
                        errors.append(
                            "required F0 confirmation cannot have confirmation provenance"
                        )
                elif status in {"confirmed", "bypassed"}:
                    if not nonempty_string(confirmed_by):
                        errors.append(
                            "confirmed or bypassed F0 requires confirmed_by"
                        )
                    if (
                        not isinstance(confirmed_at, int)
                        or isinstance(confirmed_at, bool)
                        or confirmed_at < 0
                        or confirmed_at > state.get("version", -1)
                    ):
                        errors.append(
                            "confirmed_at_runtime_version must reference the current history"
                        )

    panorama = state.get("panorama")
    if not isinstance(panorama, dict):
        return [*errors, "panorama must be an object"]
    required_panorama_keys = {
        "map_version",
        "global_expansion",
        "graph",
        "order",
        "explored",
        "frontiers",
        "external",
        "residuals",
        "modal_results",
    }
    if current:
        required_panorama_keys.add("residual_history")
    missing_panorama = sorted(required_panorama_keys - set(panorama))
    if missing_panorama:
        errors.append("panorama missing keys: " + ", ".join(missing_panorama))
    map_version = panorama.get("map_version")
    if not isinstance(map_version, int) or map_version < 0:
        errors.append("panorama.map_version must be a non-negative integer")

    graph = panorama.get("graph")
    if not isinstance(graph, dict):
        errors.append("panorama.graph must be an object")
        graph = {}
    if graph.get("status") not in ORDER_STATUSES:
        errors.append("panorama.graph.status is invalid")
    graph_nodes = graph.get("nodes")
    graph_relations = graph.get("relations")
    if not isinstance(graph_nodes, list):
        errors.append("panorama.graph.nodes must be a list")
        graph_nodes = []
    if not isinstance(graph_relations, list):
        errors.append("panorama.graph.relations must be a list")
        graph_relations = []
    graph_node_map: dict[str, dict[str, Any]] = {}
    graph_node_id_map: dict[str, list[dict[str, Any]]] = {}
    for index, node in enumerate(graph_nodes):
        label = f"panorama.graph.nodes[{index}]"
        if not isinstance(node, dict) or not nonempty_string(node.get("address")):
            errors.append(f"{label} needs a non-empty address")
            continue
        address = node["address"]
        if address in graph_node_map:
            errors.append(f"duplicate graph node address: {address}")
        graph_node_map[address] = node
        if roots and not address_has_legal_root(address, roots):
            errors.append(f"graph node has no legal root: {address}")
        if not isinstance(node.get("function"), str):
            errors.append(f"{label}.function must be a string")
        if node.get("evidence_status") not in EVIDENCE_STATUSES:
            errors.append(f"{label}.evidence_status is invalid")
        node_evidence = node.get("evidence_ids", [])
        if not isinstance(node_evidence, list) or not all(
            nonempty_string(item) for item in node_evidence
        ):
            errors.append(f"{label}.evidence_ids must be a string list")
            node_evidence = []
        elif set(node_evidence) - evidence_id_set:
            errors.append(f"{label}.evidence_ids references unknown evidence")
        if (
            graph.get("status") == "validated"
            and address != "F0"
            and node.get("validity") == "valid"
            and not node_evidence
        ):
            errors.append(
                f"{label} needs evidence_ids before the functional graph can be validated"
            )
        if node.get("validity") not in VALIDITY_STATUSES:
            errors.append(f"{label}.validity is invalid")
        if node.get("modal_status") not in {"[+]", "[◇]"}:
            errors.append(f"{label}.modal_status must be [+] or [◇]")
        if node.get("validity") != "valid" and node.get("modal_status") == "[+]":
            errors.append(f"{label} cannot remain realized while stale or invalid")
        if current_22:
            node_id = node.get("node_id")
            if not nonempty_string(node_id):
                errors.append(f"{label}.node_id must be non-empty in schema 2.2")
            else:
                graph_node_id_map.setdefault(node_id, []).append(node)
            if not is_strict_theory_address(address):
                errors.append(f"{label}.address is not a canonical F0 theory address")
            parent_address = node.get("parent_address")
            if address == "F0":
                if parent_address is not None:
                    errors.append("the F0 root node must use parent_address null")
            elif not nonempty_string(parent_address):
                errors.append(f"{label}.parent_address must be non-empty")
            payload_revision = node.get("payload_revision")
            if not isinstance(payload_revision, int) or payload_revision < 1:
                errors.append(f"{label}.payload_revision must be a positive integer")
            for issue in child_field_opening_issues(state, node):
                errors.append(f"{label}.field_opening_audit: {issue}")

    if current_22:
        if list(graph_node_map).count("F0") != 1:
            errors.append("schema 2.2 graph must contain exactly one F0 root node")
        for node_id, node_instances in graph_node_id_map.items():
            valid_instances = [
                item for item in node_instances if item.get("validity") == "valid"
            ]
            if len(valid_instances) > 1:
                errors.append(
                    f"node_id {node_id} has more than one valid current address"
                )
        for address, node in graph_node_map.items():
            if address == "F0":
                continue
            parent = node.get("parent_address")
            if parent not in graph_node_map:
                errors.append(f"graph node {address} has unknown parent_address {parent}")
                continue
            visited = {address}
            cursor = parent
            while cursor != "F0":
                if cursor in visited:
                    errors.append(f"recursive parent chain contains a cycle at {cursor}")
                    break
                visited.add(cursor)
                parent_node = graph_node_map.get(cursor)
                if parent_node is None:
                    break
                cursor = parent_node.get("parent_address")
                if not nonempty_string(cursor):
                    errors.append(
                        f"recursive parent chain for {address} does not reach F0"
                    )
                    break

    graph_relation_map: dict[str, dict[str, Any]] = {}
    for index, relation in enumerate(graph_relations):
        label = f"panorama.graph.relations[{index}]"
        if not isinstance(relation, dict) or not nonempty_string(relation.get("id")):
            errors.append(f"{label} needs a non-empty id")
            continue
        relation_id = relation["id"]
        if relation_id in graph_relation_map:
            errors.append(f"duplicate graph relation id: {relation_id}")
        graph_relation_map[relation_id] = relation
        source = relation.get("source")
        target = relation.get("target")
        if source not in graph_node_map or target not in graph_node_map:
            errors.append(f"graph relation {relation_id} must reference existing nodes")
        relation_type = relation.get("relation_type")
        if relation_type not in GENERAL_RELATION_TYPES:
            errors.append(f"graph relation {relation_id} has invalid relation_type")
        necessity = relation.get("necessity")
        if relation_type == "dependency":
            if necessity not in {"required", "conditional"}:
                errors.append(
                    f"dependency relation {relation_id} needs required or conditional necessity"
                )
        elif necessity is not None:
            errors.append(f"non-dependency relation {relation_id} must use null necessity")
        if relation.get("evidence_status") not in EVIDENCE_STATUSES:
            errors.append(f"graph relation {relation_id} has invalid evidence_status")
        relation_evidence = relation.get("evidence_ids", [])
        if not isinstance(relation_evidence, list) or not all(
            nonempty_string(item) for item in relation_evidence
        ):
            errors.append(f"graph relation {relation_id}.evidence_ids must be a string list")
            relation_evidence = []
        elif set(relation_evidence) - evidence_id_set:
            errors.append(
                f"graph relation {relation_id}.evidence_ids references unknown evidence"
            )
        if (
            graph.get("status") == "validated"
            and relation.get("validity") == "valid"
            and relation_type == "dependency"
            and necessity == "required"
            and not relation_evidence
        ):
            errors.append(
                f"required dependency {relation_id} needs evidence_ids before graph validation"
            )
        if relation.get("validity") not in VALIDITY_STATUSES:
            errors.append(f"graph relation {relation_id} has invalid validity")

    components = joint_scc_snapshot(state) if graph_node_map else []
    cyclic_nodes = {
        address for component in components for address in component["members"]
    }
    scc_blocked_descendants = {
        address
        for component in components
        for address in component.get("required_descendants", [])
    } if current else set()
    expected_order_nodes = {
        address
        for address, node in graph_node_map.items()
        if node.get("validity") == "valid"
        and address not in cyclic_nodes
        and address not in scc_blocked_descendants
    }
    expected_order_relations = {
        relation["id"]: relation
        for relation in required_dependency_relations(state)
        if relation.get("source") in expected_order_nodes
        and relation.get("target") in expected_order_nodes
    }

    order = panorama.get("order")
    if not isinstance(order, dict):
        errors.append("panorama.order must be an object")
        order = {}
    if order.get("status") not in ORDER_STATUSES:
        errors.append("panorama.order.status is invalid")
    if order.get("derived_from_map_version") != map_version:
        errors.append("panorama.order.derived_from_map_version is stale")
    order_nodes = order.get("nodes")
    order_relations = order.get("relations")
    incomparables = order.get("explicit_incomparables")
    if not isinstance(order_nodes, list):
        errors.append("panorama.order.nodes must be a list")
        order_nodes = []
    if not isinstance(order_relations, list):
        errors.append("panorama.order.relations must be a list")
        order_relations = []
    if not isinstance(incomparables, list):
        errors.append("panorama.order.explicit_incomparables must be a list")
        incomparables = []
    actual_order_nodes = {
        node.get("address")
        for node in order_nodes
        if isinstance(node, dict) and nonempty_string(node.get("address"))
    }
    if actual_order_nodes != expected_order_nodes:
        errors.append("panorama.order.nodes does not match the derived required projection")
    actual_order_relation_ids: set[str] = set()
    adjacency: dict[str, set[str]] = {address: set() for address in actual_order_nodes}
    indegree: dict[str, int] = {address: 0 for address in actual_order_nodes}
    for index, relation in enumerate(order_relations):
        label = f"panorama.order.relations[{index}]"
        if not isinstance(relation, dict) or not nonempty_string(relation.get("id")):
            errors.append(f"{label} needs a non-empty id")
            continue
        relation_id = relation["id"]
        if relation_id in actual_order_relation_ids:
            errors.append(f"duplicate order relation id: {relation_id}")
        actual_order_relation_ids.add(relation_id)
        source_relation = expected_order_relations.get(relation_id)
        if source_relation is None:
            errors.append(f"order relation {relation_id} is not a valid required graph edge")
            continue
        predecessor = relation.get("predecessor")
        successor = relation.get("successor")
        if predecessor != source_relation.get("source") or successor != source_relation.get("target"):
            errors.append(f"order relation {relation_id} endpoints drifted from G")
            continue
        if relation.get("necessity") != "required":
            errors.append(f"order relation {relation_id} must be required")
        if successor not in adjacency[predecessor]:
            adjacency[predecessor].add(successor)
            indegree[successor] += 1
    if actual_order_relation_ids != set(expected_order_relations):
        errors.append("panorama.order.relations does not match the derived required projection")
    remaining = dict(indegree)
    queue = [node for node, degree in remaining.items() if degree == 0]
    visited = 0
    while queue:
        node = queue.pop()
        visited += 1
        for successor in adjacency.get(node, set()):
            remaining[successor] -= 1
            if remaining[successor] == 0:
                queue.append(successor)
    if visited != len(actual_order_nodes):
        errors.append("joint-schema necessary order must be acyclic")
    for index, pair in enumerate(incomparables):
        if not isinstance(pair, list) or len(pair) != 2 or not all(
            nonempty_string(value) for value in pair
        ):
            errors.append(f"explicit_incomparables[{index}] must be an address pair")
            continue
        if pair[0] not in actual_order_nodes or pair[1] not in actual_order_nodes:
            errors.append(f"explicit incomparable pair references an unknown order node: {pair}")
        elif pair[1] in reachable(pair[0], adjacency) or pair[0] in reachable(pair[1], adjacency):
            errors.append(f"explicit incomparable pair is ordered: {pair}")

    scc_analysis = order.get("scc_analysis")
    if not isinstance(scc_analysis, dict) or scc_analysis.get("performed") is not True:
        errors.append("panorama.order.scc_analysis must be a performed analysis")
    else:
        if scc_analysis.get("components") != components:
            errors.append("panorama.order.scc_analysis.components is stale")
        expected_residual_ids = [component["residual_id"] for component in components]
        if scc_analysis.get("non_poset_residual_ids") != expected_residual_ids:
            errors.append("panorama.order.scc_analysis residual ids are stale")

    center = state.get("center")
    if not isinstance(center, dict):
        errors.append("center must be an object")
        center = {}
    if center.get("status") not in CENTER_STATUSES:
        errors.append("center.status is invalid")
    candidates = center.get("candidates")
    if not isinstance(candidates, list):
        errors.append("center.candidates must be a list")
        candidates = []
    candidate_map: dict[str, dict[str, Any]] = {}
    for index, candidate in enumerate(candidates):
        label = f"center.candidates[{index}]"
        if not isinstance(candidate, dict) or not nonempty_string(candidate.get("id")):
            errors.append(f"{label} needs a non-empty id")
            continue
        candidate_id = candidate["id"]
        if candidate_id in candidate_map:
            errors.append(f"duplicate center candidate id: {candidate_id}")
        candidate_map[candidate_id] = candidate
        members = string_list(candidate.get("members"), f"{label}.members")
        relation_ids = string_list(candidate.get("relation_ids"), f"{label}.relation_ids")
        closure_targets = string_list(
            candidate.get("closure_targets"), f"{label}.closure_targets"
        )
        candidate_validity = candidate.get("validity")
        if candidate_validity == "valid" and set(members) - actual_order_nodes:
            errors.append(f"{label}.members must lie in the necessary order")
        if set(closure_targets) - set(members):
            errors.append(f"{label}.closure_targets must be center members")
        for relation_id in relation_ids:
            relation = (
                expected_order_relations.get(relation_id)
                if candidate_validity == "valid"
                else graph_relation_map.get(relation_id)
            )
            if relation is None:
                errors.append(f"{label} relation {relation_id} is unknown")
                continue
            relation_source = relation.get("source", relation.get("predecessor"))
            relation_target = relation.get("target", relation.get("successor"))
            if candidate_validity == "valid" and relation_id not in expected_order_relations:
                errors.append(f"{label} relation {relation_id} is not a required order edge")
            elif relation_source not in members or relation_target not in members:
                errors.append(f"{label} relation {relation_id} leaves the candidate")
        if candidate.get("minimality_status") not in {
            "unvalidated",
            "validated",
            "invalid",
        }:
            errors.append(f"{label}.minimality_status is invalid")
        if candidate.get("minimality_status") == "validated" and (
            not members or not closure_targets
        ):
            errors.append(f"{label} cannot validate minimality without members and closure targets")
        if current:
            tests = candidate.get("tests")
            if not isinstance(tests, dict):
                errors.append(f"{label}.tests must be an object")
                tests = {}
            missing_tests = sorted(CENTER_TEST_NAMES - set(tests))
            if missing_tests:
                errors.append(
                    f"{label}.tests missing required tests: {', '.join(missing_tests)}"
                )
            all_tests_resolved = True
            for test_name in sorted(CENTER_TEST_NAMES):
                test = tests.get(test_name)
                test_label = f"{label}.tests.{test_name}"
                if not isinstance(test, dict):
                    all_tests_resolved = False
                    continue
                status = test.get("status")
                if status not in CENTER_TEST_STATUSES:
                    errors.append(f"{test_label}.status is invalid")
                    all_tests_resolved = False
                elif status not in {"pass", "not-applicable"}:
                    all_tests_resolved = False
                if not nonempty_string(test.get("rationale")):
                    errors.append(f"{test_label}.rationale must be non-empty")
                test_evidence = string_list(
                    test.get("evidence_ids"), f"{test_label}.evidence_ids"
                )
                unknown_test_evidence = set(test_evidence) - evidence_id_set
                if unknown_test_evidence:
                    errors.append(
                        f"{test_label}.evidence_ids references unknown evidence: "
                        + ", ".join(sorted(unknown_test_evidence))
                    )
                if status == "pass" and not test_evidence:
                    errors.append(f"{test_label} pass requires referenced evidence")
                    all_tests_resolved = False
            if candidate.get("minimality_status") == "validated" and not all_tests_resolved:
                errors.append(
                    f"{label}.minimality_status cannot be validated until every center test passes or is explicitly not-applicable"
                )
        if candidate.get("evidence_status") not in EVIDENCE_STATUSES:
            errors.append(f"{label}.evidence_status is invalid")
        if candidate_validity not in CENTER_VALIDITIES:
            errors.append(f"{label}.validity is invalid")
    selected_id = center.get("selected")
    if selected_id is not None:
        selected_candidate = candidate_map.get(selected_id)
        if selected_candidate is None:
            errors.append("center.selected must reference a candidate")
        elif selected_candidate.get("validity") != "valid":
            errors.append("center.selected cannot reference a stale or invalid candidate")
    if center.get("status") == "selected" and selected_id is None:
        errors.append("center.status selected requires center.selected")
    if not isinstance(center.get("selection_evidence"), list):
        errors.append("center.selection_evidence must be a list")

    residuals = panorama.get("residuals")
    if not isinstance(residuals, list):
        errors.append("panorama.residuals must be a list")
        residuals = []
    residual_ids: list[str] = []
    for index, residual in enumerate(residuals):
        errors.extend(
            validate_joint_residual_record(
                residual, f"panorama.residuals[{index}]", current=current
            )
        )
        if isinstance(residual, dict) and nonempty_string(residual.get("id")):
            residual_ids.append(residual["id"])
    if len(residual_ids) != len(set(residual_ids)):
        errors.append("panorama.residuals contains duplicate ids")
    if current:
        residual_history = panorama.get("residual_history")
        if not isinstance(residual_history, list):
            errors.append("panorama.residual_history must be a list")
            residual_history = []
        history_ids: list[str] = []
        for index, residual in enumerate(residual_history):
            errors.extend(
                validate_joint_residual_record(
                    residual,
                    f"panorama.residual_history[{index}]",
                    current=True,
                    archived=True,
                )
            )
            if isinstance(residual, dict) and nonempty_string(residual.get("id")):
                history_ids.append(residual["id"])
        if len(history_ids) != len(set(history_ids)):
            errors.append("panorama.residual_history contains duplicate ids")
        if set(history_ids) & set(residual_ids):
            errors.append("a residual id cannot be active and archived simultaneously")
    for component in components:
        if component["residual_id"] not in residual_ids:
            errors.append(f"SCC residual is missing: {component['residual_id']}")

    explored = string_list(panorama.get("explored"), "panorama.explored")
    expected_explored = {
        address
        for address, node in graph_node_map.items()
        if node.get("validity") == "valid" and node.get("modal_status") == "[+]"
    }
    if set(explored) != expected_explored:
        errors.append("panorama.explored does not match valid [+] graph nodes")

    frontiers = panorama.get("frontiers")
    if not isinstance(frontiers, dict):
        errors.append("panorama.frontiers must be an object")
        frontiers = {}
    frontier_addresses: dict[str, set[str]] = {name: set() for name in FRONTIER_TYPES}
    for frontier_type in sorted(FRONTIER_TYPES):
        items = frontiers.get(frontier_type)
        if not isinstance(items, list):
            errors.append(f"panorama.frontiers.{frontier_type} must be a list")
            items = []
        for index, item in enumerate(items):
            label = f"panorama.frontiers.{frontier_type}[{index}]"
            if not isinstance(item, dict) or not nonempty_string(item.get("address")):
                errors.append(f"{label} needs a non-empty address")
                continue
            address = item["address"]
            if address in frontier_addresses[frontier_type]:
                errors.append(f"duplicate {frontier_type} frontier address: {address}")
            frontier_addresses[frontier_type].add(address)
            node = graph_node_map.get(address)
            reopen_required = (
                frontier_type == "compressed"
                and item.get("exposure_status") == "reopen-required"
            )
            if node is None:
                errors.append(f"{label} must reference a graph node")
            elif node.get("validity") != "valid" and not reopen_required:
                errors.append(f"{label} must reference a valid graph node")
            elif node.get("modal_status") != "[◇]":
                errors.append(f"{label} graph node must have modal_status [◇]")
            elif (
                current
                and frontier_type == "action"
                and focus_display_address(state, address) is not None
                and node.get("field_opening_status") != "validated"
            ):
                errors.append(
                    f"{label} requires field_opening_status validated before action"
                )
            if item.get("modal_status") != "[◇]":
                errors.append(f"{label}.modal_status must be [◇]")
            if frontier_type in {"action", "expansion"}:
                audited = audit_path(
                    state,
                    item,
                    require_action_ready=current and frontier_type == "action",
                )
                for field_name in (
                    "display_address",
                    "focus_depth",
                    "required_predecessors",
                    "dependency_readiness",
                    "gate_status",
                    "gate_reasons",
                ):
                    if item.get(field_name) != audited.get(field_name):
                        errors.append(f"{label}.{field_name} is stale")
                if audited.get("gate_status") != "legal":
                    errors.append(f"{label} must pass the structural gate")
                if frontier_type == "action" and audited.get("dependency_readiness") != "ready":
                    errors.append(f"{label} must be dependency-ready")
                if not isinstance(item.get("task_scores"), dict):
                    errors.append(f"{label}.task_scores must be an object")
            else:
                if item.get("structural_status") not in {"required-ancestor", "optional"}:
                    errors.append(f"{label}.structural_status is invalid")
                if item.get("exposure_status") not in COMPRESSED_EXPOSURES:
                    errors.append(f"{label}.exposure_status is invalid")
                contract = item.get("contract")
                if not isinstance(contract, dict):
                    errors.append(f"{label}.contract must be an object")
                else:
                    for name in ("inputs", "outputs", "conditions"):
                        string_list(contract.get(name), f"{label}.contract.{name}")
                    if "uncertainty" not in contract:
                        errors.append(f"{label}.contract needs uncertainty")
                if not nonempty_string(item.get("reopen_address")):
                    errors.append(f"{label}.reopen_address must be non-empty")
            if current:
                linked_residuals = item.get("residual_ids", [])
                if not isinstance(linked_residuals, list) or not all(
                    nonempty_string(item_id) for item_id in linked_residuals
                ):
                    errors.append(f"{label}.residual_ids must be a string list")
                elif set(linked_residuals) - set(residual_ids):
                    errors.append(f"{label}.residual_ids references unknown active residuals")
    all_frontier_addresses = [
        address for addresses in frontier_addresses.values() for address in addresses
    ]
    if len(all_frontier_addresses) != len(set(all_frontier_addresses)):
        errors.append("an address cannot occur in multiple frontier classes")
    if set(all_frontier_addresses) & set(explored):
        errors.append("a frontier address cannot already be realized")

    global_expansion = panorama.get("global_expansion")
    if not isinstance(global_expansion, dict):
        errors.append("panorama.global_expansion must be an object")
    else:
        if not isinstance(global_expansion.get("resolution_level"), int) or global_expansion.get(
            "resolution_level", -1
        ) < 0:
            errors.append("global_expansion.resolution_level must be non-negative")
        if global_expansion.get("status") not in {"bounded", "active", "complete"}:
            errors.append("global_expansion.status is invalid")
        if not isinstance(global_expansion.get("last_uniform_expansion_version"), int):
            errors.append("global_expansion.last_uniform_expansion_version must be an integer")
        if not isinstance(global_expansion.get("last_deferred"), list):
            errors.append("global_expansion.last_deferred must be a list")

    modal_results = panorama.get("modal_results")
    if not isinstance(modal_results, list):
        errors.append("panorama.modal_results must be a list")
        modal_results = []
    modal_ids: list[str] = []
    for index, result in enumerate(modal_results):
        label = f"panorama.modal_results[{index}]"
        if not isinstance(result, dict) or not nonempty_string(result.get("id")):
            errors.append(f"{label}.id must be non-empty")
            continue
        modal_ids.append(result["id"])
        if not nonempty_string(result.get("address")):
            errors.append(f"{label}.address must be non-empty")
        if result.get("modal_status") not in {"[-]", "[∅]"}:
            errors.append(f"{label}.modal_status must be [-] or [∅]")
        if not nonempty_string(result.get("reason")):
            errors.append(f"{label}.reason must be non-empty")
        string_list(result.get("evidence_ids"), f"{label}.evidence_ids")
        if not isinstance(result.get("version"), int):
            errors.append(f"{label}.version must be an integer")
    if len(modal_ids) != len(set(modal_ids)):
        errors.append("panorama.modal_results contains duplicate ids")
    if not isinstance(panorama.get("external"), list):
        errors.append("panorama.external must be a list")

    focus = state.get("focus")
    if not isinstance(focus, dict):
        errors.append("focus must be an object")
        focus = {}
    active_paths = focus.get("active_paths")
    if not isinstance(active_paths, list):
        errors.append("focus.active_paths must be a list")
        active_paths = []
    nonlegal_active = False
    for index, item in enumerate(active_paths):
        label = f"focus.active_paths[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        expected_focus_modal = "[◇]" if current else "[+]"
        if item.get("modal_status") != expected_focus_modal:
            errors.append(f"{label}.modal_status must be {expected_focus_modal}")
        address = item.get("address")
        node = graph_node_map.get(address)
        if node is None or node.get("modal_status") != expected_focus_modal or node.get("validity") != "valid":
            errors.append(
                f"{label} must reference a valid "
                + ("potential" if current else "realized")
                + " graph node"
            )
        elif (
            current
            and focus_display_address(state, str(address)) is not None
            and node.get("field_opening_status") != "validated"
        ):
            errors.append(
                f"{label} requires field_opening_status validated before becoming active"
            )
        audited = audit_path(state, item)
        for field_name in (
            "display_address",
            "focus_depth",
            "required_predecessors",
            "dependency_readiness",
            "gate_status",
            "gate_reasons",
        ):
            if item.get(field_name) != audited.get(field_name):
                errors.append(f"{label}.{field_name} is stale")
        nonlegal_active = nonlegal_active or audited.get("gate_status") != "legal"
    if nonlegal_active and focus.get("status") == "active":
        errors.append("focus with a non-legal active path must require remodeling")

    execution = state.get("execution")
    if not isinstance(execution, dict):
        errors.append("execution must be an object")
        execution = {}
    if not isinstance(execution.get("snapshot_version"), int) or execution.get(
        "snapshot_version", -1
    ) < 0:
        errors.append("execution.snapshot_version must be non-negative")
    action_addresses = frontier_addresses["action"]
    execution_queue = string_list(execution.get("queue"), "execution.queue")
    if set(execution_queue) - action_addresses:
        errors.append("execution.queue addresses must occur in the Action frontier")
    if execution.get("active") is not None and execution.get("active") not in action_addresses:
        errors.append("execution.active must be null or an Action frontier address")
    for name in ("completed", "blocked"):
        records = execution.get(name)
        if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
            errors.append(f"execution.{name} must be a list of objects")
            records = []
        if current:
            for index, record in enumerate(records):
                label = f"execution.{name}[{index}]"
                if not nonempty_string(record.get("address")):
                    errors.append(f"{label}.address must be non-empty")
                if not isinstance(record.get("version"), int):
                    errors.append(f"{label}.version must be an integer")
                record_evidence = string_list(
                    record.get("evidence_ids"),
                    f"{label}.evidence_ids",
                    nonempty=True,
                )
                missing_record_evidence = set(record_evidence) - evidence_id_set
                if missing_record_evidence:
                    errors.append(
                        f"{label}.evidence_ids references unknown evidence: "
                        + ", ".join(sorted(missing_record_evidence))
                    )
    if execution.get("last_decision") is not None and execution.get(
        "last_decision"
    ) not in NEXT_DECISIONS:
        errors.append("execution.last_decision is invalid")
    if current_22:
        confirmation_status = field.get("f0_confirmation", {}).get("status")
        decision = execution.get("last_decision")
        if confirmation_status == "required" and decision not in {
            "FIELD_FORMATION_REQUIRED",
            "HUMAN_CALIBRATION_REQUIRED",
            "REMODEL_REQUIRED",
            "FIELD_ASCENSION_REQUIRED",
            "F0_CONFIRMATION_REQUIRED",
        }:
            errors.append(
                "an unconfirmed field requires a formation, calibration, remodel, ascent, or F0-confirmation decision"
            )
        if (
            confirmation_status in {"confirmed", "bypassed"}
            and field.get("phase") in {"forming", "stabilizing"}
            and center.get("selected") is None
            and decision in {"FOCUS_REQUIRED", "CONTINUE_EXECUTION", "F0_COMPLETE"}
        ):
            errors.append(
                "field formation without a selected center cannot claim Focus, execution, or F0 completion as the next decision"
            )
    if current:
        subgraph = execution.get("subgraph")
        if not isinstance(subgraph, dict):
            errors.append("execution.subgraph must be an object")
        else:
            for name in ("nodes", "relations", "join_nodes"):
                if not isinstance(subgraph.get(name), list):
                    errors.append(f"execution.subgraph.{name} must be a list")
        node_status = execution.get("node_status")
        if not isinstance(node_status, dict):
            errors.append("execution.node_status must be an object")
        elif any(value not in EXECUTION_NODE_STATUSES for value in node_status.values()):
            errors.append("execution.node_status contains an invalid status")
        ready = string_list(execution.get("ready"), "execution.ready")
        if set(ready) - action_addresses:
            errors.append("execution.ready addresses must occur in the Action frontier")

    evidence = state.get("evidence")
    if not isinstance(evidence, list):
        errors.append("evidence must be a list")
        evidence = []
    evidence_ids: list[str] = []
    for index, item in enumerate(evidence):
        label = f"evidence[{index}]"
        if not isinstance(item, dict) or not nonempty_string(item.get("id")):
            errors.append(f"{label}.id must be non-empty")
            continue
        evidence_ids.append(item["id"])
        if item.get("evidence_status") not in EVIDENCE_STATUSES:
            errors.append(f"{label}.evidence_status is invalid")
        if not nonempty_string(item.get("description")):
            errors.append(f"{label}.description must be non-empty")
    if len(evidence_ids) != len(set(evidence_ids)):
        errors.append("evidence contains duplicate ids")
    if current_22:
        archived_residual_ids = {
            item.get("id")
            for item in panorama.get("residual_history", [])
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        errors.extend(
            validate_address_dynamics_22(
                state,
                set(evidence_ids),
                set(residual_ids) | archived_residual_ids,
            )
        )

    drift = state.get("drift")
    if not isinstance(drift, dict):
        errors.append("drift must be an object")
        drift = {}
    baseline = drift.get("baseline")
    if not isinstance(baseline, dict):
        errors.append("drift.baseline must be an object")
    else:
        baseline_goal_key = "root_goal" if current else "ancestor_goal"
        if not nonempty_string(baseline.get(baseline_goal_key)):
            errors.append(f"drift.baseline.{baseline_goal_key} must be non-empty")
        string_list(
            baseline.get("immutable_constraints"),
            "drift.baseline.immutable_constraints",
        )
        if not isinstance(baseline.get("version"), int):
            errors.append("drift.baseline.version must be an integer")
    policy = drift.get("policy")
    if not isinstance(policy, dict):
        errors.append("drift.policy must be an object")
    else:
        for name in ("require_goal_identity", "require_immutable_constraint_retention"):
            if not isinstance(policy.get(name), bool):
                errors.append(f"drift.policy.{name} must be boolean")
        for name in ("min_address_retention", "max_dependency_churn"):
            value = policy.get(name)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                errors.append(f"drift.policy.{name} must be between 0 and 1")
    if isinstance(baseline, dict) and isinstance(policy, dict):
        if (
            policy.get("require_goal_identity") is True
            and baseline.get("root_goal" if current else "ancestor_goal")
            != field.get("root_goal" if current else "ancestor_goal")
        ):
            errors.append("current field goal has drifted from the protected baseline")
        baseline_constraints = set(baseline.get("immutable_constraints", []))
        current_constraints = set(field.get("immutable_constraints", []))
        if (
            policy.get("require_immutable_constraint_retention") is True
            and not baseline_constraints <= current_constraints
        ):
            errors.append("current field dropped a protected baseline constraint")
    audits = drift.get("audits")
    if not isinstance(audits, list):
        errors.append("drift.audits must be a list")
        audits = []
    audit_map: dict[str, dict[str, Any]] = {}
    metric_names = {
        "goal_identity",
        "immutable_constraint_retention",
        "selected_center_retention",
        "address_retention",
        "dependency_churn",
        "invalidated_realized_count",
        "stale_active_path_count",
    }
    for index, audit in enumerate(audits):
        label = f"drift.audits[{index}]"
        if not isinstance(audit, dict) or not nonempty_string(audit.get("id")):
            errors.append(f"{label}.id must be non-empty")
            continue
        if audit["id"] in audit_map:
            errors.append(f"duplicate drift audit id: {audit['id']}")
        audit_map[audit["id"]] = audit
        if audit.get("motion") not in JOINT_MOTION_TYPES:
            errors.append(f"{label}.motion is invalid")
        if not isinstance(audit.get("source_version"), int) or not isinstance(
            audit.get("target_version"), int
        ):
            errors.append(f"{label} versions must be integers")
        if not isinstance(audit.get("changes"), dict):
            errors.append(f"{label}.changes must be an object")
        metrics = audit.get("metrics")
        if not isinstance(metrics, dict) or set(metrics) != metric_names:
            errors.append(f"{label}.metrics must contain the complete metric set")
        else:
            for name in (
                "goal_identity",
                "immutable_constraint_retention",
                "address_retention",
                "dependency_churn",
            ):
                value = metrics.get(name)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                    errors.append(f"{label}.metrics.{name} must be between 0 and 1")
            selected_retention = metrics.get("selected_center_retention")
            if selected_retention is not None and selected_retention not in {0.0, 1.0, 0, 1}:
                errors.append(f"{label}.metrics.selected_center_retention is invalid")
            for name in ("invalidated_realized_count", "stale_active_path_count"):
                value = metrics.get(name)
                if not isinstance(value, int) or value < 0:
                    errors.append(f"{label}.metrics.{name} must be non-negative")
        if audit.get("status") not in DRIFT_STATUSES:
            errors.append(f"{label}.status is invalid")
        elif audit.get("status") == "fail":
            errors.append(f"{label}.status fail cannot exist in a committed state")
        if not isinstance(audit.get("reasons"), list):
            errors.append(f"{label}.reasons must be a list")
        if not nonempty_string(audit.get("timestamp")):
            errors.append(f"{label}.timestamp must be non-empty")

    history = state.get("history")
    if not isinstance(history, list):
        errors.append("history must be a list")
        history = []
    history_versions: list[int] = []
    referenced_audit_ids: list[str] = []
    for index, event in enumerate(history):
        label = f"history[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{label} must be an object")
            continue
        if not isinstance(event.get("version"), int):
            errors.append(f"{label}.version must be an integer")
        else:
            history_versions.append(event["version"])
        if event.get("type") not in EVENT_TYPES:
            errors.append(f"{label}.type is invalid")
        if event.get("type") in JOINT_MOTION_TYPES:
            audit_id = event.get("drift_audit_id")
            if nonempty_string(audit_id):
                referenced_audit_ids.append(audit_id)
            audit = audit_map.get(audit_id)
            if audit is None:
                errors.append(f"{label} must reference an existing drift audit")
            else:
                if audit.get("motion") != event.get("type"):
                    errors.append(f"{label} drift audit motion does not match")
                if audit.get("target_version") != event.get("version"):
                    errors.append(f"{label} drift audit target version does not match")
                if audit.get("source_version") != event.get("version") - 1:
                    errors.append(f"{label} drift audit source version does not match")
    if history_versions:
        if history_versions != sorted(set(history_versions)):
            errors.append("history versions must be strictly increasing")
        if history_versions[-1] != state.get("version"):
            errors.append("state.version must equal the latest history version")
    if len(referenced_audit_ids) != len(set(referenced_audit_ids)):
        errors.append("a drift audit cannot be bound to more than one history event")
    if set(referenced_audit_ids) != set(audit_map):
        errors.append("every drift audit must be bound to exactly one joint-motion event")
    return errors


def validate_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_KEYS - set(state))
    if missing:
        errors.append(f"missing top-level keys: {', '.join(missing)}")
    version_name = schema_version(state)
    if version_name not in SUPPORTED_SCHEMAS:
        errors.append(
            f"unsupported schema_version {version_name!r}; "
            f"choose from {', '.join(sorted(SUPPORTED_SCHEMAS))}"
        )
    if not isinstance(state.get("version"), int) or state.get("version", -1) < 0:
        errors.append("version must be a non-negative integer")
    field = state.get("field")
    if not isinstance(field, dict):
        errors.append("field must be an object")
    else:
        goal_key = "root_goal" if version_name in FIELD_FORM_SCHEMAS else "ancestor_goal"
        if not str(field.get(goal_key, "")).strip():
            errors.append(f"field.{goal_key} must be non-empty")
    center = state.get("center")
    if not isinstance(center, dict):
        errors.append("center must be an object")
    else:
        spine = center.get("spine", [])
        if not isinstance(spine, list):
            errors.append("center.spine must be a list")
        else:
            ids = [item.get("id") for item in spine if isinstance(item, dict)]
            if len(ids) != len(set(ids)):
                errors.append("center.spine contains duplicate ids")
    for key in ("evidence", "history"):
        if key in state and not isinstance(state[key], list):
            errors.append(f"{key} must be a list")

    if version_name in JOINT_SCHEMAS:
        errors.extend(validate_joint_state(state))
        return errors

    if version_name not in ORDERED_SCHEMAS:
        return errors

    if not isinstance(field, dict) or not isinstance(center, dict):
        return errors

    roots = field.get("legal_roots")
    if not isinstance(roots, list) or not roots or not all(
        nonempty_string(root) for root in roots
    ):
        errors.append("field.legal_roots must be a non-empty string list")
        roots = []
    elif field.get("id") not in roots:
        errors.append("field.id must be included in field.legal_roots")
    if not isinstance(field.get("tolerance"), dict):
        errors.append("field.tolerance must be an object")

    panorama = state.get("panorama")
    if not isinstance(panorama, dict):
        errors.append("panorama must be an object")
        return errors
    order = panorama.get("order")
    if not isinstance(order, dict):
        errors.append("panorama.order must be an object")
        return errors
    if order.get("status") not in ORDER_STATUSES:
        errors.append(
            "panorama.order.status must be unvalidated, tentative, validated, or invalid"
        )

    nodes = order.get("nodes")
    relations = order.get("relations")
    incomparables = order.get("explicit_incomparables")
    if not isinstance(nodes, list):
        errors.append("panorama.order.nodes must be a list")
        nodes = []
    if not isinstance(relations, list):
        errors.append("panorama.order.relations must be a list")
        relations = []
    if not isinstance(incomparables, list):
        errors.append("panorama.order.explicit_incomparables must be a list")
        incomparables = []

    node_addresses: list[str] = []
    for index, node in enumerate(nodes):
        if not isinstance(node, dict) or not nonempty_string(node.get("address")):
            errors.append(f"panorama.order.nodes[{index}] needs a non-empty address")
            continue
        address = node["address"]
        node_addresses.append(address)
        if roots and not address_has_legal_root(address, roots):
            errors.append(f"order node has no legal root: {address}")
        if version_name == SCHEMA_AUDITED and node.get("modal_status") not in {
            "[+]",
            "[◇]",
        }:
            errors.append(
                f"schema 1.3 order node {address!r} needs modal_status [+] or [◇]"
            )
    if len(node_addresses) != len(set(node_addresses)):
        errors.append("panorama.order.nodes contains duplicate addresses")
    node_set = set(node_addresses)
    if order.get("status") == "validated" and field.get("id") not in node_set:
        errors.append("a validated dependency order must contain field.id as its root node")

    relation_ids: list[str] = []
    adjacency: dict[str, set[str]] = {address: set() for address in node_set}
    indegree: dict[str, int] = {address: 0 for address in node_set}
    relation_map: dict[str, dict[str, Any]] = {}
    for index, relation in enumerate(relations):
        if not isinstance(relation, dict):
            errors.append(f"panorama.order.relations[{index}] must be an object")
            continue
        relation_id = relation.get("id")
        predecessor = relation.get("predecessor")
        successor = relation.get("successor")
        if not nonempty_string(relation_id):
            errors.append(f"panorama.order.relations[{index}] needs a non-empty id")
            continue
        relation_ids.append(relation_id)
        relation_map[relation_id] = relation
        if predecessor not in node_set or successor not in node_set:
            errors.append(
                f"order relation {relation_id} must reference existing node addresses"
            )
            continue
        if predecessor == successor:
            errors.append(f"order relation {relation_id} cannot be a self-loop")
            continue
        if relation.get("necessity") not in {"required", "conditional"}:
            errors.append(
                f"order relation {relation_id} necessity must be required or conditional"
            )
        if relation.get("evidence_status") not in EVIDENCE_STATUSES:
            errors.append(
                f"order relation {relation_id} has invalid evidence_status"
            )
        if successor not in adjacency[predecessor]:
            adjacency[predecessor].add(successor)
            indegree[successor] += 1
    if len(relation_ids) != len(set(relation_ids)):
        errors.append("panorama.order.relations contains duplicate ids")

    remaining_indegree = dict(indegree)
    queue = [address for address, degree in remaining_indegree.items() if degree == 0]
    visited_count = 0
    while queue:
        current = queue.pop()
        visited_count += 1
        for successor in adjacency.get(current, set()):
            remaining_indegree[successor] -= 1
            if remaining_indegree[successor] == 0:
                queue.append(successor)
    if visited_count != len(node_set):
        errors.append("panorama.order.relations must form a DAG within one version")

    for index, pair in enumerate(incomparables):
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or not all(nonempty_string(value) for value in pair)
        ):
            errors.append(
                f"panorama.order.explicit_incomparables[{index}] must be a two-address list"
            )
            continue
        left, right = pair
        if left not in node_set or right not in node_set:
            errors.append(
                f"explicit incomparable pair {left!r}, {right!r} references an unknown node"
            )
        elif right in reachable(left, adjacency) or left in reachable(right, adjacency):
            errors.append(
                f"explicit incomparable pair {left!r}, {right!r} is ordered by the DAG"
            )

    members = center.get("members")
    center_relation_ids = center.get("relation_ids")
    if not isinstance(members, list) or not all(
        nonempty_string(member) for member in members
    ):
        errors.append("center.members must be a string list")
        members = []
    if len(members) != len(set(members)):
        errors.append("center.members contains duplicate addresses")
    unknown_members = sorted(set(members) - node_set)
    if unknown_members:
        errors.append("center members absent from order: " + ", ".join(unknown_members))
    if not isinstance(center_relation_ids, list) or not all(
        nonempty_string(relation_id) for relation_id in center_relation_ids
    ):
        errors.append("center.relation_ids must be a string list")
        center_relation_ids = []
    if len(center_relation_ids) != len(set(center_relation_ids)):
        errors.append("center.relation_ids contains duplicates")
    for relation_id in center_relation_ids:
        relation = relation_map.get(relation_id)
        if relation is None:
            errors.append(f"center relation absent from order: {relation_id}")
        elif (
            relation.get("predecessor") not in members
            or relation.get("successor") not in members
        ):
            errors.append(
                f"center relation {relation_id} leaves the center member sub-poset"
            )
    if center.get("minimality_status") not in {
        "unvalidated",
        "validated",
        "invalid",
    }:
        errors.append(
            "center.minimality_status must be unvalidated, validated, or invalid"
        )

    compressed = panorama.get("compressed")
    if not isinstance(compressed, list):
        errors.append("panorama.compressed must be a list")
        compressed = []
    compressed_addresses: list[str] = []
    for index, interface in enumerate(compressed):
        if not isinstance(interface, dict):
            errors.append(f"panorama.compressed[{index}] must be an object")
            continue
        address = interface.get("address")
        if not nonempty_string(address):
            errors.append(f"panorama.compressed[{index}] needs a non-empty address")
        else:
            compressed_addresses.append(address)
            if address not in node_set:
                errors.append(f"compressed address absent from order: {address}")
        if interface.get("structural_status") not in {
            "required-ancestor",
            "optional",
        }:
            errors.append(
                f"compressed interface {address!r} has invalid structural_status"
            )
        if version_name in FOCUS_SCHEMAS and interface.get(
            "exposure_status"
        ) not in {"compressed", "locked"}:
            errors.append(
                f"compressed interface {address!r} needs compressed or locked exposure_status"
            )
        if not isinstance(interface.get("contract"), dict):
            errors.append(f"compressed interface {address!r} needs a contract object")
        if not nonempty_string(interface.get("reopen_address")):
            errors.append(
                f"compressed interface {address!r} needs a reopen_address"
            )
        elif roots and not address_has_legal_root(interface.get("reopen_address"), roots):
            errors.append(
                f"compressed interface {address!r} has an illegal reopen_address"
            )
    if len(compressed_addresses) != len(set(compressed_addresses)):
        errors.append("panorama.compressed contains duplicate addresses")

    focus = state.get("focus")
    if not isinstance(focus, dict):
        errors.append("focus must be an object")
        active_paths: list[Any] = []
    else:
        active_paths = focus.get("active_paths", [])
        if not isinstance(active_paths, list):
            errors.append("focus.active_paths must be a list")
            active_paths = []

    nonlegal_active = False
    for index, item in enumerate(active_paths):
        if not isinstance(item, dict):
            errors.append(
                f"focus.active_paths[{index}] must be a schema-1.1+ path object"
            )
            continue
        if version_name == SCHEMA_AUDITED and item.get("modal_status") != "[+]":
            errors.append(
                f"focus.active_paths[{index}].modal_status must be [+] in schema 1.3"
            )
        audited = audit_path(state, item)
        if item.get("gate_status") != audited["gate_status"]:
            errors.append(
                f"focus.active_paths[{index}].gate_status does not match helper audit"
            )
        if version_name in FOCUS_SCHEMAS:
            if item.get("display_address") != audited.get("display_address"):
                errors.append(
                    f"focus.active_paths[{index}].display_address is stale"
                )
            if item.get("focus_depth") != audited.get("focus_depth"):
                errors.append(f"focus.active_paths[{index}].focus_depth is stale")
            display = audited.get("display_address")
            center_root = (
                f"{field.get('id')}:{display[0]}" if nonempty_string(display) else None
            )
            if center_root not in set(members):
                errors.append(
                    f"focus.active_paths[{index}] root letter is absent from the center"
                )
        stored_predecessors = item.get("required_predecessors")
        if not isinstance(stored_predecessors, list) or not all(
            nonempty_string(value) for value in stored_predecessors
        ):
            errors.append(
                f"focus.active_paths[{index}].required_predecessors must be a string list"
            )
            stored_predecessors = []
        if set(stored_predecessors) != set(audited["required_predecessors"]):
            errors.append(
                f"focus.active_paths[{index}].required_predecessors is stale"
            )
        if item.get("dependency_readiness") != audited["dependency_readiness"]:
            errors.append(
                f"focus.active_paths[{index}].dependency_readiness is stale"
            )
        if item.get("structural_necessity") not in STRUCTURAL_NECESSITIES:
            errors.append(
                f"focus.active_paths[{index}] has invalid structural_necessity"
            )
        if not isinstance(item.get("focus_depth"), int) or item.get(
            "focus_depth", -1
        ) < 0:
            errors.append(
                f"focus.active_paths[{index}].focus_depth must be non-negative"
            )
        if not isinstance(item.get("gate_reasons"), list):
            errors.append(f"focus.active_paths[{index}].gate_reasons must be a list")
        nonlegal_active = nonlegal_active or audited["gate_status"] != "legal"
    if nonlegal_active and isinstance(focus, dict) and focus.get("status") == "active":
        errors.append("focus with a non-legal active path must require remodeling")

    frontier = panorama.get("frontier")
    if not isinstance(frontier, list):
        errors.append("panorama.frontier must be a list")
        frontier = []
    for index, item in enumerate(frontier):
        if not isinstance(item, dict):
            errors.append(f"panorama.frontier[{index}] must be an object")
            continue
        if version_name == SCHEMA_AUDITED and item.get("modal_status") != "[◇]":
            errors.append(
                f"panorama.frontier[{index}].modal_status must be [◇] in schema 1.3"
            )
        audited = audit_path(state, item)
        if item.get("gate_status") != audited["gate_status"]:
            errors.append(
                f"panorama.frontier[{index}].gate_status does not match helper audit"
            )
        if version_name in FOCUS_SCHEMAS:
            if item.get("display_address") != audited.get("display_address"):
                errors.append(f"panorama.frontier[{index}].display_address is stale")
            if item.get("focus_depth") != audited.get("focus_depth"):
                errors.append(f"panorama.frontier[{index}].focus_depth is stale")
        stored_predecessors = item.get("required_predecessors")
        if not isinstance(stored_predecessors, list) or not all(
            nonempty_string(value) for value in stored_predecessors
        ):
            errors.append(
                f"panorama.frontier[{index}].required_predecessors must be a string list"
            )
            stored_predecessors = []
        if set(stored_predecessors) != set(audited["required_predecessors"]):
            errors.append(f"panorama.frontier[{index}].required_predecessors is stale")
        if item.get("dependency_readiness") != audited["dependency_readiness"]:
            errors.append(f"panorama.frontier[{index}].dependency_readiness is stale")
        if item.get("structural_necessity") not in STRUCTURAL_NECESSITIES:
            errors.append(
                f"panorama.frontier[{index}] has invalid structural_necessity"
            )
        if not isinstance(item.get("focus_depth"), int) or item.get(
            "focus_depth", -1
        ) < 0:
            errors.append(
                f"panorama.frontier[{index}].focus_depth must be non-negative"
            )
        task_scores = item.get("task_scores")
        if not isinstance(task_scores, dict):
            errors.append(f"panorama.frontier[{index}].task_scores must be an object")
        elif task_scores.get("priority") is not None and audited["gate_status"] != "legal":
            errors.append(
                f"panorama.frontier[{index}] cannot have priority before a legal gate"
            )

    if version_name in FOCUS_SCHEMAS:
        map_version = panorama.get("map_version")
        if not isinstance(map_version, int) or map_version < 0:
            errors.append("panorama.map_version must be a non-negative integer")

        global_expansion = panorama.get("global_expansion")
        if not isinstance(global_expansion, dict):
            errors.append("panorama.global_expansion must be an object")
        else:
            resolution = global_expansion.get("resolution_level")
            if not isinstance(resolution, int) or resolution < 0:
                errors.append(
                    "panorama.global_expansion.resolution_level must be non-negative"
                )
            if global_expansion.get("status") not in {"bounded", "active", "complete"}:
                errors.append(
                    "panorama.global_expansion.status must be bounded, active, or complete"
                )
            last_uniform = global_expansion.get("last_uniform_expansion_version")
            if not isinstance(last_uniform, int) or last_uniform < 0:
                errors.append(
                    "panorama.global_expansion.last_uniform_expansion_version must be non-negative"
                )

        explored = panorama.get("explored")
        if not isinstance(explored, list) or not all(
            nonempty_string(address) for address in explored
        ):
            errors.append("panorama.explored must be a string list in schema 1.2+")
            explored = []
        external = panorama.get("external")
        if not isinstance(external, list):
            errors.append("panorama.external must be a list")
        if version_name == SCHEMA_AUDITED:
            node_map = {
                item.get("address"): item
                for item in nodes
                if isinstance(item, dict) and nonempty_string(item.get("address"))
            }
            for address in explored:
                node = node_map.get(address)
                if node is None:
                    errors.append(
                        f"schema 1.3 explored address absent from order: {address}"
                    )
                elif node.get("modal_status") != "[+]":
                    errors.append(
                        f"schema 1.3 explored address {address} must have modal_status [+]"
                    )
            frontier_addresses = {
                item.get("address")
                for item in frontier
                if isinstance(item, dict) and nonempty_string(item.get("address"))
            }
            for address in frontier_addresses:
                node = node_map.get(address)
                if node is None:
                    errors.append(
                        f"schema 1.3 frontier address absent from order: {address}"
                    )
                elif node.get("modal_status") != "[◇]":
                    errors.append(
                        f"schema 1.3 frontier address {address} must have order-node modal_status [◇]"
                    )
                if address in set(explored):
                    errors.append(
                        f"schema 1.3 frontier address {address} cannot already be realized in panorama.explored"
                    )
            for address, node in node_map.items():
                if node.get("modal_status") == "[+]" and address not in set(explored):
                    errors.append(
                        f"schema 1.3 realized order node {address} must be present in panorama.explored"
                    )
                elif node.get("modal_status") == "[◇]" and address not in frontier_addresses:
                    errors.append(
                        f"schema 1.3 potential order node {address} must be retained in frontier"
                    )

        penetration = focus.get("penetration") if isinstance(focus, dict) else None
        if not isinstance(penetration, dict):
            errors.append("focus.penetration must be an object in schema 1.2+")
        else:
            source_version = penetration.get("source_panorama_version")
            written_version = penetration.get("written_panorama_version")
            new_addresses = penetration.get("new_addresses")
            locked_addresses = penetration.get("locked_interface_addresses")
            if not isinstance(source_version, int) or source_version < 0:
                errors.append(
                    "focus.penetration.source_panorama_version must be non-negative"
                )
            if not isinstance(written_version, int) or written_version < 0:
                errors.append(
                    "focus.penetration.written_panorama_version must be non-negative"
                )
            elif isinstance(map_version, int) and written_version > map_version:
                errors.append(
                    "focus.penetration.written_panorama_version cannot exceed panorama.map_version"
                )
            if (
                isinstance(source_version, int)
                and isinstance(written_version, int)
                and source_version > written_version
            ):
                errors.append("Focus write-back cannot reduce panorama version")
            if not isinstance(new_addresses, list) or not all(
                nonempty_string(address) for address in new_addresses
            ):
                errors.append("focus.penetration.new_addresses must be a string list")
                new_addresses = []
            missing_delta_nodes = sorted(set(new_addresses) - node_set)
            if missing_delta_nodes:
                errors.append(
                    "Focus delta addresses absent from panorama order: "
                    + ", ".join(missing_delta_nodes)
                )
            missing_explored = sorted(set(new_addresses) - set(explored))
            if missing_explored:
                errors.append(
                    "Focus delta addresses absent from panorama.explored: "
                    + ", ".join(missing_explored)
                )
            if (
                new_addresses
                and isinstance(source_version, int)
                and isinstance(written_version, int)
                and written_version <= source_version
            ):
                errors.append("a non-empty Focus delta must advance panorama version")
            if not isinstance(locked_addresses, list) or not all(
                nonempty_string(address) for address in locked_addresses
            ):
                errors.append(
                    "focus.penetration.locked_interface_addresses must be a string list"
                )
                locked_addresses = []
            unknown_locked = sorted(set(locked_addresses) - set(compressed_addresses))
            if unknown_locked:
                errors.append(
                    "locked Focus interfaces absent from panorama.compressed: "
                    + ", ".join(unknown_locked)
                )
            compressed_map = compressed_indexes(state)
            for address in locked_addresses:
                if compressed_map.get(address, {}).get("exposure_status") != "locked":
                    errors.append(
                        f"Focus locked interface {address} is not marked locked"
                    )

        residuals = panorama.get("residuals")
        if not isinstance(residuals, list):
            errors.append("panorama.residuals must be a list")
        else:
            residual_ids: list[str] = []
            for index, residual in enumerate(residuals):
                if not isinstance(residual, dict):
                    errors.append(f"panorama.residuals[{index}] must be an object")
                    continue
                if residual.get("classification") != "true-residual":
                    errors.append(
                        f"panorama.residuals[{index}] must be classified true-residual"
                    )
                if not nonempty_string(residual.get("effect_on_f0")):
                    errors.append(
                        f"panorama.residuals[{index}].effect_on_f0 must be non-empty"
                    )
                if not nonempty_string(residual.get("representation_failure")):
                    errors.append(
                        f"panorama.residuals[{index}].representation_failure must be non-empty"
                    )
                if version_name == SCHEMA_AUDITED:
                    residual_id = residual.get("id")
                    if not nonempty_string(residual_id):
                        errors.append(
                            f"panorama.residuals[{index}].id must be non-empty"
                        )
                    else:
                        residual_ids.append(residual_id)
                    if residual.get("residual_type") not in RESIDUAL_TYPES:
                        errors.append(
                            f"panorama.residuals[{index}].residual_type is invalid"
                        )
                    produced_by = residual.get("produced_by")
                    if not isinstance(produced_by, dict):
                        errors.append(
                            f"panorama.residuals[{index}].produced_by must be an object"
                        )
                    else:
                        if produced_by.get("motion") not in RESIDUAL_AUDIT_EVENT_TYPES:
                            errors.append(
                                f"panorama.residuals[{index}].produced_by.motion is invalid"
                            )
                        if produced_by.get("address") is not None and not nonempty_string(
                            produced_by.get("address")
                        ):
                            errors.append(
                                f"panorama.residuals[{index}].produced_by.address must be null or non-empty"
                            )
                    if residual.get("modal_status") not in RESIDUAL_MODAL_STATUSES:
                        errors.append(
                            f"panorama.residuals[{index}].modal_status must be [◇], [-], or [∅]"
                        )
                    if residual.get("possible_destination") not in RESIDUAL_DESTINATIONS:
                        errors.append(
                            f"panorama.residuals[{index}].possible_destination is invalid"
                        )
                    scheduling = residual.get("changes_focus_or_execution")
                    if not isinstance(scheduling, dict) or not isinstance(
                        scheduling.get("changes"), bool
                    ):
                        errors.append(
                            f"panorama.residuals[{index}].changes_focus_or_execution needs a boolean changes field"
                        )
                    elif scheduling.get("changes") and not nonempty_string(
                        scheduling.get("reason")
                    ):
                        errors.append(
                            f"panorama.residuals[{index}].changes_focus_or_execution.reason is required when changes is true"
                        )
            if version_name == SCHEMA_AUDITED and len(residual_ids) != len(
                set(residual_ids)
            ):
                errors.append("panorama.residuals contains duplicate ids")

    execution = state.get("execution")
    if isinstance(execution, dict):
        decision = execution.get("last_decision")
        if version_name == SCHEMA_AUDITED and decision is not None and decision not in NEXT_DECISIONS:
            errors.append("execution.last_decision is invalid for schema 1.3")

    if version_name == SCHEMA_AUDITED:
        history = state.get("history", [])
        for index, event in enumerate(history):
            if not isinstance(event, dict):
                errors.append(f"history[{index}] must be an object")
                continue
            event_type = event.get("type")
            if event_type in RESIDUAL_AUDIT_EVENT_TYPES:
                for error in validate_residual_audit(
                    str(event_type), event.get("residual_audit")
                ):
                    errors.append(f"history[{index}]: {error}")
    return errors


def append_event(
    state: dict[str, Any],
    event_type: str,
    note: str,
    address: str | None = None,
    residual_audit: dict[str, Any] | None = None,
) -> None:
    state["version"] += 1
    event = {
        "version": state["version"],
        "type": event_type,
        "address": address,
        "note": note,
        "timestamp": now_iso(),
    }
    if residual_audit is not None:
        event["residual_audit"] = residual_audit
    state["history"].append(event)


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if path.exists():
        raise ValueError(f"refusing to overwrite existing state: {path}")
    state: dict[str, Any] = {
        "schema_version": SCHEMA_CURRENT,
        "version": 0,
        "field": {
            "id": "F0",
            "name": args.name,
            "root_goal": args.goal,
            "boundary": {"included": [], "excluded": []},
            "success_criteria": args.success or [],
            "immutable_constraints": [],
            "allowed_changes": [],
            "legal_roots": ["F0"],
            "tolerance": {"criterion": None, "threshold": None},
            "status": "field_form",
            "phase": "forming",
            "contract_status": "provisional",
            "f0_confirmation": {
                "status": "required",
                "confirmed_by": None,
                "confirmed_at_runtime_version": None,
            },
            "ambiguities": [],
            "human_calibration": {"status": "not-required", "items": []},
        },
        "center": {
            "status": "tentative",
            "candidates": [],
            "selected": None,
            "selection_reason": None,
            "selection_evidence": [],
        },
        "focus": {
            "query": None,
            "address": None,
            "rationale": None,
            "source": None,
            "active_paths": [],
            "penetration": {
                "source_panorama_version": 0,
                "written_panorama_version": 0,
                "new_addresses": [],
                "locked_interface_addresses": [],
            },
            "status": "unfocused",
        },
        "panorama": {
            "map_version": 0,
            "global_expansion": {
                "resolution_level": 0,
                "status": "bounded",
                "last_uniform_expansion_version": 0,
                "last_deferred": [],
            },
            "graph": {
                "status": "tentative",
                "nodes": [
                    {
                        "node_id": "N-F0",
                        "address": "F0",
                        "parent_address": None,
                        "payload_revision": 1,
                        "function": "task root",
                        "evidence_status": "explicit",
                        "validity": "valid",
                        "modal_status": "[+]",
                    }
                ],
                "relations": [],
            },
            "explored": ["F0"],
            "frontiers": {"action": [], "expansion": [], "compressed": []},
            "external": [],
            "residuals": [],
            "residual_history": [],
            "modal_results": [],
            "order": {
                "status": "tentative",
                "derived_from_map_version": 0,
                "nodes": [
                    {
                        "address": "F0",
                        "function": "task root",
                        "evidence_status": "explicit",
                        "modal_status": "[+]",
                        "validity": "valid",
                    }
                ],
                "relations": [],
                "explicit_incomparables": [],
                "scc_analysis": {
                    "performed": True,
                    "components": [],
                    "non_poset_residual_ids": [],
                },
            },
        },
        "execution": {
            "snapshot_version": 0,
            "queue": [],
            "active": None,
            "completed": [],
            "blocked": [],
            "last_decision": "FIELD_FORMATION_REQUIRED",
            "subgraph": {"nodes": [], "relations": [], "join_nodes": []},
            "node_status": {},
            "ready": [],
        },
        "evidence": [],
        "drift": {
            "baseline": {
                "root_goal": args.goal,
                "immutable_constraints": [],
                "version": 0,
            },
            "policy": {
                "require_goal_identity": True,
                "require_immutable_constraint_retention": True,
                "min_address_retention": 0.8,
                "max_dependency_churn": 0.5,
            },
            "audits": [],
        },
        "address_dynamics": {
            "root_address": "F0",
            "inbox": [],
            "motions": [],
            "lineage": [],
            "field_versions": {
                "active_branch_id": "main",
                "branches": [
                    {
                        "id": "main",
                        "parent_branch_id": None,
                        "status": "active",
                    }
                ],
                "heads": [
                    {
                        "branch_id": "main",
                        "field_address": "F0",
                        "version_id": None,
                        "working_closure": "open",
                        "destabilized_by_motion_ids": [],
                    }
                ],
                "records": [],
            },
        },
        "history": [
            {
                "version": 0,
                "type": "AUDIT",
                "address": "F0",
                "note": "state initialized",
                "timestamp": now_iso(),
            }
        ],
    }
    errors = validate_state(state)
    if errors:
        raise ValueError("cannot initialize invalid schema-2.2 state: " + "; ".join(errors))
    write_state(path, state)
    print(path)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    state = read_state(Path(args.path))
    errors = validate_state(state)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("valid")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    state = read_state(Path(args.path))
    errors = validate_state(state)
    if errors:
        raise ValueError("; ".join(errors))
    field = state["field"]
    focus = state["focus"]
    panorama = state["panorama"]
    execution = state["execution"]
    print(f"field: {field.get('id')} {field.get('name')}")
    print(f"schema: {schema_version(state)}")
    version_label = "runtime version" if is_current_schema(state) else "version"
    print(f"{version_label}: {state['version']}")
    goal_key = "root_goal" if has_field_formation_schema(state) else "ancestor_goal"
    print(f"root goal: {field.get(goal_key)}")
    if schema_version(state) == SCHEMA_JOINT:
        print(
            "F0 confirmation: "
            f"{field.get('f0_confirmation', {}).get('status')}"
        )
        closure_issues = f0_provisional_closure_issues(state)
        print(
            "F0 provisional closure: "
            + ("ready" if not closure_issues else f"open ({closure_issues[0]})")
        )
        print(f"panorama map version: {panorama.get('map_version')}")
    if schema_version(state) in JOINT_SCHEMAS:
        graph = panorama.get("graph", {})
        order = panorama.get("order", {})
        center = state.get("center", {})
        frontiers = panorama.get("frontiers", {})
        print(
            "graph G: "
            f"{graph.get('status')} "
            f"({len(graph.get('nodes', []))} nodes, "
            f"{len(graph.get('relations', []))} relations)"
        )
        print(
            "necessary order: "
            f"{order.get('status')} "
            f"({len(order.get('nodes', []))} nodes, "
            f"{len(order.get('relations', []))} relations, "
            f"{len(order.get('scc_analysis', {}).get('components', []))} non-poset SCCs)"
        )
        print(
            "center candidates: "
            f"{len(center.get('candidates', []))}, "
            f"selected={center.get('selected')}"
        )
        print(
            "frontiers: "
            f"Action={len(frontiers.get('action', []))}, "
            f"Expansion={len(frontiers.get('expansion', []))}, "
            f"Compressed={len(frontiers.get('compressed', []))}"
        )
        print(f"focus: {focus.get('query') or '(unfocused)'}")
        print(
            "state S: "
            f"M={len(panorama.get('explored', []))}, "
            f"R={len(panorama.get('residuals', []))}, "
            f"Frontier={sum(len(frontiers.get(name, [])) for name in FRONTIER_TYPES)}"
        )
        audits = state.get("drift", {}).get("audits", [])
        if audits:
            latest = audits[-1]
            print(
                "last drift audit: "
                f"{latest.get('status')} "
                f"dependency_churn={latest.get('metrics', {}).get('dependency_churn')}"
            )
        else:
            print("last drift audit: (none)")
        print(f"execution queue: {len(execution.get('queue', []))}")
        if has_field_formation_schema(state):
            print(
                "field formation: "
                f"phase={field.get('phase')}, contract={field.get('contract_status')}, "
                f"calibration={field.get('human_calibration', {}).get('status')}"
            )
            print(
                "execution wavefront: "
                f"D={len(execution.get('subgraph', {}).get('nodes', []))}, "
                f"Ready={len(execution.get('ready', []))}, "
                f"absorbed_R={len(panorama.get('residual_history', []))}"
            )
        if is_current_schema(state):
            dynamics = state.get("address_dynamics", {})
            versions = dynamics.get("field_versions", {})
            pending_updates = sum(
                1
                for item in dynamics.get("inbox", [])
                if isinstance(item, dict) and item.get("status") != "resolved"
            )
            applied_motions = sum(
                1
                for item in dynamics.get("motions", [])
                if isinstance(item, dict) and item.get("status") == "applied"
            )
            print(
                "address dynamics: "
                f"pending_updates={pending_updates}, "
                f"motions={len(dynamics.get('motions', []))}, "
                f"applied={applied_motions}, "
                f"closure_versions={len(versions.get('records', []))}, "
                f"heads={len(versions.get('heads', []))}"
            )
        print(f"last decision: {execution.get('last_decision')}")
        return 0
    if schema_version(state) in ORDERED_SCHEMAS:
        order = panorama.get("order", {})
        print(
            "order: "
            f"{order.get('status')} "
            f"({len(order.get('nodes', []))} nodes, "
            f"{len(order.get('relations', []))} relations)"
        )
        center = state["center"]
        print(
            "center: "
            f"{len(center.get('members', []))} members, "
            f"{len(center.get('relation_ids', []))} relations, "
            f"minimality {center.get('minimality_status')}"
        )
        gate_counts = {status: 0 for status in sorted(GATE_STATUSES)}
        for item in focus.get("active_paths", []):
            if isinstance(item, dict) and item.get("gate_status") in gate_counts:
                gate_counts[item["gate_status"]] += 1
        print(
            "active path gates: "
            + ", ".join(f"{status}={gate_counts[status]}" for status in sorted(gate_counts))
        )
        if schema_version(state) in FOCUS_SCHEMAS:
            global_expansion = panorama.get("global_expansion", {})
            penetration = focus.get("penetration", {})
            print(
                "panorama: "
                f"map_version={panorama.get('map_version')}, "
                f"global_resolution=F{global_expansion.get('resolution_level')}"
            )
            print(
                "focus write-back: "
                f"delta={len(penetration.get('new_addresses', []))}, "
                f"locked={len(penetration.get('locked_interface_addresses', []))}"
            )
    else:
        center_count = len(state["center"].get("spine", []))
        print(f"center: {center_count} legacy positions (order not encoded)")
    print(f"focus: {focus.get('query') or '(unfocused)'}")
    if schema_version(state) == SCHEMA_AUDITED:
        print(
            "state S: "
            f"M={len(panorama.get('explored', []))}, "
            f"R={len(panorama.get('residuals', []))}, "
            f"Frontier={len(panorama.get('frontier', []))}"
        )
        audited_events = [
            event
            for event in state.get("history", [])
            if isinstance(event, dict) and isinstance(event.get("residual_audit"), dict)
        ]
        if audited_events:
            audit = audited_events[-1]["residual_audit"]
            print(
                "last residual audit: "
                f"motion={audit.get('motion')}, "
                f"delta_R={len(audit.get('delta_r_ids', []))}, "
                f"decision={audit.get('residual_driven_decision')}"
            )
    else:
        print(f"frontier: {len(panorama.get('frontier', []))}")
        print(f"residuals: {len(panorama.get('residuals', []))}")
    print(f"execution queue: {len(execution.get('queue', []))}")
    print(f"last decision: {execution.get('last_decision')}")
    return 0


def append_records_by_id(
    target: list[dict[str, Any]], records: Any, label: str
) -> None:
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ValueError(f"{label} must be a list of objects")
    existing = {
        item.get("id")
        for item in target
        if isinstance(item, dict) and nonempty_string(item.get("id"))
    }
    for record in records:
        record_id = record.get("id")
        if not nonempty_string(record_id):
            raise ValueError(f"{label} item needs a non-empty id")
        if record_id in existing:
            raise ValueError(f"duplicate {label} id: {record_id}")
        target.append(copy.deepcopy(record))
        existing.add(record_id)


def archive_absorbed_residuals(state: dict[str, Any], records: Any) -> list[str]:
    """Move explicitly absorbed schema-2.1+ residuals into the auditable history ledger."""
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ValueError("absorbed_residuals must be a list of objects")
    panorama = state["panorama"]
    active = panorama["residuals"]
    active_map = {
        item.get("id"): item
        for item in active
        if isinstance(item, dict) and nonempty_string(item.get("id"))
    }
    archived_ids = {
        item.get("id")
        for item in panorama.get("residual_history", [])
        if isinstance(item, dict) and nonempty_string(item.get("id"))
    }
    absorbed_ids: list[str] = []
    for record in records:
        residual_id = record.get("id")
        if residual_id not in active_map:
            raise ValueError(f"cannot absorb unknown active residual: {residual_id}")
        if residual_id in archived_ids or residual_id in absorbed_ids:
            raise ValueError(f"duplicate absorbed residual id: {residual_id}")
        for name in ("motion", "reason"):
            if not nonempty_string(record.get(name)):
                raise ValueError(f"absorbed residual {residual_id} needs {name}")
        if record.get("address") is not None and not nonempty_string(record.get("address")):
            raise ValueError(f"absorbed residual {residual_id} address must be null or non-empty")
        evidence_ids = record.get("evidence_ids", [])
        if not isinstance(evidence_ids, list) or not all(nonempty_string(item) for item in evidence_ids):
            raise ValueError(f"absorbed residual {residual_id} evidence_ids must be a string list")
        archived = copy.deepcopy(active_map[residual_id])
        archived["absorption_status"] = "absorbed"
        archived["absorbed_by"] = copy.deepcopy(record)
        archived["absorbed_at_version"] = state["version"] + 1
        panorama["residual_history"].append(archived)
        absorbed_ids.append(residual_id)
    if absorbed_ids:
        panorama["residuals"] = [
            item for item in active if item.get("id") not in set(absorbed_ids)
        ]
    return absorbed_ids


def rebuild_execution_plan(state: dict[str, Any]) -> None:
    """Derive D_t and Ready_t from Action paths and their required ancestry."""
    execution = state["execution"]
    action_items = state["panorama"]["frontiers"]["action"]
    for item in action_items:
        audited = audit_path(state, item, require_action_ready=True)
        if audited.get("gate_status") != "legal" or audited.get(
            "dependency_readiness"
        ) != "ready":
            reasons = "; ".join(audited.get("gate_reasons", []))
            raise ValueError(
                f"Action address {item.get('address')} is not execution-ready: "
                + (reasons or "structural gate failed")
            )
    node_map, relation_map = order_indexes(state)
    addresses: set[str] = set()
    for item in action_items:
        addresses.add(item["address"])
        addresses.update(item.get("required_predecessors", []))
        ancestry = item.get("root_ancestry", {})
        if isinstance(ancestry, dict):
            addresses.update(ancestry.get("node_addresses", []))
    relations = [
        copy.deepcopy(relation)
        for relation in relation_map.values()
        if relation.get("predecessor") in addresses and relation.get("successor") in addresses
    ]
    incoming: dict[str, int] = {address: 0 for address in addresses}
    for relation in relations:
        incoming[relation["successor"]] = incoming.get(relation["successor"], 0) + 1
    action_addresses = {item["address"] for item in action_items}
    compressed_addresses = {
        item.get("address")
        for item in state["panorama"]["frontiers"]["compressed"]
        if isinstance(item, dict)
    }
    node_status: dict[str, str] = {}
    for address in addresses:
        if address in action_addresses:
            node_status[address] = "pending"
        elif address in compressed_addresses:
            node_status[address] = "compressed-valid"
        elif node_map.get(address, {}).get("modal_status") == "[+]":
            node_status[address] = "satisfied"
        else:
            node_status[address] = "blocked"
    ready = [item["address"] for item in action_items]
    execution["subgraph"] = {
        "nodes": sorted(addresses),
        "relations": relations,
        "join_nodes": sorted(address for address, count in incoming.items() if count > 1),
    }
    execution["node_status"] = node_status
    execution["ready"] = ready
    execution["queue"] = ready


def joint_addresses(state: dict[str, Any]) -> set[str]:
    node_map, _ = joint_graph_indexes(state)
    return set(node_map)


def joint_dependency_ids(state: dict[str, Any]) -> set[str]:
    return {relation["id"] for relation in required_dependency_relations(state)}


def make_joint_drift_audit(
    before: dict[str, Any],
    after: dict[str, Any],
    motion: str,
    target_version: int,
    *,
    allow_root_contract_change: bool = False,
) -> dict[str, Any]:
    before_field = before["field"]
    after_field = after["field"]
    before_constraints = set(before_field.get("immutable_constraints", []))
    after_constraints = set(after_field.get("immutable_constraints", []))
    dropped_constraints = sorted(before_constraints - after_constraints)
    before_addresses = joint_addresses(before)
    after_addresses = joint_addresses(after)
    before_dependencies = joint_dependency_ids(before)
    after_dependencies = joint_dependency_ids(after)
    address_retention = (
        len(before_addresses & after_addresses) / len(before_addresses)
        if before_addresses
        else 1.0
    )
    dependency_union = before_dependencies | after_dependencies
    dependency_churn = (
        len(before_dependencies ^ after_dependencies) / len(dependency_union)
        if dependency_union
        else 0.0
    )
    constraint_retention = (
        len(before_constraints & after_constraints) / len(before_constraints)
        if before_constraints
        else 1.0
    )
    before_selected = before.get("center", {}).get("selected")
    after_selected = after.get("center", {}).get("selected")
    selected_retention: float | None = (
        None if before_selected is None else float(before_selected == after_selected)
    )
    before_realized = set(before.get("panorama", {}).get("explored", []))
    after_realized = set(after.get("panorama", {}).get("explored", []))
    invalidated_realized = len(before_realized - after_realized)
    stale_active = sum(
        1
        for path in after.get("focus", {}).get("active_paths", [])
        if isinstance(path, dict) and path.get("gate_status") != "legal"
    )
    goal_key = "root_goal" if has_field_formation_schema(after) else "ancestor_goal"
    goal_changed = before_field.get(goal_key) != after_field.get(goal_key)
    center_changed = before_selected != after_selected
    metrics = {
        "goal_identity": float(not goal_changed),
        "immutable_constraint_retention": constraint_retention,
        "selected_center_retention": selected_retention,
        "address_retention": address_retention,
        "dependency_churn": dependency_churn,
        "invalidated_realized_count": invalidated_realized,
        "stale_active_path_count": stale_active,
    }
    changes = {
        "goal_changed": goal_changed,
        "dropped_immutable_constraints": dropped_constraints,
        "selected_center_changed": center_changed,
        "added_addresses": sorted(after_addresses - before_addresses),
        "removed_addresses": sorted(before_addresses - after_addresses),
        "added_dependencies": sorted(after_dependencies - before_dependencies),
        "removed_dependencies": sorted(before_dependencies - after_dependencies),
    }
    policy = after.get("drift", {}).get("policy", {})
    reasons: list[str] = []
    status = "pass"
    if policy.get("require_goal_identity") and goal_changed and not allow_root_contract_change:
        status = "fail"
        reasons.append("root goal changed")
    if (
        policy.get("require_immutable_constraint_retention")
        and dropped_constraints
        and not allow_root_contract_change
    ):
        status = "fail"
        reasons.append("immutable constraints were removed")
    warnings: list[str] = []
    if allow_root_contract_change and (goal_changed or dropped_constraints):
        warnings.append("root contract changed through an explicit closed root rebuild")
    if center_changed:
        warnings.append("selected center changed")
    if address_retention < policy.get("min_address_retention", 0.0):
        warnings.append("address retention fell below policy")
    if dependency_churn > policy.get("max_dependency_churn", 1.0):
        warnings.append("dependency churn exceeded policy")
    if invalidated_realized:
        warnings.append("realized addresses were invalidated")
    if stale_active:
        warnings.append("active Focus paths became stale")
    if warnings:
        reasons.extend(warnings)
        if status != "fail":
            status = "warn"
    return {
        "id": f"D{target_version}",
        "motion": motion,
        "source_version": before["version"],
        "target_version": target_version,
        "changes": changes,
        "metrics": metrics,
        "status": status,
        "reasons": reasons,
        "timestamp": now_iso(),
    }


def append_joint_motion_event(
    state: dict[str, Any],
    before: dict[str, Any],
    event_type: str,
    note: str,
    address: str | None,
    details: dict[str, Any],
    *,
    allow_root_contract_change: bool = False,
) -> None:
    target_version = before["version"] + 1
    audit = make_joint_drift_audit(
        before,
        state,
        event_type,
        target_version,
        allow_root_contract_change=allow_root_contract_change,
    )
    if audit["status"] == "fail":
        raise ValueError(
            "drift audit failed; motion rolled back: "
            + ("; ".join(audit.get("reasons", [])) or "policy violation")
        )
    state["drift"]["audits"].append(audit)
    state["version"] = target_version
    state["execution"]["snapshot_version"] = target_version
    state["history"].append(
        {
            "version": target_version,
            "type": event_type,
            "address": address,
            "note": note,
            "details": copy.deepcopy(details),
            "drift_audit_id": audit["id"],
            "timestamp": now_iso(),
        }
    )


def add_joint_graph_delta(
    state: dict[str, Any], nodes: Any, relations: Any
) -> list[str]:
    if not isinstance(nodes, list) or not all(isinstance(item, dict) for item in nodes):
        raise ValueError("graph_nodes must be a list of objects")
    if not isinstance(relations, list) or not all(
        isinstance(item, dict) for item in relations
    ):
        raise ValueError("graph_relations must be a list of objects")
    graph = state["panorama"]["graph"]
    existing_nodes = {
        item.get("address")
        for item in graph["nodes"]
        if isinstance(item, dict)
    }
    new_addresses: list[str] = []
    for node in nodes:
        address = node.get("address")
        if not nonempty_string(address):
            raise ValueError("graph delta node needs a non-empty address")
        if address in existing_nodes:
            raise ValueError(f"graph delta node already exists: {address}")
        graph["nodes"].append(copy.deepcopy(node))
        existing_nodes.add(address)
        new_addresses.append(address)
    existing_relations = {
        item.get("id")
        for item in graph["relations"]
        if isinstance(item, dict)
    }
    for relation in relations:
        relation_id = relation.get("id")
        if not nonempty_string(relation_id):
            raise ValueError("graph delta relation needs a non-empty id")
        if relation_id in existing_relations:
            raise ValueError(f"graph delta relation already exists: {relation_id}")
        graph["relations"].append(copy.deepcopy(relation))
        existing_relations.add(relation_id)
    return new_addresses


def apply_joint_graph_node_updates(
    state: dict[str, Any], updates: Any
) -> list[str]:
    if not isinstance(updates, list) or not all(isinstance(item, dict) for item in updates):
        raise ValueError("graph_node_updates must be a list of objects")
    node_map, _ = joint_graph_indexes(state)
    changed: list[str] = []
    allowed = {
        "address",
        "function",
        "evidence_status",
        "evidence_ids",
        "validity",
        "modal_status",
        "payload_revision",
        "payload_ref",
        "payload_summary",
        "field_opening_status",
        "field_opening_audit",
    }
    for update in updates:
        address = update.get("address")
        if not nonempty_string(address) or address not in node_map:
            raise ValueError(f"graph node update references an unknown address: {address!r}")
        unknown = set(update) - allowed
        if unknown:
            raise ValueError(
                "graph node update contains unsupported keys: "
                + ", ".join(sorted(unknown))
            )
        node = node_map[address]
        if "payload_revision" in update:
            next_revision = update["payload_revision"]
            if not isinstance(next_revision, int) or next_revision != node.get("payload_revision", 0) + 1:
                raise ValueError(
                    f"payload_revision for {address} must increment by exactly one"
                )
        for name, value in update.items():
            if name != "address":
                node[name] = copy.deepcopy(value)
        changed.append(address)
    return changed


def realize_joint_addresses(state: dict[str, Any], addresses: Any) -> list[str]:
    if not isinstance(addresses, list) or not all(nonempty_string(item) for item in addresses):
        raise ValueError("realized_addresses must be a string list")
    if len(addresses) != len(set(addresses)):
        raise ValueError("realized_addresses contains duplicates")
    node_map, _ = joint_graph_indexes(state)
    for address in addresses:
        node = node_map.get(address)
        if node is None:
            raise ValueError(f"cannot realize unknown graph address: {address}")
        if node.get("validity") != "valid":
            raise ValueError(f"cannot realize stale or invalid address: {address}")
        if node.get("modal_status") != "[◇]":
            raise ValueError(f"only a valid potential [◇] address may be realized: {address}")
        if (
            focus_display_address(state, address) is not None
            and node.get("field_opening_status") != "validated"
        ):
            raise ValueError(
                f"cannot realize recursive address without a validated child field: {address}"
            )
        node["modal_status"] = "[+]"
    return list(addresses)


def apply_center_update(state: dict[str, Any], update: Any) -> None:
    if update is None:
        return
    if not isinstance(update, dict):
        raise ValueError("center_update must be null or an object")
    state["center"] = copy.deepcopy(update)


def apply_joint_motion_delta(
    state: dict[str, Any],
    motion: str,
    delta: dict[str, Any],
    *,
    address_motion: dict[str, Any] | None = None,
) -> dict[str, Any]:
    panorama = state["panorama"]
    source_version = panorama["map_version"]
    confirmation_before = state.get("field", {}).get("f0_confirmation", {}).get("status")
    center_signature_before = selected_center_signature(state)
    if delta.get("source_panorama_version") != source_version:
        raise ValueError("motion delta source_panorama_version does not match map_version")
    new_residuals = delta.get("residuals")
    if not isinstance(new_residuals, list) or not all(
        isinstance(item, dict) for item in new_residuals
    ):
        raise ValueError("every audited motion requires a residuals list")
    if not new_residuals and not nonempty_string(delta.get("empty_residual_reason")):
        raise ValueError(
            "an audited motion with no new residual requires empty_residual_reason"
        )
    realized_request = delta.get("realized_addresses", [])
    if not isinstance(realized_request, list) or not all(
        nonempty_string(item) for item in realized_request
    ):
        raise ValueError("realized_addresses must be a string list")
    if realized_request:
        raise ValueError(
            f"{motion} cannot materialize task addresses; only an audited EXECUTE may change [◇] to [+]"
        )
    if motion == "GLOBAL_EXPAND":
        eligible = delta.get("eligible_addresses")
        expanded = delta.get("expanded_addresses")
        deferred = delta.get("deferred")
        if not isinstance(eligible, list) or not all(nonempty_string(item) for item in eligible):
            raise ValueError("eligible_addresses must be a string list")
        if not isinstance(expanded, list) or not all(nonempty_string(item) for item in expanded):
            raise ValueError("expanded_addresses must be a string list")
        if not isinstance(deferred, list) or not all(isinstance(item, dict) for item in deferred):
            raise ValueError("deferred must be a list of objects")
        if len(eligible) != len(set(eligible)) or len(expanded) != len(set(expanded)):
            raise ValueError("Global Expansion address lists contain duplicates")
        deferred_addresses: list[str] = []
        for item in deferred:
            address = item.get("address")
            if not nonempty_string(address) or item.get("reason") not in GLOBAL_DEFER_REASONS:
                raise ValueError("each deferred item needs an address and allowed reason")
            deferred_addresses.append(address)
        if len(deferred_addresses) != len(set(deferred_addresses)):
            raise ValueError("deferred contains duplicate addresses")
        before_expansion = {
            item.get("address")
            for item in panorama.get("frontiers", {}).get("expansion", [])
            if isinstance(item, dict)
        }
        if set(eligible) != before_expansion:
            raise ValueError(
                "Global Expansion eligible_addresses must equal the complete current Expansion frontier"
            )
        if not eligible:
            raise ValueError("Global Expansion has no eligible Expansion-frontier address")
        if set(expanded) & set(deferred_addresses):
            raise ValueError("an eligible address cannot be both expanded and deferred")
        if set(expanded) | set(deferred_addresses) != set(eligible):
            raise ValueError("every eligible address must be expanded or explicitly deferred")
    else:
        eligible = []
        expanded = []
        deferred = []

    panorama_changed = any(
        bool(delta.get(name))
        for name in (
            "graph_nodes",
            "graph_node_updates",
            "graph_relations",
            "evidence",
            "residuals",
            "absorbed_residuals",
            "modal_results",
            "center_update",
            "field_update",
            "active_paths",
        )
    ) or delta.get("frontiers_after") != panorama.get("frontiers")
    if motion == "GLOBAL_EXPAND":
        panorama_changed = panorama_changed or bool(deferred)
    address_motion_payload = isinstance(delta.get("address_dynamics_delta"), dict)
    meaningful_payload = panorama_changed or address_motion_payload
    if not meaningful_payload:
        raise ValueError(f"{motion} delta is an empty no-op")

    new_addresses = add_joint_graph_delta(
        state, delta.get("graph_nodes", []), delta.get("graph_relations", [])
    )
    updated_addresses = apply_joint_graph_node_updates(
        state, delta.get("graph_node_updates", [])
    )
    realized: list[str] = []
    if motion == "GLOBAL_EXPAND":
        field_id = state.get("field", {}).get("id")

        def direct_child(parent: str, child: str) -> bool:
            if parent == field_id:
                return bool(re.fullmatch(re.escape(parent) + r":[A-Z]\d+", child))
            return bool(re.fullmatch(re.escape(parent) + r"\.\d+", child))

        graph_nodes = delta.get("graph_nodes", [])
        for source in expanded:
            traceable = any(
                isinstance(node, dict)
                and node.get("address") in new_addresses
                and (
                    node.get("parent_address") == source
                    or direct_child(source, str(node.get("address")))
                )
                for node in graph_nodes
            )
            if not traceable:
                raise ValueError(
                    f"expanded address {source} has no traceable one-level child"
                )
    append_records_by_id(state["evidence"], delta.get("evidence", []), "evidence")
    absorbed_residual_ids = archive_absorbed_residuals(
        state, delta.get("absorbed_residuals", [])
    )
    append_records_by_id(panorama["residuals"], new_residuals, "residual")
    append_records_by_id(
        panorama["modal_results"], delta.get("modal_results", []), "modal result"
    )
    panorama["map_version"] = source_version + (1 if panorama_changed else 0)
    panorama["graph"]["status"] = delta.get("graph_status", "tentative")
    rebuild_joint_order(
        state, motion, order_status=delta.get("order_status", "tentative")
    )
    apply_center_update(state, delta.get("center_update"))
    field_update = delta.get("field_update")
    if field_update is not None:
        if not isinstance(field_update, dict):
            raise ValueError("field_update must be null or an object")
        allowed_field_updates = {
            "root_goal",
            "name",
            "boundary",
            "success_criteria",
            "immutable_constraints",
            "allowed_changes",
            "tolerance",
            "status",
            "phase",
            "contract_status",
            "f0_confirmation",
            "ambiguities",
            "human_calibration",
        }
        unknown = set(field_update) - allowed_field_updates
        if unknown:
            raise ValueError("field_update contains unsupported keys: " + ", ".join(sorted(unknown)))
        audited_root_rebuild = (
            isinstance(address_motion, dict)
            and address_motion.get("classification") == "root-rebuild"
            and address_motion.get("motion_operator") == "REBUILD"
        )
        changed_root_contract_fields = {
            name
            for name in ROOT_CONTRACT_FIELDS
            if name in field_update
            and field_update[name] != state["field"].get(name)
        }
        has_closure_versions = bool(
            state.get("address_dynamics", {})
            .get("field_versions", {})
            .get("records", [])
        )
        formation_contract_change = (
            motion in {"FIELD_FORM", "CENTER_ADJUST", "HUMAN_CALIBRATE"}
            and not has_closure_versions
        )
        if changed_root_contract_fields and not (
            audited_root_rebuild or formation_contract_change
        ):
            raise ValueError(
                "a root contract may change during pre-version field formation or through an audited root-rebuild address motion"
            )
        if changed_root_contract_fields and state["field"].get(
            "f0_confirmation", {}
        ).get("status") in {"confirmed", "bypassed"}:
            confirmation = field_update.get("f0_confirmation")
            if not isinstance(confirmation, dict) or confirmation.get("status") != "required":
                raise ValueError(
                    "a changed root contract must reset f0_confirmation to required"
                )
        state["field"].update(copy.deepcopy(field_update))
    if (
        confirmation_before in {"confirmed", "bypassed"}
        and selected_center_signature(state) != center_signature_before
        and state.get("field", {}).get("f0_confirmation", {}).get("status") != "required"
    ):
        raise ValueError(
            "a constitutive selected-center change must reset f0_confirmation to required"
        )
    panorama["frontiers"] = normalize_joint_frontiers(
        state, delta.get("frontiers_after")
    )
    if motion == "GLOBAL_EXPAND":
        expansion_after = {
            item["address"] for item in panorama["frontiers"]["expansion"]
        }
        deferred_set = {item["address"] for item in deferred}
        if not deferred_set <= expansion_after:
            raise ValueError(
                "deferred Global Expansion addresses must remain in the Expansion frontier"
            )
        if set(expanded) & expansion_after:
            raise ValueError(
                "expanded Global Expansion sources must leave the Expansion frontier"
            )
    action_addresses = [
        item["address"] for item in panorama["frontiers"]["action"]
    ]
    state["execution"]["queue"] = action_addresses
    if state["execution"].get("active") not in set(action_addresses):
        state["execution"]["active"] = None
    rebuild_execution_plan(state)
    if motion == "GLOBAL_EXPAND":
        global_state = panorama["global_expansion"]
        global_state["last_deferred"] = copy.deepcopy(deferred)
        if deferred:
            global_state["status"] = "bounded"
        else:
            global_state["status"] = "complete"
            global_state["resolution_level"] += 1
            global_state["last_uniform_expansion_version"] = panorama["map_version"]
    return {
        "source_panorama_version": source_version,
        "written_panorama_version": panorama["map_version"],
        "panorama_changed": panorama_changed,
        "new_addresses": new_addresses,
        "updated_addresses": updated_addresses,
        "realized_addresses": realized,
        "eligible_addresses": list(eligible),
        "expanded_addresses": list(expanded),
        "deferred": copy.deepcopy(deferred),
        "new_residual_ids": [item["id"] for item in new_residuals],
        "absorbed_residual_ids": absorbed_residual_ids,
        "empty_residual_reason": delta.get("empty_residual_reason"),
    }


def descendants_of(seeds: set[str], adjacency: dict[str, set[str]]) -> set[str]:
    descendants: set[str] = set()
    stack = list(seeds)
    while stack:
        current = stack.pop()
        for successor in adjacency.get(current, set()):
            if successor not in seeds and successor not in descendants:
                descendants.add(successor)
                stack.append(successor)
    return descendants


def path_touches_addresses(item: dict[str, Any], addresses: set[str]) -> bool:
    if item.get("address") in addresses:
        return True
    ancestry = item.get("root_ancestry", {})
    if not isinstance(ancestry, dict):
        return False
    retained = set(ancestry.get("node_addresses", [])) | set(
        ancestry.get("compressed_ancestor_addresses", [])
    )
    return bool(retained & addresses)


def propagate_joint_invalidation(
    state: dict[str, Any], invalidations: Any, *, motion: str
) -> dict[str, Any]:
    if not isinstance(invalidations, list) or not all(
        isinstance(item, dict) for item in invalidations
    ):
        raise ValueError("invalidations must be a list of objects")
    node_map, _ = joint_graph_indexes(state)
    evidence_ids = {
        item.get("id")
        for item in state.get("evidence", [])
        if isinstance(item, dict) and nonempty_string(item.get("id"))
    }
    adjacency: dict[str, set[str]] = {address: set() for address in node_map}
    for relation in required_dependency_relations(state):
        adjacency.setdefault(relation["source"], set()).add(relation["target"])

    direct: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for item in invalidations:
        address = item.get("address")
        if not nonempty_string(address) or address not in node_map:
            raise ValueError(f"invalidation references an unknown address: {address!r}")
        if address in direct:
            raise ValueError(f"duplicate invalidation address: {address}")
        if not nonempty_string(item.get("reason")):
            raise ValueError(f"invalidation for {address} needs a reason")
        if not nonempty_string(item.get("evidence_id")):
            raise ValueError(f"invalidation for {address} needs an evidence_id")
        if item.get("evidence_id") not in evidence_ids:
            raise ValueError(
                f"invalidation for {address} references unknown evidence: {item.get('evidence_id')}"
            )
        result_modal = item.get("result_modal", "[◇]")
        if result_modal not in RESIDUAL_MODAL_STATUSES:
            raise ValueError(f"invalidation for {address} has invalid result_modal")
        normalized.append(
            {
                "address": address,
                "reason": item["reason"],
                "evidence_id": item.get("evidence_id"),
                "result_modal": result_modal,
            }
        )
        direct.add(address)
    downstream = descendants_of(direct, adjacency)
    affected = direct | downstream

    existing_modal_ids = {
        item.get("id")
        for item in state["panorama"]["modal_results"]
        if isinstance(item, dict)
    }
    existing_residual_ids = {
        item.get("id")
        for item in state["panorama"]["residuals"]
        if isinstance(item, dict)
    }
    invalidation_by_address = {item["address"]: item for item in normalized}
    for address in sorted(affected):
        node = node_map[address]
        node["validity"] = "invalid" if address in direct else "stale"
        node["modal_status"] = "[◇]"
    for item in normalized:
        address = item["address"]
        digest = hashlib.sha256(
            f"{address}\0{state['panorama']['map_version']}".encode("utf-8")
        ).hexdigest()[:12]
        if item["result_modal"] in {"[-]", "[∅]"}:
            modal_id = f"MR-INV-{digest}"
            if modal_id not in existing_modal_ids:
                state["panorama"]["modal_results"].append(
                    {
                        "id": modal_id,
                        "address": address,
                        "modal_status": item["result_modal"],
                        "reason": item["reason"],
                        "evidence_ids": (
                            [item["evidence_id"]] if nonempty_string(item.get("evidence_id")) else []
                        ),
                        "version": state["version"] + 1,
                    }
                )
                existing_modal_ids.add(modal_id)
        residual_id = f"R-INV-{digest}"
        if residual_id not in existing_residual_ids:
            if item["result_modal"] == "[◇]":
                relation_kind = "hypothesized"
                gate_status = "unverified"
                reach_kind = "unknown"
            elif item["result_modal"] == "[-]":
                relation_kind = "negative"
                gate_status = "conflicting"
                reach_kind = "unreachable"
            else:
                relation_kind = "no-address"
                gate_status = "out-of-field"
                reach_kind = "unreachable"
            state["panorama"]["residuals"].append(
                {
                    "id": residual_id,
                    "classification": "true-residual",
                    "residual_type": "invalidation",
                    "description": item["reason"],
                    "origin": "closure-produced",
                    "produced_by": {"motion": motion, "address": address},
                    "failing_address": address,
                    "effect_on_f0": "a realized or potential dependency no longer supports the current task structure",
                    "representation_failure": "the previous necessary order and selected center still depended on an invalidated address",
                    "modal_status": item["result_modal"],
                    "possible_destination": "in-field-remodel",
                    "changes_focus_or_execution": {
                        "changes": True,
                        "reason": "propagate staleness, re-open interfaces, and re-audit legal actions",
                    },
                    "tolerance_status": "above",
                    "evidence_status": "explicit" if item.get("evidence_id") else "inferred",
                    "address_relation": {
                        "kind": relation_kind,
                        "address": address if relation_kind != "no-address" else None,
                        "gate_status": gate_status,
                        "reach": {
                            "kind": reach_kind,
                            "estimated_expansions": None,
                            "evidence_status": (
                                "explicit" if item.get("evidence_id") else "inferred"
                            ),
                        },
                        "conflict_with": [address],
                    },
                    "absorption_status": "unresolved",
                    "closure_condition": "replace or revalidate the invalidated dependency, then rebuild center, order, Focus, and execution gates",
                }
            )
            existing_residual_ids.add(residual_id)

    graph = state["panorama"]["graph"]
    for relation in graph["relations"]:
        if not isinstance(relation, dict):
            continue
        if relation.get("source") in direct or relation.get("target") in direct:
            relation["validity"] = "invalid"
        elif relation.get("source") in affected or relation.get("target") in affected:
            relation["validity"] = "stale"

    center = state["center"]
    selected = center.get("selected")
    for candidate in center.get("candidates", []):
        if isinstance(candidate, dict) and set(candidate.get("members", [])) & affected:
            candidate["validity"] = "stale"
            candidate["minimality_status"] = "unvalidated"
            if candidate.get("id") == selected:
                center["selected"] = None
                center["status"] = "remodel-required"

    frontiers = state["panorama"]["frontiers"]
    for name in ("action", "expansion"):
        frontiers[name] = [
            item
            for item in frontiers[name]
            if isinstance(item, dict) and not path_touches_addresses(item, affected)
        ]
    for interface in frontiers["compressed"]:
        if isinstance(interface, dict) and interface.get("address") in affected:
            interface["exposure_status"] = "reopen-required"

    execution = state["execution"]
    removed_queue = [address for address in execution.get("queue", []) if address in affected]
    execution["queue"] = [
        address for address in execution.get("queue", []) if address not in affected
    ]
    for address in removed_queue:
        execution["blocked"].append(
            {
                "address": address,
                "reason": "required dependency invalidated",
                "evidence_ids": sorted(
                    {item["evidence_id"] for item in normalized}
                ),
                "version": state["version"] + 1,
            }
        )
    if execution.get("active") in affected:
        execution["active"] = None

    state["focus"]["active_paths"] = [
        item
        for item in state["focus"].get("active_paths", [])
        if isinstance(item, dict) and not path_touches_addresses(item, affected)
    ]
    if affected:
        state["focus"]["status"] = "remodel-required"

    rebuild_joint_order(state, motion, order_status="tentative")
    state["focus"]["active_paths"] = [
        normalize_joint_path(state, item, modal_status="[◇]")
        for item in state["focus"].get("active_paths", [])
    ]
    return {
        "direct": sorted(direct),
        "downstream": sorted(downstream),
        "affected": sorted(affected),
        "invalidations": normalized,
    }


def apply_joint_execution_audit(
    state: dict[str, Any], audit: dict[str, Any]
) -> dict[str, Any]:
    execution = state["execution"]
    if audit.get("snapshot_version") != execution.get("snapshot_version"):
        raise ValueError("execution audit snapshot_version is stale")
    completed = audit.get("completed")
    blocked = audit.get("blocked")
    if not isinstance(completed, list) or not all(isinstance(item, dict) for item in completed):
        raise ValueError("execution audit completed must be a list of objects")
    if not isinstance(blocked, list) or not all(isinstance(item, dict) for item in blocked):
        raise ValueError("execution audit blocked must be a list of objects")
    action_before = {
        item.get("address")
        for item in state["panorama"]["frontiers"]["action"]
        if isinstance(item, dict)
    }
    realized_request = audit.get("realized_addresses")
    if not isinstance(realized_request, list) or not all(
        nonempty_string(item) for item in realized_request
    ):
        raise ValueError("execution audit realized_addresses must be a string list")
    if len(realized_request) != len(set(realized_request)):
        raise ValueError("execution audit realized_addresses contains duplicates")
    addressed: set[str] = set()
    completed_addresses: set[str] = set()
    for label, records in (("completed", completed), ("blocked", blocked)):
        for item in records:
            address = item.get("address")
            if address not in action_before:
                raise ValueError(f"execution {label} address was not in the Action frontier: {address}")
            if address in addressed:
                raise ValueError(f"execution address appears more than once: {address}")
            addressed.add(address)
            if label == "completed" and not nonempty_string(item.get("result")):
                raise ValueError(f"completed execution {address} needs a result")
            if label == "blocked" and not nonempty_string(item.get("reason")):
                raise ValueError(f"blocked execution {address} needs a reason")
            evidence_ids = item.get("evidence_ids")
            if not isinstance(evidence_ids, list) or not evidence_ids or not all(
                nonempty_string(evidence_id) for evidence_id in evidence_ids
            ):
                raise ValueError(
                    f"execution {label} {address} needs a non-empty evidence_ids list"
                )
            if label == "completed":
                completed_addresses.add(address)
    if set(realized_request) != completed_addresses:
        raise ValueError(
            "execution realized_addresses must exactly equal completed Action addresses"
        )
    for name in ("precondition_gaps", "absorbed_outcomes"):
        values = audit.get(name)
        if not isinstance(values, list) or not all(isinstance(item, dict) for item in values):
            raise ValueError(f"execution audit {name} must be a list of objects")
    decision = audit.get("residual_driven_decision")
    if decision not in NEXT_DECISIONS:
        raise ValueError("execution audit residual_driven_decision is invalid")
    new_residuals = audit.get("residuals")
    if not isinstance(new_residuals, list) or not all(
        isinstance(item, dict) for item in new_residuals
    ):
        raise ValueError("execution audit residuals must be a list of objects")
    if not new_residuals and not nonempty_string(audit.get("empty_residual_reason")):
        raise ValueError(
            "an execution audit with no new residual requires empty_residual_reason"
        )

    supplied_evidence = audit.get("evidence", [])
    if not isinstance(supplied_evidence, list) or not all(
        isinstance(item, dict) for item in supplied_evidence
    ):
        raise ValueError("execution audit evidence must be a list of objects")
    known_evidence_ids = {
        item.get("id")
        for item in state.get("evidence", []) + supplied_evidence
        if isinstance(item, dict) and nonempty_string(item.get("id"))
    }
    for label, records in (("completed", completed), ("blocked", blocked)):
        for item in records:
            missing_evidence = set(item["evidence_ids"]) - known_evidence_ids
            if missing_evidence:
                raise ValueError(
                    f"execution {label} {item.get('address')} references unknown evidence: "
                    + ", ".join(sorted(missing_evidence))
                )
    append_records_by_id(state["evidence"], supplied_evidence, "evidence")
    absorbed_residual_ids = archive_absorbed_residuals(
        state, audit.get("absorbed_residuals", [])
    )
    append_records_by_id(state["panorama"]["residuals"], new_residuals, "residual")
    append_records_by_id(
        state["panorama"]["modal_results"],
        audit.get("modal_results", []),
        "modal result",
    )
    realized = realize_joint_addresses(state, realized_request)
    state["panorama"]["map_version"] += 1
    rebuild_joint_order(
        state, "EXECUTE", order_status=audit.get("order_status", "tentative")
    )
    state["panorama"]["frontiers"] = normalize_joint_frontiers(
        state, audit.get("frontiers_after")
    )
    action_after = {
        item["address"] for item in state["panorama"]["frontiers"]["action"]
    }
    if addressed & action_after:
        raise ValueError(
            "completed or blocked addresses must be consumed from the Action frontier"
        )
    rebuild_execution_plan(state)
    target_version = state["version"] + 1
    execution["completed"].extend(
        [{**copy.deepcopy(item), "version": target_version} for item in completed]
    )
    execution["blocked"].extend(
        [{**copy.deepcopy(item), "version": target_version} for item in blocked]
    )
    execution["active"] = None
    execution["queue"] = [
        item["address"]
        for item in state["panorama"]["frontiers"]["action"]
        if item.get("address") not in addressed
    ]
    execution["ready"] = list(execution["queue"])
    for item in completed:
        execution["node_status"][item["address"]] = "completed"
    for item in blocked:
        execution["node_status"][item["address"]] = "blocked"
    execution["last_decision"] = decision
    state["focus"]["active_paths"] = [
        item
        for item in state["focus"].get("active_paths", [])
        if isinstance(item, dict) and item.get("address") not in set(realized)
    ]
    if not state["focus"]["active_paths"]:
        state["focus"]["status"] = "unfocused"
    if audit.get("invalidations"):
        propagation = propagate_joint_invalidation(
            state, audit.get("invalidations"), motion="EXECUTE"
        )
    else:
        propagation = {
            "direct": [],
            "downstream": [],
            "affected": [],
            "invalidations": [],
        }
    return {
        "completed": copy.deepcopy(completed),
        "blocked": copy.deepcopy(blocked),
        "realized_addresses": realized,
        "precondition_gaps": copy.deepcopy(audit["precondition_gaps"]),
        "absorbed_outcomes": copy.deepcopy(audit["absorbed_outcomes"]),
        "new_residual_ids": [item["id"] for item in new_residuals],
        "absorbed_residual_ids": absorbed_residual_ids,
        "empty_residual_reason": audit.get("empty_residual_reason"),
        "residual_driven_decision": decision,
        "invalidation_propagation": propagation,
    }


def next_record_id(records: list[Any], prefix: str) -> str:
    highest = 0
    pattern = re.compile(re.escape(prefix) + r"(\d+)$")
    for item in records:
        if not isinstance(item, dict):
            continue
        match = pattern.fullmatch(str(item.get("id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}{highest + 1}"


def find_record(records: list[Any], record_id: str, label: str) -> dict[str, Any]:
    matches = [
        item
        for item in records
        if isinstance(item, dict) and item.get("id") == record_id
    ]
    if len(matches) != 1:
        raise ValueError(f"{label} {record_id!r} was not found uniquely")
    return matches[0]


def validate_update_structure_semantics(structure: dict[str, Any]) -> None:
    classification = structure.get("classification")
    if classification not in UPDATE_CLASSIFICATIONS:
        raise ValueError("update classification is invalid")
    operator = structure.get("motion_operator")
    if operator not in UPDATE_MOTION_OPERATORS:
        raise ValueError("update motion_operator is invalid")
    allowed_operators = {
        "external": {"UPDATE_RECONCILE"},
        "local-replace": {"UPDATE_RECONCILE"},
        "legal-expansion": {"EXPAND", "ADDRESS_MATERIALIZE"},
        "principle-conflict": {"UPDATE_RECONCILE"},
        "no-address-residual": {"UPDATE_RECONCILE", "REBUILD"},
        "subfield-rebuild": {"REBUILD", "SPLIT"},
        "root-rebuild": {"REBUILD", "SPLIT"},
        "version-branch": {"SPLIT", "REBUILD"},
    }
    if operator not in allowed_operators[classification]:
        raise ValueError(
            f"motion_operator {operator} is incompatible with {classification}"
        )
    assignment = structure.get("assignment")
    if not isinstance(assignment, dict):
        raise ValueError("update structure assignment must be an object")
    kind = assignment.get("kind")
    modal = assignment.get("modal_status")
    expected = {
        "external": ({"external"}, {None}),
        "local-replace": ({"existing"}, {"[+]", "[◇]"}),
        "legal-expansion": ({"potential", "new-child"}, {"[◇]"}),
        "principle-conflict": ({"negative"}, {"[-]"}),
        "no-address-residual": ({"no-address"}, {"[∅]"}),
        "subfield-rebuild": ({"subtree"}, {"[+]", "[◇]", "[∅]"}),
        "root-rebuild": ({"subtree"}, {"[+]", "[◇]", "[∅]"}),
        "version-branch": ({"subtree"}, {"[+]", "[◇]", "[∅]"}),
    }
    expected_kinds, expected_modals = expected[classification]
    if kind not in expected_kinds or modal not in expected_modals:
        raise ValueError(
            f"assignment kind/modal is incompatible with {classification}"
        )
    for name in ("anchor_addresses", "from_addresses", "to_addresses"):
        addresses = assignment.get(name)
        if not isinstance(addresses, list) or not all(
            is_strict_theory_address(item) for item in addresses
        ):
            raise ValueError(f"assignment.{name} must be a canonical F0 address list")
    if classification not in {"external", "no-address-residual"} and not assignment.get(
        "anchor_addresses"
    ):
        raise ValueError(f"{classification} requires at least one anchor address")
    if not nonempty_string(assignment.get("rationale")):
        raise ValueError("assignment.rationale must be non-empty")

    closure = structure.get("closure_audit")
    if not isinstance(closure, dict):
        raise ValueError("update structure closure_audit must be an object")
    for name in ("closure_before", "closure_after"):
        if closure.get(name) not in WORKING_CLOSURE_STATUSES:
            raise ValueError(f"closure_audit.{name} is invalid")
    for name in (
        "nearest_unstable_ancestor",
        "minimal_rebuild_root",
        "propagation_stop_address",
    ):
        value = closure.get(name)
        if value is not None and not is_strict_theory_address(value):
            raise ValueError(f"closure_audit.{name} must be null or F0 address")
    if classification == "root-rebuild" and closure.get("minimal_rebuild_root") != "F0":
        raise ValueError("root-rebuild requires minimal_rebuild_root F0")
    if classification == "subfield-rebuild" and closure.get("minimal_rebuild_root") in {None, "F0"}:
        raise ValueError("subfield-rebuild requires a non-root minimal_rebuild_root")
    if classification in {"no-address-residual", "subfield-rebuild", "root-rebuild"} and closure.get(
        "nearest_unstable_ancestor"
    ) is None:
        raise ValueError(f"{classification} requires nearest_unstable_ancestor")
    tested = closure.get("tested")
    if not isinstance(tested, list) or not all(isinstance(item, dict) for item in tested):
        raise ValueError("closure_audit.tested must be a list of objects")
    if classification in {"subfield-rebuild", "root-rebuild", "version-branch"} and not tested:
        raise ValueError(f"{classification} requires a non-empty closure test path")
    if classification == "version-branch":
        if closure.get("minimal_rebuild_root") is None:
            raise ValueError("version-branch requires a minimal_rebuild_root")
        source_versions = structure.get("source_field_version_ids")
        if not isinstance(source_versions, list) or not source_versions:
            raise ValueError("version-branch requires at least one source field version")
    if (
        classification == "no-address-residual"
        and closure.get("closure_after") == "relative-closed"
    ):
        raise ValueError(
            "no-address-residual must remain open until a later motion absorbs, externalizes, or prohibits it"
        )


def cmd_update_receive(args: argparse.Namespace) -> int:
    path = Path(args.path)
    state = read_state(path)
    errors = validate_state(state)
    if errors:
        raise ValueError("; ".join(errors))
    if not is_current_schema(state):
        raise ValueError(
            f"schema {schema_version(state)} is read-only; receive updates only in schema 2.2"
        )
    if not nonempty_string(args.text):
        raise ValueError("--text must be non-empty")
    evidence_ids = args.evidence_id or []
    known_evidence = {
        item.get("id")
        for item in state.get("evidence", [])
        if isinstance(item, dict)
    }
    if set(evidence_ids) - known_evidence:
        raise ValueError("--evidence-id references unknown evidence")
    inbox = state["address_dynamics"]["inbox"]
    update_id = next_record_id(inbox, "U")
    target_version = state["version"] + 1
    update = {
        "id": update_id,
        "intake_address": f"F0@{update_id}",
        "raw_content": args.text,
        "source": {"kind": args.source, "ref": args.source_ref},
        "received_at_runtime_version": target_version,
        "evidence_ids": list(evidence_ids),
        "status": "pending",
        "motion_ids": [],
    }
    inbox.append(update)
    append_event(
        state,
        "UPDATE_INGEST",
        f"raw update {update_id} preserved before structural interpretation",
        update["intake_address"],
    )
    final_errors = validate_state(state)
    if final_errors:
        raise ValueError("; ".join(final_errors))
    write_state(path, state)
    print(f"{update_id} {update['intake_address']} pending")
    return 0


def cmd_update_structure(args: argparse.Namespace) -> int:
    path = Path(args.path)
    state = read_state(path)
    errors = validate_state(state)
    if errors:
        raise ValueError("; ".join(errors))
    if not is_current_schema(state):
        raise ValueError(
            f"schema {schema_version(state)} is read-only; structure updates only in schema 2.2"
        )
    dynamics = state["address_dynamics"]
    update = find_record(dynamics["inbox"], args.update_id, "update")
    if update.get("status") not in {"pending", "structured"}:
        raise ValueError("only a pending or unresolved structured update may be structured")
    referenced_motions = [
        item
        for item in dynamics["motions"]
        if isinstance(item, dict) and item.get("id") in update.get("motion_ids", [])
    ]
    if any(item.get("status") == "proposed" for item in referenced_motions):
        raise ValueError("apply or dismiss the current proposed motion before structuring another")
    structure = parse_json_object(args.structure_json, "--structure-json")
    validate_update_structure_semantics(structure)
    branch_ids = {
        item.get("id")
        for item in dynamics["field_versions"]["branches"]
        if isinstance(item, dict)
    }
    branch_id = structure.get(
        "branch_id", dynamics["field_versions"]["active_branch_id"]
    )
    if branch_id not in branch_ids:
        raise ValueError("update structure references an unknown branch_id")
    version_ids = {
        item.get("id")
        for item in dynamics["field_versions"]["records"]
        if isinstance(item, dict)
    }
    source_versions = structure.get("source_field_version_ids", [])
    if not isinstance(source_versions, list) or not all(
        nonempty_string(item) for item in source_versions
    ):
        raise ValueError("source_field_version_ids must be a string list")
    if set(source_versions) - version_ids:
        raise ValueError("source_field_version_ids references unknown field versions")
    residual_ids = structure.get("residual_ids", [])
    evidence_ids = structure.get("evidence_ids", [])
    if not isinstance(residual_ids, list) or not all(nonempty_string(item) for item in residual_ids):
        raise ValueError("residual_ids must be a string list")
    if not isinstance(evidence_ids, list) or not all(nonempty_string(item) for item in evidence_ids):
        raise ValueError("evidence_ids must be a string list")
    known_residuals = {
        item.get("id")
        for name in ("residuals", "residual_history")
        for item in state["panorama"].get(name, [])
        if isinstance(item, dict)
    }
    known_evidence = {
        item.get("id") for item in state.get("evidence", []) if isinstance(item, dict)
    }
    if set(residual_ids) - known_residuals:
        raise ValueError("residual_ids references unknown residuals")
    if set(evidence_ids) - known_evidence:
        raise ValueError("evidence_ids references unknown evidence")
    motion_id = next_record_id(dynamics["motions"], "AM")
    target_version = state["version"] + 1
    motion = {
        "id": motion_id,
        "update_id": update["id"],
        "branch_id": branch_id,
        "classification": structure["classification"],
        "motion_operator": structure["motion_operator"],
        "status": "proposed",
        "structured_at_runtime_version": target_version,
        "applied_at_runtime_version": None,
        "source_field_version_ids": copy.deepcopy(source_versions),
        "assignment": copy.deepcopy(structure["assignment"]),
        "closure_audit": copy.deepcopy(structure["closure_audit"]),
        "lineage_ids": [],
        "result_closure_version_ids": [],
        "residual_ids": copy.deepcopy(residual_ids),
        "evidence_ids": copy.deepcopy(evidence_ids),
    }
    dynamics["motions"].append(motion)
    update["status"] = "structured"
    update["motion_ids"].append(motion_id)
    append_event(
        state,
        "UPDATE_STRUCTURE",
        f"update {update['id']} structured as {motion['classification']}",
        update["intake_address"],
    )
    final_errors = validate_state(state)
    if final_errors:
        raise ValueError("; ".join(final_errors))
    write_state(path, state)
    closure = motion["closure_audit"]
    anchors = ", ".join(motion["assignment"].get("anchor_addresses", [])) or "(none)"
    print(f"{motion_id}: {motion['classification']} {motion['assignment']['modal_status']}")
    print(f"update: {update['id']} {update['intake_address']}")
    print(f"anchor: {anchors}")
    print(f"nearest unstable: {closure.get('nearest_unstable_ancestor')}")
    print(f"minimal rebuild root: {closure.get('minimal_rebuild_root')}")
    print(f"propagation stop: {closure.get('propagation_stop_address')}")
    return 0


def normalize_lineage_record(
    raw: dict[str, Any], motion_id: str
) -> dict[str, Any]:
    record = copy.deepcopy(raw)
    record["motion_id"] = motion_id
    return record


def apply_address_dynamics_delta(
    state: dict[str, Any], motion: dict[str, Any], raw_delta: Any, target_version: int
) -> dict[str, Any]:
    if not isinstance(raw_delta, dict):
        raise ValueError("address_dynamics_delta must be an object")
    dynamics = state["address_dynamics"]
    lineage_records = raw_delta.get("lineage", [])
    if not isinstance(lineage_records, list) or not all(
        isinstance(item, dict) for item in lineage_records
    ):
        raise ValueError("address_dynamics_delta.lineage must be an object list")
    existing_lineage_ids = {
        item.get("id") for item in dynamics["lineage"] if isinstance(item, dict)
    }
    normalized_lineage: list[dict[str, Any]] = []
    for record in lineage_records:
        normalized = normalize_lineage_record(record, motion["id"])
        if not nonempty_string(normalized.get("id")):
            raise ValueError("each lineage record needs a non-empty id")
        if normalized["id"] in existing_lineage_ids:
            raise ValueError(f"duplicate lineage id: {normalized['id']}")
        existing_lineage_ids.add(normalized["id"])
        normalized_lineage.append(normalized)
    dynamics["lineage"].extend(normalized_lineage)

    versions = dynamics["field_versions"]
    new_branches = raw_delta.get("new_branches", [])
    if not isinstance(new_branches, list) or not all(
        isinstance(item, dict) for item in new_branches
    ):
        raise ValueError("new_branches must be an object list")
    existing_branch_ids = {
        item.get("id") for item in versions["branches"] if isinstance(item, dict)
    }
    for branch in new_branches:
        branch_id = branch.get("id")
        if not nonempty_string(branch_id) or branch_id in existing_branch_ids:
            raise ValueError("new branch id must be non-empty and unique")
        versions["branches"].append(copy.deepcopy(branch))
        existing_branch_ids.add(branch_id)
    for branch in new_branches:
        parent_branch_id = branch.get("parent_branch_id")
        if parent_branch_id is not None and parent_branch_id not in existing_branch_ids:
            raise ValueError(
                f"new branch {branch.get('id')} references an unknown parent branch"
            )

    new_versions = raw_delta.get("new_field_versions", [])
    if not isinstance(new_versions, list) or not all(
        isinstance(item, dict) for item in new_versions
    ):
        raise ValueError("new_field_versions must be an object list")
    existing_version_ids = {
        item.get("id") for item in versions["records"] if isinstance(item, dict)
    }
    normalized_versions: list[dict[str, Any]] = []
    for record in new_versions:
        normalized = copy.deepcopy(record)
        version_id = normalized.get("id")
        if not nonempty_string(version_id) or version_id in existing_version_ids:
            raise ValueError("new field version id must be non-empty and unique")
        if normalized.get("closure_status") != "relative-closed":
            raise ValueError("new field versions require relative-closed status")
        branch_id = normalized.get("branch_id")
        field_address = normalized.get("field_address")
        if branch_id not in existing_branch_ids:
            raise ValueError("new field version references an unknown branch")
        if not is_strict_theory_address(field_address):
            raise ValueError("new field version requires a canonical F0 field address")
        parent_ids = normalized.get("parent_ids")
        if not isinstance(parent_ids, list) or not all(
            nonempty_string(item) for item in parent_ids
        ):
            raise ValueError("new field version parent_ids must be a string list")
        source_versions = set(motion.get("source_field_version_ids", []))
        if source_versions and not source_versions <= set(parent_ids):
            raise ValueError(
                "each result field version must retain every declared source field version as a parent"
            )
        prior_ordinals = [
            item.get("ordinal")
            for item in [*versions["records"], *normalized_versions]
            if isinstance(item, dict)
            and item.get("branch_id") == branch_id
            and item.get("field_address") == field_address
            and isinstance(item.get("ordinal"), int)
        ]
        expected_ordinal = max(prior_ordinals, default=0) + 1
        if normalized.get("ordinal") != expected_ordinal:
            raise ValueError(
                f"new field version ordinal for {branch_id}/{field_address} must be {expected_ordinal}"
            )
        normalized["root_address"] = "F0"
        normalized["formed_at_runtime_version"] = target_version
        normalized["formed_by_motion_id"] = motion["id"]
        normalized["map_version"] = state["panorama"]["map_version"]
        absorbed_updates = normalized.get("absorbed_update_ids")
        if not isinstance(absorbed_updates, list) or motion["update_id"] not in absorbed_updates:
            raise ValueError(
                "a new field version must name the update that formed it"
            )
        normalized_versions.append(normalized)
        existing_version_ids.add(version_id)
    if normalized_versions and motion["closure_audit"].get("closure_after") != "relative-closed":
        raise ValueError("a new field version requires a relative-closed motion audit")
    if normalized_versions and not normalized_lineage:
        raise ValueError(
            "a new field version must preserve at least one explicit address-lineage relation"
        )
    if motion["classification"] in {
        "external",
        "local-replace",
        "principle-conflict",
        "no-address-residual",
    } and normalized_versions:
        raise ValueError(
            f"{motion['classification']} cannot directly create a field-closure version"
        )
    if (
        motion["classification"]
        in {"subfield-rebuild", "root-rebuild", "version-branch"}
        and motion["closure_audit"].get("closure_after") == "relative-closed"
        and not normalized_versions
    ):
        raise ValueError(
            "a relatively closed rebuild must create at least one field-closure version"
        )
    rebuild_root = motion["closure_audit"].get("minimal_rebuild_root")
    if motion["classification"] == "root-rebuild" and any(
        item.get("field_address") != "F0" for item in normalized_versions
    ):
        raise ValueError("root-rebuild may create only F0 field versions")
    if motion["classification"] == "subfield-rebuild" and any(
        item.get("field_address") != rebuild_root for item in normalized_versions
    ):
        raise ValueError(
            "subfield-rebuild result versions must match minimal_rebuild_root"
        )
    if motion["classification"] == "version-branch":
        result_branches = {item.get("branch_id") for item in normalized_versions}
        new_branch_ids = {item.get("id") for item in new_branches}
        if len(normalized_versions) < 2 or len(result_branches) < 2:
            raise ValueError(
                "version-branch must create at least two versions on distinct branches"
            )
        if not result_branches <= new_branch_ids:
            raise ValueError("version-branch results must use explicitly created branches")
        if any(
            item.get("parent_branch_id") != motion.get("branch_id")
            for item in new_branches
            if item.get("id") in result_branches
        ):
            raise ValueError(
                "each result branch must name the motion branch as parent_branch_id"
            )
        if any(
            item.get("field_address") != rebuild_root for item in normalized_versions
        ):
            raise ValueError(
                "version-branch result versions must match minimal_rebuild_root"
            )
        if any(
            not nonempty_string(item.get("snapshot_ref"))
            or not re.fullmatch(
                r"sha256:[0-9a-f]{64}", str(item.get("snapshot_hash", ""))
            )
            for item in normalized_versions
        ):
            raise ValueError(
                "version-branch result versions require restorable snapshot_ref and snapshot_hash"
            )
    versions["records"].extend(normalized_versions)

    head_updates = raw_delta.get("head_updates", [])
    if not isinstance(head_updates, list) or not all(
        isinstance(item, dict) for item in head_updates
    ):
        raise ValueError("head_updates must be an object list")
    for record in normalized_versions:
        matching_heads = [
            item
            for item in head_updates
            if item.get("branch_id") == record.get("branch_id")
            and item.get("field_address") == record.get("field_address")
            and item.get("version_id") == record.get("id")
            and item.get("working_closure") == "relative-closed"
        ]
        if len(matching_heads) != 1:
            raise ValueError(
                f"new field version {record.get('id')} requires one matching relative-closed head update"
            )
    for update in head_updates:
        key = (update.get("branch_id"), update.get("field_address"))
        matching = [
            item
            for item in versions["heads"]
            if isinstance(item, dict)
            and (item.get("branch_id"), item.get("field_address")) == key
        ]
        if len(matching) > 1:
            raise ValueError(f"field-version head is duplicated before update: {key}")
        if matching:
            matching[0].update(copy.deepcopy(update))
        else:
            versions["heads"].append(copy.deepcopy(update))

    motion["lineage_ids"] = [item["id"] for item in normalized_lineage]
    motion["result_closure_version_ids"] = [
        item["id"] for item in normalized_versions
    ]
    motion["status"] = "applied"
    motion["applied_at_runtime_version"] = target_version
    update = find_record(dynamics["inbox"], motion["update_id"], "update")
    terminal_classification = motion["classification"] in {
        "external",
        "local-replace",
        "principle-conflict",
    }
    closure_completed = (
        motion["closure_audit"].get("closure_after") == "relative-closed"
        and motion["classification"] != "no-address-residual"
    )
    update["status"] = "resolved" if terminal_classification or closure_completed else "structured"
    return {
        "motion_id": motion["id"],
        "update_id": update["id"],
        "classification": motion["classification"],
        "lineage_ids": copy.deepcopy(motion["lineage_ids"]),
        "result_closure_version_ids": copy.deepcopy(
            motion["result_closure_version_ids"]
        ),
        "update_status": update["status"],
    }


def cmd_update_apply(args: argparse.Namespace) -> int:
    path = Path(args.path)
    original_state = read_state(path)
    errors = validate_state(original_state)
    if errors:
        raise ValueError("; ".join(errors))
    if not is_current_schema(original_state):
        raise ValueError(
            f"schema {schema_version(original_state)} is read-only; apply updates only in schema 2.2"
        )
    require_f0_confirmation(original_state, "UPDATE_RECONCILE")
    state = copy.deepcopy(original_state)
    dynamics = state["address_dynamics"]
    motion = find_record(dynamics["motions"], args.motion_id, "address motion")
    if motion.get("status") != "proposed":
        raise ValueError("only a proposed address motion may be applied")
    delta = parse_json_object(args.address_delta_json, "--address-delta-json")
    dynamics_delta = delta.get("address_dynamics_delta")
    operator = motion["motion_operator"]
    requested_field_update = delta.get("field_update")
    root_contract_changed = isinstance(requested_field_update, dict) and any(
        name in requested_field_update
        and requested_field_update[name] != original_state["field"].get(name)
        for name in ROOT_CONTRACT_FIELDS
    )
    if root_contract_changed and (
        motion.get("classification") != "root-rebuild"
        or motion.get("closure_audit", {}).get("closure_after") != "relative-closed"
    ):
        raise ValueError(
            "a root contract change requires a relatively closed root-rebuild address motion"
        )
    details = apply_joint_motion_delta(
        state, operator, delta, address_motion=motion
    )
    motion["residual_ids"] = list(
        dict.fromkeys(
            [
                *motion.get("residual_ids", []),
                *details.get("new_residual_ids", []),
                *details.get("absorbed_residual_ids", []),
            ]
        )
    )
    if motion["classification"] == "no-address-residual" and not motion["residual_ids"]:
        raise ValueError(
            "no-address-residual must persist at least one active or archived residual"
        )
    motion["evidence_ids"] = list(
        dict.fromkeys(
            [
                *motion.get("evidence_ids", []),
                *[
                    item.get("id")
                    for item in delta.get("evidence", [])
                    if isinstance(item, dict) and nonempty_string(item.get("id"))
                ],
            ]
        )
    )
    target_version = original_state["version"] + 1
    address_details = apply_address_dynamics_delta(
        state, motion, dynamics_delta, target_version
    )
    details["address_dynamics"] = address_details
    if root_contract_changed:
        state["drift"]["baseline"]["root_goal"] = state["field"]["root_goal"]
        state["drift"]["baseline"]["immutable_constraints"] = copy.deepcopy(
            state["field"].get("immutable_constraints", [])
        )
        state["drift"]["baseline"]["version"] = target_version
    decision = delta.get("residual_driven_decision")
    if state.get("field", {}).get("f0_confirmation", {}).get("status") == "required":
        state["execution"]["last_decision"] = (
            decision
            if decision in {
                "FIELD_FORMATION_REQUIRED",
                "HUMAN_CALIBRATION_REQUIRED",
                "REMODEL_REQUIRED",
                "FIELD_ASCENSION_REQUIRED",
            }
            else "FIELD_FORMATION_REQUIRED"
        )
    elif decision is not None:
        if decision not in NEXT_DECISIONS:
            raise ValueError("address motion residual_driven_decision is invalid")
        state["execution"]["last_decision"] = decision
    append_joint_motion_event(
        state,
        original_state,
        operator,
        f"applied {motion['id']} for update {motion['update_id']}",
        motion["assignment"].get("anchor_addresses", [None])[0]
        if motion["assignment"].get("anchor_addresses")
        else None,
        details,
        allow_root_contract_change=root_contract_changed,
    )
    final_errors = validate_state(state)
    if final_errors:
        raise ValueError("; ".join(final_errors))
    write_state(path, state)
    print(f"version {state['version']}: {operator} {motion['id']}")
    print(
        "closure versions: "
        + (", ".join(motion["result_closure_version_ids"]) or "none")
    )
    return 0


def cmd_update_show(args: argparse.Namespace) -> int:
    state = read_state(Path(args.path))
    errors = validate_state(state)
    if errors:
        raise ValueError("; ".join(errors))
    if not is_current_schema(state):
        raise ValueError("update-show requires schema 2.2")
    dynamics = state["address_dynamics"]
    updates = dynamics["inbox"]
    if args.update_id:
        updates = [find_record(updates, args.update_id, "update")]
    if not updates:
        print("no updates")
        return 0
    motion_map = {
        item.get("id"): item for item in dynamics["motions"] if isinstance(item, dict)
    }
    lineage_map = {
        item.get("id"): item for item in dynamics["lineage"] if isinstance(item, dict)
    }

    def endpoint_text(endpoint: dict[str, Any]) -> str:
        version_id = endpoint.get("field_version_id") or "working"
        return (
            f"{endpoint.get('address')}@{version_id}"
            f"#payload-{endpoint.get('payload_revision')}"
        )

    for update in updates:
        print(
            f"{update['id']} {update['intake_address']} status={update['status']} "
            f"source={update['source']['kind']}"
        )
        print(f"  raw: {update['raw_content']}")
        for motion_id in update.get("motion_ids", []):
            motion = motion_map.get(motion_id, {})
            closure = motion.get("closure_audit", {})
            anchors = ", ".join(
                motion.get("assignment", {}).get("anchor_addresses", [])
            ) or "(none)"
            print(
                f"  {motion_id}: {motion.get('classification')} "
                f"status={motion.get('status')} operator={motion.get('motion_operator')} "
                f"branch={motion.get('branch_id')}"
            )
            assignment = motion.get("assignment", {})
            source_versions = ", ".join(
                motion.get("source_field_version_ids", [])
            ) or "(working/no prior closure version)"
            print(f"    source versions: {source_versions}")
            print(
                "    address: "
                f"kind={assignment.get('kind')} modal={assignment.get('modal_status')} "
                f"anchor={anchors}"
            )
            print(
                "    migration request: "
                f"from={assignment.get('from_addresses', [])} "
                f"to={assignment.get('to_addresses', [])}"
            )
            print(f"    rationale: {assignment.get('rationale')}")
            tested_path = [
                item.get("address") or item.get("field_address")
                for item in closure.get("tested", [])
                if isinstance(item, dict)
            ]
            print(
                "    propagation: "
                f"unstable={closure.get('nearest_unstable_ancestor')} "
                f"rebuild={closure.get('minimal_rebuild_root')} "
                f"stop={closure.get('propagation_stop_address')}"
            )
            print(
                "    closure: "
                f"{closure.get('closure_before')} -> {closure.get('closure_after')} "
                f"tested_path={tested_path or '(none)'}"
            )
            for lineage_id in motion.get("lineage_ids", []):
                lineage = lineage_map.get(lineage_id, {})
                sources = ", ".join(
                    endpoint_text(item)
                    for item in lineage.get("from", [])
                    if isinstance(item, dict)
                ) or "∅"
                targets = ", ".join(
                    endpoint_text(item)
                    for item in lineage.get("to", [])
                    if isinstance(item, dict)
                ) or "∅"
                print(
                    f"    lineage {lineage_id} {lineage.get('kind')}: "
                    f"{sources} -> {targets}"
                )
            print(
                "    residuals: "
                + (", ".join(motion.get("residual_ids", [])) or "none")
            )
            print(
                "    closure versions: "
                + (
                    ", ".join(motion.get("result_closure_version_ids", []))
                    or "none"
                )
            )
    print(f"next decision: {state['execution'].get('last_decision')}")
    return 0


def require_f0_confirmation(state: dict[str, Any], operation: str) -> None:
    if schema_version(state) != SCHEMA_JOINT:
        return
    status = state.get("field", {}).get("f0_confirmation", {}).get("status")
    if status not in {"confirmed", "bypassed"}:
        raise ValueError(
            f"{operation} blocked: display the candidate F0 and obtain explicit "
            "confirmation, or record an explicit bypass"
        )


def has_audited_forward_field_formation(state: dict[str, Any]) -> bool:
    """Return whether field formation stabilized the map before F0 confirmation."""
    confirmation_version = (
        state.get("field", {})
        .get("f0_confirmation", {})
        .get("confirmed_at_runtime_version")
    )
    if not isinstance(confirmation_version, int):
        return False
    formation_types = {"FIELD_FORM", "CENTER_ADJUST", "HUMAN_CALIBRATE", "SURVEY"}
    for event in state.get("history", []):
        if not isinstance(event, dict) or event.get("type") not in formation_types:
            continue
        if not isinstance(event.get("version"), int) or event["version"] >= confirmation_version:
            continue
        details = event.get("details")
        if not isinstance(details, dict):
            continue
        source = details.get("source_panorama_version")
        written = details.get("written_panorama_version")
        if (
            details.get("panorama_changed") is True
            and isinstance(source, int)
            and isinstance(written, int)
            and written > source
        ):
            return True
    return False


def f0_confirmation_candidate_issues(state: dict[str, Any]) -> list[str]:
    """Check whether the formed candidate is stable enough to be confirmed as F0."""
    if schema_version(state) != SCHEMA_JOINT:
        return []
    candidate = copy.deepcopy(state)
    candidate["field"]["f0_confirmation"] = {
        "status": "confirmed",
        "confirmed_by": "candidate-gate",
        "confirmed_at_runtime_version": state["version"] + 1,
    }
    return f0_provisional_closure_issues(candidate)


def f0_provisional_closure_issues(state: dict[str, Any]) -> list[str]:
    """Derive why the current F0 cannot yet enter a forward motion."""
    if schema_version(state) != SCHEMA_JOINT:
        return []
    issues: list[str] = []
    field = state.get("field", {})
    confirmation = field.get("f0_confirmation", {}).get("status")
    if confirmation not in {"confirmed", "bypassed"}:
        issues.append("F0 is not confirmed")
    if field.get("contract_status") != "stable-for-execution":
        issues.append("the F0 contract is not stable-for-execution")
    if field.get("human_calibration", {}).get("status") == "required":
        issues.append("human calibration is required")

    panorama = state.get("panorama", {})
    graph = panorama.get("graph", {})
    order = panorama.get("order", {})
    if graph.get("status") != "validated":
        issues.append("the typed functional graph is not validated")
    if order.get("status") != "validated":
        issues.append("the necessary partial order is not validated")
    center = selected_center_record(state)
    if center is None:
        issues.append("no evidence-tested center is selected")
    else:
        if center.get("validity") != "valid":
            issues.append("the selected center is not valid")
        if center.get("minimality_status") != "validated":
            issues.append("the selected center has not passed the minimality tests")
    if not has_audited_forward_field_formation(state):
        issues.append(
            "no audited pre-confirmation forward field-formation motion changed the panorama"
        )

    residuals = panorama.get("residuals", [])
    # An empty ledger is legitimate only after an explicit residual audit; it
    # must not exempt graph/order/center/formation validation above.
    if not residuals:
        return issues
    graph_nodes = {
        item.get("address"): item
        for item in graph.get("nodes", [])
        if isinstance(item, dict) and nonempty_string(item.get("address"))
    }
    expansion_frontier = {
        item.get("address"): item
        for item in panorama.get("frontiers", {}).get("expansion", [])
        if isinstance(item, dict) and nonempty_string(item.get("address"))
    }
    for residual in residuals:
        residual_id = residual.get("id") or "(unidentified residual)"
        if residual.get("modal_status") != "[◇]":
            issues.append(
                f"active residual {residual_id} is {residual.get('modal_status')}, not [◇]"
            )
            continue
        relation = residual.get("address_relation", {})
        if relation.get("kind") != "frontier":
            issues.append(
                f"active residual {residual_id} lacks a verified frontier address"
            )
            continue
        address = relation.get("address")
        if relation.get("gate_status") != "legal":
            issues.append(f"active residual {residual_id} has no legal address gate")
        reach = relation.get("reach", {})
        reach_kind = reach.get("kind")
        if reach_kind not in {"next", "finite-deep"}:
            issues.append(
                f"active residual {residual_id} has unverified reach {reach_kind}; [◇,d=?] cannot close F0"
            )
        if reach_kind == "finite-deep" and (
            not isinstance(reach.get("estimated_expansions"), int)
            or reach.get("estimated_expansions", 0) < 1
        ):
            issues.append(
                f"active residual {residual_id} finite-deep reach lacks a positive expansion bound"
            )
        if reach.get("evidence_status") not in {"explicit", "inferred"}:
            issues.append(
                f"active residual {residual_id} reach is not evidence-supported"
            )
        node = graph_nodes.get(address)
        if not isinstance(node, dict):
            issues.append(
                f"active residual {residual_id} address {address!r} is absent from the realized map"
            )
        elif node.get("validity") != "valid" or node.get("modal_status") != "[◇]":
            issues.append(
                f"active residual {residual_id} address {address!r} is not a valid [◇] graph node"
            )
        else:
            if (
                focus_display_address(state, str(address)) is not None
                and node.get("field_opening_status") != "validated"
            ):
                issues.append(
                    f"active residual {residual_id} address {address!r} is only a child-field hypothesis; [◇,d=?] cannot close F0"
                )
            else:
                for opening_issue in child_field_opening_issues(state, node):
                    issues.append(
                        f"active residual {residual_id} address {address!r} has an invalid child-field opening: {opening_issue}"
                    )
        frontier_item = expansion_frontier.get(address)
        if not isinstance(frontier_item, dict):
            issues.append(
                f"active residual {residual_id} address {address!r} is not retained in the Expansion frontier"
            )
        elif audit_path(state, frontier_item).get("gate_status") != "legal":
            issues.append(
                f"active residual {residual_id} address {address!r} lacks a complete legal root path"
            )
        if residual.get("absorption_status") in {"human-pending", "prohibited"}:
            issues.append(
                f"active residual {residual_id} is {residual.get('absorption_status')}"
            )
    return issues


def require_f0_provisional_closure(state: dict[str, Any], operation: str) -> None:
    issues = f0_provisional_closure_issues(state)
    if issues:
        raise ValueError(
            f"{operation} blocked by the F0 provisional-closure gate: "
            + "; ".join(issues)
        )


def cmd_f0_confirm(args: argparse.Namespace) -> int:
    path = Path(args.path)
    original_state = read_state(path)
    errors = validate_state(original_state)
    if errors:
        raise ValueError("; ".join(errors))
    if not is_current_schema(original_state):
        raise ValueError(
            f"schema {schema_version(original_state)} is read-only; confirm F0 only in schema 2.2"
        )
    if not nonempty_string(args.by):
        raise ValueError("--by must identify the explicit confirmer or bypass source")
    current = original_state["field"]["f0_confirmation"].get("status")
    if current != "required":
        raise ValueError(f"F0 confirmation is already {current}; no state change made")
    if not args.bypass:
        candidate_issues = f0_confirmation_candidate_issues(original_state)
        if candidate_issues:
            raise ValueError(
                "F0 confirmation blocked until the candidate field is formed and auditable: "
                + "; ".join(candidate_issues)
            )

    state = copy.deepcopy(original_state)
    target_version = original_state["version"] + 1
    status = "bypassed" if args.bypass else "confirmed"
    confirmation = {
        "status": status,
        "confirmed_by": args.by,
        "confirmed_at_runtime_version": target_version,
    }
    state["field"]["f0_confirmation"] = confirmation
    state["execution"]["last_decision"] = (
        "FIELD_FORMATION_REQUIRED" if args.bypass else "EXPAND_REQUIRED"
    )
    note = args.note or (
        "F0 confirmation explicitly bypassed"
        if args.bypass
        else "formed F0 explicitly confirmed"
    )
    append_joint_motion_event(
        state,
        original_state,
        "F0_CONFIRM",
        note,
        "F0",
        {"f0_confirmation": copy.deepcopy(confirmation)},
    )
    final_errors = validate_state(state)
    if final_errors:
        raise ValueError("; ".join(final_errors))
    write_state(path, state)
    print(f"version {state['version']}: F0 {status} by {args.by}")
    return 0


def cmd_transition(args: argparse.Namespace) -> int:
    event_type = args.type.upper()
    if event_type not in EVENT_TYPES:
        raise ValueError(
            f"unsupported transition {event_type}; choose from {', '.join(sorted(EVENT_TYPES))}"
        )
    if event_type == "FOCUS":
        raise ValueError("use the focus command for a schema-2.2 Focus motion")
    if event_type in {"UPDATE_INGEST", "UPDATE_STRUCTURE", "UPDATE_RECONCILE"}:
        raise ValueError(
            "use update-receive, update-structure, or update-apply for address-motion maintenance"
        )
    path = Path(args.path)
    original_state = read_state(path)
    errors = validate_state(original_state)
    if errors:
        raise ValueError("; ".join(errors))
    if schema_version(original_state) != SCHEMA_JOINT:
        raise ValueError(
            f"schema {schema_version(original_state)} is read-only; mutate only schema 2.2"
        )
    if event_type in F0_GATED_EVENT_TYPES:
        require_f0_confirmation(original_state, event_type)
    if event_type in F0_PROVISIONAL_CLOSURE_GATED_EVENT_TYPES:
        require_f0_provisional_closure(original_state, event_type)
    if args.residual_audit_json:
        raise ValueError("--residual-audit-json is legacy-only and cannot mutate schema 2.2")

    state = copy.deepcopy(original_state)
    details: dict[str, Any]
    if event_type in RESIDUAL_AUDIT_EVENT_TYPES - {"FOCUS", "EXECUTE"}:
        if not args.motion_delta_json:
            raise ValueError(f"{event_type} requires --motion-delta-json for address and residual audit")
        details = apply_joint_motion_delta(
            state,
            event_type,
            parse_json_object(args.motion_delta_json, "--motion-delta-json"),
        )
        if args.decision:
            if args.decision not in NEXT_DECISIONS:
                raise ValueError("invalid schema-2.2 next-state decision")
            state["execution"]["last_decision"] = args.decision
    elif event_type == "EXECUTE":
        field = state["field"]
        if field.get("human_calibration", {}).get("status") == "required":
            raise ValueError(
                "EXECUTE blocked: human calibration is required for the current field"
            )
        if field.get("contract_status") != "stable-for-execution":
            raise ValueError(
                "EXECUTE blocked: stabilize the root-goal contract before execution"
            )
        if not args.execution_audit_json:
            raise ValueError("EXECUTE requires --execution-audit-json")
        details = apply_joint_execution_audit(
            state,
            parse_json_object(args.execution_audit_json, "--execution-audit-json"),
        )
        if args.decision and args.decision != details["residual_driven_decision"]:
            raise ValueError(
                "--decision must match execution audit residual_driven_decision"
            )
    elif event_type == "INVALIDATE":
        if not args.invalidation_json:
            raise ValueError("INVALIDATE requires --invalidation-json")
        payload = parse_json_object(args.invalidation_json, "--invalidation-json")
        if not payload.get("invalidations"):
            raise ValueError("INVALIDATE requires at least one invalidation record")
        state["panorama"]["map_version"] += 1
        details = propagate_joint_invalidation(
            state, payload.get("invalidations"), motion="INVALIDATE"
        )
        state["execution"]["last_decision"] = payload.get(
            "residual_driven_decision", "REMODEL_REQUIRED"
        )
        if state["execution"]["last_decision"] not in NEXT_DECISIONS:
            raise ValueError("invalidation residual_driven_decision is invalid")
    else:
        forbidden = [
            name
            for name, value in (
                ("--motion-delta-json", args.motion_delta_json),
                ("--execution-audit-json", args.execution_audit_json),
                ("--invalidation-json", args.invalidation_json),
            )
            if value
        ]
        if forbidden:
            raise ValueError(
                f"{event_type} does not accept " + ", ".join(forbidden)
            )
        append_event(state, event_type, args.note, args.address)
        state["field"]["status"] = event_type.lower()
        if args.decision:
            if args.decision not in NEXT_DECISIONS:
                raise ValueError("invalid schema-2.2 next-state decision")
            state["execution"]["last_decision"] = args.decision
        final_errors = validate_state(state)
        if final_errors:
            raise ValueError("; ".join(final_errors))
        write_state(path, state)
        print(f"version {state['version']}: {event_type}")
        return 0

    append_joint_motion_event(
        state,
        original_state,
        event_type,
        args.note,
        args.address,
        details,
    )
    state["field"]["status"] = event_type.lower()
    final_errors = validate_state(state)
    if final_errors:
        raise ValueError("; ".join(final_errors))
    write_state(path, state)
    print(f"version {state['version']}: {event_type}")
    return 0


def parse_json_object(raw: str | None, label: str) -> dict[str, Any]:
    if raw is None:
        return {}
    if raw == "@-":
        raw = sys.stdin.read()
    elif raw.startswith("@"):
        source = Path(raw[1:])
        try:
            raw = source.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"cannot read {label} file {source}: {exc}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must decode to an object")
    return value


def apply_residual_audit(
    state: dict[str, Any], motion: str, raw_audit: dict[str, Any]
) -> dict[str, Any]:
    """Apply a schema-1.3 motion audit and return its event-safe summary."""
    if schema_version(state) != SCHEMA_AUDITED:
        raise ValueError("--residual-audit-json requires schema 1.3")

    panorama = state["panorama"]
    delta_m = raw_audit.get("delta_m_addresses", [])
    delta_r = raw_audit.get("delta_r", [])
    frontier_after = raw_audit.get("frontier_after", [])
    compressed_frontier = raw_audit.get("compressed_frontier_addresses", [])
    precondition_gaps = raw_audit.get("precondition_gaps", [])
    absorbed_outcomes = raw_audit.get("absorbed_outcomes", [])

    if not isinstance(delta_m, list) or not all(
        nonempty_string(address) for address in delta_m
    ):
        raise ValueError("residual audit delta_m_addresses must be a string list")
    missing_realized = sorted(set(delta_m) - set(panorama.get("explored", [])))
    if missing_realized:
        raise ValueError(
            "residual audit delta M addresses are not realized in panorama.explored: "
            + ", ".join(missing_realized)
        )
    if not isinstance(delta_r, list) or not all(
        isinstance(item, dict) for item in delta_r
    ):
        raise ValueError("residual audit delta_r must be a list of residual objects")
    if not isinstance(frontier_after, list) or not all(
        isinstance(item, dict) for item in frontier_after
    ):
        raise ValueError("residual audit frontier_after must be a list of path objects")
    if not isinstance(compressed_frontier, list) or not all(
        nonempty_string(address) for address in compressed_frontier
    ):
        raise ValueError(
            "residual audit compressed_frontier_addresses must be a string list"
        )
    for label, values in (
        ("precondition_gaps", precondition_gaps),
        ("absorbed_outcomes", absorbed_outcomes),
    ):
        if not isinstance(values, list) or not all(
            isinstance(item, dict) for item in values
        ):
            raise ValueError(f"residual audit {label} must be a list of objects")
    for gap in precondition_gaps:
        if gap.get("kind") not in {"missing-input", "unmet-prerequisite"}:
            raise ValueError(
                "residual audit precondition gap kind must be missing-input or unmet-prerequisite"
            )
        if not nonempty_string(gap.get("description")):
            raise ValueError("residual audit precondition gap needs a description")

    existing_residual_ids = {
        item.get("id")
        for item in panorama.get("residuals", [])
        if isinstance(item, dict) and nonempty_string(item.get("id"))
    }
    delta_r_ids: list[str] = []
    for residual in delta_r:
        residual_id = residual.get("id")
        if not nonempty_string(residual_id):
            raise ValueError("residual audit delta R item needs a non-empty id")
        if residual_id in existing_residual_ids:
            raise ValueError(f"residual audit duplicate residual id: {residual_id}")
        produced_by = residual.get("produced_by")
        if not isinstance(produced_by, dict) or produced_by.get("motion") != motion:
            raise ValueError(
                f"residual {residual_id} produced_by.motion must be {motion}"
            )
        existing_residual_ids.add(residual_id)
        delta_r_ids.append(residual_id)

    panorama["frontier"] = copy.deepcopy(frontier_after)
    panorama["residuals"].extend(copy.deepcopy(delta_r))
    normalized = {
        "performed": True,
        "motion": motion,
        "scope": raw_audit.get("scope"),
        "delta_m_addresses": list(delta_m),
        "delta_r_ids": delta_r_ids,
        "frontier_after_addresses": [
            item.get("address") for item in frontier_after
        ],
        "compressed_frontier_addresses": list(compressed_frontier),
        "precondition_gaps": copy.deepcopy(precondition_gaps),
        "absorbed_outcomes": copy.deepcopy(absorbed_outcomes),
        "checks": copy.deepcopy(raw_audit.get("checks")),
        "empty_residual_reason": raw_audit.get("empty_residual_reason"),
        "residual_driven_decision": raw_audit.get("residual_driven_decision"),
    }
    audit_errors = validate_residual_audit(motion, normalized)
    if audit_errors:
        raise ValueError("; ".join(audit_errors))
    return normalized


def apply_focus_delta(
    state: dict[str, Any], delta: dict[str, Any]
) -> dict[str, Any]:
    """Materialize a schema-1.2+ Focus delta before active-path auditing."""
    panorama = state["panorama"]
    order = panorama["order"]
    source_version = panorama["map_version"]
    declared_source = delta.get("source_panorama_version", source_version)
    if declared_source != source_version:
        raise ValueError(
            "focus delta source_panorama_version does not match panorama.map_version"
        )

    nodes = delta.get("nodes", [])
    relations = delta.get("relations", [])
    locked_interfaces = delta.get("locked_interfaces", [])
    for name, values in (
        ("nodes", nodes),
        ("relations", relations),
        ("locked_interfaces", locked_interfaces),
    ):
        if not isinstance(values, list) or not all(
            isinstance(item, dict) for item in values
        ):
            raise ValueError(f"focus delta {name} must be a list of objects")

    existing_nodes = {
        item.get("address")
        for item in order["nodes"]
        if isinstance(item, dict)
    }
    new_addresses: list[str] = []
    for node in nodes:
        address = node.get("address")
        if not nonempty_string(address):
            raise ValueError("focus delta node needs a non-empty address")
        if address in existing_nodes:
            raise ValueError(f"focus delta node already exists: {address}")
        existing_nodes.add(address)
        new_addresses.append(address)
        order["nodes"].append(dict(node))

    existing_relation_ids = {
        item.get("id")
        for item in order["relations"]
        if isinstance(item, dict)
    }
    for relation in relations:
        relation_id = relation.get("id")
        if not nonempty_string(relation_id):
            raise ValueError("focus delta relation needs a non-empty id")
        if relation_id in existing_relation_ids:
            raise ValueError(f"focus delta relation already exists: {relation_id}")
        existing_relation_ids.add(relation_id)
        order["relations"].append(dict(relation))

    locked_addresses: list[str] = []
    compressed = panorama["compressed"]
    compressed_positions = {
        item.get("address"): index
        for index, item in enumerate(compressed)
        if isinstance(item, dict) and nonempty_string(item.get("address"))
    }
    for interface in locked_interfaces:
        address = interface.get("address")
        if not nonempty_string(address):
            raise ValueError("focus locked interface needs a non-empty address")
        updated = dict(interface)
        updated["exposure_status"] = "locked"
        if address in compressed_positions:
            merged = dict(compressed[compressed_positions[address]])
            merged.update(updated)
            compressed[compressed_positions[address]] = merged
        else:
            compressed_positions[address] = len(compressed)
            compressed.append(updated)
        locked_addresses.append(address)

    explored = panorama["explored"]
    for address in new_addresses:
        if address not in explored:
            explored.append(address)

    changed = bool(nodes or relations or locked_interfaces)
    written_version = source_version + 1 if changed else source_version
    panorama["map_version"] = written_version
    return {
        "source_panorama_version": source_version,
        "written_panorama_version": written_version,
        "new_addresses": new_addresses,
        "locked_interface_addresses": locked_addresses,
    }


def cmd_focus(args: argparse.Namespace) -> int:
    path = Path(args.path)
    original_state = read_state(path)
    errors = validate_state(original_state)
    if errors:
        raise ValueError("; ".join(errors))
    if schema_version(original_state) != SCHEMA_JOINT:
        raise ValueError(
            f"schema {schema_version(original_state)} is read-only; mutate only schema 2.2"
        )
    require_f0_confirmation(original_state, "FOCUS")
    require_f0_provisional_closure(original_state, "FOCUS")
    if selected_center_record(original_state) is None:
        raise ValueError(
            "FOCUS blocked: complete field formation and select an evidence-tested center first"
        )
    if args.active_path:
        raise ValueError("schema 2.2 does not accept legacy --active-path strings")
    if args.residual_audit_json:
        raise ValueError("schema 2.2 records residuals inside --focus-delta-json")
    if not args.focus_delta_json:
        raise ValueError("schema 2.2 Focus requires --focus-delta-json")

    state = copy.deepcopy(original_state)
    delta = parse_json_object(args.focus_delta_json, "--focus-delta-json")
    details = apply_joint_motion_delta(state, "FOCUS", delta)
    raw_paths = delta.get("active_paths", [])
    if not isinstance(raw_paths, list) or not all(
        isinstance(item, dict) for item in raw_paths
    ):
        raise ValueError("focus delta active_paths must be a list of objects")
    for raw in args.active_path_json or []:
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid --active-path-json: {exc}") from exc
        if not isinstance(item, dict):
            raise ValueError("--active-path-json must decode to an object")
        raw_paths.append(item)
    active_paths = [
        normalize_joint_path(state, item, modal_status="[◇]") for item in raw_paths
    ]
    nonlegal = [item for item in active_paths if item.get("gate_status") != "legal"]
    if nonlegal:
        reasons = "; ".join(nonlegal[0].get("gate_reasons", []))
        raise ValueError(reasons or "Focus path failed the structural legality gate")
    node_map, _ = joint_graph_indexes(state)
    for item in active_paths:
        node = node_map.get(item.get("address"))
        if node is None or node.get("validity") != "valid" or node.get("modal_status") != "[◇]":
            raise ValueError("Focus active paths must reference valid potential addresses")
    locked_addresses = [
        item.get("address")
        for item in state["panorama"]["frontiers"]["compressed"]
        if isinstance(item, dict) and item.get("exposure_status") == "locked"
    ]
    state["focus"] = {
        "query": args.query,
        "address": args.address,
        "rationale": args.rationale,
        "source": args.source,
        "active_paths": active_paths,
        "penetration": {
            "source_panorama_version": details["source_panorama_version"],
            "written_panorama_version": details["written_panorama_version"],
            "new_addresses": details["new_addresses"],
            "locked_interface_addresses": locked_addresses,
        },
        "status": "active" if active_paths else "unfocused",
    }
    decision = delta.get("residual_driven_decision")
    if decision is not None:
        if decision not in NEXT_DECISIONS:
            raise ValueError("Focus residual_driven_decision is invalid")
        state["execution"]["last_decision"] = decision
    details["active_addresses"] = [item["address"] for item in active_paths]
    append_joint_motion_event(
        state,
        original_state,
        "FOCUS",
        args.rationale or args.query,
        args.address,
        details,
    )
    state["field"]["status"] = "focus"
    final_errors = validate_state(state)
    if final_errors:
        raise ValueError("; ".join(final_errors))
    write_state(path, state)
    print(f"version {state['version']}: FOCUS {args.address or ''}".rstrip())
    return 0

    # Legacy mutation code below is intentionally unreachable. Schemas 1.0-1.3
    # are retained only for validate/summary compatibility.
    path = Path(args.path)
    original_state = read_state(path)
    state = copy.deepcopy(original_state)
    errors = validate_state(state)
    if errors:
        raise ValueError("; ".join(errors))
    if schema_version(state) == SCHEMA_LEGACY:
        if args.active_path_json:
            raise ValueError("--active-path-json requires schema 1.1+")
        if args.focus_delta_json:
            raise ValueError("--focus-delta-json requires schema 1.2 or 1.3")
        if args.residual_audit_json:
            raise ValueError("--residual-audit-json requires schema 1.3")
        state["focus"] = {
            "query": args.query,
            "address": args.address,
            "rationale": args.rationale,
            "source": args.source,
            "active_paths": args.active_path or [],
            "status": "remodel-required",
        }
        append_event(
            state,
            "REMODEL_REQUIRED",
            "schema 1.0 has no auditable dependency order or root ancestry; "
            "reconstruct it in schema 1.1 before Focus",
            args.address,
        )
        state["field"]["status"] = "remodel_required"
        state["execution"]["last_decision"] = "REMODEL_REQUIRED"
        write_state(path, state)
        print(
            f"version {state['version']}: REMODEL_REQUIRED {args.address or ''}".rstrip()
        )
        return 0

    penetration: dict[str, Any] | None = None
    if schema_version(state) in FOCUS_SCHEMAS:
        delta = parse_json_object(args.focus_delta_json, "--focus-delta-json")
        penetration = apply_focus_delta(state, delta)
    elif args.focus_delta_json:
        raise ValueError("--focus-delta-json requires schema 1.2 or 1.3")

    active_paths: list[dict[str, Any]] = []
    for raw in args.active_path_json or []:
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid --active-path-json: {exc}") from exc
        if not isinstance(item, dict):
            raise ValueError("--active-path-json must decode to an object")
        active_paths.append(audit_path(state, item))
    for address in args.active_path or []:
        active_paths.append(
            audit_path(state, {"address": address}, legacy_plain=True)
        )

    nonlegal = [item for item in active_paths if item["gate_status"] != "legal"]
    focus_status = "remodel-required" if nonlegal else "active"
    focus_payload: dict[str, Any] = {
        "query": args.query,
        "address": args.address,
        "rationale": args.rationale,
        "source": args.source,
        "active_paths": active_paths,
        "status": focus_status,
    }
    if penetration is not None:
        focus_payload["penetration"] = penetration
    state["focus"] = focus_payload
    if nonlegal:
        failing = nonlegal[0]
        reasons = "; ".join(failing.get("gate_reasons", []))
        if schema_version(state) in FOCUS_SCHEMAS:
            state = original_state
            map_version = state["panorama"]["map_version"]
            state["focus"] = {
                "query": args.query,
                "address": args.address,
                "rationale": args.rationale,
                "source": args.source,
                "active_paths": [],
                "penetration": {
                    "source_panorama_version": map_version,
                    "written_panorama_version": map_version,
                    "new_addresses": [],
                    "locked_interface_addresses": [],
                },
                "status": "remodel-required",
            }
        append_event(
            state,
            "REMODEL_REQUIRED",
            reasons or "active path failed structural legality gate",
            failing.get("address"),
        )
        state["field"]["status"] = "remodel_required"
        state["execution"]["last_decision"] = "REMODEL_REQUIRED"
        decision = "REMODEL_REQUIRED"
    else:
        residual_audit: dict[str, Any] | None = None
        if schema_version(state) == SCHEMA_AUDITED:
            if not args.residual_audit_json:
                raise ValueError(
                    "schema 1.3 successful Focus requires --residual-audit-json"
                )
            raw_audit = parse_json_object(
                args.residual_audit_json, "--residual-audit-json"
            )
            expected_delta = set(
                penetration.get("new_addresses", []) if penetration else []
            )
            declared_delta = set(raw_audit.get("delta_m_addresses", []))
            if expected_delta != declared_delta:
                raise ValueError(
                    "Focus residual audit delta_m_addresses must equal the Focus write-back delta"
                )
            residual_audit = apply_residual_audit(state, "FOCUS", raw_audit)
        elif args.residual_audit_json:
            raise ValueError("--residual-audit-json requires schema 1.3")
        append_event(
            state,
            "FOCUS",
            args.rationale or args.query,
            args.address,
            residual_audit,
        )
        state["field"]["status"] = "focus"
        if residual_audit is not None:
            state["execution"]["last_decision"] = residual_audit[
                "residual_driven_decision"
            ]
        decision = "FOCUS"

    final_errors = validate_state(state)
    if final_errors:
        raise ValueError("; ".join(final_errors))
    write_state(path, state)
    print(f"version {state['version']}: {decision} {args.address or ''}".rstrip())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a new state without overwriting")
    init.add_argument("path")
    init.add_argument("--name", required=True)
    init.add_argument("--goal", required=True)
    init.add_argument("--success", action="append")
    init.set_defaults(func=cmd_init)

    validate = sub.add_parser("validate", help="validate a state file")
    validate.add_argument("path")
    validate.set_defaults(func=cmd_validate)

    summary = sub.add_parser("summary", help="print a compact state summary")
    summary.add_argument("path")
    summary.set_defaults(func=cmd_summary)

    f0_confirm = sub.add_parser(
        "f0-confirm",
        help="record explicit confirmation or explicit bypass of the displayed F0",
    )
    f0_confirm.add_argument("path")
    f0_confirm.add_argument("--by", required=True)
    f0_confirm.add_argument("--bypass", action="store_true")
    f0_confirm.add_argument("--note")
    f0_confirm.set_defaults(func=cmd_f0_confirm)

    update_receive = sub.add_parser(
        "update-receive", help="preserve a raw update before structural interpretation"
    )
    update_receive.add_argument("path")
    update_receive.add_argument("--text", required=True)
    update_receive.add_argument(
        "--source",
        choices=tuple(sorted(UPDATE_SOURCE_KINDS)),
        default="user",
    )
    update_receive.add_argument("--source-ref")
    update_receive.add_argument("--evidence-id", action="append")
    update_receive.set_defaults(func=cmd_update_receive)

    update_structure = sub.add_parser(
        "update-structure", help="classify a pending update and expose its address motion"
    )
    update_structure.add_argument("path")
    update_structure.add_argument("--update-id", required=True)
    update_structure.add_argument("--structure-json", required=True)
    update_structure.set_defaults(func=cmd_update_structure)

    update_apply = sub.add_parser(
        "update-apply", help="atomically apply one proposed address motion"
    )
    update_apply.add_argument("path")
    update_apply.add_argument("--motion-id", required=True)
    update_apply.add_argument("--address-delta-json", required=True)
    update_apply.set_defaults(func=cmd_update_apply)

    update_show = sub.add_parser(
        "update-show", help="show structured update addresses and propagation"
    )
    update_show.add_argument("path")
    update_show.add_argument("--update-id")
    update_show.set_defaults(func=cmd_update_show)

    transition = sub.add_parser("transition", help="append a model transition")
    transition.add_argument("path")
    transition.add_argument("--type", required=True)
    transition.add_argument("--note", required=True)
    transition.add_argument("--address")
    transition.add_argument("--decision")
    transition.add_argument(
        "--motion-delta-json",
        help="schema 2.2 atomic joint-motion delta with residual audit",
    )
    transition.add_argument(
        "--execution-audit-json",
        help="schema 2.2 atomic execution result and residual audit payload",
    )
    transition.add_argument(
        "--invalidation-json",
        help="schema 2.2 invalidation propagation payload",
    )
    transition.add_argument(
        "--residual-audit-json",
        help="legacy schema-1.3 audit input; legacy states are now read-only",
    )
    transition.set_defaults(func=cmd_transition)

    focus = sub.add_parser("focus", help="set the current Focus and append an event")
    focus.add_argument("path")
    focus.add_argument("--query", required=True)
    focus.add_argument("--address")
    focus.add_argument("--rationale")
    focus.add_argument(
        "--source",
        choices=("user", "evidence", "agent-tentative"),
        default="user",
    )
    focus.add_argument(
        "--active-path",
        action="append",
        help="legacy plain path; ordered schemas do not certify it as legal",
    )
    focus.add_argument(
        "--active-path-json",
        action="append",
        help="schema 1.1+ active-path object with a root_ancestry sub-DAG",
    )
    focus.add_argument(
        "--focus-delta-json",
        help="schema 2.2 joint graph, frontier, center, active-path, and residual delta",
    )
    focus.add_argument(
        "--residual-audit-json",
        help="legacy schema-1.3 input; schema 2.2 stores residuals in the Focus delta",
    )
    focus.set_defaults(func=cmd_focus)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
