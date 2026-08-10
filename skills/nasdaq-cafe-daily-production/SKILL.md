---
name: nasdaq-cafe-daily-production
version: 1.2.0
description: Manage the deterministic daily production lifecycle after the user supplies a Nasdaq Cafe daily source package, including explicit Visual Evidence Planning before episode finalization.
---

# Daily Production Operational Entry Point

## Purpose

Provide one safe command-line entry point for the mechanical parts of daily 朝のNASDAQカフェ production.

The user supplies `daily_source_package_YYYY-MM-DD.md`. ChatGPT performs the research, editorial decision, fox narration, 9-Scene production, 04 inquisition, **Visual Evidence Planning**, and Primary/Fallback decision. This CLI records and validates the resulting artifacts, builds the production package and preview handoff, and records the preview result.

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
- decide whether a real source, Financial Visual, social post, photo, generated illustration, or existing asset best communicates a Visual Beat;
- generate images or choose Primary/Fallback;
- automatically start final rendering;
- automatically approve publication or promote memory.

## Research acquisition boundary

The existing Causal Research process may request bounded additional evidence from the Collector before `causal_dossier_valid`. This is an internal research loop, not a new Daily Production public state.

```text
research_inputs_bound
→ Causal Research
→ optional Research Acquisition Bridge (maximum two waves)
→ causal_dossier_valid
```

The Collector executes only explicit requests. It does not choose the lead, Expected / Actual / Gap, causal scope, or comparison set. If required evidence remains unavailable, `unresolved`, `reason_unknown`, or an unconfirmed Expected remain valid outcomes.

The original `research_input_manifest.json` remains immutable. Any acquired evidence used by the dossier must be bound through the append-only `research_evidence_supplement_manifest.json` before it is treated as current evidence.

## Visual Evidence Planning boundary

After Story Engine Pass G / final 04 re-review succeeds and before `episode_package_final` is registered, ChatGPT must explicitly plan the medium for the final Visual Beats.

```text
causal_dossier_valid
→ Story Engine / 01 / 03 / 04
→ Visual Evidence Planning
→ episode_package_final
```

Every production attempt must contain:

```text
working/YYYY-MM-DD/visual_source_intents.json
```

A missing file means planning was skipped and is a production failure. If no Visual Source is useful, the valid result is an explicit file with:

```json
{
  "contractVersion": "1.0.0",
  "episodeDate": "YYYY-MM-DD",
  "intents": []
}
```

Therefore an empty intent list is a deliberate `not-required` decision; an absent file is not.

Non-empty intents must reuse the existing Visual Source contract: exact locators, existing source/Beat IDs, Primary plus Approved Fallback, explicit rights status, and no new factual or causal meaning. Asset resolution remains mechanical and cannot rewrite the story.

## State behavior

Every state transition is forward-only and requires SHA-bound evidence. The production request and original daily source are continuously rehashed. Any changed, missing, stale, or path-escaping evidence invalidates the state.

The normal preview path remains:

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

Research Acquisition and Visual Evidence Planning are mandatory/conditional work **inside existing boundaries** and do not add public lifecycle states.

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
