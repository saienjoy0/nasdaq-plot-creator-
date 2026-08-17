# ChatGPT Semantic Freeze

## Purpose

After ChatGPT has finished the market causality, nine Scenes, Fox narration, authored Visual Beats, review result, and other semantic authoring, production must not silently continue from a different semantic source or a different edition of the 01-04 rulebooks.

The semantic freeze binds both the daily semantic source and the exact verified Canon Manifest that defines the four production rulebooks.

## Canonical artifacts

Global semantic canon:

`source-of-truth/canon_manifest.json`

Per episode `YYYY-MM-DD`:

`semantic-freezes/YYYY-MM-DD.json`

Freeze contract v1.1.0 deterministically binds:

- `source-of-truth/canon_manifest.json`
  - exact manifest byte SHA-256
  - the Canon Manifest itself is fail-closed verified before binding
- every sorted `daily-authoring-parts/YYYY-MM-DD/*.json`
  - exact file SHA-256
  - canonical JSON semantic SHA-256
- `daily-inputs/YYYY-MM-DD/daily_source_package_YYYY-MM-DD.md`
  - exact file SHA-256
- one aggregate `sourceSetDigestSha256` that includes the Canon Manifest binding

There is no timestamp. Identical source content and identical canon produce identical manifest bytes.

## Authoring sequence

1. Verify the global canon: `python3 scripts/canon_manifest.py verify`.
2. ChatGPT finishes the semantic authoring parts and daily source package.
3. Create the freeze: `python3 scripts/chatgpt_semantic_freeze.py --repo-root . create --date YYYY-MM-DD`.
4. Commit the authoring source and `semantic-freezes/YYYY-MM-DD.json` before requesting production.
5. AI-B `visual_requirements.json` must contain top-level `semanticFreezeSha256` equal to the freeze-file SHA-256.
6. AI-B `visual_intelligence_decision.json` must contain the same `semanticFreezeSha256`.
7. The production request must reference the exact freeze path and SHA.

A Canon Manifest change invalidates an older daily freeze even when the daily authoring JSON itself did not change. Regenerate the freeze from the intentionally selected canon before production; never patch an old freeze by hand.

## Production behavior

`.github/workflows/chatgpt-daily-preview-production.yml` verifies the request-bound semantic freeze before production. `chatgpt_semantic_freeze.py` in turn verifies and binds `source-of-truth/canon_manifest.json`, so the canonical Preview path cannot proceed from stale 01-04 semantics.

The semantic-frozen wrapper also requires Visual Requirements and the Director decision to bind the same freeze SHA and re-verifies the semantic source after downstream production work. Stale bindings use the existing machine-readable safe-pause path.

Since WS-4, Story Engine is validation-only after ChatGPT freeze; it is not a downstream semantic writer. The materializer remains mechanical and may not reinterpret narration, telops, causal meaning, Scene order, or Primary/Fallback selection.

Historical and synthetic canaries may continue to exercise lower-level closures directly where their test contract explicitly permits it. New canonical Preview production uses the freeze-bound path.

Final rendering remains outside this contract and still requires explicit user authorization after Preview review.
