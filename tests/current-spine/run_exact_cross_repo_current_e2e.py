#!/usr/bin/env python3
"""PR-0B exact-pinned current Cross-Repo E2E.

The test consumes the canonical Plot renderer binding, rejects any checkout or
registry mismatch, reuses the existing current Renderer fixture/Visual Intelligence
E2E, and proves the Plot Preview V4 request is accepted by the pinned Renderer
request validator.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cross_repo_module():
    path = ROOT / "tests/remotion-compat/run_visual_intelligence_v12_cross_repo.py"
    spec = importlib.util.spec_from_file_location("current_visual_intelligence_cross_repo", path)
    if not spec or not spec.loader:
        raise AssertionError(f"cannot load existing current Cross-Repo E2E: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify_preview_request_contract(renderer_root: Path, renderer: dict[str, str]) -> dict[str, str]:
    validator = renderer_root / "scripts/validate-current-request.py"
    if not validator.is_file():
        raise AssertionError(f"pinned Renderer Current request validator is missing: {validator}")

    date = "2099-07-01"
    bundle_id = "a" * 64
    artifact_name = "nasdaq-cafe-handoff-2099-07-01-123"
    with tempfile.TemporaryDirectory(prefix="nasdaq-current-preview-request-") as tmp:
        temp = Path(tmp)
        manifest = temp / "handoff_manifest.json"
        manifest.write_text(
            json.dumps({"episodeDate": date, "bundleId": bundle_id}) + "\n",
            encoding="utf-8",
        )
        request = temp / "current_preview_request_v4.json"
        built = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/build_current_preview_request_v4.py"),
                "--root",
                str(ROOT),
                "--date",
                date,
                "--manifest",
                str(manifest),
                "--plot-run-id",
                "123",
                "--artifact-name",
                artifact_name,
                "--output",
                str(request),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if built.returncode != 0:
            raise AssertionError(
                f"Plot Preview V4 request builder failed: stdout={built.stdout!r} stderr={built.stderr!r}"
            )

        value = json.loads(request.read_text(encoding="utf-8"))
        expected_fields = {
            "contractVersion",
            "episodeDate",
            "plotRunId",
            "handoffArtifactName",
            "expectedBundleId",
            "expectedManifestSha256",
            "expectedRendererCommit",
            "expectedRendererContractVersion",
            "expectedRegistrySnapshotSha256",
            "confirmation",
        }
        if set(value) != expected_fields:
            raise AssertionError(f"Plot Preview V4 request fields drifted: {sorted(value)}")
        if value.get("contractVersion") != "2.1.0":
            raise AssertionError("Plot Preview V4 request must use Renderer contractVersion 2.1.0")
        if value.get("expectedRendererCommit") != renderer["commit"]:
            raise AssertionError("Plot Preview V4 request Renderer commit mismatch")
        if value.get("expectedRendererContractVersion") != renderer["contractVersion"]:
            raise AssertionError("Plot Preview V4 request Renderer contract mismatch")
        if value.get("expectedRegistrySnapshotSha256") != renderer["registrySnapshotSha256"]:
            raise AssertionError("Plot Preview V4 request Registry SHA mismatch")

        accepted = subprocess.run(
            [sys.executable, str(validator), "preview", str(request)],
            cwd=renderer_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if accepted.returncode != 0:
            raise AssertionError(
                "pinned Renderer rejected Plot Preview V4 request: "
                f"stdout={accepted.stdout!r} stderr={accepted.stderr!r}"
            )
        return {
            "previewRequestContractVersion": value["contractVersion"],
            "previewRequestRendererValidation": "PASS",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renderer-root", required=True, type=Path)
    args = parser.parse_args()

    renderer_root = args.renderer_root.resolve()
    binding = json.loads((ROOT / "contracts/renderer_binding.json").read_text(encoding="utf-8"))
    renderer = binding["renderer"]

    actual_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=renderer_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual_commit != renderer["commit"]:
        raise AssertionError(
            f"Renderer checkout drift: expected={renderer['commit']} actual={actual_commit}"
        )

    registry_path = renderer_root / renderer["registrySnapshotPath"]
    if not registry_path.is_file():
        raise AssertionError(f"pinned Renderer registry is missing: {registry_path}")
    registry_sha = sha256(registry_path)
    if registry_sha != renderer["registrySnapshotSha256"]:
        raise AssertionError(
            "Renderer Registry snapshot drift: "
            f"expected={renderer['registrySnapshotSha256']} actual={registry_sha}"
        )

    cross_repo = load_cross_repo_module()
    result = cross_repo.run(renderer_root)
    expected = {
        "status": "PASS",
        "rendererCommit": renderer["commit"],
        "machinePausedBeforeDecision": True,
        "staleCatalogDecisionRejected": True,
        "machinePausedBeforeCritic": True,
        "criticBoundToCompiledVisual": True,
        "packageValidation": "PASS",
    }
    for key, value in expected.items():
        if result.get(key) != value:
            raise AssertionError(
                f"current Cross-Repo observable contract drifted: {key}: "
                f"expected={value!r} actual={result.get(key)!r}"
            )

    preview_request = verify_preview_request_contract(renderer_root, renderer)
    output = {
        **result,
        **preview_request,
        "bridgeContractVersion": binding["bridgeContractVersion"],
        "rendererContractVersion": renderer["contractVersion"],
        "registrySnapshotSha256": registry_sha,
        "exactPinnedRenderer": True,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
