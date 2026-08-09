---
name: nasdaq-cafe-entertainment-critic
description: Independently review a NASDAQ Cafe story for interest, clarity, understanding progression, fox voice, and late payoff while preserving the frozen causal contract.
version: 1.1.0
---

# NASDAQ Cafe Independent Entertainment Critic

## Purpose

Review the completed fox draft using 04 without inheriting the author's self-justification.

The Critic may improve presentation. It may not change facts, chronology, Expected / Actual / Gap, confidence, counterevidence, causal scope, or the nine formal Scene roles.

The governing principle is:

> **Do not ask whether the script contains enough questions. Ask whether the viewer understands something new, and whether that new understanding makes the next Scene valuable.**

## Inputs

Required:
- causal dossier
- Story Plan v1.2
- story script draft
- current 01–04

## Six scored dimensions

Score 0–5:
1. `opening` — direction, contradiction, and useful promise/value in the opening
2. `progression` — Scenes 1–8 create non-redundant understanding changes
3. `discovery` — the headline-beyond discovery is delivered
4. `clarity` — difficult mechanisms become understandable without distortion
5. `fox_voice` — one natural fox voice, guide-like rather than procedural
6. `late_payoff` — Scenes 6–8 remain necessary and Scene 8 closes/reframes the opening

Normal pass requires:
- no immediate-fail condition
- every score >= 3
- total >= 25/30
- no unresolved major/critical finding

## Scene checks

### Scenes 1–7 — Progression Check

For each Scene record:

```text
mode = continue
payoff_delivered
belief_changed
continuation_reason_natural
procedural_language_dominant
```

`closure_effective` and `opening_promise_recovered` are null.

A Scene may continue by question, comparison, test, boundary, counterevidence, implication, or verification.
Do not penalize a Scene merely because it does not end with a question mark.

### Scene 8 — Closure Check

Record:

```text
mode = close
payoff_delivered
belief_changed
closure_effective
opening_promise_recovered
procedural_language_dominant
```

`continuation_reason_natural` is null.

Scene 8 must **not** be failed for having no next-scene hook. Its job is to close the analytical story before the fixed Scene 9 exit.

## Immediate narrative concerns

Detect especially:
- the opening fully exhausts the story
- adjacent Scenes repeat the same conclusion
- facts change but understanding does not
- a Scene has no payoff
- a continuation exists only because an already-known answer was hidden
- a Scene dead-ends before Scene 8
- procedural transitions dominate
- Scene order is interchangeable
- no meaningful midpoint turn
- Scenes 6–8 are appendices
- Scene 8 is only a schedule/checklist
- Scene 8 does not recover the opening promise
- abstract editorial language replaces human explanation
- generic narrator voice replaces the fox

## Finding vocabulary

Use the schema vocabulary, including:

```text
NO_PAYOFF
NO_BELIEF_CHANGE
FAKE_OPEN_LOOP
DEAD_END_SCENE
PROCEDURAL_NARRATION
NO_LATE_PAYOFF
OPENING_PROMISE_NOT_RECOVERED
ENDING_NOT_BOOKENDED
NO_NEW_EVIDENCE_OR_MEANING
```

Causal-safety findings remain critical:

```text
CAUSALITY_DRIFT
COUNTEREVIDENCE_REMOVED
TIMELINE_DRIFT
NASDAQ_SCOPE_OVERREACH
```

If a factual/causal issue appears, return upstream instead of disguising it as a style fix.

## Fake Open Loop definition

A fake open loop exists when:
- the evidence required to answer is already available in the current Scene,
- the author intentionally withholds that answer only to preserve suspense,
- the next Scene adds no genuinely new evidence, meaning, comparison, test, or boundary.

Do not confuse a valid continuation with a fake loop.

Valid:

```text
Scene gives a payoff
→ payoff makes a peer comparison or market test newly useful
```

Invalid:

```text
Scene possesses the answer
→ says "答えは後半で"
→ next Scene merely reveals the withheld answer
```

## Late payoff rule

Scene 4 may reveal the central hypothesis.
That is not a failure.

The Critic must instead ask whether Scenes 6–8 still add distinct value:
- market reaction test
- boundary / counterevidence
- uncertainty / falsification condition
- closing reframe

If Scene 4 makes the rest optional, issue `NO_LATE_PAYOFF`.

## Targeted patch policy

If review is not pass, issue only the smallest safe operations:
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
- remove/reorder formal Scenes
- merge away a formal role
- patch Scene 9
- create a new causal explanation
- strengthen confidence
- remove important counterevidence

## Surface-only preference

For `PROCEDURAL_NARRATION`, `ABSTRACT_EDITORIAL_LANGUAGE`, `FOX_VOICE_ABSENT`, or a weak continuation, prefer surface-only rewrite first.

Do not touch Claim IDs, Evidence IDs, numbers, timeline, confidence, scope, or counterevidence unless restoring them to the frozen contract.

## Re-review

After patching:
1. run causal before/after validation
2. run this Critic again from the revised artifact
3. maximum two rounds

If the second round still fails, return to the owning upstream stage.

## Final title / thumbnail boundary

This Critic checks `opening_promise` recovery, not final title/thumbnail wording.

Final title and thumbnail promise audits occur only after the final episode package has been assembled, because those surfaces may not yet exist at Story Engine review time.

## Acceptance

A pass review plus a passing causal bundle validator is required for Story Engine creative acceptance.
External Independent Critic certification may remain optional under the current production policy; if not externally certified, that status must remain explicit.
