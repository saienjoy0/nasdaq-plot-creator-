from __future__ import annotations

import json
from pathlib import Path

import build_renderer_handoff_240 as handoff
import pytest

DATE = "2026-08-06"
COMMIT = "a" * 40
COMPILED = "c" * 64


def write_json(root: Path, relative: str, value: dict) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def fixture(root: Path, *, visual_intelligence: bool = False) -> None:
    request = {
        "renderer": {"commit": COMMIT, "contract_version": "2.4.0"},
        "visual_director": {"required": True, "contract_version": "1.0.0"},
    }
    if visual_intelligence:
        request["visual_intelligence"] = {
            "required": True,
            "bridge_contract_version": "visual-intelligence-bridge/1.2.0",
            "frozen_interface_sha256": "b" * 64,
        }
    write_json(root, f"working/{DATE}/production_request.json", request)
    for template in handoff.EXTRA_ROLES.values():
        write_json(root, template.format(date=DATE), {})

    roles = (
        handoff.VISUAL_INTELLIGENCE_ROLES
        if visual_intelligence
        else handoff.VISUAL_DIRECTOR_ROLES
    )
    write_json(root, roles["visual_candidate_catalog"].format(date=DATE), {"catalog": True})
    write_json(root, roles["visual_direction_plan"].format(date=DATE), {"plan": True})
    direction_path = write_json(
        root,
        roles["visual_direction_compile_report"].format(date=DATE),
        {"semanticDiff": "PASS"},
    )
    render_path = write_json(
        root,
        f"render-specs/{DATE}/render_spec.json",
        {"schemaVersion": "2.4.0", "episode": {"targetDate": DATE}},
    )

    vi_preflight = None
    if visual_intelligence:
        package_path = write_json(
            root,
            roles["visual_intelligence_package"].format(date=DATE),
            {
                "contractVersion": "1.0.0",
                "bridgeContractVersion": "visual-intelligence-bridge/1.2.0",
                "episodeDate": DATE,
                "inputs": {"rendererCommit": COMMIT},
                "final": {"status": "PASS", "compiledVisualSha256": COMPILED},
            },
        )
        integrity_path = write_json(
            root,
            roles["visual_intelligence_post_pass_integrity"].format(date=DATE),
            {
                "contractVersion": "1.0.0",
                "bridgeContractVersion": "visual-intelligence-bridge/1.2.0",
                "episodeDate": DATE,
                "status": "PASS",
                "approvedCompiledVisualSha256": COMPILED,
                "finalRenderSpecSha256": handoff.sha256_file(render_path),
                "secondDirectorInvoked": False,
                "visualAuthorityPreserved": True,
            },
        )
        write_json(
            root,
            roles["visual_intelligence_validation"].format(date=DATE),
            {
                "status": "PASS",
                "episodeDate": DATE,
                "packageSha256": handoff.sha256_file(package_path),
                "compiledVisualSha256": COMPILED,
            },
        )
        vi_preflight = {
            "status": "PASS",
            "packageSha256": handoff.sha256_file(package_path),
            "compiledVisualSha256": COMPILED,
            "postPassIntegritySha256": handoff.sha256_file(integrity_path),
            "rendererCommit": COMMIT,
        }

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
    preflight = {
        "renderer_validation": {
            "status": "pass",
            "report_sha256": handoff.sha256_file(renderer_report),
        },
        "artifacts": {},
    }
    if visual_intelligence:
        preflight["visual_intelligence"] = vi_preflight
    else:
        preflight["artifacts"]["visual_direction_compile_report"] = handoff.sha256_file(
            direction_path
        )
    write_json(root, f"verification/{DATE}/official_execution_preflight.json", preflight)


def test_visual_direction_evidence_enters_handoff(tmp_path: Path) -> None:
    fixture(tmp_path)
    extras = handoff._validate_renderer_evidence(
        source_root=tmp_path,
        date=DATE,
        renderer_commit=COMMIT,
        renderer_contract_version="2.4.0",
    )
    assert set(handoff.VISUAL_DIRECTOR_ROLES).issubset(extras)


def test_visual_intelligence_uses_v12_canonical_paths_and_lineage(tmp_path: Path) -> None:
    fixture(tmp_path, visual_intelligence=True)
    extras = handoff._validate_renderer_evidence(
        source_root=tmp_path,
        date=DATE,
        renderer_commit=COMMIT,
        renderer_contract_version="2.4.0",
    )
    assert set(handoff.VISUAL_INTELLIGENCE_ROLES).issubset(extras)
    assert extras["visual_candidate_catalog"] == (
        tmp_path / f"working/{DATE}/visual-intelligence/visual_candidate_catalog.json"
    ).resolve()
    assert extras["visual_direction_compile_report"] == (
        tmp_path / f"working/{DATE}/visual-intelligence/visual_direction_compile_report.json"
    ).resolve()


def test_visual_intelligence_stale_preflight_blocks_handoff(tmp_path: Path) -> None:
    fixture(tmp_path, visual_intelligence=True)
    preflight_path = tmp_path / f"verification/{DATE}/official_execution_preflight.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["visual_intelligence"]["compiledVisualSha256"] = "d" * 64
    write_json(root=tmp_path, relative=f"verification/{DATE}/official_execution_preflight.json", value=preflight)
    with pytest.raises(handoff.RendererHandoff240Error, match="preflight compiled visual SHA mismatch"):
        handoff._validate_renderer_evidence(
            source_root=tmp_path,
            date=DATE,
            renderer_commit=COMMIT,
            renderer_contract_version="2.4.0",
        )


def test_visual_direction_semantic_failure_blocks_handoff(tmp_path: Path) -> None:
    fixture(tmp_path)
    write_json(
        tmp_path,
        f"verification/{DATE}/visual_direction_compile_report.json",
        {"semanticDiff": "FAIL"},
    )
    with pytest.raises(handoff.RendererHandoff240Error, match="Semantic Diff"):
        handoff._validate_renderer_evidence(
            source_root=tmp_path,
            date=DATE,
            renderer_commit=COMMIT,
            renderer_contract_version="2.4.0",
        )
