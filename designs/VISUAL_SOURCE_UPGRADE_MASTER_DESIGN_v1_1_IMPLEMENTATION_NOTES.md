# Visual Source Upgrade v1.1 — Implementation Notes

Status: implementation authority for the Visual Source Upgrade workstream.

## Reuse-first / adopt-before-build

Before adding a component, search the current repository, prior merged PRs, and the paired Remotion repository for an equivalent contract, validator, builder, state transition, asset transport, or rendering primitive. Prefer, in order:

1. use the existing implementation unchanged;
2. extend the existing implementation with a backward-compatible field or adapter;
3. copy/adapt a proven mechanic already present in this project;
4. only then add a new implementation when no compatible mechanic exists.

Do not create a second Visual Director, a second daily state machine, a second production package, a second Visual Grammar, or a second asset manifest.

## Existing mechanics that are authoritative

- Story Engine and 01–04 own editorial meaning.
- Final Episode Contract owns post-inquisition production intent.
- `assets_resolved` remains the daily lifecycle boundary for asset resolution.
- Final Production remains the only production artifact builder.
- Existing immutable Renderer Handoff remains the transport package.
- Remotion `NasdaqCafeSpec` remains the only production renderer.
- Existing Visual Grammar, Financial Visual, Stage Shell, Shot Renderer, SpecAssetLayer and asset placements remain authoritative.

## Only new responsibilities

- Visual Source Intent extension on the Final Episode Contract.
- Exact-locator Visual Asset Resolver; no generic search.
- Plot-side `asset_resolution_log.json` provenance.
- Full immutable handoff bundle intake in Remotion Actions.
- One resolved runtime asset registry shared by validator and compiler.

## Delivery order

1. PR-0 — formal 2026-08-06 baseline.
2. PR-1 — renderer full handoff intake.
3. PR-2 — Visual Source contract and resolver.
4. PR-3 — same-story A/B preview fixture and production path.

Final rendering remains blocked until the user explicitly requests it.
