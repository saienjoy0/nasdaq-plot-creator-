#!/usr/bin/env python3
"""Run the pinned Renderer's current synthetic Visual Director acceptance.

Historical production artifacts are not current-contract fixtures. This cross-repo
check verifies the exact pinned Renderer checkout and then runs its maintained
synthetic Visual Director suite, which covers Registry/Input/Inventory/vNext.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import renderer_binding  # noqa: E402


def run(renderer_root: Path, repo_root: Path = ROOT) -> dict:
    renderer_root = renderer_root.resolve()
    binding = renderer_binding.load_renderer_binding(repo_root)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=renderer_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if commit != binding["rendererCommit"]:
        raise AssertionError(
            f"pinned Renderer mismatch: expected={binding['rendererCommit']} actual={commit}"
        )

    result = subprocess.run(
        ["npm", "run", "test:visual-director"],
        cwd=renderer_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            "current Renderer Visual Director synthetic acceptance failed:\n"
            + (result.stderr.strip() or result.stdout.strip())
        )
    return {
        "status": "PASS",
        "rendererCommit": commit,
        "candidateBuilder": binding["candidateBuilder"],
        "visualIntelligenceBridge": binding["visualIntelligenceBridge"],
        "fixturePolicy": "current-synthetic-not-historical-production",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renderer-root", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(
        json.dumps(
            run(args.renderer_root, args.repo_root),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
