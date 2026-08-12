from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import visual_director_bridge as bridge

DATE = "2026-08-06"
COMMIT = "a" * 40


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def argument(arguments: list[str], name: str) -> Path:
    return Path(arguments[arguments.index(name) + 1])


def fake_runner(renderer_root: Path, command: str, arguments: list[str]) -> None:
    del renderer_root
    spec_path = argument(arguments, "--spec")
    if command == "build":
        assert argument(arguments, "--hints").is_file()
        write_json(
            argument(arguments, "--catalog"),
            {
                "contractVersion": "1.0.0",
                "episodeDate": DATE,
                "sourceRenderSpecSha256": hashlib.sha256(
                    spec_path.read_bytes()
                ).hexdigest(),
                "candidates": [{"candidateId": "vc-one"}],
            },
        )
        return
    assert command == "compile"
    compiled = json.loads(spec_path.read_text(encoding="utf-8"))
    write_json(argument(arguments, "--output"), compiled)
    write_json(
        argument(arguments, "--report"),
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "sourceRenderSpecSha256": hashlib.sha256(
                spec_path.read_bytes()
            ).hexdigest(),
            "semanticDiff": "PASS",
            "warnings": [],
        },
    )


def render() -> dict:
    return {
        "schemaVersion": "2.4.0",
        "episode": {"targetDate": DATE},
        "scenes": [],
    }


def render_with_split_comparison() -> dict:
    return {
        "schemaVersion": "2.4.0",
        "episode": {"targetDate": DATE},
        "scenes": [
            {
                "visualBeats": [
                    {
                        "beatId": "vb-02-02",
                        "visualTemplate": "split-comparison",
                    }
                ]
            }
        ],
    }


def test_missing_hints_materializes_authored_only_policy(tmp_path: Path) -> None:
    hints_path = tmp_path / f"working/{DATE}/visual_capability_hints.json"
    hints = bridge._ensure_template_policy_hints(
        render=render_with_split_comparison(),
        hints_path=hints_path,
        date=DATE,
    )
    assert hints == {
        "contractVersion": "1.1.0",
        "episodeDate": DATE,
        "beats": [
            {
                "visualBeatId": "vb-02-02",
                "capabilities": ["comparison-set"],
                "templatePolicy": {"mode": "authored-only"},
            }
        ],
    }
    assert json.loads(hints_path.read_text(encoding="utf-8")) == hints


def test_explicit_allow_list_is_preserved(tmp_path: Path) -> None:
    hints_path = tmp_path / f"working/{DATE}/visual_capability_hints.json"
    explicit = {
        "contractVersion": "1.1.0",
        "episodeDate": DATE,
        "beats": [
            {
                "visualBeatId": "vb-02-02",
                "capabilities": ["comparison-set"],
                "templatePolicy": {
                    "mode": "allow-list",
                    "allowedTemplateIds": ["split-comparison"],
                },
            }
        ],
    }
    write_json(hints_path, explicit)
    observed = bridge._ensure_template_policy_hints(
        render=render_with_split_comparison(),
        hints_path=hints_path,
        date=DATE,
    )
    assert observed == explicit
    assert json.loads(hints_path.read_text(encoding="utf-8")) == explicit


def test_legacy_or_partial_hints_fail_closed(tmp_path: Path) -> None:
    hints_path = tmp_path / f"working/{DATE}/visual_capability_hints.json"
    write_json(
        hints_path,
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "beats": [],
        },
    )
    with pytest.raises(bridge.VisualDirectorBridgeError, match="1.1.0"):
        bridge._ensure_template_policy_hints(
            render=render_with_split_comparison(),
            hints_path=hints_path,
            date=DATE,
        )

    write_json(
        hints_path,
        {
            "contractVersion": "1.1.0",
            "episodeDate": DATE,
            "beats": [],
        },
    )
    with pytest.raises(bridge.VisualDirectorBridgeError, match="cover every Beat"):
        bridge._ensure_template_policy_hints(
            render=render_with_split_comparison(),
            hints_path=hints_path,
            date=DATE,
        )


def test_catalog_is_persisted_and_missing_plan_pauses(tmp_path: Path) -> None:
    with pytest.raises(bridge.VisualDirectorBridgeError, match="PLAN_REQUIRED"):
        bridge.prepare_and_compile(
            render=render(),
            output_root=tmp_path,
            date=DATE,
            renderer_root=tmp_path / "renderer",
            expected_renderer_commit=COMMIT,
            runner=fake_runner,
            renderer_head=lambda _: COMMIT,
        )
    assert (tmp_path / f"working/{DATE}/visual_candidate_catalog.json").is_file()
    hints = json.loads(
        (tmp_path / f"working/{DATE}/visual_capability_hints.json").read_text(
            encoding="utf-8"
        )
    )
    assert hints["contractVersion"] == "1.1.0"


def test_candidate_id_plan_compiles_before_freeze(tmp_path: Path) -> None:
    write_json(
        tmp_path / f"working/{DATE}/visual_direction_plan.json",
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "candidateCatalogSha256": "b" * 64,
            "selections": [{"visualBeatId": "beat-one", "candidateId": "vc-one"}],
        },
    )
    result = bridge.prepare_and_compile(
        render=render(),
        output_root=tmp_path,
        date=DATE,
        renderer_root=tmp_path / "renderer",
        expected_renderer_commit=COMMIT,
        runner=fake_runner,
        renderer_head=lambda _: COMMIT,
    )
    assert result["render"] == render()
    assert result["warnings"] == []
    assert result["report_path"].is_file()
    assert result["hints_path"].is_file()


def test_renderer_commit_binding_is_enforced(tmp_path: Path) -> None:
    with pytest.raises(bridge.VisualDirectorBridgeError, match="SHA mismatch"):
        bridge.prepare_and_compile(
            render=render(),
            output_root=tmp_path,
            date=DATE,
            renderer_root=tmp_path / "renderer",
            expected_renderer_commit=COMMIT,
            runner=fake_runner,
            renderer_head=lambda _: "b" * 40,
        )
