#!/usr/bin/env python3
"""PR-0A characterization for the current NASDAQ Cafe production spine.

This test intentionally records observable current behavior and known architectural
collisions before any refactor.  Later PRs are expected to update an assertion only
when they deliberately remove the corresponding divergence.
"""
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


def main() -> int:
    current = text("scripts/run_daily_production_v12.py")
    base = text("scripts/run_daily_production.py")
    closure = text("scripts/run_daily_renderer_closure_v12.py")
    frozen = text("scripts/run_semantic_frozen_renderer_closure_v12.py")
    preview = text(".github/workflows/chatgpt-daily-preview-production.yml")

    # CURRENT_POLICY still inherits policy from the hardened/legacy stack.
    require(current, "import run_daily_production_hardened as hardened", "current -> hardened policy dependency")
    require(current, "return hardened.load_hardened_daily_module()", "v1.2 control-plane loader")

    # Current request is not born complete yet: VI binding is appended and the
    # request/state lineage is repaired after the initial request write.
    require(current, "def _rebind_request_sha", "post-hoc request SHA repair helper")
    require(current, 'request["visual_intelligence"] = {', "post-init Visual Intelligence binding")
    require(current, "_rebind_request_sha(module, workspace, date)", "post-init request SHA rebind")

    # The base request is also mutated when Final is requested, including evidence
    # SHA rewrite. PR-1 must make the current request immutable for the full attempt.
    require(base, 'request["approvals"]["final_requested"] = True', "base request mutation at Final request")
    require(base, 'evidence["sha256"] = state["request_sha256"]', "request evidence SHA rewrite")

    # Current closure still imports legacy procedure and preserves semantic files via
    # capture/restore around deterministic rematerialization.
    require(closure, "import run_daily_renderer_closure as legacy", "current closure -> legacy procedure dependency")
    require(closure, "def _capture_visual_source_authoring", "capture workaround")
    require(closure, "def _restore_visual_source_authoring", "restore workaround")

    # Director and Critic are still combined in one current authority path.
    require(closure, '"visual_intelligence_decision.json"', "combined Director/Critic decision artifact")

    # Production Preview entry currently uses a dedicated semantic-frozen wrapper
    # and then separately invokes the v1.2 handoff command. This is the observable
    # workflow behavior PR-4 will consolidate behind one facade.
    require(preview, "scripts/run_semantic_frozen_renderer_closure_v12.py", "Preview semantic closure entry")
    require(preview, "scripts/run_daily_production_v12.py --workspace . build-handoff", "Preview handoff entry")
    require(frozen, '"scripts/run_daily_renderer_closure_v12.py"', "semantic wrapper delegates to closure v1.2")

    print("current spine characterization PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
