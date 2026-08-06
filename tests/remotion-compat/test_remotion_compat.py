from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sources = load_module(
    "materialize_renderer_sources_test",
    ROOT / "scripts/materialize_renderer_sources.py",
)
finalizer = load_module(
    "finalize_renderer_package_test",
    ROOT / "scripts/finalize_renderer_package.py",
)
projection = load_module(
    "remotion_240_projection_test",
    ROOT / "scripts/remotion_240_projection.py",
)


class RemotionCompatibilityTests(unittest.TestCase):
    date = "2026-08-06"

    def setUp(self):
        self.render_path = ROOT / f"render-specs/{self.date}/render_spec.json"
        self.bindings_path = (
            ROOT / f"working/{self.date}/financial_visual_bindings.json"
        )
        self.reaction_bindings_path = (
            ROOT / f"working/{self.date}/reaction_timeline_bindings.json"
        )
        self.raw = json.loads(self.render_path.read_text(encoding="utf-8"))
        self.bindings = json.loads(
            self.bindings_path.read_text(encoding="utf-8")
        )

    def normalized(self):
        normalized, mapping = sources.normalize_render_base(self.raw)
        sources._financial_contract(
            render=normalized,
            bindings=self.bindings,
            source_to_canonical=mapping,
        )
        sources._contract_scenes(normalized)
        return normalized, mapping

    def strict(self):
        normalized, _ = self.normalized()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            final_contract = root / "final.json"
            semantics = root / "semantics.json"
            compatibility = root / "compatibility.json"
            final_contract.write_text("{}\n", encoding="utf-8")
            semantics.write_text("{}\n", encoding="utf-8")
            compatibility.write_text("{}\n", encoding="utf-8")
            projected = finalizer._strict_renderer_projection(
                normalized,
                final_contract_path=final_contract,
                semantics_path=semantics,
                renderer_compatibility_path=compatibility,
            )
        return projected

    def canonical(self):
        projected = self.strict()
        projection.canonicalize_render_spec(
            projected,
            episode_date=self.date,
            reaction_bindings_path=self.reaction_bindings_path,
        )
        return projected

    def test_01_producer_projection_preserves_narration(self):
        before = [
            chunk["speechText"]
            for scene in self.raw["scenes"]
            for chunk in scene["narrationChunks"]
        ]
        normalized, mapping = sources.normalize_render_base(self.raw)
        after = [
            chunk["speechText"]
            for scene in normalized["scenes"]
            for chunk in scene["narrationChunks"]
        ]
        self.assertEqual(before, after)
        self.assertEqual(18, len(mapping))
        self.assertNotIn("tts", normalized)
        self.assertNotIn("imageSelection", normalized)
        self.assertNotIn("expectedConfirmed", normalized)
        self.assertNotIn("visualGrammarContractVersion", normalized)

    def test_02_sources_and_modes_are_renderer_compatible(self):
        normalized, _ = sources.normalize_render_base(self.raw)
        allowed_sources = {
            "official",
            "company",
            "major-media",
            "analyst",
            "market-data",
            "other",
        }
        self.assertTrue(
            all(
                item["sourceType"] in allowed_sources
                for item in normalized["sources"]
            )
        )
        self.assertNotIn(
            "memory-001",
            {item["sourceId"] for item in normalized["sources"]},
        )
        allowed_modes = {
            "conclusion-card",
            "number-comparison",
            "expected-actual-gap",
            "timeline",
            "chart",
            "causal-diagram",
            "stock-comparison",
            "news-media",
            "verification-points",
            "text-focus",
        }
        for scene in normalized["scenes"]:
            self.assertIn(scene["visualMode"], allowed_modes)
            for beat in scene["visualBeats"]:
                self.assertIn(beat["visualMode"], allowed_modes)

    def test_03_financial_bindings_exactly_cover_financial_templates(self):
        normalized, mapping = sources.normalize_render_base(self.raw)
        financial = sources._financial_contract(
            render=normalized,
            bindings=self.bindings,
            source_to_canonical=mapping,
        )
        self.assertEqual(2, len(financial["intents"]))
        self.assertEqual(4, len(financial["candidatePlans"]))
        self.assertEqual(
            {"market-snapshot", "entity-divergence"},
            {item["kind"] for item in financial["intents"]},
        )

    def test_04_strict_projection_flattens_visual_grammar(self):
        projected = self.strict()
        self.assertEqual(
            18,
            projected["visualGrammarContract"]["beatCount"],
        )
        for scene in projected["scenes"]:
            for beat in scene["visualBeats"]:
                self.assertIn("visualGrammarId", beat)
                self.assertIn("transitionRole", beat)
                self.assertNotIn("visualGrammar", beat)
                self.assertNotIn("visualBeatId", beat)

    def test_05_approved_card_lines_become_renderer_data_objects(self):
        projected = self.canonical()
        before_speech = [
            chunk["speechText"]
            for scene in projected["scenes"]
            for chunk in scene["narrationChunks"]
        ]
        after_speech = [
            chunk["speechText"]
            for scene in projected["scenes"]
            for chunk in scene["narrationChunks"]
        ]
        self.assertEqual(before_speech, after_speech)

        scene3 = projected["scenes"][2]
        number_ids = {item["numberId"] for item in scene3["numbers"]}
        self.assertGreaterEqual(len(number_ids), 6)
        for beat in scene3["visualBeats"]:
            self.assertEqual("number-comparison", beat["visualMode"])
            self.assertGreaterEqual(
                len(
                    [
                        item
                        for item in beat["objectIds"]
                        if item in number_ids
                    ]
                ),
                2,
            )

        scene4 = projected["scenes"][3]
        self.assertEqual(
            {"expected", "actual", "gap"},
            {item["role"] for item in scene4["cards"]},
        )
        self.assertEqual(
            "expected-actual-gap",
            scene4["visualBeats"][0]["visualMode"],
        )
        self.assertEqual(
            "text-focus",
            scene4["visualBeats"][1]["visualMode"],
        )
        self.assertEqual([], scene4["visualBeats"][1]["objectIds"])

    def test_06_scene_roles_and_return_states_are_canonical(self):
        projected = self.canonical()
        self.assertEqual(
            "opening-hook-market-direction-greeting-conclusion",
            projected["scenes"][0]["sceneRole"],
        )
        self.assertEqual(
            "closing-recap-sendoff-goodnight",
            projected["scenes"][8]["sceneRole"],
        )
        self.assertEqual(
            {"type": "none", "durationMs": 0},
            projected["scenes"][8]["transition"],
        )
        for scene in projected["scenes"]:
            beats = scene["visualBeats"]
            for index, beat in enumerate(beats[:-1]):
                if beat["returnScreenState"] is not None:
                    self.assertEqual(
                        beats[index + 1]["screenState"],
                        beat["returnScreenState"],
                    )

    def test_07_reaction_timeline_uses_official_times_plus_close(self):
        projected = self.canonical()
        beat = projected["scenes"][5]["visualBeats"][0]
        self.assertEqual(
            "event-reaction-timeline",
            beat["visualTemplate"],
        )
        self.assertEqual(
            "official-time-plus-close",
            beat["templateVariant"],
        )
        self.assertEqual(
            "official-time-plus-close",
            beat["templateConfig"]["variant"],
        )
        self.assertEqual(
            {
                "precision": "official-time-plus-close",
                "eventOrderIds": ["scene-06-card-001"],
                "seriesObjectIds": [],
            },
            beat["templateConfig"]["reactionTimeline"],
        )
        self.assertFalse(
            any(
                event.get("motionPreset") == "draw-line"
                and event.get("targetId") == "scene-06-card-001"
                for event in projected["scenes"][5]["visualEvents"]
            )
        )


if __name__ == "__main__":
    unittest.main()
