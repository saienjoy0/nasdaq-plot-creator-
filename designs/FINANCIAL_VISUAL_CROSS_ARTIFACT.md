# Financial Visual Cross-Artifact Contract v1.0.0

## Purpose

This phase freezes the selected Financial Recipe Plan into the derived production artifacts without changing editorial meaning.

```text
post-inquisition Episode Package
→ Final Episode Contract
→ deterministic Recipe Plan
→ base spoken script / asset manifest / render spec / preflight
→ selected-plan application
→ financial visual cross-artifact validation
→ rebound render spec / consistency report / preflight
```

The Final Episode Contract and Recipe Plan remain immutable. The selected route is applied only to the derived `render_spec.json`.

## Why the trace is applied after Recipe compilation

The Recipe Plan contains the SHA of the Final Episode Contract, which contains the SHA of the Episode Package. Writing the Recipe Plan SHA back into the Episode Package would create a circular hash dependency. Therefore:

- Episode Package is finalized and SHA-bound first.
- Recipe Plan is compiled second.
- `financialVisualTrace` is added to the derived render spec third.
- updated artifact hashes are fixed in the consistency report and official preflight.

## Selected render fields

For every selected intent, the target Visual Beat is deterministically updated with:

- `screenState`
- `visualTemplate`
- `templateVariant`
- `templateConfig.variant`
- metric and causal-step IDs
- display order
- comparison basis
- highlighted object IDs
- source IDs
- approved start/end cues
- approved preferred or fallback headline and question
- approved return target
- `financialVisualTrace`

The trace contains only the selected plan:

```json
{
  "contractVersion": "1.0.0",
  "intentId": "fvi-aws-expectation-gap",
  "selectedPlanId": "fvp-aws-gap-preferred",
  "selectedPlanSha256": "...",
  "selectedPath": "preferred",
  "recipeId": "earnings-surprise",
  "recipePlanSha256": "...",
  "finalEpisodeContractSha256": "...",
  "sourceIds": ["source-001"],
  "metricIds": ["aws-expected", "aws-actual", "aws-gap"],
  "causalStepIds": [],
  "displayOrder": ["aws-expected", "aws-actual", "aws-gap"],
  "comparisonBasis": "AWS revenue, same quarter and currency",
  "reasonCodes": []
}
```

The following are removed or rejected from the target Beat:

- non-selected Candidate Plan
- preferred/fallback plan IDs as alternatives
- arbitrary component or renderer path
- editor-only Candidate Plan collection

## Fallback diversity gate

When no fallback is selected, a diversity report must be omitted and the result is `not-required`.

When any fallback is selected, compilation stops unless a post-fallback human review report passes all fixed checks:

- at least three screen-state types
- at least two non-analysis Beats
- a major front/back screen change
- no four consecutive identical screen states
- hero-card condition
- return-target confirmation

The report is bound to the exact Recipe Plan SHA.

## Preflight update

After a successful cross-artifact validation, `official_execution_preflight.json` is updated with:

- Final Episode Contract SHA
- Financial Recipe Plan SHA
- financial consistency report SHA
- updated render spec SHA
- updated production consistency report SHA
- diversity report SHA when required
- contract versions
- selection and fallback counts
- zero unresolved states

`preview_authorized` remains true. `final_authorized` is always forced to false.

## CLI

```bash
python scripts/financial_visual_cross_artifact.py \
  --final-contract production/2026-07-31/final_episode_contract.json \
  --recipe-plan production/2026-07-31/financial_recipe_plan.json \
  --repo-root . \
  --production-root . \
  --renderer-schema-version 2.3.0
```

For fallback:

```bash
  --diversity-report production/2026-07-31/financial_visual_diversity_report.json
```

## Non-goals

This phase does not:

- change narration or captions
- choose editorial meaning
- change Expected / Actual / Gap
- create a new fallback
- generate an image
- visually inspect a preview
- authorize final render
- implement Remotion components

Renderer schema and five component implementations are FVU-R1 and FVU-R2.
