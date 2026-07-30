import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = (
    REPO_ROOT
    / "plugins"
    / "rcf-focus"
    / "skills"
    / "recursive-center-field-dynamics"
)
ADDRESS_ROOT = (
    REPO_ROOT
    / "plugins"
    / "rcf-address"
    / "skills"
    / "recursive-field-addressing"
)
DISTILL_ROOT = (
    REPO_ROOT
    / "plugins"
    / "rcf-distill"
    / "skills"
    / "distill-conversation-ideas"
)


class SkillContractTest(unittest.TestCase):
    def test_chinese_user_facing_terms_use_root_path_vocabulary(self) -> None:
        chinese_docs = list(REPO_ROOT.rglob("*.zh-CN.md"))
        for path in chinese_docs:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("祖先", text, path)

    def test_compact_skill_retains_operational_invariants(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        protocol = (SKILL_ROOT / "references" / "protocol.md").read_text(
            encoding="utf-8"
        )
        schema = (SKILL_ROOT / "references" / "state-schema.md").read_text(
            encoding="utf-8"
        )
        agent = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")

        required_skill_terms = [
            "Run only when the user attaches `Focus`",
            "F0_CONFIRMATION_REQUIRED",
            "Confirmation is a lock event, not the start of formation",
            "formed candidate",
            "Provisional closure",
            "An empty residual ledger requires an audited reason",
            "Clarify mode",
            "Action mode",
            "Progressive loading",
            "field contract `Γ_t`",
            "complete typed relation graph `G_t`",
            "necessary-predecessor projection `Π_t`",
            "candidate centers `𝒦_t`",
            "reopenable compression",
            "Global #1",
            "Focus #1",
            "`[+]`: realized only after `Execute → Audit`",
            "ActionFrontier_t",
            "ExpansionFrontier_t",
            "Compressed_t",
            "R_t",
            "D_t",
            "Ready_t",
            "F1/F2 record motion provenance",
            "F0 is `根层`",
            "`root_ancestry` is `根路径`",
            "FIELD_ASCENSION_REQUIRED",
            "F0_COMPLETE",
            "one motion result",
        ]
        for term in required_skill_terms:
            self.assertIn(term, skill)

        self.assertLessEqual(len(skill.splitlines()), 220)
        self.assertLessEqual(len(skill), 14000)
        self.assertNotIn("read both files completely before acting", skill)
        self.assertIn("Read only the reference required by the current surface", skill)
        self.assertIn("one natural-language task sentence", protocol)
        self.assertIn("mandatory F0 checkpoint", protocol)
        self.assertIn("modeling is an internal motion", protocol)
        self.assertIn("confirmation follows formation", protocol)
        self.assertIn("Clarify mode", protocol)
        self.assertIn("Default rendering contract", protocol)
        self.assertIn('"schema_version": "2.2"', schema)
        self.assertIn('"f0_confirmation"', schema)
        self.assertIn("Presentation and terminology contract", schema)
        self.assertIn("F1(Global #1)", schema)
        self.assertIn("allow_implicit_invocation: false", agent)
        self.assertIn("stabilize this task, confirm F0", agent)
        self.assertIn("F0 provisional-closure exit gate", protocol)
        self.assertIn("The F0 provisional-closure gate is derived", schema)
        self.assertIn("one motion result", schema)

    def test_marketplace_points_to_three_independent_plugins(self) -> None:
        marketplace = json.loads(
            (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            "rcf-focus": SKILL_ROOT,
            "rcf-address": ADDRESS_ROOT,
            "rcf-distill": DISTILL_ROOT,
        }
        self.assertEqual(
            [entry["name"] for entry in marketplace["plugins"]],
            list(expected),
        )
        for entry in marketplace["plugins"]:
            name = entry["name"]
            plugin_root = REPO_ROOT / "plugins" / name
            manifest = json.loads(
                (plugin_root / ".codex-plugin" / "plugin.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["name"], name)
            self.assertEqual(manifest["version"], "0.1.0-alpha.3")
            self.assertEqual(manifest["skills"], "./skills/")
            self.assertEqual(entry["source"]["path"], f"./plugins/{name}")
            self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
            self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")
            packaged_skills = [
                path for path in (plugin_root / "skills").iterdir() if path.is_dir()
            ]
            self.assertEqual(packaged_skills, [expected[name]])
            self.assertNotIn("[TODO:", json.dumps(manifest))

    def test_address_and_distill_skill_contracts_are_present(self) -> None:
        address = (ADDRESS_ROOT / "SKILL.md").read_text(encoding="utf-8")
        distill = (DISTILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("address", address.lower())
        self.assertIn("lineage", address.lower())
        self.assertTrue((ADDRESS_ROOT / "scripts" / "address_engine.py").is_file())
        self.assertIn("canonical", distill.lower())
        self.assertIn("provenance", distill.lower())


if __name__ == "__main__":
    unittest.main()
