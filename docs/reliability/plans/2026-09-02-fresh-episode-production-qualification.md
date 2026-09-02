# Fresh Episode Current Production Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `nasdaq-cafe-production-reliability` to coordinate verification. Use the existing `nasdaq-cafe-daily-production`, causal research, editorial, Visual Intelligence, and entertainment-critic authorities for episode semantics. Do not create a qualification-only production engine.

**Goal:** Prove on one genuinely fresh episode that the repaired Current architecture can travel from the real daily source package through Plot, Renderer Preview, explicit human approval, automatic runner readiness, and Final exactly once without infrastructure retry requests or 2026-08-17 special handling.

**Architecture:** Qualification uses the existing production path verbatim. It adds no production workflow. The selected episode is the first legitimate episode produced after Plans 1 and 2 are merged and protected; the reliability coordinator records evidence at every existing boundary and stops immediately on the first machine failure. Final remains prohibited until the user explicitly approves the actual Preview.

**Tech Stack:** existing Nasdaq Cafe Current v1.2 CLI/workflows, GitHub Actions, Plot/Renderer immutable Artifacts, existing skills.

**Spec:** `docs/reliability/plans/2026-09-02-current-production-reliability-closure-design.md`

## Global Constraints

- Plan 1 (Final V2 runner readiness) and Plan 2 (Required Main Merge Gates) must be complete before this qualification starts.
- Use a real new `daily_source_package_YYYY-MM-DD.md`; do not copy 2026-08-17 inputs or promote a historical artifact into a current fixture.
- ChatGPT owns research/editorial/Visual Intelligence semantics; GitHub Actions remains mechanical.
- `prepare` intentional pauses for Visual Source selection, Director, Critic, or human Preview review are PASS-like human/semantic boundaries, not machine failures.
- Do not create new production request revisions merely because `prepare`/`compile` is waiting for a semantic decision.
- Formal Preview request is merged only after Current Preview semantic readiness PASS.
- Final request is created only after the user explicitly approves the actual Preview.
- Qualification fails if normal Final requires a separate `codespace-wake-requests/*` change, any infrastructure `retry-*` Final request, or manual modification of immutable request/artifact bytes.
- On any new first broken machine boundary, stop and return to `DIAGNOSE`; do not patch forward during the same qualification attempt.

---

**Verification gap:** Synthetic Exact Cross-Repo E2E intentionally proves contract behavior without making a historical real-day artifact the current fixture. The repaired architecture has one full real-day proof (2026-08-17), so date/content independence is not yet demonstrated.

**Qualification boundary:** end-to-end Current production environment parity.

**Why existing tests cannot close this alone:** unit/contract/E2E tests do not exercise a new day's Collector evidence, newly authored semantic artifacts, actual GitHub Artifact transport, external TTS, sleeping/available Codespace lifecycle, and a new immutable Final fingerprint in one continuous real production lineage.

## Episode selection rule

At execution time define `QUALIFICATION_EPISODE_DATE` as:

> the earliest real episode date produced after both reliability repair PRs are merged for which a complete non-empty `daily_source_package_<date>.md` exists and no prior Current production request for that date has entered Preview production.

If the first candidate already has a production request, choose the next real episode; do not delete/reuse an old request to manufacture freshness.

## Expected no-retry lineage

```text
real daily source
→ Current semantic authoring
→ committed Semantic Freeze
→ PR-only prepare
→ Candidate Catalog
→ ChatGPT Director
→ PR-only compile / REVIEW_REQUIRED
→ ChatGPT Critic
→ PR-only compile PASS
→ ONE Plot PREVIEW request merge
→ ONE immutable Plot handoff/publication
→ ONE Renderer Preview request merge
→ ONE successful Preview
→ explicit user approval
→ ONE Plot Final authorization request merge
→ ONE Renderer Final request merge
→ Final V2 preflight
→ automatic Codespace readiness inside Final V2
→ ONE successful Final outcome
```

## Evidence record

Create after the run:

```text
docs/reliability/qualifications/<QUALIFICATION_EPISODE_DATE>-current-production.md
```

The record must contain:

```text
episode date
Plot PREVIEW request path + SHA
Plot production run ID
Plot handoff Artifact name/id/digest
Renderer Preview request path + SHA
Renderer Preview run ID
Preview MP4 SHA
preview_identity.json SHA
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
first broken machine boundary (must be none for PASS)
intentional semantic/human pauses encountered
qualification status PASS/FAIL
```

No secrets or token values.

## Task 1: Preconditions — prove repaired architecture and repository policy are live

**Files:** no production file changes.

- [ ] **Step 1: Verify Renderer Final V2 runner-readiness source is on `main`**

Inspect Renderer `main` and require:

```text
scripts/wake-repository-codespace.py exists
.github/workflows/nasdaq-cafe-final-v2.yml contains wake-codespace
Final job needs [preflight, wake-codespace]
standalone Wake also calls the shared helper
```

- [ ] **Step 2: Verify both `main` rulesets are active**

Read:

```text
GET /repos/saienjoy0/nasdaq-plot-creator-/rulesets
GET /repos/saienjoy0/saienjoy0-nasdaq-cafe-remotion/rulesets
```

Require active `current-production-main-v1` in both repositories and the exact observed Required Merge Gate check context.

- [ ] **Step 3: Verify baseline CI on both current main heads**

Renderer relevant CI and Plot relevant CI must have no known failing current contract before the new episode starts. A stale historical failure is not blocking if a newer exact-head run is green.

If any precondition fails, qualification does not start.

## Task 2: Select and bind the genuinely fresh source package

**Files:** normal episode input/authoring files only, as produced by the existing daily process.

- [ ] **Step 1: Resolve `QUALIFICATION_EPISODE_DATE` using the selection rule**

- [ ] **Step 2: Confirm the source package is real and non-empty**

The file name must contain the exact episode date and its contents must be the day's actual Collector/source package, not copied fixture data.

- [ ] **Step 3: Record the source-package SHA before authoring**

```bash
sha256sum daily_source_package_${QUALIFICATION_EPISODE_DATE}.md
```

Use the actual repository path if the package is stored under a dated input directory; record that exact path/SHA in the qualification report.

## Task 3: Complete semantic authoring through Visual Intelligence PASS without request churn

**Files:** the normal daily Current artifacts defined by `nasdaq-cafe-daily-production` and project instructions.

- [ ] **Step 1: Complete causal research and canonical authoring**

Use current project authority ordering. Produce evidence-grounded Expected / Actual / Gap, timing, causal spine, 9 Scenes, fox narration, counterevidence, 04 review, and final episode package without changing machine contracts for convenience.

- [ ] **Step 2: Create/verify Current Semantic Freeze before production**

Production later verifies the committed Freeze; GitHub Actions must not create it.

- [ ] **Step 3: Run the existing fresh real-day Visual Intelligence prepare phase**

```bash
python scripts/run_daily_renderer_closure_v12.py --phase prepare --date "$QUALIFICATION_EPISODE_DATE" --repo-root . --renderer-root <exact-pinned-renderer-checkout>
```

Expected intentional result when Director selection is missing:

```text
DECISION_REQUIRED / AUTHOR_VISUAL_INTELLIGENCE_DECISION
```

This is not a production failure.

- [ ] **Step 4: ChatGPT authors the Director decision from the exact emitted Candidate Catalog**

No machine ranking/selection.

- [ ] **Step 5: Run compile**

```bash
python scripts/run_daily_renderer_closure_v12.py --phase compile --date "$QUALIFICATION_EPISODE_DATE" --repo-root . --renderer-root <same-exact-pinned-renderer-checkout>
```

Expected intentional intermediate result:

```text
REVIEW_REQUIRED
```

- [ ] **Step 6: ChatGPT performs Critic review and writes the exact Critic decision**

- [ ] **Step 7: Re-run compile and require Visual Intelligence PASS**

Do not create/merge a formal PREVIEW request before this PASS.

## Task 4: Produce exactly one formal Plot Preview request and handoff

**Files:** exactly the normal Current formal Preview request plus already-approved semantic artifacts.

- [ ] **Step 1: Open the formal Plot PREVIEW PR only after readiness PASS**

The PR must not create a new semantic decision. It references the exact committed Semantic Freeze and current approved state.

- [ ] **Step 2: Require Plot `Required Merge Gate` success before merge**

The gate must in turn observe all workflows required by the Plot policy for the changed paths, including `Validate Daily Production Package` and semantic readiness where applicable.

- [ ] **Step 3: Merge exactly one formal request**

Record request path and SHA. If a second request revision is needed because a machine failure appears, qualification becomes FAIL and returns to Reliability DIAGNOSE; do not continue counting retries until Final eventually works.

- [ ] **Step 4: Verify Plot main production**

Require:

```text
canonical Current facade used
compile-only production PASS
one immutable handoff Artifact
Preview request publication receipt PASS
handoff manifest binds exact Renderer commit/contract/Registry
```

Record Plot run ID, Artifact ID/name/digest and request SHA.

## Task 5: Produce exactly one Renderer Preview and stop for human review

- [ ] **Step 1: Transfer the exact Plot-published Renderer Preview request bytes**

Create a Renderer request-only PR containing exactly one new file at the target path emitted by Plot. Do not reconstruct fields manually.

- [ ] **Step 2: Require Renderer `Required Merge Gate` success**

For request-only PR it must require `Current Request Publication Gate` and nothing unrelated.

- [ ] **Step 3: Merge and require Preview success**

Require the official Current Preview workflow to pass:

```text
request identity
exact Renderer checkout
exact Plot handoff restore
media/tooling
TTS
Remotion Preview
Preview identity capture
Preview Artifact upload
terminal Preview outcome
```

- [ ] **Step 4: Verify Preview Artifact bytes**

Record:

```text
Preview MP4 SHA-256
preview_identity.json SHA-256
RenderSpec SHA-256
TTS input SHA-256
Scenes 1-4 audio SHA-256
Scenes 5-9 audio SHA-256
Renderer commit
Registry SHA-256
```

- [ ] **Step 5: STOP for actual user visual review**

Do not authorize or request Final automatically.

If the user rejects Preview for editorial/visual reasons, that is not a reliability PASS; fix semantics through their owning process and restart qualification with the resulting legitimate production lineage.

## Task 6: After explicit approval, prove Final is single-request and self-starting

- [ ] **Step 1: Record the user's explicit approval against the exact Preview identity**

Use existing human Preview review/Final authorization builders. Do not fabricate approval.

- [ ] **Step 2: Create exactly one Plot `final-authorization-requests-v1/*.json` request**

Require Plot `Required Merge Gate` + `ChatGPT Daily Final Authorization` success, then merge.

- [ ] **Step 3: Transfer the exact published Renderer Final request bytes**

Create exactly one Renderer `final-render-requests-v2/*.json` PR. File name must NOT contain `retry-`.

- [ ] **Step 4: Require Renderer `Required Merge Gate` + request publication validation, then merge**

- [ ] **Step 5: Observe Final V2 runner readiness**

Normal success must show:

```text
preflight PASS
new Final required
wake-codespace PASS inside Current Final V2
Codespace state Available
self-hosted Final job starts without a separate wake request commit
```

The following immediately fail qualification:

```text
creation of codespace-wake-requests/* for normal Final
manual Codespace start outside Final V2
creation of a retry-* Final request for infrastructure/control-plane reasons
editing approved Preview/Final request bytes
```

- [ ] **Step 6: Require complete Final success**

Require:

```text
approved Preview SHA verified
Plot Final authorization bundle verified
exact approved Renderer checkout verified
approved production bytes restored
runtime assets materialized
cached TTS bytes reverified with 0 misses
approved Renderer Current Final procedure success
Final MP4 inspected/decoded
immutable receipt written
Final production Artifact uploaded
exactly one deterministic Final outcome published
```

## Task 7: Write the qualification report and make the pass/fail decision

**Files:**
- Create: `docs/reliability/qualifications/<resolved-date>-current-production.md`

- [ ] **Step 1: Fill every Evidence record field from actual runs/artifacts**

Do not write `TBD` or infer SHAs from filenames.

- [ ] **Step 2: Count manual infrastructure interventions**

PASS requires:

```text
manual wake request count = 0
Preview retry request count = 0
Final retry request count = 0
first broken machine boundary = none
```

Intentional semantic/human pauses may be non-zero and must be listed separately.

- [ ] **Step 3: Verify lineage consistency**

The Final receipt must preserve the exact approved Preview identity, Renderer commit, RenderSpec SHA, TTS SHAs, and Plot Final authorization SHA recorded earlier.

- [ ] **Step 4: Commit only the evidence report after Final verification**

Suggested commit:

```bash
git add docs/reliability/qualifications/${QUALIFICATION_EPISODE_DATE}-current-production.md
git commit -m "docs: record Current production real-day qualification"
```

## Qualification decision

### PASS

Call the architecture “daily-production qualified” only if Tasks 1–7 complete with no machine-boundary retry and all protected invariants preserved.

### FAIL

If any new first broken machine boundary appears:

```text
status = FAIL
record exact run/job/step/log/artifact/SHA
return to nasdaq-cafe-production-reliability DIAGNOSE
stop downstream qualification
```

Do not patch and continue the same run until the report says PASS; a repair creates a new qualification attempt on the next legitimate fresh episode unless the failure can be re-run on the exact unchanged request without creating a new immutable production identity.
