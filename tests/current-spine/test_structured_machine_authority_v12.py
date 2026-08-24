#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_final_production_package_structured_v12 as structured  # noqa: E402
import current_compatibility_adapter_v12 as compatibility  # noqa: E402

DATE = "2099-06-01"


def test_markdown_format_is_not_machine_source() -> None:
    with tempfile.TemporaryDirectory(prefix="nasdaq-structured-authority-") as temp:
        root = Path(temp)
        sidecar = root / "working" / DATE / "current_final_production_source.json"
        sidecar.parent.mkdir(parents=True)
        authority = {
            "contract_version": "1.0.0",
            "episode_date": DATE,
            "render_spec": {"identity": "structured-authority"},
        }
        sidecar.write_text(json.dumps(authority, indent=2) + "\n", encoding="utf-8")
        package_dir = root / "episodes" / DATE
        package_dir.mkdir(parents=True)
        package = package_dir / f"episode_package_{DATE}.md"
        first = (
            "# human projection\n\n"
            + structured.PROD_BEGIN
            + "\n```json\n{\"render_spec\":{\"identity\":\"markdown-A\"}}\n```\n"
            + structured.PROD_END
            + "\n"
        )
        second = (
            "# human projection\n\n\n"
            + structured.PROD_BEGIN
            + "\n```json\n{\n  \"render_spec\": {\n    \"identity\": \"markdown-B\"\n  }\n}\n```\n"
            + structured.PROD_END
            + "\n\n"
        )
        package.write_text(first, encoding="utf-8")
        _, loaded_a = structured._load_structured_source(root, DATE)
        public_a = structured._strip_human_annex_blocks(package.read_text(encoding="utf-8"))
        package.write_text(second, encoding="utf-8")
        _, loaded_b = structured._load_structured_source(root, DATE)
        public_b = structured._strip_human_annex_blocks(package.read_text(encoding="utf-8"))
        if loaded_a != authority or loaded_b != authority:
            raise AssertionError("Markdown formatting/content changed structured machine authority")
        if loaded_a["render_spec"] != loaded_b["render_spec"]:
            raise AssertionError("Markdown changed Renderer input object")
        if "markdown-A" in json.dumps(loaded_a) or "markdown-B" in json.dumps(loaded_b):
            raise AssertionError("Markdown annex leaked into structured authority")
        if public_a != "# human projection" or public_b != "# human projection":
            raise AssertionError("human projection stripping is not formatting tolerant")

    source = (ROOT / "scripts/build_final_production_package_structured_v12.py").read_text(
        encoding="utf-8"
    )
    if "parse_source_annex" in source:
        raise AssertionError("current structured builder still parses Markdown technical annex")


def test_compatibility_adapter_is_mechanical() -> None:
    review = {
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
    }
    projected = compatibility.project_creative_review(review)
    if projected.get("approvedForCodex") is not True or projected.get("verdict") != "approved":
        raise AssertionError("PASS did not deterministically project Renderer approval")
    if projected.get("scores") != {
        "openingHook": 5,
        "storyProgression": 4,
        "discovery": 5,
        "clarity": 5,
        "foxCharacter": 4,
        "reasonToFinish": 5,
    }:
        raise AssertionError("Creative Review score aliases were not projected mechanically")
    if projected.get("totalScore") != 28:
        raise AssertionError("Creative Review total was not preserved")
    if projected.get("titleThumbnailConsistency") != "consistent":
        raise AssertionError("PASS did not deterministically project consistency receipt")
    if not str(projected.get("largestDropoffRisk", "")).strip():
        raise AssertionError("Renderer-required no-unresolved-risk receipt is missing")

    failed = {**review, "verdict": "conditional"}
    failed_projection = compatibility.project_creative_review(failed)
    if failed_projection.get("approvedForCodex") is not False:
        raise AssertionError("non-PASS incorrectly projected Renderer approval")
    if failed_projection.get("verdict") != "approved-with-changes":
        raise AssertionError("conditional verdict compatibility drifted")

    stale = dict(projected)
    stale["scores"] = dict(stale["scores"])
    stale["scores"]["openingHook"] = 4
    try:
        compatibility.assert_compatibility_review_matches(
            current_review=review,
            compatibility_review=stale,
        )
    except compatibility.CurrentCompatibilityError:
        pass
    else:
        raise AssertionError("drifted compatibility review was accepted")


def test_current_final_uses_separated_authority() -> None:
    source = (ROOT / "scripts/build_final_production_package_v12.py").read_text(encoding="utf-8")
    if "visual_intelligence_decision.json" in source:
        raise AssertionError("combined Director/Critic authority remains in current final build")
    for name in ("visual_director_decision.json", "visual_critic_review.json"):
        if name not in source:
            raise AssertionError(f"separated current authority missing: {name}")
    if "builder=structured_builder.build" not in source:
        raise AssertionError("Current v1.2 final build is not using structured builder")


def main() -> int:
    test_markdown_format_is_not_machine_source()
    test_compatibility_adapter_is_mechanical()
    test_current_final_uses_separated_authority()
    print("structured current machine authority PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
