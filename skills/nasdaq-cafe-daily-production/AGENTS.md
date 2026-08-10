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

It also owns the Unified Story Engine v1.1 production gate. Story Plan, script draft, and creative review are internal editorial passes and must not become public Daily Production states. The public lifecycle advances directly from `causal_dossier_valid` to `episode_package_final` only when one hash-bound Story Engine acceptance, the final episode package, the matching projection report, and the Pre-TTS Visual Gate pass validation.

`scripts/run_daily_production_story_engine_v1_1.py` is a compatibility alias only and must not install a second state-machine layer.

If any hardened dependency is unavailable, fail closed before running the state machine.

## Research supersession boundary

`restart-research` is an exceptional 04-to-Research recovery path, not a general reset command.

- It is allowed only while the public state is `causal_dossier_valid`; it never regresses a public state.
- It requires one SHA-bound `research_retry_request.json` that cites a non-PASS 04 creative review.
- Structured retry reasons are limited to Critical `CAUSALITY_DRIFT`, `COUNTEREVIDENCE_REMOVED`, `TIMELINE_DRIFT`, or `NASDAQ_SCOPE_OVERREACH` findings.
- A pure factual error may use `FACTUAL_ERROR` only when the retry request quotes one or more exact 04 `immediate_failures` strings.
- Clarity, fox voice, pacing, entertainment, or other presentation defects must never restart Research.
- The superseded production request/state, invalidated state, 04 review, and retry request must be archived with SHA-256 lineage.
- The fresh attempt must reuse the exact same daily source, requested scope, Renderer commit, and Renderer contract version. Missing or changed inputs fail closed.
- If fresh initialization fails after invalidation, restore the prior request with the invalidated state; never silently reactivate the old attempt.

## Required boundaries

- The current ChatGPT project instructions and 01–04 remain authoritative for editorial meaning.
- Do not add an LLM, web research, lead selection, causal inference, narration generation, entertainment scoring, image generation, or Primary/Fallback selection to this CLI.
- Every public transition must be forward-only, evidence-backed, and reproducible by SHA-256.
- Story Engine internal passes must remain inside the `causal_dossier_valid` → `episode_package_final` production boundary.
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
- the original public daily state-machine behavior;
- Unified Story Engine v1.1 acceptance and projection lineage at `episode_package_final`;
- fail-closed Research supersession without public state regression.
