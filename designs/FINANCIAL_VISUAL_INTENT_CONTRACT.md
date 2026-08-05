# Financial Visual Intent Contract v1.0.0

## Purpose

This contract bridges the approved episode package and the renderer without allowing deterministic code to invent editorial meaning.

It records an already decided financial visual intent and deterministically answers only one question:

> Does the supplied evidence shape qualify for the requested financial recipe, or must the declared safe fallback recipe be used?

It does not select the lead story, create Expected values, infer causality, choose a Scene from narration text, generate images, select a renderer component, or emit a Remotion `visualTemplate`.

## Position in the production flow

```text
causal research dossier
→ editorial decision
→ fox narration
→ nine-scene episode package
→ entertainment inquisition
→ approved Financial Visual Intent
→ deterministic recipe eligibility compiler
→ final production package contract
→ explicit Visual Template candidate plan
→ render_spec
→ renderer handoff
```

The contract is intentionally independent in this first implementation. The current materialized 03/04 source-of-truth files and the renderer are unchanged. Episode Package and Visual Beat integration belongs in the Final Production Package Contract phase.

## Intent, recipe, and Visual Template are different layers

The following concepts must not be collapsed into one field.

```text
Financial Visual Intent
= what the approved episode needs to communicate

Financial Visual Recipe
= which validated financial composition is eligible

Visual Template
= the fixed renderer template that Remotion will actually draw
```

This v1.0.0 contract outputs only a **recipe decision**. A recipe ID is not a renderer `visualTemplate` ID and must never be copied directly into `render_spec.json` unless a later, versioned registry explicitly maps an approved candidate plan to that template.

Examples of recipe IDs that are not yet renderer template IDs in this phase:

- `market-pulse-grid`
- `earnings-surprise`
- `dual-asset-split`
- `macro-pressure`
- `source-receipt`
- `expected-anchor`
- `split-opposition`
- `causal-build`

Arbitrary `visualTemplate`, React component, CSS, renderer path, module name, external URL, or dynamic import fields are rejected as unknown input.

## Intent kinds

| kind | preferred recipe | safe fallback recipe |
|---|---|---|
| `market-snapshot` | `market-pulse-grid` | `opening-contradiction` |
| `expectation-gap` | `earnings-surprise` | `expected-anchor` |
| `entity-divergence` | `dual-asset-split` | `split-opposition` |
| `macro-transmission` | `macro-pressure` | `causal-build` |
| `source-evidence` | `source-receipt` | `news-media` |

Recipe pairs are fixed. Arbitrary recipes are not accepted.

## Key safety rules

1. Only an `approved` intent may select the preferred financial recipe.
2. `proposed` intents compile to the declared fallback only in this isolated v1.0.0 compatibility contract. Final Production Package integration will reject unresolved `proposed` status.
3. All metric and causal-step sources must be declared in the top-level `sourceIds`.
4. `verified-series-only` requires actual `verified-intraday-series` precision.
5. Close-only data may drive numbers, grids, and comparison bars, but never an invented price line.
6. Expected and Actual must have the same non-null unit, currency, period, and entity before `earnings-surprise` is eligible.
7. Gap must numerically equal Actual minus Expected.
8. Entity divergence requires different entities, the same session date, and the same unit.
9. Macro transmission requires one macro anchor and two to four sourced causal steps.
10. Validation PASS proves structural consistency only; it does not prove the market interpretation is correct.
11. Compile output contains recipe eligibility only. It must not contain `visualTemplate`, `selectedVisualTemplate`, component names, CSS, paths, or renderer imports.
12. A later Candidate Plan contract must bind the approved recipe to one explicitly declared Visual Beat and one allowlisted Visual Template before render-spec generation.

## CLI

```bash
python scripts/financial_visual_intent.py validate intent.json
python scripts/financial_visual_intent.py compile intent.json --output recipe_plan.json
```

Example compiled output:

```json
{
  "contractVersion": "1.0.0",
  "intentId": "fvi-aws-expectation-gap",
  "kind": "expectation-gap",
  "eligibility": "eligible",
  "selectedRecipe": "earnings-surprise",
  "fallbackRecipe": "expected-anchor",
  "reasons": []
}
```

The absence of a Visual Template field is intentional.

## Initial integration boundary

This implementation does not modify:

- source-of-truth 01–04
- causal research dossier schemas
- episode package
- Visual Beat schema
- render spec
- renderer
- memory retrieval or promotion

The next integration step is to add approved Financial Visual Intent targets and preferred/fallback Candidate Plans to the final Episode Package / Production Package contract. That later phase must verify that the selected recipe, selected Visual Template, source IDs, Scene ID, Visual Beat ID, cues, comparison basis, and return target agree across the Episode Package mirror, recipe plan, and render spec.
