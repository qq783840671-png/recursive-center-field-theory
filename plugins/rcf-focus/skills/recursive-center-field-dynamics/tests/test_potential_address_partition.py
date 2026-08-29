from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import field_state as fs  # noqa: E402
import test_forward_formation_gate as formation_tests  # noqa: E402


class PotentialAddressPartitionTest(unittest.TestCase):
    @staticmethod
    def latent_residual() -> dict:
        return {
            "id": "LR1",
            "classification": "latent-residual",
            "residual_type": "structural",
            "description": "future precision material",
            "potential_effect_on_f0": "may tighten acceptance after activation",
            "activation_condition": "the parent raises the precision requirement",
            "produced_by": {"motion": "FOCUS", "address": "F0:A1"},
            "modal_status": "[◇]",
            "possible_destination": "downward-expansion",
            "evidence_status": "inferred",
            "activation_status": "latent",
            "address_relation": {
                "kind": "frontier",
                "address": "F0:A1",
                "gate_status": "legal",
                "reach": {
                    "kind": "next",
                    "estimated_expansions": 1,
                    "evidence_status": "inferred",
                },
                "conflict_with": [],
            },
        }

    def test_legacy_expansion_defaults_to_latent_and_required_is_separate(self) -> None:
        state = {
            "panorama": {
                "frontiers": {
                    "expansion": [
                        {"address": "F0:A1"},
                        {
                            "address": "F0:B1",
                            "expansion_requirement": "required",
                        },
                    ]
                }
            }
        }
        self.assertEqual(
            fs.expansion_frontier_counts(state),
            {"required": 1, "latent": 1},
        )

    def test_required_frontier_blocks_closure_but_latent_does_not(self) -> None:
        state = formation_tests.ForwardFormationGateTest.stable_state()
        frontier = state["panorama"]["frontiers"]["expansion"][0]
        frontier["expansion_requirement"] = "latent"
        self.assertEqual(fs.f0_provisional_closure_issues(state), [])
        frontier["expansion_requirement"] = "required"
        issues = fs.f0_provisional_closure_issues(state)
        self.assertTrue(any("required Expansion frontier" in item for item in issues))

    def test_latent_residual_can_coexist_with_relative_closure(self) -> None:
        state = formation_tests.ForwardFormationGateTest.stable_state()
        state["panorama"]["frontiers"]["expansion"][0][
            "expansion_requirement"
        ] = "latent"
        state["panorama"]["latent_residuals"] = [self.latent_residual()]
        self.assertEqual(fs.f0_provisional_closure_issues(state), [])
        self.assertEqual(
            fs.validate_latent_residual_record(
                state["panorama"]["latent_residuals"][0],
                "latent",
            ),
            [],
        )

    def test_activation_moves_latent_record_to_history(self) -> None:
        state = {
            "version": 7,
            "panorama": {
                "latent_residuals": [copy.deepcopy(self.latent_residual())],
                "latent_residual_history": [],
                "residuals": [{"id": "R-ACTIVE-1"}],
            },
        }
        result = fs.transition_latent_residuals(
            state,
            [
                {
                    "id": "LR1",
                    "active_residual_id": "R-ACTIVE-1",
                    "motion": "FOCUS",
                    "reason": "the parent precision requirement was activated",
                    "evidence_ids": ["E1"],
                }
            ],
            [],
        )
        self.assertEqual(result["activated"], ["LR1"])
        self.assertEqual(state["panorama"]["latent_residuals"], [])
        archived = state["panorama"]["latent_residual_history"][0]
        self.assertEqual(archived["activation_status"], "activated")
        self.assertEqual(archived["transitioned_at_version"], 8)
        self.assertEqual(
            archived["transitioned_by"]["active_residual_id"],
            "R-ACTIVE-1",
        )


if __name__ == "__main__":
    unittest.main()
