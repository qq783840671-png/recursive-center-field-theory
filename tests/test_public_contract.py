import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugin"
SKILL = PLUGIN / "skills" / "focus"


class PublicContractTest(unittest.TestCase):
    def test_one_plugin_contains_one_skill(self) -> None:
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual([item["name"] for item in marketplace["plugins"]], ["focus-field"])
        self.assertEqual(marketplace["plugins"][0]["source"]["path"], "./plugin")
        skills = {path.name for path in (PLUGIN / "skills").iterdir() if path.is_dir()}
        self.assertEqual(skills, {"focus"})

    def test_skill_is_concise_and_routed(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: focus", text)
        self.assertIn("FORM → DRIVE → REVISE → FOLD", text)
        self.assertIn("governing question", text)
        self.assertIn("NOOP", text)
        self.assertLess(len(text), 9000)
        for name in (
            "constructive-loop.md",
            "state-contract.md",
            "knowledge-revision.md",
            "closure-and-invalidation.md",
            "field-stack.md",
        ):
            self.assertTrue((SKILL / "references" / name).is_file(), name)
        self.assertTrue((SKILL / "scripts" / "focus_runtime.py").is_file())
        self.assertFalse((SKILL / "scripts" / "field_state.py").exists())

    def test_manifest_has_public_metadata(self) -> None:
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "focus-field")
        self.assertEqual(manifest["version"], "0.5.0-alpha.1")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertIn("problem-framing", manifest["keywords"])
        interface = manifest["interface"]
        for key in (
            "displayName",
            "shortDescription",
            "longDescription",
            "websiteURL",
            "privacyPolicyURL",
            "termsOfServiceURL",
            "composerIcon",
            "logo",
            "screenshots",
        ):
            self.assertTrue(interface.get(key), key)
        for relative in (
            interface["composerIcon"],
            interface["logo"],
            *interface["screenshots"],
        ):
            self.assertTrue((PLUGIN / relative).is_file(), relative)

    def test_readme_is_product_first_and_honest(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Focus Field\n"))
        self.assertIn("Know where you are. Ask what matters.", text)
        self.assertIn("governing question", text)
        self.assertIn("## Install", text)
        self.assertIn("## Try it", text)
        self.assertIn("Use Focus:", text)
        self.assertIn("NOOP", text)
        self.assertIn("do **not** establish", text)
        self.assertIn("0.5.0-alpha.1", text)

    def test_core_is_one_english_theory(self) -> None:
        theory = (ROOT / "THEORY.md").read_text(encoding="utf-8")
        for heading in (
            "## 2. Field",
            "## 3. Center",
            "## 4. Necessary partial order",
            "## 6. Dynamic address",
            "## 7. Relative closure",
            "## 9. Multi-center fields",
            "## 10. Subject and self-construction",
            "## 13. Falsifiable program",
        ):
            self.assertIn(heading, theory)
        self.assertIsNone(re.search(r"[\u4e00-\u9fff]", theory))

    def test_removed_public_surfaces_stay_removed(self) -> None:
        for name in ("docs", "plugins", "examples"):
            self.assertFalse((ROOT / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
