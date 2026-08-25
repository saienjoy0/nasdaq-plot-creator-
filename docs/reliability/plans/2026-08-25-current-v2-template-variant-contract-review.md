# Current-v2 Template Variant Contract — Architecture Review Addendum

This addendum refines only the Renderer implementation owner in `2026-08-25-current-v2-template-variant-contract.md`. The root cause, protected semantic ownership, Plot repair, RED evidence, and E2E criteria are unchanged.

## New evidence after RED

Renderer PR #178 produced the intended RED in Visual Story Engine CI run `32793533011`: all prior typecheck/workflow/schema/render-spec/Visual Director tests reached the new test, then `test-candidate-static-soundness.ts` failed only on `Candidate Builder must never expose a template variant that is not registered for that template`.

Repository search shows `assertStaticTemplateSoundness` is already shared by:
- `src/spec/visual-candidate-builder.ts` before a Candidate is exposed;
- `src/spec/validate-render-layout.ts`;
- `src/spec/preflight-static-viewer-layout.ts`;
- existing contract/handoff tests.

Therefore a Candidate-Builder-only membership check would duplicate a static legality invariant that naturally belongs in the existing shared soundness guard.

## Refined Renderer file map

| File | Action | Responsibility |
|---|---|---|
| `scripts/test-candidate-static-soundness.ts` | keep RED regression | Prove `verification-matrix/default` cannot survive Candidate construction |
| `src/spec/static-template-soundness.ts` | modify | Use the existing `VISUAL_COMPONENT_REGISTRY` descriptor for `beat.visualTemplate` and reject `templateConfig.variant` when it is outside `descriptor.variants` |
| `src/spec/visual-candidate-builder.ts` | no production change required unless tests prove otherwise | Its existing `try/catch` around `assertStaticTemplateSoundness` will mechanically drop the illegal Candidate |

## Refined implementation

At the start of `assertStaticTemplateSoundness`:
1. resolve `const descriptor = getVisualComponentDescriptor(beat.visualTemplate)`;
2. resolve the existing authored variant from `beat.templateConfig.variant`;
3. fail with a path-local error if `descriptor.variants` does not include it.

This must not substitute `descriptor.defaultVariant`; it validates only. Therefore it cannot choose semantic meaning.

## Why this is smaller and safer

- one existing shared guard owns static template legality;
- Candidate Builder already converts static-soundness failure into Candidate exclusion;
- layout/preflight paths gain the same early protection automatically;
- no new registry, fallback, or semantic decision is added;
- the official validator remains unchanged and continues to be the final authority.

All original GREEN/SUITE/E2E and real-day verification requirements remain mandatory.