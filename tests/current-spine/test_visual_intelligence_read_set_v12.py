#!/usr/bin/env python3
"""PR-3 exact direct read-set stale-invalidation acceptance A-D."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import visual_intelligence_artifacts_v12 as artifacts  # noqa: E402
import visual_intelligence_read_set_v12 as read_sets  # noqa: E402
import visual_intelligence_requirements as requirements_validator  # noqa: E402

DATE = "2099-05-01"


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_a_b_c_direct_read_set() -> None:
    with tempfile.TemporaryDirectory(prefix="nasdaq-read-set-") as temp:
        root = Path(temp)
        direct = root / "inputs/direct.json"
        unrelated = root / "metadata/unrelated.json"
        write(direct, {"value": 1})
        write(unrelated, {"note": 1})
        receipt = {
            "stage": {
                "files": [read_sets.file_ref(root, direct)],
                "implementation": [],
            }
        }

        # A: direct input unchanged -> child remains valid.
        if read_sets.verify(root, receipt) != []:
            raise AssertionError("unchanged direct input became stale")

        # C: unrelated metadata-only change -> child remains valid.
        write(unrelated, {"note": 2})
        if read_sets.verify(root, receipt) != []:
            raise AssertionError("unrelated metadata invalidated child")

        # B: direct input changed -> child stale/rebuild.
        write(direct, {"value": 2})
        stale = read_sets.verify(root, receipt)
        if not stale or "sha-mismatch" not in stale[0]:
            raise AssertionError(f"changed direct input was not stale: {stale}")


def test_d_story_snapshot_invalidates_old_requirements() -> None:
    with tempfile.TemporaryDirectory(prefix="nasdaq-snapshot-stale-") as temp:
        root = Path(temp)
        vi = root / "working" / DATE / "visual-intelligence"
        snapshot = vi / "editorial_snapshot.json"
        semantic = vi / artifacts.REQUIREMENTS_SEMANTIC
        write(snapshot, {"contractVersion": "1.0.0", "episodeDate": DATE, "story": "A"})
        write(
            semantic,
            {
                "semanticPayloadVersion": "1.0.0",
                "episodeDate": DATE,
                "intent": {"beats": []},
                "provisionalDirection": {"requirements": []},
            },
        )
        canonical_path = artifacts.materialize_requirements(vi_dir=vi, date=DATE)
        canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
        old_snapshot_sha = read_sets.sha256_file(snapshot)
        if canonical.get("editorialSnapshotSha256") != old_snapshot_sha:
            raise AssertionError("Requirements did not bind initial Snapshot")

        # Candidate Catalog freezes the accepted Requirements lifecycle stage.
        write(vi / "visual_candidate_catalog.json", {"contractVersion": "1.0.0"})
        write(snapshot, {"contractVersion": "1.0.0", "episodeDate": DATE, "story": "B"})
        new_snapshot_sha = read_sets.sha256_file(snapshot)
        if new_snapshot_sha == old_snapshot_sha:
            raise AssertionError("Story/Snapshot mutation did not change identity")

        try:
            requirements_validator.validate(
                canonical,
                {"scenes": []},
                DATE,
                editorial_snapshot_sha256=new_snapshot_sha,
            )
        except requirements_validator.VisualRequirementsError as exc:
            if "editorialSnapshotSha256 mismatch" not in str(exc):
                raise
        else:
            raise AssertionError("old Requirements accepted after Story/Snapshot change")

        try:
            artifacts.materialize_requirements(vi_dir=vi, date=DATE)
        except artifacts.VisualIntelligenceArtifactError as exc:
            if "E_VISUAL_IMMUTABLE_CLOBBER" not in str(exc):
                raise
        else:
            raise AssertionError("sealed Requirements were silently rewritten")


def main() -> int:
    test_a_b_c_direct_read_set()
    test_d_story_snapshot_invalidates_old_requirements()
    print("visual intelligence exact read-set A-D PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
