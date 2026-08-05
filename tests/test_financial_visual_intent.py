from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import financial_visual_intent as module  # noqa: E402

FIXTURES = ROOT / "tests" / "financial-visual-intent" / "fixtures"


def load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FinancialVisualIntentTests(unittest.TestCase):
    def test_expectation_gap_is_eligible(self):
        decision = module.compile_intent(load("expectation-gap.valid.json"))
        self.assertEqual(decision.eligibility, "eligible")
        self.assertEqual(decision.selected_recipe, "earnings-surprise")
        self.assertEqual(decision.reasons, ())

    def test_market_snapshot_is_eligible_without_fake_series(self):
        intent = load("market-snapshot.valid.json")
        decision = module.compile_intent(intent)
        self.assertEqual(decision.eligibility, "eligible")
        self.assertEqual(intent["chartPolicy"], "no-series")
        self.assertEqual(decision.selected_recipe, "market-pulse-grid")

    def test_wrong_gap_uses_fallback(self):
        decision = module.compile_intent(load("expectation-gap.invalid-gap.json"))
        self.assertEqual(decision.eligibility, "fallback")
        self.assertEqual(decision.selected_recipe, "expected-anchor")
        self.assertIn("gap numericValue must equal actual minus expected", decision.reasons)

    def test_unapproved_intent_never_selects_new_recipe(self):
        decision = module.compile_intent(load("unapproved.valid-fallback.json"))
        self.assertEqual(decision.eligibility, "fallback")
        self.assertEqual(decision.selected_recipe, "news-media")
        self.assertIn("intent status is not approved", decision.reasons)

    def test_verified_series_policy_rejects_non_series_precision(self):
        intent = load("market-snapshot.valid.json")
        intent["chartPolicy"] = "verified-series-only"
        with self.assertRaises(module.ContractError):
            module.validate_intent(intent)

    def test_metric_source_must_be_declared_at_top_level(self):
        intent = load("market-snapshot.valid.json")
        intent["metrics"][0]["sourceIds"] = ["source-999"]
        with self.assertRaises(module.ContractError):
            module.validate_intent(intent)

    def test_kind_recipe_pair_is_fixed(self):
        intent = load("market-snapshot.valid.json")
        intent["preferredRecipe"] = "earnings-surprise"
        with self.assertRaises(module.ContractError):
            module.validate_intent(intent)

    def test_visual_template_input_is_rejected(self):
        intent = load("market-snapshot.valid.json")
        intent["visualTemplate"] = "market-pulse-grid"
        with self.assertRaises(module.ContractError):
            module.validate_intent(intent)

    def test_recipe_decision_does_not_emit_renderer_template(self):
        decision = module.compile_intent(load("expectation-gap.valid.json")).as_dict()
        self.assertEqual(decision["selectedRecipe"], "earnings-surprise")
        self.assertNotIn("visualTemplate", decision)
        self.assertNotIn("selectedVisualTemplate", decision)
        self.assertNotIn("component", decision)
        self.assertNotIn("rendererPath", decision)


if __name__ == "__main__":
    unittest.main()
