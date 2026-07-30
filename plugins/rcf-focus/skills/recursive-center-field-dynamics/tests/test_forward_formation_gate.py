from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import field_state as fs  # noqa: E402


class ForwardFormationGateTest(unittest.TestCase):
    @staticmethod
    def child_snapshot(
        *,
        field_id: str = "CF-F0-A1-v1",
        parent_address: str = "F0:A",
        contract_status: str = "stable-for-execution",
        graph_status: str = "validated",
        order_status: str = "validated",
        center_status: str = "validated",
        recursive_status: str = "validated",
        return_status: str = "valid",
    ) -> dict:
        return {
            "field": {
                "field_id": field_id,
                "local_root": "F0",
                "parent_address": parent_address,
                "contract_status": contract_status,
            },
            "graph": {
                "status": graph_status,
                "nodes": [{"address": "F0"}, {"address": "F0:A"}],
                "relations": [
                    {
                        "id": "C-R1",
                        "source": "F0",
                        "target": "F0:A",
                        "relation_type": "dependency",
                        "necessity": "required",
                    }
                ],
            },
            "order": {
                "status": order_status,
                "nodes": ["F0", "F0:A"],
                "relations": [
                    {"id": "C-R1", "predecessor": "F0", "successor": "F0:A"}
                ],
            },
            "center": {
                "status": center_status,
                "selected": "C-K1" if center_status == "validated" else None,
                "candidates": (
                    [
                        {
                            "id": "C-K1",
                            "members": ["F0", "F0:A"],
                            "minimality_status": "validated",
                        }
                    ]
                    if center_status == "validated"
                    else []
                ),
            },
            "recursive_structure_status": recursive_status,
            "frontiers": {"action": [], "expansion": [], "compressed": []},
            "residuals": [],
            "residual_audit": {"status": "performed"},
            "return_interface": {
                "status": return_status,
                "parent_address": parent_address,
            },
        }

    @staticmethod
    def stable_state() -> dict:
        child_snapshot = ForwardFormationGateTest.child_snapshot()
        nodes = [
            {
                "address": "F0",
                "function": "root",
                "evidence_status": "explicit",
                "validity": "valid",
                "modal_status": "[+]",
            },
            {
                "address": "F0:A",
                "function": "necessary center function",
                "evidence_status": "explicit",
                "validity": "valid",
                "modal_status": "[+]",
            },
            {
                "address": "F0:A1",
                "function": "reachable potential absorption address",
                "evidence_status": "inferred",
                "validity": "valid",
                "modal_status": "[◇]",
                "parent_address": "F0:A",
                "field_opening_status": "validated",
                "field_opening_audit": {
                    "field_id": "CF-F0-A1-v1",
                    "local_root": "F0",
                    "parent_address": "F0:A",
                    "contract_status": "stable-for-execution",
                    "graph_status": "validated",
                    "order_status": "validated",
                    "center_status": "validated",
                    "recursive_structure_status": "validated",
                    "residual_audit_status": "performed",
                    "return_interface_status": "valid",
                    "state_ref": "memory://CF-F0-A1-v1",
                    "state_snapshot": child_snapshot,
                    "state_hash": fs.child_snapshot_hash(child_snapshot),
                    "evidence_ids": ["E1"],
                },
            },
        ]
        relations = [
            {
                "id": "R0A",
                "predecessor": "F0",
                "successor": "F0:A",
                "necessity": "required",
            },
            {
                "id": "RA1",
                "predecessor": "F0:A",
                "successor": "F0:A1",
                "necessity": "required",
            },
        ]
        expansion = {
            "address": "F0:A1",
            "display_address": "A1",
            "modal_status": "[◇]",
            "structural_necessity": "optional",
            "focus_depth": 1,
            "root_ancestry": {
                "root_address": "F0",
                "node_addresses": ["F0", "F0:A", "F0:A1"],
                "relation_ids": ["R0A", "RA1"],
                "compressed_ancestor_addresses": [],
            },
            "required_predecessors": ["F0", "F0:A"],
            "dependency_readiness": "ready",
            "gate_status": "legal",
            "gate_reasons": [],
        }
        return {
            "schema_version": fs.SCHEMA_JOINT,
            "version": 3,
            "field": {
                "id": "F0",
                "legal_roots": ["F0"],
                "contract_status": "stable-for-execution",
                "f0_confirmation": {
                    "status": "confirmed",
                    "confirmed_at_runtime_version": 3,
                },
                "human_calibration": {"status": "not-required"},
            },
            "center": {
                "selected": "C1",
                "candidates": [
                    {
                        "id": "C1",
                        "members": ["F0", "F0:A"],
                        "relation_ids": ["R0A"],
                        "validity": "valid",
                        "minimality_status": "validated",
                    }
                ],
            },
            "panorama": {
                "graph": {"status": "validated", "nodes": nodes},
                "order": {
                    "status": "validated",
                    "nodes": nodes,
                    "relations": relations,
                },
                "frontiers": {
                    "action": [],
                    "expansion": [expansion],
                    "compressed": [],
                },
                "residuals": [
                    {
                        "id": "RES-1",
                        "modal_status": "[◇]",
                        "address_relation": {
                            "kind": "frontier",
                            "address": "F0:A1",
                            "gate_status": "legal",
                            "reach": {
                                "kind": "next",
                                "estimated_expansions": 1,
                                "evidence_status": "explicit",
                            },
                        },
                        "absorption_status": "unresolved",
                    }
                ],
            },
            "history": [
                {
                    "version": 2,
                    "type": "FIELD_FORM",
                    "details": {
                        "source_panorama_version": 0,
                        "written_panorama_version": 1,
                        "panorama_changed": True,
                    },
                }
            ],
            "evidence": [{"id": "E1"}],
        }

    def test_verified_forward_formation_and_reachable_potential_can_close(self) -> None:
        self.assertEqual(fs.f0_provisional_closure_issues(self.stable_state()), [])

    def test_confirmation_without_forward_formation_cannot_close(self) -> None:
        state = self.stable_state()
        state["history"] = []
        self.assertTrue(
            any(
                "forward field-formation" in issue
                for issue in fs.f0_provisional_closure_issues(state)
            )
        )

    def test_hypothesized_unknown_reach_is_not_a_closing_potential(self) -> None:
        state = self.stable_state()
        relation = state["panorama"]["residuals"][0]["address_relation"]
        relation["kind"] = "hypothesized"
        relation["gate_status"] = "unverified"
        relation["reach"]["kind"] = "unknown"
        issues = fs.f0_provisional_closure_issues(state)
        self.assertTrue(any("verified frontier address" in issue for issue in issues))

    def test_missing_predecessor_or_reversed_path_cannot_close(self) -> None:
        state = self.stable_state()
        frontier = state["panorama"]["frontiers"]["expansion"][0]
        frontier["root_ancestry"]["node_addresses"] = ["F0", "F0:A1"]
        frontier["root_ancestry"]["relation_ids"] = ["RA1"]
        issues = fs.f0_provisional_closure_issues(state)
        self.assertTrue(any("complete legal root path" in issue for issue in issues))

    def test_unvalidated_center_cannot_close(self) -> None:
        state = copy.deepcopy(self.stable_state())
        state["center"]["candidates"][0]["minimality_status"] = "unvalidated"
        issues = fs.f0_provisional_closure_issues(state)
        self.assertTrue(any("minimality tests" in issue for issue in issues))

    def test_generated_address_without_child_field_audit_cannot_close(self) -> None:
        state = self.stable_state()
        state["panorama"]["graph"]["nodes"][2].pop("field_opening_audit")
        issues = fs.f0_provisional_closure_issues(state)
        self.assertTrue(any("child-field opening" in issue for issue in issues))

    def test_tampered_child_snapshot_cannot_close(self) -> None:
        state = self.stable_state()
        audit = state["panorama"]["graph"]["nodes"][2]["field_opening_audit"]
        audit["state_snapshot"]["field"]["field_id"] = "tampered"
        issues = fs.f0_provisional_closure_issues(state)
        self.assertTrue(any("state_hash" in issue for issue in issues))

    def test_forming_child_may_remain_potential_but_cannot_close_or_execute(self) -> None:
        state = self.stable_state()
        node = state["panorama"]["graph"]["nodes"][2]
        node["field_opening_status"] = "forming"
        snapshot = self.child_snapshot(
            contract_status="provisional",
            graph_status="tentative",
            order_status="tentative",
            center_status="selected",
            recursive_status="forming",
            return_status="tentative",
        )
        audit = node["field_opening_audit"]
        audit.update(
            {
                "contract_status": "provisional",
                "graph_status": "tentative",
                "order_status": "tentative",
                "center_status": "selected",
                "recursive_structure_status": "forming",
                "return_interface_status": "tentative",
                "state_snapshot": snapshot,
                "state_hash": fs.child_snapshot_hash(snapshot),
            }
        )
        self.assertEqual(fs.child_field_opening_issues(state, node), [])
        self.assertTrue(
            any("child-field hypothesis" in issue for issue in fs.f0_provisional_closure_issues(state))
        )
        action_audit = fs.audit_path(
            state,
            state["panorama"]["frontiers"]["expansion"][0],
            require_action_ready=True,
        )
        self.assertEqual(action_audit["gate_status"], "illegal")

    def test_unformed_initial_state_cannot_be_confirmed_without_explicit_bypass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            with contextlib.redirect_stdout(io.StringIO()):
                fs.cmd_init(
                    argparse.Namespace(
                        path=str(path),
                        name="formation-before-confirmation",
                        goal="confirm only an audited F0",
                        success=None,
                    )
                )
            before = fs.read_state(path)
            with self.assertRaisesRegex(ValueError, "formed and auditable"):
                with contextlib.redirect_stdout(io.StringIO()):
                    fs.cmd_f0_confirm(
                        argparse.Namespace(
                            path=str(path),
                            by="test:user",
                            bypass=False,
                            note=None,
                        )
                    )
            self.assertEqual(fs.read_state(path), before)

    def test_audited_formed_candidate_can_be_confirmed_normally(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            with contextlib.redirect_stdout(io.StringIO()):
                fs.cmd_init(
                    argparse.Namespace(
                        path=str(path),
                        name="formed-candidate",
                        goal="lock only a formed F0",
                        success=None,
                    )
                )
                delta = {
                    "source_panorama_version": 0,
                    "graph_nodes": [],
                    "graph_node_updates": [
                        {"address": "F0", "function": "formed root contract"}
                    ],
                    "graph_relations": [],
                    "realized_addresses": [],
                    "frontiers_after": {
                        "action": [],
                        "expansion": [],
                        "compressed": [],
                    },
                    "residuals": [],
                    "absorbed_residuals": [],
                    "empty_residual_reason": "the complete one-node formation has no unabsorbed difference at this test tolerance",
                    "modal_results": [],
                    "evidence": [],
                    "graph_status": "validated",
                    "order_status": "validated",
                    "center_update": {
                        "status": "selected",
                        "candidates": [
                            {
                                "id": "K-F0",
                                "members": ["F0"],
                                "relation_ids": [],
                                "closure_targets": ["F0"],
                                "minimality_status": "validated",
                                "tests": {
                                    name: {
                                        "status": "not-applicable",
                                        "rationale": "the test field contains only its irreducible root contract",
                                        "evidence_ids": [],
                                    }
                                    for name in (
                                        "deletion",
                                        "replacement",
                                        "reordering",
                                        "compression",
                                        "closure",
                                        "cycle",
                                        "hollow_abstraction",
                                    )
                                },
                                "evidence_status": "explicit",
                                "validity": "valid",
                            }
                        ],
                        "selected": "K-F0",
                        "selection_reason": "the root contract is the complete test center",
                        "selection_evidence": [],
                    },
                    "field_update": {
                        "status": "field_form",
                        "phase": "execution-stable",
                        "contract_status": "stable-for-execution",
                    },
                }
                fs.cmd_transition(
                    argparse.Namespace(
                        path=str(path),
                        type="FIELD_FORM",
                        note="form and validate the candidate before confirmation",
                        motion_delta_json=json.dumps(delta),
                        residual_audit_json=None,
                        execution_audit_json=None,
                        invalidation_json=None,
                        decision="F0_CONFIRMATION_REQUIRED",
                        address=None,
                    )
                )
                fs.cmd_f0_confirm(
                    argparse.Namespace(
                        path=str(path),
                        by="test:user",
                        bypass=False,
                        note=None,
                    )
                )
            state = fs.read_state(path)
            self.assertEqual(state["field"]["f0_confirmation"]["status"], "confirmed")
            self.assertEqual(state["history"][-1]["type"], "F0_CONFIRM")
            self.assertEqual(state["execution"]["last_decision"], "EXPAND_REQUIRED")
            self.assertEqual(fs.validate_state(state), [])

    def test_unbounded_finite_deep_claim_cannot_close(self) -> None:
        state = self.stable_state()
        reach = state["panorama"]["residuals"][0]["address_relation"]["reach"]
        reach["kind"] = "finite-deep"
        reach["estimated_expansions"] = None
        issues = fs.f0_provisional_closure_issues(state)
        self.assertTrue(any("positive expansion bound" in issue for issue in issues))

    def test_validated_graph_cannot_use_unbound_semantic_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            with contextlib.redirect_stdout(io.StringIO()):
                fs.cmd_init(
                    argparse.Namespace(
                        path=str(path),
                        name="evidence-binding-test",
                        goal="reject self-certified structure",
                        success=None,
                    )
                )
            state = fs.read_state(path)
            state["panorama"]["graph"]["nodes"].append(
                {
                    "node_id": "N-A",
                    "address": "F0:A",
                    "parent_address": "F0",
                    "payload_revision": 1,
                    "function": "unsupported claimed function",
                    "evidence_status": "explicit",
                    "validity": "valid",
                    "modal_status": "[◇]",
                }
            )
            state["panorama"]["graph"]["relations"].append(
                {
                    "id": "D-A",
                    "source": "F0",
                    "target": "F0:A",
                    "relation_type": "dependency",
                    "necessity": "required",
                    "evidence_status": "explicit",
                    "validity": "valid",
                }
            )
            state["panorama"]["graph"]["status"] = "validated"
            fs.rebuild_joint_order(state, "FIELD_FORM", order_status="validated")
            errors = fs.validate_state(state)
            self.assertTrue(any("needs evidence_ids" in error for error in errors))

    def test_numeric_recursive_node_requires_child_field_certificate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            with contextlib.redirect_stdout(io.StringIO()):
                fs.cmd_init(
                    argparse.Namespace(
                        path=str(path),
                        name="child-certificate-test",
                        goal="reject suffix-only recursion",
                        success=None,
                    )
                )
            state = fs.read_state(path)
            state["panorama"]["graph"]["nodes"].append(
                {
                    "node_id": "N-A1",
                    "address": "F0:A1",
                    "parent_address": "F0",
                    "payload_revision": 1,
                    "function": "claimed child field",
                    "evidence_status": "tentative",
                    "validity": "valid",
                    "modal_status": "[◇]",
                    "field_opening_status": "hypothesized",
                }
            )
            fs.rebuild_joint_order(state, "GLOBAL_EXPAND", order_status="tentative")
            errors = fs.validate_state(state)
            self.assertTrue(any("field_opening_audit" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
