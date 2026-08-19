#!/usr/bin/env python3
"""One-shot deterministic PR-5 migration; removed after successful application."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_between(path: Path, start: str, end: str, replacement: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    a = text.find(start)
    b = text.find(end, a if a >= 0 else 0)
    if a < 0 or b < 0 or text.find(start, a + 1) >= 0:
        raise SystemExit(f"{label}: marker drift")
    path.write_text(text[:a] + replacement + text[b:], encoding="utf-8")

# 1) Current v2 Creative Review -> legacy-shaped boolean lives in one adapter.
materializer = root / "scripts/materialize_chatgpt_daily_authoring.py"
replace_once(
    materializer,
    "import visual_source_checkpoint_v12\n",
    "import visual_source_checkpoint_v12\nimport current_compatibility_adapter_v12\n",
    "compatibility adapter import",
)
replace_between(
    materializer,
    "    derived_review = {\n",
    "    a = dict(production)\n",
    "    derived_review = current_compatibility_adapter_v12.project_creative_review(review)\n",
    "Creative Review compatibility projection",
)

# 2) Persist the already-built production_annex as the current machine authority
# before embedding the same semantic object into the human Markdown projection.
daily = root / "scripts/materialize_daily_episode.py"
needle = '''    production_annex = {\n        "contract_version": "1.0.0",\n        "episode_date": date,\n        "post_inquisition": {\n            "status": "pass",\n            "required_changes_applied": True,\n            "unresolved_required_changes": 0,\n        },\n        "image_resolution": image_resolution,\n        "renderer_contract": {"repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion", "schema_version": render["schemaVersion"]},\n        "asset_catalog": asset_catalog,\n        "render_spec": render,\n    }\n    public = normalize_scene_headings(contract_package.read_text(encoding="utf-8").rstrip())\n'''
replacement = '''    production_annex = {\n        "contract_version": "1.0.0",\n        "episode_date": date,\n        "post_inquisition": {\n            "status": "pass",\n            "required_changes_applied": True,\n            "unresolved_required_changes": 0,\n        },\n        "image_resolution": image_resolution,\n        "renderer_contract": {"repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion", "schema_version": render["schemaVersion"]},\n        "asset_catalog": asset_catalog,\n        "render_spec": render,\n    }\n    structured_source = work / "current_final_production_source.json"\n    structured_source.write_text(dump(production_annex) + "\\n", encoding="utf-8")\n    public = normalize_scene_headings(contract_package.read_text(encoding="utf-8").rstrip())\n'''
replace_once(daily, needle, replacement, "structured production source persistence")

# 3) Current final authority consumes separated Director/Critic canonical artifacts.
v12 = root / "scripts/build_final_production_package_v12.py"
replace_once(
    v12,
    "import build_final_production_package_hardened as hardened\nimport renderer_binding\n",
    "import build_final_production_package_hardened as hardened\nimport build_final_production_package_structured_v12 as structured_builder\nimport renderer_binding\n",
    "structured builder import",
)
replace_once(
    v12,
    '''    package_path = vi_dir / "visual_intelligence_package.json"\n    decision_path = vi_dir / "visual_intelligence_decision.json"\n    validation_path = verification / "visual_intelligence_validation.json"\n\n    for path, label in (\n        (compiled_path, "Critic-approved compiled visual"),\n        (warning_path, "Visual warning report"),\n        (package_path, "Visual Intelligence package"),\n        (decision_path, "Visual Intelligence decision"),\n        (validation_path, "Visual Intelligence validation"),\n    ):\n''',
    '''    package_path = vi_dir / "visual_intelligence_package.json"\n    director_path = vi_dir / "visual_director_decision.json"\n    critic_path = vi_dir / "visual_critic_review.json"\n    validation_path = verification / "visual_intelligence_validation.json"\n\n    for path, label in (\n        (compiled_path, "Critic-approved compiled visual"),\n        (warning_path, "Visual warning report"),\n        (package_path, "Visual Intelligence package"),\n        (director_path, "Visual Director Decision"),\n        (critic_path, "Visual Critic Review"),\n        (validation_path, "Visual Intelligence validation"),\n    ):\n''',
    "separated authority paths",
)
replace_once(
    v12,
    '''    compiled = _load_json_object(compiled_path, "Critic-approved compiled visual")\n    package = _load_json_object(package_path, "Visual Intelligence package")\n    decision = _load_json_object(decision_path, "Visual Intelligence decision")\n    validation = _load_json_object(validation_path, "Visual Intelligence validation")\n\n    compiled_sha = _sha256_file(compiled_path)\n    warning_sha = _sha256_file(warning_path)\n    package_sha = _sha256_file(package_path)\n    final = package.get("final")\n    rounds = decision.get("reviewRounds")\n    last_round = rounds[-1] if isinstance(rounds, list) and rounds else None\n''',
    '''    compiled = _load_json_object(compiled_path, "Critic-approved compiled visual")\n    package = _load_json_object(package_path, "Visual Intelligence package")\n    director = _load_json_object(director_path, "Visual Director Decision")\n    critic = _load_json_object(critic_path, "Visual Critic Review")\n    validation = _load_json_object(validation_path, "Visual Intelligence validation")\n\n    compiled_sha = _sha256_file(compiled_path)\n    warning_sha = _sha256_file(warning_path)\n    package_sha = _sha256_file(package_path)\n    director_sha = _sha256_file(director_path)\n    critic_sha = _sha256_file(critic_path)\n    final = package.get("final")\n    rounds = critic.get("reviewRounds")\n    last_round = rounds[-1] if isinstance(rounds, list) and rounds else None\n''',
    "separated authority loading",
)
old_critic_check = '''    if (\n        not isinstance(last_round, dict)\n        or last_round.get("status") != "PASS"\n        or last_round.get("compiledVisualSha256") != compiled_sha\n        or last_round.get("warningReportSha256") != warning_sha\n    ):\n        raise VisualIntelligenceFinalBuildError(\n            "E_VISUAL_INTELLIGENCE_POST_PASS_AUTHORITY_STALE: Critic PASS lineage mismatch"\n        )\n'''
new_critic_check = '''    inputs = package.get("inputs")\n    if not isinstance(inputs, dict):\n        raise VisualIntelligenceFinalBuildError(\n            "E_VISUAL_INTELLIGENCE_POST_PASS_AUTHORITY_INVALID: package inputs missing"\n        )\n    if (\n        validation.get("visualDirectorDecisionSha256") != director_sha\n        or inputs.get("visualDirectorDecisionSha256") != director_sha\n        or validation.get("visualCriticReviewSha256") != critic_sha\n        or final.get("criticReviewSha256") != critic_sha\n        or critic.get("directorDecisionSha256") != director_sha\n        or critic.get("compiledVisualSha256") != compiled_sha\n        or critic.get("warningReportSha256") != warning_sha\n        or not isinstance(last_round, dict)\n        or last_round.get("status") != "PASS"\n    ):\n        raise VisualIntelligenceFinalBuildError(\n            "E_VISUAL_INTELLIGENCE_POST_PASS_AUTHORITY_STALE: separated Director/Critic lineage mismatch"\n        )\n'''
replace_once(v12, old_critic_check, new_critic_check, "separated Critic lineage validation")
replace_once(
    v12,
    '''        "packagePath": package_path,\n        "packageSha256": package_sha,\n        "catalogPath": vi_dir / "visual_candidate_catalog.json",\n''',
    '''        "packagePath": package_path,\n        "packageSha256": package_sha,\n        "directorPath": director_path,\n        "directorSha256": director_sha,\n        "criticPath": critic_path,\n        "criticSha256": critic_sha,\n        "catalogPath": vi_dir / "visual_candidate_catalog.json",\n''',
    "separated authority return paths",
)
replace_once(
    v12,
    '''    result = hardened.build_hardened(\n        package,\n        output_root,\n        schema,\n        repo_root=repo_root,\n        renderer_finalizer=_renderer_finalizer_v12,\n    )\n''',
    '''    result = hardened.build_hardened(\n        package,\n        output_root,\n        schema,\n        repo_root=repo_root,\n        builder=structured_builder.build,\n        renderer_finalizer=_renderer_finalizer_v12,\n    )\n''',
    "current structured builder injection",
)
if "visual_intelligence_decision.json" in v12:
    raise SystemExit("combined Visual Intelligence decision authority remains in current final builder")

print("PR-5 structured authority migration applied")
