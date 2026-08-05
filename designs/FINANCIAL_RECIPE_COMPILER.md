# Financial Recipe Eligibility Compiler v1.0.0

## Purpose

The compiler freezes one route from two routes that the editor already completed and approved in the Final Episode Contract.

It never chooses the story, creates Expected values, infers causality, writes narration, selects a new Visual Template, or generates a third fallback.

```text
post-inquisition Final Episode Contract
→ validate Episode Package / Annex / Candidate Plans
→ validate versioned Recipe Registry
→ evaluate preferred data shape
→ preferred eligible: freeze preferred
→ preferred ineligible: freeze the declared fallback with reason codes
→ fallback invalid: stop
→ financial_recipe_plan.json
```

## Inputs

- `final_episode_contract.json`
- `financial_recipe_registry.json`
- Final Episode and Candidate Plan schemas
- the SHA-bound Episode Package referenced by the Final Episode Contract

## Output

Recommended path:

```text
production/YYYY-MM-DD/financial_recipe_plan.json
```

The Recipe Plan records only the selected route for each intent:

- intent, Scene, Visual Beat
- selected path, plan, Recipe, Visual Template, variant and screen state
- source, metric and causal-step IDs
- canonical selected-plan SHA-256
- deterministic reason codes
- whether fallback visual-diversity recheck is required

The unselected plan is not copied into the Recipe Plan.

## Fixed decisions

- `approved` intents only
- Registry version `1.0.0`
- Intent contract version `1.1.0`
- one target Visual Beat per intent for MVP
- preferred/fallback Recipe pairs are fixed per intent kind
- Visual Template must be allowlisted for the declared Recipe
- close-only data never becomes an intraday line
- fallback must be structurally and semantically eligible for its safe role
- fallback invalid means compilation failure, not a third automatic alternative

## Eligibility

### market-snapshot

Preferred requires 3–6 numeric metrics from one session with one unit. Fallback `opening-contradiction` may use 1–4 confirmed metrics.

### expectation-gap

Preferred requires exactly one Expected, Actual and Gap with matching entity, unit, currency and period, and `Gap = Actual - Expected`. Fallback `expected-anchor` omits Gap and uses the pre-approved Expected/Actual display.

### entity-divergence

Both paths require two distinct entities from the same session and unit. If the comparison itself is invalid, fallback is also invalid and compilation stops.

### macro-transmission

Preferred requires one macro anchor and 2–4 sourced causal steps. Fallback `causal-build` may use 2–4 sourced steps without the specialized anchor treatment.

### source-evidence

A source, and at least one displayed metric or causal step, must be declared.

## Fallback diversity

The compiler does not visually judge the finished video. A fallback selection is emitted with:

```text
fallbackDiversityRecheck = required
```

FVU-3 must receive an explicit passing diversity decision before renderer handoff. Preferred selections emit `not-required`.

## CLI

```bash
python scripts/financial_recipe_compiler.py compile \
  production/2026-07-31/final_episode_contract.json \
  --repo-root . \
  --output production/2026-07-31/financial_recipe_plan.json
```
