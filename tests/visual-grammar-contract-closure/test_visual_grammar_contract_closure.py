from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import visual_grammar_contract_closure as module  # noqa: E402


def final_contract() -> dict:
    return {
        "contractVersion": "1.1.0",
        "visualGrammarContractVersion": "1.0.0",
        "episodeDate": "2026-07-31",
        "scenes": [
            {
                "sceneId": "scene-01",
                "visualBeats": [
                    {
                        "visualBeatId": "vb-01-01",
                        "visualGrammar": {
                            "contractVersion": "1.0.0",
                            "grammarId": "contradiction",
                            "transitionRole": "major-shift",
                            "returnTargetBeatId": None,
                        },
                    }
                ],
            },
            {
                "sceneId": "scene-02",
                "visualBeats": [
                    {
                        "visualBeatId": "vb-02-01",
                        "visualGrammar": {
                            "contractVersion": "1.0.0",
                            "grammarId": "entity",
                            "transitionRole": "return",
                            "returnTargetBeatId": "vb-01-01",
                        },
                    }
                ],
            },
        ],
    }


def render_spec() -> dict:
    return {
        "schemaVersion": "2.4.0",
        "episode": {"id": "2026-07-31"},
        "visualGrammarContract": {"contractVersion": "1.0.0"},
        "scenes": [
            {
                "sceneId": "scene-01",
                "visualBeats": [
                    {
                        "beatId": "vb-01-01",
                        "visualGrammarId": "contradiction",
                        "transitionRole": "major-shift",
                        "returnTargetBeatId": None,
                    }
                ],
            },
            {
                "sceneId": "scene-02",
                "visualBeats": [
                    {
                        "beatId": "vb-02-01",
                        "visualGrammarId": "entity",
                        "transitionRole": "return",
                        "returnTargetBeatId": "vb-01-01",
                    }
                ],
            },
        ],
    }


class VisualGrammarContractClosureTests(unittest.TestCase):
    def test_exact_contract_passes(self):
        result = module.validate_final_contract_against_render(
            final_contract(), render_spec()
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["visualBeatCount"], 2)

    def test_grammar_mismatch_is_rejected(self):
        render = render_spec()
        render["scenes"][0]["visualBeats"][0]["visualGrammarId"] = "evidence"
        with self.assertRaisesRegex(
            module.VisualGrammarClosureError, "Visual Grammar mismatch"
        ):
            module.validate_final_contract_against_render(final_contract(), render)

    def test_transition_mismatch_is_rejected(self):
        render = render_spec()
        render["scenes"][0]["visualBeats"][0]["transitionRole"] = "continuation"
        with self.assertRaisesRegex(
            module.VisualGrammarClosureError, "Visual Grammar mismatch"
        ):
            module.validate_final_contract_against_render(final_contract(), render)

    def test_return_target_mismatch_is_rejected(self):
        render = render_spec()
        render["scenes"][1]["visualBeats"][0]["returnTargetBeatId"] = None
        with self.assertRaisesRegex(
            module.VisualGrammarClosureError, "Visual Grammar mismatch"
        ):
            module.validate_final_contract_against_render(final_contract(), render)

    def test_missing_beat_is_rejected(self):
        render = render_spec()
        render["scenes"].pop()
        with self.assertRaisesRegex(
            module.VisualGrammarClosureError, "Visual Beat set mismatch"
        ):
            module.validate_final_contract_against_render(final_contract(), render)

    def test_wrong_final_contract_version_is_rejected(self):
        final = final_contract()
        final["contractVersion"] = "1.0.0"
        with self.assertRaisesRegex(
            module.VisualGrammarClosureError, "must be 1.1.0"
        ):
            module.validate_final_contract_against_render(final, render_spec())

    def test_wrong_render_spec_version_is_rejected(self):
        render = render_spec()
        render["schemaVersion"] = "2.3.0"
        with self.assertRaisesRegex(
            module.VisualGrammarClosureError, "must be 2.4.0"
        ):
            module.validate_final_contract_against_render(final_contract(), render)

    def test_episode_date_mismatch_is_rejected(self):
        render = render_spec()
        render["episode"]["id"] = "2026-08-01"
        with self.assertRaisesRegex(
            module.VisualGrammarClosureError, "episode date mismatch"
        ):
            module.validate_final_contract_against_render(final_contract(), render)


if __name__ == "__main__":
    unittest.main()
