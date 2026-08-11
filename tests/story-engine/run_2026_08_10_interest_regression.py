#!/usr/bin/env python3
"""Run the real 2026-08-10 Story Interest A/B using the immutable H4 fixture lineage."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

DATE = "2026-08-10"
EXPECTED_ACCEPTANCE_FIXTURE_COMMIT = "b986888660aa8efd64428aa8119200965351c047"
ROOT_REL = Path("tests/story-engine/fixtures/2026-08-10-interest")
RECEIPT_REL = ROOT_REL / "baseline_source_receipt.json"
INVARIANTS_REL = ROOT_REL / "editorial_invariants.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise SystemExit(f"{label} drift: actual={actual!r} expected={expected!r}")


def _verify_acceptance_checkout(acceptance_source: Path) -> None:
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=acceptance_source, text=True).strip()
    except Exception as exc:
        raise SystemExit(f"cannot resolve acceptance fixture HEAD: {exc}") from exc
    assert_equal(head, EXPECTED_ACCEPTANCE_FIXTURE_COMMIT, "acceptance fixture commit")


def _copy_acceptance_payload(root: Path, acceptance_source: Path) -> None:
    source = acceptance_source / f"acceptance-inputs/{DATE}"
    target = root / f"acceptance-inputs/{DATE}"
    target.mkdir(parents=True, exist_ok=True)
    parts = sorted(source.glob("part-*.b64"))
    if not parts:
        raise SystemExit(f"acceptance payload missing under {source}")
    for part in parts:
        shutil.copy2(part, target / part.name)


def _materialize_h4_baseline(root: Path, acceptance_source: Path) -> None:
    verification = root / f"verification/{DATE}"
    verification.mkdir(parents=True, exist_ok=True)
    run(sys.executable, "tests/real-day-2026-08-10/materialize_fixture.py", "--repo-root", str(root), "--acceptance-source", str(acceptance_source), "--output", str(verification / "interest_h4_fixture_materialization.json"), cwd=root)
    run(sys.executable, "scripts/story-engine/materialize_story_engine.py", "--repo-root", str(root), "--date", DATE, "--external-critic", "off", cwd=root)


def _story_paths(root: Path) -> dict[str, Path]:
    return {
        "causal_dossier": root / f"research/{DATE}/causal_research_dossier_{DATE}.json",
        "story_plan": root / f"working/{DATE}/story-engine/story_plan.json",
        "story_script": root / f"working/{DATE}/story-engine/story_script.json",
        "creative_review": root / f"working/{DATE}/story-engine/creative_review.json",
    }


def _verify_historical_baseline(root: Path, receipt: dict[str, Any]) -> dict[str, str]:
    paths = _story_paths(root)
    digests = {name: sha(path) for name, path in paths.items()}
    for name, expected in receipt["files"].items():
        assert_equal(digests[name], expected["sha256"], f"historical H4 {name} sha256")
    review = load(paths["creative_review"])
    assert_equal(review["total_score"], 29, "historical H4 score")
    assert_equal(review["verdict"], "pass", "historical H4 verdict")
    assert_equal(review["findings"], [], "historical H4 findings")
    plan = load(paths["story_plan"])
    if "E-005" not in plan["scenes"][5]["new_evidence_ids"]:
        raise SystemExit("historical H4 Scene 6 no longer carries the earnings branch")
    if "E-008" not in plan["scenes"][7]["new_evidence_ids"]:
        raise SystemExit("historical H4 Scene 8 no longer carries minute-timing verification")
    return digests


def _patch_revised_templates(root: Path) -> dict[str, Any]:
    output = root / f"verification/{DATE}/interest_revised_fixture_materialization.json"
    run(sys.executable, "tests/story-engine/fixtures/2026-08-10-interest/materialize_revised_interest_fixture.py", "--repo-root", str(root), "--output", str(output), cwd=root)
    return load(output)


def _materialize_revised(root: Path) -> None:
    run(sys.executable, "scripts/story-engine/materialize_story_engine.py", "--repo-root", str(root), "--date", DATE, "--external-critic", "off", cwd=root)


def _verify_invariants(root: Path, invariants: dict[str, Any], baseline_dossier_sha: str) -> dict[str, Any]:
    paths = _story_paths(root)
    dossier = load(paths["causal_dossier"])
    plan = load(paths["story_plan"])
    script = load(paths["story_script"])
    review = load(paths["creative_review"])

    assert_equal(sha(paths["causal_dossier"]), baseline_dossier_sha, "revised dossier sha256")
    assert_equal(sha(paths["causal_dossier"]), invariants["causal_dossier_sha256"], "invariant dossier sha256")
    gap = dossier["expected_actual_gap"]
    assert_equal(gap["expected"]["statement"], "Reuters集計の市場予想は7月非農業部門雇用者数+8万人。", "Expected")
    assert_equal(gap["actual"]["statement"], "BLS発表の7月非農業部門雇用者数は-2.3万人。", "Actual")
    assert_equal(gap["gap"]["statement"], "Expected +8万人に対しActual -2.3万人で、Gapは-10.3万人。", "Gap")
    assert_equal(plan["central_contradiction_id"], invariants["central_contradiction_id"], "central contradiction")
    assert_equal(plan["midpoint_turn"]["scene_id"], "scene-06", "Understanding Upgrade scene")
    assert_equal(set(plan["midpoint_turn"]["evidence_ids"]), set(invariants["chronology"]["minute_evidence_ids"]), "Understanding Upgrade evidence")

    scenes = {row["scene_id"]: row for row in plan["scenes"]}
    assert_equal(set(scenes["scene-06"]["new_evidence_ids"]), set(invariants["chronology"]["minute_evidence_ids"]), "Scene 6 minute-evidence branch")
    if not {"E-005", "E-006", "E-007"} <= set(scenes["scene-07"]["new_evidence_ids"]):
        raise SystemExit("Scene 7 no longer resolves company-specific engine plus counterexamples")

    retained = set(script["retained_counterevidence_ids"])
    missing = set(invariants["material_counterevidence_ids"]) - retained
    if missing:
        raise SystemExit(f"revised script dropped material counterevidence: {sorted(missing)}")

    claims = {claim["claim_id"]: claim for scene in script["scenes"] for claim in scene["causal_claims"]}
    for claim_id in ("claim-09", "claim-10"):
        if claims[claim_id]["scope"] == "nasdaq_support":
            raise SystemExit(f"{claim_id} promoted company material to NASDAQ support")

    narration = "\n".join(row["narration"] for row in script["scenes"])
    for phrase in ("1分足だけで因果は証明できません", "別エンジン", "違う理由の上昇が同じ指数方向へ重なった"):
        if phrase not in narration:
            raise SystemExit(f"revised narration lost required meaning: {phrase}")

    if review["verdict"] != "pass":
        raise SystemExit(f"revised review is not PASS: {review['verdict']}")
    if any(row["severity"] in {"critical", "major"} for row in review["findings"]):
        raise SystemExit("revised review contains unresolved critical/major finding")

    return {
        "story_plan_sha256": sha(paths["story_plan"]),
        "story_script_sha256": sha(paths["story_script"]),
        "creative_review_sha256": sha(paths["creative_review"]),
        "understanding_upgrade_scene": plan["midpoint_turn"]["scene_id"],
        "scene_6_evidence_ids": scenes["scene-06"]["new_evidence_ids"],
        "scene_7_evidence_ids": scenes["scene-07"]["new_evidence_ids"],
        "review_total_score": review["total_score"],
        "review_verdict": review["verdict"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--acceptance-source", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    acceptance_source = args.acceptance_source.resolve()
    receipt = load(root / RECEIPT_REL)
    invariants = load(root / INVARIANTS_REL)

    _verify_acceptance_checkout(acceptance_source)
    _copy_acceptance_payload(root, acceptance_source)
    _materialize_h4_baseline(root, acceptance_source)
    baseline = _verify_historical_baseline(root, receipt)

    revised_materialization = _patch_revised_templates(root)
    assert_equal(revised_materialization["causal_dossier_sha256"], baseline["causal_dossier"], "revised patch dossier lineage")
    _materialize_revised(root)
    revised = _verify_invariants(root, invariants, baseline["causal_dossier"])

    report = {
        "contract_version": "1.0.0",
        "episode_date": DATE,
        "status": "pass",
        "baseline_source": receipt["source"],
        "baseline": {
            **baseline,
            "historical_score": 29,
            "historical_verdict": "pass",
            "historical_findings": [],
            "structure": "earnings branch in Scene 6; strongest minute-timing branch in Scene 8",
        },
        "revised": revised,
        "causal_dossier_unchanged": True,
        "semantic_interest_judgment": {
            "deterministic_ci_scope": "lineage, schemas, chronology, evidence retention, scope boundaries, and A/B structure",
            "editorial_critic_scope": "FACT_STACKING / LOW_INFORMATION_GAIN / PAYOFF_DROUGHT / WEAK_SURPRISE remain semantic judgments",
        },
    }
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    output = args.output or root / f"verification/{DATE}/story_interest_regression.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
