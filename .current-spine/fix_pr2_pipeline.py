#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "scripts/visual_intelligence_pipeline_v12.py"
text = path.read_text(encoding="utf-8")


def one(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, found {count}")
    text = text.replace(old, new, 1)

one(
    '    catalog_sha = base.sha256_file(catalog_path)\n\n    director_semantic = vi_dir / artifacts.DIRECTOR_SEMANTIC\n',
    '    catalog_sha = base.sha256_file(catalog_path)\n    catalog_content_sha = base.canonical_sha(catalog)\n\n    director_semantic = vi_dir / artifacts.DIRECTOR_SEMANTIC\n',
    "catalog dual identity",
)
one(
    '''                "directorDecisionSha256": base.sha256_file(director_path),\n                "candidateCatalogSha256": catalog_sha,\n                "selections": [\n''',
    '''                "candidateCatalogSha256": catalog_content_sha,\n                "selections": [\n''',
    "strict Renderer plan shape",
)
one(
    '''        if plan_value.get("directorDecisionSha256") != base.sha256_file(director_path):\n            raise VisualIntelligenceStageError("E_VISUAL_COMPILE_STALE: Director Decision SHA mismatch")\n        if plan_value.get("candidateCatalogSha256") != catalog_sha:\n            raise VisualIntelligenceStageError("E_VISUAL_COMPILE_STALE: Candidate Catalog SHA mismatch")\n''',
    '''        if plan_value.get("candidateCatalogSha256") != catalog_content_sha:\n            raise VisualIntelligenceStageError("E_VISUAL_COMPILE_STALE: Candidate Catalog content SHA mismatch")\n''',
    "compiled plan reuse validation",
)
path.write_text(text, encoding="utf-8")
print("PR-2 Renderer strict plan compatibility repaired")
