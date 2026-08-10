from __future__ import annotations

import copy
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


cross = load_module("financial_cross_h3_test", SCRIPTS / "financial_visual_cross_artifact.py")
compat = load_module("renderer_compat_h3_test", SCRIPTS / "finalize_renderer_package_compat.py")
base = load_module("renderer_base_h3_test", SCRIPTS / "finalize_renderer_package.py")
projection = load_module("renderer_projection_h3_test", SCRIPTS / "remotion_240_projection.py")
template_data = load_module("renderer_template_h3_test", SCRIPTS / "remotion_template_data.py")
sequence = load_module("renderer_sequence_h3_test", SCRIPTS / "remotion_sequence_policy.py")
sources = load_module("renderer_sources_h3_test", SCRIPTS / "materialize_renderer_sources.py")


class Renderer240TransactionTests(unittest.TestCase):
    date = "2026-08-06"

    def canonical_render(self):
        raw = json.loads(
            (ROOT / f"render-specs/{self.date}/render_spec.json").read_text(encoding="utf-8")
        )
        bindings = json.loads(
            (ROOT / f"working/{self.date}/financial_visual_bindings.json").read_text(encoding="utf-8")
        )
        terminal = json.loads(
            (ROOT / f"working/{self.date}/terminal_assembly_bindings.json").read_text(encoding="utf-8")
        )
        render, mapping = sources.normalize_render_base(raw)
        sources._financial_contract(render=render, bindings=bindings, source_to_canonical=mapping)
        sources._contract_scenes(render)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            files = [root / name for name in ("final.json", "semantics.json", "compatibility.json")]
            for path in files:
                path.write_text("{}\n", encoding="utf-8")
            strict = base._strict_renderer_projection(
                render,
                final_contract_path=files[0],
                semantics_path=files[1],
                renderer_compatibility_path=files[2],
            )
        projection.canonicalize_render_spec(
            strict,
            episode_date=self.date,
            reaction_bindings_path=ROOT / f"working/{self.date}/reaction_timeline_bindings.json",
        )
        template_data.materialize_template_data(strict, terminal_binding=terminal)
        sequence.resolve_sequence_policies(strict)
        return strict

    def test_2_4_matrix_is_approved_without_runtime_global_mutation(self):
        path = ROOT / "contracts/financial_visual_compatibility_2_4.json"
        matrix, digest = cross.validate_compatibility_matrix(path, "2.4.0")
        self.assertEqual("2.4.0", matrix["renderer"]["renderSpecVersion"])
        self.assertEqual(64, len(digest))

    def test_compat_finalizer_contains_no_module_monkey_patch(self):
        source = (SCRIPTS / "finalize_renderer_package_compat.py").read_text(encoding="utf-8")
        self.assertNotIn("EXPECTED_COMPATIBILITY_MATRIX =", source)
        self.assertNotIn(".final_contract_module.validate_contract =", source)
        self.assertNotIn("recipe_compiler.final_contract_module.validate_contract =", source)
        self.assertIn("final_contract_validator=_validator_adapter", source)
        self.assertIn("recipe_plan_compiler=_compile_recipe_plan_adapter", source)

    def test_referential_integrity_accepts_known_good_canonical_fixture(self):
        compat._validate_referential_integrity(self.canonical_render())

    def test_referential_integrity_rejects_dangling_beat_object(self):
        render = self.canonical_render()
        damaged = copy.deepcopy(render)
        damaged["scenes"][0]["visualBeats"][0]["objectIds"].append("missing-object")
        with self.assertRaises(compat.CompatibilityFinalizationError):
            compat._validate_referential_integrity(damaged)

    def test_expected_gap_projection_preserves_unrelated_followup_cards(self):
        scene = {
            "sceneId": "scene-test",
            "cards": [
                {
                    "cardId": "source-gap-card",
                    "title": "Expected / Actual / Gap",
                    "lines": [
                        {"label": "Expected", "value": "+80k", "tone": "neutral"},
                        {"label": "Actual", "value": "-23k", "tone": "negative"},
                        {"label": "Gap", "value": "-103k", "tone": "negative"},
                    ],
                },
                {
                    "cardId": "followup-card",
                    "title": "Follow-up evidence",
                    "lines": [{"label": "Boundary", "value": "kept", "tone": "neutral"}],
                },
            ],
            "visualEvents": [
                {
                    "eventId": "event-001",
                    "action": "show",
                    "targetId": "source-gap-card",
                },
                {
                    "eventId": "event-002",
                    "action": "show",
                    "targetId": "followup-card",
                },
            ],
        }
        beat = {"beatId": "scene-test-beat-001", "objectIds": ["source-gap-card"]}
        used_event_ids = {"event-001", "event-002"}

        projection._materialize_expected_actual_gap(scene, beat, used_event_ids)

        card_ids = [item["cardId"] for item in scene["cards"]]
        self.assertEqual(
            [
                "scene-test-card-expected",
                "scene-test-card-actual",
                "scene-test-card-gap",
                "followup-card",
            ],
            card_ids,
        )
        self.assertEqual(
            ["scene-test-card-expected", "scene-test-card-actual", "scene-test-card-gap"],
            beat["objectIds"],
        )
        event_targets = [item.get("targetId") for item in scene["visualEvents"]]
        self.assertIn("followup-card", event_targets)
        self.assertIn("scene-test-card-expected", event_targets)
        self.assertIn("scene-test-card-actual", event_targets)
        self.assertIn("scene-test-card-gap", event_targets)
        self.assertNotIn("source-gap-card", event_targets)

    def test_renderer_card_projection_drops_legacy_producer_only_fields(self):
        scene = {
            "sceneId": "scene-test",
            "cards": [
                {
                    "cardId": "card-001",
                    "role": None,
                    "title": "Verified timing",
                    "label": "producer-only label",
                    "text": "producer-only text",
                    "sourceId": "source-001",
                    "lines": [
                        {
                            "label": "QQQ",
                            "value": "719.16 → 720.23",
                            "tone": "neutral",
                            "sourceId": "source-001",
                            "note": "producer-only note",
                        }
                    ],
                }
            ],
        }

        projection._normalize_renderer_cards(scene)

        self.assertEqual(
            {
                "cardId": "card-001",
                "role": None,
                "title": "Verified timing",
                "lines": [
                    {
                        "label": "QQQ",
                        "value": "719.16 → 720.23",
                        "tone": "neutral",
                    }
                ],
            },
            scene["cards"][0],
        )

    def test_snapshot_restore_is_byte_exact_and_removes_new_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            existing = root / "existing.json"
            created = root / "created.json"
            existing.write_bytes(b"before\n")
            snap = compat._snapshot([existing, created])
            existing.write_bytes(b"after\n")
            created.write_bytes(b"new\n")
            compat._restore(snap)
            self.assertEqual(b"before\n", existing.read_bytes())
            self.assertFalse(created.exists())


if __name__ == "__main__":
    unittest.main()
