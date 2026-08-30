from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ADDRESS = load_module(
    "public_address_engine",
    ROOT
    / "plugins"
    / "rcf-address"
    / "skills"
    / "recursive-field-addressing"
    / "scripts"
    / "address_engine.py",
)
DISTILL = load_module(
    "public_distill_ledger",
    ROOT
    / "plugins"
    / "rcf-distill"
    / "skills"
    / "distill-conversation-ideas"
    / "scripts"
    / "distill_ledger.py",
)


class AddressDistillRuntimeTest(unittest.TestCase):
    def test_address_current_engine_self_test(self) -> None:
        self.assertEqual(ADDRESS.ENGINE_VERSION, "0.5-experimental")
        ADDRESS.self_test()

    def test_distill_ledger_self_test(self) -> None:
        self.assertEqual(DISTILL.SCHEMA_VERSION, "distill-ledger-1.0")
        DISTILL.self_test()

    def test_distill_rejects_summary_promotion(self) -> None:
        state = {
            "schema_version": DISTILL.SCHEMA_VERSION,
            "revision": 0,
            "destination": "knowledge.md",
            "source_scope": "compacted conversation",
            "status": "open",
            "candidates": {},
            "plan_history": [],
            "finalization_history": [],
        }
        with self.assertRaises(DISTILL.DistillLedgerError):
            DISTILL.apply_plan(
                state,
                {
                    "evidence": ["conversation summary"],
                    "candidates": [
                        {
                            "candidate_id": "C1",
                            "semantic_key": "claim",
                            "title": "Claim",
                            "statement": "A summarized claim.",
                            "classification": "ADD",
                            "status": "已验证",
                            "source_kind": "conversation-summary",
                            "basis": ["conversation summary"],
                        }
                    ],
                },
            )


if __name__ == "__main__":
    unittest.main()
