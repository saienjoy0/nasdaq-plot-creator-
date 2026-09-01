# Current-v2 Structured Production Source Repair Implementation Plan

**Root cause:** `scripts/materialize_daily_episode.py::_run_current_v2` constructs the final `production_annex` but only embeds it into the human Markdown package. It does not persist `working/<date>/current_final_production_source.json`. The current structured builder intentionally refuses to reconstruct machine authority from Markdown and therefore fails when that sidecar is absent. The legacy materialization path in the same file already writes the exact sidecar before projecting the Markdown package.

**First broken boundary:** `FINAL_PRODUCTION_SOURCE` — Validate Daily Production Package run `32782526981`, job `97607456478`, Current Preview readiness → `build-production` → `build_final_production_package_structured_v12._load_structured_source`.

**Observed error:** `E_PACKAGE_MISMATCH: current structured production source invalid: [Errno 2] No such file or directory: '.../working/2026-08-17/current_final_production_source.json'`.

**Prior boundary status:** The previous integrated-04 heading failure is resolved. The same real-day run now passes materialization, Visual Intelligence PASS, `episode_package_final`, `memory_usage_valid`, and reaches the next boundary at structured machine authority.

**Cascade status:** `CASCADE_DETECTED`. Architecture review result: current ownership remains correct. The structured builder is correctly fail-closed and must not parse Markdown annexes. The defect is a current-v2 projection parity gap in the existing materializer, not a need for another facade, validator, or fallback parser.

## Protected invariants

- Do not parse the human Markdown annex to recover machine authority.
- Do not change narration, Scenes, Visual Beats, telops, numbers, sources, Director, Critic, or 04 review content.
- Do not alter Semantic Freeze or editorial authority.
- Keep `current_final_production_source.json` a deterministic projection of the already-built `production_annex`.
- Keep GitHub Actions mechanical.
- Do not weaken `build_final_production_package_structured_v12` fail-closed behavior.
- Do not create a second Current facade/state machine.
- Keep requested scope PREVIEW; Final remains unauthorized.

## Current code path

```text
materialize_daily_episode.py::_run_current_v2
  -> production_annex (already complete)
  -> episode_package_<date>.md only        # BUG: no structured sidecar
run_daily_production_v12.py build-production
  -> build_final_production_package_v12.py
  -> build_final_production_package_structured_v12.py
  -> _load_structured_source
  -> missing working/<date>/current_final_production_source.json
```

## Working analogue

The legacy path later in `scripts/materialize_daily_episode.py` performs:

```python
structured_source = work / "current_final_production_source.json"
structured_source.write_text(dump(production_annex) + "\n", encoding="utf-8")
```

immediately after building the same `production_annex` and before projecting the final Markdown package. This is the correct architecture because machine execution reads the sidecar while Markdown remains a human projection identity target.

## Repair hypothesis

I think the missing current-v2 sidecar write is the root cause because the structured builder's contract explicitly requires that file, the real-day error is an ENOENT for exactly that path, and the legacy path already persists the same deterministic `production_annex`. Adding the identical two-line write to `_run_current_v2` should advance the real-day path without changing any protected semantic value.

## File map

| File | Action | Responsibility |
|---|---|---|
| `docs/reliability/plans/2026-08-25-current-v2-structured-source.md` | create | Evidence-first repair design |
| `tests/current-spine/test_structured_machine_authority_v12.py` | modify | RED regression that `_run_current_v2` explicitly persists structured machine authority |
| `scripts/materialize_daily_episode.py` | modify | Persist current-v2 `production_annex` to the canonical sidecar path before Markdown projection |

## Task 1 — RED

Extend the targeted Current Spine test to AST-inspect only `_run_current_v2` and require the string constant `current_final_production_source.json` plus a `write_text` call inside that function. This avoids optional runtime dependencies and distinguishes the current-v2 function from the already-working legacy path.

Expected RED before repair: failure that `_run_current_v2` does not persist current structured production authority.

## Task 2 — Minimal repair

Insert the exact working legacy two-line sidecar persistence directly after current-v2 `production_annex` construction and before `public = normalize_scene_headings(...)`.

Do not change `production_annex`, structured builder, schema, or Markdown parsing.

## Task 3 — Verification

1. Capture targeted RED for the missing current-v2 writer.
2. Apply the two-line owning-layer repair.
3. Require Current Spine PR-5 Targeted Validation GREEN.
4. Require Daily Production Control Plane and Exact Cross-Repo E2E GREEN.
5. Re-run real 2026-08-17 PREVIEW readiness. The original ENOENT must disappear and the path must proceed to immutable Preview handoff or expose the next first broken boundary.
6. Continue Reliability cycle until Preview MP4 Artifact exists.

## Rollback

Revert the test and two-line sidecar write. No migration is required because the sidecar is deterministic and regenerated per run.
