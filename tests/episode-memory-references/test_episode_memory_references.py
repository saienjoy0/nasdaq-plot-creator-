from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[2]
    / "skills/nasdaq-cafe-episode-production/validators/validate_episode_memory_references.py"
)
spec = importlib.util.spec_from_file_location("validator", MODULE_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(validator)


def base_dossier():
    return {
        "episode_date": "2026-08-06",
        "validation": {"status": "pass"},
        "evidence": [
            {"evidence_id": "E-001"},
            {"evidence_id": "E-002"},
            {"evidence_id": "E-003"},
        ],
        "memory_revalidation": [
            {
                "memory_reference_type": "claim",
                "memory_reference_id": "ai-capex-evaluation-axis",
                "historical_confidence": "medium",
                "retrieval_use_mode": "current_revalidation_required",
                "revalidation_status": "supported",
                "current_evidence_ids": ["E-001", "E-002"],
                "difference_from_previous": "Current filings still support the same evaluation axis.",
                "editorial_use": "explanation_context",
                "notes": "",
            },
            {
                "memory_reference_type": "thread",
                "memory_reference_id": "old-thread",
                "historical_confidence": "low",
                "retrieval_use_mode": "current_revalidation_required",
                "revalidation_status": "invalidated",
                "current_evidence_ids": ["E-003"],
                "difference_from_previous": "The former relationship no longer holds.",
                "editorial_use": "counterevidence",
                "notes": "",
            },
        ],
    }


def refs_for_supported():
    return {
        "schema_version": "1.0.0",
        "episode_date": "2026-08-06",
        "references": [
            {
                "memory_reference_type": "claim",
                "memory_reference_id": "ai-capex-evaluation-axis",
                "historical_confidence": "medium",
                "current_revalidation_status": "supported",
                "current_evidence_ids": ["E-001", "E-002"],
                "difference_from_previous": "Current filings still support the same evaluation axis.",
                "editorial_use": "explanation_context",
                "scene_ids": ["scene-04", "scene-07"],
                "public_usage_mode": "current_supported_context",
            }
        ],
        "validation": {"status": "pass", "errors": [], "warnings": []},
    }


class EpisodeMemoryReferenceTests(unittest.TestCase):
    def assert_pass(self, dossier, refs):
        errors, _ = validator.validate(dossier, refs)
        self.assertEqual([], errors)

    def assert_fail_contains(self, dossier, refs, needle):
        errors, _ = validator.validate(dossier, refs)
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_supported_current_context_passes(self):
        self.assert_pass(base_dossier(), refs_for_supported())

    def test_no_memory_is_allowed(self):
        refs = refs_for_supported()
        refs["references"] = []
        errors, warnings = validator.validate(base_dossier(), refs)
        self.assertEqual([], errors)
        self.assertTrue(warnings)

    def test_unknown_memory_is_rejected(self):
        refs = refs_for_supported()
        refs["references"][0]["memory_reference_id"] = "missing"
        self.assert_fail_contains(base_dossier(), refs, "not found")

    def test_status_mismatch_is_rejected(self):
        refs = refs_for_supported()
        refs["references"][0]["current_revalidation_status"] = "partially_supported"
        self.assert_fail_contains(base_dossier(), refs, "does not match dossier")

    def test_evidence_mismatch_is_rejected(self):
        refs = refs_for_supported()
        refs["references"][0]["current_evidence_ids"] = ["E-001"]
        self.assert_fail_contains(base_dossier(), refs, "must exactly match dossier")

    def test_missing_evidence_is_rejected(self):
        dossier = base_dossier()
        dossier["evidence"] = [{"evidence_id": "E-001"}]
        self.assert_fail_contains(dossier, refs_for_supported(), "missing dossier evidence")

    def test_historical_only_cannot_be_current_context(self):
        dossier = base_dossier()
        entry = dossier["memory_revalidation"][0]
        entry["revalidation_status"] = "historical_context_only"
        entry["current_evidence_ids"] = []
        entry["editorial_use"] = "comparison"
        refs = refs_for_supported()
        ref = refs["references"][0]
        ref["current_revalidation_status"] = "historical_context_only"
        ref["current_evidence_ids"] = []
        ref["editorial_use"] = "comparison"
        self.assert_fail_contains(dossier, refs, "not permitted")

    def test_invalidated_counterevidence_passes(self):
        refs = refs_for_supported()
        refs["references"] = [
            {
                "memory_reference_type": "thread",
                "memory_reference_id": "old-thread",
                "historical_confidence": "low",
                "current_revalidation_status": "invalidated",
                "current_evidence_ids": ["E-003"],
                "difference_from_previous": "The former relationship no longer holds.",
                "editorial_use": "counterevidence",
                "scene_ids": ["scene-07"],
                "public_usage_mode": "counterevidence",
            }
        ]
        self.assert_pass(base_dossier(), refs)

    def test_invalidated_cannot_be_current_context(self):
        refs = refs_for_supported()
        ref = refs["references"][0]
        ref.update(
            {
                "memory_reference_type": "thread",
                "memory_reference_id": "old-thread",
                "historical_confidence": "low",
                "current_revalidation_status": "invalidated",
                "current_evidence_ids": ["E-003"],
                "difference_from_previous": "The former relationship no longer holds.",
                "editorial_use": "counterevidence",
                "public_usage_mode": "current_supported_context",
            }
        )
        self.assert_fail_contains(base_dossier(), refs, "not permitted")

    def test_internal_only_must_not_have_scene_ids(self):
        refs = refs_for_supported()
        refs["references"][0]["public_usage_mode"] = "internal_only"
        self.assert_fail_contains(base_dossier(), refs, "must not declare public scene_ids")

    def test_public_usage_requires_scene(self):
        refs = refs_for_supported()
        refs["references"][0]["scene_ids"] = []
        self.assert_fail_contains(base_dossier(), refs, "requires at least one scene_id")

    def test_duplicate_reference_is_rejected(self):
        refs = refs_for_supported()
        refs["references"].append(copy.deepcopy(refs["references"][0]))
        self.assert_fail_contains(base_dossier(), refs, "duplicate episode memory reference")

    def test_episode_date_mismatch_is_rejected(self):
        refs = refs_for_supported()
        refs["episode_date"] = "2026-08-07"
        self.assert_fail_contains(base_dossier(), refs, "episode_date mismatch")

    def test_unvalidated_dossier_is_rejected(self):
        dossier = base_dossier()
        dossier["validation"]["status"] = "fail"
        self.assert_fail_contains(dossier, refs_for_supported(), "must be pass")


if __name__ == "__main__":
    unittest.main()
