#!/usr/bin/env python3
"""Static contract: all current execution lanes route through existing canonical boundaries."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    facade = read("scripts/current_production_facade_v12.py")
    readiness = read("scripts/current_preview_request_readiness_v12.py")
    production = read(".github/workflows/chatgpt-daily-preview-production.yml")
    validation = read(".github/workflows/validate-daily-production-package.yml")
    canary = read(".github/workflows/visual-intelligence-real-day-canary.yml")
    exact = read(".github/workflows/current-spine-exact-cross-repo-e2e.yml")
    qualification = read(".github/workflows/current-renderer-runtime-qualification-handoff.yml")

    if 'FACADE_VERSION = "1.0.0"' not in facade:
        raise AssertionError("canonical facade version missing")
    for label, workflow in (("Production", production), ("Canary", canary)):
        if "scripts/current_production_facade_v12.py" not in workflow:
            raise AssertionError(f"{label} does not use canonical current facade")
    if "scripts/run_semantic_frozen_renderer_closure_v12.py" in production:
        raise AssertionError("Production still calls semantic closure below the facade")
    if "scripts/run_daily_production_v12.py --workspace . build-handoff" in production:
        raise AssertionError("Production still calls handoff below the facade")
    if "--phase compile" not in production:
        raise AssertionError("formal main Preview production is no longer compile-only")
    if "scripts/run_daily_renderer_closure_v12.py" in canary:
        raise AssertionError("Canary still bypasses canonical current facade")
    if "test_current_production_facade_contract.py" not in exact:
        raise AssertionError("Exact E2E does not assert canonical facade routing")

    if '"daily-production-requests/**"' not in validation:
        raise AssertionError("PR validation does not observe formal Preview request changes")
    if "scripts/current_preview_request_readiness_v12.py" not in validation:
        raise AssertionError("PR validation does not run Current Preview readiness")
    if "contracts/renderer_binding.json" not in validation:
        raise AssertionError("PR validation does not resolve the canonical Renderer binding")
    if "RENDERER_COMMIT: fc1aa384011549e93bd0698e0bb4790c58dfa153" in validation:
        raise AssertionError("PR validation still hard-codes a stale Renderer commit")
    if "scripts/current_production_facade_v12.py" not in readiness:
        raise AssertionError("Preview readiness does not reuse the sole Current facade")
    forbidden_readiness_calls = (
        "scripts/run_semantic_frozen_renderer_closure_v12.py",
        "scripts/run_daily_renderer_closure_v12.py",
        "scripts/run_daily_production_v12.py",
        "scripts/build_current_preview_publication.py",
        "scripts/build_current_preview_request_v4.py",
        "--build-handoff-on-pass",
    )
    for forbidden in forbidden_readiness_calls:
        if forbidden in readiness:
            raise AssertionError(
                f"Preview readiness bypasses semantic ownership or publishes output: {forbidden}"
            )

    duplicate_fixture = ROOT / "tests/current-spine/build_renderer_runtime_qualification_handoff.py"
    if duplicate_fixture.exists():
        raise AssertionError("duplicate full synthetic Renderer qualification fixture reappeared")
    if "build_renderer_runtime_qualification_handoff.py" in qualification:
        raise AssertionError("Renderer qualification rebuilt the removed duplicate fixture")
    required_existing_boundaries = (
        "test_current_authoring_materializer_parity.py",
        "run_exact_cross_repo_current_e2e.py",
        "test_visual_director_handoff.py",
        "test_current_preview_final_request_builders.py",
    )
    for boundary in required_existing_boundaries:
        if boundary not in qualification:
            raise AssertionError(
                f"Renderer qualification does not compose existing Current boundary: {boundary}"
            )
    if "syntheticProductionFixture':False" not in qualification:
        raise AssertionError("Renderer qualification receipt does not declare duplicate fixture absent")

    print("canonical current facade, Preview readiness, and boundary composition PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
