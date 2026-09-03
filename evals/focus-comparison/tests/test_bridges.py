import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from rcf_eval.bridges.deepeval_bridge import to_conversational_test_case
from rcf_eval.bridges.inspect_ai_bridge import build_dataset
from rcf_eval.models import load_suite
from rcf_eval.reference_adapter import build_reference_run


class OptionalBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = load_suite(ROOT / "datasets" / "pilot_tasks.json")

    def test_inspect_bridge_or_actionable_missing_error(self):
        if importlib.util.find_spec("inspect_ai") is not None:
            self.assertEqual(36, len(build_dataset(self.suite, seeds=[1])))
        else:
            with self.assertRaisesRegex(RuntimeError, "Inspect AI is not installed"):
                build_dataset(self.suite, seeds=[1])

    def test_deepeval_bridge_or_actionable_missing_error(self):
        request = {
            "suite_id": self.suite["suite_id"],
            "contract_version": self.suite["contract_version"],
            "task": self.suite["tasks"][0],
            "condition": {"id": "focus-none", "workflow": "focus", "memory": "none"},
            "seed": 1,
        }
        run = build_reference_run(request)
        if importlib.util.find_spec("deepeval") is not None:
            case = to_conversational_test_case(self.suite, run)
            self.assertEqual(16, len(case.turns))
        else:
            with self.assertRaisesRegex(RuntimeError, "DeepEval is not installed"):
                to_conversational_test_case(self.suite, run)


if __name__ == "__main__":
    unittest.main()
