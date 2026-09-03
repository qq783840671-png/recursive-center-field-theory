import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from rcf_eval.models import load_suite
from rcf_eval.reference_adapter import build_reference_run
from rcf_eval.scoring import aggregate_scores, score_run


class ScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = load_suite(ROOT / "datasets" / "pilot_tasks.json")
        cls.task = cls.suite["tasks"][0]

    def make_run(self, condition_id="focus-none", workflow="focus", memory="none", seed=1):
        return build_reference_run(
            {
                "suite_id": self.suite["suite_id"],
                "contract_version": self.suite["contract_version"],
                "task": self.task,
                "condition": {"id": condition_id, "workflow": workflow, "memory": memory},
                "seed": seed,
            }
        )

    def test_reference_run_scores_perfectly(self):
        score = score_run(self.suite, self.make_run())
        self.assertEqual(0.0, score["metrics"]["drift_rate"])
        self.assertEqual(0.0, score["metrics"]["error_rate"])
        self.assertEqual(1, score["metrics"]["rework_count"])
        self.assertEqual(1.0, score["metrics"]["necessary_rework_recall"])
        self.assertEqual(0, score["metrics"]["avoidable_rework_count"])
        self.assertEqual(1.0, score["metrics"]["closure_quality"])
        self.assertEqual(0.0, score["resources"]["tokens"])

    def test_detects_drift_error_rework_and_bad_closure(self):
        run = self.make_run()
        step = run["steps"][3]
        step["state_snapshot"]["goal_refs"] = []
        step["state_snapshot"]["version_ref"] = "theory-v1"
        step["claims"][0]["evidence_refs"] = ["ev:support-a"]
        step["action"]["predecessor_refs"] = []
        step["checks"][0]["passed"] = False
        run["steps"][4]["action"]["key"] = step["action"]["key"]
        run["steps"][4]["rework_of"] = ["theory-revision:event-4"]
        run["final"]["evidence_refs"] = []
        run["final"]["version_ref"] = "theory-v1"
        score = score_run(self.suite, run)
        self.assertGreater(score["metrics"]["drift_rate"], 0)
        self.assertGreater(score["metrics"]["error_rate"], 0)
        self.assertEqual(3, score["metrics"]["rework_count"])
        self.assertLess(score["metrics"]["closure_quality"], 1)

    def test_aggregate_reports_focus_effect_with_direction(self):
        ordinary = self.make_run("ordinary-none", "ordinary", "none", 1)
        focus = self.make_run("focus-none", "focus", "none", 1)
        ordinary["steps"][0]["state_snapshot"]["goal_refs"] = []
        scores = [score_run(self.suite, ordinary), score_run(self.suite, focus)]
        summary = aggregate_scores(scores)
        self.assertLess(summary["focus_effect_by_memory"]["none"]["drift_rate"], 0)
        self.assertEqual(
            0.0,
            summary["focus_effect_by_memory"]["none"]["resources"]["tokens"],
        )
        self.assertTrue(summary["contains_synthetic_runs"])


if __name__ == "__main__":
    unittest.main()
