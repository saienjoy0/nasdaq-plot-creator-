from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import current_production_facade_v12 as facade
import current_production_resume_v12 as resume
import run_daily_production_v12 as production
import run_daily_renderer_closure_v12 as closure


def valid_status(state: str) -> dict:
    return {
        "current_state": state,
        "validation": {"status": "pass", "errors": []},
    }


def test_completed_transition_is_skipped_from_validated_entry_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple] = []
    monkeypatch.setattr(closure, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    closure.advance(
        tmp_path,
        date="2026-08-17",
        state="research_inputs_bound",
        evidence=["research/2026-08-17/research_input_manifest.json"],
        env={},
        completed_state="handoff_ready",
    )

    assert calls == []


def test_build_production_revalidates_existing_later_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    episode_package = tmp_path / "episode.md"
    episode_package.write_text("episode\n", encoding="utf-8")
    built_output = tmp_path / "render_spec.json"
    built_output.write_text("{}\n", encoding="utf-8")

    class DailyProductionError(RuntimeError):
        def __init__(self, _code: str, message: str):
            super().__init__(message)

    module = SimpleNamespace(
        ERROR_CODES={"package": "E_PACKAGE"},
        DailyProductionError=DailyProductionError,
        safe_path=lambda _workspace, path, _label: path,
    )

    monkeypatch.setattr(
        production,
        "_request",
        lambda *_args, **_kwargs: {"visual_intelligence": {"required": True}},
    )
    monkeypatch.setattr(production, "status", lambda **_kwargs: valid_status("handoff_ready"))
    monkeypatch.setattr(
        production.final_v12,
        "build_hardened_v12",
        lambda *_args, **_kwargs: {"paths": {"render_spec": str(built_output)}},
    )
    transitions: list[dict] = []
    monkeypatch.setattr(production, "add_transition", lambda **kwargs: transitions.append(kwargs))

    result = production.build_production(
        module=module,
        workspace=tmp_path,
        date="2026-08-17",
        episode_package=episode_package,
    )

    assert result["paths"]["render_spec"] == str(built_output)
    assert transitions == []


def test_invalid_completed_state_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        resume,
        "production_status",
        lambda _root, _date: {
            "current_state": "handoff_ready",
            "validation": {"status": "fail", "errors": ["evidence SHA changed"]},
        },
    )

    with pytest.raises(resume.CurrentProductionResumeError, match="evidence SHA changed"):
        resume.has_reached(tmp_path, "2026-08-17", "research_inputs_bound")


def test_facade_reuses_valid_existing_handoff(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    renderer_root = tmp_path / "renderer"
    renderer_root.mkdir()
    freeze = tmp_path / "freeze.json"
    freeze.write_text("{}\n", encoding="utf-8")
    gate = tmp_path / "verification" / "2026-08-17" / "renderer_closure_gate_v12.json"
    gate.parent.mkdir(parents=True)
    gate.write_text('{"status":"PASS","rendererCommit":"renderer-sha"}\n', encoding="utf-8")

    monkeypatch.setattr(facade.renderer_binding, "verify_renderer_checkout", lambda *_args: None)
    monkeypatch.setattr(resume, "production_status", lambda _root, _date: valid_status("handoff_ready"))
    commands: list[list[str]] = []

    def runner(command: list[str], **_kwargs) -> subprocess.CompletedProcess:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    outcome = facade.run_closure(
        root=tmp_path,
        renderer_root=renderer_root,
        date="2026-08-17",
        phase="compile",
        semantic_freeze=freeze,
        build_handoff_on_pass=True,
        bundle_root=tmp_path / "bundles",
        plot_commit="plot-sha",
        runner=runner,
    )

    assert outcome["status"] == "PASS"
    assert outcome["previewHandoffReady"] is True
    assert len(commands) == 1
    assert "scripts/run_semantic_frozen_renderer_closure_v12.py" in commands[0]


def test_official_renderer_validator_avoids_npm_environment_noise() -> None:
    source = (ROOT / "scripts" / "finalize_renderer_package.py").read_text(encoding="utf-8")
    assert '"node", "--import", "tsx", "scripts/spec-cli.ts"' in source
    assert '"npx", "--no-install", "tsx", "scripts/spec-cli.ts"' not in source
