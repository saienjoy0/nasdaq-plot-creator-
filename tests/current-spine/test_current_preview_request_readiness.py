import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import current_preview_request_readiness_v12 as readiness


def make_preview_request(root: Path, date: str = "2026-08-17") -> Path:
    freeze = root / "semantic-freezes" / f"{date}.json"
    freeze.parent.mkdir(parents=True, exist_ok=True)
    freeze.write_text('{"contractVersion":"1.2.0"}\n', encoding="utf-8")
    request = root / "daily-production-requests" / f"{date}-preview.json"
    request.parent.mkdir(parents=True, exist_ok=True)
    request.write_text(
        json.dumps(
            {
                "episodeDate": date,
                "confirmation": "PREVIEW",
                "semanticFreeze": {
                    "path": f"semantic-freezes/{date}.json",
                    "sha256": hashlib.sha256(freeze.read_bytes()).hexdigest(),
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return request


def test_choose_prepare_when_director_semantic_missing(tmp_path: Path):
    vi = tmp_path / "working/2026-08-17/visual-intelligence"
    vi.mkdir(parents=True)
    assert readiness.choose_phase(tmp_path, "2026-08-17") == "prepare"


def test_choose_compile_when_director_semantic_exists(tmp_path: Path):
    vi = tmp_path / "working/2026-08-17/visual-intelligence"
    vi.mkdir(parents=True)
    (vi / "visual_director_decision.semantic.json").write_text("{}\n", encoding="utf-8")
    assert readiness.choose_phase(tmp_path, "2026-08-17") == "compile"


def test_prepared_is_not_ready_and_preserves_required_action():
    state, action = readiness.classify_facade_outcome({
        "status": "PREPARED",
        "requiredAction": "AUTHOR_VISUAL_INTELLIGENCE_DECISION",
    })
    assert state == "NOT_READY"
    assert action == "AUTHOR_VISUAL_INTELLIGENCE_DECISION"


def test_review_required_maps_to_critic_action():
    state, action = readiness.classify_facade_outcome({"status": "REVIEW_REQUIRED"})
    assert state == "NOT_READY"
    assert action == "AUTHOR_VISUAL_CRITIC_REVIEW"


def test_pass_is_ready():
    state, action = readiness.classify_facade_outcome({"status": "PASS"})
    assert state == "PASS"
    assert action is None


def test_validate_request_accepts_exact_preview_freeze(tmp_path: Path):
    request = make_preview_request(tmp_path)
    validated = readiness.validate_request(tmp_path, request)
    assert validated.episode_date == "2026-08-17"
    assert validated.request_path == "daily-production-requests/2026-08-17-preview.json"
    assert validated.freeze_path == tmp_path / "semantic-freezes/2026-08-17.json"
    assert validated.request_sha256 == hashlib.sha256(request.read_bytes()).hexdigest()


def test_validate_request_rejects_non_preview_confirmation(tmp_path: Path):
    request = make_preview_request(tmp_path)
    value = json.loads(request.read_text(encoding="utf-8"))
    value["confirmation"] = "FINAL"
    request.write_text(json.dumps(value) + "\n", encoding="utf-8")
    with pytest.raises(readiness.ReadinessError, match="confirmation must be PREVIEW"):
        readiness.validate_request(tmp_path, request)


def test_validate_request_rejects_freeze_sha_mismatch(tmp_path: Path):
    request = make_preview_request(tmp_path)
    value = json.loads(request.read_text(encoding="utf-8"))
    value["semanticFreeze"]["sha256"] = "0" * 64
    request.write_text(json.dumps(value) + "\n", encoding="utf-8")
    with pytest.raises(readiness.ReadinessError, match="Semantic Freeze SHA mismatch"):
        readiness.validate_request(tmp_path, request)


def test_run_readiness_uses_canonical_facade_and_writes_not_ready_receipt(tmp_path: Path):
    request = make_preview_request(tmp_path)
    renderer = tmp_path / ".renderer"
    renderer.mkdir()
    captured = {}

    def fake_runner(command, *, cwd, check):
        captured["command"] = command
        captured["cwd"] = cwd
        captured["check"] = check
        outcome = tmp_path / "verification/2026-08-17/current_production_facade_outcome.json"
        outcome.parent.mkdir(parents=True, exist_ok=True)
        outcome.write_text(
            json.dumps(
                {
                    "status": "PREPARED",
                    "requiredAction": "AUTHOR_VISUAL_INTELLIGENCE_DECISION",
                    "reason": None,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0)

    code, receipt = readiness.run_readiness(
        root=tmp_path,
        renderer_root=renderer,
        request_path=request,
        runner=fake_runner,
    )

    command = captured["command"]
    assert command[1] == "scripts/current_production_facade_v12.py"
    assert "--phase" in command and command[command.index("--phase") + 1] == "prepare"
    assert "--build-handoff-on-pass" not in command
    assert not any("run_semantic_frozen_renderer_closure_v12.py" in part for part in command)
    assert not any("run_daily_renderer_closure_v12.py" in part for part in command)
    assert not any("run_daily_production_v12.py" in part for part in command)
    assert code == readiness.NOT_READY_EXIT
    assert receipt["state"] == "NOT_READY"
    assert receipt["facadeStatus"] == "PREPARED"
    assert receipt["requiredAction"] == "AUTHOR_VISUAL_INTELLIGENCE_DECISION"
    assert receipt["selectedPhase"] == "prepare"
    assert receipt["previewHandoffReady"] is False
    assert receipt["previewPublicationReady"] is False
    written = json.loads(
        (tmp_path / "verification/2026-08-17/current_preview_request_readiness.json").read_text(
            encoding="utf-8"
        )
    )
    assert written == receipt
