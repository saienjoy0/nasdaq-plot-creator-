# PR #10｜Renderer Handoff Bundle

## Purpose

Deliver only validated, date-aligned, resolved production artifacts to the renderer through an immutable SHA-bound bundle.

## Bundle

Each bundle is stored under:

```text
production-bundles/YYYY-MM-DD/<bundle_id>/
```

It contains copied production files, all required asset bytes, and `handoff_manifest.json`. The bundle ID is the SHA-256 of the canonical manifest content before adding the ID.

## Validation gates

- PR #9 preflight PASS and unresolved states zero;
- production consistency PASS;
- render-spec date and renderer schema match;
- selected image path resolved;
- all file and asset SHA values match;
- source and destination paths stay inside their roots;
- renderer repository, contract version, and base commit are pinned.

## Preview/final separation

Preview bundles always set `final_authorized=false` and reject approval records. Final bundles require a final-authorized preflight plus an explicit approved-preview record. There is no automatic preview-to-final transition.

## Verification

Thirty deterministic tests cover missing and stale artifacts, unresolved states, asset/path/SHA attacks, renderer mismatch, final authorization, tampered bundle detection, bundle identity, and idempotent replay.
