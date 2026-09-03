import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from rcf_eval.models import load_run, load_suite
from rcf_eval.runner import run_matrix, select_tasks, split_adapter_command
from rcf_eval.scoring import score_run


class RunnerTests(unittest.TestCase):
    def test_command_split_preserves_executable(self):
        command = split_adapter_command(f'"{sys.executable}" -m rcf_eval.reference_adapter')
        self.assertEqual(sys.executable, command[0])

    def test_task_selection_is_explicit(self):
        suite = load_suite(ROOT / "datasets" / "pilot_tasks.json")
        selected = select_tasks(suite, ["theory-revision"])
        self.assertEqual(["theory-revision"], [task["id"] for task in selected])

    def test_process_adapter_round_trip(self):
        suite = load_suite(ROOT / "datasets" / "pilot_tasks.json")
        command = f"{sys.executable} -m rcf_eval.reference_adapter"
        with tempfile.TemporaryDirectory() as directory:
            paths = run_matrix(
                suite,
                adapter_command=command,
                output_dir=Path(directory),
                seeds=[7],
                condition_ids=["ordinary-none"],
            )
            self.assertEqual(6, len(paths))
            first = load_run(paths[0], suite=suite)
            self.assertTrue(first["synthetic"])
            self.assertEqual(0.0, score_run(suite, first)["metrics"]["drift_rate"])


if __name__ == "__main__":
    unittest.main()
