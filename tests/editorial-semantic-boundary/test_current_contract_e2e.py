from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = Path(__file__).with_name("current_fixture.py")
SPEC = importlib.util.spec_from_file_location("current_editorial_fixture", FIXTURE_PATH)
assert SPEC and SPEC.loader
fx = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fx)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_workspace(tmp_path: Path) -> tuple[Path, dict]:
    root = tmp_path / "repo"
    root.mkdir()
    fx.install_runtime(ROOT, root)
    fx.make_canon(root)

    daily = root / "daily-inputs" / fx.DATE / f"daily_source_package_{fx.DATE}.md"
    daily.parent.mkdir(parents=True, exist_ok=True)
    daily.write_text("synthetic daily source\n", encoding="utf-8")
    query = root / "working" / fx.DATE / "memory_query_plan.json"
    context = root / "working" / fx.DATE / f"memory_context_{fx.DATE}.md"
    report = root / "working" / fx.DATE / f"memory_retrieval_report_{fx.DATE}.json"
    fx.write_json(query, fx.query_plan())
    context.write_text("# synthetic memory context\n", encoding="utf-8")
    fx.write_json(report, fx.retrieval_report(query.relative_to(root).as_posix()))
    manifest = root / "research" / fx.DATE / "research_input_manifest.json"
    fx.write_json(manifest, fx.research_manifest(root, daily, query, context, report))
    dossier = root / "research" / fx.DATE / f"causal_research_dossier_{fx.DATE}.json"
    fx.write_json(dossier, fx.dossier(root, manifest, daily))

    validator = load_module(
        "fixture_causal_validator",
        root / "skills/nasdaq-cafe-causal-research/validators/validate_causal_research_dossier.py",
    )
    context_bytes = context.read_bytes()
    report_bytes = report.read_bytes()

    def deterministic_runner(_query, context_out, report_out, **_kwargs):
        context_out.write_bytes(context_bytes)
        report_out.write_bytes(report_bytes)
        return {}

    result = validator.validate_dossier(
        dossier,
        manifest,
        report,
        contracts_dir=root / "skills/nasdaq-cafe-causal-research/contracts",
        repo_root=root,
        retrieval_runner=deterministic_runner,
    )
    assert result.ok, result.errors
    receipt = validator.build_validation_receipt(
        result=result,
        dossier_path=dossier,
        manifest_path=manifest,
        retrieval_report_path=report,
        contracts_dir=root / "skills/nasdaq-cafe-causal-research/contracts",
        repo_root=root,
    )
    receipt_errors = validator._validate_receipt_schema(
        receipt,
        root / "skills/nasdaq-cafe-causal-research/contracts/causal_dossier_validation_receipt.schema.json",
    )
    assert receipt_errors == []
    receipt_path = root / "research" / fx.DATE / "causal_dossier_validation.json"
    fx.write_json(receipt_path, receipt)

    authoring = fx.canonical_authoring(root, dossier)
    authoring["causalDossier"]["validation"] = fx.file_ref(root, receipt_path)
    authoring_path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(authoring_path, authoring)

    # Freeze 1.2 retains raw parts as lineage only. One tiny part is sufficient here.
    part = root / "daily-authoring-parts" / fx.DATE / "00_fixture.json"
    fx.write_json(part, {"contractVersion": "2.0.0", "episodeDate": fx.DATE, "fixture": True})
    return root, authoring


def test_current_contract_positive_semantic_chain(tmp_path: Path):
    root, authoring = build_workspace(tmp_path)
    semantic = load_module("fixture_semantic_boundary", root / "scripts/validate_editorial_semantic_boundary.py")
    acceptance = semantic.validate_boundary(root, fx.DATE, root / "daily-authoring" / f"{fx.DATE}.json")
    acceptance_path = root / "verification" / fx.DATE / "editorial_semantic_acceptance.json"
    semantic.atomic_write_json(acceptance_path, acceptance)
    semantic.verify_acceptance(root, fx.DATE, acceptance_path)

    freeze = load_module("fixture_semantic_freeze", root / "scripts/chatgpt_semantic_freeze.py")
    freeze_path = root / "semantic-freezes" / f"{fx.DATE}.json"
    freeze.write_manifest(root, fx.DATE, freeze_path)
    verified = freeze.verify_manifest(root, fx.DATE, freeze_path)
    assert verified["contractVersion"] == "1.2.0"

    # File-linkage cycle is deterministic before sidecar creation.
    predicted = authoring["storyScript"]["story_plan"]
    sidecar = root / predicted["path"]
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_bytes(fx.canonical_projection_bytes(authoring["storyPlan"]))
    assert fx.sha(sidecar) == predicted["sha256"]


def test_missing_temporal_usage_fails_official_story_validator(tmp_path: Path):
    root, authoring = build_workspace(tmp_path)
    del authoring["storyPlan"]["temporal_usage"]
    authoring["storyScript"]["story_plan"]["sha256"] = fx.sha_bytes(
        fx.canonical_projection_bytes(authoring["storyPlan"])
    )
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, authoring)
    semantic = load_module("fixture_semantic_missing_temporal", root / "scripts/validate_editorial_semantic_boundary.py")
    with pytest.raises(Exception, match="temporal_usage|Temporal"):
        semantic.validate_boundary(root, fx.DATE, path)


def test_material_counterevidence_omission_fails(tmp_path: Path):
    root, authoring = build_workspace(tmp_path)
    authoring["storyPlan"]["angle_candidates"][0]["counterevidence_ids"] = []
    # Rebind the predicted Story Plan SHA because linkage is machine-owned, so the
    # failure comes from the official material-counterevidence rule, not stale linkage.
    authoring["storyScript"]["story_plan"]["sha256"] = fx.sha_bytes(
        fx.canonical_projection_bytes(authoring["storyPlan"])
    )
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, authoring)
    semantic = load_module("fixture_semantic_counter", root / "scripts/validate_editorial_semantic_boundary.py")
    with pytest.raises(Exception, match="material counterevidence"):
        semantic.validate_boundary(root, fx.DATE, path)


def test_stale_dossier_receipt_fails_before_story(tmp_path: Path):
    root, _ = build_workspace(tmp_path)
    dossier = root / "research" / fx.DATE / f"causal_research_dossier_{fx.DATE}.json"
    value = json.loads(dossier.read_text(encoding="utf-8"))
    value["editorial_handoff"]["central_hypothesis"] += " changed"
    fx.write_json(dossier, value)
    verifier = load_module("fixture_research_receipt", root / "scripts/materialize_causal_research.py")
    with pytest.raises(Exception, match="sha256 mismatch"):
        verifier.verify_validation_receipt(root, fx.DATE, root / "research" / fx.DATE / "causal_dossier_validation.json")


def test_unknown_dossier_contract_fails_closed(tmp_path: Path):
    root, _ = build_workspace(tmp_path)
    validator = load_module(
        "fixture_causal_unknown",
        root / "skills/nasdaq-cafe-causal-research/validators/validate_causal_research_dossier.py",
    )
    dossier_path = root / "research" / fx.DATE / f"causal_research_dossier_{fx.DATE}.json"
    dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
    dossier["contract_version"] = "9.9.9"
    fx.write_json(dossier_path, dossier)
    report = root / "working" / fx.DATE / f"memory_retrieval_report_{fx.DATE}.json"
    manifest = root / "research" / fx.DATE / "research_input_manifest.json"
    result = validator.validate_dossier(
        dossier_path, manifest, report,
        contracts_dir=root / "skills/nasdaq-cafe-causal-research/contracts", repo_root=root,
        retrieval_runner=lambda *_args, **_kwargs: {},
    )
    assert not result.ok
    assert any("unsupported Causal Dossier contract_version" in error for error in result.errors)


def test_story_narration_production_drift_fails(tmp_path: Path):
    root, authoring = build_workspace(tmp_path)
    authoring["production"]["scenes"][0]["chunks"][0]["text"] += " drift"
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, authoring)
    semantic = load_module("fixture_semantic_narration", root / "scripts/validate_editorial_semantic_boundary.py")
    with pytest.raises(Exception, match="production narration differs"):
        semantic.validate_boundary(root, fx.DATE, path)


def test_missing_creative_review_fails_schema(tmp_path: Path):
    root, authoring = build_workspace(tmp_path)
    del authoring["creativeReview"]
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, authoring)
    semantic = load_module("fixture_semantic_review", root / "scripts/validate_editorial_semantic_boundary.py")
    with pytest.raises(Exception, match="creativeReview"):
        semantic.validate_boundary(root, fx.DATE, path)


def test_implicit_visual_mode_is_rejected(tmp_path: Path):
    root, authoring = build_workspace(tmp_path)
    del authoring["production"]["scenes"][0]["beats"][0]["visualMode"]
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, authoring)
    semantic = load_module("fixture_semantic_visual_mode", root / "scripts/validate_editorial_semantic_boundary.py")
    with pytest.raises(Exception, match="visualMode"):
        semantic.validate_boundary(root, fx.DATE, path)


def test_implicit_expression_is_rejected(tmp_path: Path):
    root, authoring = build_workspace(tmp_path)
    del authoring["production"]["scenes"][0]["chunks"][0]["expression"]
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, authoring)
    semantic = load_module("fixture_semantic_expression", root / "scripts/validate_editorial_semantic_boundary.py")
    with pytest.raises(Exception, match="expression"):
        semantic.validate_boundary(root, fx.DATE, path)


def test_stale_acceptance_after_validator_change_fails(tmp_path: Path):
    root, _ = build_workspace(tmp_path)
    semantic = load_module("fixture_semantic_acceptance", root / "scripts/validate_editorial_semantic_boundary.py")
    acceptance = semantic.validate_boundary(root, fx.DATE, root / "daily-authoring" / f"{fx.DATE}.json")
    acceptance_path = root / "verification" / fx.DATE / "editorial_semantic_acceptance.json"
    semantic.atomic_write_json(acceptance_path, acceptance)
    validator = root / "skills/nasdaq-cafe-story-plan/validators/validate_story_plan.py"
    validator.write_text(validator.read_text(encoding="utf-8") + "\n# contract changed\n", encoding="utf-8")
    with pytest.raises(Exception, match="contractBindings are stale"):
        semantic.verify_acceptance(root, fx.DATE, acceptance_path)


def test_stale_freeze_after_authoring_change_fails(tmp_path: Path):
    root, _ = build_workspace(tmp_path)
    semantic = load_module("fixture_semantic_freeze_prep", root / "scripts/validate_editorial_semantic_boundary.py")
    acceptance = semantic.validate_boundary(root, fx.DATE, root / "daily-authoring" / f"{fx.DATE}.json")
    acceptance_path = root / "verification" / fx.DATE / "editorial_semantic_acceptance.json"
    semantic.atomic_write_json(acceptance_path, acceptance)
    freeze = load_module("fixture_freeze_stale", root / "scripts/chatgpt_semantic_freeze.py")
    freeze_path = root / "semantic-freezes" / f"{fx.DATE}.json"
    freeze.write_manifest(root, fx.DATE, freeze_path)
    authoring_path = root / "daily-authoring" / f"{fx.DATE}.json"
    authoring = json.loads(authoring_path.read_text(encoding="utf-8"))
    authoring["publishing"]["description"] += " changed"
    fx.write_json(authoring_path, authoring)
    with pytest.raises(Exception, match="stale|Acceptance"):
        freeze.verify_manifest(root, fx.DATE, freeze_path)


def test_research_authoring_input_must_be_exactly_one(tmp_path: Path):
    module = load_module("fixture_research_exactly_one", ROOT / "scripts/materialize_causal_research.py")
    one = tmp_path / "one.json"
    two = tmp_path / "two.json"
    fx.write_json(one, {"researchAuthoring": {"memoryQueryPlan": {"a": 1}}})
    fx.write_json(two, {"memoryQueryPlan": {"a": 2}})
    assert module.extract_exactly_one([one], field="memoryQueryPlan") == {"a": 1}
    with pytest.raises(Exception, match="exactly once"):
        module.extract_exactly_one([one, two], field="memoryQueryPlan")


def test_fixture_has_exactly_9_scenes_and_18_beats(tmp_path: Path):
    root, authoring = build_workspace(tmp_path)
    assert len(authoring["storyPlan"]["scenes"]) == 9
    assert len(authoring["storyScript"]["scenes"]) == 9
    assert len(authoring["creativeReview"]["scene_checks"]) == 8
    assert len(authoring["production"]["scenes"]) == 9
    assert sum(len(scene["beats"]) for scene in authoring["production"]["scenes"]) == 18


def test_stale_dossier_receipt_after_validator_change_fails(tmp_path: Path):
    root, _ = build_workspace(tmp_path)
    validator_path = root / "skills/nasdaq-cafe-causal-research/validators/validate_causal_research_dossier.py"
    validator_path.write_text(validator_path.read_text(encoding="utf-8") + "\n# validator changed\n", encoding="utf-8")
    verifier = load_module("fixture_receipt_validator_stale", root / "scripts/materialize_causal_research.py")
    receipt = root / "research" / fx.DATE / "causal_dossier_validation.json"
    with pytest.raises(Exception, match="sha256 mismatch"):
        verifier.verify_validation_receipt(root, fx.DATE, receipt)


def test_stale_dossier_receipt_after_dependency_change_fails(tmp_path: Path):
    root, _ = build_workspace(tmp_path)
    dependency = root / "scripts/build_research_input_manifest.py"
    dependency.write_text(dependency.read_text(encoding="utf-8") + "\n# dependency changed\n", encoding="utf-8")
    verifier = load_module("fixture_receipt_dependency_stale", root / "scripts/materialize_causal_research.py")
    receipt = root / "research" / fx.DATE / "causal_dossier_validation.json"
    with pytest.raises(Exception, match="sha256 mismatch"):
        verifier.verify_validation_receipt(root, fx.DATE, receipt)


def test_story_script_wrong_predicted_plan_sha_fails(tmp_path: Path):
    root, authoring = build_workspace(tmp_path)
    authoring["storyScript"]["story_plan"]["sha256"] = "f" * 64
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, authoring)
    semantic = load_module("fixture_semantic_wrong_plan_ref", root / "scripts/validate_editorial_semantic_boundary.py")
    with pytest.raises(Exception, match="deterministic post-Freeze Story Plan projection"):
        semantic.validate_boundary(root, fx.DATE, path)


def test_missing_authored_review_scene_check_is_not_filled(tmp_path: Path):
    root, authoring = build_workspace(tmp_path)
    authoring["creativeReview"]["scene_checks"].pop()
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, authoring)
    semantic = load_module("fixture_semantic_missing_scene_check", root / "scripts/validate_editorial_semantic_boundary.py")
    with pytest.raises(Exception, match="scene_checks|too short|8"):
        semantic.validate_boundary(root, fx.DATE, path)


def test_flat_legacy_authoring_is_rejected_by_current_semantic_boundary(tmp_path: Path):
    root, _ = build_workspace(tmp_path)
    legacy = {"episodeDate": fx.DATE, "scenes": []}
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, legacy)
    semantic = load_module("fixture_semantic_legacy_reject", root / "scripts/validate_editorial_semantic_boundary.py")
    with pytest.raises(Exception, match="contractVersion|required"):
        semantic.validate_boundary(root, fx.DATE, path)


def test_validation_projection_drift_stales_acceptance(tmp_path: Path):
    root, _ = build_workspace(tmp_path)
    semantic = load_module("fixture_semantic_projection_stale", root / "scripts/validate_editorial_semantic_boundary.py")
    acceptance = semantic.validate_boundary(root, fx.DATE, root / "daily-authoring" / f"{fx.DATE}.json")
    acceptance_path = root / "verification" / fx.DATE / "editorial_semantic_acceptance.json"
    semantic.atomic_write_json(acceptance_path, acceptance)
    projection_path = root / acceptance["validationProjections"]["storyPlan"]["path"]
    projection = json.loads(projection_path.read_text(encoding="utf-8"))
    projection["story_spine"] += " drift"
    fx.write_json(projection_path, projection)
    with pytest.raises(Exception, match="sha256 mismatch|projection drifted"):
        semantic.verify_acceptance(root, fx.DATE, acceptance_path)


def test_story_plan_script_connector_drift_fails(tmp_path: Path):
    root, authoring = build_workspace(tmp_path)
    authoring["storyScript"]["scenes"][1]["connection_to_previous"] = "therefore"
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, authoring)
    semantic = load_module("fixture_semantic_connector_drift", root / "scripts/validate_editorial_semantic_boundary.py")
    with pytest.raises(Exception, match="connector differs"):
        semantic.validate_boundary(root, fx.DATE, path)


def test_story_plan_script_evidence_drift_fails(tmp_path: Path):
    root, authoring = build_workspace(tmp_path)
    authoring["storyScript"]["scenes"][1]["evidence_ids"] = ["E-001"]
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, authoring)
    semantic = load_module("fixture_semantic_evidence_drift", root / "scripts/validate_editorial_semantic_boundary.py")
    with pytest.raises(Exception, match="evidence IDs differ"):
        semantic.validate_boundary(root, fx.DATE, path)
