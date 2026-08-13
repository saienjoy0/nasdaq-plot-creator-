---
name: nasdaq-cafe-visual-intelligence
version: 1.2.0
description: Select and independently critique legal visual candidates for 朝のNASDAQカフェ so visuals increase viewer understanding without changing the frozen story, evidence, causality, or machine eligibility.
---

# NASDAQ Cafe Visual Intelligence

Run after the Story Engine / 04-reviewed editorial snapshot exists and after Architecture has produced the legal Candidate Catalog. This Skill is the **editorial visual judgment layer** only.

It does not decide whether a template can render, whether an asset exists, whether a series is verified, whether a numeric basis is valid, whether the renderer is compatible, or whether CI may advance.

## Governing contract

- Frozen bridge: `visual-intelligence-bridge/1.2.0`
- Frozen Interface SHA-256: `a9c54f2115f1d5a73251be64edcd5ff3f84c0940613ff7a6d7718f755581977f`
- Do not rename frozen fields, statuses, artifact paths, or responsibility boundaries.
- Do not edit `scripts/**`, `contracts/**`, `.github/**`, Remotion, Hard Validators, existing Story Engine, existing Entertainment Critic, or daily production artifacts from this Skill.

## Source-of-truth order

Read and obey, in order:

1. Current ChatGPT project instructions
2. `source-of-truth/02_editorial_bible.md`
3. `source-of-truth/01_fox_character_bible.md`
4. materialized `03_episode_production_spec.md`
5. materialized `04_entertainment_inquisitor.md`
6. `skills/nasdaq-cafe-story-engine/SKILL.md`
7. `AGENTS.md`
8. `designs/VISUAL_DIRECTOR_PRODUCTION_INTEGRATION.md`
9. this Skill and its references

This Skill may strengthen presentation only. It must never become a second Story Engine.

## Core philosophy

> **映像は情報を飾るためではなく、理解を変えるために使う。**

> **Visual change is not editorial progress.**

> **Novelty is not editorial value.**

> **Past success is not a mandate.**

Inherit the Story Engine definition of interestingness:

> Evidence should cause a meaningful update in the viewer's explanatory model.

Visual Information Gain is therefore a semantic editorial judgment, never a numeric quota, template-count target, motion target, or novelty score.

## Absolute boundary

This Skill may decide:

- Visual Intent semantics
- Provisional Direction semantics
- final selection among legal Candidate IDs
- strongest-alternative comparison
- Reality Anchor editorial use
- Visual Turn / visual progression quality
- independent Visual Plan Critic findings
- targeted candidate-selection patch
- whether a Visual defect requires `RETURN_TO_STORY`
- Production Lesson eligibility after human approval

This Skill may not decide or rewrite:

- template renderability
- asset existence
- verified-series eligibility
- numeric or basis validity
- Candidate ID generation
- Registry structure
- renderer compatibility
- production state / CI
- Hard Validator behavior
- story lead, facts, numbers, Expected / Actual / Gap
- chronology, evidence bindings, causal scope, confidence
- material counterevidence or uncertainty
- Scene order or formal Scene roles
- narration during a Visual-only patch

If the Story itself lacks progression or meaning, use `RETURN_TO_STORY` rather than repairing meaning inside Visual Intelligence.

# Required passes

## Pass A — Visual Intent

For every visual Beat, author the frozen semantic fields:

```json
{
  "visualBeatId": "vb-04-01",
  "purpose": "ExpectedとActualの差が評価軸だったことを理解させる",
  "audienceBeliefBefore": "Actualが良ければポジティブ",
  "audienceBeliefAfter": "Expectedとの差が評価軸",
  "visualInformationGain": "同一尺度で比較することで差を一目で認識できる",
  "preferredEvidenceModes": ["comparison", "source-document"],
  "realityAnchorPreference": "preferred",
  "editorialReason": "ここまで抽象説明なので確認済み事実へ接地したい"
}
```

Rules:

- `visualInformationGain` is prose, not a score.
- `audienceBeliefBefore/After` must inherit Story meaning; do not manufacture a new belief update.
- `preferredEvidenceModes` expresses editorial preference, not machine capability.
- Valid visual gains include faster comparison, visible sequence, source grounding, spatialized distance/path, and visible confirmed/unconfirmed boundaries.
- Weak intents such as “数字を見せる” or “画面を派手にする” are invalid.

## Pass B — Provisional Direction

Identify likely visual requirements before final asset resolution. Do not choose a final template here.

Use only the frozen fields:

```json
{
  "visualBeatId": "vb-05-01",
  "requiredModes": ["source-document", "image-media"],
  "imageRequirement": "required|possible|not-required",
  "reason": "string"
}
```

Questions:

- Would a source document materially ground an abstract claim?
- Would image media add real understanding, not decoration?
- Is an entity anchor useful?
- Would a chart or timeline materially improve comparison or chronology?

Use `required` sparingly. If fallback representation preserves the same fact, causality, uncertainty, and understanding function, prefer `possible`.

### Image rule

For any Beat requiring a day-specific generated image, Primary and Approved Fallback must already exist before generation. A failed Primary does not imply `BLOCKED` when a legal fallback preserves the understanding function.

## Pass C — Final Candidate Selection

Input is a machine-produced Candidate Catalog containing only legal candidates.

Never infer preference from Candidate ID order. In particular:

- `-01` is not default
- first-listed is not recommended
- authored template is not automatically safer
- new component is not automatically better

Compare candidates on:

1. Visual Information Gain
2. fit with Story role
3. grounding in Evidence
4. explanatory progression, not superficial screen variation
5. misunderstanding risk
6. visual information load vs narration load
7. inertia from recent approved episodes, when Phase 2 context exists

For multiple legal candidates, always output:

```json
{
  "visualBeatId": "vb-04-01",
  "selectedCandidateId": "vc-vb-04-01-02",
  "strongestAlternativeCandidateId": "vc-vb-04-01-01",
  "whySelected": "string",
  "whyNotAlternative": "string"
}
```

For one legal candidate, do not invent a second option:

```json
{
  "visualBeatId": "vb-04-01",
  "selectedCandidateId": "vc-vb-04-01-01",
  "strongestAlternativeCandidateId": null,
  "whySelected": "only legal candidate",
  "whyNotAlternative": ""
}
```

The final editorial truth for template choice is the LLM Visual Director selection, but the Director may select only from the legal Catalog.

## Pass D — Independent Visual Plan Critic

Run in a separate context from the Director. The Critic receives:

- Editorial Snapshot
- Visual Intent
- Candidate Catalog
- Director Selection
- Compiled Visual Plan
- Mechanical Warnings
- Visual Editorial Principles
- Recent Approved Visual Pattern Context when Phase 2 is available

Do not accept the Director's rationale as proof.

Ask at least:

1. Does this Visual actually advance viewer belief?
2. Is it only repeating narration as a receipt?
3. Is a high-value Reality Anchor being missed?
4. Is repetition justified by comparison/tracking, or just inertia?
5. Is the selected candidate truly stronger than the strongest alternative?
6. Does the Visual Turn correspond to a real understanding turn?
7. Do Scenes 6–8 retain a visual reason to watch?
8. Is a recent approved pattern being repeated without today-specific justification?
9. Is novelty merely decorative?
10. Does the Visual hide a material boundary, counterevidence, or uncertainty?
11. Is there unnecessary visual switching that weakens comprehension?
12. Is the episode over-directed relative to the narration?

### Critic status

Use exactly:

```text
PASS
REVISE
RETURN_TO_STORY
BLOCKED
```

`PASS` — no unresolved major finding.

`REVISE` — a candidate-selection change can resolve the major problem without changing story meaning.

`RETURN_TO_STORY` — Visual-only changes cannot fix the underlying lack of Story progression or meaning.

`BLOCKED` — required understanding function cannot be produced by any legal candidate/fallback because required evidence, asset, or renderer capability is unavailable.

Do not use `BLOCKED` for a failed Primary image when Approved Fallback is legal.

### Finding vocabulary

At minimum:

```text
VISUAL_NO_INFORMATION_GAIN
VISUAL_RECEIPT_ONLY
MISSED_REALITY_ANCHOR
DECORATIVE_NOVELTY
UNJUSTIFIED_REPETITION
UNNECESSARY_VISUAL_CHANGE
OVERDIRECTED_VISUALS
CROSS_EPISODE_PATTERN_STALENESS
WEAK_VISUAL_TURN
NO_VISUAL_PROGRESS
CANDIDATE_SELECTION_UNJUSTIFIED
```

Findings are editorial. Never auto-promote them into Hard Validator errors.

Use `major` when understanding progression, Evidence interpretation, or late visual value materially fails. Use `minor` for localized issues that do not invalidate the whole plan.

## Pass E — Targeted Candidate Patch

For `REVISE`, patch only the affected selection:

- identify Beat
- provide replacement Candidate ID
- state why it fixes the finding
- preserve narration, Evidence, causality, Expected / Actual / Gap, Scene order, and all frozen Story meaning

Automatic Visual patch scope is **candidate selection only**.

Do not generate a new Component, free-write a shot, rewrite narration, add Evidence, delete Evidence, or change causal scope.

## Pass F — Re-review

Recompile through the Architecture-owned path, then run the independent Critic again.

Maximum two review rounds.

If still unresolved:

- Story meaning defect → `RETURN_TO_STORY`
- genuine capability/evidence absence → `BLOCKED`
- otherwise fail closed rather than silently accepting a weak plan

### RETURN_TO_STORY route

```text
Visual Critic
→ RETURN_TO_STORY
→ Story patch
→ 04 re-review
→ Story Engine re-review
→ editorial snapshot regeneration
→ old Visual Intent / Candidate Catalog / PASS invalidated
→ restart from Pass A
```

Never reuse an old Visual PASS after Story meaning changes.

## Pass G — Production Lesson eligibility

Production Lessons and Recent Pattern memory are **human-approved memory only**.

Eligible only when `verification/YYYY-MM-DD/human_preview_review.json` exists, has `status: approved`, and binds the exact Preview SHA.

The LLM may not self-promote a Preview as successful.

Phase 1 must work without cross-episode memory.

Phase 2 may retrieve:

- recent approved visual pattern context, initially up to about five episodes
- up to about three context-relevant Production Lessons

A Lesson must contain:

```text
Context
What worked
Why
When not to use
```

Do not convert Lessons into Hard rules.

# Editorial diagnostics

## Reality Anchor

Use a Reality Anchor when moving from explanation to confirmation materially improves understanding.

Examples:

- primary source / IR
- Fed or government document
- real chart
- company/product reality anchor
- verified timeline

Do not use a document simply because one exists.

Issue `MISSED_REALITY_ANCHOR` only when a legal high-value anchor exists and would materially improve the viewer model over the selected abstraction.

## Visual Turn

A Visual Turn is not a color/layout change. It is a change in information structure that tracks the Story's understanding change.

Valid example:

```text
market interpretation card
→ actual IR receipt
```

because the function changes from interpretation to confirmation.

Invalid:

```text
blue card
→ red card
```

when the explanatory function is unchanged.

## Repetition

Repetition is allowed when it preserves a comparison frame, follows one chart through time, or exposes sequential differences in one document.

Issue `UNJUSTIFIED_REPETITION` when the Story meaning progresses but the visual function remains a generic card wall, or when materially different Evidence is visually collapsed so the difference becomes hard to read.

## Visual Receipt Only

Issue `VISUAL_RECEIPT_ONLY` when the Visual simply restates narration without making comparison, source boundary, grounding, chronology, scope, or uncertainty easier to understand.

A receipt is valid when it confirms provenance or makes a meaningful Gap/boundary directly visible.

## Decorative Novelty

Issue `DECORATIVE_NOVELTY` when a new Component, image, or motion is used but viewer belief does not progress.

Do not use new-component adoption rate as a KPI.

## Visual Economy

Prefer the minimum visual change required to maintain clear understanding.

The same chart, document, fox framing, or held screen may remain when continuity itself helps comprehension.

Issue:

- `UNNECESSARY_VISUAL_CHANGE` for switching that adds no explanatory value
- `OVERDIRECTED_VISUALS` when direction competes with narration, fragments attention, or makes the causal structure harder to follow

## Episode-level progression

Inspect Scene 1–9 as an explanatory sequence, not nine isolated design opportunities.

A strong progression may move through functions such as:

```text
contradiction
→ protagonist / reality anchor
→ hypothesis
→ Expected / Actual comparison
→ causal route
→ actual price-response test
→ peer comparison
→ verification boundary
→ synthesis
```

This is an example, not a fixed template order.

### Scene 4 → Scene 8 Visual Delta

State internally:

```text
Scene 4 visual understanding:
Scene 8 visual understanding:
What the visuals added, limited, or verified:
```

If the last line is only “more cards” or “more numbers,” issue `NO_VISUAL_PROGRESS` or the more specific finding.

### Scenes 6–8 Visual Deletion Test

Ask:

> If all Scenes 6–8 Visuals became generic text cards, would important understanding be lost?

Loss should include a real function such as:

- price reaction test
- peer divergence
- scope limit
- counterevidence
- verification condition
- reason-unknown boundary

If little is lost, late Visual value is weak.

## Cross-episode staleness — Phase 2 only

Do not penalize template repetition by itself.

Issue `CROSS_EPISODE_PATTERN_STALENESS` only when:

1. functional sequence strongly resembles multiple recent **human-approved** episodes,
2. a different legal expression is genuinely strong for today's Evidence, and
3. repeating the pattern has weak today-specific justification.

If Phase 2 context is unavailable, mark this diagnostic unassessed. Do not invent history.

## Reason unknown

`reason_unknown` can still have strong Visual Information Gain through:

- fixed chronology
- rejection of simple explanations
- confirmed vs unconfirmed boundaries
- peer divergence
- visible scope limits

Never create a causal graph that implies causality the Story does not support.

## Experimental components

Respect Component lifecycle:

```text
experimental → production → deprecated
```

Experimental Components are not normal production choices merely because they appear novel. Production promotion requires the Architecture-side lifecycle and human isolated/gallery review. This Skill does not perform that promotion.

# Fox boundary

`01_fox_character_bible.md` remains authoritative.

Visual review may check whether:

- fox expression matches the meaning transition
- fox presentation does not interrupt the market explanation

Do not invent fox history, holdings, trades, losses, university incidents, or life events.

# Acceptance checklist

A Phase 1 implementation/use is acceptable only when all are true:

- Visual Intent preserves Story belief progression
- `visualInformationGain` is semantic prose, not numeric scoring
- Provisional Direction does not pretend capability exists
- final selection uses only legal Candidate IDs
- Candidate ID ordering carries no recommendation meaning
- multiple-candidate Beats compare strongest alternative
- single-candidate Beats do not invent alternatives
- Reality Anchor is selected by editorial value, not mere availability
- repetition is not mechanically forbidden
- novelty is neutral
- reason_unknown stays causal-safe
- independent Critic does not inherit Director justification as truth
- Critic statuses use only PASS / REVISE / RETURN_TO_STORY / BLOCKED
- targeted patch changes Candidate ID only
- review rounds are capped at two
- no Hard Validator or machine contract is modified
- no Story meaning is rewritten
- Phase 1 works with Phase 2 memory absent
- human approval is required before Production Lesson / Recent Pattern promotion
