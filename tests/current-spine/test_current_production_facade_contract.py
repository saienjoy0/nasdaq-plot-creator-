#!/usr/bin/env python3
"""Static contract: all current execution lanes route through the canonical facade."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    facade = read("scripts/current_production_facade_v12.py")
    production = read(".github/workflows/chatgpt-daily-preview-production.yml")
    canary = read(".github/workflows/visual-intelligence-real-day-canary.yml")
    exact = read(".github/workflows/current-spine-exact-cross-repo-e2e.yml")

    if 'FACADE_VERSION = "1.0.0"' not in facade:
        raise AssertionError("canonical facade version missing")
    for label, workflow in (("Production", production), ("Canary", canary)):
        if "scripts/current_production_facade_v12.py" not in workflow:
            raise AssertionError(f"{label} does not use canonical current facade")
    if "scripts/run_semantic_frozen_renderer_closure_v12.py" in production:
        raise AssertionError("Production still calls semantic closure below the facade")
    if "scripts/run_daily_production_v12.py --workspace . build-handoff" in production:
        raise AssertionError("Production still calls handoff below the facade")
    if "scripts/run_daily_renderer_closure_v12.py" in canary:
        raise AssertionError("Canary still bypasses canonical current facade")
    if "test_current_production_facade_contract.py" not in exact:
        raise AssertionError("Exact E2E does not assert canonical facade routing")
    print("canonical current facade routing PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
