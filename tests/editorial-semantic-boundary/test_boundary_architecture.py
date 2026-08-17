from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_new_json_schemas_are_valid_draft_2020_12():
    for rel in (
        "contracts/chatgpt_daily_authoring_v2.schema.json",
        "contracts/editorial_semantic_acceptance.schema.json",
        "contracts/chatgpt_semantic_freeze.schema.json",
        "skills/nasdaq-cafe-causal-research/contracts/causal_dossier_validation_receipt.schema.json",
    ):
        Draft202012Validator.check_schema(json.loads((ROOT / rel).read_text(encoding="utf-8")))


def test_production_cannot_duplicate_story_or_review_authority():
    schema = json.loads((ROOT / "contracts/chatgpt_daily_authoring_v2.schema.json").read_text(encoding="utf-8"))
    props = schema["$defs"]["production"]["properties"]
    for key in (
        "editorial",
        "review",
        "expectedConfirmed",
        "retainedCounterevidenceIds",
        "unresolvedPoints",
        "centralContradiction",
        "centralQuestion",
        "selectedAngleId",
        "openingPromise",
        "midpointTurn",
        "closingReframe",
        "openLoops",
    ):
        assert props[key] is False


def test_current_v2_authoring_requires_explicit_presentation_intent():
    schema = json.loads((ROOT / "contracts/chatgpt_daily_authoring_v2.schema.json").read_text(encoding="utf-8"))
    scene_required = set(schema["$defs"]["scene"]["required"])
    beat_required = set(schema["$defs"]["beat"]["required"])
    chunk_required = set(schema["$defs"]["chunk"]["required"])
    assert {"visualMode", "initialExpression", "sceneRole", "causalScope"} <= scene_required
    assert {"primaryFunction", "visualMode", "visualTemplate", "transitionRole"} <= beat_required
    assert {"text", "expression"} <= chunk_required


def test_research_input_extraction_is_fail_closed(tmp_path: Path):
    module = _load("materialize_causal_research_arch", ROOT / "scripts/materialize_causal_research.py")
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text(json.dumps({"researchAuthoring": {"memoryQueryPlan": {"x": 1}}}), encoding="utf-8")
    b.write_text(json.dumps({"memoryQueryPlan": {"x": 2}}), encoding="utf-8")
    assert module.extract_exactly_one([a], field="memoryQueryPlan") == {"x": 1}
    try:
        module.extract_exactly_one([a, b], field="memoryQueryPlan")
    except module.ResearchMaterializationError as exc:
        assert "exactly once" in str(exc)
    else:
        raise AssertionError("duplicate Research authoring input must fail")


def test_freeze_contract_binds_acceptance_not_story_sidecars():
    schema = json.loads((ROOT / "contracts/chatgpt_semantic_freeze.schema.json").read_text(encoding="utf-8"))
    required = set(schema["required"])
    assert "editorialSemanticAcceptance" in required
    assert "canonicalAuthoring" in required
    assert "causalDossierValidation" in required
    assert "storyPlan" not in required
    assert "storyScript" not in required
    assert "creativeReview" not in required


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_pr_a_current_v2_core_has_no_aug17_migration_literal():
    for rel in (
        "scripts/materialize_causal_research.py",
        "scripts/validate_editorial_semantic_boundary.py",
        "scripts/chatgpt_semantic_freeze.py",
        "contracts/chatgpt_daily_authoring_v2.schema.json",
        "contracts/editorial_semantic_acceptance.schema.json",
    ):
        assert "2026-08-17" not in _text(rel), rel


def test_current_v2_runtime_path_has_no_fixup_or_semantic_creation():
    closure = _text("scripts/run_daily_renderer_closure_v12.py")
    frozen_wrapper = _text("scripts/run_semantic_frozen_renderer_closure_v12.py")
    assert "fixup_chatgpt_daily_materialization.py" not in closure
    assert "NASDAQ_CAFE_SEMANTIC_FREEZE_PATH" in closure
    assert "editorial_semantic_acceptance.json" in closure
    assert '"scripts/materialize_causal_research.py"' not in closure
    assert '"scripts/validate_editorial_semantic_boundary.py"' not in closure
    assert "create_manifest" not in frozen_wrapper
    assert "write_manifest" not in frozen_wrapper


def test_story_materializer_is_projection_only_for_v2():
    text = _text("scripts/story-engine/materialize_story_engine.py")
    start = text.index("def _materialize_current_v2")
    end = text.index("def main()", start)
    v2 = text[start:end]
    assert 'authoring["storyPlan"]' in v2
    assert 'authoring["storyScript"]' in v2
    assert 'authoring["creativeReview"]' in v2
    assert '"semantic_writer": False' in v2
    assert "temporalUsage" not in v2
    assert "temporal_usage" not in v2


def test_ws4_contains_v2_identity_branch_and_legacy_fallback():
    text = _text("scripts/story-engine/project_story_script_to_production.py")
    assert 'authoring.get("contractVersion") == "2.0.0"' in text
    assert "projected Story Plan differs from frozen Daily Authoring v2" in text
    assert "projected Story Script differs from frozen Daily Authoring v2" in text
    assert "retainedCounterevidenceIds" in text


def test_preview_workflow_installs_semantic_dependencies_before_freeze_verify():
    text = _text(".github/workflows/chatgpt-daily-preview-production.yml")
    dependency = text.index("Install semantic verification dependencies")
    freeze = text.index("Verify committed ChatGPT semantic freeze")
    acceptance = text.index("Verify current Editorial Semantic Acceptance")
    renderer = text.index("Resolve canonical Renderer binding")
    assert dependency < freeze < acceptance < renderer
    assert "jsonschema referencing" in text
    assert "actions/setup-python@v5" in text
