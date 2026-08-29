import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FOCUS_PLUGIN = REPO_ROOT / "plugins" / "rcf-focus"
SKILL_ROOT = FOCUS_PLUGIN / "skills" / "recursive-center-field-dynamics"
FOCUS_ALIAS = FOCUS_PLUGIN / "skills" / "focus"
ADDRESS_ROOT = (
    REPO_ROOT / "plugins" / "rcf-address" / "skills" / "recursive-field-addressing"
)
DISTILL_ROOT = (
    REPO_ROOT / "plugins" / "rcf-distill" / "skills" / "distill-conversation-ideas"
)
RELEASE_VERSION = "0.4.0-alpha.1"


class SkillContractTest(unittest.TestCase):
    def test_focus_constructive_contract_is_packaged(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        runtime = (SKILL_ROOT / "scripts" / "focus_runtime.py")
        reference = (SKILL_ROOT / "references" / "constructive-loop.md")

        for term in [
            "parent model retains execution authority",
            "without becoming an authorization gate",
            "FORM",
            "DRIVE",
            "REVISE",
            "FOLD",
            "ingest-delta",
            "assess-impact",
            "NOOP",
        ]:
            self.assertIn(term, skill)
        self.assertTrue(runtime.is_file())
        self.assertTrue(reference.is_file())
        reference_text = reference.read_text(encoding="utf-8")
        self.assertIn("FORM", reference_text)
        self.assertIn("Return one decision", reference_text)
        self.assertTrue((SKILL_ROOT / "references" / "knowledge-revision.md").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "closure-and-invalidation.md").is_file())
        self.assertTrue((SKILL_ROOT / "tests" / "test_constructive_focus_runtime.py").is_file())

    def test_focus_alias_routes_to_canonical_skill(self) -> None:
        alias = (FOCUS_ALIAS / "SKILL.md").read_text(encoding="utf-8")
        agent = (FOCUS_ALIAS / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("Invocation alias", alias)
        self.assertIn("constructive", alias.lower())
        self.assertIn("FORM → DRIVE → REVISE → FOLD", alias)
        self.assertIn("NOOP", alias)
        self.assertIn("allow_implicit_invocation: false", agent)

    def test_latent_frontier_and_residual_ledgers_are_distinct(self) -> None:
        protocol = (SKILL_ROOT / "references" / "protocol.md").read_text(encoding="utf-8")
        self.assertIn("`Λ_t` is not an address and never inherits `[◇]`", protocol)
        self.assertIn("binding may be `bound`, `candidate`, or `unaddressed`", protocol)
        self.assertNotIn("`Λ_t` (addressed future material", protocol)
        self.assertNotIn("Active `[◇]` names a residual", protocol)

    def test_marketplace_points_to_three_independent_plugins(self) -> None:
        marketplace = json.loads(
            (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        expected_skills = {
            "rcf-focus": {"recursive-center-field-dynamics", "focus"},
            "rcf-address": {"recursive-field-addressing"},
            "rcf-distill": {"distill-conversation-ideas"},
        }
        self.assertEqual(
            [entry["name"] for entry in marketplace["plugins"]],
            list(expected_skills),
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
            self.assertEqual(manifest["version"], RELEASE_VERSION)
            self.assertEqual(manifest["skills"], "./skills/")
            self.assertEqual(entry["source"]["path"], f"./plugins/{name}")
            self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
            self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")
            packaged = {
                path.name for path in (plugin_root / "skills").iterdir() if path.is_dir()
            }
            self.assertEqual(packaged, expected_skills[name])
            self.assertNotIn("[TODO:", json.dumps(manifest))

    def test_address_and_distill_contracts_are_present(self) -> None:
        address = (ADDRESS_ROOT / "SKILL.md").read_text(encoding="utf-8")
        distill = (DISTILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("address", address.lower())
        self.assertIn("lineage", address.lower())
        self.assertTrue((ADDRESS_ROOT / "scripts" / "address_engine.py").is_file())
        self.assertIn("canonical", distill.lower())
        self.assertIn("provenance", distill.lower())

    def test_public_scope_states_implementation_limits(self) -> None:
        scope = (REPO_ROOT / "docs" / "release-scope.md").read_text(encoding="utf-8")
        for term in [
            "自动发现真实场或真实中心",
            "未实现",
            "多个独立 `FocusReturn` 自动重新汇合",
            "相对现有方法的经验性能优势",
            "未验证",
            "不是“已证明自洽”的完备形式系统",
        ]:
            self.assertIn(term, scope)


if __name__ == "__main__":
    unittest.main()
