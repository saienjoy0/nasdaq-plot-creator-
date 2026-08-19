# PR-0A — Current Spine Characterization

Date: 2026-08-19
Design authority: `NASDAQ_CAFE_CURRENT_SPINE_ROOT_CAUSE_CONSOLIDATION_DESIGN_v1.3.2_FINAL_2026-08-19`
Scope: characterization only. No production behavior changes.

## Purpose

Freeze the observable current contract before refactoring.  This document is an index; executable assertions live in `tests/current-spine/test_current_spine_characterization.py` and the existing Visual Intelligence v1.2 acceptance suite.

## Current policy/entry inventory

| Concern | Current owner/path | Classification | Known divergence |
|---|---|---|---|
| Current production state | `scripts/run_daily_production_v12.py` | CURRENT_POLICY | Loads `run_daily_production_hardened` as policy/runtime base |
| Hardened daily wrapper | `scripts/run_daily_production_hardened.py` | MIXED: policy + reusable safety mechanism | Patches base module at runtime and contains compatibility rebind behavior |
| Base daily state machine | `scripts/run_daily_production.py` | LEGACY/BASE POLICY | Request bytes are mutable at Final request |
| Semantic-frozen production wrapper | `scripts/run_semantic_frozen_renderer_closure_v12.py` | CURRENT ENTRY WRAPPER | Delegates to a second v1.2 closure entry |
| Current renderer closure | `scripts/run_daily_renderer_closure_v12.py` | CURRENT PROCEDURE | Imports legacy closure and uses capture/restore workaround |
| Plot Preview workflow | `.github/workflows/chatgpt-daily-preview-production.yml` | CURRENT WORKFLOW | Calls semantic wrapper, then a separate v1.2 handoff entry |
| Renderer identity source | `contracts/renderer_binding.json` | CURRENT BINDING AUTHORITY | Must remain the single source when YAML hard-coded values are removed |

## Artifact ownership snapshot

| Artifact | Current writer | Current readers | Current collision to remove |
|---|---|---|---|
| `working/<date>/production_request.json` | base `init_request`, then v1.2 mutation, later Final mutation | daily state/status | Multiple lifecycle writers + SHA rebind |
| `working/<date>/production_state.json` | base/current state functions | state/status/handoff/final | Request/evidence SHA is rewritten post hoc |
| `working/<date>/visual_source_intents.json` | authoring materialization + semantic checkpoint | current closure / source preparation | Capture/restore is required to prevent overwrite |
| `working/<date>/visual_source_selection.json` | semantic authoring | current closure / source preparation | Capture/restore is required to prevent overwrite |
| `working/<date>/visual-intelligence/visual_requirements.json` | AI-B/ChatGPT current authoring | requirements validator / VI bridge | Semantic payload and machine envelope are still combined |
| `working/<date>/visual-intelligence/visual_intelligence_decision.json` | AI-B/ChatGPT, rewritten after compile for review | VI bridge / package validator | Director and Critic share one temporal artifact |
| `render-specs/<date>/render_spec.json` | Plot production materialization | handoff / Renderer | Markdown-origin compatibility remains elsewhere in the spine |
| `production-bundles/<date>/handoff_manifest.json` | handoff builder | Renderer intake | Current Preview transport is not yet one reusable job path |

## Exact current direct-read-set index

This is a characterization index, not a new dependency registry.  PR-3 will move verified direct-input identities into existing receipts.

| Child / stage | Direct inputs observed in current code |
|---|---|
| Production request init | daily source package, requested scope, canonical Renderer binding arguments |
| Editorial snapshot state gate | editorial snapshot, Editorial Semantic Acceptance, Semantic Freeze, Story projection report |
| Visual Requirements state gate | Visual Requirements, requirements validation, current Editorial Snapshot |
| Visual Intelligence PASS gate | VI package, VI validation, current Editorial Snapshot |
| Episode final gate | episode package Markdown, Story acceptance, Story projection report, Pre-TTS Visual Gate |
| Handoff build | current production package + canonical Renderer binding through existing handoff builder |

## Known divergence ledger

The following are intentional PR-0A assertions and are **not** endorsed target architecture.

1. `run_daily_production_v12.py` directly imports `run_daily_production_hardened`.
2. Current request is created by the base writer, then gains `visual_intelligence`, then `_rebind_request_sha()` rewrites state/evidence lineage.
3. Base `request_final()` mutates the request again and rewrites request evidence SHA.
4. `run_daily_renderer_closure_v12.py` imports the legacy closure.
5. Current closure captures/restores semantic Visual Source files around rematerialization.
6. Director selection and post-compile Critic review still share `visual_intelligence_decision.json`.
7. Plot Preview workflow has more than one current procedure entry (`run_semantic_frozen_renderer_closure_v12.py` plus `run_daily_production_v12.py build-handoff`).
8. Renderer-side child dispatch/polling, hard-coded contract identity, repo-local Final data dependency, and TTS-cache authority are cross-repo divergences covered by PR-0B inventory/tests.

## Observable contract retained by later PRs

Later refactors must preserve these external behaviors unless the design explicitly changes them:

- forward-only current production states;
- semantic pauses expose deterministic `requiredAction`;
- no Preview before Visual Intelligence PASS and handoff validation;
- no Final without explicit user Final authorization;
- pinned Renderer checkout must match `contracts/renderer_binding.json`;
- Story/04/Pre-TTS hard gates stay fail-closed;
- historical real-day artifacts are not current synthetic fixtures.

## PR-0A acceptance

- production source code unchanged;
- characterization test passes on the pre-refactor current spine;
- existing v1.2 Visual Intelligence tests remain the semantic/renderer behavior baseline;
- PR-1 must update this ledger only in the same change that removes each divergence.
