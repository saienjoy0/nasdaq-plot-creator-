# Financial Renderer Compatibility Contract v1.0.0

## Purpose

This contract closes the structural boundary between the selected Financial Recipe Plan produced by `nasdaq-plot-creator-` and `render_spec 2.3.0` consumed by `saienjoy0-nasdaq-cafe-remotion`.

It does not change editorial meaning. It records and validates the exact version tuple and completes the fixed Template configuration required by the renderer.

## Compatibility matrix

Both repositories store the same JSON object:

```text
matrixId: financial-visual-compat-2026-08
status: pass
Plot Intent: 1.1.0
Plot Recipe Plan: 1.0.0
Plot Final Episode Contract: 1.0.0
Renderer render_spec: 2.3.0
Renderer Template Registry: 1.0.0
Renderer Financial Trace: 1.0.0
```

The object must match exactly. A newer or older version is not accepted by implication.

## Renderer TemplateConfig completion

Every selected financial Beat now contains the complete 2.3.0 Template config:

```json
{
  "variant": "zero-baseline",
  "comparisonBasis": "same entity, period, currency and unit",
  "dataBasis": "financial-recipe-plan",
  "nodeOrder": [],
  "laneLabels": [],
  "outcomeNodeId": null,
  "displayOrder": ["expected", "actual", "gap"],
  "metricIds": ["expected", "actual", "gap"],
  "causalStepIds": [],
  "highlightObjectIds": ["gap"]
}
```

For causal financial Templates:

- `nodeOrder` is the selected causal-step order, up to four nodes.
- `outcomeNodeId` is the last selected causal-step ID.
- noncausal Templates use an empty order and `null` outcome.
- `laneLabels` remains empty unless a later versioned contract adds editor-approved labels.

No renderer field is inferred from narration.

## SHA binding

The exact compatibility matrix SHA-256 is written to:

- production consistency report
- Financial Visual Consistency Report
- official execution preflight artifacts
- official execution preflight financial metadata

The preflight also records the matrix ID. A stale or modified matrix stops the cross-artifact step.

## Validation

R3A verifies:

- the compatibility matrix exactly matches the approved tuple
- requested renderer schema version equals `2.3.0`
- render Template config contains all legacy and financial fields
- compatibility matrix SHA is present in the report and preflight
- a changed renderer version is rejected
- all previous Final Episode, Recipe Compiler and Cross-Artifact tests still pass

## Next

R3B creates one deterministic financial `render_spec 2.3.0` fixture, stores its SHA manifest in both repositories, validates it with the renderer schema/layout/public-view pipeline, and then runs the technical preview handoff path.
