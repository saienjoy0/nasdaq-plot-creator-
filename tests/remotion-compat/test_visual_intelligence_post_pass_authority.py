#!/usr/bin/env python3
"""Regression coverage for the v1.2 post-Critic immutable visual authority."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_final_production_package_v12 as v12  # noqa: E402


def sample_render() -> dict:
    return {
        "schemaVersion": "2.4.0",
        "episode": {"targetDate": "2026-08-12"},
        "scenes": [
            {
                "sceneId": "scene-01",
                "narrationChunks": [
                    {
                        "chunkId": "scene-01-chunk-001",
                        "speechText": "同じナレーション",
                        "captionText": "同じナレーション",
                        "pauseAfterMs": 0,
                    }
                ],
                "visualBeats": [
                    {
                        "beatId": "scene-01-beat-001",
                        "startChunkId": "scene-01-chunk-001",
                        "endChunkId": "scene-01-chunk-001",
                        "narrationStartCue": "開始",
                        "narrationEndCue": "終了",
                        "primaryFunction": "evidence",
                        "contentType": "source-receipt",
                        "screenQuestion": "何が確認できた？",
                        "primaryElement": "一次情報",
                        "viewerTexts": ["確認済み"],
                        "evidenceSourceIds": ["source-1"],
                        "screenState": "Main",
                        "visualMode": "text-focus",
                        "visualTemplate": "source-receipt",
                        "templateVariant": "receipt",
                        "objectIds": ["metric-1"],
                        "assetPlacementIds": [],
                        "returnScreenState": "Main",
                        "financialReturnTarget": None,
                        "entity": None,
                        "pictureBook": None,
                        "shots": [],
                        "sequencePolicy": "explicit",
                        "templateConfig": {
                            "variant": "receipt",
                            "dataBasis": "verified",
                        },
                    }
                ],
            }
        ],
    }


def expect_error(candidate: dict, code: str) -> None:
    approved = sample_render()
    try:
        v12._assert_post_pass_integrity(approved, candidate)
    except v12.VisualIntelligenceFinalBuildError as exc:
        if code not in str(exc):
            raise AssertionError(f"expected {code}, got {exc}") from exc
    else:
        raise AssertionError(f"expected {code}")


def test_exact_authority_passes() -> None:
    approved = sample_render()
    result = v12._assert_post_pass_integrity(approved, copy.deepcopy(approved))
    if result["sceneCount"] != 1 or result["beatCount"] != 1:
        raise AssertionError(result)
    if result["secondDirectorInvoked"] is not False:
        raise AssertionError(result)


def test_beat_addition_fails() -> None:
    candidate = sample_render()
    extra = copy.deepcopy(candidate["scenes"][0]["visualBeats"][0])
    extra["beatId"] = "scene-01-beat-002"
    candidate["scenes"][0]["visualBeats"].append(extra)
    expect_error(candidate, "E_VISUAL_INTELLIGENCE_POST_PASS_BEAT_DRIFT")


def test_beat_reorder_fails() -> None:
    approved = sample_render()
    second = copy.deepcopy(approved["scenes"][0]["visualBeats"][0])
    second["beatId"] = "scene-01-beat-002"
    approved["scenes"][0]["visualBeats"].append(second)
    candidate = copy.deepcopy(approved)
    candidate["scenes"][0]["visualBeats"].reverse()
    try:
        v12._assert_post_pass_integrity(approved, candidate)
    except v12.VisualIntelligenceFinalBuildError as exc:
        if "E_VISUAL_INTELLIGENCE_POST_PASS_BEAT_DRIFT" not in str(exc):
            raise
    else:
        raise AssertionError("reordered Beats must fail")


def test_semantic_drift_fails() -> None:
    candidate = sample_render()
    candidate["scenes"][0]["visualBeats"][0]["viewerTexts"] = ["変更"]
    expect_error(candidate, "E_VISUAL_INTELLIGENCE_POST_PASS_SEMANTIC_DRIFT")


def test_visual_selection_drift_fails() -> None:
    candidate = sample_render()
    candidate["scenes"][0]["visualBeats"][0]["visualTemplate"] = "text-focus"
    expect_error(candidate, "E_VISUAL_INTELLIGENCE_POST_PASS_VISUAL_DRIFT")


def test_post_pass_render_is_immutable() -> None:
    candidate = sample_render()
    candidate["scenes"][0]["visualBeats"][0]["templateConfig"]["runtimeData"] = {
        "resolved": True
    }
    expect_error(candidate, "E_VISUAL_INTELLIGENCE_POST_PASS_VISUAL_DRIFT")


def test_legacy_visual_director_is_suppressed_without_mutating_request() -> None:
    request = {
        "visual_intelligence": {"required": True},
        "visual_director": {"required": True, "contract_version": "1.0.0"},
    }
    result = v12._without_legacy_visual_director(request)
    if "visual_director" in result:
        raise AssertionError("legacy Visual Director binding must be suppressed")
    if "visual_director" not in request:
        raise AssertionError("suppression mutated the production request")


def test_second_director_guard() -> None:
    try:
        v12._forbid_second_director()
    except v12.VisualIntelligenceFinalBuildError as exc:
        if "E_VISUAL_INTELLIGENCE_SECOND_DIRECTOR_FORBIDDEN" not in str(exc):
            raise
    else:
        raise AssertionError("second Director guard did not fail")


def main() -> int:
    test_exact_authority_passes()
    test_beat_addition_fails()
    test_beat_reorder_fails()
    test_semantic_drift_fails()
    test_visual_selection_drift_fails()
    test_post_pass_render_is_immutable()
    test_legacy_visual_director_is_suppressed_without_mutating_request()
    test_second_director_guard()
    print("visual intelligence post-PASS authority tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
