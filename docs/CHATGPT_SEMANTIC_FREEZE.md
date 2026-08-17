# ChatGPT Semantic Freeze

## Purpose

After ChatGPT has finished the market causality, nine Scenes, Fox narration, authored Visual Beats, review result, and other semantic authoring, production must not silently continue from a different semantic source.

WS-3 freezes the **committed ChatGPT semantic source**. It does not yet freeze generated `render_spec.json` or the final episode package because the current materializer still contains the Story Engine projection that is removed in WS-4.

## Canonical artifact

For episode `YYYY-MM-DD`:

`semantic-freezes/YYYY-MM-DD.json`

The manifest deterministically binds:

- every sorted `daily-authoring-parts/YYYY-MM-DD/*.json`
  - exact file SHA-256
  - canonical JSON semantic SHA-256
- `daily-inputs/YYYY-MM-DD/daily_source_package_YYYY-MM-DD.md`
  - exact file SHA-256
- one aggregate `sourceSetDigestSha256`

There is no timestamp. Identical source content produces identical manifest bytes.

## Authoring sequence

1. ChatGPT finishes the semantic authoring parts and the daily source package.
2. Create the freeze:

   `python3 scripts/chatgpt_semantic_freeze.py --repo-root . create --date YYYY-MM-DD`

3. Commit the authoring source and `semantic-freezes/YYYY-MM-DD.json` before requesting production.
4. AI-B `visual_requirements.json` must contain top-level:

   `"semanticFreezeSha256": "<SHA-256 of semantic-freezes/YYYY-MM-DD.json>"`

5. AI-B `visual_intelligence_decision.json` must contain the same top-level `semanticFreezeSha256`.
6. The new production request must contain:

```json
{
  "episodeDate": "YYYY-MM-DD",
  "confirmation": "PREVIEW",
  "requestedBy": "ChatGPT",
  "semanticFreeze": {
    "path": "semantic-freezes/YYYY-MM-DD.json",
    "sha256": "<same manifest SHA-256>"
  }
}
```

Only the production-request commit triggers the canonical Preview workflow.

## Production behavior

`.github/workflows/chatgpt-daily-preview-production.yml` verifies the request-bound manifest before production and calls `run_semantic_frozen_renderer_closure_v12.py` rather than calling the legacy closure directly.

The semantic-frozen wrapper:

- verifies the committed freeze before the v1.2 closure;
- requires existing Visual Requirements to bind the same freeze SHA;
- requires the Director decision to bind the same freeze SHA;
- converts stale AI-B bindings into the existing machine-readable safe-pause actions;
- runs the unchanged v1.2 closure;
- verifies the semantic source again after all derived production work.

Because Visual Intelligence already stores the SHA of `visual_requirements.json` in its final package lineage, the freeze binding flows into the existing package without creating a second state machine.

## Deliberate WS-3 boundary

WS-3 does **not** claim that the current generated `render_spec.json` or episode package is already immutable semantic truth. The current `materialize_daily_episode.py` still invokes Story Engine projection. Removing that second semantic-authority path is WS-4. After WS-4, the freeze can be extended to the final projected episode/render artifacts without creating conflicting authorities.

Historical and synthetic canaries may continue to call `run_daily_renderer_closure_v12.py` directly. The freeze requirement is mandatory only for the canonical new production Preview entrypoint.

Final rendering remains outside this contract and still requires explicit user authorization after Preview review.
