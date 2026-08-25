# Renderer Candidate Variant Contract Repair Implementation Plan

**Classification:** `CASCADE_DETECTED` / `ARCHITECTURE_REVIEW_REQUIRED`

**Root cause:** Current-v2 materialization emits a schema-valid compatibility placeholder `templateConfig.variant = "default"` when the Daily Authoring Beat does not specify a variant, and the Renderer Visual Candidate Builder preserves that placeholder unchanged when a Candidate uses the authored template. Because Candidate legality currently checks template shape but not the template-specific variant registry, `verification-matrix + default` entered the Candidate Catalog, was legitimately selected by AI-B, compiled, and allowed Visual Intelligence to report PASS before the official Renderer validator rejected the final RenderSpec.

**First broken boundary:** `VALIDATOR` after `VISUAL_INTELLIGENCE` PASS, on exact Current Preview readiness run `32783589904` for episode `2026-08-17`.

**Evidence:**

- Official Renderer validator failure: `$.scenes[2].visualBeats[1].templateConfig.variant: default is not registered for verification-matrix`.
- Renderer `VISUAL_TEMPLATE_CONTRACTS["verification-matrix"].variants` contains only `strengthen-vs-weaken` and `reported-sequence`.
- Renderer component registry already owns the canonical default: `verification-matrix -> strengthen-vs-weaken`.
- Current Director semantic selected Candidate `vc-scene-03-beat-002-02`; AI-B did not invent or mutate the illegal variant.
- Visual Intelligence compile reported PASS before the later official validator caught the contract mismatch.

**Why existing tests missed it:** Candidate static-soundness tests cover lane semantics and Candidate availability, but there is no global invariant that every emitted Candidate's `templateVariant` / `templateConfig.variant` is registered for its selected template. Visual Intelligence compile validates schema, protected semantic identity, and Visual Grammar, but the production CLI does not currently invoke the official `validateVisualStoryContract` before writing a successful compiled RenderSpec. Synthetic fixtures therefore allowed a Candidate Catalog/compile path that was structurally valid but template-variant invalid.

**Goal:** Make the Renderer Candidate Builder the single mechanical owner of default variant resolution, guarantee that every Candidate is template-variant legal, and make Visual Intelligence compile fail at its own boundary if any compiled RenderSpec violates the official visual-story contract. Do this without copying Renderer variant tables into Plot and without changing editorial or AI-B visual-selection meaning.

**Protected invariants:**

- 01-04 editorial meaning, causal scope, narration, Scene order, and Visual Beat meaning do not change.
- Semantic Freeze bytes and Editorial Semantic Acceptance do not change.
- AI-B remains the owner of Candidate selection; Machine only builds legal Candidates.
- GitHub Actions remains mechanical and does not choose a Candidate.
- Plot must not duplicate Renderer template/variant registry knowledge.
- Existing explicit legal variants remain preserved.
- No hidden fallback or second production facade/state machine is added.
- Renderer contract version remains 2.4.0; only the pinned Renderer commit changes after Renderer tests pass.
- No Final render is triggered. Verification stops at Preview or the next first broken boundary.

## Current code path

```text
.github/workflows/validate-production.yml
-> scripts/current_preview_request_readiness_v12.py
-> scripts/current_production_facade_v12.py closure --phase compile
-> scripts/run_semantic_frozen_renderer_closure_v12.py
-> scripts/run_daily_renderer_closure_v12.py
-> scripts/materialize_chatgpt_daily_authoring.py::build_scene
   pre-VI templateConfig.variant = beat.get("variant", "default")
-> scripts/visual_intelligence_bridge_staged.py::prepare_and_compile
-> Renderer scripts/visual-director-cli.ts build --candidate-builder vnext
-> Renderer src/spec/visual-candidate-builder.ts::templateConfigFor
   authored-template path currently clones the pre-VI config verbatim
-> AI-B Director selects one legal Candidate ID from that Catalog
-> Renderer scripts/visual-director-cli.ts compile
-> Renderer src/spec/visual-direction-compiler.ts::compileVisualDirection
   schema + semantic + grammar checks; official visual-story validator not invoked by CLI
-> Visual Intelligence reports PASS
-> run_daily_production_v12.py build-production
-> official Renderer validateVisualStoryContract
-> FAIL on verification-matrix + default
```

## Working analogue

Renderer already has the correct single source of truth:

- `src/spec/visual-component-registry.ts::DEFAULT_VARIANT_BY_TEMPLATE`
- `getVisualComponentDescriptor(template).defaultVariant`
- `VISUAL_TEMPLATE_CONTRACTS[template].variants`

For alternative templates, `visual-candidate-builder.ts::templateConfigFor` already uses `getVisualComponentDescriptor(template).defaultVariant`; only the authored-template compatibility path bypasses that registry-derived normalization.

The compiler also already exposes `validateOutput?: (value: RenderSpec) => void`, showing that final-output validation was designed as an explicit compile boundary hook. The production CLI currently omits the hook.

## Repair hypothesis

I think the defect is that the Renderer-owned Candidate Builder special-cases the authored template by preserving a pre-VI compatibility placeholder without checking the Renderer registry, and the production compile CLI omits the official output validator; changing the Candidate Builder to preserve only registered variants (otherwise using that template's registry default) and wiring the official visual-story validator into compile should make the exact `verification-matrix + default` incident produce a legal `strengthen-vs-weaken` Candidate and prevent any future invalid compiled RenderSpec from being reported as Visual Intelligence PASS, without changing protected semantics or AI-B selection ownership.

## File map

| File | Action | Responsibility | Why this file owns the change |
|---|---|---|---|
| `saienjoy0-nasdaq-cafe-remotion/src/spec/visual-candidate-builder.ts` | modify | Resolve Candidate template variants against the canonical Renderer registry | Candidate Builder owns legal implementation Candidates and already owns default resolution for alternative templates |
| `saienjoy0-nasdaq-cafe-remotion/scripts/test-candidate-static-soundness.ts` | modify | RED/GREEN regression for authored-template placeholder normalization plus global Candidate variant legality | Existing Candidate contract regression suite |
| `saienjoy0-nasdaq-cafe-remotion/scripts/visual-director-cli.ts` | modify | Invoke official visual-story validation before compile output is accepted | Production Visual Intelligence calls this CLI directly |
| `saienjoy0-nasdaq-cafe-remotion/scripts/test-visual-director.ts` | modify if needed | Prove invalid manually-supplied Candidate output cannot compile as production-valid | Existing Director/compiler regression owner |
| `nasdaq-plot-creator-/contracts/renderer_binding.json` | modify after Renderer GREEN | Pin the tested Renderer commit while preserving contract/registry snapshot identity | Plot intentionally binds an exact Renderer implementation commit |
| `nasdaq-plot-creator-/docs/reliability/plans/2026-08-25-renderer-candidate-variant-contract.md` | create | Persist this cross-repo repair design and cascade review | Reliability Skill requires consequential plans to be saved before repair |

## Task 1: Regression reproduction (RED)

1. In Renderer `scripts/test-candidate-static-soundness.ts`, create a single-Beat `verification-matrix` fixture with valid two-lane viewer text / lane labels but a pre-VI compatibility placeholder `templateConfig.variant = "default"`.
2. Build the catalog through `buildVisualCandidateCatalogVNext`, the same Candidate Builder used by Current Visual Intelligence.
3. Assert the emitted `verification-matrix` Candidate has both `templateVariant` and `templateConfig.variant` equal to the registry default `strengthen-vs-weaken`.
4. Add a generic invariant over emitted Candidates: `descriptor.variants` must include both Candidate variant fields and the two fields must match.
5. Before repair, the test must fail because the authored-template Candidate retains `default`.

Expected RED signature: Candidate variant is `default` or the generic registry-membership assertion fails for `verification-matrix`.

## Task 2: Minimal owning-layer repair

1. In `visual-candidate-builder.ts::templateConfigFor`, obtain the descriptor once via `getVisualComponentDescriptor(template)`.
2. For the authored-template path, clone the existing config to preserve authored comparison/data/lane/order semantics.
3. If the cloned `variant` is registered in `descriptor.variants`, preserve it exactly.
4. If it is not registered, replace only `variant` with `descriptor.defaultVariant`.
5. Keep the existing alternative-template path using the same descriptor default.
6. Do not mutate viewer text, evidence, object IDs, asset IDs, screen question, or AI-B selection.

Expected GREEN: the RED regression passes; current legal authored variants remain unchanged.

## Task 3: Compile-boundary defense

1. In `scripts/visual-director-cli.ts`, import `validateVisualStoryContract`.
2. On `compile`, call `compileVisualDirection(..., validateOutput: validateVisualStoryContract)` rather than accepting schema/grammar-only output.
3. Add/extend a Director/compiler test so a manually crafted template-variant-invalid compiled Candidate cannot produce a successful production compile.
4. This is a detection boundary, not a second validator chain in Plot: it invokes the existing official Renderer validator at the point where Visual Intelligence claims its compiled output is ready.

Expected GREEN: valid current fixtures still compile; an invalid Candidate fails inside Visual Intelligence compile rather than later in build-production.

## Task 4: Affected-suite and Renderer verification

Run the Renderer package's existing Candidate / Visual Director / visual architecture tests, including at minimum:

```text
node --import tsx scripts/test-candidate-static-soundness.ts
node --import tsx scripts/test-visual-director.ts
```

Then run the repository's normal relevant CI on the Renderer repair branch. Review the actual diff for unrelated changes.

## Task 5: Pin and exact Current E2E

1. After Renderer GREEN, update only `contracts/renderer_binding.json.renderer.commit` in Plot to the tested Renderer commit. Keep `contractVersion = 2.4.0` and the same registry snapshot SHA unless the registry snapshot bytes actually changed; this repair should not change registry data.
2. Run Plot Targeted Validation, Current Authoring Parity, Current Spine Exact Cross-Repo E2E, and Validate Daily Production Package.
3. Exercise the exact `2026-08-17` Current PREVIEW request.
4. Confirm the prior validator error is gone.
5. Continue only until Preview Artifact exists or a new first broken boundary is observed.

## Architecture-risk review

- **Ownership:** PASS. Variant legality/default resolution stays in Renderer, where the registry lives.
- **Duplicate-control:** PASS. Plot gets no copied variant table; compile defense calls the existing official Renderer validator.
- **Staleness:** LOW. Renderer implementation commit is repinned; registry snapshot bytes should remain identical.
- **Test parity:** IMPROVED. RED uses VNext Candidate Builder; compile CLI gains the same official validator later used by production.
- **Human boundary:** PASS. AI-B still selects Candidate IDs; Machine does not choose visual meaning.
- **Loop risk:** IMPROVED. Invalid Candidate output is prevented and invalid compiled output is rejected at Visual Intelligence rather than surfacing as a later validator surprise.

## Review / rollback

Before merge, compare Renderer and Plot diffs against this plan. Any copied template/variant map in Plot, editorial mutation, automatic Candidate selection, changed registry snapshot without cause, or Final-render trigger blocks merge.

Rollback is safe: revert the Renderer repair commit and restore the previous Plot renderer commit binding. No semantic artifact or Freeze bytes are rewritten by this repair.
