#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_final_render_authorization_v12 as final_auth  # noqa: E402

DATE = "2099-04-04"
RUN_ID = "123456789"


def write(path: Path, value: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def fixture(root: Path) -> tuple[Path, Path, Path]:
    (root / "contracts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / "contracts/final_render_authorization.schema.json",
        root / "contracts/final_render_authorization.schema.json",
    )
    spec = write(root / f"render-specs/{DATE}/render_spec.json", {"episode": {"targetDate": DATE}})
    write(root / f"working/{DATE}/production_state.json", {
        "episode_date": DATE,
        "current_state": "user_preview_approved",
    })
    package = write(root / f"working/{DATE}/visual-intelligence/visual_intelligence_package.json", {
        "contractVersion": "1.0.0",
        "episodeDate": DATE,
    })
    write(root / f"verification/{DATE}/visual_intelligence_validation.json", {
        "status": "PASS",
        "episodeDate": DATE,
        "packageSha256": final_auth.sha256_file(package),
    })
    mp4 = root / "downloaded/preview.mp4"
    mp4.parent.mkdir(parents=True, exist_ok=True)
    mp4.write_bytes(b"synthetic-preview-bytes")
    preview_sha = final_auth.sha256_file(mp4)
    review = write(root / f"verification/{DATE}/human_preview_review.json", {
        "contractVersion": "1.0.0",
        "episodeDate": DATE,
        "previewSha256": preview_sha,
        "status": "approved",
        "reviewedAt": "2099-04-04T12:00:00Z",
    })
    technical = write(root / "downloaded/technical_report.json", {
        "status": "preview-generated",
        "episodeId": DATE,
        "inputSpecSha256": final_auth.sha256_file(spec),
        "previewPath": "renders/preview/synthetic.mp4",
    })
    return review, mp4, technical


def expect_failure(root: Path, review: Path, mp4: Path, technical: Path, needle: str, *, explicit: bool = True) -> None:
    try:
        final_auth.build_authorization(
            root=root,
            date=DATE,
            preview_run_id=RUN_ID,
            preview_mp4=mp4,
            preview_technical_report=technical,
            human_preview_review=review,
            explicit_final=explicit,
        )
    except final_auth.FinalAuthorizationError as exc:
        if needle not in str(exc):
            raise AssertionError(f"expected {needle!r}, got {exc}") from exc
    else:
        raise AssertionError("expected FinalAuthorizationError")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nasdaq-final-auth-") as temp:
        root = Path(temp)
        review, mp4, technical = fixture(root)
        result = final_auth.build_authorization(
            root=root,
            date=DATE,
            preview_run_id=RUN_ID,
            preview_mp4=mp4,
            preview_technical_report=technical,
            human_preview_review=review,
            explicit_final=True,
        )
        assert result["status"] == "approved"
        assert result["final_requested"] is True
        assert result["previewSha256"] == final_auth.sha256_file(mp4)
        assert result["renderSpecSha256"] == json.loads(technical.read_text())["inputSpecSha256"]
        assert result["previewTechnicalReportSha256"] == final_auth.sha256_file(technical)
        assert result["humanPreviewReviewSha256"] == final_auth.sha256_file(review)

        expect_failure(root, review, mp4, technical, "--explicit-final", explicit=False)

        mp4.write_bytes(b"different-preview")
        expect_failure(root, review, mp4, technical, "actual Preview MP4 SHA")

        mp4.write_bytes(b"synthetic-preview-bytes")
        value = json.loads(technical.read_text())
        value["inputSpecSha256"] = "c" * 64
        write(technical, value)
        expect_failure(root, review, mp4, technical, "current render_spec SHA")

        value["inputSpecSha256"] = final_auth.sha256_file(root / f"render-specs/{DATE}/render_spec.json")
        write(technical, value)
        state = root / f"working/{DATE}/production_state.json"
        write(state, {"episode_date": DATE, "current_state": "user_review_pending"})
        expect_failure(root, review, mp4, technical, "user_preview_approved")

    print("final render authorization v1.2 tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
