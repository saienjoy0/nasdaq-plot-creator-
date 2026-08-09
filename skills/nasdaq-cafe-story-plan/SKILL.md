---
name: nasdaq-cafe-story-plan
description: Transform a validated causal research dossier into an evidence-bound nine-scene understanding progression before fox narration is written.
version: 1.2.0
---

# NASDAQ Cafe Story Plan

## Purpose

This skill sits between the validated causal research dossier and Fox Script Authoring.
It does not redo market research and does not write final narration.

Its job is:

> Preserve facts, causality, timeline, confidence, counterevidence, and the fixed nine formal Scene roles, then arrange them so the viewer's market understanding progresses across Scenes 1–8.

The governing retention principle is:

> **朝のNASDAQカフェは、質問を連鎖させる番組ではない。視聴者の理解を連鎖させる番組である。**

A viewer should continue because a new piece of understanding makes the next comparison, test, boundary, counterevidence, implication, or verification valuable — not because an already-known answer was artificially withheld.

## Authority boundary

```text
Project Instructions
→ 02_editorial_bible.md
→ 01_fox_character_bible.md
→ 03_episode_production_spec.md
→ 04_entertainment_inquisitor.md
→ this Skill
```

This Skill may design explanation order. It may not change the accepted market meaning.

## Inputs

Required:
- validated causal research dossier JSON
- episode date and information cutoff
- current 01–04 source-of-truth documents

If evidence is insufficient, return to Causal Research / 02. Never use story design to fill evidence gaps.

## Output

```text
working/YYYY-MM-DD/story-engine/story_plan.json
```

The artifact must validate against:

```text
skills/nasdaq-cafe-story-plan/contracts/story_plan.schema.json
skills/nasdaq-cafe-story-plan/validators/validate_story_plan.py
```

No narration is generated at this stage.

---

## Stage 0 — Lock the dossier

Freeze before story design:
- lead / lead theme
- Expected / Actual / Gap
- Evidence IDs
- chronology
- confidence
- primary / amplifier / offset / counterevidence roles
- company / sector / NASDAQ causal scope
- unresolved points

Forbidden:
- inventing Expected
- strengthening confidence
- promoting a company cause to NASDAQ primary without evidence
- reordering real events for drama
- removing material counterevidence

## Stage 1 — Select the central contradiction

Select one supported dossier contradiction and bind it exactly.
The contradiction should explain the important overnight tension rather than merely repeat the largest headline.

## Stage 2 — Naive Explanation Test

Generate 1–4 plausible first-pass explanations and classify each using existing Evidence IDs as:

```text
survives
weakened
rejected
unresolved
```

Do not invent strawmen.
The purpose is to create explainable belief change when evidence rules a simple explanation in or out.

## Stage 3 — Headline-beyond discovery

Preserve the dossier's `editorial_handoff.headline_beyond_discovery` without strengthening it.
This is the minimum insight the episode must deliver beyond the headline.

## Stage 4 — Angle Competition

Create 3–5 structurally distinct angles using the same locked evidence.
Allowed types:

```text
contradiction
comparison
evaluation_axis_shift
misconception_disproof
causal_chain
reason_unknown
```

Select the angle that best:
1. explains the contradiction
2. reaches NASDAQ without overreach
3. creates a real explanatory turn
4. preserves counterevidence
5. leaves independent value for Scenes 6–8
6. delivers the headline-beyond discovery

## Stage 5 — Opening Promise

Scenes 1–2 must establish:
- direction
- contradiction
- an answerable promise/question

The opening must provide early value, not merely promise later value.
Do not hide evidence that is already needed to make the opening truthful.

Bad:

```text
「答えは後半で分かります」
```

Better structure:

```text
方向を示す
→ 単純説明では噛み合わないことを示す
→ そのズレを何で判定するかが次の価値になる
```

## Stage 6 — Build the fixed nine-scene Understanding Progression

The formal Scene order from 03 is fixed:

```text
Scene 1  direction_and_conclusion
Scene 2  contradiction
Scene 3  confirmed_facts
Scene 4  expected_actual_gap
Scene 5  global_context
Scene 6  market_reaction
Scene 7  entity_divergence
Scene 8  validation_points
Scene 9  fixed_closing
```

For every Scene record:
- `viewer_belief_before`
- `new_evidence_ids`
- `new_meaning`
- `viewer_belief_after`
- `continuation_reason`
- `connector`

### Understanding contract

Scenes 1–8 must each provide a concrete market-understanding payoff in `new_meaning`.

A payoff does **not** require a new causal explanation. Valid payoffs include:
- ruling out a simple explanation
- narrowing the uncertainty
- fixing the confirmed timeline
- understanding Expected / Actual / Gap
- making a peer difference concrete
- testing the hypothesis against price reaction
- limiting the causal scope
- understanding contrary evidence
- understanding what remains unknown
- learning what would strengthen or weaken the hypothesis

### Scenes 1–7 — continuation

Each Scene must have a non-empty `continuation_reason`.
A continuation reason is not required to be a question.
Allowed forms include:

```text
question
comparison
test
boundary
counterevidence
implication
verification
```

Examples:

```text
「NVIDIA側を見ると、この差を比較できる」
「この説明が値動きとも整合するか試す価値がある」
「個別半導体の説明をNASDAQ全体へ広げてよいか切り分ける必要がある」
```

### Scene 8 — closure

Scene 8 must have:

```text
continuation_reason = ""
```

It closes the narrative by:
- preserving strengthen/weaken verification points
- retaining important uncertainty/counterevidence
- recovering the opening promise as a more informed interpretation
- stating only a conclusion within the dossier confidence ceiling

Scene 8 is not required to create another reason to continue.

### Scene 9 — fixed close

Scene 9 has:
- no new Evidence IDs
- no new meaning
- no continuation reason
- connector `closing`

Do not repair an unresolved story in Scene 9.

## Stage 7 — Midpoint Turn

A real explanatory turn must occur in Scene 4, 5, or 6.
A turn changes the explanation, not just the amount of information.

Valid examples:
- a naive explanation is rejected
- peer comparison changes the evaluation axis
- price reaction meaningfully tests the hypothesis
- reason_unknown becomes the most defensible conclusion

## Stage 8 — Macro Open Loops

Maximum: 2.

Each loop records:
- open Scene
- question
- promised Evidence IDs
- close Scene
- resolution

Rules:
- close after opening
- close by Scene 8
- do not hide already-known evidence to manufacture suspense
- no fresh dramatic loop may survive into Scene 9

These are macro episode loops only. `continuation_reason` is local Scene-to-Scene value and does not need to be an open loop.

## Stage 9 — Closing Reframe

The bookend belongs in Scene 8.
The viewer should see the opening contradiction differently because of the evidence and meaning accumulated across the episode.

## Stage 10 — reason_unknown episodes

Do not create an answer for retention.
Valid payoffs include:
- candidate A conflicts with one piece of evidence
- candidate B remains weak for another reason
- a single cause cannot be isolated
- the missing data needed to distinguish candidates becomes clear

「分からない理由が分かる」 is a valid understanding payoff.

---

## Deterministic validation

Python validates structure and evidence safety only:
- schema / contract version
- dossier path and SHA
- Evidence ID existence
- contradiction and headline-discovery binding
- angle binding / confidence ceiling / causal scope
- material counterevidence preservation
- fixed Scene order and roles
- Scenes 1–8 have before / payoff / after
- Scenes 1–7 have `continuation_reason`
- Scene 8 has no continuation reason
- Scene 4–6 midpoint turn
- Scene 8 closing reframe
- macro loops close by Scene 8
- Scene 9 adds nothing new

Python does **not** judge whether prose is interesting, whether belief change is meaningful enough, or whether the continuation reason feels natural. That belongs to 04 / the Entertainment Critic.

Forbidden validators:
- question-mark counting
- requiring a question at every Scene end
- requiring new Evidence in every Scene
- requiring a fixed connective phrase
- requiring a surprise word
- judging interestingness from character count

## Downstream failure vocabulary

The Story Plan must make these detectable by the Entertainment Critic:

```text
REPEATED_CONCLUSION
NO_PAYOFF
NO_BELIEF_CHANGE
FAKE_OPEN_LOOP
DEAD_END_SCENE
PROCEDURAL_NARRATION
SCENE_ORDER_INTERCHANGEABLE
NO_MIDPOINT_TURN
NO_LATE_PAYOFF
OPENING_PROMISE_NOT_RECOVERED
ENDING_NOT_BOOKENDED
NO_NEW_EVIDENCE_OR_MEANING
```

Causal-safety failures remain critical and upstream-owned.
