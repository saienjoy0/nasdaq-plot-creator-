from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY_TEST = ROOT / "tests/story-engine/test_story_engine.py"
CATALOG = ROOT / "skills/nasdaq-cafe-story-engine/fixtures/fixture_catalog.json"

spec = importlib.util.spec_from_file_location("story_engine_test_harness", LEGACY_TEST)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)
Harness = module.Harness

EXPECTED_IDS = {
    "valid_single_driver",
    "valid_multi_factor",
    "valid_reason_unknown",
}


def assert_case(case: dict) -> None:
    expected = case["expected"]
    harness = Harness(case["harness_kind"])
    try:
        result = harness.validate()
        assert result["status"] == expected["validation_status"], result

        baseline = harness.pkg["editorial_baseline"]
        assert baseline["lead_type"] == expected["lead_type"]
        assert baseline["causality_scope"] == expected["causality_scope"]
        assert baseline["confidence"] == expected["confidence"]
        assert baseline["primary_driver"] == expected["primary_driver"]

        for key in ("amplifiers", "offsets", "unresolved_factors"):
            if key in expected:
                assert baseline[key] == expected[key]

        angles = harness.pkg["story_discovery"]["angle_candidates"]
        eligible = [item for item in angles if item["eligible"]]
        assert len(eligible) == expected["eligible_angle_count"]
        assert eligible[0]["angle_type"] == expected["angle_type"]
    finally:
        harness.close()


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    valid_entries = {
        item["id"]: item
        for item in catalog["fixtures"]
        if item.get("kind") == "valid"
    }
    assert set(valid_entries) == EXPECTED_IDS, valid_entries

    for fixture_id in sorted(EXPECTED_IDS):
        entry = valid_entries[fixture_id]
        case_path = ROOT / entry["case_path"]
        assert case_path.is_file(), case_path
        case = json.loads(case_path.read_text(encoding="utf-8"))
        assert case["contract_version"] == "1.0.0"
        assert case["id"] == fixture_id
        assert_case(case)

    print("committed Story Engine valid fixtures: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
