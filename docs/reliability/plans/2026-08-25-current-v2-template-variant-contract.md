# Current-v2 Template Variant Contract Repair Plan

**Root cause:** Current-v2 materialization bypasses the existing `remotion_template_variant` contract and blindly injects `templateConfig.variant="default"` when Authoring omits a variant. For semantic multi-variant templates such as `verification-matrix`, `default` is not registered. Renderer Candidate Builder then preserves the authored template config on the compatibility path without first rejecting a variant outside the template registry, allowing an illegal Candidate to reach the official Renderer validator.

**First broken boundary:** `VALIDATOR` during the exact 2026-08-17 Current Preview readiness path. The official Renderer 2.4 validator rejects `$.scenes[2].visualBeats[1].templateConfig.variant` because `default` is not registered for `verification-matrix`.

**Evidence:**
- Exact run `32783589904` reaches Visual Intelligence PASS and `episode_package_final`, then `build-production` fails with `E_PACKAGE_MISMATCH` at the official Renderer validator.
- Pinned Renderer `505fd664935c9ff94b5d2bb1b6092a54c6a4e033` registers `verification-matrix` variants `strengthen-vs-weaken` and `reported-sequence`; its registry default is `strengthen-vs-weaken`.
- Plot already contains `scripts/remotion_template_variant.py`, which explicitly rejects missing/`default` `verification-matrix` variants rather than inferring semantic meaning.
- Current-v2 Authoring for Scene 3 Beat 2 specifies `visualTemplate=verification-matrix` but no variant, while `scripts/materialize_chatgpt_daily_authoring.py::build_scene` currently writes `beat.get("variant", "default")`.
- Renderer `visual-candidate-builder.ts::templateConfigFor` returns the authored `beat.templateConfig` unchanged when the Candidate template equals the authored template.

**Why existing tests missed it:**
- `validate_chatgpt_daily_authoring_closure.py` validates authoring/renderability structure but does not enforce the existing semantic multi-variant contract before materialization.
- `test_remotion_template_variant.py` proves `verification-matrix` must be explicit, but the current-v2 materializer does not invoke that existing normalizer on the generated RenderSpec.
- Renderer Candidate static-soundness tests cover lane structure but do not include a case where an authored-compatible Candidate carries a registry-illegal variant.
- Synthetic Current E2E fixtures therefore pass while the real-day Authoring path can emit a value the official Renderer rejects.

**Goal:** Restore the existing variant ownership contract at the earliest owning boundaries so Current-v2 cannot create or propagate a registry-illegal Candidate, while preserving ChatGPT ownership of semantic variant choice and leaving GitHub Actions mechanical.

**Architecture review:** `ARCHITECTURE_REVIEW_REQUIRED` was triggered because the immutable 2026-08-17 request exposed multiple successive boundaries. The review finds no need for a new facade/state machine or duplicated control plane. The durable issue is contract-bypass/parity: an existing Plot semantic-variant guard is disconnected from Current-v2, and Renderer candidate discovery lacks a registry-membership defense. Repair the existing owners rather than add another orchestration layer.

**Protected invariants:**
- Do not change 01-04 editorial meaning, narration, Scene order, causal scope, evidence, or Semantic Freeze identity except for a ChatGPT-authored visual variant field needed to express already-selected screen semantics.
- ChatGPT/AI-B remains owner of semantic multi-variant choices. Machine code may normalize only deterministic single-variant templates and validate explicit choices.
- GitHub Actions remains mechanical; it must not choose `strengthen-vs-weaken` or `reported-sequence` from content.
- Visual Director Candidate ownership remains unchanged.
- Do not loosen the official Renderer validator.
- Do not create a second template registry, second production facade, hidden fallback, or automatic Final path.
- Keep the pinned Renderer exact until the Renderer-side defense has its own green PR/commit and the Plot binding is intentionally updated.

## Current code path

```text
.github workflow Current Preview readiness
→ scripts/current_production_facade_v12.py
→ scripts/run_semantic_frozen_renderer_closure_v12.py
→ scripts/run_daily_renderer_closure_v12.py
→ scripts/validate_chatgpt_daily_authoring_closure.py
→ scripts/materialize_chatgpt_daily_authoring.py::build_scene
   currently injects beat.get("variant", "default")
→ render-specs/<date>/render_spec.json
→ Renderer visual-candidate-builder.ts::templateConfigFor
   authored-template path copies beat.templateConfig
→ Visual Director / compile / Critic
→ scripts/run_daily_production_v12.py build-production
→ official pinned Renderer validator
→ FAIL on unregistered verification-matrix/default
```

## Working analogue

Plot already has `scripts/remotion_template_variant.py` plus `tests/remotion-compat/test_remotion_template_variant.py`:
- deterministic single-variant templates are normalized mechanically;
- `verification-matrix` accepts only explicit `strengthen-vs-weaken` or `reported-sequence`;
- missing, mismatched, or `default` values fail closed.

Renderer already has `VISUAL_TEMPLATE_CONTRACTS`/`VISUAL_COMPONENT_REGISTRY` containing the legal variant set and `defaultVariant` for each template. New-path Candidate construction uses that registry default for alternate templates. The missing defense is only the authored-compatibility path.

## Repair hypothesis

I think the Current-v2 contract bypass is the root cause because the real materializer creates `verification-matrix/default` despite an existing fail-closed Plot variant contract, and changing Current-v2 to validate/normalize through that existing contract while making Renderer reject authored Candidates whose variant is outside its registry should make the real validator failure disappear without changing editorial or visual semantic ownership.

## File map

| File | Action | Responsibility | Why this file owns the change |
|---|---|---|---|
| `tests/remotion-compat/test_chatgpt_daily_authoring_closure.py` | modify | RED: Current-v2 Authoring with `verification-matrix` and no explicit variant must be rejected before materialization; valid explicit variants remain accepted | Authoring closure is the earliest machine gate before RenderSpec materialization |
| `scripts/validate_chatgpt_daily_authoring_closure.py` | modify | Reuse existing `remotion_template_variant` semantic multi-variant rules to validate Authoring Beat variant fields without choosing meaning | This validator owns authoring closure and must fail before rendering artifacts exist |
| `scripts/materialize_chatgpt_daily_authoring.py` | modify | Stop blind `default` injection; project explicit Beat variant when present, then run existing `remotion_template_variant.normalize_single_variant_templates(render)` before writing RenderSpec | This is the origin of the bad RenderSpec value |
| `daily-authoring/2026-08-17.json` | modify | Add ChatGPT-owned `variant: strengthen-vs-weaken` for Scene 3 Beat 2 | The Beat is explicitly a hypothesis-strength comparison; machine code must not infer it |
| Renderer `scripts/test-candidate-static-soundness.ts` | modify in Renderer PR | RED: authored-compatible Candidate with registry-illegal variant must not appear in Candidate Catalog | This is the existing Candidate Builder regression suite |
| Renderer `src/spec/visual-candidate-builder.ts` | modify in Renderer PR | Reject/drop candidate drafts when the resolved variant is not in `descriptor.variants`, including authored-template compatibility path | Candidate Builder owns which Candidates it exposes to AI-B |
| `contracts/renderer_binding.json` | modify only after Renderer PR GREEN/merge | Pin exact repaired Renderer commit/registry identity | Plot Current production must use one exact Renderer identity |

## Task 1: Plot RED regression

1. Extend `test_chatgpt_daily_authoring_closure.py` with a Current-v2 Beat changed to `verification-matrix`:
   - no `variant` -> expect error mentioning explicit registered variant;
   - `variant="default"` -> expect error;
   - `variant="strengthen-vs-weaken"` -> no variant-contract error;
   - `variant="reported-sequence"` -> no variant-contract error.
2. Add/extend a materializer regression proving `build_scene` no longer manufactures `default` for an omitted semantic multi-variant and that the RenderSpec normalizer is called.
3. RED command: affected pytest target(s). Expected pre-fix failure: missing-variant Current-v2 is incorrectly accepted / materializer still injects `default`.

## Task 2: Plot minimal owning-layer repair

1. Import the existing variant contract; do not duplicate its allowed sets.
2. In Authoring closure, validate semantic explicit-variant templates by mapping Beat `{visualTemplate, variant}` into the existing contract behavior. Report stable Beat-local errors.
3. In `build_scene`, do not use `beat.get("variant", "default")`; include an authored variant only when present.
4. After constructing the full RenderSpec and before `dump(render_spec.json)`, run `remotion_template_variant.normalize_single_variant_templates(render)` so deterministic single-variant templates stay mechanical and semantic multi-variant templates fail closed.
5. Add `variant: strengthen-vs-weaken` to 2026-08-17 Scene 3 Beat 2 as a ChatGPT-owned semantic field. Do not change narration, viewer text, template, Director decision, or causal content.

## Task 3: Renderer RED and defense

1. In `test-candidate-static-soundness.ts`, create a single authored `verification-matrix` Beat with valid lanes but `templateVariant/templateConfig.variant="default"`.
2. RED expectation: pre-fix Candidate Catalog incorrectly contains `verification-matrix/default`.
3. In `visual-candidate-builder.ts`, after resolving `variant` and descriptor, require `descriptor.variants.includes(variant)` before constructing/validating a Candidate. An illegal authored-compatible Candidate is skipped exactly like another unsound Candidate; no replacement semantic variant is invented.
4. GREEN expectation: invalid authored variant is absent, while valid `strengthen-vs-weaken` matrix remains available and existing Candidate coverage tests pass.

## Task 4: Affected suites and Current E2E

Plot GREEN/SUITE:
- `tests/remotion-compat/test_chatgpt_daily_authoring_closure.py`
- `tests/remotion-compat/test_remotion_template_variant.py`
- Current Spine targeted validation
- Current Authoring Parity CI

Renderer GREEN/SUITE:
- candidate static soundness / visual candidate coverage
- Renderer visual-contract tests relevant to template variants

Cross-repo E2E:
- exact pinned Current Spine E2E after updating Renderer binding to the repaired Renderer commit.

Real-day verification:
- rerun exact 2026-08-17 Current Preview readiness through `scripts/current_production_facade_v12.py` via the normal GitHub Actions request path;
- prove the previous `verification-matrix/default` validator failure is gone;
- continue to Preview artifact, or return to DIAGNOSE at the next first broken boundary.

## Risk review

- **Ownership:** semantic choice stays in ChatGPT Authoring; machines validate/normalize only deterministic contract facts.
- **Duplicate control:** reuse `remotion_template_variant.py` and Renderer registry; do not add a third variant table.
- **Staleness:** Plot Renderer binding changes only after Renderer fix is merged and exact commit is known.
- **Test parity:** real-day Current Preview request is mandatory after unit/contract GREEN.
- **Human boundary:** no machine inference between the two semantic `verification-matrix` variants.
- **Loop:** Renderer Candidate defense prevents another illegal authored variant from surviving until final validator; real-day verification continues until Preview or a genuinely new boundary.

## Review / rollback

Block merge if any diff:
- changes narration/editorial semantics;
- invents a semantic variant from viewer text/content in machine code;
- weakens the official Renderer validator;
- duplicates the variant registry instead of reusing existing ownership;
- changes Renderer binding before Renderer CI is green.

Rollback is file-local: revert Plot variant integration/authoring field and/or Renderer Candidate membership guard. No schema migration or state-machine rollback is required.