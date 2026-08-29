from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import field_state as fs  # noqa: E402


class RecursiveFocusExpansionTest(unittest.TestCase):
    @staticmethod
    def node(address: str, parent: str | None, function: str) -> dict:
        result = {
            "node_id": "N-" + address.replace(":", "-").replace(".", "-"),
            "address": address,
            "parent_address": parent,
            "payload_revision": 1,
            "function": function,
            "validity": "valid",
            "modal_status": "[◇]",
        }
        if parent is not None:
            result["field_opening_status"] = "validated"
        return result

    @staticmethod
    def relation(identifier: str, source: str, target: str) -> dict:
        return {
            "id": identifier,
            "source": source,
            "target": target,
            "relation_type": "dependency",
            "necessity": "required",
            "validity": "valid",
        }

    def fixture(self) -> tuple[dict, dict]:
        original = {
            "version": 10,
            "field": {"id": "F0"},
            "panorama": {
                "graph": {
                    "nodes": [
                        self.node("F0:A", "F0", "first required function"),
                        self.node("F0:B", "F0", "second required function"),
                    ],
                    "relations": [self.relation("R-A-B", "F0:A", "F0:B")],
                }
            },
            "recursive_focus": {
                "required_focus_rounds": 3,
                "child_center_width": 3,
                "s0_confirmation_version": 8,
                "current_snapshot_id": "S0",
                "snapshots": [
                    {
                        "state_id": "S0",
                        "focus_round": 0,
                        "source_state_id": None,
                        "active_addresses": ["F0:A", "F0:B"],
                        "active_relations": [
                            {"source": "F0:A", "target": "F0:B", "kind": "center-dependency"}
                        ],
                        "f0_checkpoint_hash": "sha256:" + "0" * 64,
                    }
                ],
            },
        }
        state = copy.deepcopy(original)
        children = []
        relations = list(state["panorama"]["graph"]["relations"])
        for letter in ("A", "B"):
            addresses = [f"F0:{letter}{index}" for index in (1, 2, 3)]
            children.extend(
                self.node(address, f"F0:{letter}", f"{letter} child {index}")
                for index, address in enumerate(addresses, start=1)
            )
            relations.extend(
                [
                    self.relation(f"R-{letter}-{letter}1", f"F0:{letter}", addresses[0]),
                    self.relation(f"R-{letter}1-{letter}2", addresses[0], addresses[1]),
                    self.relation(f"R-{letter}2-{letter}3", addresses[1], addresses[2]),
                ]
            )
        state["panorama"]["graph"]["nodes"].extend(children)
        state["panorama"]["graph"]["relations"] = relations
        return original, state

    def test_one_round_can_expand_multiple_fields_and_preserve_closure(self) -> None:
        original, state = self.fixture()
        delta = {
            "recursive_replacements": [
                {
                    "parent_address": "F0:A",
                    "child_center_addresses": ["F0:A1", "F0:A2", "F0:A3"],
                },
                {
                    "parent_address": "F0:B",
                    "child_center_addresses": ["F0:B1", "F0:B2", "F0:B3"],
                },
            ]
        }
        details: dict = {}
        snapshot = fs.apply_recursive_focus_round(original, state, delta, details)
        self.assertEqual(snapshot["state_id"], "S1")
        self.assertEqual(
            snapshot["active_addresses"],
            ["F0:A1", "F0:A2", "F0:A3", "F0:B1", "F0:B2", "F0:B3"],
        )
        self.assertIn(
            {"source": "F0:A3", "target": "F0:B1", "kind": "preserved-interface", "source_relation_id": None},
            snapshot["active_relations"],
        )
        self.assertEqual(details["recursive_replacement_count"], 2)
        self.assertEqual(details["active_closure_address_count"], 6)

    def test_focus_cannot_cross_an_unformed_level(self) -> None:
        original, state = self.fixture()
        with self.assertRaisesRegex(ValueError, "cannot cross levels"):
            fs.apply_recursive_focus_round(
                original,
                state,
                {
                    "recursive_replacements": [
                        {
                            "parent_address": "F0:A1",
                            "child_center_addresses": ["F0:A1.1", "F0:A1.2", "F0:A1.3"],
                        }
                    ]
                },
                {},
            )

    def test_focus_rejects_parent_interface_drift(self) -> None:
        original, state = self.fixture()
        state["panorama"]["graph"]["nodes"][0]["function"] = "silently changed function"
        with self.assertRaisesRegex(ValueError, "protected parent interface"):
            fs.apply_recursive_focus_round(
                original,
                state,
                {
                    "recursive_replacements": [
                        {
                            "parent_address": "F0:A",
                            "child_center_addresses": ["F0:A1", "F0:A2", "F0:A3"],
                        }
                    ]
                },
                {},
            )


if __name__ == "__main__":
    unittest.main()
