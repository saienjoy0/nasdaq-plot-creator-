# Synthetic Runtime Dependency Wiring Repair — 2026-08-25

## First failed boundary

Current Authoring Parity / Exact Cross-Repo E2E synthetic runtime import boundary.

## Symptom

`ModuleNotFoundError: No module named 'remotion_template_variant'`

## Root cause

Two independent synthetic-test wiring gaps exposed the same local dependency:

1. `tests/editorial-semantic-boundary/current_fixture.py::install_runtime()` copied `validate_editorial_semantic_boundary.py` into the temporary repository but did not copy its direct local dependency `scripts/remotion_template_variant.py`.
2. `scripts/validate_chatgpt_daily_authoring_closure.py` imported the sibling module directly but did not establish `SCRIPT_DIR` on `sys.path`, unlike the other validator entrypoints that are intentionally loadable through `importlib.util.spec_from_file_location()` in parity tests.

The production semantic/visual contract was not changed. The failure was in test/runtime dependency wiring.

## Repair

- Include `scripts/remotion_template_variant.py` in the synthetic Current runtime copy set.
- Make the closure validator resolve sibling modules from its own `SCRIPT_DIR` before importing `remotion_template_variant`.

## Regression proof

The existing failing workflows are the regression tests:

- Current Authoring Parity CI
- Current Spine Exact Cross-Repo E2E

They must progress beyond module collection/import before this incident is considered closed.

## Non-goals

- No editorial meaning change.
- No Renderer registry change.
- No Visual Intelligence selection change.
- No Final render.
