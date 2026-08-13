#!/usr/bin/env python3
"""Approved Fallback must remain a legal resolved route, not BLOCKED."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import visual_intelligence_bridge as bridge  # noqa: E402


def main() -> int:
    date = "2099-04-04"
    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-fallback-") as temp:
        root = Path(temp)
        audit = root / "verification" / date / "asset_resolution_log.json"
        audit.parent.mkdir(parents=True)
        audit.write_text(
            json.dumps({
                "status": "resolved",
                "selection": {
                    "status": "resolved",
                    "selected_path": "fallback",
                    "unresolved_count": 0,
                    "intent_routes": {
                        "vi-test": {
                            "selected_path": "fallback",
                            "selected_asset_id": "fallback-existing-asset",
                        }
                    },
                },
            }, indent=2) + "\n",
            encoding="utf-8",
        )
        result = bridge._asset_resolution_state(root, date)
        if result["status"] != "resolved" or result["selectedPath"] != "fallback":
            raise AssertionError(f"approved fallback was not treated as resolved: {result}")

        audit.write_text(
            json.dumps({
                "status": "unresolved",
                "selection": {"status": "unresolved", "unresolved_count": 1},
            }, indent=2) + "\n",
            encoding="utf-8",
        )
        try:
            bridge._asset_resolution_state(root, date)
        except bridge.VisualIntelligenceBridgeError as exc:
            if "E_VISUAL_ASSET_RESOLUTION_UNRESOLVED" not in str(exc):
                raise
        else:
            raise AssertionError("unresolved asset route must fail closed")

    print("visual intelligence fallback routing tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
