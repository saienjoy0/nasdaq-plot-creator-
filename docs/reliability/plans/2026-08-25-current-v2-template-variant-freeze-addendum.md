# Current-v2 Template Variant Contract — Freeze Boundary Addendum

The earlier repair plan is extended after inspecting the authoritative semantic-freeze path.

## Finding

`validate_chatgpt_daily_authoring_closure.py` runs in Renderer closure after the committed Semantic Freeze has already been accepted. Guarding only there would detect bad Authoring earlier than the Renderer validator but would still permit ChatGPT to create an invalid Semantic Freeze in the first place.

The canonical pre-Freeze owner is `scripts/validate_editorial_semantic_boundary.py`; its PASS receipt is required by `scripts/chatgpt_semantic_freeze.py create`.

## Required refinement

Reuse `scripts/remotion_template_variant.py` as the single Python variant-policy source and connect it to both semantic boundaries:

1. Add a small helper that validates an authored `{visualTemplate, variant}` without selecting a variant.
2. `validate_editorial_semantic_boundary.py` calls it for each production Beat before publishing Editorial Semantic Acceptance.
3. `validate_chatgpt_daily_authoring_closure.py` calls the same helper as a runtime parity guard.
4. `materialize_chatgpt_daily_authoring.py` uses the explicit authored variant and then calls the existing RenderSpec normalizer; machine code never selects between semantic variants.
5. The 2026-08-17 Authoring correction is followed by official Editorial Semantic Acceptance regeneration and then `chatgpt_semantic_freeze.py create`; no frozen bytes are silently rewritten by runtime.

## Additional tests

- RED/GREEN at the editorial semantic boundary: missing `verification-matrix` variant cannot produce PASS Acceptance.
- Existing runtime closure RED remains required.
- Freeze verify must PASS against the newly regenerated Acceptance/Authoring bytes.

This makes the correction explicit, lineage-bound, and replayable rather than a post-Freeze compatibility patch.