from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import field_state as fs  # noqa: E402


class AddressMotionTest(unittest.TestCase):
    def run_quietly(self, function, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return function(argparse.Namespace(**kwargs))

    def initialize_confirmed(self, path: Path) -> None:
        self.run_quietly(
            fs.cmd_init,
            path=str(path),
            name="address-motion-test",
            goal="maintain one theory under a stable F0 lineage",
            success=None,
        )
        state = fs.read_state(path)
        self.assertEqual(state["field"]["f0_confirmation"]["status"], "required")
        self.assertEqual(state["execution"]["last_decision"], "FIELD_FORMATION_REQUIRED")
        with self.assertRaises(ValueError):
            fs.require_f0_confirmation(state, "FOCUS")
        with self.assertRaisesRegex(ValueError, "formed and auditable"):
            self.run_quietly(
                fs.cmd_f0_confirm,
                path=str(path),
                by="test:user-confirmation",
                bypass=False,
                note=None,
            )
        state = fs.read_state(path)
        state["field"]["f0_confirmation"] = {
            "status": "confirmed",
            "confirmed_by": "test:preformed-fixture",
            "confirmed_at_runtime_version": state["version"],
        }
        state["execution"]["last_decision"] = "EXPAND_REQUIRED"
        # This maintenance fixture intentionally represents an older confirmed
        # schema-2.2 state without the new S0 recursive Focus surface.
        state.pop("recursive_focus", None)
        fs.write_state(path, state)
        self.assertEqual(fs.validate_state(state), [])

    def test_legacy_display_label_is_not_fabricated_child_field(self) -> None:
        state = {"address_dynamics": {"legacy_display_addresses": ["F0:A1"]}}
        node = {"address": "F0:A1", "modal_status": "[◇]"}
        self.assertEqual(fs.child_field_opening_issues(state, node), [])
        node["modal_status"] = "[+]"
        self.assertIn(
            "legacy display label must remain [◇]",
            fs.child_field_opening_issues(state, node),
        )

    @staticmethod
    def no_address_structure() -> dict:
        return {
            "classification": "no-address-residual",
            "motion_operator": "REBUILD",
            "branch_id": "main",
            "source_field_version_ids": [],
            "assignment": {
                "kind": "no-address",
                "anchor_addresses": [],
                "from_addresses": [],
                "to_addresses": [],
                "modal_status": "[\u2205]",
                "rationale": "reliable update has no legal current theory address",
            },
            "closure_audit": {
                "tested": [],
                "nearest_unstable_ancestor": "F0",
                "minimal_rebuild_root": None,
                "propagation_stop_address": None,
                "closure_before": "unstable",
                "closure_after": "open",
            },
            "residual_ids": [],
            "evidence_ids": [],
        }

    @staticmethod
    def no_address_residual() -> dict:
        return {
            "id": "R1",
            "classification": "true-residual",
            "residual_type": "structural",
            "description": "reliable update has no legal address in the current field",
            "effect_on_f0": "the current closure cannot represent a relevant difference",
            "representation_failure": "nearest-node insertion would distort the current contract",
            "produced_by": {"motion": "REBUILD", "address": "F0"},
            "modal_status": "[\u2205]",
            "possible_destination": "field-ascension",
            "changes_focus_or_execution": {
                "changes": True,
                "reason": "the residual must be located before closure",
            },
            "tolerance_status": "unknown",
            "evidence_status": "explicit",
            "address_relation": {
                "kind": "no-address",
                "address": None,
                "gate_status": "unverified",
                "reach": {
                    "kind": "unknown",
                    "estimated_expansions": None,
                    "evidence_status": "explicit",
                },
                "conflict_with": [],
            },
            "absorption_status": "unresolved",
            "closure_condition": "find a minimal legal reconstruction or externalize the update",
        }

    @staticmethod
    def base_delta(*, residuals: list[dict], field_update=None) -> dict:
        delta = {
            "source_panorama_version": 0,
            "graph_nodes": [],
            "graph_node_updates": [],
            "graph_relations": [],
            "evidence": [],
            "residuals": residuals,
            "absorbed_residuals": [],
            "modal_results": [],
            "realized_addresses": [],
            "frontiers_after": {"action": [], "expansion": [], "compressed": []},
            "graph_status": "tentative",
            "order_status": "tentative",
            "residual_driven_decision": "FIELD_ASCENSION_REQUIRED",
            "address_dynamics_delta": {
                "lineage": [],
                "new_branches": [],
                "new_field_versions": [],
                "head_updates": [],
            },
        }
        if residuals:
            delta["empty_residual_reason"] = None
        else:
            delta["empty_residual_reason"] = "negative smoke case intentionally omitted the required residual"
            delta["field_update"] = field_update or {"phase": "stabilizing"}
        return delta

    def receive_and_structure_no_address(self, path: Path) -> None:
        self.run_quietly(
            fs.cmd_update_receive,
            path=str(path),
            text="a reliable counterexample has no current address",
            source="user",
            source_ref=None,
            evidence_id=None,
        )
        self.run_quietly(
            fs.cmd_update_structure,
            path=str(path),
            update_id="U1",
            structure_json=json.dumps(self.no_address_structure(), ensure_ascii=False),
        )

    def create_base_root_version(self, path: Path) -> None:
        self.run_quietly(
            fs.cmd_update_receive,
            path=str(path),
            text="form the first relatively closed root version",
            source="user",
            source_ref=None,
            evidence_id=None,
        )
        structure = {
            "classification": "root-rebuild",
            "motion_operator": "REBUILD",
            "branch_id": "main",
            "source_field_version_ids": [],
            "assignment": {
                "kind": "subtree",
                "anchor_addresses": ["F0"],
                "from_addresses": ["F0"],
                "to_addresses": ["F0"],
                "modal_status": "[+]",
                "rationale": "establish the first closed root payload",
            },
            "closure_audit": {
                "tested": [{"address": "F0", "result": "relative-closed"}],
                "nearest_unstable_ancestor": "F0",
                "minimal_rebuild_root": "F0",
                "propagation_stop_address": None,
                "closure_before": "open",
                "closure_after": "relative-closed",
            },
            "residual_ids": [],
            "evidence_ids": [],
        }
        self.run_quietly(
            fs.cmd_update_structure,
            path=str(path),
            update_id="U1",
            structure_json=json.dumps(structure, ensure_ascii=False),
        )
        delta = {
            "source_panorama_version": 0,
            "graph_nodes": [],
            "graph_node_updates": [
                {
                    "address": "F0",
                    "payload_revision": 2,
                    "function": "versioned root field",
                }
            ],
            "graph_relations": [],
            "evidence": [],
            "residuals": [],
            "absorbed_residuals": [],
            "modal_results": [],
            "realized_addresses": [],
            "frontiers_after": {"action": [], "expansion": [], "compressed": []},
            "empty_residual_reason": "the base root version passed its closure audit",
            "graph_status": "tentative",
            "order_status": "tentative",
            "address_dynamics_delta": {
                "lineage": [
                    {
                        "id": "L-base",
                        "kind": "payload-replace",
                        "from": [
                            {
                                "node_id": "N-F0",
                                "field_version_id": None,
                                "address": "F0",
                                "payload_revision": 1,
                            }
                        ],
                        "to": [
                            {
                                "node_id": "N-F0",
                                "field_version_id": "FV-main-F0-1",
                                "address": "F0",
                                "payload_revision": 2,
                            }
                        ],
                        "reason": "the stable root address receives its first closed payload",
                        "evidence_ids": [],
                    }
                ],
                "new_branches": [],
                "new_field_versions": [
                    {
                        "id": "FV-main-F0-1",
                        "branch_id": "main",
                        "field_address": "F0",
                        "ordinal": 1,
                        "parent_ids": [],
                        "closure_status": "relative-closed",
                        "absorbed_update_ids": ["U1"],
                        "absorbed_residual_ids": [],
                        "lineage_ids": ["L-base"],
                        "reused_addresses": ["F0"],
                    }
                ],
                "head_updates": [
                    {
                        "branch_id": "main",
                        "field_address": "F0",
                        "version_id": "FV-main-F0-1",
                        "working_closure": "relative-closed",
                        "destabilized_by_motion_ids": [],
                    }
                ],
            },
        }
        self.run_quietly(
            fs.cmd_update_apply,
            path=str(path),
            motion_id="AM1",
            address_delta_json=json.dumps(delta, ensure_ascii=False),
        )

    def test_no_address_stays_unresolved_and_accepts_next_motion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            self.initialize_confirmed(path)
            self.receive_and_structure_no_address(path)
            self.run_quietly(
                fs.cmd_update_apply,
                path=str(path),
                motion_id="AM1",
                address_delta_json=json.dumps(
                    self.base_delta(residuals=[self.no_address_residual()]),
                    ensure_ascii=False,
                ),
            )
            state = fs.read_state(path)
            self.assertEqual(state["address_dynamics"]["inbox"][0]["status"], "structured")
            self.assertEqual(state["address_dynamics"]["motions"][0]["status"], "applied")

            root_rebuild = {
                "classification": "root-rebuild",
                "motion_operator": "REBUILD",
                "branch_id": "main",
                "source_field_version_ids": [],
                "assignment": {
                    "kind": "subtree",
                    "anchor_addresses": ["F0"],
                    "from_addresses": ["F0"],
                    "to_addresses": ["F0"],
                    "modal_status": "[+]",
                    "rationale": "the unresolved residual now requires root-scope reconstruction",
                },
                "closure_audit": {
                    "tested": [{"address": "F0", "result": "still-open"}],
                    "nearest_unstable_ancestor": "F0",
                    "minimal_rebuild_root": "F0",
                    "propagation_stop_address": None,
                    "closure_before": "unstable",
                    "closure_after": "open",
                },
                "residual_ids": ["R1"],
                "evidence_ids": [],
            }
            self.run_quietly(
                fs.cmd_update_structure,
                path=str(path),
                update_id="U1",
                structure_json=json.dumps(root_rebuild, ensure_ascii=False),
            )
            state = fs.read_state(path)
            self.assertEqual(len(state["address_dynamics"]["motions"]), 2)
            self.assertEqual(state["address_dynamics"]["motions"][1]["status"], "proposed")
            with self.assertRaises(ValueError):
                self.run_quietly(
                    fs.cmd_update_structure,
                    path=str(path),
                    update_id="U1",
                    structure_json=json.dumps(root_rebuild, ensure_ascii=False),
                )

    def test_no_address_without_residual_rolls_back(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            self.initialize_confirmed(path)
            self.receive_and_structure_no_address(path)
            before = fs.read_state(path)
            with self.assertRaisesRegex(ValueError, "must persist at least one"):
                self.run_quietly(
                    fs.cmd_update_apply,
                    path=str(path),
                    motion_id="AM1",
                    address_delta_json=json.dumps(
                        self.base_delta(residuals=[], field_update={"phase": "stabilizing"}),
                        ensure_ascii=False,
                    ),
                )
            self.assertEqual(fs.read_state(path), before)

    def test_local_replace_and_counterexample_classification(self) -> None:
        local = {
            "classification": "local-replace",
            "motion_operator": "UPDATE_RECONCILE",
            "assignment": {
                "kind": "existing",
                "anchor_addresses": ["F0:G2"],
                "from_addresses": ["F0:G2"],
                "to_addresses": ["F0:G2"],
                "modal_status": "[\u25c7]",
                "rationale": "role, dependency, scope, and interface remain equivalent",
            },
            "closure_audit": {
                "tested": [],
                "nearest_unstable_ancestor": None,
                "minimal_rebuild_root": None,
                "propagation_stop_address": "F0:G",
                "closure_before": "relative-closed",
                "closure_after": "relative-closed",
            },
        }
        fs.validate_update_structure_semantics(local)

        no_address = self.no_address_structure()
        fs.validate_update_structure_semantics(no_address)
        wrong = json.loads(json.dumps(no_address))
        wrong["classification"] = "principle-conflict"
        with self.assertRaises(ValueError):
            fs.validate_update_structure_semantics(wrong)

    def test_version_branch_creates_two_heads_without_rewriting_panorama(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            self.initialize_confirmed(path)
            self.create_base_root_version(path)
            base_state = fs.read_state(path)
            self.assertEqual(base_state["panorama"]["map_version"], 1)

            self.run_quietly(
                fs.cmd_update_receive,
                path=str(path),
                text="preserve two supported but incomparable root closures",
                source="user",
                source_ref=None,
                evidence_id=None,
            )
            structure = {
                "classification": "version-branch",
                "motion_operator": "SPLIT",
                "branch_id": "main",
                "source_field_version_ids": ["FV-main-F0-1"],
                "assignment": {
                    "kind": "subtree",
                    "anchor_addresses": ["F0"],
                    "from_addresses": ["F0"],
                    "to_addresses": ["F0"],
                    "modal_status": "[+]",
                    "rationale": "both closures preserve the root identity but remain incomparable",
                },
                "closure_audit": {
                    "tested": [
                        {"address": "F0", "result": "two-incomparable-closures"}
                    ],
                    "nearest_unstable_ancestor": "F0",
                    "minimal_rebuild_root": "F0",
                    "propagation_stop_address": None,
                    "closure_before": "unstable",
                    "closure_after": "relative-closed",
                },
                "residual_ids": [],
                "evidence_ids": [],
            }
            self.run_quietly(
                fs.cmd_update_structure,
                path=str(path),
                update_id="U2",
                structure_json=json.dumps(structure, ensure_ascii=False),
            )
            delta = {
                "source_panorama_version": 1,
                "graph_nodes": [],
                "graph_node_updates": [],
                "graph_relations": [],
                "evidence": [],
                "residuals": [],
                "absorbed_residuals": [],
                "modal_results": [],
                "realized_addresses": [],
                "frontiers_after": {"action": [], "expansion": [], "compressed": []},
                "empty_residual_reason": "both branch closures are explicitly represented",
                "graph_status": "tentative",
                "order_status": "tentative",
                "address_dynamics_delta": {
                    "lineage": [
                        {
                            "id": "L-alpha",
                            "kind": "retain",
                            "from": [
                                {
                                    "node_id": "N-F0",
                                    "field_version_id": "FV-main-F0-1",
                                    "address": "F0",
                                    "payload_revision": 2,
                                }
                            ],
                            "to": [
                                {
                                    "node_id": "N-F0",
                                    "field_version_id": "FV-alpha-F0-1",
                                    "address": "F0",
                                    "payload_revision": 2,
                                }
                            ],
                            "reason": "alpha retains the stable root address",
                            "evidence_ids": [],
                        },
                        {
                            "id": "L-beta",
                            "kind": "retain",
                            "from": [
                                {
                                    "node_id": "N-F0",
                                    "field_version_id": "FV-main-F0-1",
                                    "address": "F0",
                                    "payload_revision": 2,
                                }
                            ],
                            "to": [
                                {
                                    "node_id": "N-F0",
                                    "field_version_id": "FV-beta-F0-1",
                                    "address": "F0",
                                    "payload_revision": 2,
                                }
                            ],
                            "reason": "beta retains the stable root address",
                            "evidence_ids": [],
                        },
                    ],
                    "new_branches": [
                        {
                            "id": "alpha",
                            "parent_branch_id": "main",
                            "status": "active",
                        },
                        {
                            "id": "beta",
                            "parent_branch_id": "main",
                            "status": "active",
                        },
                    ],
                    "new_field_versions": [
                        {
                            "id": "FV-alpha-F0-1",
                            "branch_id": "alpha",
                            "field_address": "F0",
                            "ordinal": 1,
                            "parent_ids": ["FV-main-F0-1"],
                            "closure_status": "relative-closed",
                            "absorbed_update_ids": ["U2"],
                            "absorbed_residual_ids": [],
                            "lineage_ids": ["L-alpha"],
                            "reused_addresses": ["F0"],
                            "snapshot_ref": "snapshots/alpha.json",
                            "snapshot_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                        },
                        {
                            "id": "FV-beta-F0-1",
                            "branch_id": "beta",
                            "field_address": "F0",
                            "ordinal": 1,
                            "parent_ids": ["FV-main-F0-1"],
                            "closure_status": "relative-closed",
                            "absorbed_update_ids": ["U2"],
                            "absorbed_residual_ids": [],
                            "lineage_ids": ["L-beta"],
                            "reused_addresses": ["F0"],
                            "snapshot_ref": "snapshots/beta.json",
                            "snapshot_hash": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                        },
                    ],
                    "head_updates": [
                        {
                            "branch_id": "alpha",
                            "field_address": "F0",
                            "version_id": "FV-alpha-F0-1",
                            "working_closure": "relative-closed",
                            "destabilized_by_motion_ids": [],
                        },
                        {
                            "branch_id": "beta",
                            "field_address": "F0",
                            "version_id": "FV-beta-F0-1",
                            "working_closure": "relative-closed",
                            "destabilized_by_motion_ids": [],
                        },
                    ],
                },
            }
            self.run_quietly(
                fs.cmd_update_apply,
                path=str(path),
                motion_id="AM2",
                address_delta_json=json.dumps(delta, ensure_ascii=False),
            )
            state = fs.read_state(path)
            self.assertEqual(fs.validate_state(state), [])
            self.assertEqual(state["panorama"]["map_version"], 1)
            self.assertEqual(
                {item["version_id"] for item in state["address_dynamics"]["field_versions"]["heads"]},
                {"FV-main-F0-1", "FV-alpha-F0-1", "FV-beta-F0-1"},
            )

    def test_root_goal_change_requires_closed_root_version_and_reconfirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            self.initialize_confirmed(path)
            self.create_base_root_version(path)
            self.run_quietly(
                fs.cmd_update_receive,
                path=str(path),
                text="revise the root acceptance contract without changing the F0 lineage",
                source="user",
                source_ref=None,
                evidence_id=None,
            )
            structure = {
                "classification": "root-rebuild",
                "motion_operator": "REBUILD",
                "branch_id": "main",
                "source_field_version_ids": ["FV-main-F0-1"],
                "assignment": {
                    "kind": "subtree",
                    "anchor_addresses": ["F0"],
                    "from_addresses": ["F0"],
                    "to_addresses": ["F0"],
                    "modal_status": "[+]",
                    "rationale": "the acceptance contract changes but the constitutive lineage remains traceable",
                },
                "closure_audit": {
                    "tested": [{"address": "F0", "result": "relative-closed"}],
                    "nearest_unstable_ancestor": "F0",
                    "minimal_rebuild_root": "F0",
                    "propagation_stop_address": None,
                    "closure_before": "unstable",
                    "closure_after": "relative-closed",
                },
                "residual_ids": [],
                "evidence_ids": [],
            }
            self.run_quietly(
                fs.cmd_update_structure,
                path=str(path),
                update_id="U2",
                structure_json=json.dumps(structure, ensure_ascii=False),
            )
            delta = {
                "source_panorama_version": 1,
                "graph_nodes": [],
                "graph_node_updates": [
                    {
                        "address": "F0",
                        "payload_revision": 3,
                        "function": "revised versioned root field",
                    }
                ],
                "graph_relations": [],
                "evidence": [],
                "residuals": [],
                "absorbed_residuals": [],
                "modal_results": [],
                "realized_addresses": [],
                "frontiers_after": {"action": [], "expansion": [], "compressed": []},
                "empty_residual_reason": "the revised root contract passed closure audit",
                "graph_status": "tentative",
                "order_status": "tentative",
                "field_update": {
                    "root_goal": "revised root acceptance contract",
                    "f0_confirmation": {
                        "status": "required",
                        "confirmed_by": None,
                        "confirmed_at_runtime_version": None,
                    },
                },
                "address_dynamics_delta": {
                    "lineage": [
                        {
                            "id": "L-root-2",
                            "kind": "payload-replace",
                            "from": [
                                {
                                    "node_id": "N-F0",
                                    "field_version_id": "FV-main-F0-1",
                                    "address": "F0",
                                    "payload_revision": 2,
                                }
                            ],
                            "to": [
                                {
                                    "node_id": "N-F0",
                                    "field_version_id": "FV-main-F0-2",
                                    "address": "F0",
                                    "payload_revision": 3,
                                }
                            ],
                            "reason": "the root address remains F0 while its contract payload changes",
                            "evidence_ids": [],
                        }
                    ],
                    "new_branches": [],
                    "new_field_versions": [
                        {
                            "id": "FV-main-F0-2",
                            "branch_id": "main",
                            "field_address": "F0",
                            "ordinal": 2,
                            "parent_ids": ["FV-main-F0-1"],
                            "closure_status": "relative-closed",
                            "absorbed_update_ids": ["U2"],
                            "absorbed_residual_ids": [],
                            "lineage_ids": ["L-root-2"],
                            "reused_addresses": ["F0"],
                        }
                    ],
                    "head_updates": [
                        {
                            "branch_id": "main",
                            "field_address": "F0",
                            "version_id": "FV-main-F0-2",
                            "working_closure": "relative-closed",
                            "destabilized_by_motion_ids": [],
                        }
                    ],
                },
            }
            self.run_quietly(
                fs.cmd_update_apply,
                path=str(path),
                motion_id="AM2",
                address_delta_json=json.dumps(delta, ensure_ascii=False),
            )
            state = fs.read_state(path)
            self.assertEqual(fs.validate_state(state), [])
            self.assertEqual(state["field"]["root_goal"], "revised root acceptance contract")
            self.assertEqual(state["field"]["f0_confirmation"]["status"], "required")
            self.assertEqual(state["execution"]["last_decision"], "FIELD_FORMATION_REQUIRED")
            self.assertEqual(
                state["address_dynamics"]["field_versions"]["heads"][0]["version_id"],
                "FV-main-F0-2",
            )
            with self.assertRaisesRegex(ValueError, "explicit confirmation"):
                fs.require_f0_confirmation(fs.read_state(path), "EXECUTE")
            self.assertEqual(fs.validate_state(fs.read_state(path)), [])


if __name__ == "__main__":
    unittest.main()
