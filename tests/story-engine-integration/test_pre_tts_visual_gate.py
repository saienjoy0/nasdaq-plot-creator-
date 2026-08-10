from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/pre_tts_visual_gate.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PreTTSVisualGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_module("pre_tts_visual_gate_test", SCRIPT)
        cls.render_path = ROOT / "render-specs/2026-08-06/render_spec.json"
        cls.bindings_path = ROOT / "working/2026-08-06/story-engine/story_production_bindings.json"
        cls.semantics_path = ROOT / "contracts/visual_grammar_semantics.json"
        cls.semantics_schema_path = ROOT / "contracts/visual_grammar_semantics.schema.json"
        cls.compatibility_path = ROOT / "contracts/visual_grammar_renderer_compatibility.json"
        cls.report_schema_path = ROOT / "contracts/visual_grammar_structural_report.schema.json"

    def load_inputs(self):
        return {
            "render": json.loads(self.render_path.read_text(encoding="utf-8")),
            "story_bindings": json.loads(self.bindings_path.read_text(encoding="utf-8")),
            "semantics": json.loads(self.semantics_path.read_text(encoding="utf-8")),
            "semantics_schema": json.loads(self.semantics_schema_path.read_text(encoding="utf-8")),
            "compatibility_registry": json.loads(self.compatibility_path.read_text(encoding="utf-8")),
            "report_schema": json.loads(self.report_schema_path.read_text(encoding="utf-8")),
        }

    def test_2026_08_06_authored_visuals_pass_pre_tts_gate(self):
        inputs = self.load_inputs()
        report = self.gate.validate_pre_tts(**inputs)
        self.assertEqual("PASS", report["status"], report)

    def test_evidence_plus_text_focus_fails_before_renderer(self):
        inputs = self.load_inputs()
        bindings = copy.deepcopy(inputs["story_bindings"])
        override = bindings["beat_overrides"]["scene-08-beat-002"]
        override["visualTemplate"] = "text-focus"
        override["templateVariant"] = "default"
        inputs["story_bindings"] = bindings
        report = self.gate.validate_pre_tts(**inputs)
        self.assertEqual("FAIL", report["status"])
        matching = [
            item
            for item in report["violations"]
            if item["code"] == "VG_GRAMMAR_TEMPLATE_MISMATCH"
        ]
        self.assertTrue(matching, report)
        self.assertTrue(any("text-focus" in item["message"] for item in matching))

    def test_unknown_template_fails_closed(self):
        inputs = self.load_inputs()
        bindings = copy.deepcopy(inputs["story_bindings"])
        bindings["beat_overrides"]["scene-08-beat-002"]["visualTemplate"] = "not-a-template"
        inputs["story_bindings"] = bindings
        report = self.gate.validate_pre_tts(**inputs)
        self.assertEqual("FAIL", report["status"])
        self.assertTrue(
            any(
                item["code"] == "VG_GRAMMAR_TEMPLATE_MISMATCH"
                and "unregistered" in item["message"]
                for item in report["violations"]
            )
        )

    def test_malformed_compatibility_mirror_fails_closed(self):
        inputs = self.load_inputs()
        registry = copy.deepcopy(inputs["compatibility_registry"])
        del registry["templates"][0]["appearanceClass"]
        inputs["compatibility_registry"] = registry
        with self.assertRaises(self.gate.PreTTSVisualGateError):
            self.gate.validate_pre_tts(**inputs)

    def test_validation_does_not_mutate_input_render_or_bindings(self):
        inputs = self.load_inputs()
        render_before = copy.deepcopy(inputs["render"])
        bindings_before = copy.deepcopy(inputs["story_bindings"])
        self.gate.validate_pre_tts(**inputs)
        self.assertEqual(render_before, inputs["render"])
        self.assertEqual(bindings_before, inputs["story_bindings"])


if __name__ == "__main__":
    unittest.main()
