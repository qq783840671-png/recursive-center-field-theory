import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


RUNTIME_PATH = Path(__file__).parents[1] / "scripts" / "focus_runtime.py"
SPEC = importlib.util.spec_from_file_location("focus_runtime_v16", RUNTIME_PATH)
RUNTIME = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNTIME)


class TwoStagePotentialSemanticsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp.name) / "state.json"
        args = type("Args", (), {"state": str(self.state_path), "task": "semantic split", "mode": "clarify"})
        self.assertEqual(RUNTIME.cmd_init(args), 0)

    def tearDown(self):
        self.temp.cleanup()

    def call(self, function, payload):
        args = type("Args", (), {"state": str(self.state_path), "payload": json.dumps(payload, ensure_ascii=False)})
        self.assertEqual(function(args), 0)

    def state(self):
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def frame(self):
        self.call(
            RUNTIME.cmd_frame,
            {
                "field_id": "root",
                "contract": {
                    "goal": "separate semantic axes",
                    "boundary": "test",
                    "completion": "node audited",
                    "evidence_standard": "recorded evidence",
                    "constraints": [],
                },
                "closure_gap": "node is unrealized",
                "centers": [
                    {
                        "center_id": "main",
                        "status": "active",
                        "obligation": "close node",
                        "nodes": [{"node_id": "n1", "role": "required position"}],
                    }
                ],
                "selected_center_id": "main",
                "order": [],
                "evidence": ["field calibration"],
            },
        )

    def test_candidate_has_calibration_state_but_no_address_modality(self):
        self.call(
            RUNTIME.cmd_register_candidate,
            {
                "candidate_address_id": "cand-1",
                "proposed_structural_role": "possible child role",
                "evidence": ["hypothesis source"],
            },
        )
        candidate = self.state()["address_candidates"]["cand-1"]
        self.assertEqual(candidate["calibration_status"], "hypothesized")
        self.assertNotIn("modality", candidate)

        self.frame()
        state = self.state()
        address_id = state["fields"]["root"]["node_addresses"]["n1"]
        address = state["addresses"][address_id]
        self.assertEqual(address["calibration_status"], "calibrated")
        self.assertEqual(address["modality"], "[◇]")
        self.call(
            RUNTIME.cmd_resolve_candidate,
            {
                "candidate_address_id": "cand-1",
                "disposition": "calibrated",
                "resulting_address_id": address_id,
                "evidence": ["calibration audit"],
            },
        )
        self.assertEqual(
            self.state()["address_candidates"]["cand-1"]["resulting_address_id"],
            address_id,
        )

    def test_latent_residual_is_not_an_address_and_activation_creates_result(self):
        self.frame()
        self.call(RUNTIME.cmd_execute, {"addresses": ["n1"], "evidence": ["audit"], "result": "done"})
        self.call(
            RUNTIME.cmd_fold,
            {
                "conclusion": "current contract closed",
                "evidence": ["closure audit"],
                "latent_residuals": [
                    {
                        "residual_id": "lambda-1",
                        "description": "future mismatch",
                        "activation_condition": "new counterexample",
                        "address_binding": {"kind": "unaddressed"},
                    }
                ],
                "active_residuals": [],
            },
        )
        state = self.state()
        latent = state["latent_residuals"]["lambda-1"]
        self.assertNotIn("modality", latent)
        self.assertTrue(state["fields"]["root"]["closure_audit"]["field_closure"])

        self.call(
            RUNTIME.cmd_activate_residual,
            {
                "residual_id": "lambda-1",
                "disposition": "active-residual",
                "active_residual_id": "active-1",
                "blocking": True,
                "evidence": ["counterexample E2"],
                "addressing_result": {"modality": "[∅]", "reason": "no current legal route"},
            },
        )
        state = self.state()
        self.assertNotIn("lambda-1", state["latent_residuals"])
        self.assertEqual(state["active_residuals"]["active-1"]["addressing_result"]["modality"], "[∅]")
        self.assertEqual(state["phase"], "blocked")
        self.assertEqual(RUNTIME.validate_state(state), [])


if __name__ == "__main__":
    unittest.main()
