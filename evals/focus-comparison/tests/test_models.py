import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from rcf_eval.models import CONDITIONS, EvalDataError, load_suite, validate_run
from rcf_eval.reference_adapter import build_reference_run


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = load_suite(ROOT / "datasets" / "pilot_tasks.json")

    def request(self):
        return {
            "suite_id": self.suite["suite_id"],
            "contract_version": self.suite["contract_version"],
            "task": self.suite["tasks"][0],
            "condition": {"id": "focus-none", "workflow": "focus", "memory": "none"},
            "seed": 1,
        }

    def test_pilot_has_six_long_horizon_tasks_and_capability_map(self):
        self.assertEqual(6, len(self.suite["tasks"]))
        self.assertTrue(all(len(task["events"]) >= 8 for task in self.suite["tasks"]))
        self.assertEqual(8, len(self.suite["capabilities"]))
        self.assertTrue(all("capability_ids" in task for task in self.suite["tasks"]))
        self.assertEqual(9, len(CONDITIONS))

    def test_reference_run_is_valid(self):
        validate_run(build_reference_run(self.request()), suite=self.suite)

    def test_rejects_condition_label_mismatch(self):
        run = build_reference_run(self.request())
        run["condition"]["memory"] = "rag"
        with self.assertRaises(EvalDataError):
            validate_run(run, suite=self.suite)

    def test_rejects_event_reordering(self):
        run = build_reference_run(self.request())
        run["steps"][0], run["steps"][1] = run["steps"][1], run["steps"][0]
        with self.assertRaises(EvalDataError):
            validate_run(run, suite=self.suite)

    def test_suite_is_plain_json(self):
        payload = json.loads((ROOT / "datasets" / "pilot_tasks.json").read_text(encoding="utf-8"))
        self.assertEqual("focus-eval-suite-1.1", payload["schema_version"])


if __name__ == "__main__":
    unittest.main()
