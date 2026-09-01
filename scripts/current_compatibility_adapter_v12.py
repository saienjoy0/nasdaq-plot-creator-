#!/usr/bin/env python3
"""Deterministic compatibility projection for current-v1.2 production.

This module is the only current owner of legacy/Renderer-shaped compatibility fields.
It may copy or deterministically derive a mechanical field from already-accepted
Current authority, but it must never make an editorial choice or infer missing meaning.
Unknown enum values fail closed instead of being guessed.
"""
from __future__ import annotations

import copy
from typing import Any


class CurrentCompatibilityError(ValueError):
    pass


EXPECTED_BASIS_MAP = {
    "official_consensus": "official-consensus",
    "official-consensus": "official-consensus",
    "company_prior_guidance": "company-prior-guidance",
    "company-prior-guidance": "company-prior-guidance",
    "major_reporting": "major-reporting",
    "major-reporting": "major-reporting",
    "analyst_view": "analyst-view",
    "analyst-view": "analyst-view",
    "price_inference": "price-inference",
    "price-inference": "price-inference",
    "unconfirmed": "unconfirmed",
    "not-applicable": None,
    None: None,
}

CAUSAL_SCOPE_MAP = {
    "company_direct": "lead-stock",
    "lead-stock": "lead-stock",
    "sector_support": "sector",
    "sector": "sector",
    "nasdaq_wide": "nasdaq",
    "nasdaq_support": "nasdaq",
    "nasdaq": "nasdaq",
    "multiple": "multiple",
}

SCREEN_STATE_MAP = {
    "Data": "Data",
    "Chart": "Chart",
    "EntityFocus": "EntityFocus",
    "MainWithEntity": "MainWithEntity",
    "PictureBook": "PictureBook",
    "News": "News",
    # Current authoring uses Source to mean a source/document surface. Renderer 2.4
    # calls that transient surface News; template soundness remains the final check.
    "Source": "News",
}

REVIEW_SCORE_MAP = {
    "opening": "openingHook",
    "progression": "storyProgression",
    "discovery": "discovery",
    "clarity": "clarity",
    "fox_voice": "foxCharacter",
    "late_payoff": "reasonToFinish",
}

REVIEW_VERDICT_MAP = {
    "pass": "approved",
    "conditional": "approved-with-changes",
    "restructure": "rejected",
    "fail": "rejected",
    # Compatibility with pre-v1.1 Current review vocabulary retained only for
    # already-accepted historical artifacts.
    "revise": "approved-with-changes",
    "return_to_story": "rejected",
    "blocked": "rejected",
}


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise CurrentCompatibilityError(f"{label} must be a list")
    return value


def _nonempty_strings(value: Any, label: str) -> list[str]:
    rows = _require_list(value, label)
    if any(not isinstance(item, str) or not item.strip() for item in rows):
        raise CurrentCompatibilityError(f"{label} must contain non-empty strings")
    return list(rows)


def project_expected_basis(value: Any) -> str | None:
    if value not in EXPECTED_BASIS_MAP:
        raise CurrentCompatibilityError(
            f"unsupported Current expected basis type: {value!r}"
        )
    return EXPECTED_BASIS_MAP[value]


def _scene_by_role(production: dict[str, Any], role: str) -> dict[str, Any] | None:
    scenes = production.get("scenes")
    if not isinstance(scenes, list):
        raise CurrentCompatibilityError("Current production.scenes must be a list")
    matches = [
        scene
        for scene in scenes
        if isinstance(scene, dict) and scene.get("sceneRole") == role
    ]
    if len(matches) > 1:
        raise CurrentCompatibilityError(f"Current production has duplicate sceneRole: {role}")
    return matches[0] if matches else None


def project_renderer_editorial(
    *,
    dossier: dict[str, Any],
    production: dict[str, Any],
    story_plan: dict[str, Any],
) -> dict[str, Any]:
    """Project accepted Current research/story authority into Renderer editorial metadata.

    No prose is authored here. Every non-invariant value is copied from the accepted
    Causal Dossier, Story Plan, or explicitly authored production scene metadata.
    """
    handoff = dossier.get("editorial_handoff")
    gap_block = dossier.get("expected_actual_gap")
    factor_roles = dossier.get("factor_roles")
    if not isinstance(handoff, dict) or not isinstance(gap_block, dict) or not isinstance(factor_roles, dict):
        raise CurrentCompatibilityError(
            "Current Causal Dossier lacks editorial_handoff/expected_actual_gap/factor_roles"
        )
    expected = gap_block.get("expected")
    actual = gap_block.get("actual")
    gap = gap_block.get("gap")
    if not all(isinstance(item, dict) for item in (expected, actual, gap)):
        raise CurrentCompatibilityError("Current Expected/Actual/Gap block is incomplete")

    episode_type = production.get("episodeType")
    if episode_type not in {"single-news", "composite-story", "reason-unknown"}:
        raise CurrentCompatibilityError(f"unsupported Current episodeType: {episode_type!r}")

    gap_scene = _scene_by_role(production, "expected_actual_gap")
    reaction_scene = _scene_by_role(production, "market_reaction")
    expected_source_ids = (
        _nonempty_strings(gap_scene.get("evidenceSourceIds", []), "Expected/Actual/Gap evidenceSourceIds")
        if gap_scene is not None
        else []
    )
    timeline_basis = None
    if reaction_scene is not None:
        raw_timeline = reaction_scene.get("timelineBasis")
        if raw_timeline is not None and (not isinstance(raw_timeline, str) or not raw_timeline.strip()):
            raise CurrentCompatibilityError("market_reaction timelineBasis must be non-empty or null")
        timeline_basis = raw_timeline

    counter_rows = _require_list(dossier.get("contrary_evidence", []), "contrary_evidence")
    counter_evidence: list[str] = []
    for index, row in enumerate(counter_rows):
        if not isinstance(row, dict) or not isinstance(row.get("statement"), str) or not row["statement"].strip():
            raise CurrentCompatibilityError(f"contrary_evidence[{index}] lacks statement")
        counter_evidence.append(row["statement"])

    story_spine = story_plan.get("story_spine")
    if not isinstance(story_spine, str) or not story_spine.strip():
        raise CurrentCompatibilityError("Current Story Plan story_spine is required")

    lead = handoff.get("provisional_lead")
    theme = handoff.get("headline_beyond_discovery")
    if not isinstance(lead, str) or not lead.strip():
        raise CurrentCompatibilityError("Current editorial_handoff.provisional_lead is required")
    if not isinstance(theme, str) or not theme.strip():
        raise CurrentCompatibilityError("Current editorial_handoff.headline_beyond_discovery is required")

    central_hypothesis = handoff.get("central_hypothesis")
    confidence = handoff.get("confidence")
    if not isinstance(central_hypothesis, str) or not central_hypothesis.strip():
        raise CurrentCompatibilityError("Current editorial_handoff.central_hypothesis is required")
    if confidence not in {"high", "medium", "low", "unknown"}:
        raise CurrentCompatibilityError(f"unsupported Current confidence: {confidence!r}")

    expected_statement = expected.get("statement")
    actual_statement = actual.get("statement")
    gap_statement = gap.get("statement")
    for label, value in (
        ("expected.statement", expected_statement),
        ("actual.statement", actual_statement),
        ("gap.statement", gap_statement),
    ):
        if not isinstance(value, str) or not value.strip():
            raise CurrentCompatibilityError(f"Current {label} is required")

    return {
        "leadNews": lead if episode_type == "single-news" else None,
        "leadTheme": theme if episode_type == "composite-story" else None,
        # NASDAQ Cafe's Renderer always needs at least the program's final lens. Extra
        # supporting indices remain authored inside Scene/Beat evidence and are not inferred.
        "targetIndices": ["Nasdaq Composite"],
        "storySpine": story_spine,
        "centralHypothesis": central_hypothesis,
        "confidence": confidence,
        "directMaterial": _nonempty_strings(
            handoff.get("company_direct_material", []),
            "editorial_handoff.company_direct_material",
        ),
        "nasdaqDrivers": _nonempty_strings(
            handoff.get("nasdaq_wide_material", []),
            "editorial_handoff.nasdaq_wide_material",
        ),
        "amplifiers": _nonempty_strings(factor_roles.get("amplifiers", []), "factor_roles.amplifiers"),
        "offsettingFactors": _nonempty_strings(factor_roles.get("offsetting", []), "factor_roles.offsetting"),
        "expected": expected_statement,
        "actual": actual_statement,
        "gap": gap_statement,
        "expectedBasisType": project_expected_basis(expected.get("basis_class")),
        "expectedBasisDetails": expected_statement,
        "expectedSourceIds": expected_source_ids,
        "timelineBasis": timeline_basis,
        "counterEvidence": counter_evidence,
        "verificationPoints": _nonempty_strings(
            handoff.get("next_validation_points", []),
            "editorial_handoff.next_validation_points",
        ),
    }


def project_renderer_publishing(publishing: dict[str, Any]) -> dict[str, Any]:
    """Project ranked Current publishing candidates into Renderer 2.4 publishing.

    Current-v2 authoring preserves candidate order. Compatibility treats index 0 as
    the already-authored preferred candidate; it never re-ranks or rewrites copy.
    """
    titles = _nonempty_strings(publishing.get("titleCandidates"), "publishing.titleCandidates")
    thumbnails = _nonempty_strings(
        publishing.get("thumbnailTextCandidates"),
        "publishing.thumbnailTextCandidates",
    )
    if len(titles) != 3 or len(set(titles)) != 3:
        raise CurrentCompatibilityError("Renderer publishing requires exactly 3 unique title candidates")
    if len(thumbnails) != 3 or len(set(thumbnails)) != 3:
        raise CurrentCompatibilityError("Renderer publishing requires exactly 3 unique thumbnail candidates")
    description = publishing.get("description")
    if not isinstance(description, str) or not description.strip():
        raise CurrentCompatibilityError("publishing.description is required")
    return {
        "recommendedTitle": titles[0],
        "titleCandidates": titles,
        "recommendedThumbnailText": thumbnails[0],
        "thumbnailTextCandidates": thumbnails,
        "description": description,
    }


def project_creative_review(review: dict[str, Any]) -> dict[str, Any]:
    """Project current Creative Review into Renderer 2.4 review metadata.

    `approvedForCodex` is a compatibility boolean only. The semantic authority is
    still the current Creative Review verdict; this adapter does not re-review it.
    """
    verdict = review.get("verdict")
    if verdict not in REVIEW_VERDICT_MAP:
        raise CurrentCompatibilityError(f"unsupported current Creative Review verdict: {verdict!r}")
    findings = _require_list(review.get("findings", []), "current Creative Review findings")
    scores = review.get("scores")
    if not isinstance(scores, dict):
        raise CurrentCompatibilityError("current Creative Review scores must be an object")
    if set(scores) != set(REVIEW_SCORE_MAP):
        raise CurrentCompatibilityError(
            f"current Creative Review score keys drifted: {sorted(scores)}"
        )
    renderer_scores: dict[str, int] = {}
    for source_key, target_key in REVIEW_SCORE_MAP.items():
        value = scores[source_key]
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 5:
            raise CurrentCompatibilityError(f"invalid Creative Review score {source_key}: {value!r}")
        renderer_scores[target_key] = value
    score_total = sum(renderer_scores.values())
    authored_total = review.get("total_score")
    if authored_total is not None and authored_total != score_total:
        raise CurrentCompatibilityError(
            f"Creative Review total_score drifted: {authored_total!r} != {score_total}"
        )

    required_changes: list[str] = []
    for index, item in enumerate(findings):
        if not isinstance(item, dict):
            raise CurrentCompatibilityError(f"Creative Review findings[{index}] must be an object")
        if item.get("severity") in {"critical", "major"}:
            fix = item.get("minimal_fix")
            if not isinstance(fix, str) or not fix.strip():
                raise CurrentCompatibilityError(f"Creative Review findings[{index}] lacks minimal_fix")
            required_changes.append(fix)

    if findings:
        first_impact = findings[0].get("viewer_impact") if isinstance(findings[0], dict) else None
        if not isinstance(first_impact, str) or not first_impact.strip():
            raise CurrentCompatibilityError("first Creative Review finding lacks viewer_impact")
        largest_risk = first_impact
    else:
        # A passed/empty final review contains no identified finding. Renderer requires a
        # non-empty receipt string, so encode that state without inventing a new risk.
        largest_risk = "No unresolved drop-off risk identified in final Creative Review"

    return {
        "verdict": REVIEW_VERDICT_MAP[verdict],
        "approvedForCodex": verdict == "pass",
        "scores": renderer_scores,
        "totalScore": score_total,
        "largestDropoffRisk": largest_risk,
        "requiredChanges": required_changes,
        "changesApplied": [],
        "titleThumbnailConsistency": "consistent" if verdict == "pass" else "needs-revision",
    }


def project_renderer_scene_compatibility(scene: dict[str, Any]) -> dict[str, Any]:
    """Normalize only known Current enum aliases needed by Renderer 2.4."""
    projected = copy.deepcopy(scene)
    scope = projected.get("causalScope")
    if scope not in CAUSAL_SCOPE_MAP:
        raise CurrentCompatibilityError(f"unsupported Current causalScope: {scope!r}")
    projected["causalScope"] = CAUSAL_SCOPE_MAP[scope]
    projected["expectedBasisType"] = project_expected_basis(
        projected.get("expectedBasisType")
    )
    beats = projected.get("beats")
    if not isinstance(beats, list):
        raise CurrentCompatibilityError("Current scene.beats must be a list")
    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            raise CurrentCompatibilityError(f"Current scene.beats[{index}] must be an object")
        state = beat.get("screenState")
        if state not in SCREEN_STATE_MAP:
            raise CurrentCompatibilityError(f"unsupported Current screenState: {state!r}")
        beat["screenState"] = SCREEN_STATE_MAP[state]
    return projected


def project_renderer_production(production: dict[str, Any]) -> dict[str, Any]:
    projected = copy.deepcopy(production)
    scenes = projected.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 9:
        raise CurrentCompatibilityError("Current Renderer production requires exactly 9 scenes")
    projected["scenes"] = [project_renderer_scene_compatibility(scene) for scene in scenes]
    return projected


def assert_compatibility_review_matches(
    *,
    current_review: dict[str, Any],
    compatibility_review: dict[str, Any],
) -> None:
    expected = project_creative_review(current_review)
    if compatibility_review != expected:
        raise CurrentCompatibilityError(
            "Renderer-shaped Creative Review projection does not match current authority"
        )
