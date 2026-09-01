#!/usr/bin/env python3
"""Regression for reviewed producer modes -> Renderer template-canonical modes."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import renderer_strict_projection as projection  # noqa: E402


def main() -> int:
    expected = {
        "event-reaction-timeline": "timeline",
        "verification-matrix": "verification-points",
        "split-comparison": "stock-comparison",
        "focus-matrix": "stock-comparison",
        "index-return-bars": "stock-comparison",
        "diverging-stock-bars": "stock-comparison",
        "metric-comparison-board": "number-comparison",
        "market-pulse-grid": "number-comparison",
    }
    for template, visual_mode in expected.items():
        actual = projection.normalize_visual_mode("comparison", template)
        if actual != visual_mode:
            raise AssertionError(
                f"comparison template mapping drifted: {template}: {actual!r} != {visual_mode!r}"
            )

    # Real 2026-08-17 producer combinations: the template is more specific than
    # the reviewed producer mode and must win in the strict Renderer projection.
    reviewed_mismatches = {
        ("conclusion-card", "hero-number"): "text-focus",
        ("text-focus", "split-comparison"): "stock-comparison",
        ("number-comparison", "split-comparison"): "stock-comparison",
        ("number-comparison", "verification-matrix"): "verification-points",
        ("verification-matrix", "verification-matrix"): "verification-points",
        ("verification-matrix", "split-comparison"): "stock-comparison",
    }
    for (producer_mode, template), expected_mode in reviewed_mismatches.items():
        actual = projection.normalize_visual_mode(producer_mode, template)
        if actual != expected_mode:
            raise AssertionError(
                f"reviewed template canonicalization drifted: {producer_mode}/{template}: "
                f"{actual!r} != {expected_mode!r}"
            )

    if projection.normalize_visual_mode("expectation-gap", "expected-actual-gap-flow") != "expected-actual-gap":
        raise AssertionError("simple reviewed alias drifted")
    if projection.normalize_visual_mode("verification-matrix") != "verification-points":
        raise AssertionError("scene-level verification-matrix alias drifted")
    if projection.normalize_visual_mode("future-unreviewed-mode", "text-focus") != "future-unreviewed-mode":
        raise AssertionError("unknown mode must remain unknown for fail-closed validation")

    print("template-canonical Renderer visual mode projection PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
