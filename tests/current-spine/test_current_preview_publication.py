#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_current_preview_publication as publication  # noqa: E402


DATE = "2099-07-01"
SHA = "a" * 64


def request(binding: dict, *, run_id: int = 123) -> dict:
    renderer = binding["renderer"]
    return {
        "contractVersion": "2.1.0",
        "episodeDate": DATE,
        "plotRunId": run_id,
        "handoffArtifactName": f"nasdaq-cafe-handoff-{DATE}-{run_id}",
        "expectedBundleId": SHA,
        "expectedManifestSha256": "b" * 64,
        "expectedRendererCommit": renderer["commit"],
        "expectedRendererContractVersion": renderer["contractVersion"],
        "expectedRegistrySnapshotSha256": renderer["registrySnapshotSha256"],
        "confirmation": "PREVIEW",
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nasdaq-current-preview-publication-") as temp:
        root = Path(temp)
        (root / "contracts").mkdir(parents=True)
        shutil.copyfile(ROOT / "contracts/renderer_binding.json", root / "contracts/renderer_binding.json")
        binding = json.loads((root / "contracts/renderer_binding.json").read_text(encoding="utf-8"))
        request_path = root / "verification" / DATE / "current_preview_request_v4.json"
        request_path.parent.mkdir(parents=True)
        request_path.write_text(json.dumps(request(binding), indent=2, sort_keys=True) + "\n", encoding="utf-8")

        first = publication.build(root=root, request_path=request_path)
        second = publication.build(root=root, request_path=request_path)
        if first != second:
            raise AssertionError("same immutable request did not produce the same publication identity")
        expected_prefix = f"handoff-preview-requests-v4/{DATE}-plot-123-"
        if not first["renderer"]["targetPath"].startswith(expected_prefix):
            raise AssertionError("publication target path is not date/run/SHA bound")
        if first["state"] != "REQUEST_PUBLICATION_READY":
            raise AssertionError("publication receipt state mismatch")

        changed = request(binding, run_id=124)
        request_path.write_text(json.dumps(changed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        third = publication.build(root=root, request_path=request_path)
        if third["renderer"]["targetPath"] == first["renderer"]["targetPath"]:
            raise AssertionError("changed request reused an earlier append-only publication path")

        stale = request(binding)
        stale["expectedRendererCommit"] = "f" * 40
        request_path.write_text(json.dumps(stale, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        try:
            publication.build(root=root, request_path=request_path)
        except publication.PublicationError:
            pass
        else:
            raise AssertionError("stale Renderer binding was accepted for publication")

    print("current Preview publication identity PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
