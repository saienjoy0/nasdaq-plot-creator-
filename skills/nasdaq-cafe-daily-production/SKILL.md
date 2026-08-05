---
name: nasdaq-cafe-daily-production
version: 1.1.0
description: Manage the deterministic daily production lifecycle after the user supplies a Nasdaq Cafe daily source package.
---

# Daily Production Operational Entry Point

## Purpose

Provide one safe command-line entry point for the mechanical parts of daily 朝のNASDAQカフェ production.

The user supplies `daily_source_package_YYYY-MM-DD.md`. ChatGPT performs the research, editorial decision, fox narration, 9-Scene production, 04 inquisition, and Primary/Fallback decision. This CLI records and validates the resulting artifacts, builds the production package and preview handoff, and records the preview result.

## Production entrypoint

Use the hardening wrapper:

```bash
python scripts/run_daily_production_hardened.py --workspace . <command> ...
```

Do not use `scripts/run_daily_production.py` directly for production. The base script remains the deterministic state-machine implementation and unit-test target.

The wrapper preserves the same state transitions and replaces only these dependencies:

```text
build-production → hardened Final Production
build-handoff    → hardened Renderer Handoff
record-preview   → hardened Real-Day Acceptance
```

## It does not do

- search the web or replace ChatGPT research;
- choose the lead or market causality;
- create or rewrite narration, titles, telops, or Visual Beats;
- perform the 04 entertainment inquisition;
- generate images or choose Primary/Fallback;
- automatically start final rendering;
- automatically approve publication or promote memory.

## State behavior

Every state transition is forward-only and requires SHA-bound evidence. The production request and original daily source are continuously rehashed. Any changed, missing, stale, or path-escaping evidence invalidates the state.

The normal preview path is:

```text
intake_ready
→ research_inputs_bound
→ causal_dossier_valid
→ episode_package_final
→ memory_usage_valid
→ assets_resolved
→ production_package_valid
→ handoff_ready
→ preview_dispatched
→ preview_ready
→ user_review_pending
→ user_preview_approved
```

Final can only be requested after `user_preview_approved`, with an approval record and the explicit `--explicit-final` flag. The CLI records authorization only; it does not execute final.

## Main commands

```bash
python scripts/run_daily_production_hardened.py --workspace . init ...
python scripts/run_daily_production_hardened.py --workspace . status ...
python scripts/run_daily_production_hardened.py --workspace . advance ...
python scripts/run_daily_production_hardened.py --workspace . build-production ...
python scripts/run_daily_production_hardened.py --workspace . build-handoff ...
python scripts/run_daily_production_hardened.py --workspace . record-preview ...
python scripts/run_daily_production_hardened.py --workspace . request-final --explicit-final ...
```

The CLI emits machine-readable JSON and stable error codes. Stop reasons identify the failed lifecycle boundary rather than silently repairing inputs.
