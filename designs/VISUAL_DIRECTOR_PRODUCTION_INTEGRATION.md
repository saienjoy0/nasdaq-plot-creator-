# Visual Director production integration

Visual Director is a pre-freeze selection layer. Plot owns the production
orchestration and Remotion owns Candidate Builder, plan validation, compilation,
and Protected Semantic Diff.

```text
strict post-Story render
→ pinned Remotion Candidate Builder
→ working/YYYY-MM-DD/visual_candidate_catalog.json
→ ChatGPT candidate-ID-only selection
→ working/YYYY-MM-DD/visual_direction_plan.json
→ pinned Remotion compiler + Protected Semantic Diff
→ existing referential / visual / renderer gates
→ immutable handoff freeze
```

New `production_request.json` files bind Visual Director contract `1.0.0` as
required. The two immutable acceptance renderer commits that predate the
Visual Director core remain an explicit migration allowlist; every other
renderer commit requires the binding. If the plan does not exist, production deliberately stops with
`E_VISUAL_DIRECTION_PLAN_REQUIRED` after persisting the exact input and catalog.
No default candidate is chosen. Re-running against the same pinned renderer and
strict input recompiles only after the plan's catalog SHA and candidate IDs pass.

The immutable Remotion 2.4 handoff includes the candidate catalog, direction
plan, and compile report. The preflight binds the compile report SHA and the
report must contain `semanticDiff: PASS`.

Visual Source Primary/Fallback decisions are frozen per Intent. The episode
summary path is `primary`, `fallback`, or `mixed`; each route and selected asset
retains its own Intent-level path. The legacy episode-wide selection remains
accepted for existing fixtures and explicitly uniform decisions.

The 2026-08-10 episode remains a Golden acceptance fixture. Generic production
logic never branches on its date, companies, or news content.
