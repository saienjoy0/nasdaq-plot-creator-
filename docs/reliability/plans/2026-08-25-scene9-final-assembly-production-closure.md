# Scene 9 final-assembly production closure repair

**Root cause:** Renderer `scripts/visual-director-cli.ts` passed `validateVisualStoryContract` to the Visual Direction compiler without production options. The callback therefore used `enforceVariety=false`, accepted a Director plan whose Scene 9 contained `closing-recap` and `conclusion-card` but no `final-assembly`, and emitted a PASS compile report. `build-production` correctly adopted that Critic-approved compiled RenderSpec; the later production `loadRenderSpec()` call used `enforceVariety=true` and rejected the same bytes.

**First broken boundary:** `RENDER_SPEC` — Visual Intelligence compiled-RenderSpec production closure.

**Evidence:**

- Plot run `32870801170`, job `97877047327`, first failed production command:
  `python3 scripts/run_daily_production_v12.py --workspace . build-production --episode-date 2026-08-17 ...`
- Stable downstream diagnostic:
  `E_PACKAGE_MISMATCH: $.scenes[8].visualBeats: Scene 9 requires final-assembly`.
- `visual_intelligence_validation.json` and `visual_direction_compile_report.json` are PASS.
- The artifact `visual_direction_compiled_render.json` has Scene 9 templates
  `closing-recap` and `conclusion-card`; it has no `final-assembly`.
- The Director semantic explicitly selected `vc-scene-09-beat-001-01`
  (`closing-recap`) over `vc-scene-09-beat-001-03` (`final-assembly`).
- Renderer `visual-director-cli.ts` supplies the bare validator callback, while
  production `load-render-spec.ts` explicitly supplies `{enforceVariety: true}`.
- Plot `build_final_production_package_v12.py` loads the SHA-bound compiled visual,
  replaces the legacy strict projection with that exact value, forbids a second
  Director, and checks byte equality. This disproves stale intermediate adoption
  as the cause of this failure.

**Why existing tests missed it:** `test-visual-director-cli.ts` proved that compile invokes the official validator with a template-local invalid variant, but it never exercised a globally invalid yet individually legal Candidate combination. The bare callback catches local Beat/template violations and skips production-only episode closure rules such as Scene 9 `final-assembly`.

**Goal:** Make Visual Director compile use the same production Visual Story closure as final Renderer validation, then correct the 2026-08-17 Director semantic selection so the exact real-day flow can advance beyond `build-production` without changing narration or market meaning.

**Protected invariants:**

- 01–04 editorial meaning, narration, Scene order, evidence, uncertainty, and Visual Beat purposes do not change.
- Visual Director/AI-B continues to own Candidate meaning selection; machine code only validates the completed selection.
- Candidate Catalog may offer multiple legal candidates; Renderer does not auto-select `final-assembly`.
- Critic-approved compiled RenderSpec remains the immutable post-VI visual authority.
- No legacy second Director, visual canonicalizer, or hidden fallback is reintroduced.
- Renderer binding remains exact and moves only to the tested repair commit.
- GitHub Actions remains mechanical; Preview remains separate from explicit Final.

## Current code path

```text
.github/workflows/validate-daily-production-package.yml
→ scripts/current_production_facade_v12.py
→ scripts/run_semantic_frozen_renderer_closure_v12.py
→ scripts/run_daily_renderer_closure_v12.py
→ scripts/run_visual_intelligence_v12.py
→ scripts/visual_intelligence_pipeline_v12.py::prepare_and_compile
→ Renderer scripts/visual-director-cli.ts::compile
→ compileVisualDirection(... validateOutput)
→ validateVisualStoryContract(value)              # currently non-production closure
→ Critic / visual_intelligence_valid PASS
→ scripts/run_daily_production_v12.py::build_production
→ scripts/build_final_production_package_v12.py::_renderer_finalizer_v12
→ exact Critic-approved compiled RenderSpec adoption
→ Renderer loadRenderSpec(... enforceVariety=true) # first rejection
```

## Working analogue

Renderer `scripts/load-render-spec.ts::loadRenderSpec` is the production analogue.
It derives fixture status from the resolved input path and calls
`validateVisualStoryContract(parsed.data, {enforceVariety})`; all non-fixture
production specs therefore receive the full episode closure. Visual Director CLI
compile is itself a production boundary and must call the same full closure, not the
validator's permissive default.

## Repair hypothesis

I think the missing production options on the Renderer Visual Director compile validator are the root cause because the exact compiled artifact lacks `final-assembly` yet passed VI, and changing that callback to enforce full Visual Story variety/closure should reject the bad Director plan before Critic/PASS without changing protected semantics.

## File map

| File | Action | Responsibility | Why this file owns the change |
|---|---|---|---|
| Renderer `scripts/test-visual-director-cli.ts` | modify | Reproduce a globally invalid but Candidate-local-valid Scene 9 plan through the production CLI | Existing regression covers only local variant invalidity and missed this production closure |
| Renderer `scripts/visual-director-cli.ts` | modify | Invoke official Visual Story validation with full production closure after Candidate compilation | This is the first owner that can prevent an invalid compiled visual from becoming VI PASS |
| Renderer `scripts/test-support/current-visual-grammar-fixture.ts` | modify after Exact E2E RED | Make the Renderer-owned Current fixture satisfy Scene 1/8/9 production closure | Exact Cross-Repo E2E must exercise strict production compile with an identity plan, not rely on a locally-valid-only fixture |
| Plot `working/2026-08-17/visual-intelligence/visual_director_decision.semantic.json` | modify | Correct AI-B's real-day Candidate selection to include `final-assembly` | Meaning selection belongs to Director semantic, not build-production or Renderer auto-repair |
| Plot `docs/reliability/incidents/2026-08-25-current-v2-parity-cascade.md` | modify | Append the newly exposed boundary, cause, and regression evidence | The same immutable request has exposed successive contract boundaries |
| Plot `contracts/renderer_binding.json` | modify after Renderer merge | Pin the exact repaired Renderer commit and registry snapshot | Plot production must not float to an unverified Renderer |

## Task 1: Regression reproduction

In Renderer `test-visual-director-cli.ts`, clone the fixture's valid Scene 9
`final-assembly` Candidate into an individually legal `closing-recap` Candidate and
select it so the compiled episode contains no `final-assembly`.

- Command: `node --import tsx scripts/test-visual-director-cli.ts`
- RED before repair: CLI compile exits 0, proving the invalid episode closure is accepted; the regression assertion fails.
- GREEN after repair: CLI compile exits non-zero and includes
  `$.scenes[8].visualBeats: Scene 9 requires final-assembly`.
- Negative protection: the existing local-invalid-variant case must still fail with a JSON-path Visual Story diagnostic; the unmodified valid CLI flow must still pass.

## Task 2: Minimal owning-layer repair

In Renderer `visual-director-cli.ts`, wrap the output validator as:

```ts
validateOutput: (value) => validateVisualStoryContract(value, {enforceVariety: true})
```

Do not change Candidate construction, selection, compiler mutation fields, or final
Renderer validation.

Then update the real 2026-08-17 Director semantic so Scene 9 Beat 1 selects the
existing `final-assembly` Candidate `vc-scene-09-beat-001-03`. Keep Beat 2 as the
quiet `conclusion-card`; this satisfies the Scene-level closure without creating a
second final assembly or changing narration/evidence.

## Task 3: Affected-suite and Current E2E verification

Renderer ladder:

```text
node --import tsx scripts/test-visual-director-cli.ts
npm run test:visual-story
npm run test:visual-templates
npm run test:visual-variety
npm run test:spec
npm run typecheck
npm run lint
npm run build
```

Plot ladder after exact Renderer binding update:

```text
python3 tests/remotion-compat/test_visual_intelligence_v12_state.py
python3 tests/remotion-compat/run_visual_intelligence_v12_cross_repo.py --renderer-root ../renderer
python3 tests/current-spine/run_exact_cross_repo_current_e2e.py --renderer-root ../renderer
```

Finally replay the exact Current public path for 2026-08-17 through
`scripts/current_production_facade_v12.py` (via the repository's validation workflow
or exact local closure command) and continue until Preview or the next first broken
boundary. Do not claim Preview before an actual artifact exists.

## Cascade follow-up: Current fixture production closure

After Renderer PR #183 made compile strict and merged as `6abbf155`, the exact
Cross-Repo E2E failed at the next first boundary:

```text
$.scenes[0].visualBeats: Scene 1 requires opening-contradiction
```

The E2E intentionally imports Renderer `makeCurrentVisualDirectorFixture()` and
selects identity Candidates. The shared fixture therefore has to be a production
episode baseline, not merely a local schema/Registry fixture. Move the temporary
CLI-test specialization into the shared fixture: assign a compatible one-card Beat
to Scene 1 `opening-contradiction`, assign Scene 9 `final-assembly`, and remove the
synthetic Scene ordinal from Scene 9 public numeric-lineage text. Do not relax the
strict validator or special-case fixture paths in production compile.

RED on `6abbf155`: exact E2E rejected the identity plan at Scene 1 closure.
GREEN on the repair commit: exact E2E returned PASS for machine pauses, Critic
binding/seal, package validation, and Preview V4 request validation.
Renderer PR #184 merged as `e7e9980ce0b941967cdc86ef396bb216109a9bf9`;
the Plot binding and final exact E2E use that merge SHA.

## Risk review

- **Ownership:** fixed at Renderer compile validation; Director semantic owns the real-day choice.
- **Duplicate control:** no new rule is added. The existing official production rule is invoked earlier with the same strictness.
- **Staleness:** Plot pins the exact repaired Renderer commit and retains the registry snapshot SHA because the Registry bytes do not change.
- **Test parity:** regression enters the same Renderer CLI used by Visual Intelligence production.
- **Human boundary:** an invalid Director choice becomes an explicit semantic correction request; machine code never chooses the replacement.
- **Loop:** the full production closure runs before Critic/PASS, preventing the same invalid compiled visual from reaching build-production again.

## Review / rollback

Review must show only the strict validator option, its boundary regression, the
Director semantic correction, incident update, and exact Renderer binding change.
Rollback is reverting those commits; no schema migration or persisted state rewrite
is introduced.
