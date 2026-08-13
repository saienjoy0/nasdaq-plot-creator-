from __future__ import annotations

import json
from pathlib import Path

import build_renderer_handoff_240 as handoff
import pytest

DATE = "2099-01-02"
COMMIT = "a" * 40


def write_json(root: Path, relative: str, value: dict) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def fixture(root: Path) -> None:
    write_json(
        root,
        f"working/{DATE}/production_request.json",
        {
            "renderer": {"commit": COMMIT, "contract_version": "2.4.0"},
            "visual_director": {"required": True, "contract_version": "1.0.0"},
        },
    )
    for template in handoff.EXTRA_ROLES.values():
        write_json(root, template.format(date=DATE), {})
    for template in handoff.VISUAL_INTELLIGENCE_ROLES.values():
        write_json(root, template.format(date=DATE), {})

    package_path = write_json(
        root,
        f"working/{DATE}/visual-intelligence/visual_intelligence_package.json",
        {"bridgeContractVersion": "visual-intelligence-bridge/1.2.0"},
    )
    direction_path = write_json(
        root,
        f"working/{DATE}/visual-intelligence/visual_direction_compile_report.json",
        {"semanticDiff": "PASS"},
    )
    render_path = write_json(
        root,
        f"render-specs/{DATE}/render_spec.json",
        {"schemaVersion": "2.4.0", "episode": {"targetDate": DATE}},
    )
    renderer_report = write_json(
        root,
        f"verification/{DATE}/renderer_validation_report.json",
        {
            "status": "PASS",
            "renderer": {"commit": COMMIT, "contractVersion": "2.4.0"},
            "renderSpec": {"sha256": handoff.sha256_file(render_path)},
            "unresolvedStateCount": 0,
        },
    )
    write_json(
        root,
        f"verification/{DATE}/visual_intelligence_validation.json",
        {
            "status": "PASS",
            "episodeDate": DATE,
            "rendererCommit": COMMIT,
            "packageSha256": handoff.sha256_file(package_path),
        },
    )
    write_json(
        root,
        f"verification/{DATE}/official_execution_preflight.json",
        {
            "renderer_validation": {
                "status": "pass",
                "report_sha256": handoff.sha256_file(renderer_report),
            },
            "artifacts": {
                "visual_direction_compile_report": handoff.sha256_file(direction_path)
            },
        },
    )


def test_visual_intelligence_evidence_enters_handoff(tmp_path: Path) -> None:
    fixture(tmp_path)
    extras = handoff._validate_renderer_evidence(
        source_root=tmp_path,
        date=DATE,
        renderer_commit=COMMIT,
        renderer_contract_version="2.4.0",
    )
    assert set(handoff.VISUAL_INTELLIGENCE_ROLES).issubset(extras)
    assert extras["visual_intelligence_package"].is_file()
    assert extras["visual_intelligence_validation"].is_file()


def test_visual_direction_semantic_failure_blocks_handoff(tmp_path: Path) -> None:
    fixture(tmp_path)
    write_json(
        tmp_path,
        f"working/{DATE}/visual-intelligence/visual_direction_compile_report.json",
        {"semanticDiff": "FAIL"},
    )
    with pytest.raises(handoff.RendererHandoff240Error, match="Semantic Diff"):
        handoff._validate_renderer_evidence(
            source_root=tmp_path,
            date=DATE,
            renderer_commit=COMMIT,
            renderer_contract_version="2.4.0",
        )


def test_visual_intelligence_package_sha_mismatch_blocks_handoff(tmp_path: Path) -> None:
    fixture(tmp_path)
    write_json(
        tmp_path,
        f"verification/{DATE}/visual_intelligence_validation.json",
        {
            "status": "PASS",
            "episodeDate": DATE,
            "rendererCommit": COMMIT,
            "packageSha256": "b" * 64,
        },
    )
    with pytest.raises(handoff.RendererHandoff240Error, match="package SHA mismatch"):
        handoff._validate_renderer_evidence(
            source_root=tmp_path,
            date=DATE,
            renderer_commit=COMMIT,
            renderer_contract_version="2.4.0",
        )
