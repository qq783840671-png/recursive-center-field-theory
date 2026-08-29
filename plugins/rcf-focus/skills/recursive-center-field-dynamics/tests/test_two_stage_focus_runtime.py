import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "focus_runtime.py"
)
SPEC = importlib.util.spec_from_file_location("focus_runtime", SCRIPT)
RUNTIME = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNTIME)


def base_contract(goal="完成当前任务"):
    return {
        "goal": goal,
        "boundary": "只处理当前任务范围",
        "completion": "必要结构执行并取得证据",
        "evidence_standard": "可追溯的执行或分析证据",
        "constraints": [],
    }


def center(center_id, nodes, *, status="active", closure_status="open"):
    return {
        "center_id": center_id,
        "label": center_id,
        "status": status,
        "closure_status": closure_status,
        "obligation": f"完成{center_id}承担的父契约义务",
        "nodes": [
            {"node_id": node_id, "role": role, "object_id": node_id}
            for node_id, role in nodes
        ],
    }


class TwoStageFocusRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state_path = self.root / "state.json"

    def tearDown(self):
        self.temp.cleanup()

    def init_state(self, mode="clarify"):
        args = type("Args", (), {"state": str(self.state_path), "task": "测试任务", "mode": mode})
        self.assertEqual(RUNTIME.cmd_init(args), 0)

    def write_payload(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return f"@{path}"

    def frame(self, payload):
        args = type(
            "Args",
            (),
            {"state": str(self.state_path), "payload": self.write_payload("frame.json", payload)},
        )
        self.assertEqual(RUNTIME.cmd_frame(args), 0)

    def expand(self, payload):
        args = type(
            "Args",
            (),
            {"state": str(self.state_path), "payload": self.write_payload("expand.json", payload)},
        )
        self.assertEqual(RUNTIME.cmd_expand(args), 0)

    def observe(self, payload):
        args = type(
            "Args",
            (),
            {"state": str(self.state_path), "payload": self.write_payload("observe.json", payload)},
        )
        self.assertEqual(RUNTIME.cmd_observe(args), 0)

    def reconstruct(self, payload):
        args = type(
            "Args",
            (),
            {
                "state": str(self.state_path),
                "payload": self.write_payload("reconstruct.json", payload),
            },
        )
        self.assertEqual(RUNTIME.cmd_reconstruct(args), 0)

    def execute(self, addresses, suffix="execute"):
        payload = {
            "addresses": addresses,
            "evidence": [f"{suffix}-evidence"],
            "result": f"{suffix}-result",
        }
        args = type(
            "Args",
            (),
            {"state": str(self.state_path), "payload": self.write_payload(f"{suffix}.json", payload)},
        )
        return RUNTIME.cmd_execute(args)

    def fold(self, payload):
        args = type(
            "Args",
            (),
            {"state": str(self.state_path), "payload": self.write_payload("fold.json", payload)},
        )
        return RUNTIME.cmd_fold(args)

    def read_state(self):
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def test_sidecar_reconstructs_addresses_from_observed_execution(self):
        self.init_state(mode="sidecar")
        self.observe(
            {
                "raw_request": "修改配置并验证结果",
                "events": [
                    {
                        "kind": "read",
                        "summary": "检查现有配置",
                        "evidence": ["config-before"],
                    },
                    {
                        "kind": "write",
                        "summary": "更新配置",
                        "evidence": ["config-diff"],
                    },
                    {
                        "kind": "result",
                        "summary": "验证修改结果",
                        "evidence": ["test-pass"],
                    },
                ],
                "result": "配置已修改并通过测试",
                "evidence": ["config-diff", "test-pass"],
            }
        )
        observation_id = self.read_state()["observations"][0]["observation_id"]
        self.reconstruct(
            {
                "field_id": "observed-task",
                "contract": base_contract("根据真实轨迹回收任务场"),
                "closure_gap": "确认实际执行是否满足任务",
                "centers": [
                    center(
                        "actual-work",
                        [
                            ("inspect", "检查现状"),
                            ("change", "完成修改"),
                            ("verify", "验证结果"),
                        ],
                    )
                ],
                "selected_center_id": "actual-work",
                "order": [
                    {"before": "inspect", "after": "change"},
                    {"before": "change", "after": "verify"},
                ],
                "trace_observation_ids": [observation_id],
                "realized_nodes": ["inspect", "change", "verify"],
                "node_evidence": {
                    "inspect": ["config-before"],
                    "change": ["config-diff"],
                    "verify": ["test-pass"],
                },
            }
        )
        state = self.read_state()
        field = state["fields"]["observed-task"]
        self.assertEqual(state["phase"], "reconstructed")
        self.assertEqual(field["reconstruction_basis"], "observed-execution")
        self.assertEqual(field["trace_observation_refs"], [observation_id])
        self.assertTrue(
            all(
                state["addresses"][address_id]["modality"] == "[+]"
                for address_id in field["node_addresses"].values()
            )
        )
        self.assertEqual(RUNTIME.validate_state(state), [])

    def test_sidecar_reconstruction_rejects_missing_observation(self):
        self.init_state(mode="sidecar")
        args = type(
            "Args",
            (),
            {"state": str(self.state_path), "payload": self.write_payload("empty.json", {})},
        )
        with self.assertRaisesRegex(
            RUNTIME.FocusRuntimeError, "requires an observed execution trace"
        ):
            RUNTIME.cmd_reconstruct(args)

    def test_focus_1_preserves_multi_center_panorama_and_projects_one_center(self):
        self.init_state()
        payload = {
            "field_id": "root-field",
            "contract": base_contract("定位真正阻断发布的问题"),
            "closure_gap": "尚未确认失败来源",
            "centers": [
                center("diagnosis", [("observe", "恢复失败证据"), ("locate", "定位原因")]),
                center("release", [("review", "审查发布条件")], status="active", closure_status="closed"),
            ],
            "center_relations": [
                {"source": "diagnosis", "target": "release", "type": "supports", "evidence": []}
            ],
            "selected_center_id": "diagnosis",
            "order": [{"before": "observe", "after": "locate"}],
            "confidence": "provisional",
            "projection_assumptions": ["发布接口仍有效"],
            "invalidation_triggers": ["发布契约变化"],
        }
        self.frame(payload)
        state = self.read_state()
        field = state["fields"]["root-field"]
        self.assertEqual(field["selected_center_ref"], "diagnosis")
        self.assertEqual(field["peer_center_refs"], ["release"])
        self.assertEqual(
            field["projection_certificate"]["selected_center_ref"], "diagnosis"
        )
        self.assertEqual(len(field["node_addresses"]), 3)
        locate = state["addresses"][field["node_addresses"]["locate"]]
        self.assertEqual(locate["relation_path"], [field["node_addresses"]["observe"]])
        self.assertTrue(
            all(state["addresses"][address]["modality"] == "[◇]" for address in field["node_addresses"].values())
        )
        self.assertEqual(RUNTIME.validate_state(state), [])

    def test_focus_2_opens_one_real_child_field_without_fixed_width(self):
        self.init_state()
        self.frame(
            {
                "field_id": "root-field",
                "contract": base_contract(),
                "closure_gap": "父位置尚未实现",
                "centers": [center("main", [("parent", "需要打开的父位置")])],
                "selected_center_id": "main",
                "order": [],
            }
        )
        self.expand(
            {
                "field_id": "child-field",
                "parent_address": "parent",
                "parent_return": {
                    "required_function": "解释父位置",
                    "required_output": "可验证结果",
                    "closure_requirement": "子场必要位置完成",
                    "parent_return": "压缩为父接口",
                },
                "contract": base_contract("打开父位置内部结构"),
                "closure_gap": "子场证据尚未完成",
                "centers": [
                    center(
                        "child-main",
                        [
                            ("entry", "恢复入口"),
                            ("transform", "完成必要转化"),
                            ("verify", "验证输出"),
                            ("return", "形成返回接口"),
                        ],
                    )
                ],
                "selected_center_id": "child-main",
                "order": [
                    {"before": "entry", "after": "transform"},
                    {"before": "transform", "after": "verify"},
                    {"before": "verify", "after": "return"},
                ],
            }
        )
        state = self.read_state()
        child = state["fields"]["child-field"]
        self.assertEqual(child["global_depth"], 1)
        self.assertEqual(len(child["node_addresses"]), 4)
        parent_address = state["addresses"][state["fields"]["root-field"]["node_addresses"]["parent"]]
        self.assertEqual(parent_address["child_field_id"], "child-field")
        self.assertEqual(len(state["field_stack"]), 2)
        self.assertEqual(RUNTIME.validate_state(state), [])

    def test_execute_enforces_partial_order_and_fold_unwind_returns_interface(self):
        self.init_state(mode="action")
        self.frame(
            {
                "field_id": "root-field",
                "contract": base_contract(),
                "closure_gap": "父接口尚未形成",
                "centers": [center("main", [("parent", "子场返回接口")])],
                "selected_center_id": "main",
                "order": [],
            }
        )
        self.expand(
            {
                "field_id": "child-field",
                "parent_address": "parent",
                "parent_return": {
                    "required_function": "完成子场",
                    "required_output": "子场结果",
                    "closure_requirement": "a与b均完成",
                    "parent_return": "返回父地址",
                },
                "contract": base_contract("完成子场"),
                "closure_gap": "a与b尚未执行",
                "centers": [center("child", [("a", "先执行"), ("b", "后执行")])],
                "selected_center_id": "child",
                "order": [{"before": "a", "after": "b"}],
            }
        )
        bad_args = type(
            "Args",
            (),
            {
                "state": str(self.state_path),
                "payload": self.write_payload(
                    "bad-execute.json",
                    {"addresses": ["b"], "evidence": ["premature"], "result": "bad"},
                ),
            },
        )
        with self.assertRaises(RUNTIME.FocusRuntimeError):
            RUNTIME.cmd_execute(bad_args)
        self.assertEqual(self.execute(["a"], "execute-a"), 0)
        panorama_after_a = self.read_state()["panorama_version"]
        self.assertEqual(self.execute(["b"], "execute-b"), 0)
        self.assertGreater(self.read_state()["panorama_version"], panorama_after_a)
        self.assertEqual(
            self.fold(
                {
                    "conclusion": "子场已经相对闭合",
                    "evidence": ["a-b-audit"],
                    "outputs": ["child-output"],
                    "residuals": [],
                }
            ),
            0,
        )
        unwind_args = type("Args", (), {"state": str(self.state_path)})
        self.assertEqual(RUNTIME.cmd_unwind(unwind_args), 0)
        state = self.read_state()
        root = state["fields"]["root-field"]
        parent = state["addresses"][root["node_addresses"]["parent"]]
        self.assertEqual(parent["modality"], "[+]")
        self.assertEqual(parent["exposure_state"], "compressed")
        self.assertEqual(len(state["field_stack"]), 1)
        self.assertEqual(RUNTIME.validate_state(state), [])

    def test_fold_does_not_claim_full_field_closure_when_peer_center_is_open(self):
        self.init_state(mode="action")
        self.frame(
            {
                "field_id": "root-field",
                "contract": base_contract(),
                "closure_gap": "两个中心尚未联合闭合",
                "centers": [
                    center("selected", [("a", "完成当前中心")]),
                    center("peer", [("p", "完成平级中心")]),
                ],
                "selected_center_id": "selected",
                "order": [],
            }
        )
        self.assertEqual(self.execute(["a"]), 0)
        self.assertEqual(
            self.fold(
                {
                    "conclusion": "当前中心闭合",
                    "evidence": ["selected-audit"],
                    "outputs": ["selected-output"],
                    "residuals": [],
                    "reprojection_request": "switch-to-peer",
                }
            ),
            0,
        )
        state = self.read_state()
        audit = state["fields"]["root-field"]["closure_audit"]
        self.assertTrue(audit["selected_center_closure"])
        self.assertFalse(audit["field_closure"])
        self.assertEqual(state["phase"], "folded")
        self.assertIsNotNone(state["fields"]["root-field"]["remaining_closure_gap"])

    def test_validation_detects_tampered_child_depth(self):
        self.init_state()
        self.frame(
            {
                "field_id": "root-field",
                "contract": base_contract(),
                "closure_gap": "父位置尚未实现",
                "centers": [center("main", [("parent", "父位置")])],
                "selected_center_id": "main",
                "order": [],
            }
        )
        self.expand(
            {
                "field_id": "child-field",
                "parent_address": "parent",
                "parent_return": {
                    "required_function": "完成子场",
                    "required_output": "结果",
                    "closure_requirement": "子节点完成",
                    "parent_return": "返回父场",
                },
                "contract": base_contract("子场"),
                "closure_gap": "子节点未完成",
                "centers": [center("child", [("x", "子节点")])],
                "selected_center_id": "child",
                "order": [],
            }
        )
        state = self.read_state()
        state["fields"]["child-field"]["global_depth"] = 9
        errors = RUNTIME.validate_state(state)
        self.assertTrue(any("depth is not parent depth + 1" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
