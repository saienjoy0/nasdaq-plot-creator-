from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pre_tts_visual_gate as module  # noqa: E402


def compatibility() -> dict[str, dict]:
    return {
        "data-card": {
            "visualTemplateId": "data-card",
            "allowedGrammarIds": ["evidence"],
            "appearanceClass": "card",
            "dominantSurface": "panel",
            "stageShell": "default",
            "motionLanguage": "standard",
            "variantOverrides": [],
        }
    }


def render(template: str = "data-card") -> dict:
    scenes = []
    for scene_index in range(8):
        scenes.append(
            {
                "sceneId": f"scene-{scene_index + 1:02d}",
                "visualBeats": [
                    {
                        "visualBeatId": f"vb-{scene_index + 1:02d}-01",
                        "visualTemplate": template,
                        "visualGrammar": {
                            "grammarId": "evidence",
                            "transitionRole": "major-shift" if scene_index else "continuation",
                        },
                    }
                ],
            }
        )
    return {"scenes": scenes}


def report() -> dict:
    return {"status": "PASS", "violations": [], "warnings": []}


class VisualGateWarningBoundaryTests(unittest.TestCase):
    def test_editorial_homogeneity_warns_but_does_not_stop_production(self):
        result = report()
        module._validate_renderer_compatibility(render(), result, compatibility())
        codes = {warning["code"] for warning in result["warnings"]}
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["violations"], [])
        self.assertIn("VG_APPEARANCE_COUNT_TOO_LOW", codes)
        self.assertIn("VG_DOMINANT_SURFACE_COUNT_TOO_LOW", codes)
        self.assertIn("VG_SAME_APPEARANCE_RUN_TOO_LONG", codes)
        self.assertIn("VG_MAJOR_SHIFT_NOT_PHYSICAL", codes)

    def test_unregistered_template_remains_hard_failure(self):
        result = report()
        module._validate_renderer_compatibility(
            render(template="not-registered"), result, compatibility()
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "VG_GRAMMAR_TEMPLATE_MISMATCH",
            {violation["code"] for violation in result["violations"]},
        )

    def test_grammar_template_incompatibility_remains_hard_failure(self):
        bad = render()
        bad["scenes"][0]["visualBeats"][0]["visualGrammar"]["grammarId"] = "causal"
        result = report()
        module._validate_renderer_compatibility(bad, result, compatibility())
        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "VG_GRAMMAR_TEMPLATE_MISMATCH",
            {violation["code"] for violation in result["violations"]},
        )


if __name__ == "__main__":
    unittest.main()
