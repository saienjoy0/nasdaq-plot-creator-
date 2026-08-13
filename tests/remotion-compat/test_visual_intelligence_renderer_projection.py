#!/usr/bin/env python3
"""Regression tests for producer -> Visual Intelligence Renderer input projection."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import visual_intelligence_renderer_projection as projection  # noqa: E402


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def beat(scene_number: int, beat_number: int, mode: str, grammar_id: str = "evidence") -> dict:
    scene_id = f"scene-{scene_number:02d}"
    chunk_id = f"{scene_id}-chunk-001"
    beat_id = f"{scene_id}-beat-{beat_number:03d}"
    return {
        "beatId": beat_id,
        "visualBeatId": beat_id,
        "startChunkId": chunk_id,
        "endChunkId": chunk_id,
        "narrationStartCue": "開始",
        "narrationEndCue": "終了",
        "primaryFunction": "Evidence",
        "screenState": "Data",
        "visualMode": mode,
        "visualTemplate": "text-focus",
        "visualGrammar": {
            "contractVersion": "1.0.0",
            "grammarId": grammar_id,
            "transitionRole": "continuation",
        },
        "templateConfig": {
            "variant": "default",
            "comparisonBasis": None,
            "dataBasis": "synthetic",
            "nodeOrder": [],
            "laneLabels": [],
            "outcomeNodeId": None,
        },
        "contentType": "text",
        "screenQuestion": "何を見る？",
        "primaryElement": "表示内容",
        "viewerTexts": ["5,000億ドル", "字幕は変えない"],
        "changeCue": "表示",
        "objectIds": [],
        "assetPlacementIds": [],
        "assetState": "not-required",
        "returnScreenState": None,
        "evidenceSourceIds": ["source-001"],
        "expressionChange": None,
        "fallback": None,
        "producerOnlyBeatField": "drop-me",
    }


def scene(scene_number: int, mode: str, beat_modes: list[str]) -> dict:
    scene_id = f"scene-{scene_number:02d}"
    chunk_id = f"{scene_id}-chunk-001"
    return {
        "sceneId": scene_id,
        "sceneNumber": scene_number,
        "sceneRole": "editorial-body",
        "formalName": f"synthetic-{scene_number}",
        "purpose": "projection test",
        "causalScope": "multiple",
        "performanceIntent": "preserve semantics",
        "evidenceSourceIds": ["source-001"],
        "uncertainty": None,
        "timelineBasis": None,
        "expectedBasisType": "major-reporting",
        "visualMode": mode,
        "initialExpression": "分析",
        "headline": "見出し",
        "supportingTexts": ["補助"],
        "sourceLabel": "source",
        "narrationChunks": [
            {
                "chunkId": chunk_id,
                "speechText": "五千億ドルと話す音声はそのまま。",
                "captionText": "5,000億ドルと表示する。",
                "expression": "分析",
                "pauseAfterMs": 0,
            }
        ],
        "visualBeats": [
            beat(scene_number, index, beat_mode)
            for index, beat_mode in enumerate(beat_modes, start=1)
        ],
        "cards": [],
        "numbers": [],
        "nodes": [],
        "arrows": [],
        "visualEvents": [],
        "assetPlacements": [],
        "transition": {"type": "cut", "durationMs": 0},
        "producerOnlySceneField": "drop-me",
    }


def main() -> int:
    date = "2099-05-05"
    aliases = [
        "causal-chain",
        "intraday-comparison",
        "verification",
        "closing-recap",
    ]
    expected_aliases = {
        "causal-chain": "causal-diagram",
        "intraday-comparison": "number-comparison",
        "verification": "verification-points",
        "closing-recap": "conclusion-card",
    }
    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-projection-") as temp:
        root = Path(temp)
        write(root / "working" / date / "final_episode_contract.json", {"contractVersion": "1.1.0"})
        write(root / "contracts" / "visual_grammar_semantics.json", {"contractVersion": "1.0.0"})
        write(root / "contracts" / "visual_grammar_renderer_compatibility.json", {"contractVersion": "1.0.0"})

        scenes = []
        for scene_number in range(1, 10):
            first_mode = aliases[(scene_number - 1) % len(aliases)]
            second_mode = aliases[scene_number % len(aliases)]
            scenes.append(scene(scene_number, first_mode, [first_mode, second_mode]))
        render = {
            "schemaVersion": "2.4.0",
            "episode": {"targetDate": date},
            "scenes": scenes,
            "expectedConfirmed": True,
            "visualGrammarContractVersion": "legacy-producer-only",
        }
        # This card is deliberately not Beat-owned at authoring time. Visual Intelligence
        # may later select an object like this from Renderer-native inventory. It must be
        # display-safe before Candidate Builder/Critic, not only after it becomes visible.
        render["scenes"][0]["cards"].append({
            "cardId": "metric.synthetic.third-party-funding",
            "role": None,
            "title": "Reuters",
            "lines": [{
                "label": "確認",
                "value": "AIインフラ向け第三者資本5000億ドル超の動員を目指す",
                "tone": "positive",
            }],
        })
        original = copy.deepcopy(render)
        strict = projection.project_visual_intelligence_renderer_input(
            render,
            repo_root=root,
            date=date,
        )

        if render != original:
            raise AssertionError("projection mutated producer render")
        if "expectedConfirmed" in strict or "visualGrammarContractVersion" in strict:
            raise AssertionError("producer-only root keys leaked into Renderer input")
        expected_roles = [
            "opening-hook-market-direction-greeting-conclusion",
            *("editorial-body" for _ in range(7)),
            "closing-recap-sendoff-goodnight",
        ]
        observed_roles = [item["sceneRole"] for item in strict["scenes"]]
        if observed_roles != expected_roles:
            raise AssertionError(f"scene roles drifted: {observed_roles}")

        producer_beats = [beat for item in render["scenes"] for beat in item["visualBeats"]]
        strict_beats = [beat for item in strict["scenes"] for beat in item["visualBeats"]]
        if len(producer_beats) != 18 or len(strict_beats) != 18:
            raise AssertionError("18-Beat boundary changed")
        for source_beat, projected_beat in zip(producer_beats, strict_beats, strict=True):
            expected_mode = expected_aliases[source_beat["visualMode"]]
            if projected_beat["visualMode"] != expected_mode:
                raise AssertionError(
                    f"mode alias drifted: {source_beat['visualMode']} -> {projected_beat['visualMode']}"
                )
            if projected_beat["beatId"] != source_beat["beatId"]:
                raise AssertionError("authoring Beat ID drifted")
            if projected_beat["viewerTexts"] != source_beat["viewerTexts"]:
                raise AssertionError("viewer text changed")
            if projected_beat["screenQuestion"] != source_beat["screenQuestion"]:
                raise AssertionError("screenQuestion changed")
            if "visualBeatId" in projected_beat or "visualGrammar" in projected_beat:
                raise AssertionError("producer-only Beat keys leaked")
            if projected_beat["visualGrammarId"] != source_beat["visualGrammar"]["grammarId"]:
                raise AssertionError("visualGrammarId projection failed")
            if projected_beat["transitionRole"] != source_beat["visualGrammar"]["transitionRole"]:
                raise AssertionError("transitionRole projection failed")
        for source_scene, projected_scene in zip(render["scenes"], strict["scenes"], strict=True):
            if projected_scene["narrationChunks"] != source_scene["narrationChunks"]:
                raise AssertionError("narration changed")

        projected_cards = {
            item["cardId"]: item
            for item in strict["scenes"][0]["cards"]
        }
        selectable = projected_cards["metric.synthetic.third-party-funding"]
        if selectable["lines"][0]["value"] != "AIインフラ向け第3者資本5000億ドル超の動員を目指す":
            raise AssertionError(f"selectable viewer inventory was not normalized: {selectable}")
        if render["scenes"][0]["cards"][0]["lines"][0]["value"] != "AIインフラ向け第三者資本5000億ドル超の動員を目指す":
            raise AssertionError("producer selectable inventory was mutated")

        # Simulate the real-day intermediate renaming every Beat to canonical vb-*.
        intermediate = copy.deepcopy(render)
        for scene_index, item in enumerate(intermediate["scenes"], start=1):
            for beat_index, item_beat in enumerate(item["visualBeats"], start=1):
                item_beat["beatId"] = f"vb-{scene_index:02d}-{beat_index:02d}"
        intermediate_path = root / "working" / date / "render_spec_intermediate.json"
        write(intermediate_path, intermediate)
        restored = projection.project_visual_intelligence_renderer_input(
            render,
            repo_root=root,
            date=date,
        )
        restored_ids = [
            item_beat["beatId"]
            for item in restored["scenes"]
            for item_beat in item["visualBeats"]
        ]
        producer_ids = [item["beatId"] for item in producer_beats]
        if restored_ids != producer_ids:
            raise AssertionError(f"canonical intermediate Beat IDs leaked: {restored_ids}")
        intermediate_path.unlink()

        unknown = copy.deepcopy(render)
        unknown["scenes"][0]["visualMode"] = "future-unreviewed-mode"
        try:
            projection.project_visual_intelligence_renderer_input(
                unknown,
                repo_root=root,
                date=date,
            )
        except projection.VisualIntelligenceRendererProjectionError as exc:
            if "E_VISUAL_MODE_UNMAPPED" not in str(exc):
                raise AssertionError(f"unexpected fail-closed error: {exc}") from exc
        else:
            raise AssertionError("unknown visualMode did not fail closed")

    print("visual intelligence renderer projection tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
