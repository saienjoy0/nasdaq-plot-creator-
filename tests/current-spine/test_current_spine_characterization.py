#!/usr/bin/env python3
"""Executable characterization of the current NASDAQ Cafe production spine."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    value = (ROOT / path).read_text(encoding="utf-8")
    if not value.strip():
        raise AssertionError(f"characterized source is empty: {path}")
    return value


def require(source: str, needle: str, label: str) -> None:
    if needle not in source:
        raise AssertionError(f"current characterization drifted: {label}: {needle!r}")


def forbid(source: str, needle: str, label: str) -> None:
    if needle in source:
        raise AssertionError(f"resolved divergence regressed: {label}: {needle!r}")


def main() -> int:
    current = text("scripts/run_daily_production_v12.py")
    mechanisms = text("scripts/current_daily_mechanisms_v12.py")
    base = text("scripts/run_daily_production.py")
    closure = text("scripts/run_daily_renderer_closure_v12.py")
    frozen = text("scripts/run_semantic_frozen_renderer_closure_v12.py")
    preview = text(".github/workflows/chatgpt-daily-preview-production.yml")

    # PR-1 resolves Current -> legacy policy inheritance. The historical policy name
    # may remain in explanatory prose, so this guard intentionally checks imports.
    require(
        current,
        "import current_daily_mechanisms_v12 as current_mechanisms",
        "current mechanisms dependency",
    )
    forbid(
        current,
        "import run_daily_production_hardened as hardened",
        "current -> hardened policy import",
    )
    forbid(
        mechanisms,
        "import run_daily_production as base",
        "current mechanisms -> legacy base policy import",
    )
    require(mechanisms, "def request_final(", "current Final authorization mechanism")

    # Current request is born complete and immutable for the attempt.
    forbid(current, "def _rebind_request_sha", "post-hoc request SHA repair helper")
    require(current, '"semantic_freeze": {', "Semantic Freeze bound at request creation")
    require(current, '"registry_snapshot_sha256":', "Registry identity bound at request creation")

    # Legacy/base still mutates its own request. That is permitted only outside the
    # current path and remains visible until PR-8 legacy isolation documentation.
    require(
        base,
        'request["approvals"]["final_requested"] = True',
        "legacy request mutation at Final request",
    )
    require(
        base,
        'evidence["sha256"] = state["request_sha256"]',
        "legacy request evidence SHA rewrite",
    )

    # PR-2 resolves the multi-writer/combined VI authority collisions.
    forbid(
        closure,
        "import run_daily_renderer_closure as legacy",
        "current closure -> legacy procedure dependency",
    )
    forbid(closure, "def _capture_visual_source_authoring", "capture workaround")
    forbid(closure, "def _restore_visual_source_authoring", "restore workaround")
    forbid(closure, "visual_intelligence_decision.json", "combined Director/Critic authority")
    require(
        closure,
        "visual_director_decision.semantic.json",
        "Director semantic payload boundary",
    )
    require(
        closure,
        "materialize_visual_intelligence_artifact_v12.py",
        "Requirements machine materializer",
    )
    require(
        closure,
        "renderer_contract_sync_v12.sync_renderer_owned_contracts",
        "Renderer contract sync mechanism",
    )

    # PR-4 will consolidate these two current procedure entries behind one facade.
    require(
        preview,
        "scripts/run_semantic_frozen_renderer_closure_v12.py",
        "Preview semantic closure entry",
    )
    require(
        preview,
        "scripts/run_daily_production_v12.py --workspace . build-handoff",
        "Preview handoff entry",
    )
    require(
        frozen,
        '"scripts/run_daily_renderer_closure_v12.py"',
        "semantic wrapper delegates to closure v1.2",
    )

    print("current spine characterization PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
