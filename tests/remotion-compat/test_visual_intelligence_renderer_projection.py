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


def beat(beat_id: str, mode: str, grammar_id: str = "evidence") -> dict:
    return {
        "beatId": beat_id,
        "visualBeatId": f"legacy-{beat_id}",
        "startChunkId": "scene-01-chunk-001",
        "endChunkId": "scene-01-chunk-001",
        "narrationStartCue": "開始",
        "narrationEndCue": "終了",
        "primaryFunction": "Evidence",
        "screenState": "Data",
        "visualMode": mode,
        "visualTemplate": "text-focus",
        "visualGrammar": {
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


def scene(mode: str, beats: list[dict]) -> dict:
    return {
        "sceneId": "scene-01",
        "sceneNumber": 1,
        "sceneRole": "opening-hook-market-direction-greeting-conclusion",
        "formalName": "synthetic",
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
                "chunkId": "scene-01-chunk-001",
                "speechText": "五千億ドルと話す音声はそのまま。",
                "captionText": "5,000億ドルと表示する。",
                "expression": "分析",
                "pauseAfterMs": 0,
            }
        ],
        "visualBeats": beats,
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
    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-projection-") as temp:
        root = Path(temp)
        write(root / "working" / date / "final_episode_contract.json", {"contractVersion": "1.1.0"})
        write(root / "contracts" / "visual_grammar_semantics.json", {"contractVersion": "1.0.0"})
        write(root / "contracts" / "visual_grammar_renderer_compatibility.json", {"contractVersion": "1.0.0"})

        modes = [
            "causal-chain",
            "intraday-comparison",
            "verification",
            "closing-recap",
        ]
        beats = [beat(f"vb-01-{index:02d}", mode) for index, mode in enumerate(modes, start=1)]
        render = {
            "schemaVersion": "2.4.0",
            "episode": {"targetDate": date},
            "scenes": [scene("causal-chain", beats)],
            "expectedConfirmed": True,
            "visualGrammarContractVersion": "legacy-producer-only",
        }
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
        if strict["scenes"][0]["visualMode"] != "causal-diagram":
            raise AssertionError(strict["scenes"][0]["visualMode"])
        expected_modes = [
            "causal-diagram",
            "number-comparison",
            "verification-points",
            "conclusion-card",
        ]
        observed_modes = [item["visualMode"] for item in strict["scenes"][0]["visualBeats"]]
        if observed_modes != expected_modes:
            raise AssertionError(f"mode aliases drifted: {observed_modes}")
        if len(strict["scenes"][0]["visualBeats"]) != len(beats):
            raise AssertionError("Beat count changed")
        if strict["scenes"][0]["narrationChunks"] != render["scenes"][0]["narrationChunks"]:
            raise AssertionError("narration changed")
        for source_beat, projected_beat in zip(beats, strict["scenes"][0]["visualBeats"], strict=True):
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
