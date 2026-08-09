from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATOR = ROOT / "skills/nasdaq-cafe-story-plan/migrate_v1_1_to_v1_2.py"

spec = importlib.util.spec_from_file_location("story_plan_migrator", MIGRATOR)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)


def legacy_plan() -> dict:
    scenes = []
    for i in range(1, 10):
        scenes.append({
            "scene_id": f"scene-{i:02d}",
            "remaining_question": "次に確認します" if i == 3 else ("why?" if i <= 7 else "legacy tail"),
        })
    return {"contract_version": "1.1.0", "scenes": scenes}


def test_migration_renames_field_and_requires_review():
    target, report = module.migrate(legacy_plan())
    assert target["contract_version"] == "1.2.0"
    assert all("remaining_question" not in scene for scene in target["scenes"])
    assert target["scenes"][0]["continuation_reason"] == "why?"
    assert target["scenes"][7]["continuation_reason"] == ""
    assert target["scenes"][8]["continuation_reason"] == ""
    assert report["status"] == "review_required"


def test_migration_flags_procedural_legacy_continuation():
    _, report = module.migrate(legacy_plan())
    scene_03 = report["scene_reports"][2]
    assert scene_03["classification"] == "procedural_review_required"


def test_scene_08_legacy_question_is_discarded_into_report():
    _, report = module.migrate(legacy_plan())
    scene_08 = report["scene_reports"][7]
    assert scene_08["migrated_continuation_reason"] == ""
    assert scene_08["closure_discarded_legacy_text"] == "legacy tail"
