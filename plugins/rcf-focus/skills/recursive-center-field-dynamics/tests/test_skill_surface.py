import re
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class SkillSurfaceTest(unittest.TestCase):
    def test_frontmatter_and_progressive_loading_surface(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        _, frontmatter, body = text.split("---", 2)
        keys = {
            match.group(1)
            for match in re.finditer(r"^([a-z_]+):", frontmatter, re.MULTILINE)
        }
        self.assertEqual(keys, {"name", "description"})
        self.assertIn("name: recursive-center-field-dynamics", frontmatter)
        self.assertIn("`$focus`", frontmatter)
        self.assertIn("`fous`", frontmatter)
        self.assertIn("parent model retains execution authority", body)
        self.assertIn("FORM → DRIVE → REVISE → FOLD", body)
        self.assertIn("ingest-delta", body)
        self.assertIn("assess-impact", body)
        self.assertIn("NOOP", body)
        self.assertIn("without becoming an authorization gate", body)
        self.assertNotIn("## Mandatory pre-action gate", body)
        self.assertNotIn("stop after Focus-1", body)
        self.assertNotIn("Default to `Global ×0 → Focus ×3`", body)
        self.assertNotIn("Complete the user's task first", body)
        self.assertLess(len(text.splitlines()), 500)

    def test_referenced_runtime_resources_exist(self):
        for relative in (
            "scripts/focus_runtime.py",
            "scripts/field_state.py",
            "references/constructive-loop.md",
            "references/knowledge-revision.md",
            "references/closure-and-invalidation.md",
            "references/field-stack.md",
            "references/state-contract.md",
            "references/two-stage-runtime.md",
            "references/sidecar-runtime.md",
            "references/protocol.md",
            "references/state-schema.md",
            "references/maintenance.md",
            "agents/openai.yaml",
        ):
            self.assertTrue((SKILL_DIR / relative).is_file(), relative)

    def test_openai_yaml_matches_current_skill(self):
        text = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "Focus — Constructive Field Control"', text)
        self.assertIn("$recursive-center-field-dynamics", text)
        self.assertIn("maintain the live field", text)
        self.assertIn("revise closure when evidence changes", text)
        self.assertIn("allow_implicit_invocation: false", text)


if __name__ == "__main__":
    unittest.main()
