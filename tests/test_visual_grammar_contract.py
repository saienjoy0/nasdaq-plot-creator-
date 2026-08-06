from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import visual_grammar_contract as module  # noqa: E402

REGISTRY = json.loads(
    (ROOT / "contracts" / "visual_grammar_semantics.json").read_text(
        encoding="utf-8"
    )
)
SCHEMA = json.loads(
    (ROOT / "contracts" / "visual_grammar_semantics.schema.json").read_text(
        encoding="utf-8"
    )
)


def beat(
    scene: int,
    number: int,
    grammar: str,
    transition: str = "continuation",
    target: str | None = None,
) -> dict:
    return {
        "visualBeatId": f"vb-{scene:02d}-{number:02d}",
        "visualGrammar": {
            "contractVersion": "1.0.0",
            "grammarId": grammar,
            "transitionRole": transition,
            "returnTargetBeatId": target,
        },
    }


def valid_episode() -> dict:
    scene_grammars = {
        1: [("contradiction", "major-shift")],
        2: [("entity", "major-shift"), ("comparison", "continuation")],
        3: [("evidence", "major-shift")],
        4: [("gap", "major-shift"), ("analogy", "return")],
        5: [("causal", "major-shift")],
        6: [("reaction", "major-shift"), ("evidence", "continuation")],
        7: [("comparison", "major-shift")],
        8: [("verification", "major-shift")],
        9: [("assembly", "closing")],
    }
    scenes = []
    for scene_number in range(1, 10):
        visual_beats = []
        for index, (grammar, transition) in enumerate(
            scene_grammars[scene_number], start=1
        ):
            target = "vb-04-01" if transition == "return" else None
            visual_beats.append(
                beat(scene_number, index, grammar, transition, target)
            )
        scenes.append(
            {
                "sceneId": f"scene-{scene_number:02d}",
                "visualBeats": visual_beats,
            }
        )
    return {
        "episodeDate": "2026-08-06",
        "visualGrammarContractVersion": "1.0.0",
        "expectedConfirmed": True,
        "scene5CausalExceptionReason": None,
        "scenes": scenes,
    }


class VisualGrammarContractTests(unittest.TestCase):
    def test_registry_is_valid_and_complete(self):
        module.validate_registry(REGISTRY, SCHEMA)

    def test_valid_episode_passes(self):
        report = module.validate_episode(valid_episode(), REGISTRY)
        self.assertEqual(report["status"], "PASS")
        self.assertGreaterEqual(report["semanticGrammarCount"], 6)
        self.assertGreaterEqual(report["majorShiftCount"], 4)

    def test_every_beat_requires_explicit_grammar(self):
        episode = valid_episode()
        episode["scenes"][0]["visualBeats"][0].pop("visualGrammar")
        report = module.validate_episode(episode, REGISTRY)
        self.assertIn(
            "VG_DECLARATION_MISSING",
            {violation["code"] for violation in report["violations"]},
        )

    def test_unknown_grammar_is_rejected(self):
        episode = valid_episode()
        episode["scenes"][0]["visualBeats"][0]["visualGrammar"][
            "grammarId"
        ] = "auto-guessed"
        report = module.validate_episode(episode, REGISTRY)
        self.assertIn(
            "VG_UNKNOWN_GRAMMAR",
            {violation["code"] for violation in report["violations"]},
        )

    def test_return_requires_existing_target(self):
        episode = valid_episode()
        episode["scenes"][3]["visualBeats"][1]["visualGrammar"][
            "returnTargetBeatId"
        ] = "vb-99-99"
        report = module.validate_episode(episode, REGISTRY)
        self.assertIn(
            "VG_RETURN_TARGET_UNKNOWN",
            {violation["code"] for violation in report["violations"]},
        )

    def test_bridge_text_does_not_inflate_diversity(self):
        episode = valid_episode()
        for scene in episode["scenes"][:8]:
            for visual_beat in scene["visualBeats"]:
                visual_beat["visualGrammar"]["grammarId"] = "bridge-text"
                visual_beat["visualGrammar"]["transitionRole"] = "continuation"
                visual_beat["visualGrammar"]["returnTargetBeatId"] = None
        report = module.validate_episode(episode, REGISTRY)
        codes = {violation["code"] for violation in report["violations"]}
        self.assertIn("VG_GRAMMAR_COUNT_TOO_LOW", codes)
        self.assertIn("VG_BRIDGE_TEXT_OVERUSED", codes)

    def test_expected_confirmed_requires_gap_in_scene4(self):
        episode = valid_episode()
        episode["scenes"][3]["visualBeats"][0]["visualGrammar"][
            "grammarId"
        ] = "evidence"
        report = module.validate_episode(episode, REGISTRY)
        self.assertIn(
            "VG_SCENE4_GAP_MISSING",
            {violation["code"] for violation in report["violations"]},
        )

    def test_reason_unknown_may_omit_scene5_causal_with_reason(self):
        episode = valid_episode()
        episode["scenes"][4]["visualBeats"][0]["visualGrammar"][
            "grammarId"
        ] = "evidence"
        episode["scene5CausalExceptionReason"] = "明確な因果経路を確認できないため"
        report = module.validate_episode(episode, REGISTRY)
        self.assertNotIn(
            "VG_SCENE5_CAUSAL_MISSING",
            {violation["code"] for violation in report["violations"]},
        )

    def test_registry_rejects_counted_assembly(self):
        registry = copy.deepcopy(REGISTRY)
        next(
            item
            for item in registry["grammars"]
            if item["grammarId"] == "assembly"
        )["counted"] = True
        with self.assertRaisesRegex(module.VisualGrammarError, "must not count"):
            module.validate_registry(registry, SCHEMA)


if __name__ == "__main__":
    unittest.main()
