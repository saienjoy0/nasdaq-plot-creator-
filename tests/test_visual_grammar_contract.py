from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import visual_grammar_contract as module  # noqa: E402

FIXTURES = ROOT / "tests" / "visual-grammar-contract" / "fixtures"
REGISTRY = json.loads(
    (ROOT / "contracts" / "visual_grammar_registry.json").read_text(
        encoding="utf-8"
    )
)
REGISTRY_SCHEMA = json.loads(
    (ROOT / "contracts" / "visual_grammar_registry.schema.json").read_text(
        encoding="utf-8"
    )
)
DECLARATION_SCHEMA = json.loads(
    (ROOT / "contracts" / "visual_grammar.schema.json").read_text(
        encoding="utf-8"
    )
)


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class VisualGrammarContractTests(unittest.TestCase):
    def test_registry_is_valid_and_complete(self):
        validated = module.validate_registry(REGISTRY, REGISTRY_SCHEMA)
        self.assertEqual(len(validated["grammars"]), 8)
        self.assertEqual(
            {item["grammarId"] for item in validated["grammars"]},
            module.GRAMMAR_IDS,
        )

    def test_valid_declaration_passes(self):
        declaration = module.validate_declaration(
            load("declaration.valid.json"), DECLARATION_SCHEMA
        )
        self.assertEqual(declaration["grammarId"], "gap")
        self.assertEqual(declaration["transitionRole"], "major-shift")

    def test_return_requires_target(self):
        declaration = load("declaration.return.valid.json")
        declaration.pop("returnTargetBeatId")
        with self.assertRaisesRegex(module.ContractError, "VISUAL_GRAMMAR_INVALID"):
            module.validate_declaration(declaration, DECLARATION_SCHEMA)

    def test_non_return_rejects_target(self):
        with self.assertRaisesRegex(module.ContractError, "VISUAL_GRAMMAR_INVALID"):
            module.validate_declaration(
                load("declaration.return-target-unexpected.invalid.json"),
                DECLARATION_SCHEMA,
            )

    def test_unknown_grammar_is_rejected(self):
        with self.assertRaisesRegex(module.ContractError, "VISUAL_GRAMMAR_INVALID"):
            module.validate_declaration(
                load("declaration.unknown-grammar.invalid.json"),
                DECLARATION_SCHEMA,
            )

    def test_scene_number_or_narration_cannot_be_used_as_input(self):
        declaration = load("declaration.valid.json")
        declaration["sceneNumber"] = 4
        declaration["narrationText"] = "予想を上回った"
        with self.assertRaisesRegex(module.ContractError, "VISUAL_GRAMMAR_INVALID"):
            module.validate_declaration(declaration, DECLARATION_SCHEMA)

    def test_every_grammar_has_one_mvp_stage(self):
        module.validate_registry(REGISTRY, REGISTRY_SCHEMA)
        actual = {
            item["grammarId"]: item["allowedStageIds"]
            for item in REGISTRY["stageCompatibility"]
        }
        expected = {
            grammar_id: [stage_id]
            for grammar_id, stage_id in module.STAGE_BY_GRAMMAR.items()
        }
        self.assertEqual(actual, expected)

    def test_compatible_stage_passes(self):
        decision = module.check_compatibility("causal", "causal-stage", REGISTRY)
        self.assertTrue(decision.compatible)

    def test_incompatible_stage_is_rejected(self):
        with self.assertRaisesRegex(
            module.ContractError, "GRAMMAR_STAGE_INCOMPATIBLE"
        ):
            module.check_compatibility("gap", "comparison-stage", REGISTRY)

    def test_registry_rejects_duplicate_grammar(self):
        registry = copy.deepcopy(REGISTRY)
        registry["grammars"][1]["grammarId"] = "contradiction"
        with self.assertRaises(module.ContractError):
            module.validate_registry(registry, REGISTRY_SCHEMA)

    def test_registry_rejects_wrong_stage_mapping(self):
        registry = copy.deepcopy(REGISTRY)
        registry["stageCompatibility"][2]["allowedStageIds"] = [
            "comparison-stage"
        ]
        with self.assertRaisesRegex(
            module.ContractError, "REGISTRY_STAGE_MAP_MISMATCH"
        ):
            module.validate_registry(registry, REGISTRY_SCHEMA)


if __name__ == "__main__":
    unittest.main()
