#!/usr/bin/env python3
"""Apply the FVU-R3 plot-to-renderer compatibility patch deterministically."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PatchError(RuntimeError):
    pass


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise PatchError(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def patch_cross_artifact(text: str) -> str:
    if "EXPECTED_COMPATIBILITY_MATRIX" not in text:
        anchor = "class CrossArtifactError(ValueError):\n    pass\n\n\n"
        addition = anchor + '''EXPECTED_COMPATIBILITY_MATRIX = {
    "matrixId": "financial-visual-compat-2026-08",
    "status": "pass",
    "plotCreator": {
        "repository": "saienjoy0/nasdaq-plot-creator-",
        "financialIntentVersion": "1.1.0",
        "financialRecipePlanVersion": "1.0.0",
        "finalEpisodeContractVersion": "1.0.0",
    },
    "renderer": {
        "repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion",
        "renderSpecVersion": "2.3.0",
        "financialTemplateRegistryVersion": "1.0.0",
        "financialVisualTraceVersion": "1.0.0",
    },
}


'''
        text = replace_once(text, anchor, addition, "compatibility matrix constant")

    if "def validate_compatibility_matrix(" not in text:
        anchor = '''def load_schema(path: Path) -> dict[str, Any]:
    return load_json(path, "schema")


'''
        addition = anchor + '''def validate_compatibility_matrix(
    path: Path,
    renderer_schema_version: str,
) -> tuple[dict[str, Any], str]:
    matrix = load_json(path, "financial visual compatibility matrix")
    if matrix != EXPECTED_COMPATIBILITY_MATRIX:
        raise CrossArtifactError(
            "financial visual compatibility matrix does not exactly match the approved cross-repository tuple"
        )
    if matrix["renderer"]["renderSpecVersion"] != renderer_schema_version:
        raise CrossArtifactError(
            "renderer schema version disagrees with financial visual compatibility matrix"
        )
    return matrix, sha256_file(path)


'''
        text = replace_once(text, anchor, addition, "compatibility validator")

    old_config = '''        render_beat["templateConfig"] = {
            "variant": selection["templateVariant"],
            "displayOrder": selected_plan["displayOrder"],
            "comparisonBasis": selected_plan["comparisonBasis"],
            "metricIds": selection["metricIds"],
            "causalStepIds": selection["causalStepIds"],
            "highlightObjectIds": selected_plan["highlightObjectIds"],
        }
'''
    new_config = '''        causal_step_ids = selection["causalStepIds"]
        render_beat["templateConfig"] = {
            "variant": selection["templateVariant"],
            "comparisonBasis": selected_plan["comparisonBasis"],
            "dataBasis": "financial-recipe-plan",
            "nodeOrder": causal_step_ids[:4],
            "laneLabels": [],
            "outcomeNodeId": causal_step_ids[-1] if causal_step_ids else None,
            "displayOrder": selected_plan["displayOrder"],
            "metricIds": selection["metricIds"],
            "causalStepIds": causal_step_ids,
            "highlightObjectIds": selected_plan["highlightObjectIds"],
        }
'''
    if '"dataBasis": "financial-recipe-plan"' not in text:
        text = replace_once(text, old_config, new_config, "renderer 2.3 TemplateConfig")

    if "compatibility_matrix_path: Path | None = None" not in text:
        anchor = '''    consistency_schema_path: Path,
    diversity_report_path: Path | None = None,
) -> dict[str, Any]:
'''
        replacement = '''    consistency_schema_path: Path,
    diversity_report_path: Path | None = None,
    compatibility_matrix_path: Path | None = None,
) -> dict[str, Any]:
'''
        text = replace_once(text, anchor, replacement, "integrate compatibility parameter")

    if "compatibility_matrix, compatibility_matrix_sha" not in text:
        anchor = '''    if actual_recipe_plan["episodeDate"] != date:
        raise CrossArtifactError("episode date mismatch between Final Contract and Recipe Plan")
    paths = _artifact_paths(production_root, date)
'''
        replacement = '''    if actual_recipe_plan["episodeDate"] != date:
        raise CrossArtifactError("episode date mismatch between Final Contract and Recipe Plan")
    compatibility_matrix_path = compatibility_matrix_path or (
        repo_root / "contracts" / "financial_visual_compatibility.json"
    )
    compatibility_matrix, compatibility_matrix_sha = validate_compatibility_matrix(
        compatibility_matrix_path,
        renderer_schema_version,
    )
    paths = _artifact_paths(production_root, date)
'''
        text = replace_once(text, anchor, replacement, "integrate compatibility validation")

    if '"compatibility_matrix_sha256": compatibility_matrix_sha' not in text:
        anchor = '''        "fallback_diversity": diversity_status,
        "unresolved_states": 0,
    }
'''
        replacement = '''        "fallback_diversity": diversity_status,
        "compatibility_matrix_id": compatibility_matrix["matrixId"],
        "compatibility_matrix_sha256": compatibility_matrix_sha,
        "unresolved_states": 0,
    }
'''
        text = replace_once(text, anchor, replacement, "production consistency compatibility binding")

    if '"compatibilityMatrix": {' not in text:
        anchor = '''        "financialRecipePlan": {
            "path": safe_relative(repo_root, recipe_plan_path, "Financial Recipe Plan"),
            "sha256": recipe_plan_sha,
        },
        "episodePackageSha256": final_contract["episodePackage"]["sha256"],
'''
        replacement = '''        "financialRecipePlan": {
            "path": safe_relative(repo_root, recipe_plan_path, "Financial Recipe Plan"),
            "sha256": recipe_plan_sha,
        },
        "compatibilityMatrix": {
            "path": safe_relative(repo_root, compatibility_matrix_path, "Compatibility Matrix"),
            "sha256": compatibility_matrix_sha,
        },
        "episodePackageSha256": final_contract["episodePackage"]["sha256"],
'''
        text = replace_once(text, anchor, replacement, "cross report compatibility file")

    if '"compatibilityMatrix": True' not in text:
        anchor = '''            "comparisonBasis": True,
            "selectedPathFreeze": True,
'''
        replacement = '''            "comparisonBasis": True,
            "compatibilityMatrix": True,
            "selectedPathFreeze": True,
'''
        text = replace_once(text, anchor, replacement, "cross report compatibility check")

    if 'artifacts["financial_visual_compatibility"]' not in text:
        anchor = '''    artifacts["financial_recipe_plan"] = recipe_plan_sha
    artifacts["financial_visual_consistency_report"] = cross_report_sha
'''
        replacement = '''    artifacts["financial_recipe_plan"] = recipe_plan_sha
    artifacts["financial_visual_compatibility"] = compatibility_matrix_sha
    artifacts["financial_visual_consistency_report"] = cross_report_sha
'''
        text = replace_once(text, anchor, replacement, "preflight compatibility artifact")

    if '"compatibility_matrix_id": compatibility_matrix["matrixId"]' not in text[text.index('preflight["financial_visuals"]'):]:
        anchor = '''        "recipe_registry_version": actual_recipe_plan["recipeRegistryVersion"],
        "recipe_plan_sha256": recipe_plan_sha,
'''
        replacement = '''        "recipe_registry_version": actual_recipe_plan["recipeRegistryVersion"],
        "compatibility_matrix_id": compatibility_matrix["matrixId"],
        "compatibility_matrix_sha256": compatibility_matrix_sha,
        "recipe_plan_sha256": recipe_plan_sha,
'''
        text = replace_once(text, anchor, replacement, "preflight compatibility metadata")

    if '"compatibility_matrix": compatibility_matrix_sha' not in text:
        anchor = '''            "financial_visual_consistency_report": cross_report_sha,
            "preflight": sha256_file(paths["preflight"]),
'''
        replacement = '''            "financial_visual_consistency_report": cross_report_sha,
            "compatibility_matrix": compatibility_matrix_sha,
            "preflight": sha256_file(paths["preflight"]),
'''
        text = replace_once(text, anchor, replacement, "result compatibility hash")

    if 'parser.add_argument("--compatibility-matrix"' not in text:
        anchor = '''    parser.add_argument("--consistency-schema", type=Path, default=root / "contracts/financial_visual_consistency_report.schema.json")
    parser.add_argument("--report", type=Path)
'''
        replacement = '''    parser.add_argument("--consistency-schema", type=Path, default=root / "contracts/financial_visual_consistency_report.schema.json")
    parser.add_argument("--compatibility-matrix", type=Path, default=root / "contracts/financial_visual_compatibility.json")
    parser.add_argument("--report", type=Path)
'''
        text = replace_once(text, anchor, replacement, "CLI compatibility argument")

    if "compatibility_matrix_path=args.compatibility_matrix" not in text:
        anchor = '''            consistency_schema_path=args.consistency_schema,
            diversity_report_path=args.diversity_report,
        )
'''
        replacement = '''            consistency_schema_path=args.consistency_schema,
            diversity_report_path=args.diversity_report,
            compatibility_matrix_path=args.compatibility_matrix,
        )
'''
        text = replace_once(text, anchor, replacement, "CLI compatibility handoff")
    return text


def patch_consistency_schema(text: str) -> str:
    if '"compatibilityMatrix"' not in text:
        text = replace_once(
            text,
            '''    "financialRecipePlan", "episodePackageSha256", "renderSpec",
''',
            '''    "financialRecipePlan", "compatibilityMatrix", "episodePackageSha256", "renderSpec",
''',
            "schema compatibility required field",
        )
        text = replace_once(
            text,
            '''    "financialRecipePlan": {"$ref": "#/$defs/fileRef"},
    "episodePackageSha256":''',
            '''    "financialRecipePlan": {"$ref": "#/$defs/fileRef"},
    "compatibilityMatrix": {"$ref": "#/$defs/fileRef"},
    "episodePackageSha256":''',
            "schema compatibility property",
        )
        text = replace_once(
            text,
            '''        "objectIds", "sourceIds", "displayOrder", "comparisonBasis",
        "selectedPathFreeze",''',
            '''        "objectIds", "sourceIds", "displayOrder", "comparisonBasis",
        "compatibilityMatrix", "selectedPathFreeze",''',
            "schema compatibility check required",
        )
        text = replace_once(
            text,
            '''        "comparisonBasis": {"const": true},
        "selectedPathFreeze":''',
            '''        "comparisonBasis": {"const": true},
        "compatibilityMatrix": {"const": true},
        "selectedPathFreeze":''',
            "schema compatibility check property",
        )
    return text


def patch_tests(text: str) -> str:
    if '"financial_visual_compatibility.json"' not in text:
        anchor = '''            "financial_visual_consistency_report.schema.json",
        ):
'''
        replacement = '''            "financial_visual_consistency_report.schema.json",
            "financial_visual_compatibility.json",
        ):
'''
        text = replace_once(text, anchor, replacement, "test compatibility fixture copy")

    if 'self.assertEqual("financial-recipe-plan", beat["templateConfig"]["dataBasis"])' not in text:
        anchor = '''        self.assertEqual("AWS revenue, same quarter and currency", beat["templateConfig"]["comparisonBasis"])
'''
        replacement = anchor + '''        self.assertEqual("financial-recipe-plan", beat["templateConfig"]["dataBasis"])
        self.assertEqual([], beat["templateConfig"]["nodeOrder"])
        self.assertEqual([], beat["templateConfig"]["laneLabels"])
        self.assertIsNone(beat["templateConfig"]["outcomeNodeId"])
'''
        text = replace_once(text, anchor, replacement, "renderer 2.3 config assertions")

    if "test_17_compatibility_matrix_is_sha_bound" not in text:
        anchor = '''    def test_16_diversity_report_is_forbidden_without_fallback(self):
        report = self.repo / "fake-diversity.json"
        report.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(cross.CrossArtifactError, "must be omitted"):
            self.integrate(report)


if __name__ == "__main__":
'''
        addition = '''    def test_16_diversity_report_is_forbidden_without_fallback(self):
        report = self.repo / "fake-diversity.json"
        report.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(cross.CrossArtifactError, "must be omitted"):
            self.integrate(report)

    def test_17_compatibility_matrix_is_sha_bound(self):
        result = self.integrate()
        matrix = self.repo / "contracts" / "financial_visual_compatibility.json"
        self.assertEqual(sha(matrix), result["hashes"]["compatibility_matrix"])
        report = json.loads((self.production / "verification" / self.date / "financial_visual_consistency_report.json").read_text())
        self.assertEqual(sha(matrix), report["compatibilityMatrix"]["sha256"])
        preflight = json.loads((self.production / "verification" / self.date / "official_execution_preflight.json").read_text())
        self.assertEqual("financial-visual-compat-2026-08", preflight["financial_visuals"]["compatibility_matrix_id"])

    def test_18_compatibility_matrix_mismatch_is_rejected(self):
        matrix = self.repo / "contracts" / "financial_visual_compatibility.json"
        value = json.loads(matrix.read_text())
        value["renderer"]["renderSpecVersion"] = "2.4.0"
        write_json(matrix, value)
        with self.assertRaisesRegex(cross.CrossArtifactError, "does not exactly match"):
            self.integrate()


if __name__ == "__main__":
'''
        text = replace_once(text, anchor, addition, "compatibility tests")
    return text


def patched_files() -> dict[Path, str]:
    targets = {
        ROOT / "scripts/financial_visual_cross_artifact.py": patch_cross_artifact,
        ROOT / "contracts/financial_visual_consistency_report.schema.json": patch_consistency_schema,
        ROOT / "tests/financial-visual-cross-artifact/test_financial_visual_cross_artifact.py": patch_tests,
    }
    return {path: patcher(path.read_text(encoding="utf-8")) for path, patcher in targets.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed: list[str] = []
    for path, patched in patched_files().items():
        current = path.read_text(encoding="utf-8")
        if current != patched:
            changed.append(path.relative_to(ROOT).as_posix())
            if not args.check:
                path.write_text(patched, encoding="utf-8")
    if args.check and changed:
        raise SystemExit("FVU-R3 renderer compatibility patch is not applied: " + ", ".join(changed))
    print("patched: " + ", ".join(changed) if changed else "FVU-R3 renderer compatibility patch already applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
