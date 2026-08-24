#!/usr/bin/env python3
"""Regression: Current-v2 accepted semantics project deterministically to Renderer 2.4 metadata."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import current_compatibility_adapter_v12 as adapter  # noqa: E402


def main() -> int:
    dossier = {
        "expected_actual_gap": {
            "expected": {
                "status": "confirmed",
                "basis_class": "major_reporting",
                "statement": "formal expected",
                "evidence_ids": ["E-003", "E-004"],
            },
            "actual": {"statement": "actual result", "evidence_ids": ["E-004"]},
            "gap": {"statement": "positive formal gap", "confidence": "medium"},
        },
        "factor_roles": {
            "amplifiers": ["amplifier A"],
            "offsetting": ["offset A", "offset B"],
        },
        "contrary_evidence": [
            {"statement": "counter A", "evidence_ids": ["E-002"], "effect_on_confidence": "material"},
        ],
        "editorial_handoff": {
            "provisional_lead": "lead company event",
            "headline_beyond_discovery": "theme beyond headline",
            "central_hypothesis": "central hypothesis",
            "confidence": "medium",
            "company_direct_material": ["direct A"],
            "nasdaq_wide_material": ["driver A", "driver B"],
            "next_validation_points": ["verify A"],
        },
    }
    production = {
        "episodeType": "single-news",
        "scenes": [
            {
                "sceneRole": "expected_actual_gap",
                "evidenceSourceIds": ["source-003", "source-004"],
                "timelineBasis": "gap timing",
            },
            {
                "sceneRole": "market_reaction",
                "evidenceSourceIds": ["source-001"],
                "timelineBasis": "after close -> next session",
            },
        ],
    }
    story_plan = {"story_spine": "story spine"}
    editorial = adapter.project_renderer_editorial(
        dossier=dossier,
        production=production,
        story_plan=story_plan,
    )
    expected_keys = {
        "leadNews", "leadTheme", "targetIndices", "storySpine", "centralHypothesis",
        "confidence", "directMaterial", "nasdaqDrivers", "amplifiers", "offsettingFactors",
        "expected", "actual", "gap", "expectedBasisType", "expectedBasisDetails",
        "expectedSourceIds", "timelineBasis", "counterEvidence", "verificationPoints",
    }
    if set(editorial) != expected_keys:
        raise AssertionError(f"Renderer editorial key drift: {sorted(editorial)}")
    if editorial["leadTheme"] is not None:
        raise AssertionError("single-news must not synthesize leadTheme")
    if editorial["targetIndices"] != ["Nasdaq Composite"]:
        raise AssertionError("NASDAQ Cafe baseline target index drifted")
    if editorial["directMaterial"] != ["direct A"]:
        raise AssertionError("company_direct_material was not preserved")
    if editorial["nasdaqDrivers"] != ["driver A", "driver B"]:
        raise AssertionError("nasdaq_wide_material was not preserved")
    if editorial["amplifiers"] != ["amplifier A"] or editorial["offsettingFactors"] != ["offset A", "offset B"]:
        raise AssertionError("factor roles were not preserved")
    if editorial["expectedBasisType"] != "major-reporting":
        raise AssertionError("expected basis alias was not normalized")
    if editorial["expectedSourceIds"] != ["source-003", "source-004"]:
        raise AssertionError("Expected/Actual/Gap source IDs were not preserved")
    if editorial["timelineBasis"] != "after close -> next session":
        raise AssertionError("market reaction timeline was not preserved")
    if editorial["verificationPoints"] != ["verify A"]:
        raise AssertionError("next validation points were not preserved")

    composite = copy.deepcopy(production)
    composite["episodeType"] = "composite-story"
    composite_editorial = adapter.project_renderer_editorial(
        dossier=dossier,
        production=composite,
        story_plan=story_plan,
    )
    if composite_editorial["leadNews"] is not None or composite_editorial["leadTheme"] != "theme beyond headline":
        raise AssertionError("composite-story lead ownership drifted")

    publishing = adapter.project_renderer_publishing({
        "titleCandidates": ["title A", "title B", "title C"],
        "thumbnailTextCandidates": ["thumb A", "thumb B", "thumb C"],
        "description": "description",
    })
    if publishing["recommendedTitle"] != "title A" or publishing["recommendedThumbnailText"] != "thumb A":
        raise AssertionError("Current-v2 ranked publishing order did not project to recommendation")
    if publishing["titleCandidates"] != ["title A", "title B", "title C"]:
        raise AssertionError("publishing candidates changed")

    review = adapter.project_creative_review({
        "verdict": "pass",
        "scores": {
            "opening": 5,
            "progression": 4,
            "discovery": 5,
            "clarity": 5,
            "fox_voice": 4,
            "late_payoff": 5,
        },
        "total_score": 28,
        "findings": [],
    })
    if review["scores"] != {
        "openingHook": 5,
        "storyProgression": 4,
        "discovery": 5,
        "clarity": 5,
        "foxCharacter": 4,
        "reasonToFinish": 5,
    }:
        raise AssertionError(f"Creative Review score aliases drifted: {review['scores']}")
    if review["totalScore"] != 28 or not review["largestDropoffRisk"].strip():
        raise AssertionError("Renderer review summary is incomplete")
    if review["titleThumbnailConsistency"] != "consistent" or review["approvedForCodex"] is not True:
        raise AssertionError("pass verdict compatibility drifted")

    scene = {
        "causalScope": "company_direct",
        "expectedBasisType": "not-applicable",
        "beats": [
            {"screenState": "Source", "visualTemplate": "source-receipt"},
            {"screenState": "Data", "visualTemplate": "split-comparison"},
        ],
    }
    projected_scene = adapter.project_renderer_scene_compatibility(scene)
    if projected_scene["causalScope"] != "lead-stock":
        raise AssertionError("company_direct did not map to lead-stock")
    if projected_scene["expectedBasisType"] is not None:
        raise AssertionError("not-applicable must project to null")
    if projected_scene["beats"][0]["screenState"] != "News":
        raise AssertionError("Source screen state did not map to Renderer News")
    if scene["causalScope"] != "company_direct" or scene["beats"][0]["screenState"] != "Source":
        raise AssertionError("compatibility projection mutated accepted Current semantics")

    for source, target in {
        "sector_support": "sector",
        "nasdaq_wide": "nasdaq",
        "nasdaq_support": "nasdaq",
        "multiple": "multiple",
    }.items():
        item = adapter.project_renderer_scene_compatibility({
            "causalScope": source,
            "expectedBasisType": "major-reporting",
            "beats": [{"screenState": "Data", "visualTemplate": "text-focus"}],
        })
        if item["causalScope"] != target:
            raise AssertionError(f"causal scope alias drifted: {source} -> {item['causalScope']}")

    try:
        adapter.project_renderer_scene_compatibility({
            "causalScope": "future-unknown-scope",
            "expectedBasisType": "major-reporting",
            "beats": [{"screenState": "Data", "visualTemplate": "text-focus"}],
        })
    except adapter.CurrentCompatibilityError:
        pass
    else:
        raise AssertionError("unknown Current causalScope did not fail closed")

    print("Current-v2 -> Renderer 2.4 compatibility projection PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
