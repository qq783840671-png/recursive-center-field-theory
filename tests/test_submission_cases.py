import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SubmissionCasesTest(unittest.TestCase):
    def test_required_positive_and_negative_cases(self) -> None:
        payload = json.loads(
            (ROOT / "evals" / "submission-cases.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(payload["positive"]), 5)
        self.assertEqual(len(payload["negative"]), 3)
        ids = []
        for group in ("positive", "negative"):
            for case in payload[group]:
                self.assertEqual(set(case), {"id", "prompt", "expected"})
                self.assertTrue(all(case.values()))
                ids.append(case["id"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_negative_cases_cover_trigger_noop_and_authority(self) -> None:
        payload = json.loads(
            (ROOT / "evals" / "submission-cases.json").read_text(encoding="utf-8")
        )
        joined = " ".join(case["expected"] for case in payload["negative"])
        self.assertIn("Does not invoke", joined)
        self.assertIn("NOOP", joined)
        self.assertIn("cannot expand", joined)

    def test_positive_cases_cover_orientation_and_question_formation(self) -> None:
        payload = json.loads(
            (ROOT / "evals" / "submission-cases.json").read_text(encoding="utf-8")
        )
        cases = {case["id"]: case for case in payload["positive"]}
        self.assertIn("locate-overloaded-situation", cases)
        self.assertIn("derive-research-question", cases)
        joined = " ".join(case["expected"] for case in cases.values()).lower()
        self.assertIn("functional position", joined)
        self.assertIn("governing question", joined)
        self.assertIn("next evidence", joined)


if __name__ == "__main__":
    unittest.main()
