# PR-0B — Exact Cross-Repo Current E2E

Date: 2026-08-19
Base: PR-0A characterization

## Goal

Prove the current synthetic production contract against the exact Renderer pinned by `contracts/renderer_binding.json` before any root refactor begins.

## Reuse, not a second fixture

This PR intentionally reuses:

- `tests/editorial-semantic-boundary/current_fixture.py` for the current authoring/semantic chain;
- the Renderer-owned `scripts/test-support/current-visual-grammar-fixture.ts` through `tests/remotion-compat/run_visual_intelligence_v12_cross_repo.py`;
- existing v1.2 state/preflight/final authorization acceptance tests.

No historical real-day artifact is promoted into a current fixture.

## Exact identity gate

The E2E fails before semantic/VI execution unless all of the following match the Plot binding exactly:

- Renderer repository;
- Renderer commit;
- Renderer contract version (reported in the result);
- Registry snapshot path;
- Registry snapshot SHA-256;
- Visual Intelligence bridge version (reported in the result).

## Observable E2E assertions

The existing current Visual Intelligence E2E must prove:

1. Candidate generation completes before Director choice.
2. Machine pauses before Director selection.
3. A decision bound to a stale Candidate Catalog is rejected.
4. Director-only choice compiles before Critic.
5. Machine pauses at post-compile Critic review.
6. Critic PASS is bound to the actual compiled visual/warning outputs.
7. Visual Intelligence package validation reaches PASS.

In the same job we also run the current semantic-boundary fixture and current v1.2 state/preflight/final-authorization tests so the exact Renderer identity check is not isolated from the current production contract.

## Acceptance

`Current Spine Exact Cross-Repo E2E` must be green before PR-1 is allowed to change Current/Legacy policy boundaries.
