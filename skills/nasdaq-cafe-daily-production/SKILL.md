---
name: nasdaq-cafe-daily-production
version: 1.3.1
description: Manage the deterministic daily production lifecycle after the user supplies a Nasdaq Cafe daily source package, including Visual Intelligence v1.2 and explicit Visual Evidence Planning before preview.
---

# Daily Production Operational Entry Point

## Purpose

Provide one safe command-line entry point for the mechanical parts of daily 朝のNASDAQカフェ production.

The user supplies `daily_source_package_YYYY-MM-DD.md`. ChatGPT performs the research, editorial decision, fox narration, 9-Scene production, 04 inquisition, Visual Intelligence editorial judgment, **Visual Evidence Planning**, and Primary/Fallback decision. The CLI records and validates the resulting artifacts, builds the production package and preview handoff, and records the preview result.

## Production entrypoints

Legacy production continues to use the hardening wrapper:

```bash
python scripts/run_daily_production_hardened.py --workspace . <command> ...
```

A new production request explicitly bound to:

```text
visual-intelligence-bridge/1.2.0
```

uses the contract-versioned wrapper instead:

```bash
python scripts/run_daily_production_v12.py --workspace . <command> ...
```

The Renderer SHA and Registry Snapshot SHA for the v1.2 path come only from:

```text
contracts/renderer_binding.json
```

Do not copy those values into another v1.2 script or workflow. Do not silently migrate a legacy request to v1.2.

For the fresh real-day canary, use the two-stage closure:

```bash
python scripts/run_daily_renderer_closure_v12.py --phase prepare ...
# ChatGPT/AI-B authors the exact decision from the resulting legal Candidate Catalog.
python scripts/run_daily_renderer_closure_v12.py --phase compile ...
```

`prepare` must stop at `DECISION_REQUIRED` after Candidate generation. GitHub Actions does not select a Candidate. `compile` is legal only after ChatGPT has authored the Visual Director/Critic decision. Neither phase renders Preview or Final automatically.

Do not use `scripts/run_daily_production.py` directly for production. The base script remains the deterministic legacy state-machine implementation and unit-test target.

## Visual Intelligence responsibility boundary

Before authoring `visual_requirements.json` or `visual_intelligence_decision.json`, read:

```text
skills/nasdaq-cafe-visual-intelligence/SKILL.md
skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md
```

The frozen division is:

```text
Machine = accident prevention, eligibility, references, SHA lineage, reproducibility
LLM     = Visual Intent, Candidate selection, information gain, Critic judgment
Human   = actual Preview quality and explicit approval
```

Machine code must not rank legal Candidates by novelty, variety, or interest. `Visual change is not editorial progress.` `Novelty is not editorial value.`

The v1.2 machine artifacts live under:

```text
working/YYYY-MM-DD/visual-intelligence/
```

and include the current editorial snapshot, Financial Candidate Provider, VisualCandidateInput, Capability Inventory, Candidate Catalog, compile report, warning shadow report, review result, and final `visual_intelligence_package.json`.

The final package must be bound to the same editorial snapshot, exact Renderer commit, exact Registry Snapshot SHA, asset-resolution state, Candidate Catalog, compiled visual, warnings and Critic PASS. A Story change invalidates the old Visual Intent, Candidate Catalog and PASS; restart from the new editorial snapshot.

## It does not do

- search the web or replace ChatGPT research;
- choose the lead or market causality;
- create or rewrite narration, titles, telops, or Visual Beats;
- perform the 04 entertainment inquisition;
- decide whether a real source, Financial Visual, social post, photo, generated illustration, or existing asset best communicates a Visual Beat;
- generate images or choose Primary/Fallback;
- automatically start final rendering;
- automatically approve publication, Preview quality, Component promotion, or memory promotion.

## Research acquisition boundary

The existing Causal Research process may request bounded additional evidence from the Collector before `causal_dossier_valid`. This is an internal research loop, not a second Research Engine.

```text
research_inputs_bound
→ Causal Research
→ optional Research Acquisition Bridge (maximum two waves)
→ causal_dossier_valid
```

The Collector executes only explicit requests. It does not choose the lead, Expected / Actual / Gap, causal scope, or comparison set. If required evidence remains unavailable, `unresolved`, `reason_unknown`, or an unconfirmed Expected remain valid outcomes.

The original `research_input_manifest.json` remains immutable. Any acquired evidence used by the dossier must be bound through the append-only `research_evidence_supplement_manifest.json` before it is treated as current evidence.

## Visual Evidence Planning boundary

For v1.2, after the Story snapshot is valid and before asset resolution, ChatGPT must author Visual Intent and Provisional Direction. Any Beat whose `imageRequirement` is `required` must already have an existing Visual Source Intent with Primary and Approved Fallback before asset resolution begins.

```text
causal_dossier_valid
→ editorial_snapshot_valid
→ ChatGPT Visual Intent / Provisional Direction
→ visual_requirements_planned
→ Primary / Approved Fallback planning
→ assets_resolved
→ legal Candidate Catalog
→ ChatGPT Final Visual Director / Visual Plan Critic
→ visual_intelligence_valid
→ episode_package_final
```

Every production attempt must still contain:

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

Once `working/YYYY-MM-DD/visual-intelligence/visual_requirements.json` exists, the working Visual Source plan is a ChatGPT-authored semantic checkpoint. A deterministic v1.2 rerun must preserve the exact bytes of any existing:

```text
working/YYYY-MM-DD/visual_source_intents.json
working/YYYY-MM-DD/visual_source_selection.json
```

Do not let Daily Authoring rematerialization silently replace those post-Pass-B decisions with an older baseline or an empty list. Before Pass B exists, Daily Authoring remains authoritative for seeding the initial working files. Story or editorial-snapshot drift still invalidates the old Visual Requirements through the existing SHA checks; preservation is not permission to reuse stale semantics.

After Pass B, ChatGPT must explicitly review Reality Anchor opportunities. If `preferredEvidenceModes` includes `source-document` or a real source materially improves grounding, update `working/YYYY-MM-DD/visual_source_intents.json` before rerunning closure rather than accepting a mechanically inherited empty list by default.

For sources already represented in the approved Source Registry by an exact public URL, reuse the existing Visual Source route first:

```text
official-url / direct-download
or
official-url / pdf-page-render
or
official-url / webpage-screenshot
```

Use `collector-document` only when the actual Collector archive is locally mounted and the exact document/local path exists. Do not add a second Collector→Plot transport, asset manifest, Visual Source resolver, or handoff format merely to move a source that the existing exact URL route can already resolve.

Non-empty intents must reuse the existing Visual Source contract: exact locators, existing source/Beat IDs, Primary plus Approved Fallback, explicit rights status, and no new factual or causal meaning. Asset resolution remains mechanical and cannot rewrite the story. A failed Primary with a legal Approved Fallback remains `resolved`; only exhaustion of legal alternatives may become `BLOCKED`.

A non-empty Visual Source plan also requires an explicit `working/YYYY-MM-DD/visual_source_selection.json`. If that selection has not been authored yet, v1.2 closure must stop as an expected semantic pause with `AUTHOR_VISUAL_SOURCE_SELECTION`; it must not classify the missing selection as a renderer or machine failure.

## State behavior

Every state transition is forward-only and requires SHA-bound evidence. The production request and original daily source are continuously rehashed. Any changed, missing, stale, or path-escaping evidence invalidates the state.

The legacy preview path remains unchanged.

The v1.2 preview path is:

```text
intake_ready
→ research_inputs_bound
→ causal_dossier_valid
→ editorial_snapshot_valid
→ visual_requirements_planned
→ assets_resolved
→ visual_intelligence_valid
→ episode_package_final
→ memory_usage_valid
→ production_package_valid
→ handoff_ready
→ preview_dispatched
→ preview_ready
→ user_review_pending
→ user_preview_approved
```

`episode_package_final` on the v1.2 path still re-runs the existing Story Engine v1.1 acceptance, Story projection, and Pre-TTS Visual Gate. Visual Intelligence does not weaken those hard gates.

The v1.2 production build also persists the exact Visual Intelligence PASS, package SHA, compiled-visual SHA, editorial-snapshot SHA, Renderer commit and Registry Snapshot SHA into `official_execution_preflight.json`. Renderer handoff then carries that evidence into the immutable Preview bundle.

Final can only be requested after `user_preview_approved`, with an approval record and the explicit `--explicit-final` flag. The approval record may be created only after the user explicitly approves the actual Preview. The CLI records authorization only; it does not execute final.

## Main commands

Legacy:

```bash
python scripts/run_daily_production_hardened.py --workspace . init ...
python scripts/run_daily_production_hardened.py --workspace . status ...
python scripts/run_daily_production_hardened.py --workspace . advance ...
python scripts/run_daily_production_hardened.py --workspace . build-production ...
python scripts/run_daily_production_hardened.py --workspace . build-handoff ...
python scripts/run_daily_production_hardened.py --workspace . record-preview ...
python scripts/run_daily_production_hardened.py --workspace . request-final --explicit-final ...
```

Visual Intelligence v1.2:

```bash
python scripts/run_daily_production_v12.py --workspace . init ...
python scripts/run_daily_production_v12.py --workspace . status ...
python scripts/run_daily_production_v12.py --workspace . advance ...
python scripts/run_daily_production_v12.py --workspace . build-production ...
python scripts/run_daily_production_v12.py --workspace . build-handoff ...
python scripts/run_daily_production_v12.py --workspace . record-preview ...
python scripts/run_daily_production_v12.py --workspace . request-final --explicit-final ...
```

The CLIs emit machine-readable JSON and stable error codes. Stop reasons identify the failed lifecycle boundary rather than silently repairing inputs.

## Editorial Semantic Boundary v2

Current Visual Intelligence v1.2 production uses this authority chain:

```text
Raw Daily Authoring Parts (authoring / lineage only)
→ Authoritative Causal Dossier + SHA-bound validation receipt
→ Canonical Daily Authoring v2
→ Official Story Plan / Story Script / 04 validation
→ Editorial Semantic Acceptance
→ Semantic Freeze 1.2 CREATE (authoring / PR preparation only)
→ committed Freeze
→ Production VERIFY only
→ derived Story sidecars + Story Engine acceptance (validation receipt only)
→ WS-4 read-only identity gate
→ editorial_snapshot_valid
→ Visual Intelligence
```

Hard rules:

- Daily Authoring v2 is the current ChatGPT semantic authority.
- The Dossier body is referenced, not duplicated into production.
- `creativeReview` is authored/reviewed by ChatGPT; machine code never synthesizes PASS.
- Story Engine is validation-only after Semantic Freeze.
- Current-v2 never calls generic semantic fixup.
- Production GitHub Actions never CREATE Semantic Freeze or Editorial Semantic Acceptance.
- Unknown contract versions fail closed.
- Historical daily artifacts remain on explicit legacy paths and are never current-contract fixtures.
