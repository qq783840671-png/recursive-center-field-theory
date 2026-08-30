#!/usr/bin/env python3
"""Validate and preserve Distill merge plans without deciding semantics."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "distill-ledger-1.0"
CLASSIFICATIONS = {"ADD", "REFINE", "REPLACE", "CONTRADICT", "NOOP"}
STATUSES = {"用户明确", "已验证", "工作假设", "模型推断", "待确认", "已替代", "已否定"}
SOURCE_KINDS = {"user-explicit", "verified-artifact", "model-inference", "conversation-summary"}
NON_AUTHORITATIVE_SOURCES = {"model-inference", "conversation-summary"}


class DistillLedgerError(ValueError):
    pass


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DistillLedgerError(f"{label} must be non-empty text")
    return value.strip()


def require_text_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise DistillLedgerError(f"{label} must be a list of non-empty text")
    if not allow_empty and not value:
        raise DistillLedgerError(f"{label} must not be empty")
    return [item.strip() for item in value]


def load_payload(raw: str) -> dict[str, Any]:
    if raw.startswith("@"):
        data = json.loads(Path(raw[1:]).read_text(encoding="utf-8"))
    else:
        data = json.loads(raw)
    if not isinstance(data, dict):
        raise DistillLedgerError("payload must be a JSON object")
    return data


def load_state(path: str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DistillLedgerError("state must be a JSON object")
    return data


def write_state(path: str, state: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(state, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def state_digest(state: dict[str, Any]) -> str:
    payload = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_candidate(raw: Any, known_ids: set[str]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise DistillLedgerError("candidate must be an object")
    candidate_id = require_text(raw.get("candidate_id"), "candidate_id")
    if candidate_id in known_ids:
        raise DistillLedgerError(f"candidate_id is duplicated: {candidate_id}")
    classification = require_text(raw.get("classification"), f"{candidate_id}.classification")
    if classification not in CLASSIFICATIONS:
        raise DistillLedgerError(f"{candidate_id}.classification is invalid")
    status = require_text(raw.get("status"), f"{candidate_id}.status")
    if status not in STATUSES:
        raise DistillLedgerError(f"{candidate_id}.status is invalid")
    source_kind = require_text(raw.get("source_kind"), f"{candidate_id}.source_kind")
    if source_kind not in SOURCE_KINDS:
        raise DistillLedgerError(f"{candidate_id}.source_kind is invalid")
    if source_kind in NON_AUTHORITATIVE_SOURCES and status in {"用户明确", "已验证"}:
        raise DistillLedgerError(f"{candidate_id} promotes a non-authoritative source")
    target_id = raw.get("target_id")
    if classification == "ADD" and target_id is not None:
        raise DistillLedgerError(f"{candidate_id}.ADD must not set target_id")
    if classification != "ADD":
        target_id = require_text(target_id, f"{candidate_id}.target_id")
    relations = raw.get("relations", [])
    if not isinstance(relations, list) or not all(isinstance(item, dict) for item in relations):
        raise DistillLedgerError(f"{candidate_id}.relations must be a list of objects")
    open_edge = raw.get("open_edge")
    if open_edge is not None:
        open_edge = require_text(open_edge, f"{candidate_id}.open_edge")
    return {
        "candidate_id": candidate_id,
        "semantic_key": require_text(raw.get("semantic_key"), f"{candidate_id}.semantic_key"),
        "title": require_text(raw.get("title"), f"{candidate_id}.title"),
        "statement": require_text(raw.get("statement"), f"{candidate_id}.statement"),
        "classification": classification,
        "status": status,
        "source_kind": source_kind,
        "basis": require_text_list(raw.get("basis"), f"{candidate_id}.basis"),
        "target_id": target_id,
        "relations": copy.deepcopy(relations),
        "open_edge": open_edge,
    }


def validate_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version is unsupported")
    if not isinstance(state.get("revision"), int) or state.get("revision", -1) < 0:
        errors.append("revision must be a non-negative integer")
    for field in ("destination", "source_scope", "status"):
        if not isinstance(state.get(field), str) or not state[field].strip():
            errors.append(f"{field} must be non-empty text")
    if state.get("status") not in {"open", "finalized-with-deferred", "finalized"}:
        errors.append("status is invalid")
    candidates = state.get("candidates")
    if not isinstance(candidates, dict):
        errors.append("candidates must be an object")
        candidates = {}
    for candidate_id, candidate in candidates.items():
        try:
            normalized = normalize_candidate(candidate, set())
            if normalized["candidate_id"] != candidate_id:
                errors.append(f"candidate key mismatch: {candidate_id}")
        except DistillLedgerError as exc:
            errors.append(str(exc))
    if not isinstance(state.get("plan_history"), list):
        errors.append("plan_history must be a list")
    if not isinstance(state.get("finalization_history"), list):
        errors.append("finalization_history must be a list")
    return errors


def apply_plan(state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if state.get("status") != "open":
        raise DistillLedgerError("cannot apply a plan to a finalized ledger")
    raw_candidates = payload.get("candidates")
    if not isinstance(raw_candidates, list) or not raw_candidates:
        raise DistillLedgerError("candidates must be a non-empty list")
    result = copy.deepcopy(state)
    known_ids = set(result["candidates"])
    added: list[str] = []
    for raw in raw_candidates:
        candidate = normalize_candidate(raw, known_ids)
        candidate_id = candidate["candidate_id"]
        result["candidates"][candidate_id] = candidate
        known_ids.add(candidate_id)
        added.append(candidate_id)
    result["revision"] += 1
    result["plan_history"].append({
        "revision": result["revision"],
        "candidate_ids": added,
        "evidence": require_text_list(payload.get("evidence"), "plan.evidence"),
    })
    return result


def finalize(state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if state.get("status") != "open":
        raise DistillLedgerError("ledger is already finalized")
    applied = require_text_list(payload.get("applied_candidate_ids", []), "applied_candidate_ids", allow_empty=True)
    deferred = require_text_list(payload.get("deferred_candidate_ids", []), "deferred_candidate_ids", allow_empty=True)
    if set(applied) & set(deferred):
        raise DistillLedgerError("a candidate cannot be both applied and deferred")
    known = set(state["candidates"])
    if not set(applied + deferred).issubset(known):
        raise DistillLedgerError("finalization references an unknown candidate")
    write_bearing = {
        candidate_id
        for candidate_id, candidate in state["candidates"].items()
        if candidate["classification"] != "NOOP"
    }
    if set(applied + deferred) != write_bearing:
        raise DistillLedgerError("every non-NOOP candidate must be applied or deferred")
    if deferred and not payload.get("deferred_reason"):
        raise DistillLedgerError("deferred candidates require deferred_reason")
    result = copy.deepcopy(state)
    result["revision"] += 1
    audit = {
        "revision": result["revision"],
        "destination_hash_before": require_text(payload.get("destination_hash_before"), "destination_hash_before"),
        "destination_hash_after": require_text(payload.get("destination_hash_after"), "destination_hash_after"),
        "applied_candidate_ids": applied,
        "deferred_candidate_ids": deferred,
        "deferred_reason": payload.get("deferred_reason"),
        "section_refs": require_text_list(payload.get("section_refs"), "section_refs"),
        "evidence": require_text_list(payload.get("evidence"), "finalization.evidence"),
    }
    result["finalization_history"].append(audit)
    result["status"] = "finalized-with-deferred" if deferred else "finalized"
    return result


def summary(state: dict[str, Any]) -> dict[str, Any]:
    counts = {classification: 0 for classification in sorted(CLASSIFICATIONS)}
    for candidate in state.get("candidates", {}).values():
        counts[candidate["classification"]] += 1
    return {
        "schema_version": state.get("schema_version"),
        "revision": state.get("revision"),
        "destination": state.get("destination"),
        "status": state.get("status"),
        "counts": counts,
        "state_digest": state_digest(state),
    }


def self_test() -> None:
    state = {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "destination": "knowledge.md",
        "source_scope": "current conversation",
        "status": "open",
        "candidates": {},
        "plan_history": [],
        "finalization_history": [],
    }
    state = apply_plan(state, {"evidence": ["conversation"], "candidates": [{
        "candidate_id": "C1",
        "semantic_key": "field-relative-closure",
        "title": "Relative closure",
        "statement": "Closure remains relative to the active field contract.",
        "classification": "ADD",
        "status": "用户明确",
        "source_kind": "user-explicit",
        "basis": ["conversation"],
    }]})
    state = finalize(state, {
        "destination_hash_before": "before",
        "destination_hash_after": "after",
        "applied_candidate_ids": ["C1"],
        "deferred_candidate_ids": [],
        "section_refs": ["knowledge.md#relative-closure"],
        "evidence": ["post-write audit"],
    })
    errors = validate_state(state)
    if errors:
        raise DistillLedgerError("; ".join(errors))
    print("Distill ledger self-test passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("state")
    init_parser.add_argument("--destination", required=True)
    init_parser.add_argument("--source-scope", required=True)
    for name in ("apply", "finalize"):
        command = subparsers.add_parser(name)
        command.add_argument("state")
        command.add_argument("--payload", required=True)
    for name in ("validate", "summary"):
        command = subparsers.add_parser(name)
        command.add_argument("state")
    subparsers.add_parser("self-test")
    args = parser.parse_args()

    try:
        if args.command == "self-test":
            self_test()
            return 0
        if args.command == "init":
            state = {
                "schema_version": SCHEMA_VERSION,
                "revision": 0,
                "destination": require_text(args.destination, "destination"),
                "source_scope": require_text(args.source_scope, "source_scope"),
                "status": "open",
                "candidates": {},
                "plan_history": [],
                "finalization_history": [],
            }
            write_state(args.state, state)
            print(json.dumps(summary(state), ensure_ascii=False, sort_keys=True))
            return 0
        state = load_state(args.state)
        errors = validate_state(state)
        if errors:
            raise DistillLedgerError("; ".join(errors))
        if args.command == "apply":
            state = apply_plan(state, load_payload(args.payload))
            write_state(args.state, state)
        elif args.command == "finalize":
            state = finalize(state, load_payload(args.payload))
            write_state(args.state, state)
        elif args.command == "validate":
            print("VALID")
            return 0
        print(json.dumps(summary(state), ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, DistillLedgerError) as exc:
        print(f"distill-ledger: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

