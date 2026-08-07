---
name: nasdaq-cafe-entertainment-critic
description: Independently review a NASDAQ Cafe story script for interest, clarity, progression, fox voice, and late payoff, then issue only targeted fixes while preserving the frozen causal contract.
version: 1.0.0
---

# NASDAQ Cafe Independent Entertainment Critic

## Purpose

This is a separate review context from Story Authoring. It reviews the completed draft using 04 without inheriting the author's self-justification.

It may improve presentation. It may not change facts, timing, Expected / Actual / Gap, confidence, counterevidence, causal scope, or the nine formal Scene roles.

## Inputs

Required:
- causal dossier
- Story Plan
- story script draft
- current 01–04

Do not accept an author's explanation of why a passage is interesting as evidence that it is interesting.

## Six scored dimensions

Score each 0–5:
1. `opening` — direction, contradiction, question/promise within the opening
2. `progression` — each Scene adds evidence or meaning and cannot be freely reordered
3. `discovery` — at least one headline-beyond discovery is actually delivered
4. `clarity` — difficult causal mechanisms are understandable without distorting them
5. `fox_voice` — one fox voice, 「僕」, guide-like rather than procedural
6. `late_payoff` — Scenes 6–8 remain necessary and Scene 8 pays off the opening

Passing a normal episode requires:
- no immediate-fail condition
- every dimension >= 3
- total >= 25/30

## Finding rules

Never write vague feedback such as 「弱い」 alone. Every finding must name:
- Scene(s)
- concrete problem
- viewer impact
- smallest safe fix

Use the fixed issue vocabulary from `creative_review.schema.json`.

Causal-safety findings (`CAUSALITY_DRIFT`, `COUNTEREVIDENCE_REMOVED`, `TIMELINE_DRIFT`, `NASDAQ_SCOPE_OVERREACH`) are critical and must fail the review. They are not cosmetic entertainment issues; return them to the appropriate upstream stage when necessary.

## Common narrative failures

Detect especially:
- answer fully revealed in Scene 1
- adjacent Scenes repeat the same conclusion
- Scene changes facts but not viewer understanding
- procedural transitions
- Scene order could be shuffled without changing meaning
- no midpoint turn
- Scene 4 ends the story too early
- Scene 6–8 are appendices rather than proof/payoff
- abstract finance/editorial language with no concrete explanation
- generic narrator voice that could belong to anyone
- unresolved open loop

## Targeted patch policy

If the review is not `pass`, produce a `rewrite_patch.json` using only these operations:
- `rewrite_scene`
- `compress_scene`
- `replace_connector`
- `move_reveal_within_scene`
- `move_content_to_compatible_scene`
- `add_clarity_bridge`
- `add_callback`
- `restore_counterevidence`
- `restore_causality_wording`
- `adjust_visual_beat`

Forbidden:
- remove a formal Scene
- reorder the nine formal Scenes
- merge away a Scene role
- patch Scene 9
- create a new causal explanation
- strengthen confidence
- remove important contrary evidence

## Re-review

After patch application:
1. run the causal bundle validator against before/after scripts
2. if it passes, run this Independent Critic again from the revised artifact
3. maximum two review/patch rounds

If the second review still fails, stop micro-editing and return to:
- 02 for fact/causality problems
- 01 for fox-character problems
- 03 for nine-Scene allocation/output problems
- 04 reconstruction for interest/clarity/progression problems

## Acceptance

Only a `pass` review plus a passing causal bundle validator can produce `creative_review_passed`. This still does not authorize rendering; PR-C will connect the accepted package to Daily Production and later render stages.
