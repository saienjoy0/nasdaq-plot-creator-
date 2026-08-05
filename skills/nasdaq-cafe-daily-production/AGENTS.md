# AGENTS.md

## Scope

This directory and the daily production scripts manage deterministic daily production state only.

## Authoritative entrypoint

Production must use:

```text
scripts/run_daily_production_hardened.py
```

`scripts/run_daily_production.py` remains the base state-machine implementation and unit-test target. Do not invoke it directly for production.

The hardening wrapper must inject:

- `build_final_production_package_hardened.py`
- `build_renderer_handoff_hardened.py`
- `run_real_day_acceptance_hardened.py`

If any hardened dependency is unavailable, fail closed before running the state machine.

## Required boundaries

- The current ChatGPT project instructions and 01–04 remain authoritative for editorial meaning.
- Do not add an LLM, web research, lead selection, causal inference, narration generation, entertainment scoring, image generation, or Primary/Fallback selection to this CLI.
- Every transition must be forward-only, evidence-backed, and reproducible by SHA-256.
- A changed daily source, request, or transition evidence invalidates the existing state.
- Preview and final are separate authorization paths.
- `request-final` only records a user's explicit authorization after approved preview; it never dispatches or executes final.
- Publication approval and memory promotion remain separate explicit states with separate evidence.
- Do not infer missing files, dates, commits, renderer versions, paths, or approval status.
- Fail with the stable error code and exact path or lifecycle boundary.

## Regression requirement

Changes must preserve:

- PR #8 episode-memory validation and final-package hardening;
- deterministic Final Production Package consistency and metadata-leak rejection;
- immutable Renderer Handoff with hardened preflight evidence;
- Real-Day Acceptance with bundled hardening evidence;
- the original daily state-machine behavior.
