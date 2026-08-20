# NASDAQ Cafe Plot Current Entrypoints

Status: current-spine authority after PR-8 migration.

## CURRENT PRODUCTION

Only these entrypoints are current production authority:

- `scripts/current_production_facade_v12.py`
  - sole public Plot facade for current closure/handoff execution;
  - delegates to the current control plane and existing stage executors;
  - owns no editorial judgement.
- `scripts/run_daily_production_v12.py`
  - internal current control-plane policy owner; not a public workflow entry.
- `scripts/run_semantic_frozen_renderer_closure_v12.py`
  - internal current semantic-freeze wrapper behind the facade.
- `scripts/run_daily_renderer_closure_v12.py`
  - internal current stage executor behind the semantic wrapper.
- `scripts/build_current_preview_request_v4.py`
  - deterministic Renderer Preview request builder from immutable handoff + canonical Renderer binding.
- `scripts/build_current_final_request_v2.py`
  - deterministic Final request builder from approved Preview identity + human review + Plot Final authorization;
  - requires explicit Final authorization and never renders.
- `.github/workflows/chatgpt-daily-preview-production.yml`
  - current production workflow; calls the canonical facade.

Machine execution authority is structured JSON/RenderSpec. `episode_package_<date>.md` remains the human-readable production package and an identity-validation target, not a source from which technical Renderer objects are reconstructed.

## CURRENT QUALIFICATION BOUNDARIES

Current qualification must compose the existing authorities; it must not create another full production/Renderer fixture.

- Plot Current authoring is qualified by the shared Current authoring fixture and materializer parity tests.
- Renderer runtime/Visual Intelligence is qualified by `tests/current-spine/run_exact_cross_repo_current_e2e.py`, which consumes the canonical `contracts/renderer_binding.json` and the Renderer's own Current fixture/Registry.
- Renderer 2.4 handoff lineage is qualified by the existing `tests/remotion-compat/test_visual_director_handoff.py` gates.
- Immutable Preview / explicit Final request construction is qualified by `tests/current-spine/test_current_preview_final_request_builders.py`.
- `.github/workflows/current-renderer-runtime-qualification-handoff.yml` composes those existing boundaries and emits a qualification receipt only. It does not manufacture or render a second synthetic production package.

A qualification-only helper may not own a parallel Renderer commit, Registry identity, grammar vocabulary, screen-state vocabulary, editorial schema, publishing schema, or full RenderSpec fixture. Those authorities remain with the existing canonical binding/contracts/Renderer Current fixture.

## LEGACY READ-ONLY / COMPATIBILITY

These remain for historical compatibility and migration evidence. Current production must not route through them:

- `scripts/run_daily_production.py`
- `scripts/run_daily_production_hardened.py`
- `scripts/run_daily_renderer_closure.py`
- historical combined `visual_intelligence_decision.json` readers/writers outside current v1.2 paths
- old Preview request/request-shape helpers that do not bind Renderer commit + contract + Registry identity.

Shared security/mechanical helpers may be extracted from legacy modules, but Current policy must not import Legacy policy owners.

## TEST / HISTORICAL ONLY

- historical real-day fixtures used only for regression/history;
- synthetic Current fixtures may cover the contract layer that owns them, but must not duplicate a downstream authority as another all-in-one production fixture;
- one-shot migration scripts are not production entrypoints and must be deleted after successful application.

## Renderer handoff targets

Current Plot output targets the Renderer Current Preview V4 / Final V2 contracts. Transitional Renderer V3/old Final workflows are compatibility paths only after PR-8 qualification.

## Safety

- Never change market causality, narration, Scene order, Visual meaning, or Primary/Fallback selection in GitHub Actions/Renderer.
- Never auto-run Final. Preview -> human review -> explicit Final only.
- Never repair lineage by rewriting a sealed request/evidence SHA in the same attempt.
- Never fix Current contract drift by growing a second full synthetic production/Renderer fixture; reconnect the test to the existing Current authority instead.
