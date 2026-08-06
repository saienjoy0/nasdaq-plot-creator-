# Final Episode Contract v1.1.0

## Purpose

This contract mirrors the post-inquisition Episode Package as a machine-readable source for deterministic validation and later compilation.

Version 1.1.0 closes two approved editorial boundaries without allowing code to decide meaning:

- Financial Visual Intent targets with complete preferred/fallback Candidate Plans
- explicit Beat-level Visual Grammar declarations and transitions

The human-readable `episode_package_YYYY-MM-DD.md` remains the editorial source of truth. `final_episode_contract.json` is its machine-readable mirror. A separate Visual Grammar sidecar is required as a byte-semantically identical transport mirror, not as an independent place to edit editorial decisions.

## Position

```text
validated causal dossier
→ 02 editorial decision
→ 01 fox narration
→ 03 nine-scene Episode Package
→ 04 inquisition and revision
→ post-inquisition final Episode Package
→ explicit Visual Grammar on every Visual Beat
→ approved Financial Visual Intent targets
→ complete preferred/fallback Candidate Plans
→ Final Episode Contract 1.1.0 validator
→ Recipe Compiler / render_spec compiler
→ Beat-level Final Contract to render_spec closure check
```

This phase does not select preferred or fallback and does not select a Visual Grammar. Those decisions must already exist in the post-inquisition Episode Package.

## Markdown contract

Every Visual Beat represented by the Final Episode Contract has exactly one deterministic marker:

```html
<!--VISUAL_BEAT:scene-04:vb-04-02-->
```

### Visual Grammar Annex

The Episode Package contains exactly one Visual Grammar Annex:

````markdown
<!--BEGIN_VISUAL_GRAMMAR_ANNEX-->
```json
{
  "episodeDate": "2026-07-31",
  "visualGrammarContractVersion": "1.0.0",
  "expectedConfirmed": true,
  "scene5CausalExceptionReason": null,
  "scenes": []
}
```
<!--END_VISUAL_GRAMMAR_ANNEX-->
````

The annex must be semantically identical to both:

- the referenced Visual Grammar sidecar file
- the Beat-level Visual Grammar projection in `final_episode_contract.json`

### Financial Visual Annex

The Episode Package also contains exactly one Financial Visual Annex:

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

The annex must be semantically identical to `final_episode_contract.json.financialVisuals`.

Neither annex is shown in narration or the public render.

## Machine-readable files

Recommended paths:

```text
production/YYYY-MM-DD/final_episode_contract.json
production/YYYY-MM-DD/visual_grammar_sidecar.json
```

The Final Episode Contract fixes:

- Episode Package repository-relative path and SHA-256
- Visual Grammar sidecar repository-relative path and SHA-256
- episode date
- post-inquisition approval state
- Visual Grammar contract version
- whether Expected was confirmed
- explicit Scene 5 causal-exception reason when applicable
- source registry
- exactly Scene 1–9
- globally unique Visual Beat IDs
- human-facing preferred and fallback headline/question/cues/return target
- explicit Visual Grammar, transition role, and return target on every Beat
- approved Financial Visual Intent bindings
- complete preferred and fallback Candidate Plans

## Visual Grammar boundary

Every Visual Beat must declare:

```json
{
  "visualGrammar": {
    "contractVersion": "1.0.0",
    "grammarId": "gap",
    "transitionRole": "major-shift",
    "returnTargetBeatId": null
  }
}
```

Rules:

- `grammarId` must be one of the versioned Visual Grammar 1.0.0 IDs.
- `transitionRole` must be explicit.
- `return` requires an existing `returnTargetBeatId`.
- non-return transitions require `returnTargetBeatId = null`.
- Scene number, narration, metric sign, Template, and renderer output must never be used to infer a missing Grammar.
- the sidecar must pass the existing semantic diversity and required-Scene checks.

After `render_spec 2.4.0` is generated, `scripts/visual_grammar_contract_closure.py` compares Final Episode Contract and render spec by explicit Scene/Beat ID. The following must match exactly:

- Visual Beat set
- `grammarId`
- `transitionRole`
- `returnTargetBeatId`
- episode date

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

At this phase every Financial Visual Intent must have:

```text
status = approved
compilerSelection = not-run
selectedPlanId = null
selectedRecipeId = null
selectedVisualTemplateId = null
fallbackDiversityRecheck = not-run
```

Manual pre-selection is rejected. The Recipe Compiler is the only component allowed to freeze the selected path from the two pre-approved plans.

Visual Grammar is different: it is not selected by the Recipe Compiler or Renderer. It is already an editorial decision and must be fixed before compilation.

## Validation rules

1. Episode Package exists under the repository root and SHA-256 matches.
2. Visual Grammar sidecar exists under the repository root and SHA-256 matches.
3. Financial Annex appears exactly once and mirrors `financialVisuals`.
4. Visual Grammar Annex appears exactly once and mirrors the sidecar.
5. Visual Grammar sidecar mirrors the Final Episode Contract Beat declarations.
6. Visual Grammar sidecar passes the versioned semantic contract and structural diversity checks.
7. Scene IDs are exactly `scene-01` through `scene-09`.
8. Every declared Visual Beat marker appears exactly once in Markdown.
9. Every Visual Beat has explicit Visual Grammar and transition data.
10. Every `return` target resolves to an existing Visual Beat.
11. Every Financial Visual Intent target resolves to one declared Scene/Beat pair.
12. Every intent is `approved` and remains uncompiled.
13. Every metric and causal-step source is declared by the intent and source registry.
14. Every intent has exactly one referenced preferred plan and one referenced fallback plan.
15. Candidate Plan target, path, intent, metrics, steps, display order, highlights, sources, and URI references agree.
16. Candidate Plans contain no arbitrary component, React, CSS, path, URL, or dynamic import fields.
17. Unreferenced third plans are rejected. There is no automatic third fallback.
18. Final Episode Contract and `render_spec 2.4.0` must carry the same Beat-level Visual Grammar declarations.
19. A PASS proves structural consistency only; it does not prove the editorial interpretation is correct.

## CLI

Validate the Final Episode Contract:

```bash
python scripts/final_episode_contract.py \
  production/2026-07-31/final_episode_contract.json \
  --repo-root .
```

Audit the VG-1 closure:

```bash
python scripts/visual_grammar_contract_audit.py \
  --repo-root . \
  --output reports/visual_grammar_contract_audit.json
```

Verify Final Contract to render spec closure:

```bash
python scripts/visual_grammar_contract_closure.py \
  --final-episode-contract production/2026-07-31/final_episode_contract.json \
  --render-spec render-specs/2026-07-31/render_spec.json
```

## Non-goals

This contract does not:

- select the lead story
- create Expected values
- infer causality
- choose a Visual Grammar
- rewrite narration or telops
- choose a Recipe or Visual Template
- generate images
- invent a return target
- generate `render_spec.json`
- call Remotion
- run preview or final

The next implementation phase is the deterministic Plot-side A/B Input Package compiler. It may only translate already approved editorial decisions into explicit baseline and candidate render inputs.
