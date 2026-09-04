import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "plugin"
    / "skills"
    / "focus"
    / "scripts"
    / "focus_runtime.py"
)
SPEC = importlib.util.spec_from_file_location("constructive_focus_runtime", SCRIPT)
RUNTIME = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNTIME)


def contract(goal="维护一个可被新证据修正的知识体系"):
    return {
        "goal": goal,
        "boundary": "只处理当前知识场及其可追溯依赖",
        "completion": "必要命题获得证据并通过闭合审计",
        "evidence_standard": "来源、推理或验证均可追溯",
        "constraints": [],
    }


def center(nodes):
    return {
        "center_id": "knowledge-maintenance",
        "label": "知识维护",
        "status": "active",
        "closure_status": "open",
        "obligation": "保持当前结论可用，并在反证出现时使其失效",
        "nodes": [
            {
                "node_id": node_id,
                "role": role,
                "object_id": node_id,
                "required_for_closure": True,
                "frontier_class": frontier,
            }
            for node_id, role, frontier in nodes
        ],
    }


class ConstructiveFocusRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state_path = self.root / "state.json"

    def tearDown(self):
        self.temp.cleanup()

    def payload(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return f"@{path}"

    def call(self, function, name, payload=None):
        values = {"state": str(self.state_path)}
        if payload is not None:
            values["payload"] = self.payload(f"{name}.json", payload)
        return function(type("Args", (), values))

    def init(self):
        args = type(
            "Args",
            (),
            {"state": str(self.state_path), "task": "维护知识体系", "mode": "constructive"},
        )
        self.assertEqual(RUNTIME.cmd_init(args), 0)

    def frame(self, frontier="none"):
        self.assertEqual(
            self.call(
                RUNTIME.cmd_frame,
                "frame",
                {
                    "field_id": "knowledge-field",
                    "contract": contract(),
                    "orientation": {
                        "functional_position": "正在维护可修订结论的分析者",
                        "governing_question": "哪项证据会改变当前结论？",
                        "evidence_needed": ["必要前提的验证结果"],
                        "reopen_triggers": ["必要前提被反驳"],
                    },
                    "closure_gap": "当前命题尚未取得闭合证据",
                    "centers": [
                        center(
                            [
                                ("premise", "必要前提", "none"),
                                ("conclusion", "依赖前提的结论", frontier),
                            ]
                        )
                    ],
                    "selected_center_id": "knowledge-maintenance",
                    "order": [{"before": "premise", "after": "conclusion"}],
                },
            ),
            0,
        )

    def test_orientation_survives_summary_and_closure_version(self):
        self.init()
        self.frame()
        state = self.state()
        orientation = state["fields"]["knowledge-field"]["orientation"]
        self.assertEqual(RUNTIME.state_summary(state)["orientation"], orientation)
        self.assertEqual(self.execute(["premise"], "premise"), 0)
        self.assertEqual(self.execute(["conclusion"], "conclusion"), 0)
        self.assertEqual(self.fold_closed(), 0)
        state = self.state()
        self.assertEqual(state["field_closure_versions"][0]["orientation"], orientation)
        self.assertEqual(
            state["fields"]["knowledge-field"]["focus_return"]["orientation"],
            orientation,
        )

    def execute(self, addresses, suffix):
        return self.call(
            RUNTIME.cmd_execute,
            suffix,
            {
                "addresses": addresses,
                "evidence": [f"{suffix}-evidence"],
                "result": f"{suffix}-result",
            },
        )

    def fold_closed(self):
        return self.call(
            RUNTIME.cmd_fold,
            "fold",
            {
                "conclusion": "当前版本相对闭合",
                "evidence": ["closure-audit"],
                "outputs": ["current-conclusion"],
                "latent_residuals": [],
                "active_residuals": [],
            },
        )

    def ingest(self, delta_id, raw_content="新证据"):
        return self.call(
            RUNTIME.cmd_ingest_delta,
            f"ingest-{delta_id}",
            {
                "delta_id": delta_id,
                "kind": "evidence",
                "raw_content": raw_content,
                "source": "paper.pdf#p4",
                "evidence": ["paper.pdf#p4"],
            },
        )

    def assess(self, delta_id, classification, scope, affected=None):
        return self.call(
            RUNTIME.cmd_assess_impact,
            f"assess-{delta_id}",
            {
                "delta_id": delta_id,
                "classification": classification,
                "propagation_scope": scope,
                "affected_addresses": affected or [],
                "reason": f"{classification} changes the current field",
                "evidence": ["impact-audit"],
            },
        )

    def decide(self, decision, target=None, suffix="decide"):
        payload = {
            "decision": decision,
            "reason": f"choose {decision}",
            "evidence": ["decision-audit"],
        }
        if target is not None:
            payload["target_address"] = target
        return self.call(RUNTIME.cmd_decide, suffix, payload)

    def state(self):
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def test_constructive_init_has_live_decision_and_version_ledgers(self):
        self.init()
        state = self.state()
        self.assertEqual(state["schema_version"], "focus-constructive-2.0")
        self.assertEqual(state["mode"], "constructive")
        self.assertEqual(state["knowledge_deltas"], {})
        self.assertEqual(state["decision_history"], [])
        self.assertEqual(state["field_closure_versions"], [])
        self.assertEqual(state["version_branches"], [])

    def test_contradiction_invalidates_closure_and_all_necessary_descendants(self):
        self.init()
        self.frame()
        self.assertEqual(self.execute(["premise"], "premise"), 0)
        self.assertEqual(self.execute(["conclusion"], "conclusion"), 0)
        self.assertEqual(self.fold_closed(), 0)
        before = self.state()
        self.assertTrue(before["fields"]["knowledge-field"]["closure_audit"]["field_closure"])
        self.assertEqual(len(before["field_closure_versions"]), 1)

        self.assertEqual(self.ingest("delta-conflict", "实验反驳必要前提"), 0)
        self.assertEqual(
            self.assess("delta-conflict", "CONTRADICT", "interface", ["premise"]),
            0,
        )
        state = self.state()
        field = state["fields"]["knowledge-field"]
        premise = state["addresses"][field["node_addresses"]["premise"]]
        conclusion = state["addresses"][field["node_addresses"]["conclusion"]]
        self.assertEqual(premise["modality"], "[◇]")
        self.assertEqual(conclusion["modality"], "[◇]")
        self.assertIn("delta-conflict", premise["invalidated_by"])
        self.assertIn("delta-conflict", conclusion["invalidated_by"])
        self.assertFalse(field["closure_audit"]["field_closure"])
        self.assertEqual(field["closure_certificates"][-1]["status"], "invalidated")
        self.assertEqual(state["active_decision"]["decision"], "REOPEN_INTERFACE")
        self.assertEqual(len(state["field_closure_versions"]), 1)
        self.assertEqual(RUNTIME.validate_state(state), [])

    def test_noop_delta_creates_no_address_or_field_version(self):
        self.init()
        self.frame()
        before = self.state()
        self.assertEqual(self.ingest("delta-noop", "重复的既有材料"), 0)
        self.assertEqual(self.assess("delta-noop", "NOOP", "none"), 0)
        state = self.state()
        self.assertEqual(set(state["addresses"]), set(before["addresses"]))
        self.assertEqual(state["field_closure_versions"], before["field_closure_versions"])
        self.assertEqual(state["active_decision"]["decision"], "NOOP")
        self.assertEqual(state["knowledge_deltas"]["delta-noop"]["status"], "assessed")

    def test_incomparable_conflict_opens_version_branch_without_overwriting_source(self):
        self.init()
        self.frame()
        self.assertEqual(self.execute(["premise"], "premise"), 0)
        self.assertEqual(self.execute(["conclusion"], "conclusion"), 0)
        self.assertEqual(self.fold_closed(), 0)
        source_version = self.state()["field_closure_versions"][0]["version_id"]
        self.assertEqual(self.ingest("delta-branch", "另一套同样有证据的解释"), 0)
        self.assertEqual(
            self.assess("delta-branch", "CONTRADICT", "branch", ["premise"]),
            0,
        )
        state = self.state()
        self.assertEqual(state["active_decision"]["decision"], "SPLIT_BRANCH")
        self.assertEqual(state["version_branches"][-1]["source_versions"], [source_version])
        self.assertEqual(state["field_closure_versions"][0]["version_id"], source_version)
        self.assertEqual(state["field_closure_versions"][0]["status"], "superseded-by-branch")

    def test_drive_rejects_continue_when_target_requires_expansion(self):
        self.init()
        self.frame(frontier="expansion_required")
        with self.assertRaisesRegex(RUNTIME.FocusRuntimeError, "requires EXPAND_REQUIRED"):
            self.call(
                RUNTIME.cmd_decide,
                "bad-drive",
                {
                    "decision": "CONTINUE",
                    "target_address": "conclusion",
                    "reason": "错误地跳过必要展开",
                    "evidence": ["decision-audit"],
                },
            )
        self.assertEqual(
            self.call(
                RUNTIME.cmd_decide,
                "good-drive",
                {
                    "decision": "EXPAND_REQUIRED",
                    "target_address": "conclusion",
                    "reason": "先打开必要子场",
                    "evidence": ["decision-audit"],
                },
            ),
            0,
        )
        self.assertEqual(self.state()["active_decision"]["decision"], "EXPAND_REQUIRED")

    def test_reclosure_creates_new_version_linked_to_invalidated_version(self):
        self.init()
        self.frame()
        self.assertEqual(self.execute(["premise"], "premise"), 0)
        self.assertEqual(self.execute(["conclusion"], "conclusion"), 0)
        self.assertEqual(self.fold_closed(), 0)
        old_version = self.state()["field_closure_versions"][0]["version_id"]
        self.assertEqual(self.ingest("delta-revise", "新证据要求局部替换"), 0)
        self.assertEqual(
            self.assess("delta-revise", "REFINE", "local", ["premise"]), 0
        )
        self.assertEqual(self.decide("CONTINUE", "premise", "resume-premise"), 0)
        self.assertEqual(self.execute(["premise"], "revised-premise"), 0)
        self.assertEqual(self.execute(["conclusion"], "revised-conclusion"), 0)
        self.assertEqual(self.fold_closed(), 0)
        state = self.state()
        self.assertEqual(len(state["field_closure_versions"]), 2)
        self.assertEqual(state["field_closure_versions"][0]["status"], "invalidated")
        self.assertEqual(state["field_closure_versions"][1]["status"], "current")
        self.assertEqual(state["field_closure_versions"][1]["parent_versions"], [old_version])
        certificates = state["fields"]["knowledge-field"]["closure_certificates"]
        self.assertEqual(certificates[0]["status"], "invalidated")
        self.assertEqual(certificates[1]["status"], "active")

    def test_child_contradiction_reopens_parent_interface_and_dependents(self):
        self.init()
        self.assertEqual(
            self.call(
                RUNTIME.cmd_frame,
                "root-frame",
                {
                    "field_id": "root-field",
                    "contract": contract("形成可复用的父结论"),
                    "closure_gap": "子场接口尚未返回",
                    "centers": [
                        center(
                            [
                                ("parent-interface", "子场压缩接口", "expansion_required"),
                                ("parent-conclusion", "依赖接口的父结论", "none"),
                            ]
                        )
                    ],
                    "selected_center_id": "knowledge-maintenance",
                    "order": [
                        {"before": "parent-interface", "after": "parent-conclusion"}
                    ],
                },
            ),
            0,
        )
        self.assertEqual(
            self.call(
                RUNTIME.cmd_expand,
                "child-frame",
                {
                    "field_id": "child-field",
                    "parent_address": "parent-interface",
                    "parent_return": {
                        "required_function": "验证父前提",
                        "required_output": "可追溯的子结论",
                        "closure_requirement": "子前提取得证据",
                        "parent_return": "压缩为父场接口",
                    },
                    "contract": contract("验证父场所需的子前提"),
                    "closure_gap": "子前提尚未验证",
                    "centers": [
                        center([("child-premise", "父结论所需的子前提", "none")])
                    ],
                    "selected_center_id": "knowledge-maintenance",
                    "order": [],
                },
            ),
            0,
        )
        self.assertEqual(self.execute(["child-premise"], "child-premise"), 0)
        self.assertEqual(self.fold_closed(), 0)
        self.assertEqual(
            RUNTIME.cmd_unwind(type("Args", (), {"state": str(self.state_path)})), 0
        )
        self.assertEqual(self.execute(["parent-conclusion"], "parent-conclusion"), 0)
        self.assertEqual(self.fold_closed(), 0)

        self.assertEqual(self.ingest("delta-child", "新实验反驳子前提"), 0)
        impact = {
            "delta_id": "delta-child",
            "field_id": "child-field",
            "classification": "CONTRADICT",
            "propagation_scope": "interface",
            "affected_addresses": ["child-premise"],
            "reason": "子前提失效使父接口及父结论失效",
            "evidence": ["impact-audit"],
        }
        self.assertEqual(self.call(RUNTIME.cmd_assess_impact, "child-impact", impact), 0)
        state = self.state()
        root = state["fields"]["root-field"]
        child = state["fields"]["child-field"]
        self.assertEqual(
            state["addresses"][child["node_addresses"]["child-premise"]]["modality"],
            "[◇]",
        )
        self.assertEqual(
            state["addresses"][root["node_addresses"]["parent-interface"]]["modality"],
            "[◇]",
        )
        self.assertEqual(
            state["addresses"][root["node_addresses"]["parent-conclusion"]]["modality"],
            "[◇]",
        )
        self.assertFalse(root["closure_audit"]["field_closure"])
        self.assertEqual(state["active_decision"]["decision"], "REOPEN_INTERFACE")


if __name__ == "__main__":
    unittest.main()
