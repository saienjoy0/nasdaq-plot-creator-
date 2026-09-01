# Pre-VI Template Variant Ownership Repair — 2026-08-25

## First failed boundary

Current Preview semantic readiness, before Visual Intelligence Candidate Catalog / Director selection.

## Symptom

The real 2026-08-17 authoring closure rejected two `verification-matrix` Beats because no explicit semantic variant had been authored:

- `scene-03-beat-002`
- `scene-08-beat-001`

Allowed final variants are `reported-sequence` and `strengthen-vs-weaken`.

## Root cause

The Current v1.2 temporal contract assigns Candidate selection to the Visual Director after Candidate Catalog generation:

`Requirements -> Candidate Catalog -> Director semantic -> compile -> Critic semantic -> PASS`.

The pre-VI Daily Authoring Closure was nevertheless calling the strict final template-variant validator. That forced the semantic multi-variant choice before Candidate Catalog existed and created dual ownership between Daily Authoring and the Visual Director.

## Repair design

Split validation by boundary:

- **Pre-VI authoring:** single-variant templates remain deterministic; a semantic multi-variant template may be unresolved (`null`/missing or materializer placeholder `default`) until the Visual Director chooses a Candidate. If authoring explicitly supplies a variant, it must already be registered.
- **Final Renderer normalization:** remains strict. Unresolved or mismatched multi-variant values are rejected and no content-based inference is permitted.

The final normalizer continues to call the strict `validate_authored_variant`. Only `validate_chatgpt_daily_authoring_closure.py` uses the new pre-VI validator.

## Regression evidence

RED before implementation:

- `test_pre_vi_multi_variant_template_may_defer_variant_to_visual_director` failed.
- `test_pre_vi_default_placeholder_may_defer_variant_to_visual_director` failed.
- 81 other closure/Renderer compatibility tests passed.

Additional contract tests preserve final strictness for missing/default/mismatched `verification-matrix` variants.

## Repair hygiene incident

An intermediate full-file replacement accidentally removed the legacy `validate_or_raise()` compatibility API and altered unrelated financial-binding validation. The file was restored byte-for-byte from the RED baseline commit and the intended ownership change was reapplied as exactly one validator-call substitution. This is why the final repair must be reviewed relative to the RED baseline, not the intermediate commit.

## Non-goals

- No change to 2026-08-17 editorial meaning.
- No hand-authored variant patch in daily authoring.
- No change to Candidate selection ownership.
- No weakening of final Renderer validation.
- No Preview or Final render authorization.
