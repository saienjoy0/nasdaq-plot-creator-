# Public headline budget pre-Freeze repair

**Status:** `CASCADE_DETECTED` / `ARCHITECTURE_REVIEW_REQUIRED` completed before repair.

**Root cause:** Daily Authoring v2 accepts any non-empty `production.scenes[*].headline`, so Renderer-only public layout validation is the first place that rejects a 27+ character headline. The immutable 2026-08-17 Semantic Freeze therefore carried Scene 1 and Scene 2 headlines that cannot fit the public headline surface.

**First broken boundary:** `DAILY_AUTHORING` ownership defect, observed late at the `RENDER_SPEC` public-layout validator during `build-production`.

**Evidence:**

- The exact Current facade with Renderer `e7e9980ce0b941967cdc86ef396bb216109a9bf9` passes Visual Intelligence, including Scene 9 `final-assembly`, then fails `build-production` with `$.scenes[0].headline[line 1]: 27 characters exceed headline limit 26`.
- Running the official Renderer validator against the exact compiled visual reproduces the same error.
- Daily Authoring Scene 1 is 27 characters and Scene 2 is 28 characters; both pass the current Authoring schema because `headline` has only `minLength: 1`.
- `validate_editorial_semantic_boundary.py::validate_boundary` validates the Authoring schema before acceptance/Freeze creation. The schema and its hash are already part of `contractBindings`, so this is the existing owning gate rather than a new validator chain.
- Renderer `preflight-static-viewer-layout.ts` defines the production analogue: public headline is one line with a 26-character limit.

**Why existing tests missed it:** Editorial Semantic Boundary tests cover required presentation fields, variants, story alignment, stale acceptance, and Freeze linkage, but no test sends a Renderer-unsafe public headline through the real boundary. Synthetic fixtures use short `Scene N` headlines, so Exact Cross-Repo E2E never exercises this text-budget edge.

**Goal:** Reject Renderer-unsafe public headlines before Editorial Semantic Acceptance and Semantic Freeze, then re-author only the two over-budget 2026-08-17 headline surfaces without changing market meaning, numbers, narration, evidence, or Scene roles.

**Protected invariants:**

- 01–04 meaning, causal dossier, Story Plan, narration, evidence, confidence, chronology, Scene order, and Visual Beat meaning do not change.
- Scene 1 retains both exact percentage values; Scene 2 retains the beat-and-raise result and the contradictory negative price reaction.
- Renderer remains the final public-layout authority; Authoring adds an earlier compatible input constraint, not a second state machine or fallback.
- Existing Semantic Freeze identity is regenerated because the owning editorial source and contract binding intentionally change; production never mutates a sealed Freeze in place.
- Visual Director/Critic semantics and exact Renderer binding remain unchanged.
- No automatic Final is run.

## Current code path

```text
Daily Authoring v2
→ scripts/validate_editorial_semantic_boundary.py::validate_boundary
→ validate_daily_authoring_schema
→ Editorial Semantic Acceptance
→ scripts/chatgpt_semantic_freeze.py
→ scripts/current_production_facade_v12.py
→ scripts/run_semantic_frozen_renderer_closure_v12.py
→ scripts/run_daily_renderer_closure_v12.py
→ Visual Intelligence compiled RenderSpec
→ build-production
→ Renderer loadRenderSpec / static-viewer preflight (first current rejection)
```

## Working analogue

Renderer `src/spec/preflight-static-viewer-layout.ts` applies a literal 26-character, one-line limit to every public `headline`. Plot already uses JSON Schema at the pre-Freeze semantic boundary for other Authoring presentation invariants, and acceptance binds that schema by SHA. The compatible analogue is therefore a JSON Schema `maxLength`, not another runtime check in `build-production`.

## Repair hypothesis

I think the absent `maxLength` on the pre-Freeze Daily Authoring headline contract is the root cause because both invalid headlines pass Authoring and fail unchanged at Renderer, and adding `maxLength: 26` should make the real semantic boundary reject the incident shape before Freeze without changing any protected semantics.

## File map

| File | Action | Responsibility | Why this file owns the change |
|---|---|---|---|
| `tests/editorial-semantic-boundary/test_current_contract_e2e.py` | modify | Exercise the real semantic boundary with literal 26- and 27-character public headlines | This is the same pre-Freeze validator production uses and proves observable accept/reject behavior |
| `contracts/chatgpt_daily_authoring_v2.schema.json` | modify | Bound the public Scene headline to Renderer-safe length | It is the existing source contract and is already bound into acceptance/Freeze identity |
| `daily-authoring/2026-08-17.json` | modify | Shorten only Scene 1 and Scene 2 public headline surfaces | These are the two confirmed over-budget source values |
| `verification/2026-08-17/editorial_semantic_acceptance.json` | regenerate | Bind the updated Authoring and schema bytes after validation | Existing acceptance must become stale when either input or contract changes |
| `semantic-freezes/2026-08-17.json` | regenerate | Seal the newly accepted authoritative inputs | Production must use an immutable Freeze matching the accepted source |
| `docs/reliability/incidents/2026-08-25-current-v2-parity-cascade.md` | append | Record the newly exposed boundary, cause, regression, and canary result | The same real-day request has crossed successive boundaries |

## Task 1: Regression reproduction

Add a behavior test that builds the canonical Current fixture, validates a literal 26-character headline successfully, then changes the same field to a literal 27-character headline and expects `validate_boundary` to reject it at `daily-authoring.production.scenes.0.headline`.

- Command: `/tmp/nasdaq-plot-venv.CH2gTL/bin/python -m pytest tests/editorial-semantic-boundary/test_current_contract_e2e.py -k public_headline`
- RED: the 27-character input is accepted, so the expected exception is not raised.
- GREEN: the 26-character input passes and the 27-character input fails with the schema diagnostic.
- Mutation check: removing or raising `maxLength` makes the 27-character assertion fail again.

## Task 2: Minimal owning-layer repair

Add `"maxLength": 26` to `$defs.scene.properties.headline` only. Do not add a second Python constant or duplicate validator.

Apply the Story Authoring surface-only pass to the two real-day values:

- Scene 1: `NASDAQ -0.28%／AMAT -5.12%` — same two values, compressed separator.
- Scene 2: `AMAT：決算も見通しも予想超え、それでも下落` — Japanese rendering of beat-and-raise plus the same contradictory decline.

Regenerate Editorial Semantic Acceptance and Semantic Freeze through their official scripts; never hand-edit hashes.

## Task 3: Affected-suite and Current E2E verification

```text
/tmp/nasdaq-plot-venv.CH2gTL/bin/python -m pytest tests/editorial-semantic-boundary
/tmp/nasdaq-plot-venv.CH2gTL/bin/python tests/remotion-compat/test_visual_intelligence_v12_state.py
/tmp/nasdaq-plot-venv.CH2gTL/bin/python tests/remotion-compat/run_visual_intelligence_v12_cross_repo.py --renderer-root /tmp/nasdaq-renderer-e7e9980.KHiYJf
/tmp/nasdaq-plot-venv.CH2gTL/bin/python tests/current-spine/run_exact_cross_repo_current_e2e.py --renderer-root /tmp/nasdaq-renderer-e7e9980.KHiYJf
python3 scripts/current_production_facade_v12.py --workspace . --renderer-root /tmp/nasdaq-renderer-e7e9980.KHiYJf closure --episode-date 2026-08-17 --phase compile --semantic-freeze semantic-freezes/2026-08-17.json
```

The real-day canary must pass the repaired headline boundary and continue until Preview, an intentional semantic/human pause, or a newly evidenced first broken boundary.

## Architecture and risk review

- **Architecture review:** successive boundaries came from permissive preproduction fixtures/contracts meeting stricter production closure. This repair aligns the existing Authoring input contract with the existing Renderer public surface; it adds no orchestration layer.
- **Ownership:** headline wording remains ChatGPT-authored; the schema owns admissible public-surface shape; Renderer retains final enforcement.
- **Duplicate control:** the numeric limit appears once in Plot schema and once in Renderer surface authority because the repositories exchange a public contract. Plot does not introduce another Python constant or validator.
- **Staleness:** schema hash and Authoring bytes intentionally invalidate old acceptance/Freeze; official regeneration restores lineage.
- **Test parity:** the regression enters the same `validate_boundary` used before Freeze, and the real-day canary enters the public Current facade.
- **Human boundary:** no Candidate choice or approval state is automated.
- **Loop:** Scene 2 is corrected in the same source pass because it is already proven over budget and would be the immediate next failure.

## Review / rollback

Review the actual diff against this plan and confirm only the public headline budget, two surface strings, regenerated lineage artifacts, prior Scene 9 semantic/binding work, and incident memory are included. Rollback is a normal revert; no persisted runtime state or Renderer fallback is introduced.

## Cascade follow-up: Editorial Boundary still uses final variant ownership

After the headline regression became GREEN, official Editorial Semantic Acceptance regeneration reached the next first broken boundary:

```text
scene-03-beat-002: verification-matrix requires explicit variant
scene-08-beat-001: verification-matrix requires explicit variant
```

This is `EDITORIAL_ACCEPTANCE`, not a defect in the two real-day Beats. Commit
`6edb0c1` introduced `validate_pre_visual_intelligence_variant()` and the Authoring
Closure correctly uses it, but `validate_editorial_semantic_boundary.py` retained
the final-only `validate_authored_variant()` call. Both gates inspect the same
pre-VI Daily Authoring object, so the latter is a stale duplicate-control call site.

The owning repair is to make Editorial Semantic Boundary use the existing pre-VI
validator. Add a regression to `test_current_contract_e2e.py` that changes a fixture
Beat to `verification-matrix` with no variant and proves `validate_boundary()` accepts
it, then changes the same value to an unregistered variant and proves rejection.
The RED before repair is rejection of the unresolved case; GREEN accepts unresolved
pre-VI ownership while retaining fail-closed validation for an explicit invalid value.

Protected invariants remain unchanged: Candidate Catalog and Visual Director own the
multi-variant semantic decision, final RenderSpec normalization stays strict, and no
default variant is inferred. The affected files are only the real boundary test and
the stale call site in `scripts/validate_editorial_semantic_boundary.py`.

## Cascade follow-up: Director compile omits the static production contract

With the regenerated Freeze, the exact public facade passes Authoring, Story Engine,
Pre-TTS, Visual Intelligence, Scene 9 closure, and the repaired headline budget. The
next first broken boundary is:

```text
$.scenes[7].cards[1].title[line 1]: 29 characters exceed card title limit 18
```

The compiled value is `Company-direct vs NASDAQ-wide`. It originates at Daily
Authoring Scene 8 Beat 2 `primaryElement`, is deterministically projected to
`scene-08-card-002.title`, survives Candidate selection unchanged, and is first
rejected by final `loadRenderSpec()`.

This confirms a broader Renderer strictness drift: Visual Director compile currently
calls only `validateVisualStoryContract`, while final loading also calls Shot Story,
static viewer layout, expression, and viewer-surface preflights. Because this is the
fourth same-family strictness gap, the architecture repair is to extract one pure
static production-contract function and call it from both compile and final load.
Runtime asset-reference validation remains in `loadRenderSpec()` because Director
compile does not receive the resolved runtime asset manifest.

Renderer file map:

| File | Action | Responsibility |
|---|---|---|
| `scripts/test-visual-director-cli.ts` | modify | Build and compile a source with a visible 19-character card-title line; prove the production CLI rejects it |
| `src/spec/validate-render-spec-static.ts` | create | Own the pure Visual Story, Shot Story, static layout, expression, and viewer-surface validation sequence |
| `scripts/load-render-spec.ts` | modify | Use the shared pure validator after schema/reference validation |
| `scripts/visual-director-cli.ts` | modify | Use the same shared pure validator with production closure after Candidate compilation |

RED is Director compile exit 0 for the 19-character title. GREEN is a non-zero exit
with the card-title JSON path; existing local variant and Scene 9 closure regressions
must remain GREEN. Final loader behavior must not change.

The real-day source-only correction is an explicit line break:

```text
Company-direct vs
NASDAQ-wide
```

Each line fits 18 characters and the English boundary labels remain exact. No
causality, narration, evidence, Candidate selection, or card-line values change.
Acceptance and Freeze are regenerated again after that authored surface change.

### Stage-ownership refinement from the real canary

The first shared-validator implementation also invoked expression-asset preflight at
Director compile. The real canary correctly rejected Scene 1 because Plot expands the
expression-specific fox placements only in the later final package materializer.
That is not a valid VI compile requirement.

Refine the common contract into layers: Visual Story + Shot Story + static layout is
the shared pre-final core; final loader alone adds expression-asset and final viewer
preflights. The CLI regression makes Scene 1 use `軽い驚き` without the later
`foxSlightSurprise` placement and requires compile to pass, while the 19-character
card title still must fail. This preserves the real stage boundary instead of moving
a post-finalization gate too early.

## Cascade follow-up: Current materializer drops authored expression assets

After the staged Validator repair, Visual Intelligence compile passes and
`build-production` reaches final expression preflight. It then rejects Scene 1
`軽い驚き` because `materialize_chatgpt_daily_authoring.py::build_scene` hardcodes a
single `foxAnalysis` placement for every Scene.

The working legacy analogue already exists in
`fixup_chatgpt_daily_materialization.py`: it reads the expression→asset authority
from the exact pinned Renderer, collects initial/chunk/event/Shot expressions, and
adds one fixed placement per used asset. Current production intentionally does not
run that legacy fixup, so the projection-only logic must move to the Current
materializer without reintroducing the legacy semantic mutation path.

Add a public materializer regression using a fake pinned Renderer map: a Scene with
`軽い驚き` initial expression and `分析` chunk expression must emit exactly the
`foxSlightSurprise` and `foxAnalysis` fixed placements. RED is the current output's
single hardcoded `foxAnalysis`; GREEN is Renderer-map-driven placement projection.
Unknown authored expressions and duplicate placements remain fail-closed under the
existing expression-projection suite.

Extract only `load_renderer_expression_asset_map` and
`ensure_fox_expression_placements` into a neutral projection helper used by both the
legacy fixup and Current materializer. Do not copy the mapping, infer a fallback, or
run the legacy fixup from Current production.
