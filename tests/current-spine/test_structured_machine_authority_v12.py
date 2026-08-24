#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_final_production_package_structured_v12 as structured  # noqa: E402
import current_compatibility_adapter_v12 as compatibility  # noqa: E402

DATE = "2099-06-01"


def _materializer_function(name: str) -> ast.FunctionDef:
    source_path = ROOT / "scripts/materialize_daily_episode.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    function = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name),
        None,
    )
    if function is None:
        raise AssertionError(f"materializer function is missing: {name}")
    return function


def _load_materializer_heading_normalizer():
    source_path = ROOT / "scripts/materialize_daily_episode.py"
    function = _materializer_function("normalize_scene_headings")
    module = ast.Module(body=[function], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"re": re}
    exec(compile(module, str(source_path), "exec"), namespace)
    return namespace["normalize_scene_headings"]


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


def test_current_v2_human_package_normalizes_inquisition_heading() -> None:
    normalize = _load_materializer_heading_normalizer()
    legacy_heading = "## 04による興味深さ・わかりやすさ審問結果"
    canonical_heading = "## H. 04 興味深さ・わかりやすさ審問結果"
    body = "審問本文は変更しない。"
    source = (
        "## B1. Scene 1｜導入\n"
        "Scene body\n\n"
        f"{legacy_heading}\n"
        f"{body}\n"
    )
    projected = normalize(source)
    if "## B1. Scene 1" in projected or "## Scene 1｜導入" not in projected:
        raise AssertionError("existing Scene heading normalization regressed")
    if projected.count(canonical_heading) != 1:
        raise AssertionError("current-v2 final package did not canonicalize the integrated 04 heading")
    if legacy_heading in projected:
        raise AssertionError("legacy 04 heading remained after current-v2 projection")
    if body not in projected:
        raise AssertionError("04 review body changed during mechanical heading normalization")


def test_current_v2_persists_structured_machine_authority() -> None:
    function = _materializer_function("_run_current_v2")
    string_constants = {
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    if "current_final_production_source.json" not in string_constants:
        raise AssertionError("current-v2 materializer does not persist current structured production authority")

    writes_production_annex = False
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "write_text":
            continue
        if not node.args:
            continue
        if any(isinstance(inner, ast.Name) and inner.id == "production_annex" for inner in ast.walk(node.args[0])):
            writes_production_annex = True
            break
    if not writes_production_annex:
        raise AssertionError("current-v2 structured sidecar is not written from production_annex")


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
    test_current_v2_human_package_normalizes_inquisition_heading()
    test_current_v2_persists_structured_machine_authority()
    test_compatibility_adapter_is_mechanical()
    test_current_final_uses_separated_authority()
    print("structured current machine authority PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
