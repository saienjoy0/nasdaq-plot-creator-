# Current-v2 Terminal Assembly Bindings Repair Implementation Plan

**Root cause:** `scripts/materialize_chatgpt_daily_authoring.py::_materialize_current_v2` projects financial bindings, visual source checkpoint, Story bindings, render_spec and reaction timeline bindings, but unlike the legacy materialization path in the same file it does not write `working/<date>/terminal_assembly_bindings.json`. The final structured production builder requires that explicit machine binding and correctly fails closed when it is absent.

**First broken boundary:** `TERMINAL_ASSEMBLY_BINDINGS` — Validate Daily Production Package run `32783074088`, job `97609125553`, Current Preview readiness → `build-production` after Visual Intelligence PASS, `episode_package_final`, and `memory_usage_valid`.

**Observed error:** `E_PACKAGE_MISMATCH: terminal assembly bindings is required: working/2026-08-17/terminal_assembly_bindings.json`.

**Prior boundary status:** The current-v2 structured production sidecar ENOENT is resolved. The same real-day run proceeds past `current_final_production_source.json` and now stops at the next missing deterministic binding.

**Cascade status:** `CASCADE_DETECTED`. Architecture review result: another current-v2 projection parity gap. The binding schema and legacy producer already exist; no new state machine, fallback parser, or validator relaxation is needed.

## Protected invariants

- Do not infer terminal text in GitHub Actions.
- Bind only already-authored Scene text from Canonical Daily Authoring v2.
- Keep final Scene `scene-09` and the existing three source text paths used by the working legacy path.
- Do not alter narration, Scenes, Visual Beats, publishing, sources, Director/Critic, 04 review, Semantic Freeze, or Renderer pin.
- Do not weaken the final production builder.
- Keep scope PREVIEW only.

## Working analogue

The legacy branch of the same `materialize_chatgpt_daily_authoring.py` writes:

```python
dump(work / "terminal_assembly_bindings.json", {
    "contractVersion":"1.0.0","episodeDate":args.date,"finalSceneId":"scene-09",
    "sourceTextPaths":["$.scenes[0].headline","$.scenes[4].supportingTexts[0]","$.scenes[7].supportingTexts[0]"],
    "lines":[a["scenes"][0]["headline"],a["scenes"][4]["supportingTexts"][0],a["scenes"][7]["supportingTexts"][0]],
})
```

Current-v2 already builds compatibility projection `a` with the same `scenes` shape before writing other machine artifacts, so this exact deterministic binding can be emitted there without semantic inference.

## Repair hypothesis

I think the missing terminal assembly binding is the root cause because the real-day builder fails specifically on the absent canonical file, the current-v2 materializer never writes it, and the legacy materializer in the same module writes the exact required schema from already-authored Scene text. Emitting that same object in `_materialize_current_v2` should advance the real-day path while preserving all semantic authority.

## File map

| File | Action | Responsibility |
|---|---|---|
| `docs/reliability/plans/2026-08-25-current-v2-terminal-assembly-bindings.md` | create | Evidence-first repair design |
| `tests/current-spine/test_structured_machine_authority_v12.py` | modify | RED structural regression requiring current-v2 terminal binding materialization |
| `scripts/materialize_chatgpt_daily_authoring.py` | modify | Write the already-defined terminal assembly binding in current-v2 materialization |

## Task 1 — RED

AST-inspect `_materialize_current_v2` and require the string constant `terminal_assembly_bindings.json`. Also require the function to reference `scene-09` so a future accidental empty placeholder cannot satisfy the test.

Expected RED: `current-v2 materializer does not persist terminal assembly bindings`.

## Task 2 — Minimal repair

Immediately after `work`, `story`, `episodes`, and `render_dir` are established and before downstream render materialization, write the exact legacy-compatible binding object using `date` and the already-projected `a["scenes"]`.

No changes to validators or downstream consumers.

## Task 3 — Verify

1. Capture target RED.
2. Apply the deterministic binding write.
3. Require Current Spine PR-5 Targeted Validation GREEN.
4. Require Exact Cross-Repo E2E and Daily Production Control Plane GREEN.
5. Re-run real 2026-08-17 PREVIEW readiness; the terminal binding error must disappear.
6. Continue the Reliability cycle on the next first broken boundary, if any, until immutable Preview handoff and Preview MP4 are produced.

## Rollback

Revert the test plus current-v2 binding write. The file is generated per run and requires no migration.
