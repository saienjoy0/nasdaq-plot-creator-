# Visual Candidate Coverage / Return-to-Story Implementation Plan

**Date:** 2026-08-24  
**Incident:** 2026-08-17 Current Preview readiness  
**Mode:** REPAIR_DESIGN  
**Status:** design only — do not implement or merge this repair until RED evidence is captured

## Root cause

The first broken boundary is the Renderer-owned Visual Candidate Catalog build inside the Current Visual Intelligence `prepare` path.

The real 2026-08-17 run reached `assets_resolved`, then the pinned Renderer v2.4 Candidate Builder failed with:

```text
scene-02-beat-002: Candidate Builder produced no legal candidate
```

The exact failing Beat already contains the mismatch before Visual Requirements are interpreted:

```text
visualBeatId: scene-02-beat-002
visualGrammarId: comparison
visualTemplate: split-comparison
objectIds: [scene-02-card-002]
card lines:
  - 数字：予想超え
  - 株価：引け後から5%超下落
numbers: 0
nodes: 0
arrows: 0
```

Renderer `comparison` templates require numeric comparison inventory. This Beat has a qualitative-vs-price contradiction card, not two aligned numeric values. Therefore the authored visual structure has no legal Renderer candidate.

The problem is not that the Renderer should guess a fallback. The problem is that exact Renderer eligibility is first evaluated by a **fail-fast** builder after the frozen Beat has already passed structural, editorial, and Visual Requirements checks. That makes an editorial/visual-structure return look like a technical failure and exposes only the first impossible Beat per run.

## First broken boundary

```text
VISUAL_INTELLIGENCE
  → Candidate Catalog build
  → Renderer vNext candidate eligibility
  → zero legal candidates for scene-02-beat-002
```

Owning layers:

- **Renderer:** candidate legality, template inventory constraints, grammar/template compatibility, eligibility rules.
- **Plot Current orchestration:** classify machine result and route the next required action.
- **ChatGPT Story / Visual authoring:** revise impossible authored visual Beats while preserving facts, narration, causality, uncertainty, Scene order, and 01–04 meaning.

## Evidence

- Real readiness run: `32708190439`
- Readiness artifact: `9513068798`
- Exact Current path reached:
  - Daily Authoring closure PASS
  - Story projection PASS
  - pre-TTS Visual Gate PASS
  - Visual Requirements PASS
  - Visual Asset Plan PASS
  - assets resolved
  - Renderer Candidate Builder FAIL
- Renderer Candidate Builder currently throws immediately when one Beat produces zero candidates.
- `visual_intelligence_requirements.py` currently validates semantic shape/order, not Renderer feasibility.
- Existing Current closure already has normal semantic pauses represented as `PREPARED + requiredAction`.

## Why existing tests / gates missed it

1. `pre_tts_visual_gate.py` validates Visual Grammar structure/diversity, not exact Renderer template inventory eligibility.
2. `visual_intelligence_requirements.py` validates authored Visual Intent / Provisional Direction shape and order, not Renderer legality. This is correct ownership and should remain so.
3. Synthetic Current fixtures do not reproduce a card-only `comparison` Beat with zero numeric objects.
4. Renderer Candidate Builder fails on the **first** zero-candidate Beat, so one run cannot reveal the full set of impossible Beats.
5. The Current readiness lane receives a non-zero facade exit and can only report generic `FAIL`, losing the semantic route back to Story authoring.

## Goal

Change the system from:

```text
first impossible Beat
→ Renderer throw
→ technical FAIL
→ fix one Beat
→ rerun
→ maybe reveal another impossible Beat
```

into:

```text
all Beats
→ Renderer-owned candidate coverage analysis in one pass
→ one machine coverage artifact
→ if any Beat has zero legal candidates:
     PREPARED
     requiredAction = RETURN_TO_STORY_FOR_VISUAL_FEASIBILITY
     no Candidate Catalog exposed as production-ready
→ ChatGPT revises all impossible visual Beats together
→ 04 / acceptance / Freeze regenerated as required
→ prepare rerun
→ Candidate Catalog ready
→ AUTHOR_VISUAL_INTELLIGENCE_DECISION
```

This removes the repeated one-boundary-at-a-time loop without letting GitHub Actions or Renderer make editorial choices.

## Protected invariants

The repair must not change:

- 01–04 market meaning, facts, numbers, causality, chronology, counterevidence, uncertainty, or confidence.
- Fox narration or Scene order merely to satisfy Renderer constraints.
- Semantic Freeze bytes silently. A Story/Visual Beat patch must produce fresh acceptance/freeze lineage.
- Candidate selection ownership: ChatGPT/AI-B still selects only from legal Candidate IDs.
- Renderer ownership of candidate legality.
- GitHub Actions remains mechanical.
- No automatic Final.
- No second Current facade, second state machine, or duplicate Renderer validator in Plot.
- No machine-authored fallback template/grammar when no legal candidate exists.
- No incomplete Candidate Catalog may be treated as production-ready.
- Existing normal paths for `AUTHOR_VISUAL_REQUIREMENTS`, `AUTHOR_VISUAL_SOURCE_SELECTION`, `AUTHOR_VISUAL_INTELLIGENCE_DECISION`, `RESELECT_VISUAL_CANDIDATES`, and `AUTHOR_VISUAL_CRITIC_REVIEW` remain valid.

## Current code path

```text
.github/workflows/validate-daily-production-package.yml
→ scripts/current_preview_request_readiness_v12.py
→ scripts/current_production_facade_v12.py
→ scripts/run_semantic_frozen_renderer_closure_v12.py
→ scripts/run_daily_renderer_closure_v12.py::prepare_common
→ scripts/run_visual_intelligence_v12.py
→ scripts/visual_intelligence_pipeline_v12.py::_ensure_candidate_artifacts
→ Renderer scripts/visual-director-cli.ts build --candidate-builder vnext
→ Renderer src/spec/visual-candidate-builder.ts::buildVisualCandidateCatalogVNext
→ first zero-candidate Beat throws
→ facade exits FAIL
```

## Working analogues to reuse

### 1. Missing Visual Requirements / Source Selection

`run_daily_renderer_closure_v12.py` already raises `VisualIntelligenceDecisionRequired`, writes:

```text
status = PREPARED
requiredAction = <explicit ChatGPT action>
```

and returns exit 0.

### 2. Stale Director decision

Compile exit 3 is already converted into:

```text
PREPARED
requiredAction = RESELECT_VISUAL_CANDIDATES
```

instead of a machine failure.

### 3. Preview readiness

`current_preview_request_readiness_v12.py` already maps every `PREPARED` facade result to:

```text
readiness = NOT_READY
exitCode = 3
```

while preserving `requiredAction`.

### 4. Visual Intelligence editorial boundary

`nasdaq-cafe-visual-intelligence` explicitly forbids the LLM/Renderer from inventing renderability or fallback legality. When legal candidates cannot preserve the required understanding function, the correct route is back to Story, not a guessed Candidate.

## Repair hypothesis

I think the root cause is that Renderer candidate legality is evaluated only by a fail-fast builder after the frozen visual Beat reaches Visual Intelligence, so an impossible authored Beat is misclassified as a technical failure; adding Renderer-owned **all-Beat candidate coverage diagnostics** and mapping coverage-unavailable to the existing `PREPARED` semantic-pause path should expose every impossible Beat at once and return control to ChatGPT without changing protected story semantics.

# Architecture decision

## Decision A — Renderer owns coverage diagnostics

Do **not** copy template inventory, grammar/template compatibility, or eligibility rules into `visual_intelligence_requirements.py` or another Plot validator.

Renderer already owns:

- `canBuild(...)`
- Visual Template inventory contracts
- Visual Grammar/template compatibility
- eligibility rules
- candidate capabilities

The same owner must produce the diagnostic.

### New machine artifact

Renderer build vNext writes an optional diagnostic file:

```text
visual_candidate_coverage.json
```

Minimum contract:

```json
{
  "contractVersion": "1.0.0",
  "episodeDate": "YYYY-MM-DD",
  "rendererContractVersion": "2.4.0",
  "sourceRenderSpecSha256": "...",
  "status": "PASS | UNAVAILABLE",
  "beatCount": 18,
  "unavailableBeatCount": 0,
  "beats": [
    {
      "visualBeatId": "scene-02-beat-002",
      "visualGrammarId": "comparison",
      "authoredVisualTemplate": "split-comparison",
      "requestedCapabilities": ["comparison-set", "gap"],
      "inferredCapabilities": ["source-document"],
      "inventory": {
        "cards": 1,
        "numbers": 0,
        "nodes": 0,
        "arrows": 0
      },
      "legalCandidateCount": 0,
      "failureCode": "E_VISUAL_CANDIDATE_NONE"
    }
  ],
  "unavailableBeats": ["scene-02-beat-002"]
}
```

Rules:

- Evaluate **every Beat** before returning coverage status.
- Do not stop on the first zero-candidate Beat.
- Do not invent a Candidate to make coverage pass.
- Do not make editorial statements such as which grammar/template should replace the authored one.
- Only write the normal `visual_candidate_catalog.json` when every Beat has at least one legal Candidate under the exact Renderer rules.
- Coverage is diagnostic/machine evidence, not editorial authority.

## Decision B — Reuse PREPARED, do not add a new state machine status

When Renderer reports:

```text
E_VISUAL_CANDIDATE_COVERAGE_UNAVAILABLE
```

Plot must convert that into the existing normal pause surface:

```json
{
  "status": "PREPARED",
  "requiredAction": "RETURN_TO_STORY_FOR_VISUAL_FEASIBILITY",
  "candidateCoverageReport": "working/<date>/visual-intelligence/visual_candidate_coverage.json",
  "candidateCatalog": null,
  "previewRendered": false,
  "finalRendered": false
}
```

Do not add another top-level state to `run_daily_production_v12.py`.

`PREPARED` already means “machine work reached an intentional ChatGPT semantic checkpoint.”

## Decision C — Requirements validator remains semantic-only

`visual_intelligence_requirements.py` should **not** gain copied Renderer feasibility logic.

It continues to validate:

- contract/version/date/SHA
- Beat coverage/order
- Visual Intent completeness
- allowed semantic values
- Provisional Direction shape

Exact renderability remains downstream in Renderer.

## Decision D — No automatic fallback

For `UNAVAILABLE` coverage, the system must not automatically:

- switch `comparison` → `bridge-text`;
- switch `split-comparison` → `text-focus`;
- add fake numeric objects;
- parse qualitative text into an invented Expected value;
- downgrade requiredModes merely to unblock CI.

ChatGPT must read the report and revise the authored visual structure in context.

For the current Scene 2 Beat 2, a nonnumeric contradiction representation may be a valid editorial repair, but that choice must be made in the Story/Visual authoring step and then revalidated. It is not a machine rule.

# Exact file map

## Renderer repository: `saienjoy0/saienjoy0-nasdaq-cafe-remotion`

| File | Action | Responsibility | Why this file owns the change |
|---|---|---|---|
| `src/spec/visual-director-contract.ts` | modify | define `visualCandidateCoverageSchema` and TypeScript type | Renderer owns Candidate/Capability contracts |
| `src/spec/visual-candidate-builder.ts` | modify | collect legal-candidate counts for all Beats; return coverage before throwing | this file owns exact candidate legality |
| `scripts/visual-director-cli.ts` | modify | accept `--coverage-report`, write diagnostic, keep catalog fail-closed | existing Renderer CLI is the machine bridge entry |
| `scripts/test-visual-candidate-coverage.ts` | create | RED/GREEN regression for two simultaneous impossible Beats and PASS case | prevents fail-fast recurrence |
| `package.json` | modify | include coverage test in `test:visual-director` | ensures normal Renderer CI exercises it |

No visual component or rendering component should change.

## Plot repository: `saienjoy0/nasdaq-plot-creator-`

| File | Action | Responsibility | Why this file owns the change |
|---|---|---|---|
| `scripts/visual_intelligence_pipeline_v12.py` | modify | pass `--coverage-report`; classify stable Renderer coverage error as a Visual Intelligence semantic return | owns machine bridge orchestration |
| `scripts/run_visual_intelligence_v12.py` | modify | emit `DECISION_REQUIRED` with `requiredAction=RETURN_TO_STORY_FOR_VISUAL_FEASIBILITY` and diagnostic path for coverage-unavailable | owns VI machine status translation |
| `scripts/run_daily_renderer_closure_v12.py` | modify | preserve VI `requiredAction`; write `PREPARED` without a Candidate Catalog when coverage is unavailable | owns Current prepare/compile checkpoint handling |
| `scripts/current_production_facade_v12.py` | modify | propagate diagnostic artifact path from closure gate | facade must remain thin but observable |
| `scripts/current_preview_request_readiness_v12.py` | modify | propagate diagnostic artifact into readiness receipt; keep `NOT_READY` exit 3 | PR gate must explain what ChatGPT must fix |
| `contracts/renderer_binding.json` | modify after Renderer PR merges | pin the exact Renderer commit containing coverage diagnostics | preserve exact cross-repo binding |
| `tests/current-spine/test_visual_candidate_coverage_pause.py` | create | regression for coverage-unavailable → PREPARED / RETURN_TO_STORY | freezes orchestration behavior |
| `tests/current-spine/test_current_preview_request_readiness.py` | modify | prove new PREPARED action stays NOT_READY, not FAIL | freezes PR-gate classification |
| `tests/current-spine/test_current_production_facade_contract.py` | modify | prove diagnostic artifact survives facade without semantic rewriting | protects thin-facade invariant |
| `.github/workflows/current-spine-characterization-ci.yml` | modify | execute new Current coverage-pause regression | makes regression part of required Current CI |

### Explicit no-change files

Do **not** change merely to fix this incident:

- `scripts/visual_intelligence_requirements.py`
- `scripts/run_daily_production_v12.py`
- Story narration generators
- 01–04 source-of-truth files
- Remotion visual components
- GitHub Preview render workflow semantics

# Task 1 — Renderer RED regression

Create `scripts/test-visual-candidate-coverage.ts`.

### Fixture A: two impossible Beats

Construct a valid Renderer 2.4 spec containing at least two Beats where:

- grammar/template is legal structurally;
- object inventory cannot build any Candidate;
- each Beat fails for the same class of real incident without violating the RenderSpec schema itself.

Expected **before repair**:

```text
builder throws on first Beat only
no complete coverage report
second impossible Beat is not reported
```

Expected **after repair**:

```text
coverage.status = UNAVAILABLE
unavailableBeatCount = 2
unavailableBeats contains both Beat IDs in Story order
catalog is not emitted as production-ready
```

### Fixture B: all Beats legal

Expected:

```text
coverage.status = PASS
unavailableBeatCount = 0
existing Candidate Catalog contents remain semantically unchanged
```

### Negative assertion

No candidate may appear for an impossible Beat merely to make coverage pass.

Test command:

```bash
npm run test:visual-director
```

# Task 2 — Plot RED regression

Create `tests/current-spine/test_visual_candidate_coverage_pause.py` before Plot production edits.

Fixture outcome from the exact VI boundary:

```json
{
  "status": "DECISION_REQUIRED",
  "requiredAction": "RETURN_TO_STORY_FOR_VISUAL_FEASIBILITY",
  "candidateCoverageReport": "working/2099-.../visual-intelligence/visual_candidate_coverage.json"
}
```

Expected **before repair**:

```text
closure/facade treats Renderer non-zero as FAIL
requiredAction is lost
```

Expected **after repair**:

```text
closureGate.status = PREPARED
requiredAction = RETURN_TO_STORY_FOR_VISUAL_FEASIBILITY
candidateCoverageReport is preserved
candidateCatalog is absent
facade exits 0
readiness = NOT_READY
readiness exit = 3
```

Negative cases:

- genuine Renderer schema/parser crash remains `FAIL` exit 2;
- missing Requirements remains `AUTHOR_VISUAL_REQUIREMENTS`;
- Candidate Catalog ready remains `AUTHOR_VISUAL_INTELLIGENCE_DECISION`;
- stale Director remains `RESELECT_VISUAL_CANDIDATES`;
- Review remains `AUTHOR_VISUAL_CRITIC_REVIEW`.

# Task 3 — Minimal Renderer repair

Refactor Candidate Builder so the per-Beat inner loop no longer throws immediately at:

```text
ordered.length === 0
```

Instead:

1. record that Beat in coverage;
2. continue through remaining Beats;
3. after all Beats, write/return the coverage object;
4. if any unavailable Beat exists, raise one stable machine code:

```text
E_VISUAL_CANDIDATE_COVERAGE_UNAVAILABLE:<count>
```

5. do not expose a normal Candidate Catalog for the failed build.

The coverage artifact must contain enough object/capability information for ChatGPT to repair all affected Beats in one authoring pass, but must not recommend the replacement semantic.

# Task 4 — Minimal Plot orchestration repair

## `visual_intelligence_pipeline_v12.py`

- request Renderer `--coverage-report` output;
- detect only the stable coverage-unavailable machine code;
- convert it to a `VisualIntelligenceStageError` carrying the coverage artifact path;
- all other Renderer failures remain failures.

## `run_visual_intelligence_v12.py`

Map only candidate coverage unavailable to:

```text
status = DECISION_REQUIRED
requiredAction = RETURN_TO_STORY_FOR_VISUAL_FEASIBILITY
candidateCoverageReport = <path>
exit = 3
```

Normal Candidate Catalog ready remains:

```text
status = DECISION_REQUIRED
requiredAction = AUTHOR_VISUAL_INTELLIGENCE_DECISION
exit = 3
```

## `run_daily_renderer_closure_v12.py`

Do not hardcode every prepare exit 3 as `AUTHOR_VISUAL_INTELLIGENCE_DECISION`.

Use the VI report's explicit `requiredAction` when present.

For RETURN_TO_STORY coverage pause:

- write `PREPARED`;
- preserve `candidateCoverageReport`;
- set `include_candidate_catalog = false`;
- return 0.

## Facade / readiness

Propagate the diagnostic artifact path only. Do not interpret its contents or make an editorial decision.

# Task 5 — Cross-repo binding

After the Renderer PR is independently GREEN:

1. merge Renderer PR;
2. capture exact Renderer commit SHA;
3. update Plot `contracts/renderer_binding.json` to that exact SHA;
4. run Renderer qualification handoff;
5. only then run Plot cross-repo Current E2E.

Do not point Plot to an unmerged/mutable Renderer branch.

# Task 6 — Real-day 2026-08-17 repair after generic code is GREEN

Run the exact 2026-08-17 Current `prepare` path once.

Expected first controlled result:

```text
PREPARED
requiredAction = RETURN_TO_STORY_FOR_VISUAL_FEASIBILITY
candidateCoverageReport = .../visual_candidate_coverage.json
```

The report must list **all** impossible Beats from that exact run, not only Scene 2 Beat 2.

Then ChatGPT performs one visual/story-authoring repair pass:

1. inspect every unavailable Beat;
2. preserve narration, facts, numbers, causal claims, uncertainty, Scene order;
3. revise only the visual grammar/template/object representation necessary to make the intended understanding function renderable;
4. do not invent numeric data;
5. run required Story / 04 re-review;
6. regenerate Editorial Semantic Acceptance and Semantic Freeze when frozen authoring changes;
7. invalidate old Visual Requirements / Director / Critic artifacts by lineage;
8. author fresh Visual Requirements against the new snapshot;
9. rerun prepare.

Success condition for this stage is **not Preview yet**. It is:

```text
PREPARED
requiredAction = AUTHOR_VISUAL_INTELLIGENCE_DECISION
Candidate Catalog exists and covers every Beat
```

Then continue the existing path:

```text
ChatGPT Director
→ compile
→ REVIEW_REQUIRED
→ ChatGPT Critic
→ PASS
→ formal PREVIEW request
→ GitHub Actions Preview
```

# Verification ladder

## RED

Renderer:

```bash
npm run test:visual-director
```

must demonstrate first-failure behavior before the Renderer repair.

Plot:

```bash
PYTHONPATH=scripts python3 tests/current-spine/test_visual_candidate_coverage_pause.py
```

must demonstrate FAIL/missing requiredAction before Plot repair.

## GREEN

Re-run the same tests after minimal changes.

## SUITE

Renderer:

```bash
npm run typecheck
npm run test:visual-director
npm run test:visual-story
```

Plot:

```bash
python3 tests/current-spine/test_current_spine_characterization.py
python3 tests/current-spine/test_current_production_facade_contract.py
PYTHONPATH=scripts python3 tests/current-spine/test_current_preview_request_readiness.py
PYTHONPATH=scripts python3 tests/current-spine/test_visual_candidate_coverage_pause.py
```

plus existing Visual Intelligence / Remotion compatibility suites used by PR #171.

## E2E

1. `Current Spine Exact Cross-Repo E2E`
2. `Current Renderer Runtime Qualification Handoff`
3. real-day 2026-08-17 readiness request
4. inspect coverage report
5. one ChatGPT authoring patch for all impossible Beats
6. rerun real-day prepare until the next stop is the intentional Director checkpoint

Do not claim fixed merely because the synthetic suites pass.

# Four-expert review

## Reliability / SRE

**Approve with condition:** fail-fast must become all-Beat coverage diagnostics. Otherwise the original sequential-stop problem remains.

## Architecture / ownership

**Approve:** Renderer remains the only legality owner; Plot must not duplicate `canBuild`, template ranges, grammar compatibility, or eligibility rules.

## Visual Editorial / Story

**Approve:** no automatic fallback. `UNAVAILABLE` returns control to ChatGPT, which repairs the authored visual representation while preserving the frozen market meaning.

## Verification / CI

**Approve with condition:** regression must contain **two simultaneous impossible Beats** and the real 2026-08-17 canary must prove both full coverage reporting and correct PREPARED classification before merge.

# Risk review

## Ownership risk

Low if exact candidate legality stays in Renderer. High if copied into Plot; that option is rejected.

## Duplicate-control risk

Low. No new semantic validator chain is introduced. Coverage is a Renderer diagnostic from the existing builder path.

## Staleness risk

Controlled by existing exact Renderer binding and Semantic Freeze lineage. A Story patch must create fresh acceptance/freeze artifacts.

## Test-parity risk

Addressed by pinning the new Renderer commit and running exact cross-repo Current E2E plus the real-day request.

## Human-boundary risk

Reduced: impossible Candidate coverage becomes an explicit ChatGPT action instead of generic machine failure.

## Loop risk

Primary design target. All unavailable Beats must be reported in one coverage artifact so ChatGPT can patch them together.

# Rejected alternatives

## 1. Add Renderer legality rules to `visual_intelligence_requirements.py`

Rejected because it creates a second validator owner and future contract drift.

## 2. Always inject `text-only` as a safe fallback

Rejected because it overrides authored understanding requirements and can hide a genuine Story/Visual structure defect.

## 3. Auto-convert `comparison` to another grammar/template

Rejected because grammar/template replacement is an editorial choice.

## 4. Invent numeric objects from qualitative text

Rejected. `数字：予想超え` is not an authored Expected numeric value and must not be converted into one.

## 5. Fix only Scene 2 Beat 2

Rejected as the generic repair. The actual current episode may contain more impossible Beats; one-at-a-time repair recreates the original loop.

# Merge gate

Do not merge the generic repair until all are true:

- Renderer two-impossible-Beat RED/GREEN regression exists.
- Renderer normal Candidate Catalog behavior remains unchanged for legal specs.
- Plot coverage pause RED/GREEN regression exists.
- genuine Renderer technical errors still fail.
- Current facade remains thin.
- readiness returns NOT_READY / exit 3 with explicit requiredAction and diagnostic artifact.
- exact pinned Renderer qualification passes.
- exact Current cross-repo E2E passes.
- real 2026-08-17 prepare reports all unavailable Beats in one run.
- after ChatGPT repairs those Beats, the real path reaches the intentional Director checkpoint.
- no Preview request is merged before the semantic/visual checkpoints are complete.
