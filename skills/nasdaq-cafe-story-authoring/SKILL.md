---
name: nasdaq-cafe-story-authoring
description: Convert an approved NASDAQ Cafe Story Plan into the fox's natural nine-scene narration without changing market causality, confidence, timing, counterevidence, or formal scene roles.
version: 1.1.1
---

# NASDAQ Cafe Story Authoring

## Purpose

This skill begins only after the causal dossier and Story Plan v1.2 pass their validators.
It writes the fox's spoken draft. It does not research new facts, choose a new lead, change Expected / Actual / Gap, or alter the nine formal Scene roles.

The key rule is:

> **The Story Plan is strict about meaning. The spoken surface is free.**

The fox must never sound like he is reading the production process.

## Inputs

Required:
- validated causal dossier
- validated Story Plan v1.2
- current 01–04 source-of-truth documents

## Output

`story_script.json` matching the Story Engine `story_script.schema.json`.

## Frozen editorial state

Never change:
- Evidence IDs and evidence meaning
- central contradiction / selected angle
- Expected / Actual / Gap
- chronology
- causal edge scope
- confidence
- material counterevidence
- unresolved factors
- Scene 1–9 order and formal roles

If natural prose would require changing these, return upstream instead.

---

## Stage 1 — Read each Scene as an Understanding Progression

For Scenes 1–7 read:
- `viewer_belief_before`
- `new_evidence_ids`
- `new_meaning`
- `viewer_belief_after`
- `continuation_reason`
- `connector`

For Scene 8 read:
- `viewer_belief_before`
- `new_evidence_ids`
- `new_meaning`
- `viewer_belief_after`
- `closing_reframe`
- strengthen / weaken / uncertainty material

The narration must deliver the meaning transition.
It must **not** recite those field names or their production-language paraphrases.

## Stage 2 — Give early value without exhausting the story

Scene 1 must provide:
- NASDAQ direction
- the contradiction
- a useful early interpretation/promise

Do not use artificial withholding such as:

```text
「答えは後半で分かります」
```

Do not fully exhaust the later proof either.
The viewer should already have learned something and still have a rational reason to inspect the mechanism.

## Stage 3 — Translate continuation reason into natural speech

`continuation_reason` is an internal meaning contract, not spoken copy.

It may surface as:
- a question
- a comparison
- a test
- a boundary
- counterevidence
- an implication
- a short contrast

Do **not** force every Scene to end with a question.

Bad procedural transitions:
- 「次に見ます」
- 「続いて確認します」
- 「時系列を固定します」
- 「ここまでが確認済み事実です」
- 「ではExpectedとActualです」
- 「仮説を検証します」

Better examples:
- 「しかも、見通しは市場予想にも勝っています。」
- 「ここでNVIDIA側を見ると、差が具体的になります。」
- 「じゃあ、この説明は実際の値動きとも合うのか。」
- 「ただ、NASDAQまでAMD一社で説明すると、話がきれいすぎます。」

## Stage 3.5 — Compress fact stacking with ABT logic

Use **And / But / Therefore (ABT)** as a diagnostic, not as a mandatory sentence template.

The purpose is to stop the middle of the episode from becoming:

```text
fact
AND fact
AND fact
AND another fact
```

when the viewer's explanatory model is not changing.

Before the spoken delivery pass, inspect adjacent Scenes 1–7. If two or more consecutive Scenes mainly add supporting facts, ask whether they can be expressed more economically as:

```text
known context / fact
BUT contradiction, boundary, or mismatch
THEREFORE updated interpretation
```

Example:

```text
雇用は予想を大きく下回った。
でもNASDAQとSOXは上昇した。
だから市場が採点していたのは、景気だけではない。
```

ABT is not permission to invent a contradiction. `BUT` must be supported by the locked evidence. `THEREFORE` may not strengthen causality, confidence, or scope beyond the Story Plan.

### Fact-stacking compression rule

If two consecutive Scenes are both primarily `support` or factual accumulation and neither changes the explanatory model materially:
- keep every fact required by the formal role and causal contract,
- compress duplicate explanation,
- move repeated setup wording within compatible Scenes if needed,
- make the next actual comparison/test/boundary arrive sooner.

Do **not** merge or remove formal Scenes.
Do **not** omit Expected / Actual / Gap, counterevidence, chronology, or required uncertainty for pacing.

A weak Scene may remain short when its formal role is necessary. It does not need artificial drama.

## Stage 4 — Preserve the fox

- first person is 「僕」
- one fox voice across all Scenes
- guide, not teacher or outside announcer
- short spoken sentences where useful
- IT analogy 0–2 total
- self-deprecating / poverty / loss / leverage joke 0–1 total
- jokes and analogies are optional
- never invent holdings, trades, P&L, wins/losses, or history

Fox character should emerge primarily from observation and guidance, not from inserted jokes.

## Stage 5 — Clarify without replacing the mechanism

For difficult concepts, use at most a short:
- concrete comparison
- daily-life example
- university-life example
- IT analogy

Return immediately to the actual market mechanism.

## Stage 6 — Protect late value

Scene 4 may reveal the central hypothesis.
That does not authorize Scenes 6–8 to become appendices.

Preferred functions:
- Scene 4: evaluation axis becomes visible
- Scene 5: concrete mechanism / comparison
- Scene 6: price reaction tests the hypothesis
- Scene 7: boundary and counterevidence define scope
- Scene 8: verification conditions + opening reframe + closure

Scene 6 and Scene 7 must each provide independent understanding value.

## Stage 7 — Scene 8 closes; Scene 9 exits

Scene 8 should make the opening contradiction look different after the evidence accumulated across the episode.
It must not manufacture another open loop.

Scene 9 uses the fixed closing meaning:

`以上、朝のNASDAQカフェでした。今日も気をつけて、いってらっしゃい。こちらはそろそろ、おやすみなさい。`

No new evidence, thesis, advice, or long disclaimer.

---

## Surface-only Spoken Delivery Pass

Run exactly one delivery pass after the factual draft is complete and before Entertainment Critic review.

Allowed changes:
- word order
- sentence length
- connectors
- spoken phrasing
- short fox reaction
- whether a question is explicit or implicit
- optional short analogy
- pauses/punctuation
- compression of repeated factual setup when all guarded meaning remains present

Forbidden changes:
- Claim ID
- Evidence ID
- numeric values
- Expected / Actual / Gap
- chronology
- claim type
- confidence
- causal scope
- counterevidence
- formal role

After the pass, run the causal before/after validator. Any guarded metadata difference fails.

## Causal claim metadata

Every material causal sentence must have a `causal_claims` entry.

- `fact`: direct fact
- `reported_interpretation`: reported market interpretation
- `grounded_inference`: evidence-bound editorial inference
- `unknown`: confidence `unknown`, scope `reason_unknown`

Non-fact confidence may never exceed dossier confidence.
Allowed scope ends at `nasdaq_support`.

## Counterevidence and uncertainty

Every material dossier counterevidence item must remain represented and listed in `retained_counterevidence_ids`.
Missing data must remain in `unresolved_points`.

## Final self-check

Before Critic handoff:
- nine Scenes present and ordered
- formal roles match Story Plan
- Scenes 1–8 each deliver their planned understanding payoff
- Scenes 1–7 naturally justify continuation without question-factory behavior
- adjacent Scenes are not merely fact stacking when a truthful ABT compression can expose the meaning faster
- Scene 6 and 7 have independent value
- Scene 8 closes the opening promise
- Scene 9 adds nothing new
- procedural narration is not dominant
- first person is 「僕」
- no investment advice or deterministic price prediction
- material counterevidence and unresolved factors remain
- causal metadata is unchanged
