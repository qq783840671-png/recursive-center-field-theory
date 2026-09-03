import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from rcf_eval.adapters.codex_cli_adapter import (
    focus_ledger,
    graph_memory,
    lexical_memory,
    memory_payload,
    normalize_response,
    public_event_delta,
)
from rcf_eval.models import load_suite
from rcf_eval.reference_adapter import build_reference_run


class CodexAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = load_suite(ROOT / "datasets" / "pilot_tasks.json")
        cls.task = cls.suite["tasks"][0]

    def history(self):
        request = {
            "suite_id": self.suite["suite_id"],
            "contract_version": self.suite["contract_version"],
            "task": self.task,
            "condition": {"id": "focus-rag", "workflow": "focus", "memory": "rag"},
            "seed": 1,
        }
        run = build_reference_run(request)
        return [
            {
                "event": public_event_delta(self.task, index),
                "response": {
                    **step,
                    "inheritance": run["final"]["inheritance"],
                },
            }
            for index, step in enumerate(run["steps"][:4])
        ]

    def test_public_delta_does_not_repeat_unchanged_root(self):
        first = public_event_delta(self.task, 0)
        second = public_event_delta(self.task, 1)
        self.assertIn("goal:theory-revision", first["introduced_goal_refs"])
        self.assertNotIn("goal:theory-revision", second["introduced_goal_refs"])
        self.assertNotIn("required_predecessor_refs", second)

    def test_public_delta_exposes_invalidation_when_it_arrives(self):
        delta = public_event_delta(self.task, 3)
        self.assertEqual(["ev:support-a"], delta["invalidated_evidence_refs"])
        self.assertEqual("theory-v2", delta["version_update"])

    def test_each_memory_condition_has_distinct_payload(self):
        history = self.history()
        delta = public_event_delta(self.task, 4)
        ordinary_none = memory_payload(
            {"id": "ordinary-none", "workflow": "ordinary", "memory": "none"},
            history,
            delta,
        )
        ordinary_rag = memory_payload(
            {"id": "ordinary-rag", "workflow": "ordinary", "memory": "rag"},
            history,
            delta,
        )
        ordinary_kg = memory_payload(
            {"id": "ordinary-kg", "workflow": "ordinary", "memory": "kg"},
            history,
            delta,
        )
        focus_none = memory_payload(
            {"id": "focus-none", "workflow": "focus", "memory": "none"},
            history,
            delta,
        )
        self.assertEqual({"recent_window"}, set(ordinary_none))
        self.assertIn("retrieved_history", ordinary_rag)
        self.assertIn("knowledge_graph", ordinary_kg)
        self.assertIn("focus_ledger", focus_none)

    def test_lexical_graph_and_focus_memory_are_nonempty(self):
        history = self.history()
        delta = public_event_delta(self.task, 4)
        self.assertTrue(lexical_memory(history, delta["prompt"]))
        self.assertTrue(graph_memory(history, delta)["nodes"])
        self.assertTrue(focus_ledger(history)["action_lineage"])

    def test_response_boundary_removes_duplicate_refs(self):
        response = self.history()[0]["response"]
        response["state_snapshot"]["constraint_refs"] *= 2
        normalized = normalize_response(response)
        refs = normalized["state_snapshot"]["constraint_refs"]
        self.assertEqual(len(refs), len(set(refs)))


if __name__ == "__main__":
    unittest.main()
