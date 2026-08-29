import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))

    def test_candidate_has_no_unrecorded_remote_write(self):
        self.assertEqual("local-candidate-not-uploaded", self.manifest["status"])
        self.assertIsNone(self.manifest["git"]["candidate_commit"])
        self.assertIsNone(self.manifest["git"]["tag"])
        self.assertFalse(self.manifest["git"]["remote_write_performed"])

    def test_release_version_is_consistent(self):
        version = self.manifest["release_version"]
        citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        self.assertRegex(citation, rf'(?m)^version: "{re.escape(version)}"$')
        for plugin_name, plugin_version in self.manifest["components"]["plugins"].items():
            plugin = json.loads(
                (ROOT / "plugins" / plugin_name / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
            )
            self.assertEqual(version, plugin_version)
            self.assertEqual(version, plugin["version"])
        self.assertIn(version, (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn(version, (ROOT / "README.zh-CN.md").read_text(encoding="utf-8"))

    def test_component_versions_match_canonical_headers(self):
        components = self.manifest["components"]
        expected = {
            "root_theory": ("docs/methodology/递归中心偏序动力场域论.md", f"v{components['root_theory']}"),
            "dynamics_spec": ("docs/spec/递归中心场偏序动力模型.md", f"v{components['dynamics_spec']}"),
            "multi_center_spec": ("docs/spec/递归偏序多中心动态场域论.md", f"v{components['multi_center_spec']}"),
            "dynamic_addressing": ("docs/dynamic-addressing/递归动态寻址理论.md", f"v{components['dynamic_addressing']}"),
            "public_text": ("docs/theory.zh-CN.md", components["public_text"]),
            "focus_skill": ("plugins/rcf-focus/skills/recursive-center-field-dynamics/SKILL.md", f"v{components['focus_skill']}"),
        }
        for label, (relative_path, marker) in expected.items():
            with self.subTest(component=label):
                self.assertIn(marker, (ROOT / relative_path).read_text(encoding="utf-8"))

    def test_system_snapshot_is_visible(self):
        snapshot = self.manifest["system_snapshot"]
        self.assertIn(snapshot, (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn(snapshot, (ROOT / "README.zh-CN.md").read_text(encoding="utf-8"))
        self.assertIn(snapshot, (ROOT / "docs/release-scope.md").read_text(encoding="utf-8"))

    def test_release_snapshot_hashes_match_tree(self):
        output = subprocess.check_output(
            [sys.executable, str(ROOT / "scripts/repository-maintenance/hash_release.py")],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
        )
        current = json.loads(output)
        snapshot = (ROOT / "RELEASE_SNAPSHOT.md").read_text(encoding="utf-8")
        for group, record in current.items():
            with self.subTest(group=group):
                self.assertIn(f"| {record['files']} | `{record['sha256']}` |", snapshot)


if __name__ == "__main__":
    unittest.main()
