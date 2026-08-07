---
name: nasdaq-cafe-story-authoring
description: Convert an approved NASDAQ Cafe Story Plan into the fox's nine-scene narration without changing market causality, confidence, timing, counterevidence, or the formal scene roles.
version: 1.0.0
---

# NASDAQ Cafe Story Authoring

## Purpose

This skill begins only after the causal dossier and Story Plan have passed their validators. It writes the fox's spoken draft. It does not research new facts, choose a new lead, change Expected / Actual / Gap, or alter the nine formal scene roles.

## Inputs

Required:
- validated causal dossier
- validated `story_plan.json`
- current 01–04 source-of-truth documents

Optional:
- approved historical style memory, only when already allowed by the current memory contract

## Output

`story_script.json` matching the Story Engine `story_script.schema.json`.

## Non-negotiable boundary

Treat the following as frozen editorial state:
- Evidence IDs and source meaning
- central contradiction and selected angle
- Expected / Actual / Gap
- causal edge scope
- confidence
- important contrary evidence
- unresolved factors
- Scene 1–9 order and formal roles

If the prose would be easier only by changing one of these, stop and return the artifact to the owning upstream stage.

## Authoring workflow

### Stage 1 — Read the Story Plan as viewer-state transitions

For each Scene, read:
- `viewer_belief_before`
- `new_evidence_ids`
- `new_meaning`
- `viewer_belief_after`
- `remaining_question`
- `connector`

The narration must make that change legible. A Scene that merely restates the previous conclusion is not complete.

### Stage 2 — Protect the opening information gap

Scene 1 must give:
- NASDAQ direction
- the contradiction
- the question or promise

Do not fully resolve the central question in Scene 1. The viewer should know what is strange and why it matters, but still need Scenes 3–6 to understand the mechanism.

### Stage 3 — Write causal connectors, not slide transitions

Prefer connections whose meaning is equivalent to `but`, `therefore`, `contrast`, or `callback`.

Avoid procedural narration such as:
- 「次に見ます」
- 「続いて確認します」
- 「ではExpectedとActualです」

A connection must explain why the next evidence changes the current understanding.

### Stage 4 — Preserve the fox

- first person is 「僕」
- the fox is a guide, not an outside announcer or teacher
- all Scenes are voiced by the same fox
- IT analogy: 0–2 per episode
- self-deprecating / poverty / loss / leverage joke: total 0–1
- jokes and analogies are optional and must return immediately to the real market mechanism
- never invent holdings, trades, P&L, past wins/losses, or personal market history

Fox character comes mainly from the way the audience is guided: short observations, human-scale comparisons, and a feeling of checking the market together.

### Stage 5 — Make difficult mechanisms understandable

When a concept is difficult, use one of:
- a concrete comparison
- a short daily-life example
- a university-life example
- a short IT analogy

Then return to the actual market structure in the next sentence. Do not replace the real mechanism with the analogy.

### Stage 6 — Keep the late payoff alive

Scene 4 may state the central hypothesis, but it must not make Scenes 6–8 unnecessary.

Preferred progression:
- Scene 4: hypothesis becomes visible
- Scene 5: context explains why the gap matters
- Scene 6: market reaction tests the hypothesis and acts as the preferred midpoint turn
- Scene 7: comparison defines the hypothesis's range and limit
- Scene 8: validation points and closing reframe

### Stage 7 — Scene 9 is fixed closing

Use the meaning of:

`以上、朝のNASDAQカフェでした。今日も気をつけて、いってらっしゃい。こちらはそろそろ、おやすみなさい。`

Punctuation and natural pauses may vary, but do not add evidence, a new thesis, investment advice, or a long disclaimer.

## Causal claim metadata

Every material causal sentence must have a `causal_claims` entry.

- `fact`: directly supported fact; confidence may follow the evidence
- `reported_interpretation`: reported market interpretation; may not exceed dossier central confidence
- `grounded_inference`: editorial inference; may not exceed dossier central confidence
- `unknown`: must remain confidence `unknown`, scope `reason_unknown`

Allowed scope ends at `nasdaq_support`. This Story Engine may not promote a company-specific event to `nasdaq_primary`.

## Counterevidence and uncertainty

Every dossier `contrary_evidence` item with `effect_on_confidence=material` must remain represented in the script and listed in `retained_counterevidence_ids`.

If the dossier has unresolved factors, record them in `unresolved_points`. Do not convert missing data into a clean answer for narrative convenience.

## Final self-check

Before handing the draft to the Independent Critic:
- nine Scenes are present and in fixed order
- Scene roles match Story Plan
- Scene 1 preserves an information gap
- every Scene 2–8 changes understanding
- Scene 6 is a real test/turn when evidence permits
- Scene 8 contains the closing reframe
- Scene 9 contains no new evidence
- first person is 「僕」
- no investment advice or deterministic price prediction
- material counterevidence and unresolved factors remain
- all causal claim IDs have Evidence IDs and unchanged confidence/scope
