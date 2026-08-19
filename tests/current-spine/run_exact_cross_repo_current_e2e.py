#!/usr/bin/env python3
"""PR-0B exact-pinned current Cross-Repo E2E.

The test consumes the canonical Plot renderer binding, rejects any checkout or
registry mismatch, and then reuses the existing current Renderer fixture/Visual
Intelligence E2E rather than inventing a second synthetic production fixture.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
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

    output = {
        **result,
        "bridgeContractVersion": binding["bridgeContractVersion"],
        "rendererContractVersion": renderer["contractVersion"],
        "registrySnapshotSha256": registry_sha,
        "exactPinnedRenderer": True,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
