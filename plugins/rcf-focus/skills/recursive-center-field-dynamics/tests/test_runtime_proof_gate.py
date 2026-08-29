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


class RuntimeProofGateTest(unittest.TestCase):
    def run_quietly(self, function, **kwargs):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            function(argparse.Namespace(**kwargs))
        return output.getvalue()

    @staticmethod
    def child_snapshot(
        field_id: str,
        parent_address: str,
        *,
        validated: bool,
    ) -> dict:
        contract = "stable-for-execution" if validated else "provisional"
        graph_status = "validated" if validated else "tentative"
        order_status = "validated" if validated else "tentative"
        center_status = "validated" if validated else "selected"
        recursive_status = "validated" if validated else "hypothesized"
        return_status = "valid" if validated else "tentative"
        candidates = (
            [{"id": "C-K1", "members": ["F0"], "minimality_status": "validated"}]
            if validated
            else []
        )
        return {
            "field": {
                "field_id": field_id,
                "local_root": "F0",
                "parent_address": parent_address,
                "contract_status": contract,
            },
            "graph": {
                "status": graph_status,
                "nodes": [{"address": "F0"}],
                "relations": [],
            },
            "order": {
                "status": order_status,
                "nodes": ["F0"],
                "relations": [],
            },
            "center": {
                "status": center_status,
                "selected": "C-K1" if validated else None,
                "candidates": candidates,
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

    @classmethod
    def opening_audit(
        cls,
        field_id: str,
        parent_address: str,
        *,
        validated: bool,
        evidence_ids: list[str],
    ) -> dict:
        snapshot = cls.child_snapshot(
            field_id,
            parent_address,
            validated=validated,
        )
        return {
            "field_id": field_id,
            "local_root": "F0",
            "parent_address": parent_address,
            "contract_status": (
                "stable-for-execution" if validated else "provisional"
            ),
            "graph_status": "validated" if validated else "tentative",
            "order_status": "validated" if validated else "tentative",
            "center_status": "validated" if validated else "selected",
            "recursive_structure_status": (
                "validated" if validated else "hypothesized"
            ),
            "residual_audit_status": "performed",
            "return_interface_status": "valid" if validated else "tentative",
            "state_ref": f"memory://{field_id}",
            "state_snapshot": snapshot,
            "state_hash": fs.child_snapshot_hash(snapshot),
            "evidence_ids": evidence_ids,
        }

    @staticmethod
    def path(address: str, nodes: list[str], relations: list[str]) -> dict:
        return {
            "address": address,
            "modal_status": "[◇]",
            "structural_necessity": "optional",
            "root_ancestry": {
                "root_address": "F0",
                "node_addresses": nodes,
                "relation_ids": relations,
                "compressed_ancestor_addresses": [],
            },
        }

    @staticmethod
    def center_update() -> dict:
        tests = {
            name: {
                "status": "not-applicable",
                "rationale": "the test fixture exposes one irreducible center chain",
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
        }
        return {
            "status": "selected",
            "candidates": [
                {
                    "id": "K-F0-A",
                    "members": ["F0", "F0:A"],
                    "relation_ids": ["R-F0-A"],
                    "closure_targets": ["F0:A"],
                    "minimality_status": "validated",
                    "tests": tests,
                    "evidence_status": "explicit",
                    "validity": "valid",
                }
            ],
            "selected": "K-F0-A",
            "selection_reason": "the required F0 to A chain is the test center",
            "selection_evidence": ["E-A"],
        }

    def initialize_formed_confirmed(self, path: Path) -> None:
        self.run_quietly(
            fs.cmd_init,
            path=str(path),
            name="runtime-proof-test",
            goal="derive the final Focus result only from recorded field motion",
            success=None,
        )
        formation_path = self.path(
            "F0:A1",
            ["F0", "F0:A", "F0:A1"],
            ["R-F0-A", "R-A-A1"],
        )
        delta = {
            "source_panorama_version": 0,
            "graph_nodes": [
                {
                    "node_id": "N-F0-A",
                    "address": "F0:A",
                    "parent_address": "F0",
                    "payload_revision": 1,
                    "function": "minimum load-bearing task function",
                    "evidence_status": "explicit",
                    "evidence_ids": ["E-A"],
                    "validity": "valid",
                    "modal_status": "[+]",
                },
                {
                    "node_id": "N-F0-A1",
                    "address": "F0:A1",
                    "parent_address": "F0:A",
                    "payload_revision": 1,
                    "function": "eligible recursive opening",
                    "evidence_status": "explicit",
                    "evidence_ids": ["E-A1"],
                    "validity": "valid",
                    "modal_status": "[◇]",
                    "field_opening_status": "validated",
                    "field_opening_audit": self.opening_audit(
                        "CF-F0-A1-v1",
                        "F0:A",
                        validated=True,
                        evidence_ids=["E-A1"],
                    ),
                },
            ],
            "graph_relations": [
                {
                    "id": "R-F0-A",
                    "source": "F0",
                    "target": "F0:A",
                    "relation_type": "dependency",
                    "necessity": "required",
                    "evidence_status": "explicit",
                    "evidence_ids": ["E-R0"],
                    "validity": "valid",
                },
                {
                    "id": "R-A-A1",
                    "source": "F0:A",
                    "target": "F0:A1",
                    "relation_type": "dependency",
                    "necessity": "required",
                    "evidence_status": "explicit",
                    "evidence_ids": ["E-R1"],
                    "validity": "valid",
                },
            ],
            "realized_addresses": [],
            "frontiers_after": {
                "action": [],
                "expansion": [formation_path],
                "compressed": [],
            },
            "residuals": [],
            "absorbed_residuals": [],
            "empty_residual_reason": (
                "the formed test field retains every unresolved legal direction in its expansion frontier"
            ),
            "modal_results": [],
            "evidence": [
                {"id": "E-A", "evidence_status": "explicit", "description": "center node evidence"},
                {"id": "E-A1", "evidence_status": "explicit", "description": "opening evidence"},
                {"id": "E-R0", "evidence_status": "explicit", "description": "root dependency evidence"},
                {"id": "E-R1", "evidence_status": "explicit", "description": "opening dependency evidence"},
            ],
            "graph_status": "validated",
            "order_status": "validated",
            "center_update": self.center_update(),
            "field_update": {
                "status": "field_form",
                "phase": "execution-stable",
                "contract_status": "stable-for-execution",
            },
        }
        self.run_quietly(
            fs.cmd_transition,
            path=str(path),
            type="FIELD_FORM",
            note="form the auditable runtime-proof fixture",
            motion_delta_json=json.dumps(delta),
            residual_audit_json=None,
            execution_audit_json=None,
            invalidation_json=None,
            decision="F0_CONFIRMATION_REQUIRED",
            address=None,
        )
        checkpoint = self.run_quietly(
            fs.cmd_render_checkpoint,
            path=str(path),
        )
        self.assertIn("前沿：必要◇0 / 普通◇1", checkpoint)
        self.assertIn("剩余：潜在Λ0 / 活动◇0 / -0 / ∅0", checkpoint)
        self.assertIn("F0_CONFIRMATION_REQUIRED", checkpoint)
        self.run_quietly(
            fs.cmd_f0_confirm,
            path=str(path),
            by="test:user",
            bypass=False,
            note=None,
        )

    def test_result_requires_real_motion_and_derives_counts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            self.initialize_formed_confirmed(path)
            with self.assertRaisesRegex(ValueError, "RUNTIME_PROOF_REQUIRED"):
                self.run_quietly(
                    fs.cmd_render_result,
                    path=str(path),
                    result="narrative-only completion",
                )
            with self.assertRaisesRegex(ValueError, "RUNTIME_PROOF_REQUIRED"):
                self.run_quietly(
                    fs.cmd_focus,
                    path=str(path),
                    query="narrative Focus without a run profile",
                    address=None,
                    rationale=None,
                    source="user",
                    active_path=None,
                    active_path_json=None,
                    focus_delta_json="{}",
                    residual_audit_json=None,
                )

            self.run_quietly(
                fs.cmd_run_open,
                path=str(path),
                mode="inquiry",
                global_count=0,
                focus_count=1,
            )
            state = fs.read_state(path)
            child_addresses = ["F0:A1", "F0:A2", "F0:A3"]
            child_paths = [
                self.path("F0:A1", ["F0", "F0:A", "F0:A1"], ["R-F0-A", "R-A-A1"]),
                self.path(
                    "F0:A2",
                    ["F0", "F0:A", "F0:A1", "F0:A2"],
                    ["R-F0-A", "R-A-A1", "R-A1-A2"],
                ),
                self.path(
                    "F0:A3",
                    ["F0", "F0:A", "F0:A1", "F0:A2", "F0:A3"],
                    ["R-F0-A", "R-A-A1", "R-A1-A2", "R-A2-A3"],
                ),
            ]
            focus_delta = {
                "source_panorama_version": state["panorama"]["map_version"],
                "graph_nodes": [
                    {
                        "node_id": f"N-F0-A{index}",
                        "address": f"F0:A{index}",
                        "parent_address": "F0:A",
                        "payload_revision": 1,
                        "function": f"child center position A{index}",
                        "evidence_status": "explicit",
                        "evidence_ids": [f"E-A{index}"],
                        "validity": "valid",
                        "modal_status": "[◇]",
                        "field_opening_status": "validated",
                        "field_opening_audit": self.opening_audit(
                            f"CF-F0-A{index}-v1",
                            "F0:A",
                            validated=True,
                            evidence_ids=[f"E-A{index}"],
                        ),
                    }
                    for index in (2, 3)
                ],
                "graph_node_updates": [],
                "graph_relations": [
                    {
                        "id": relation_id,
                        "source": source,
                        "target": target,
                        "relation_type": "dependency",
                        "necessity": "required",
                        "evidence_status": "explicit",
                        "evidence_ids": [evidence_id],
                        "validity": "valid",
                    }
                    for relation_id, source, target, evidence_id in (
                        ("R-A1-A2", "F0:A1", "F0:A2", "E-R12"),
                        ("R-A2-A3", "F0:A2", "F0:A3", "E-R23"),
                    )
                ],
                "realized_addresses": [],
                "frontiers_after": {
                    "action": [],
                    "expansion": [],
                    "compressed": [],
                },
                "residuals": [],
                "absorbed_residuals": [],
                "empty_residual_reason": (
                    "the Focus opening passed its child-field proof without exposing an unabsorbed difference"
                ),
                "modal_results": [],
                "evidence": [
                    {
                        "id": evidence_id,
                        "evidence_status": "explicit",
                        "description": description,
                    }
                    for evidence_id, description in (
                        ("E-A2", "second child center evidence"),
                        ("E-A3", "third child center evidence"),
                        ("E-R12", "first child-center dependency"),
                        ("E-R23", "second child-center dependency"),
                    )
                ],
                "graph_status": "validated",
                "order_status": "validated",
                "center_update": None,
                "field_update": None,
                "active_paths": child_paths,
                "recursive_replacements": [
                    {
                        "parent_address": "F0:A",
                        "child_center_addresses": child_addresses,
                    }
                ],
                "residual_driven_decision": "F0_COMPLETE",
            }
            self.run_quietly(
                fs.cmd_focus,
                path=str(path),
                query="replace A with its validated three-position child center",
                address="F0:A",
                rationale="perform one auditable recursive center substitution",
                source="user",
                active_path=None,
                active_path_json=None,
                focus_delta_json=json.dumps(focus_delta),
                residual_audit_json=None,
            )
            output = self.run_quietly(
                fs.cmd_render_result,
                path=str(path),
                result="runtime proof completed",
            )
            self.assertIn("运动：Focus ×1（S0→S1）", output)
            self.assertIn(
                "地址：生成 2 条，验证 2 条，必要待展开 0 条，普通待展开 0 条",
                output,
            )
            self.assertIn("必要待展开 0 条，普通待展开", output)
            self.assertIn("剩余：潜在Λ0 / 活动◇0 / -0 / ∅0", output)
            self.assertIn("决策：F0_COMPLETE", output)
            final_state = fs.read_state(path)
            self.assertEqual(
                final_state["execution"]["motion_profile"]["status"], "rendered"
            )
            self.assertEqual(final_state["history"][-1]["type"], "RUN_RENDER")
            self.assertEqual(fs.validate_state(final_state), [])


if __name__ == "__main__":
    unittest.main()
