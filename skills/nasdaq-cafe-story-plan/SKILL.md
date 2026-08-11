---
name: nasdaq-cafe-story-plan
description: Transform a validated causal research dossier into an evidence-bound nine-scene understanding progression before fox narration is written.
version: 1.2.2
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

A second governing principle is:

> **結論を遅らせるのではなく、結論を進化させる。**

The opening may reveal the direction and even the provisional driver. It must not consume the final synthesis. By Scene 8, the viewer must understand something materially deeper, narrower, more branched, or better tested than they did around Scene 4.

A third planning principle is:

> **面白さは、Evidenceによって視聴者の説明モデルが有意味に更新される量で作る。**

This is an editorial Information Gain concept, not a numeric formula. New information is useful only when it changes, narrows, branches, tests, or clarifies the viewer's model enough to make the next Scene more valuable.

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
3. creates a real evidence-backed understanding upgrade
4. preserves counterevidence
5. leaves independent value for Scenes 6–8
6. delivers the headline-beyond discovery
7. creates more than one meaningful Evidence-backed model update instead of one reveal surrounded by factual filler

Do not choose an angle merely because it can manufacture a reversal. A straight causal chain can still be interesting if later evidence reveals mechanism, scope, scale, branching, or a meaningful verification boundary.

Before selecting, compare the likely **Understanding Gain curve** of each angle. Prefer the angle in which several Scenes change the explanatory model for distinct reasons rather than one angle that spends most of the runtime accumulating support for an answer already understood.

## Stage 5 — Opening Promise

Scenes 1–2 must establish:
- direction
- contradiction
- an answerable promise/question

The opening must provide early value, not merely promise later value.
Do not hide evidence that is already needed to make the opening truthful.

The opening should normally provide a **provisional understanding**, not the full final synthesis.

Bad:

```text
「答えは後半で分かります」
```

Also bad:

```text
Scene 1 already states the primary driver, all amplifiers, all counterevidence, the scope boundary, and the final synthesis.
```

Better structure:

```text
方向を示す
→ 暫定的に何が効いたかを示す
→ その説明の範囲・別エンジン・反対材料・実反応のどれを確認すると理解が深くなるかを残す
```

This is the `HOOK_EXHAUSTS_STORY` boundary: early value is required, early exhaustion is not.

### Information Gap boundary

Use an **honest unresolved mismatch**, not a hidden answer.

A strong opening can tell the viewer:
- the provisional driver,
- what concrete part of the market does not yet fit that driver,
- why resolving that mismatch matters.

It does not need to state every later numeric receipt immediately if those values are not required to make the opening truthful.

Good:

```text
金利がまず鍵です。
ただ、半導体を全部この説明に入れると、一銘柄だけ発表時刻と値動きが合いません。
```

Bad:

```text
答えは知っているけれど後半まで隠します。
```

Never withhold evidence that changes the truth of the provisional statement. Information Gap may organize disclosure; it may not manufacture ignorance.

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

**Information addition is not automatically an understanding upgrade.**

A new statistic, another headline, or another supporting factor does not count as progression if the viewer's explanatory model is unchanged.

For Scenes 1–8:

```text
viewer_belief_before
!=
viewer_belief_after
```

The difference must be about market understanding, not merely wording.

### Internal Understanding Gain classification

Before narration, classify each Scene's main gain internally. This is a planning aid and is **not** a required Story Plan schema field yet.

Allowed primary gain types:

```text
support
narrow
branch
disproof
mechanism_reveal
verification
uncertainty_reduction
synthesis
```

Definitions:
- `support`: strengthens an already-understood model without materially changing it
- `narrow`: limits scope, confidence, or applicability
- `branch`: separates one apparent explanation into multiple causal engines
- `disproof`: rejects a plausible simple explanation
- `mechanism_reveal`: shows how the effect travels rather than only that it exists
- `verification`: tests the provisional model against timing, price, peers, or another direct observation
- `uncertainty_reduction`: makes what remains unknown more specific
- `synthesis`: combines prior model updates into the final interpretation

`support` is valid but usually low Information Gain. A Story Plan with many consecutive `support` Scenes is at risk of becoming a correct but dull evidence receipt.

Do not assign a stronger gain type than the evidence supports merely to improve the curve.

### Payoff-drought planning check

Before approving the plan, inspect Scenes 1–8 for stretches where facts accumulate but the explanatory model barely moves.

If two or more consecutive Scenes are primarily factual accumulation or `support`:
- preserve the fixed formal roles,
- keep mandatory facts and Evidence bindings,
- make those Scenes concise,
- move the next real comparison, test, boundary, or model update forward within chronology-compatible Scene roles when possible.

Do not invent a surprise to avoid a drought. A short necessary low-gain Scene is better than fake drama.

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

## Stage 7 — Evidence-backed Understanding Upgrade

The existing JSON field remains named `midpoint_turn` for compatibility, but its semantic contract is now **Understanding Upgrade**, not mandatory theatrical reversal.

It must occur in Scene 4, 5, or 6 and must be backed by one or more real Evidence IDs.

A valid upgrade changes, branches, narrows, or materially tests the viewer's explanatory model. Valid forms include:

```text
turn
branch
boundary
scale_reveal
mechanism_reveal
disproof
reason_unknown_payoff
```

Examples:
- a naive explanation is rejected
- the same sector move splits into macro and company-specific engines
- a company explanation is narrowed because the index/peer reaction does not match
- price timing materially tests the provisional hypothesis
- a hidden mechanism explains why the same headline produced different reactions
- reason_unknown becomes the most defensible conclusion after competing explanations fail

Invalid upgrade:

```text
暫定解：弱い雇用で金利観測が下がった
追加情報：原油も下がった
最終解：弱い雇用で金利観測が下がった
```

That is support, not an upgrade.

The legacy `midpoint_turn.what_changes` must explicitly state the before→after model change. The turn Scene's `viewer_belief_before` and `viewer_belief_after` must reflect that same change.

Do not manufacture a reversal. If the evidence does not support a reversal, use a genuine branch, boundary, mechanism, verification result, or reason-unknown payoff. If even those are unavailable, shorten the episode rather than invent late drama.

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

## Stage 9 — Late Value and Closing Reframe

The bookend belongs in Scene 8.
The viewer should see the opening contradiction differently because of the evidence and meaning accumulated across the episode.

The key test is not whether Scene 4 already reveals the central hypothesis. It may.

The key test is:

> **If Scenes 6–8 were removed, what material understanding would the viewer lose?**

A valid answer must name a concrete evidence-backed gain such as:
- a second causal engine
- a scope limit
- a disconfirming peer
- an actual price-reaction test
- a mechanism the headline did not reveal
- a falsification condition
- a reason why one-cause attribution remains unresolved

If no material understanding is lost, the late section is an appendix and the plan is not ready.

Scene 8 must also be materially more informed than Scene 4. Repeating the Scene 4 answer plus a disclaimer is not a closing reframe.

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
- Scenes 1–8 have structurally distinct before / after text
- Scenes 1–7 have `continuation_reason`
- Scene 8 has no continuation reason
- Scene 4–6 Understanding Upgrade has evidence
- Scene 8 understanding is structurally distinct from Scene 4 understanding
- Scene 8 closing reframe is not identical to the opening promise
- macro loops close by Scene 8
- Scene 9 adds nothing new

Python does **not** judge whether prose is interesting, whether a Scene's Information Gain is high or low, whether a `support` stretch is boring, whether the model change is semantically meaningful enough, or whether the late value is genuinely worth watching. Those belong to 04 / the Entertainment Critic.

Forbidden validators:
- question-mark counting
- requiring a question at every Scene end
- requiring new Evidence in every Scene
- requiring a fixed connective phrase
- requiring a surprise word
- assigning Information Gain from Evidence count
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
NO_UNDERSTANDING_UPGRADE
FAKE_UNDERSTANDING_UPGRADE
HOOK_EXHAUSTS_STORY
NO_LATE_PAYOFF
OPENING_PROMISE_NOT_RECOVERED
ENDING_NOT_BOOKENDED
NO_NEW_EVIDENCE_OR_MEANING
FACT_STACKING
LOW_INFORMATION_GAIN
PAYOFF_DROUGHT
WEAK_SURPRISE
```

Causal-safety failures remain critical and upstream-owned.
