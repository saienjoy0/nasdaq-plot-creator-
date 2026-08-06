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


sources = load_module("renderer_sources_test", SCRIPTS / "materialize_renderer_sources.py")
base = load_module("renderer_finalizer_test", SCRIPTS / "finalize_renderer_package.py")
projection = load_module("remotion_projection_test", SCRIPTS / "remotion_240_projection.py")
template_data = load_module("remotion_template_data_test", SCRIPTS / "remotion_template_data.py")
sequence = load_module("remotion_sequence_test", SCRIPTS / "remotion_sequence_policy.py")


class RemotionCompatibilityTests(unittest.TestCase):
    date = "2026-08-06"

    def setUp(self):
        self.raw = json.loads(
            (ROOT / f"render-specs/{self.date}/render_spec.json").read_text(encoding="utf-8")
        )
        self.bindings = json.loads(
            (ROOT / f"working/{self.date}/financial_visual_bindings.json").read_text(encoding="utf-8")
        )
        self.reaction_bindings = ROOT / f"working/{self.date}/reaction_timeline_bindings.json"

    def normalized(self):
        render, mapping = sources.normalize_render_base(self.raw)
        sources._financial_contract(
            render=render,
            bindings=self.bindings,
            source_to_canonical=mapping,
        )
        sources._contract_scenes(render)
        return render, mapping

    def strict(self):
        render, _ = self.normalized()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            files = [root / name for name in ("final.json", "semantics.json", "compatibility.json")]
            for path in files:
                path.write_text("{}\n", encoding="utf-8")
            return base._strict_renderer_projection(
                render,
                final_contract_path=files[0],
                semantics_path=files[1],
                renderer_compatibility_path=files[2],
            )

    def canonical(self):
        render = self.strict()
        projection.canonicalize_render_spec(
            render,
            episode_date=self.date,
            reaction_bindings_path=self.reaction_bindings,
        )
        template_data.materialize_template_data(render)
        sequence.resolve_sequence_policies(render)
        return render

    def test_01_narration_is_unchanged(self):
        before = [c["speechText"] for s in self.raw["scenes"] for c in s["narrationChunks"]]
        after_render, mapping = sources.normalize_render_base(self.raw)
        after = [c["speechText"] for s in after_render["scenes"] for c in s["narrationChunks"]]
        self.assertEqual(before, after)
        self.assertEqual(18, len(mapping))

    def test_02_producer_only_fields_and_memory_source_are_removed(self):
        render, _ = sources.normalize_render_base(self.raw)
        for key in ("tts", "imageSelection", "expectedConfirmed", "visualGrammarContractVersion"):
            self.assertNotIn(key, render)
        self.assertNotIn("memory-001", {source["sourceId"] for source in render["sources"]})
        self.assertTrue(
            all(
                source["sourceType"]
                in {"official", "company", "major-media", "analyst", "market-data", "other"}
                for source in render["sources"]
            )
        )

    def test_03_financial_bindings_cover_selected_templates(self):
        render, mapping = sources.normalize_render_base(self.raw)
        financial = sources._financial_contract(
            render=render,
            bindings=self.bindings,
            source_to_canonical=mapping,
        )
        self.assertEqual(2, len(financial["intents"]))
        self.assertEqual(4, len(financial["candidatePlans"]))
        self.assertEqual(
            {"market-snapshot", "entity-divergence"},
            {intent["kind"] for intent in financial["intents"]},
        )

    def test_04_visual_grammar_is_flattened_for_all_18_beats(self):
        render = self.strict()
        self.assertEqual(18, render["visualGrammarContract"]["beatCount"])
        for scene in render["scenes"]:
            for beat in scene["visualBeats"]:
                self.assertIn("visualGrammarId", beat)
                self.assertIn("transitionRole", beat)
                self.assertNotIn("visualGrammar", beat)
                self.assertNotIn("visualBeatId", beat)

    def test_05_card_lines_become_numeric_and_eag_objects(self):
        render = self.canonical()
        scene2 = render["scenes"][1]
        beat2 = scene2["visualBeats"][1]
        number_map = {number["numberId"]: number for number in scene2["numbers"]}
        self.assertEqual("number-comparison", beat2["visualMode"])
        self.assertEqual("tailwind-headwind", beat2["visualTemplate"])
        self.assertEqual("two-lane", beat2["templateVariant"])
        self.assertEqual("evidence", beat2["visualGrammarId"])
        self.assertEqual(2, len(beat2["objectIds"]))
        self.assertTrue(all(number_map[item]["numericValue"] is not None for item in beat2["objectIds"]))
        self.assertEqual("major-shift", render["scenes"][2]["visualBeats"][0]["transitionRole"])
        scene4 = render["scenes"][3]
        self.assertEqual({"expected", "actual", "gap"}, {card["role"] for card in scene4["cards"]})
        self.assertEqual("text-focus", scene4["visualBeats"][1]["visualMode"])
        self.assertEqual([], scene4["visualBeats"][1]["objectIds"])

    def test_06_causal_card_becomes_nodes_and_arrows(self):
        render = self.canonical()
        scene5 = render["scenes"][4]
        beat = scene5["visualBeats"][1]
        node_ids = {node["nodeId"] for node in scene5["nodes"]}
        arrow_ids = {arrow["arrowId"] for arrow in scene5["arrows"]}
        self.assertEqual("causal-diagram", beat["visualMode"])
        self.assertEqual(3, len([item for item in beat["objectIds"] if item in node_ids]))
        self.assertEqual(2, len([item for item in beat["objectIds"] if item in arrow_ids]))
        self.assertEqual(3, len(beat["templateConfig"]["nodeOrder"]))
        object_order = {item: index for index, item in enumerate(beat["objectIds"])}
        for arrow in scene5["arrows"]:
            if arrow["arrowId"] not in object_order:
                continue
            self.assertGreater(object_order[arrow["arrowId"]], object_order[arrow["fromNodeId"]])
            self.assertGreater(object_order[arrow["arrowId"]], object_order[arrow["toNodeId"]])

    def test_07_reaction_timeline_and_terminal_scene_are_explicit(self):
        render = self.canonical()
        beat = render["scenes"][5]["visualBeats"][0]
        self.assertEqual("official-time-plus-close", beat["templateVariant"])
        self.assertEqual(
            {
                "precision": "official-time-plus-close",
                "eventOrderIds": ["scene-06-card-001"],
                "seriesObjectIds": [],
            },
            beat["templateConfig"]["reactionTimeline"],
        )
        self.assertEqual({"type": "none", "durationMs": 0}, render["scenes"][8]["transition"])
        self.assertEqual("closing-recap-sendoff-goodnight", render["scenes"][8]["sceneRole"])

    def test_08_sequence_policy_matches_transformed_objects(self):
        render = self.canonical()
        allowed = {"explicit", "object-order-fallback", "static"}
        for scene in render["scenes"]:
            for beat in scene["visualBeats"]:
                self.assertIn(beat["sequencePolicy"], allowed)
                if not beat["objectIds"]:
                    self.assertEqual("static", beat["sequencePolicy"])


if __name__ == "__main__":
    unittest.main()
