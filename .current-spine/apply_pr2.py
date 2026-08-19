#!/usr/bin/env python3
"""One-shot deterministic PR-2 migration; removed after successful application."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a = text.find(start)
    if a < 0:
        raise SystemExit(f"{label}: start marker missing")
    b = text.find(end, a)
    if b < 0:
        raise SystemExit(f"{label}: end marker missing")
    if text.find(start, a + 1) >= 0:
        raise SystemExit(f"{label}: start marker not unique")
    return text[:a] + replacement + text[b:]


# Current closure: remove legacy procedure dependency/capture-restore and route the
# authoring pauses to semantic payloads while only canonical artifacts enter evidence.
closure_path = ROOT / "scripts/run_daily_renderer_closure_v12.py"
closure = closure_path.read_text(encoding="utf-8")
closure = replace_once(
    closure,
    "import renderer_binding\nimport run_daily_renderer_closure as legacy\n",
    "import renderer_binding\nimport renderer_contract_sync_v12\n",
    "closure mechanism import",
)
closure = replace_between(
    closure,
    "VISUAL_SOURCE_AUTHORING_FILES = (",
    "def advance(",
    "",
    "capture/restore removal",
)
closure = replace_once(
    closure,
    '''    preserved_visual_source_authoring = _capture_visual_source_authoring(root, date)\n    run(root, "python3", "scripts/materialize_chatgpt_daily_authoring.py", "--date", date, "--repo-root", ".", env=env)\n    _restore_visual_source_authoring(root, date, preserved_visual_source_authoring)\n''',
    '''    run(root, "python3", "scripts/materialize_chatgpt_daily_authoring.py", "--date", date, "--repo-root", ".", env=env)\n''',
    "capture/restore invocation removal",
)
old_requirements = '''    vi = root / "working" / date / "visual-intelligence"\n    requirements = vi / "visual_requirements.json"\n    if not requirements.is_file():\n        raise VisualIntelligenceDecisionRequired(\n            "E_VISUAL_REQUIREMENTS_MISSING: AI-B must author working/<date>/visual-intelligence/visual_requirements.json",\n            required_action="AUTHOR_VISUAL_REQUIREMENTS",\n        )\n    run(root, "python3", "scripts/visual_intelligence_requirements.py", "--requirements", str(requirements.relative_to(root)),\n'''
new_requirements = '''    vi = root / "working" / date / "visual-intelligence"\n    requirements_semantic = vi / "visual_requirements.semantic.json"\n    if not requirements_semantic.is_file():\n        raise VisualIntelligenceDecisionRequired(\n            "E_VISUAL_REQUIREMENTS_MISSING: AI-B must author working/<date>/visual-intelligence/visual_requirements.semantic.json",\n            required_action="AUTHOR_VISUAL_REQUIREMENTS",\n        )\n    run(\n        root,\n        "python3",\n        "scripts/materialize_visual_intelligence_artifact_v12.py",\n        "requirements",\n        "--root",\n        ".",\n        "--date",\n        date,\n        env=env,\n    )\n    requirements = vi / "visual_requirements.json"\n    run(root, "python3", "scripts/visual_intelligence_requirements.py", "--requirements", str(requirements.relative_to(root)),\n'''
closure = replace_once(
    closure,
    old_requirements,
    new_requirements,
    "Requirements semantic materialization",
)
closure = replace_once(
    closure,
    '''        decision = root / "working" / date / "visual-intelligence" / "visual_intelligence_decision.json"\n        if not decision.is_file():\n            raise VisualIntelligenceClosureError(\n                "compile phase requires AI-B visual_intelligence_decision.json"\n            )\n''',
    '''        director_semantic = (\n            root\n            / "working"\n            / date\n            / "visual-intelligence"\n            / "visual_director_decision.semantic.json"\n        )\n        if not director_semantic.is_file():\n            raise VisualIntelligenceClosureError(\n                "compile phase requires AI-B visual_director_decision.semantic.json"\n            )\n''',
    "Director semantic compile gate",
)
closure = replace_once(
    closure,
    "        legacy.sync_renderer_owned_contracts(root, renderer_root)\n",
    "        renderer_contract_sync_v12.sync_renderer_owned_contracts(root, renderer_root)\n",
    "Renderer contract sync mechanism",
)
for forbidden in (
    "run_daily_renderer_closure as legacy",
    "_capture_visual_source_authoring",
    "_restore_visual_source_authoring",
    "visual_intelligence_decision.json",
):
    if forbidden in closure:
        raise SystemExit(f"current closure legacy/multi-writer residue: {forbidden}")
closure_path.write_text(closure, encoding="utf-8")

# Daily Authoring owns the initial Visual Source projection only. Once canonical
# Requirements exist, the semantic checkpoint is sealed and reruns must not overwrite it.
materializer_path = ROOT / "scripts/materialize_chatgpt_daily_authoring.py"
materializer = materializer_path.read_text(encoding="utf-8")
old_sources = '''    dump(work / "financial_visual_bindings.json", {"contractVersion":"1.0.0","episodeDate":date,"bindings":projected.get("financialBindings",[])})\n    dump(work / "visual_source_intents.json", {"contractVersion":"1.0.0","episodeDate":date,"intents":projected.get("visualSourceIntents",[])})\n    if projected.get("visualSourceSelection") is not None:\n        dump(work / "visual_source_selection.json", projected["visualSourceSelection"])\n    dump(story / "story_production_bindings.json", {\n'''
new_sources = '''    dump(work / "financial_visual_bindings.json", {"contractVersion":"1.0.0","episodeDate":date,"bindings":projected.get("financialBindings",[])})\n    requirements_sealed = work / "visual-intelligence" / "visual_requirements.json"\n    visual_source_intents = work / "visual_source_intents.json"\n    if not requirements_sealed.is_file():\n        dump(visual_source_intents, {"contractVersion":"1.0.0","episodeDate":date,"intents":projected.get("visualSourceIntents",[])})\n        if projected.get("visualSourceSelection") is not None:\n            dump(work / "visual_source_selection.json", projected["visualSourceSelection"])\n    elif not visual_source_intents.is_file():\n        raise SystemExit(\n            "sealed Visual Requirements require the existing ChatGPT Visual Source checkpoint"\n        )\n    dump(story / "story_production_bindings.json", {\n'''
materializer = replace_once(
    materializer,
    old_sources,
    new_sources,
    "Visual Source single-writer boundary",
)
materializer_path.write_text(materializer, encoding="utf-8")

# Semantic Freeze wrapper no longer asks LLM artifacts to hand-copy the Freeze SHA.
# Current request + Snapshot/Requirements lineage owns that machine identity.
frozen_path = ROOT / "scripts/run_semantic_frozen_renderer_closure_v12.py"
frozen = frozen_path.read_text(encoding="utf-8")
frozen = replace_between(
    frozen,
    "def semantic_binding_pause(",
    "def verify_freeze(",
    '''def semantic_binding_pause(\n    root: Path,\n    date: str,\n    *,\n    phase: str,\n    semantic_freeze_sha256: str,\n) -> tuple[str, str] | None:\n    """Current VI semantic payloads never hand-author machine Freeze SHA values.\n\n    The immutable current request binds the verified Semantic Freeze, and the\n    canonical Requirements bind the Editorial Snapshot. Direct read-set invalidation\n    is enforced at those machine boundaries rather than duplicated in LLM payloads.\n    """\n    del root, date, phase, semantic_freeze_sha256\n    return None\n\n\n''',
    "Semantic Freeze duplicate binding removal",
)
frozen_path.write_text(frozen, encoding="utf-8")

# Update executable characterization: PR-2 resolves the closure legacy import,
# capture/restore workaround, and combined Director/Critic authority.
character_path = ROOT / "tests/current-spine/test_current_spine_characterization.py"
character = character_path.read_text(encoding="utf-8")
old_debt = '''    # PR-2 targets these remaining multi-writer/legacy closure collisions.\n    require(\n        closure,\n        "import run_daily_renderer_closure as legacy",\n        "current closure -> legacy procedure dependency",\n    )\n    require(closure, "def _capture_visual_source_authoring", "capture workaround")\n    require(closure, "def _restore_visual_source_authoring", "restore workaround")\n    require(\n        closure,\n        '\"visual_intelligence_decision.json\"',\n        "combined Director/Critic decision artifact",\n    )\n\n'''
new_debt = '''    # PR-2 resolves the multi-writer/combined VI authority collisions.\n    forbid(\n        closure,\n        "import run_daily_renderer_closure as legacy",\n        "current closure -> legacy procedure dependency",\n    )\n    forbid(closure, "def _capture_visual_source_authoring", "capture workaround")\n    forbid(closure, "def _restore_visual_source_authoring", "restore workaround")\n    forbid(closure, "visual_intelligence_decision.json", "combined Director/Critic authority")\n    require(\n        closure,\n        "visual_director_decision.semantic.json",\n        "Director semantic payload boundary",\n    )\n    require(\n        closure,\n        "materialize_visual_intelligence_artifact_v12.py",\n        "Requirements machine materializer",\n    )\n    require(\n        closure,\n        "renderer_contract_sync_v12.sync_renderer_owned_contracts",\n        "Renderer contract sync mechanism",\n    )\n\n'''
character = replace_once(character, old_debt, new_debt, "PR-2 characterization")
character_path.write_text(character, encoding="utf-8")

print("PR-2 deterministic migration applied")
