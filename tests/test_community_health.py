import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ISSUE_ROOT = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"


class CommunityHealthTest(unittest.TestCase):
    def test_required_community_files_exist(self) -> None:
        required = [
            "README.md",
            "README.zh-CN.md",
            "LICENSE",
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
            "SECURITY.md",
            "SUPPORT.md",
            "GOVERNANCE.md",
            ".github/PULL_REQUEST_TEMPLATE.md",
            ".github/ISSUE_TEMPLATE/config.yml",
        ]
        for relative in required:
            path = REPO_ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertGreater(path.stat().st_size, 0, relative)

    def test_issue_forms_have_github_community_profile_fields(self) -> None:
        forms = sorted(ISSUE_ROOT.glob("*.yml"))
        form_names = {path.name for path in forms}
        self.assertTrue(
            {"skill-failure.yml", "theory-challenge.yml", "documentation.yml"}
            <= form_names
        )
        for path in forms:
            if path.name == "config.yml":
                continue
            text = path.read_text(encoding="utf-8")
            self.assertRegex(text, r"(?m)^name:\s*\S")
            self.assertRegex(text, r"(?m)^description:\s*\S")
            ids = re.findall(r"(?m)^\s+id:\s*([^\s]+)", text)
            self.assertEqual(len(ids), len(set(ids)), f"duplicate ids in {path}")
            self.assertIn("validations:", text, path)

    def test_issue_routing_and_private_security_boundary(self) -> None:
        config = (ISSUE_ROOT / "config.yml").read_text(encoding="utf-8")
        security = (REPO_ROOT / "SECURITY.md").read_text(encoding="utf-8")
        support = (REPO_ROOT / "SUPPORT.md").read_text(encoding="utf-8")
        self.assertIn("blank_issues_enabled: false", config)
        self.assertIn("/discussions", config)
        self.assertIn("/security/advisories/new", config)
        self.assertIn("Do not open a public issue", security)
        self.assertIn("Theory or evidence challenge", support)

    def test_readmes_link_community_boundaries(self) -> None:
        for name in ("README.md", "README.zh-CN.md"):
            text = (REPO_ROOT / name).read_text(encoding="utf-8")
            for target in (
                "CONTRIBUTING.md",
                "CODE_OF_CONDUCT.md",
                "SUPPORT.md",
                "SECURITY.md",
                "GOVERNANCE.md",
            ):
                self.assertIn(f"]({target})", text, (name, target))

    def test_pull_request_template_preserves_claim_layers(self) -> None:
        text = (
            REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Evidence and scope", text)
        self.assertIn("Invariant and compatibility audit", text)
        self.assertIn("definitions, hypotheses, implementation claims", text)
        self.assertIn("CC BY-NC 4.0", text)


if __name__ == "__main__":
    unittest.main()
