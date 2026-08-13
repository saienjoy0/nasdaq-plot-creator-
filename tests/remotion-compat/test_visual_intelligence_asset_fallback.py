#!/usr/bin/env python3
"""Asset resolution normalizes current flat logs and legacy nested compatibility."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import visual_intelligence_bridge as bridge  # noqa: E402


def write_audit(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    date = "2099-04-04"
    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-fallback-") as temp:
        root = Path(temp)
        audit = root / "verification" / date / "asset_resolution_log.json"
        audit.parent.mkdir(parents=True)

        # Current canonical resolver shape: flat, resolved, no generated asset required.
        write_audit(audit, {
            "episode_date": date,
            "registered_assets": ["foxNormal"],
            "selected_path": "not-required",
            "status": "resolved",
            "unresolved_count": 0,
        })
        result = bridge._asset_resolution_state(root, date)
        if result["status"] != "resolved" or result["selectedPath"] != "not-required":
            raise AssertionError(f"flat not-required resolution was not normalized: {result}")
        if result["intentRoutes"] != {}:
            raise AssertionError(f"flat not-required route invented intent routes: {result}")

        # Current flat resolver shape may also report an approved fallback route.
        write_audit(audit, {
            "episode_date": date,
            "selected_path": "fallback",
            "status": "resolved",
            "unresolved_count": 0,
            "intent_routes": {
                "vi-test": {
                    "selected_path": "fallback",
                    "selected_asset_id": "fallback-existing-asset",
                }
            },
        })
        result = bridge._asset_resolution_state(root, date)
        if result["status"] != "resolved" or result["selectedPath"] != "fallback":
            raise AssertionError(f"flat approved fallback was not treated as resolved: {result}")
        if result["intentRoutes"]["vi-test"]["selected_asset_id"] != "fallback-existing-asset":
            raise AssertionError(f"flat fallback intent route was lost: {result}")

        # Legacy nested compatibility remains accepted during migration.
        write_audit(audit, {
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
        })
        result = bridge._asset_resolution_state(root, date)
        if result["status"] != "resolved" or result["selectedPath"] != "fallback":
            raise AssertionError(f"nested compatibility fallback was not resolved: {result}")

        # Either shape must fail closed while unresolved alternatives remain.
        write_audit(audit, {
            "status": "unresolved",
            "selected_path": None,
            "unresolved_count": 1,
        })
        try:
            bridge._asset_resolution_state(root, date)
        except bridge.VisualIntelligenceBridgeError as exc:
            if "E_VISUAL_ASSET_RESOLUTION_UNRESOLVED" not in str(exc):
                raise
        else:
            raise AssertionError("flat unresolved asset route must fail closed")

        write_audit(audit, {
            "status": "unresolved",
            "selection": {"status": "unresolved", "unresolved_count": 1},
        })
        try:
            bridge._asset_resolution_state(root, date)
        except bridge.VisualIntelligenceBridgeError as exc:
            if "E_VISUAL_ASSET_RESOLUTION_UNRESOLVED" not in str(exc):
                raise
        else:
            raise AssertionError("nested unresolved asset route must fail closed")

    print("visual intelligence asset resolution shape tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
