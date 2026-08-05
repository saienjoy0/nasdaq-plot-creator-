from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import financial_recipe_compiler as compiler  # noqa: E402

FIX = ROOT / "tests" / "final-episode-contract" / "fixtures"


class FinancialRecipeCompilerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        for name in (
            "final_episode_contract.schema.json",
            "financial_visual_candidate_plan.schema.json",
            "financial_recipe_registry.json",
            "financial_recipe_plan.schema.json",
        ):
            (self.repo / "contracts").mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "contracts" / name, self.repo / "contracts" / name)
        fixture_dir = self.repo / "tests" / "final-episode-contract" / "fixtures"
        fixture_dir.mkdir(parents=True)
        shutil.copy2(FIX / "episode_package_2026-07-31.md", fixture_dir)
        shutil.copy2(FIX / "final_episode_contract.valid.json", fixture_dir)
        self.contract_path = fixture_dir / "final_episode_contract.valid.json"

    def tearDown(self):
        self.tempdir.cleanup()

    def load(self) -> dict:
        return json.loads(self.contract_path.read_text(encoding="utf-8"))

    def save(self, contract: dict, *, replace_annex: bool = True) -> None:
        package = self.repo / contract["episodePackage"]["path"]
        if replace_annex:
            text = package.read_text(encoding="utf-8")
            start = text.index("<!--BEGIN_FINANCIAL_VISUAL_ANNEX-->")
            end = text.index("<!--END_FINANCIAL_VISUAL_ANNEX-->") + len("<!--END_FINANCIAL_VISUAL_ANNEX-->")
            block = (
                "<!--BEGIN_FINANCIAL_VISUAL_ANNEX-->\n```json\n"
                + json.dumps(contract["financialVisuals"], ensure_ascii=False, indent=2)
                + "\n```\n<!--END_FINANCIAL_VISUAL_ANNEX-->"
            )
            package.write_text(text[:start] + block + text[end:], encoding="utf-8")
        contract["episodePackage"]["sha256"] = hashlib.sha256(package.read_bytes()).hexdigest()
        self.contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def compile(self) -> dict:
        return compiler.compile_recipe_plan(
            self.contract_path,
            self.repo,
            self.repo / "contracts" / "financial_recipe_registry.json",
            self.repo / "contracts" / "financial_recipe_plan.schema.json",
            self.repo / "contracts" / "final_episode_contract.schema.json",
            self.repo / "contracts" / "financial_visual_candidate_plan.schema.json",
        )

    def intent(self, contract: dict) -> dict:
        return contract["financialVisuals"]["intents"][0]

    def plans(self, contract: dict) -> tuple[dict, dict]:
        plans = contract["financialVisuals"]["candidatePlans"]
        return next(plan for plan in plans if plan["path"] == "preferred"), next(plan for plan in plans if plan["path"] == "fallback")

    def test_valid_expectation_gap_selects_preferred(self):
        plan = self.compile()
        selection = plan["selections"][0]
        self.assertEqual(selection["selectedPath"], "preferred")
        self.assertEqual(selection["selectedRecipeId"], "earnings-surprise")
        self.assertEqual(selection["reasonCodes"], [])
        self.assertEqual(selection["fallbackDiversityRecheck"], "not-required")

    def test_gap_mismatch_selects_preapproved_fallback(self):
        contract = self.load()
        self.intent(contract)["metrics"][2]["numericValue"] = 1.2
        self.save(contract)
        selection = self.compile()["selections"][0]
        self.assertEqual(selection["selectedPath"], "fallback")
        self.assertEqual(selection["selectedRecipeId"], "expected-anchor")
        self.assertIn("GAP_VALUE_MISMATCH", selection["reasonCodes"])
        self.assertEqual(selection["fallbackDiversityRecheck"], "required")

    def test_entity_mismatch_stops_when_fallback_comparison_is_also_invalid(self):
        contract = self.load()
        self.intent(contract)["metrics"][1]["entityId"] = "other-entity"
        self.save(contract)
        with self.assertRaisesRegex(compiler.CompileError, "EXPECTED_ACTUAL_ENTITY_MISMATCH"):
            self.compile()

    def test_period_mismatch_selects_fallback(self):
        contract = self.load()
        self.intent(contract)["metrics"][2]["period"] = "2026 Q1"
        self.save(contract)
        self.assertIn("EXPECTED_ACTUAL_PERIOD_MISMATCH", self.compile()["selections"][0]["reasonCodes"])

    def test_currency_mismatch_selects_fallback(self):
        contract = self.load()
        self.intent(contract)["metrics"][2]["currency"] = "JPY"
        self.save(contract)
        self.assertIn("EXPECTED_ACTUAL_CURRENCY_MISMATCH", self.compile()["selections"][0]["reasonCodes"])

    def test_disallowed_preferred_template_selects_fallback(self):
        contract = self.load()
        preferred, _ = self.plans(contract)
        preferred["visualTemplateId"] = "expected-actual-bullet"
        self.save(contract)
        selection = self.compile()["selections"][0]
        self.assertEqual(selection["selectedPath"], "fallback")
        self.assertIn("RECIPE_TEMPLATE_PAIR_NOT_ALLOWED", selection["reasonCodes"])

    def test_invalid_fallback_stops_compilation(self):
        contract = self.load()
        _, fallback = self.plans(contract)
        fallback["visualTemplateId"] = "earnings-surprise"
        self.save(contract)
        with self.assertRaisesRegex(compiler.CompileError, "FALLBACK_PLAN_INVALID"):
            self.compile()

    def test_output_is_deterministic_and_sha_bound(self):
        first = self.compile()
        second = self.compile()
        self.assertEqual(compiler.canonical_bytes(first), compiler.canonical_bytes(second))
        self.assertEqual(first["finalEpisodeContract"]["sha256"], hashlib.sha256(self.contract_path.read_bytes()).hexdigest())
        selected = first["selections"][0]
        preferred, _ = self.plans(self.load())
        self.assertEqual(selected["selectedPlanSha256"], compiler.canonical_sha256(preferred))

    def test_recipe_plan_contains_only_selected_route(self):
        selection = self.compile()["selections"][0]
        self.assertNotIn("fallbackPlanId", selection)
        self.assertNotIn("preferredPlanId", selection)
        self.assertNotIn("unselectedPlan", selection)

    def test_market_snapshot_requires_three_metrics_for_preferred(self):
        contract = self.load()
        intent = self.intent(contract)
        preferred, fallback = self.plans(contract)
        intent["kind"] = "market-snapshot"
        intent["dataPrecision"] = "market-close"
        intent["metrics"] = [
            {
                "metricId": "nasdaq-close",
                "label": "Nasdaq close",
                "role": "market",
                "valueText": "+0.5%",
                "numericValue": 0.5,
                "unit": "percent",
                "currency": None,
                "period": "2026-07-31 session",
                "entityId": "nasdaq-composite",
                "sessionDate": "2026-07-31",
                "sourceIds": ["source-001"],
            }
        ]
        preferred.update({
            "recipeId": "market-pulse-grid",
            "visualTemplateId": "market-pulse-grid",
            "metricIds": ["nasdaq-close"],
            "displayOrder": ["nasdaq-close"],
            "highlightObjectIds": ["nasdaq-close"],
        })
        fallback.update({
            "recipeId": "opening-contradiction",
            "visualTemplateId": "opening-contradiction",
            "metricIds": ["nasdaq-close"],
            "displayOrder": ["nasdaq-close"],
            "highlightObjectIds": ["nasdaq-close"],
        })
        self.save(contract)
        selection = self.compile()["selections"][0]
        self.assertEqual(selection["selectedPath"], "fallback")
        self.assertIn("MARKET_METRIC_COUNT_INVALID", selection["reasonCodes"])

    def test_entity_divergence_same_entity_stops_when_fallback_also_invalid(self):
        contract = self.load()
        intent = self.intent(contract)
        preferred, fallback = self.plans(contract)
        intent["kind"] = "entity-divergence"
        intent["dataPrecision"] = "market-close"
        intent["metrics"] = [
            {
                "metricId": "left",
                "label": "Left",
                "role": "left-entity",
                "valueText": "+1%",
                "numericValue": 1.0,
                "unit": "percent",
                "currency": None,
                "period": "session",
                "entityId": "same",
                "sessionDate": "2026-07-31",
                "sourceIds": ["source-001"],
            },
            {
                "metricId": "right",
                "label": "Right",
                "role": "right-entity",
                "valueText": "-1%",
                "numericValue": -1.0,
                "unit": "percent",
                "currency": None,
                "period": "session",
                "entityId": "same",
                "sessionDate": "2026-07-31",
                "sourceIds": ["source-001"],
            },
        ]
        for plan, recipe, template in (
            (preferred, "dual-asset-split", "dual-asset-split"),
            (fallback, "split-opposition", "split-comparison"),
        ):
            plan.update({
                "recipeId": recipe,
                "visualTemplateId": template,
                "metricIds": ["left", "right"],
                "displayOrder": ["left", "right"],
                "highlightObjectIds": ["left"],
            })
        self.save(contract)
        with self.assertRaisesRegex(compiler.CompileError, "DIVERGENCE_ENTITY_NOT_DISTINCT"):
            self.compile()

    def test_macro_preferred_requires_anchor_but_fallback_can_use_causal_steps(self):
        contract = self.load()
        intent = self.intent(contract)
        preferred, fallback = self.plans(contract)
        intent["kind"] = "macro-transmission"
        intent["dataPrecision"] = "qualitative-only"
        intent["metrics"] = []
        intent["causalSteps"] = [
            {"stepId": "rates", "label": "Rates rose", "sourceIds": ["source-001"]},
            {"stepId": "nasdaq", "label": "Valuation pressure", "sourceIds": ["source-001"]},
        ]
        for plan, recipe, template in (
            (preferred, "macro-pressure", "macro-pressure"),
            (fallback, "causal-build", "causal-lane"),
        ):
            plan.update({
                "recipeId": recipe,
                "visualTemplateId": template,
                "metricIds": [],
                "causalStepIds": ["rates", "nasdaq"],
                "displayOrder": ["rates", "nasdaq"],
                "highlightObjectIds": ["nasdaq"],
                "templateVariant": "left-to-right",
            })
        self.save(contract)
        selection = self.compile()["selections"][0]
        self.assertEqual(selection["selectedPath"], "fallback")
        self.assertIn("MACRO_ANCHOR_COUNT_INVALID", selection["reasonCodes"])

    def test_verified_series_policy_requires_verified_precision(self):
        contract = self.load()
        intent = self.intent(contract)
        intent["chartPolicy"] = "verified-series-only"
        intent["dataPrecision"] = "market-close"
        self.save(contract)
        with self.assertRaisesRegex(Exception, "verified-intraday-series"):
            self.compile()


if __name__ == "__main__":
    unittest.main()
