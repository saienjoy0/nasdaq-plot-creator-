# NASDAQ Cafe Architecture Convergence — Open PR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Use `nasdaq-cafe-production-reliability` as coordinator, `superpowers:systematic-debugging` before any non-trivial behavior change, `superpowers:test-driven-development` for every code change, `superpowers:requesting-code-review` before merge, and `superpowers:verification-before-completion` before any success claim.

**Goal:** Converge the currently open Skill/Visual Reliability work into one coherent Production OS without duplicate Skill ownership, stale PR bases, incomplete `semanticScope` enforcement, or Renderer-side semantic invention.

**Architecture:** Keep the existing Current production spine and authority model. `scripts/current_production_facade_v12.py` remains the sole Current production entrypoint. Project Auditor is a development/change gate, not a runtime production stage. Editorial Director owns the existing editorial decision under source-of-truth 02 rather than creating a second editorial engine. Audience Retention Critic reviews a Story draft without owning story facts. Visual Intelligence owns visual semantic decisions. Renderer receives already-approved meaning and renders deterministically.

**Tech Stack:** Python 3 + pytest in `saienjoy0/nasdaq-plot-creator-`; TypeScript + Zod + tsx + Remotion in `saienjoy0/saienjoy0-nasdaq-cafe-remotion`; GitHub Actions for mechanical verification only.

**Spec:** `AGENTS.md`, `skills/nasdaq-cafe-production-reliability/SKILL.md`, `skills/nasdaq-cafe-production-reliability/references/REPAIR_DESIGN_PROTOCOL.md`, `skills/nasdaq-cafe-daily-production/SKILL.md`, `skills/nasdaq-cafe-visual-intelligence/SKILL.md`, Renderer `AGENTS.md`, Renderer PR #220 `docs/17_visual_skill_routing.md`, and Renderer PR #220 `docs/superpowers/plans/2026-09-03-visual-reliability-pr-a-semantic-scope.md`.

## Global Constraints

- Do not create a second Current facade, state machine, semantic validator chain, Renderer handoff, Story Engine, Editorial Engine, Visual Director, or Reliability layer.
- `scripts/current_production_facade_v12.py` remains the only public Current production entrypoint.
- `render_spec.json` remains the Renderer-side source of truth; legacy mirrors do not become new authorities.
- Protected Semantic Diff remains intact: narration, numbers, evidence, Scene/Beat meaning, Expected / Actual / Gap, causal claims, and `semanticScope` cannot be rewritten by Renderer selection/compile.
- GitHub Actions remains mechanical and may not choose Candidates or perform editorial/visual judgment.
- No automatic Final. Human Preview approval and explicit Final request remain mandatory.
- Fresh Current authoring may require new contracts; historical compatibility paths must remain explicit rather than silently migrated.
- A behavior change must have a RED regression first.
- A completion claim requires fresh command/CI evidence.

---

## Confirmed current evidence

1. Plot PR #194 is open, mergeable, but diverged from current `main` by 6 commits and adds seven new files. It creates two names for each of three responsibilities: generic `skills/project-auditor`, `skills/editorial-director`, `skills/audience-retention-critic` and namespaced `skills/nasdaq-cafe-*` equivalents.
2. PR #194's architecture text places `Final Production` before `Visual Intelligence`, while the Current production authority has Visual Intelligence before `episode_package_final` / Renderer handoff.
3. Renderer PR #220 is based on current Renderer `main`, keeps imported Agent Skills advisory/reference-only, pins upstream commits, keeps `render_spec` and Protected Semantic Diff authoritative, and its Agent Skills / visual CI is green.
4. Plot PR #191 and Renderer PR #223 implement the first PR-A `semanticScope` transport. Their current CI is green, but Plot PR #191 is diverged from Plot `main` by 6 commits.
5. The approved PR-A implementation plan also requires scope-aware Candidate legality and handoff version/spec identity checks. Renderer PR #223 currently transports/protects `semanticScope` but does not add the planned `visual-semantic-scope-contract.ts`, scope-aware candidate rejection, or `handoff-intake.ts` version/spec identity check.

**Root cause:** Planning and local PR implementation advanced on separate branches faster than the Production OS authority graph was reconciled, so several individually green PRs no longer prove the whole planned contract is complete.

**Repair hypothesis:** If we first consolidate Skill ownership and canonical order, then land the advisory Skill routing, rebase the Plot semantic branch, finish the missing Renderer PR-A contract gates with RED tests, and finally run cross-repo Current qualification plus one Golden Episode, the project can regain one authoritative path without adding another engine or downstream patch.

---

## Task 1: Consolidate PR #194 into one namespaced Skill owner per responsibility

**Repository:** `saienjoy0/nasdaq-plot-creator-`

**Target branch:** `integrate-editorial-auditor-retention-skills` after rebasing onto current `main`.

**Files:**
- Delete: `skills/project-auditor/SKILL.md`
- Delete: `skills/editorial-director/SKILL.md`
- Delete: `skills/audience-retention-critic/SKILL.md`
- Modify: `skills/nasdaq-cafe-project-auditor/SKILL.md`
- Modify: `skills/nasdaq-cafe-editorial-director/SKILL.md`
- Modify: `skills/nasdaq-cafe-audience-retention-critic/SKILL.md`
- Modify: `designs/NEW_SKILL_INTEGRATION_ARCHITECTURE_v1.md`
- Modify: `AGENTS.md`
- Create: `tests/current-spine/test_skill_routing_contract.py`

**Interfaces:**
- Consumes: Current project source-of-truth order, existing Causal Research, Story/03, Entertainment/04, Visual Intelligence, Reliability.
- Produces: exactly one discoverable namespaced Skill owner per new responsibility plus a routing contract that does not add production state.

- [ ] **Step 1: Write the failing duplicate-owner regression**

Create `tests/current-spine/test_skill_routing_contract.py` with the following contract:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GENERIC_DUPLICATES = (
    ROOT / "skills/project-auditor/SKILL.md",
    ROOT / "skills/editorial-director/SKILL.md",
    ROOT / "skills/audience-retention-critic/SKILL.md",
)

NAMESPACED = (
    ROOT / "skills/nasdaq-cafe-project-auditor/SKILL.md",
    ROOT / "skills/nasdaq-cafe-editorial-director/SKILL.md",
    ROOT / "skills/nasdaq-cafe-audience-retention-critic/SKILL.md",
)


def test_new_skill_responsibilities_have_one_namespaced_owner():
    assert all(path.is_file() for path in NAMESPACED)
    assert not any(path.exists() for path in GENERIC_DUPLICATES)


def test_architecture_keeps_visual_intelligence_before_episode_package_and_renderer():
    text = (ROOT / "designs/NEW_SKILL_INTEGRATION_ARCHITECTURE_v1.md").read_text(encoding="utf-8")
    ordered = [
        "Story Engine",
        "Audience Retention Critic",
        "Entertainment Inquisitor",
        "Visual Intelligence",
        "Episode Package",
        "Renderer",
        "Acceptance",
    ]
    positions = [text.index(item) for item in ordered]
    assert positions == sorted(positions)
    assert "Final Production\n        |\n        v\nVisual Intelligence" not in text


def test_project_auditor_is_change_gate_not_daily_runtime_stage():
    skill = (ROOT / "skills/nasdaq-cafe-project-auditor/SKILL.md").read_text(encoding="utf-8")
    assert "development/change gate" in skill
    assert "daily runtime stage" in skill
    assert "must not create production state" in skill
```

- [ ] **Step 2: Run RED**

```bash
pytest -q tests/current-spine/test_skill_routing_contract.py
```

Expected before repair: FAIL because the three generic duplicate Skill files exist and the architecture document places `Final Production` before `Visual Intelligence`.

- [ ] **Step 3: Rebase PR #194 before editing**

Rebase `integrate-editorial-auditor-retention-skills` onto current Plot `main`. Do not resolve conflicts by dropping Current production rules introduced after merge-base `fc28181b8139d51645a2545ba744df591d1a0d12`.

After rebase, rerun:

```bash
pytest -q tests/current-spine/test_current_production_facade_contract.py
```

Expected: PASS before continuing.

- [ ] **Step 4: Remove duplicate Skill directories**

Keep only the namespaced paths:

```text
skills/nasdaq-cafe-project-auditor/SKILL.md
skills/nasdaq-cafe-editorial-director/SKILL.md
skills/nasdaq-cafe-audience-retention-critic/SKILL.md
```

Do not add aliases or symlinks for the deleted generic names.

- [ ] **Step 5: Make Project Auditor explicitly non-runtime**

`skills/nasdaq-cafe-project-auditor/SKILL.md` must state all of the following literally enough for the test/reviewer to identify them:

```text
- this is a development/change gate
- it is not a daily runtime stage
- it must not create production state
- it may inspect architecture, Skills, contracts, workflows, tests, and PR diffs
- it may recommend owner/contract changes
- it does not replace nasdaq-cafe-production-reliability
```

- [ ] **Step 6: Bind Editorial Director to the existing editorial authority**

`skills/nasdaq-cafe-editorial-director/SKILL.md` must define:

```text
Input: validated Causal Research / current evidence / allowed memory context
Decision: why-now, audience reason, central question, selected angle, rejected alternatives, reject decision
Authority: source-of-truth/02_editorial_bible.md
Must not: write final script, synthesize evidence, bypass Causal Research, create a second editorial state machine
```

- [ ] **Step 7: Bind Audience Retention Critic to review-only behavior**

`skills/nasdaq-cafe-audience-retention-critic/SKILL.md` must define:

```text
Input: Story Engine draft / nine-scene package before final visual production
Output: hook strength, curiosity progression, scene drop-off risk, payoff timing, revision requests
Must not: change facts, numbers, sources, causal claims, scene identity, or Visual Candidate selection
Failure routing: story-order/hook problems return to Story owner; visual-legibility problems return to Visual Intelligence only after semantics are frozen
```

- [ ] **Step 8: Correct the architecture document**

Replace the single mixed flow with two separate diagrams.

Generation / production dependency:

```text
Causal Research
→ Editorial Director / editorial decision under 02
→ Story Plan
→ Story Engine / nine-scene draft
→ Fox Character realization
→ Audience Retention Critic
→ Entertainment Inquisitor under 04
→ Visual Intelligence
→ Episode Package Final
→ Renderer
→ Acceptance / Preview
```

Development/review gates:

```text
Gate 0 Project Auditor / Architecture
Gate 1 Editorial Director
Gate 2 Audience Retention
Gate 3 Story quality / 04
Gate 4 Visual Intelligence
Gate 5 Reliability
Gate 6 Audience Learning after publish
```

Add one sentence: gate numbering is review authority and must not be misread as generation chronology when a reviewer requires an already-generated artifact.

- [ ] **Step 9: Add routing to `AGENTS.md` without changing the Current entrypoint**

Add a short specialist-routing section that maps the three Skills to existing authority; do not insert a new Current state or change `scripts/current_production_facade_v12.py`.

- [ ] **Step 10: Run GREEN and existing Current contract**

```bash
pytest -q tests/current-spine/test_skill_routing_contract.py
pytest -q tests/current-spine/test_current_production_facade_contract.py
```

Expected: PASS.

- [ ] **Step 11: Commit**

```bash
git add AGENTS.md designs/NEW_SKILL_INTEGRATION_ARCHITECTURE_v1.md \
  skills/nasdaq-cafe-project-auditor/SKILL.md \
  skills/nasdaq-cafe-editorial-director/SKILL.md \
  skills/nasdaq-cafe-audience-retention-critic/SKILL.md \
  tests/current-spine/test_skill_routing_contract.py

git rm skills/project-auditor/SKILL.md \
  skills/editorial-director/SKILL.md \
  skills/audience-retention-critic/SKILL.md

git commit -m "fix: consolidate editorial skill ownership"
```

---

## Task 2: Land Renderer PR #220 as the visual-improvement Skill routing layer

**Repository:** `saienjoy0/saienjoy0-nasdaq-cafe-remotion`

**PR:** #220 `Integrate pinned visual improvement agent skills`

**Files already owned by this task:**
- `.github/workflows/agent-skills-contract-ci.yml`
- `AGENTS.md`
- `config/agent-skills.lock.json`
- `docs/17_visual_skill_routing.md`
- `docs/superpowers/specs/2026-09-02-visual-improvement-skill-architecture-design.md`
- `docs/superpowers/plans/2026-09-02-visual-improvement-skill-integration.md`
- `scripts/sync-agent-skills.mjs`
- `scripts/test-agent-skills-contract.ts`
- `package.json`

**Interfaces:**
- Consumes: approved semantics, existing Visual Director Candidate Catalog, existing motion/event contracts.
- Produces: advisory visual diagnosis/translation/motion/Remotion implementation guidance only.

- [ ] **Step 1: Re-run the exact Skill contract checks on the latest PR head**

```bash
npm ci
npm run test:agent-skills
npm run agent-skills:sync
npm run agent-skills:check
npm run test:visual-story
```

Expected: all commands PASS. `agent-skills:sync` may use network in development/CI; production runtime must not.

- [ ] **Step 2: Review ownership invariants**

Confirm the PR still states and enforces:

```text
visual-cognition-slides = reference-only
external Skills cannot override Protected Semantic Diff
Candidate Catalog cannot be bypassed by arbitrary daily SVG/HTML/React
GitHub Actions does not run AI visual judgment
production runtime does not fetch Skill repositories
render_spec remains the daily Renderer-side source of truth
```

Any deviation is Important and blocks merge.

- [ ] **Step 3: Merge only after fresh CI evidence**

Use squash or repository-normal merge policy. Record the exact merged SHA in the Architecture Convergence ledger/plan notes.

Rollback: revert the #220 merge only. Because it changes no production render semantics, rollback must not alter a daily `render_spec` or episode package.

---

## Task 3: Rebase and re-qualify Plot PR #191 on current main

**Repository:** `saienjoy0/nasdaq-plot-creator-`

**PR:** #191 `feat: PR-A require explicit visual semantic scope`

**Files:**
- `.github/workflows/current-authoring-parity-ci.yml`
- `scripts/materialize_chatgpt_daily_authoring.py`
- `scripts/materialize_renderer_sources.py`
- `scripts/renderer_strict_projection.py`
- `scripts/validate_chatgpt_daily_authoring_closure.py`
- `scripts/visual_intelligence_renderer_projection.py`
- `tests/current-spine/test_current_authoring_materializer_parity.py`
- `tests/current-spine/test_current_renderer_compatibility_projection.py`
- `tests/current-spine/test_renderer_source_version_transport.py`
- `tests/editorial-semantic-boundary/current_fixture.py`
- `tests/remotion-compat/test_chatgpt_daily_authoring_closure.py`
- `tests/remotion-compat/test_visual_intelligence_renderer_projection.py`

**Interfaces:**
- Consumes: Current authoring contract `2.0.0` and authored Beat `semanticScope`.
- Produces: fresh Current `render_spec 2.5.0` with byte-for-value `semanticScope`; compatibility paths retain explicit 2.4 behavior.

- [ ] **Step 1: Rebase onto current Plot main**

Current known merge-base is `fc28181b8139d51645a2545ba744df591d1a0d12`; current main contains later visual-feasibility / Current changes. Rebase before any merge decision.

- [ ] **Step 2: Run the targeted semantic-scope suite**

```bash
pytest -q \
  tests/current-spine/test_current_authoring_materializer_parity.py \
  tests/current-spine/test_current_renderer_compatibility_projection.py \
  tests/current-spine/test_renderer_source_version_transport.py \
  tests/remotion-compat/test_chatgpt_daily_authoring_closure.py \
  tests/remotion-compat/test_visual_intelligence_renderer_projection.py
```

Expected: PASS.

- [ ] **Step 3: Prove the Current public entrypoint contract still passes**

```bash
pytest -q tests/current-spine/test_current_production_facade_contract.py
```

Expected: PASS.

- [ ] **Step 4: Run exact cross-repo qualification against the Renderer branch that contains PR #223**

With that Renderer checkout mounted as `../renderer`:

```bash
PYTHONPATH=scripts python3 tests/current-spine/run_exact_cross_repo_current_e2e.py --renderer-root ../renderer
```

Expected: PASS through the semantic-scope boundary. A later intentional `DECISION_REQUIRED` / human semantic pause is not a machine failure.

- [ ] **Step 5: Code review before merge**

Reviewer must specifically check that no code derives `semanticScope` from Scene `causalScope`, narration, Scene number, template, or node labels.

Rollback: revert #191 as one logical contract change; do not partially revert only the schema version while leaving authored scope requirements in place.

---

## Task 4: Finish the missing Renderer PR-A behavior in PR #223 with TDD

**Repository:** `saienjoy0/saienjoy0-nasdaq-cafe-remotion`

**PR:** #223 `feat: PR-A carry visual semantic scope through Renderer`

**Existing files in #223:**
- `.github/workflows/semantic-scope-contract-ci.yml`
- `schemas/render_spec.schema.json`
- `scripts/test-semantic-scope-contract.ts`
- `src/spec/measure-visual-grammar.ts`
- `src/spec/preflight-static-viewer-layout.ts`
- `src/spec/render-spec.ts`
- `src/spec/validate-visual-grammar.ts`
- `src/spec/visual-candidate-builder.ts`
- `src/spec/visual-candidate-input.ts`
- `src/spec/visual-direction-compiler.ts`
- `src/spec/visual-director-contract.ts`

**Additional files required by the approved PR-A plan:**
- Create: `src/spec/visual-semantic-scope-contract.ts`
- Create: `scripts/test-visual-semantic-scope.ts`
- Modify: `package.json`
- Modify: `scripts/handoff-intake.ts`
- Modify: `scripts/test-handoff-intake.ts`
- Modify: `.github/workflows/semantic-scope-contract-ci.yml`

**Interfaces:**
- Consumes: a 2.5 Beat scope authored upstream; a Candidate Catalog bound to the exact source render spec; handoff manifest renderer contract declaration.
- Produces: only scope-compatible legal Candidates; compile-time scope immutability; handoff version/spec identity; legacy 2.4 compatibility where intentionally supported.

### Task 4A: Candidate legality must use scope, not merely transport it

- [ ] **Step 1: Write RED scope-eligibility tests**

Create `scripts/test-visual-semantic-scope.ts`. The test must exercise real Candidate generation, not a mock, and prove at least:

```text
lead-stock + legal causal-lane inventory -> may remain legal
sector + legal causal-lane inventory -> may remain legal
nasdaq + legal macro-pressure inventory -> may remain legal
multiple + causal-lane -> rejected
multiple + macro-pressure -> rejected
multiple + a registered separated-lane template such as tailwind-headwind -> may remain legal only when its existing grammar/inventory rules pass
Candidate Builder never rewrites semanticScope or object topology to make a Candidate legal
```

Use the current visual fixture helper already used by `scripts/test-semantic-scope-contract.ts`, mutate only the minimum Beat/template/inventory needed by each case, and assert on actual Candidate IDs/templates returned by `buildVisualCandidateCatalog`.

- [ ] **Step 2: Run RED**

```bash
node --import tsx scripts/test-visual-semantic-scope.ts
```

Expected before implementation: at least the `multiple + causal-lane` / `multiple + macro-pressure` cases FAIL because current Candidate generation does not consult `semanticScope` for template legality.

- [ ] **Step 3: Implement the smallest explicit compatibility helper**

Create `src/spec/visual-semantic-scope-contract.ts` with a pure contract function, for example:

```ts
import type {RenderSpec} from "./render-spec";
import type {VisualCandidate} from "./visual-director-contract";

export type VisualSemanticScope = NonNullable<
  RenderSpec["scenes"][number]["visualBeats"][number]["semanticScope"]
>;

const SINGLE_CHAIN_TEMPLATES = new Set(["causal-lane", "macro-pressure"]);

export const isTemplateCompatibleWithSemanticScope = ({
  semanticScope,
  visualTemplate,
}: {
  semanticScope: VisualSemanticScope | undefined;
  visualTemplate: VisualCandidate["visualTemplate"];
}) => {
  if (semanticScope !== "multiple") return true;
  return !SINGLE_CHAIN_TEMPLATES.has(visualTemplate);
};
```

The exact template IDs must match the current registry/types. Do not add a new Template in PR-A.

- [ ] **Step 4: Apply the helper at Candidate eligibility**

Modify `src/spec/visual-candidate-builder.ts` so incompatible templates are excluded before Candidate objects are finalized. Do not mutate Beat data to make the template pass.

- [ ] **Step 5: Run GREEN**

```bash
node --import tsx scripts/test-visual-semantic-scope.ts
node --import tsx scripts/test-semantic-scope-contract.ts
npm run test:visual-director
npm run test:visual-story
```

Expected: PASS.

### Task 4B: Handoff declaration and actual render spec version must agree

- [ ] **Step 6: Write RED handoff mismatch tests**

Extend `scripts/test-handoff-intake.ts` with two real temporary handoff bundles:

```text
manifest expected_contract_version = 2.5.0, render_spec.schemaVersion = 2.4.0 -> reject
manifest expected_contract_version = 2.4.0, render_spec.schemaVersion = 2.5.0 -> reject
manifest expected_contract_version = 2.5.0, render_spec.schemaVersion = 2.5.0 -> accept when all existing hashes/fields are valid
```

Expected error should be stable and specific, e.g. `handoff render_spec schemaVersion mismatch`.

- [ ] **Step 7: Run RED**

```bash
npm run test:handoff-intake
```

Expected before implementation: mismatch case reaches intake because current `prepareHandoffIntake` compares manifest metadata with workflow input but does not read the `render_spec` JSON and bind its `schemaVersion` to the manifest declaration.

- [ ] **Step 8: Implement the owning intake check**

After `specPath` is found and file integrity is verified, parse the render spec JSON only far enough to read `schemaVersion` and require:

```ts
spec.schemaVersion === manifest.renderer.expected_contract_version
spec.schemaVersion === expectedRendererContractVersion
```

Do not perform duplicate full RenderSpec semantic validation inside `handoff-intake.ts`; full schema parsing remains owned by the existing Renderer spec validator.

- [ ] **Step 9: Run GREEN**

```bash
npm run test:handoff-intake
npm run test:workflow-contract
```

Expected: PASS.

### Task 4C: Wire both regressions into PR CI

- [ ] **Step 10: Add package script and CI step**

Modify `package.json`:

```json
"test:visual-semantic-scope": "node --import tsx scripts/test-visual-semantic-scope.ts"
```

Modify `.github/workflows/semantic-scope-contract-ci.yml` so the job runs:

```bash
node --import tsx scripts/test-semantic-scope-contract.ts
npm run test:visual-semantic-scope
npm run test:handoff-intake
```

- [ ] **Step 11: Full Renderer verification**

```bash
npm run typecheck
npm run lint
npm run test:spec
npm run test:visual-director
npm run test:visual-story
npm run test:handoff-intake
npm run build
```

Expected: PASS with zero test failures and build exit code 0.

- [ ] **Step 12: Commit in small reviewable units**

```bash
git add src/spec/visual-semantic-scope-contract.ts \
  src/spec/visual-candidate-builder.ts \
  scripts/test-visual-semantic-scope.ts \
  package.json \
  .github/workflows/semantic-scope-contract-ci.yml

git commit -m "feat: enforce visual semantic scope candidate legality"
```

Then:

```bash
git add scripts/handoff-intake.ts scripts/test-handoff-intake.ts

git commit -m "fix: bind handoff contract version to render spec"
```

Rollback: revert these commits independently only if the corresponding regression also reverts. Never leave a regression green by weakening its assertion.

---

## Task 5: Cross-repo merge order and verification

**Required order:**

```text
1. PR #220 visual Skill routing
2. cleaned/rebased PR #194 editorial/auditor/retention Skill ownership
3. completed PR #223 Renderer 2.5 support + semanticScope enforcement, while retaining 2.4 compatibility
4. rebased PR #191 Plot semanticScope authoring/transport starts emitting fresh 2.5
5. cross-repo Current qualification on merged heads
```

Reasoning:
- #220 is advisory infrastructure with green Skill/visual CI and no production render semantic change.
- #194 must be consolidated before its Skills become another source of ownership ambiguity.
- #223 is backward compatible with 2.4 and therefore can safely make Renderer ready for 2.5 before the producer starts emitting 2.5.
- #191 changes fresh Current producer output to 2.5 and must not land until the bound Renderer main accepts 2.5.

- [ ] **Step 1: Before merging #223 or #191, qualify their exact two heads together**

From the rebased Plot #191 checkout with the completed Renderer #223 checkout mounted as `../renderer`:

```bash
PYTHONPATH=scripts python3 tests/current-spine/run_exact_cross_repo_current_e2e.py --renderer-root ../renderer
```

Expected: PASS through the semantic-scope boundary.

- [ ] **Step 2: Merge #223 and verify Renderer main fresh CI**

Do not rely only on the PR-head run after merge. Verify the required Renderer workflows on the resulting main SHA.

- [ ] **Step 3: Merge #191 only after Renderer main is 2.5-ready**

Then run:

```bash
pytest -q tests/current-spine/test_current_production_facade_contract.py
```

and the exact cross-repo Current qualification against Renderer `main`.

- [ ] **Step 4: Verify required GitHub Actions on exact final heads**

Plot must show success for at least:

```text
Current Authoring Parity CI
Current Spine Characterization
Current Spine Exact Cross-Repo E2E
Current Renderer Runtime Qualification Handoff
Daily Renderer Closure Gate
Visual Intelligence v1.2
Production Closure Contract CI
Validate Daily Production Package
```

Renderer must show success for at least:

```text
Semantic Scope Contract CI
Visual Grammar Renderer Contract
Visual Story Engine CI
Visual Story Media CI
Production Closure Contract CI
```

Do not use an earlier successful run after a rebase/new commit as completion evidence.

---

## Task 6: Golden Episode qualification before visual-quality expansion

**Repository authority:** Plot Current facade + exact bound Renderer.

**Goal:** Prove that the converged architecture produces a Preview without machine failure and without bypassing human/semantic pauses.

- [ ] **Step 1: Select one fresh Current episode/request**

Use the exact Current input format and `scripts/current_production_facade_v12.py`; do not build a qualification-only engine or synthetic second facade.

- [ ] **Step 2: Record gate artifacts**

Preserve evidence for:

```text
Causal Research
Editorial decision
Story / 03 package
Audience Retention review
04 Entertainment Inquisition
Semantic Freeze
Visual Requirements
Visual Source planning/selection when required
Candidate Catalog
Visual Director decision
Visual Intelligence PASS
Episode Package Final
Renderer handoff
Preview artifact
Acceptance / user review pending
```

- [ ] **Step 3: Failure routing**

If any machine boundary fails, return to `nasdaq-cafe-production-reliability` DIAGNOSE and stop at the first broken boundary. Do not patch a later component.

If the path stops on `DECISION_REQUIRED`, `AUTHOR_VISUAL_SOURCE_SELECTION`, Preview approval, or another documented human/semantic pause, classify it as an intentional pause rather than a pipeline failure.

- [ ] **Step 4: Completion evidence**

The Architecture Convergence phase may be called complete only when fresh evidence proves:

```text
one Skill owner per responsibility
no Final Production-before-Visual Intelligence ordering error
#220 Skill routing merged with current CI
#194 cleaned/rebased with routing regression green
#223 scope transport + Candidate legality + handoff identity green and merged before Plot starts emitting 2.5
#191 rebased and Plot semanticScope tests green
exact cross-repo Current path green through repaired boundaries
Golden Episode reaches Preview or an intentional human review pause
no hidden fallback, duplicate engine, or automatic Final introduced
```

---

## Review checklist

Before each merge, the reviewer must answer all of these:

1. Does this diff change the correct owner rather than patching a downstream symptom?
2. Does it create a second control path, validator, state machine, Skill owner, or Renderer handoff?
3. Does any machine code infer editorial/visual meaning from narration, Scene number, template, object count, or stale fixtures?
4. Are all new behavior changes protected by a RED-first regression?
5. Are legacy 2.4 cases explicit compatibility tests rather than silent downgrades?
6. Does GitHub Actions remain mechanical?
7. Are Preview and Final boundaries unchanged?
8. Is the success claim supported by a fresh command/CI run on the exact current head?

Critical or Important review findings block merge.
