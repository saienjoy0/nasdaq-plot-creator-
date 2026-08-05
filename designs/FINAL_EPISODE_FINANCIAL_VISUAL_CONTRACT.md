# Final Episode Financial Visual Contract v1.0.0

## Purpose

This contract adds approved Financial Visual Intent targets and complete preferred/fallback Candidate Plans to the post-inquisition Episode Package without allowing deterministic code to decide editorial meaning.

The human-readable `episode_package_YYYY-MM-DD.md` remains the editorial source of truth. `final_episode_contract.json` is a machine-readable mirror used only for validation and later compilation.

## Position

```text
validated causal dossier
→ 02 editorial decision
→ 01 fox narration
→ 03 nine-scene Episode Package
→ 04 inquisition and revision
→ post-inquisition final Episode Package
→ approved Financial Visual Intent targets
→ complete preferred/fallback Candidate Plans
→ Final Episode Contract validator
→ Recipe Compiler (next phase)
```

This phase does not select preferred or fallback. It proves both routes are complete before selection.

## Markdown contract

Every Visual Beat represented in the sidecar has one deterministic marker:

```html
<!--VISUAL_BEAT:scene-04:vb-04-02-->
```

The Episode Package contains exactly one Financial Visual Annex:

````markdown
<!--BEGIN_FINANCIAL_VISUAL_ANNEX-->
```json
{
  "annexVersion": "1.0.0",
  "intents": [],
  "candidatePlans": []
}
```
<!--END_FINANCIAL_VISUAL_ANNEX-->
````

The annex must be semantically identical to `final_episode_contract.json.financialVisuals`. It is not shown in narration or the public render.

## Sidecar

Recommended path:

```text
production/YYYY-MM-DD/final_episode_contract.json
```

The sidecar fixes:

- Episode Package repository-relative path and SHA-256
- episode date
- post-inquisition approval state
- source registry
- exactly Scene 1–9
- globally unique Visual Beat IDs
- human-facing preferred and fallback headline/question/cues/return target
- approved Financial Visual Intent bindings
- complete preferred and fallback Candidate Plans

## Candidate Plan

A Candidate Plan is a complete possible screen route. It includes:

- recipe ID
- allowlisted Visual Template ID
- variant
- target Scene and Visual Beat
- screen state
- selected metrics and causal steps
- display order
- comparison basis
- highlighted objects
- headline/question/cue/return references
- source IDs

Fallback is not a bare template name. Its human-facing text, displayed objects, comparison basis, cues, and return target must already be complete.

## Production boundary

At this phase every intent must have:

```text
status = approved
compilerSelection = not-run
selectedPlanId = null
selectedRecipeId = null
selectedVisualTemplateId = null
fallbackDiversityRecheck = not-run
```

Manual pre-selection is rejected. The later Recipe Compiler is the only component allowed to freeze the selected path from the two pre-approved plans.

## Validation rules

1. Episode Package exists under the repository root and SHA-256 matches.
2. Financial Annex appears exactly once and mirrors the sidecar.
3. Scene IDs are exactly `scene-01` through `scene-09`.
4. Every declared Visual Beat marker appears exactly once in Markdown.
5. Every intent target resolves to one declared Scene/Beat pair.
6. Every intent is `approved` and remains uncompiled.
7. Every metric and causal-step source is declared by the intent and source registry.
8. Every intent has exactly one referenced preferred plan and one referenced fallback plan.
9. Candidate Plan target, path, intent, metrics, steps, display order, highlights, sources, and URI references agree.
10. Candidate Plans contain no arbitrary component, React, CSS, path, URL, or dynamic import fields.
11. Unreferenced third plans are rejected. There is no automatic third fallback.
12. A PASS proves structural consistency only; it does not prove the editorial interpretation is correct.

## CLI

```bash
python scripts/final_episode_contract.py \
  production/2026-07-31/final_episode_contract.json \
  --repo-root .
```

## Non-goals

This contract does not:

- select the lead story
- create Expected values
- infer causality
- rewrite narration or telops
- choose a Recipe or Visual Template
- generate images
- generate `render_spec.json`
- call Remotion
- run preview or final

The next phase is Financial Recipe Eligibility Compiler v1.1.0.
