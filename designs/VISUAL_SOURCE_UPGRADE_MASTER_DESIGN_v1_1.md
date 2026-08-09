# 朝のNASDAQカフェ｜Visual Source Upgrade Master Design v1.1

Status: APPROVED FOR PR-0 IMPLEMENTATION

This repository uses the following implementation authority for Visual Source Upgrade v1.1.

## Core rule

Reuse existing mechanics before building anything new. Search current code and merged history first; prefer unchanged reuse, backward-compatible extension, or adaptation of proven in-project mechanics. Do not duplicate Final Episode Contract, Daily Production state machine, Final Production, Visual Grammar, Financial Visual, asset manifest, renderer composition, or immutable handoff.

## Delivery order

1. PR-0 — Formal 2026-08-06 baseline.
2. PR-1 — Renderer full immutable-handoff intake and shared runtime asset registry.
3. PR-2 — Visual Source Intent + exact-locator resolver integrated into the Final Episode Contract and `assets_resolved`.
4. PR-3 — Same-story/same-narration A/B preview with 2–4 Visual Source Beats and stagnation warning.

## Responsibility boundary

```text
collector raw evidence
→ causal research
→ Story Engine / 01–04
→ Final Episode Contract
→ Visual Source Intent
→ exact-locator resolver
→ assets_resolved
→ existing Final Production
→ existing immutable handoff
→ Remotion handoff intake
→ shared runtime asset registry
→ existing validator + compile + NasdaqCafeSpec
→ preview
→ user visual review
→ final only on explicit request
```

Visual Source resolution never changes lead, causality, Expected/Actual/Gap, chronology, confidence, counterevidence, Scene order, narration, telops, Visual Grammar, Financial Visual meaning, or Primary/Fallback meaning.

## Visual Source model

Do not add a second semantic Visual Role hierarchy. Existing `primaryFunction`, `visualGrammarId`, Scene role, and Financial Visual Intent remain authoritative for meaning.

Visual Source only describes the medium and acquisition mechanics:

- `presentationClass`: `source-document`, `real-world-photo`, `social-post`, `generated-illustration`, `existing-asset`
- `sourceKind`: `existing-asset`, `collector-document`, `official-url`, `web-page`, `social-post`, `wikimedia`, `generated-image`
- `captureMethod`: `registry-reference`, `archive-file`, `direct-download`, `pdf-page-render`, `webpage-screenshot`, `social-capture`, `mediawiki-fetch`, `local-file-validation`
- `selectedPath`: existing `primary`, `fallback`, `not-required`

Resolver inputs must contain exact locators. Generic search queries are forbidden.

Rights use existing vocabulary: `cleared`, `user-review-required`, `not-required`. Resolver never auto-promotes third-party material to `cleared`.

## Production projection

The Visual Source result projects into existing Final Production `image_resolution`, `asset_catalog`, `asset_manifest`, and selected `render_spec.assetPlacements`. Non-selected candidates remain only in the Plot-side audit log and must not enter the renderer handoff.

## Renderer transport

The existing immutable handoff remains the transport format. The renderer adds only an intake layer that verifies bundle identity, manifest SHA, every file SHA/size, safe paths, renderer pin, and asset collisions, then stages daily binary assets.

Static assets plus validated daily assets form one Resolved Runtime Asset Registry. Validator and compiler must receive the same registry. Renderer components, Visual Grammar, Stage Shell, Shot Renderer, and SpecAssetLayer are not redesigned.

## Collision rule

- same asset ID + same bytes: reuse static asset;
- same asset ID + different bytes: fail closed;
- new asset ID: register as daily handoff asset.

## Security and execution

- no generic web search in resolver;
- no external fetch from Remotion;
- no image generation from Actions/Codex/Remotion;
- no arbitrary React/CSS/dynamic import;
- no path escape;
- all binary assets SHA-256 bound;
- PR CI performs deterministic tests only;
- paid TTS is only used by explicit Preview dispatch;
- final rendering remains unauthorized until the user explicitly requests it.

## Definition of Done

The workstream is complete when the 2026-08-06 formal baseline is frozen; handoff assets reach the renderer through an immutable verified Artifact; one runtime registry is shared by validator and compile; exact-locator Visual Source resolution fails closed; selected assets alone enter production; static-only regression passes; a same-story A/B Preview is produced; and final remains blocked pending explicit user authorization.
