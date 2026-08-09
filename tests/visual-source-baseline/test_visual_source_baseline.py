from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/record_visual_source_baseline.py"

spec = importlib.util.spec_from_file_location("record_visual_source_baseline", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def test_build_baseline_accepts_uncertified_optional_policy(tmp_path: Path) -> None:
    date = "2026-08-06"
    plot_commit = "a" * 40
    renderer_commit = "b" * 40
    render = {
        "schemaVersion": "2.4.0",
        "episode": {"targetDate": date},
    }
    files = {
        f"episodes/{date}/episode_package_{date}.md": "episode\n",
        f"episodes/{date}/spoken_script_{date}.md": "spoken\n",
        f"episodes/{date}/asset_manifest.json": "{}\n",
    }
    for relative, text in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    write_json(tmp_path / f"render-specs/{date}/render_spec.json", render)
    write_json(
        tmp_path / f"verification/{date}/official_execution_preflight.json",
        {
            "status": "pass",
            "unresolved_states": 0,
            "preview_authorized": True,
            "final_authorized": False,
        },
    )
    write_json(
        tmp_path / f"verification/{date}/production_consistency_report.json",
        {"status": "pass", "unresolved_states": 0},
    )
    write_json(
        tmp_path / f"working/{date}/story-engine/story_engine_acceptance.json",
        {
            "production_allowed_by_policy": True,
            "production_policy": "external_critic_optional",
            "critic": {
                "critic_certified": False,
                "external_critic_status": "not_certified",
            },
        },
    )
    bundle = tmp_path / "production-bundles" / date / ("c" * 64)
    write_json(
        bundle / "handoff_manifest.json",
        {
            "bundle_id": "c" * 64,
            "episode_date": date,
            "mode": "preview",
            "plot_creator": {"commit": plot_commit},
            "renderer": {
                "expected_base_commit": renderer_commit,
                "expected_contract_version": "2.4.0",
            },
        },
    )

    baseline = module.build_baseline(
        repo_root=tmp_path,
        episode_date=date,
        plot_commit=plot_commit,
        renderer_commit=renderer_commit,
        renderer_contract_version="2.4.0",
        bundle_root=tmp_path / "production-bundles",
    )
    assert baseline["status"] == "pass"
    assert baseline["story_engine"]["critic_certified"] is False
    assert baseline["story_engine"]["external_critic_status"] == "not_certified"
    assert baseline["validation"]["final_authorized"] is False


def test_build_baseline_rejects_final_authorized_preflight(tmp_path: Path) -> None:
    date = "2026-08-06"
    for relative, text in {
        f"episodes/{date}/episode_package_{date}.md": "episode\n",
        f"episodes/{date}/spoken_script_{date}.md": "spoken\n",
        f"episodes/{date}/asset_manifest.json": "{}\n",
    }.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    write_json(
        tmp_path / f"render-specs/{date}/render_spec.json",
        {"schemaVersion": "2.4.0", "episode": {"targetDate": date}},
    )
    write_json(
        tmp_path / f"verification/{date}/official_execution_preflight.json",
        {
            "status": "pass",
            "unresolved_states": 0,
            "preview_authorized": True,
            "final_authorized": True,
        },
    )
    write_json(
        tmp_path / f"verification/{date}/production_consistency_report.json",
        {"status": "pass", "unresolved_states": 0},
    )
    write_json(
        tmp_path / f"working/{date}/story-engine/story_engine_acceptance.json",
        {
            "production_allowed_by_policy": True,
            "critic": {"critic_certified": False, "external_critic_status": "not_certified"},
        },
    )
    try:
        module.build_baseline(
            repo_root=tmp_path,
            episode_date=date,
            plot_commit="a" * 40,
            renderer_commit="b" * 40,
            renderer_contract_version="2.4.0",
            bundle_root=tmp_path / "production-bundles",
        )
    except module.BaselineError as exc:
        assert "must not be final-authorized" in str(exc)
    else:
        raise AssertionError("final-authorized baseline must fail")
