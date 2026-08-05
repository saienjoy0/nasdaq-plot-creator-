# AGENTS.md

## Scope

This directory and `scripts/run_daily_production.py` manage deterministic daily production state only.

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

Changes must preserve PR #8 episode-memory validation, Final Production Package consistency, immutable Renderer Handoff, and Real-Day Acceptance behavior.
