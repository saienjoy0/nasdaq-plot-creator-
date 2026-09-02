# Fresh Episode Current Production Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `nasdaq-cafe-production-reliability` to coordinate verification. Use existing `nasdaq-cafe-daily-production`, causal research, editorial, Visual Intelligence, and entertainment-critic authorities for episode semantics. Do not create a qualification-only production engine.

**Goal:** Prove on one genuinely fresh episode that the repaired Current architecture can travel from real daily source through Plot, Renderer Preview, explicit human approval, automatic Final runner readiness, and Final exactly once without infrastructure retries or 2026-08-17 special handling.

**Architecture:** Use the existing Current production path verbatim. Add no production workflow. Record evidence at every existing boundary and stop immediately on the first new machine failure. Final remains prohibited until the user explicitly approves the actual Preview.

**Required merge status:** `Nasdaq Cafe Required Merge Gate`

**Spec:** `docs/reliability/plans/2026-09-02-current-production-reliability-closure-design.md`

## Preconditions and protected invariants

- Plan 1 runner-readiness integration is merged and GREEN.
- Plan 2 trusted merge status + active rulesets are installed in both repositories.
- Use a real new daily source package; never copy 2026-08-17 or promote a historical real-day Artifact into the current fixture.
- ChatGPT owns research/editorial/Visual Intelligence semantics; GitHub Actions remains mechanical.
- `DECISION_REQUIRED`, `REVIEW_REQUIRED`, Visual Source selection, and human Preview review are intentional semantic/human pauses, not machine failures.
- Do not create a new formal production request merely because one of those intentional pauses occurred.
- Formal Preview request is merged only after semantic readiness PASS.
- Final authorization/request is created only after explicit user approval of the actual Preview.
- A normal Final that needs a separate `codespace-wake-requests/*`, manual Codespace start, or infrastructure `retry-*` Final request fails qualification.
- On a new first broken machine boundary, stop and return to `DIAGNOSE`; do not patch forward and still call the same qualification PASS.

## Verification gap

Synthetic Exact Cross-Repo E2E intentionally proves contract behavior without turning a historical real-day artifact into a current fixture. After the repairs, the only complete real-day Preview→Final proof is still 2026-08-17. This plan supplies the missing different-date/content proof.

## Episode selection inputs

At execution, choose the earliest legitimate real episode after Plans 1 and 2 are complete for which:

```text
actual non-empty daily source package exists
no formal Current Preview production request for that date has already entered production
```

The executor must provide two concrete values from the actual current episode context:

```text
QUALIFICATION_EPISODE_DATE = selected YYYY-MM-DD
DAILY_SOURCE_PATH = exact path to that real source package
```

Export the resolved values and validate:

```bash
[[ "$QUALIFICATION_EPISODE_DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]
[[ -s "$DAILY_SOURCE_PATH" ]]
[[ "$(basename "$DAILY_SOURCE_PATH")" == *"$QUALIFICATION_EPISODE_DATE"* ]]
export QUALIFICATION_REPORT="docs/reliability/qualifications/${QUALIFICATION_EPISODE_DATE}-current-production.md"
```

If either value is unresolved, qualification has not started.

## Required no-retry lineage

```text
real source package
→ Current semantic authoring
→ committed Semantic Freeze
→ PR-only prepare
→ Candidate Catalog
→ ChatGPT Director
→ compile / REVIEW_REQUIRED
→ ChatGPT Critic
→ compile PASS
→ ONE Plot PREVIEW request
→ ONE immutable Plot handoff/publication
→ ONE Renderer Preview request
→ ONE successful Preview
→ explicit user approval
→ ONE Plot Final authorization request
→ ONE Renderer Final request
→ Final V2 preflight
→ Final V2 automatic Codespace readiness
→ ONE successful Final outcome
```

## Evidence report contract

`$QUALIFICATION_REPORT` must contain actual values for:

```text
episode date
source package path + SHA
Plot PREVIEW request path + SHA
Plot production run ID
Plot handoff Artifact name/id/digest
Renderer Preview request path + SHA
Renderer Preview run ID
Preview MP4 SHA
preview_identity.json SHA
RenderSpec SHA
TTS input SHA
Scenes 1-4 audio SHA
Scenes 5-9 audio SHA
Renderer commit
Registry SHA
human approval reference
Plot Final authorization request path + SHA
Plot Final authorization run ID/artifact name
Renderer Final request path + SHA
Final fingerprint
Renderer Final run ID
Final MP4 SHA
Final outcome Artifact id/digest
manual wake request count
Preview retry request count
Final retry request count
first broken machine boundary
intentional semantic/human pauses encountered
qualification status PASS/FAIL
```

No `TBD`, inferred SHA, secret, or token value.

## Task 1: Verify architecture preconditions

- [ ] Renderer `main` contains `scripts/wake_repository_codespace.py`.
- [ ] Renderer Final V2 contains `wake-codespace` after preflight and Final depends on successful wake.
- [ ] Standalone Wake uses the same shared helper.
- [ ] Plot and Renderer each have active `current-production-main-v1` ruleset targeting `main`.
- [ ] Both rulesets require commit-status context `Nasdaq Cafe Required Merge Gate`.
- [ ] Current main heads have no unresolved known contract failure.

Verify rulesets through GitHub API before starting real production. If any precondition fails, stop.

## Task 2: Bind the fresh real source

- [ ] Resolve/export `QUALIFICATION_EPISODE_DATE` and `DAILY_SOURCE_PATH` using the selection rule.
- [ ] Verify source is non-empty and date-bound.
- [ ] Record:

```bash
sha256sum "$DAILY_SOURCE_PATH"
```

in `$QUALIFICATION_REPORT` before semantic authoring.

## Task 3: Complete Current semantics and Visual Intelligence PASS without request churn

- [ ] Complete causal research and canonical authoring under current project authority: Expected / Actual / Gap, timing, causal spine, counterevidence, 9 Scenes, fox narration, 04 review, final episode package.
- [ ] Create/verify the committed Current Semantic Freeze before formal production.
- [ ] Resolve exact Renderer binding once:

```bash
export RENDERER_REPOSITORY="$(python3 - <<'PY'
import json
from pathlib import Path
v=json.loads(Path('contracts/renderer_binding.json').read_text(encoding='utf-8'))
print(v['renderer']['repository'])
PY
)"
export RENDERER_COMMIT="$(python3 - <<'PY'
import json
from pathlib import Path
v=json.loads(Path('contracts/renderer_binding.json').read_text(encoding='utf-8'))
print(v['renderer']['commit'])
PY
)"
export RENDERER_ROOT="$PWD/.renderer-qualification"
rm -rf "$RENDERER_ROOT"
git clone --no-checkout "https://github.com/${RENDERER_REPOSITORY}.git" "$RENDERER_ROOT"
git -C "$RENDERER_ROOT" fetch --no-tags origin "$RENDERER_COMMIT" --depth=1
git -C "$RENDERER_ROOT" checkout --detach "$RENDERER_COMMIT"
[[ "$(git -C "$RENDERER_ROOT" rev-parse HEAD)" == "$RENDERER_COMMIT" ]]
```

Keep this same checkout through prepare/compile.

- [ ] Run prepare:

```bash
python scripts/run_daily_renderer_closure_v12.py \
  --phase prepare \
  --date "$QUALIFICATION_EPISODE_DATE" \
  --repo-root . \
  --renderer-root "$RENDERER_ROOT"
```

If Director is absent, expected pause is `DECISION_REQUIRED / AUTHOR_VISUAL_INTELLIGENCE_DECISION`.

- [ ] ChatGPT writes Director decision from the exact emitted Candidate Catalog.
- [ ] Run compile using the same date/root/Renderer. Expected intermediate pause is `REVIEW_REQUIRED`.
- [ ] ChatGPT performs Critic review and writes the exact Critic decision.
- [ ] Re-run compile and require Visual Intelligence PASS.

Do not create formal PREVIEW request before this PASS.

## Task 4: Prove one Plot Preview request and immutable handoff

- [ ] Open one formal Plot PREVIEW PR after readiness PASS only.
- [ ] Require PR-head commit status `Nasdaq Cafe Required Merge Gate = success` before merge.
- [ ] Merge exactly one formal request; record path/SHA.
- [ ] Require main production:

```text
canonical Current facade
compile-only PASS
one immutable handoff Artifact
Preview publication receipt PASS
handoff binds exact Renderer commit/contract/Registry
```

Record Plot run/artifact identities.

If infrastructure failure requires a second formal Preview request, qualification is FAIL and returns to Reliability DIAGNOSE.

## Task 5: Prove one Renderer Preview and stop for human review

- [ ] Transfer Plot-published Renderer Preview request bytes exactly; do not reconstruct fields.
- [ ] Open one request-only Renderer PR.
- [ ] Require `Nasdaq Cafe Required Merge Gate = success`; for request-only classification the trusted gate must wait for `Current Request Publication Gate` and not unrelated CI.
- [ ] Merge and require official Current Preview success through request identity, exact Renderer checkout, exact Plot handoff restore, media/tooling, TTS, Remotion, identity capture, Artifact upload, and terminal outcome.
- [ ] Download/inspect Preview Artifact and record exact Preview MP4/identity/RenderSpec/TTS/Renderer/Registry SHAs.
- [ ] **STOP for actual user visual review.** Do not authorize Final automatically.

If the user rejects Preview for semantic/visual reasons, return through the owning semantic process; do not label that as machine reliability success.

## Task 6: After explicit approval, prove one self-starting Final

- [ ] Record user approval against the exact Preview identity using existing human-review/Final authorization builders.
- [ ] Create exactly one Plot `final-authorization-requests-v1/*.json` PR.
- [ ] Require `Nasdaq Cafe Required Merge Gate = success`; trusted gate must wait for `ChatGPT Daily Final Authorization`.
- [ ] Merge and take the exact published Renderer Final request bytes.
- [ ] Create exactly one Renderer `final-render-requests-v2/*.json` PR; filename must not contain `retry-`.
- [ ] Require `Nasdaq Cafe Required Merge Gate = success`; merge once.
- [ ] Observe Final V2:

```text
preflight PASS
new Final required
wake-codespace PASS inside Current Final V2
Codespace state Available
self-hosted Final starts without separate Wake request commit
```

Immediate qualification failures:

```text
codespace-wake-requests/* created for normal Final
manual Codespace start outside Final V2
retry-* Final request created for infrastructure/control-plane failure
approved Preview/Final request bytes manually edited
```

- [ ] Require Final success through Preview SHA verification, Plot authorization verification, exact approved Renderer checkout, approved-byte restore, runtime-asset materialization, TTS cache re-verification with zero misses, render, full MP4 inspection/decode, immutable receipt, production Artifact, and exactly one deterministic Final outcome.

## Task 7: Finalize qualification evidence

- [ ] Fill every evidence field in `$QUALIFICATION_REPORT` from actual GitHub runs/artifacts/files.
- [ ] Count interventions. PASS requires:

```text
manual wake request count = 0
Preview retry request count = 0
Final retry request count = 0
first broken machine boundary = none
```

Intentional semantic/human pauses are listed separately and may be non-zero.

- [ ] Verify Final receipt preserves exact approved Preview identity, Renderer commit, RenderSpec SHA, TTS SHAs, and Plot Final authorization SHA.
- [ ] Commit the evidence report only after Final verification:

```bash
git add "$QUALIFICATION_REPORT"
git commit -m "docs: record Current production real-day qualification ${QUALIFICATION_EPISODE_DATE}"
```

## Qualification decision

### PASS

Call the architecture `daily-production qualified` only if Tasks 1–7 complete with zero machine-boundary retries and all protected invariants preserved.

### FAIL

On any new first broken machine boundary:

```text
status = FAIL
record exact run/job/step/log/artifact/SHA
return to nasdaq-cafe-production-reliability DIAGNOSE
stop downstream qualification
```

A repair produces a new qualification attempt on the next legitimate fresh episode, unless the failure can be re-run on the exact unchanged immutable request without creating a new production identity.
