from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = (
    REPOSITORY_ROOT
    / "examples"
    / "open-source-defect-repair"
    / "payloads"
    / "01-formed-candidate.json"
)
PACKAGED_HELPER = (
    REPOSITORY_ROOT
    / "plugins"
    / "rcf-focus"
    / "skills"
    / "recursive-center-field-dynamics"
    / "scripts"
    / "field_state.py"
)
HELPER = Path(os.environ.get("RCF_FIELD_STATE_HELPER", PACKAGED_HELPER)).resolve()


class PublicExampleTest(unittest.TestCase):
    def run_helper(
        self,
        *arguments: str | Path,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, str(HELPER), *(str(item) for item in arguments)],
            cwd=REPOSITORY_ROOT,
            env=environment,
            check=check,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    @staticmethod
    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def load(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_current_formation_confirmation_and_atomic_gate(self) -> None:
        self.assertTrue(HELPER.is_file())
        self.assertTrue(PAYLOAD.is_file())
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            self.run_helper(
                "init",
                state_path,
                "--name",
                "Open-source defect repair",
                "--goal",
                "Repair a reproducible defect without changing requested behavior",
                "--success",
                "The repair is supported by verification evidence",
            )
            initialized = self.load(state_path)
            self.assertEqual(initialized["schema_version"], "2.2")
            self.assertEqual(
                initialized["execution"]["last_decision"],
                "FIELD_FORMATION_REQUIRED",
            )

            before_illegal_motion = self.digest(state_path)
            illegal_motion = self.run_helper(
                "transition",
                state_path,
                "--type",
                "GLOBAL_EXPAND",
                "--note",
                "must wait for a formed and confirmed F0",
                "--motion-delta-json",
                f"@{PAYLOAD}",
                check=False,
            )
            self.assertNotEqual(illegal_motion.returncode, 0)
            self.assertIn("GLOBAL_EXPAND", illegal_motion.stderr)
            self.assertEqual(before_illegal_motion, self.digest(state_path))

            self.run_helper(
                "transition",
                state_path,
                "--type",
                "FIELD_FORM",
                "--note",
                "form and validate the candidate before confirmation",
                "--motion-delta-json",
                f"@{PAYLOAD}",
                "--decision",
                "F0_CONFIRMATION_REQUIRED",
            )
            formed = self.load(state_path)
            self.assertEqual(
                formed["field"]["f0_confirmation"]["status"], "required"
            )
            self.assertEqual(
                formed["execution"]["last_decision"],
                "F0_CONFIRMATION_REQUIRED",
            )

            checkpoint = self.run_helper("render-checkpoint", state_path)
            self.assertIn("F0", checkpoint.stdout)
            self.run_helper("f0-confirm", state_path, "--by", "example:user")
            confirmed = self.load(state_path)
            self.assertEqual(
                confirmed["field"]["f0_confirmation"]["status"], "confirmed"
            )
            self.assertEqual(confirmed["history"][-1]["type"], "F0_CONFIRM")
            self.run_helper("validate", state_path)

    def test_schema_22_maintenance_surface(self) -> None:
        help_result = self.run_helper("--help")
        for command in (
            "update-receive",
            "update-structure",
            "update-apply",
            "update-show",
        ):
            self.assertIn(command, help_result.stdout)


if __name__ == "__main__":
    unittest.main()
