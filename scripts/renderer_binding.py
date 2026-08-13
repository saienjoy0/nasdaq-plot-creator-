#!/usr/bin/env python3
"""Load the single production Renderer/Visual Intelligence binding.

This module is mechanical only. It does not choose visuals or alter editorial
meaning. All production scripts/workflows should read the same binding instead
of hand-copying Renderer SHAs.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

BINDING_RELATIVE_PATH = Path("contracts/renderer_binding.json")
EXPECTED_CONTRACT_VERSION = "1.0.0"
EXPECTED_RENDERER_REPOSITORY = "saienjoy0/saienjoy0-nasdaq-cafe-remotion"
EXPECTED_RENDERER_CONTRACT_VERSION = "2.4.0"
EXPECTED_VISUAL_INTELLIGENCE_BRIDGE = "visual-intelligence-bridge/1.2.0"
EXPECTED_CANDIDATE_BUILDER = "vnext"


class RendererBindingError(ValueError):
    pass


def load_renderer_binding(repo_root: Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    path = root / BINDING_RELATIVE_PATH
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RendererBindingError(f"renderer binding invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise RendererBindingError("renderer binding root must be an object")

    expected = {
        "contractVersion": EXPECTED_CONTRACT_VERSION,
        "rendererRepository": EXPECTED_RENDERER_REPOSITORY,
        "rendererContractVersion": EXPECTED_RENDERER_CONTRACT_VERSION,
        "visualIntelligenceBridge": EXPECTED_VISUAL_INTELLIGENCE_BRIDGE,
        "candidateBuilder": EXPECTED_CANDIDATE_BUILDER,
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise RendererBindingError(
                f"renderer binding {key} mismatch: expected={wanted} actual={value.get(key)}"
            )

    commit = value.get("rendererCommit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RendererBindingError("rendererCommit must be a lowercase 40-hex Git SHA")

    snapshot = value.get("registrySnapshotPath")
    if snapshot != "contracts/visual_component_registry_snapshot.json":
        raise RendererBindingError("registrySnapshotPath must point to the Renderer-owned registry snapshot")

    return value


def _env_values(binding: dict[str, Any]) -> dict[str, str]:
    return {
        "RENDERER_REPOSITORY": binding["rendererRepository"],
        "RENDERER_COMMIT": binding["rendererCommit"],
        "RENDERER_CONTRACT_VERSION": binding["rendererContractVersion"],
        "VISUAL_INTELLIGENCE_BRIDGE": binding["visualIntelligenceBridge"],
        "VISUAL_CANDIDATE_BUILDER": binding["candidateBuilder"],
        "VISUAL_REGISTRY_SNAPSHOT_PATH": binding["registrySnapshotPath"],
    }


def export_github_env(binding: dict[str, Any], path: Path) -> None:
    with Path(path).open("a", encoding="utf-8") as handle:
        for key, value in _env_values(binding).items():
            handle.write(f"{key}={value}\n")


def export_github_output(binding: dict[str, Any], path: Path) -> None:
    output_keys = {
        "renderer_repository": binding["rendererRepository"],
        "renderer_commit": binding["rendererCommit"],
        "renderer_contract_version": binding["rendererContractVersion"],
        "visual_intelligence_bridge": binding["visualIntelligenceBridge"],
        "candidate_builder": binding["candidateBuilder"],
        "registry_snapshot_path": binding["registrySnapshotPath"],
    }
    with Path(path).open("a", encoding="utf-8") as handle:
        for key, value in output_keys.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--github-env", type=Path)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    try:
        binding = load_renderer_binding(args.repo_root)
    except RendererBindingError as exc:
        print(f"FAIL: {exc}")
        return 2
    if args.github_env:
        export_github_env(binding, args.github_env)
    if args.github_output:
        export_github_output(binding, args.github_output)
    print(json.dumps(binding, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
