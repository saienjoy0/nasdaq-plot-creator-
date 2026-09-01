# 2026-08-25 Current-v2 parity cascade

- incident_id: `current-v2-parity-cascade-2026-08-17`
- episode_date: `2026-08-17`
- classification: `CASCADE_DETECTED / ARCHITECTURE_REVIEW_REQUIRED`
- latest_first_failed_boundary: `VALIDATOR`
- error_signature: `verification-matrix + templateConfig.variant=default is not registered`
- root_cause_family: `Current-v2 projection / final contract parity gaps not exercised by exact pre-merge production validation`
- previous_exposed_boundaries:
  - integrated 04 heading canonicalization missing
  - `current_final_production_source.json` sidecar missing
  - `terminal_assembly_bindings.json` missing
  - Renderer Candidate template/variant legality gap
- repair_plan: `docs/reliability/plans/2026-08-25-renderer-candidate-variant-contract.md`
- why_tests_missed_it: `Candidate tests did not assert template-specific variant registry membership; Visual Intelligence compile did not invoke official visual-story validation before PASS.`
- preview_result: `not produced yet`

## 2026-08-29 Public-surface and expression closure update

- first_failed_boundary_1: `DAILY_AUTHORING observed at final Renderer layout preflight`
- error_signature_1: `Scene 1 headline 27 > 26, followed by Scene 2 headline 28 > 26`
- root_cause_1: `Daily Authoring v2 schema required only a non-empty headline, so Renderer-unsafe public text could be sealed into Semantic Freeze`
- repair_1: `add headline maxLength=26 at the existing Editorial Semantic Boundary; shorten only the two 2026-08-17 public surfaces and regenerate Acceptance/Freeze`
- regression_1: `real validate_boundary accepts 26 characters and rejects 27 before Freeze`
- first_failed_boundary_2: `EDITORIAL_ACCEPTANCE`
- error_signature_2: `unresolved verification-matrix variant rejected before Candidate Catalog`
- root_cause_2: `Editorial Semantic Boundary retained the final-only variant validator after Authoring Closure moved to pre-VI ownership`
- repair_2: `use the existing pre-VI variant validator; unresolved passes and explicit unregistered values remain fail-closed`
- first_failed_boundary_3: `RENDER_SPEC / static viewer layout`
- error_signature_3: `Scene 8 card title Company-direct vs NASDAQ-wide, 29 > 18 on one line`
- root_cause_3: `Visual Director compile validated Visual Story closure but omitted the static layout contract used by final loadRenderSpec`
- renderer_repair_3: `share Visual Story + Shot Story + static layout validation between Director compile and final loader; keep finalization-owned expression/viewer preflights at final load`
- renderer_local_commit: `09db695e9cb27dc30e3422d72618511175641309`
- episode_repair_3: `preserve the exact boundary labels with an explicit two-line card title`
- first_failed_boundary_4: `RENDER_SPEC / final expression asset preflight`
- error_signature_4: `Scene 1 軽い驚き requires foxSlightSurprise; found=0`
- root_cause_4: `Current materializer hardcoded foxAnalysis instead of projecting all authored Scene expression assets from the exact Renderer map`
- repair_4: `extract the existing projection-only expression mapping/placement helper and invoke it during Current Scene materialization; no fallback or legacy semantic fixup`
- regression_4: `public Current materializer emits foxAnalysis + foxSlightSurprise for authored chunk/initial expressions; unknown/duplicate cases remain rejected`
- exact_e2e_result: `PASS against local Renderer 09db695, including Preview request Renderer validation`
- real_day_result: `current_production_facade_v12 compile PASS; production_package_valid; official Renderer finalization pass; Final not run`
- preview_result: `handoff not yet built at time of this entry`

- recurrence_signature: `current-v2 passes local projection/VI checks but fails at a later exact Renderer contract boundary`

## 2026-08-25 Scene 9 production-closure update

- first_failed_boundary: `RENDER_SPEC / Visual Intelligence compiled output`
- error_signature: `$.scenes[8].visualBeats: Scene 9 requires final-assembly`
- observed_downstream_boundary: `build-production official Renderer validation`
- artifact_finding: `build-production adopted the SHA-bound visual_direction_compiled_render.json exactly; the adopted compiled visual itself contained closing-recap + conclusion-card and no final-assembly`
- root_cause: `production visual-director compile invoked validateVisualStoryContract with its default enforceVariety=false, so whole-episode Scene 1/8/9 production closure was skipped`
- repair_plan: `docs/reliability/plans/2026-08-25-scene9-final-assembly-production-closure.md`
- renderer_repair: `make production compile call the official validator with enforceVariety=true and add a globally-invalid-but-locally-legal Scene 9 regression`
- episode_repair: `select existing Candidate vc-scene-09-beat-001-03 (final-assembly) in Director semantic; do not patch compiled RenderSpec`
- why_tests_missed_it: `the CLI regression covered local Template/Variant legality only and used a fixture that did not characterize whole-episode production closure`
- preview_result: `not produced yet`

## 2026-08-25 Exact E2E fixture-closure update

- trigger: `Renderer PR #183 strict compile merged as 6abbf155`
- first_failed_boundary: `SYNTHETIC_FIXTURE / exact Cross-Repo Current E2E`
- error_signature: `$.scenes[0].visualBeats: Scene 1 requires opening-contradiction`
- root_cause: `makeCurrentVisualDirectorFixture was Registry/local-contract valid but did not satisfy whole-episode production closure; the exact E2E selects identity Candidates`
- repair: `centralize Scene 1 opening-contradiction, Scene 9 final-assembly, and synthetic Scene 9 numeric-lineage cleanup in the Renderer-owned shared fixture`
- renderer_pr: `#184, merged as e7e9980ce0b941967cdc86ef396bb216109a9bf9`
- forbidden_workaround: `do not disable enforceVariety for fixtures in production Visual Director compile and do not bypass the exact identity E2E`
- regression_result: `Exact Cross-Repo E2E PASS on the fixture repair commit, including packageValidation and Preview V4 request validation`
- preview_result: `not produced yet`
