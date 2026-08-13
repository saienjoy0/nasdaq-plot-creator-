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
PREVIEW_SHA = "a" * 64


def write(path: Path, value: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def fixture(root: Path) -> tuple[Path, Path]:
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
    review = write(root / f"verification/{DATE}/human_preview_review.json", {
        "contractVersion": "1.0.0",
        "episodeDate": DATE,
        "previewSha256": PREVIEW_SHA,
        "status": "approved",
        "reviewedAt": "2099-04-04T12:00:00Z",
    })
    delivery = write(root / "downloaded/delivery_manifest.json", {
        "status": "handoff-preview-delivery-ready",
        "runId": RUN_ID,
        "episodeDate": DATE,
        "specSha256": final_auth.sha256_file(spec),
        "previewSha256": PREVIEW_SHA,
    })
    return review, delivery


def expect_failure(root: Path, review: Path, delivery: Path, needle: str, *, explicit: bool = True) -> None:
    try:
        final_auth.build_authorization(
            root=root,
            date=DATE,
            preview_run_id=RUN_ID,
            preview_delivery_manifest=delivery,
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
        review, delivery = fixture(root)
        result = final_auth.build_authorization(
            root=root,
            date=DATE,
            preview_run_id=RUN_ID,
            preview_delivery_manifest=delivery,
            human_preview_review=review,
            explicit_final=True,
        )
        assert result["status"] == "approved"
        assert result["final_requested"] is True
        assert result["previewSha256"] == PREVIEW_SHA
        assert result["renderSpecSha256"] == json.loads(delivery.read_text())["specSha256"]
        assert result["humanPreviewReviewSha256"] == final_auth.sha256_file(review)

        expect_failure(root, review, delivery, "--explicit-final", explicit=False)

        value = json.loads(delivery.read_text())
        value["previewSha256"] = "b" * 64
        write(delivery, value)
        expect_failure(root, review, delivery, "actual Preview SHA")

        value["previewSha256"] = PREVIEW_SHA
        value["specSha256"] = "c" * 64
        write(delivery, value)
        expect_failure(root, review, delivery, "current render_spec SHA")

        value["specSha256"] = final_auth.sha256_file(root / f"render-specs/{DATE}/render_spec.json")
        write(delivery, value)
        state = root / f"working/{DATE}/production_state.json"
        write(state, {"episode_date": DATE, "current_state": "user_review_pending"})
        expect_failure(root, review, delivery, "user_preview_approved")

    print("final render authorization v1.2 tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
