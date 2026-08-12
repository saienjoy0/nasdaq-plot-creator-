---
name: nasdaq-cafe-entertainment-critic
description: Review a NASDAQ Cafe story for interest, clarity, understanding progression, fox voice, and late payoff while preserving the frozen causal contract.
version: 1.3.0
---

# NASDAQ Cafe Entertainment Critic

## Purpose

Review the completed fox draft using 04 without accepting the author's self-justification as evidence of quality.

The Critic may improve presentation. It may not change facts, chronology, Expected / Actual / Gap, confidence, counterevidence, causal scope, or the nine formal Scene roles.

The governing principle is:

> **Do not ask whether the script contains enough questions. Ask whether the viewer understands something new, and whether that new understanding makes the next Scene valuable.**

A second governing principle is:

> **Score is secondary. A script that fails the understanding-upgrade or late-value hard gates cannot PASS even at 29/30.**

A third interest principle is:

> **Interestingness comes from Evidence-backed model updates, not from the number of facts, headlines, or dramatic words.**

Treat Information Gain as a semantic editorial judgment. Do not infer it mechanically from Evidence count or text length.

## Reviewer modes

The 04 review itself is mandatory. External certification is not.

Two reviewer labels are allowed:

```text
editorial_critic
independent_critic
```

Use `editorial_critic` for the normal ChatGPT-side 04 review when no separately proven external model process executed.

Use `independent_critic` only when the review actually came from the external Critic path. A reviewer label alone does not prove certification; certification still requires the external request/receipt and an `orchestrator_signed` attestation.

Never relabel an editorial review as independent merely to pass a gate.

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
- all hard narrative gates below pass

## Hard narrative gates — run before scoring

### Gate A — Hook Exhaustion Test

Ask:

> By the end of Scene 1–2, has the script already stated the primary driver, the main amplifiers, the important boundary/counterevidence, and the final synthesis so completely that the rest is only documentation?

If yes, issue `HOOK_EXHAUSTS_STORY` as major or critical.

Early value is good. Early exhaustion is not.

Allowed:

```text
「鍵は金利です」
```

Not allowed as a complete opening synthesis:

```text
「雇用悪化で金利観測が下がり、原油も下がり、好決算も重なり、ただし全面高ではなく…」
```

when those are the episode's remaining discoveries.

### Gate B — Understanding Upgrade Authenticity Test

The Story Plan field is still named `midpoint_turn`, but review it as an **Evidence-backed Understanding Upgrade**.

A real upgrade changes, branches, narrows, or materially tests the explanatory model.

Valid forms include:
- turn
- branch
- boundary
- scale reveal
- mechanism reveal
- disproof
- reason-unknown payoff

A mere extra fact or extra supporting factor is not an upgrade.

If the nominated upgrade is only information addition, issue `NO_UNDERSTANDING_UPGRADE`.

If the author manufactured a turn by withholding evidence that was already available, issue `FAKE_UNDERSTANDING_UPGRADE` or `FAKE_OPEN_LOOP`.

Do **not** demand a theatrical reversal when evidence does not support one.

### Gate C — Scene 4 → Scene 8 Understanding Delta

Ask explicitly:

> What does the viewer understand in Scene 8 that they did not already understand by Scene 4?

The answer must be concrete and evidence-backed.

Examples of valid delta:
- macro move vs company-specific move separated
- causal scope narrowed
- a peer or price reaction limits the simple explanation
- the actual transmission mechanism becomes visible
- a one-cause explanation becomes reason_unknown
- falsification conditions become materially clearer

Invalid delta:

```text
Scene 4: weak jobs lowered rate-hike expectations and helped tech.
Scene 8: weak jobs lowered rate-hike expectations and helped tech, but causality cannot be proven perfectly.
```

That is the same answer plus a disclaimer.

If there is no material delta, issue `NO_LATE_PAYOFF` as major or critical.

### Gate D — Late Value Deletion Test

Ask:

> If Scenes 6–8 were removed, what important understanding would the viewer lose?

The lost value must be stated concretely.

If the answer is only:
- extra examples
- another supporting statistic
- repeated caution
- a checklist that does not change the interpretation

then issue `NO_LATE_PAYOFF`.

The late section is not allowed to exist merely because the format has nine Scenes.

### Gate E — No Forced Drama

If the evidence does not support a reversal, do not fail the script for lacking one.
A branch, boundary, mechanism reveal, price test, or reason-unknown payoff can satisfy the upgrade requirement.

If the only way to make the episode pass would be to invent a dramatic reversal, return upstream or shorten the episode instead.

## Interest-quality diagnostics — run after hard gates, before scoring

These diagnostics catch stories that are causally safe and structurally valid but still feel like a correct lecture or evidence receipt.

They do **not** override causal truth. Never create, exaggerate, or reorder a fact merely to avoid one of these findings.

### `FACT_STACKING`

Issue when adjacent Scenes mainly add facts or supporting headlines while the explanatory model remains effectively unchanged.

Typical pattern:

```text
fact A
AND fact B
AND fact C
```

without a meaningful comparison, boundary, test, mechanism, or implication.

This is usually a pacing/authoring problem. Prefer compression, a clearer ABT relation, or earlier arrival at the next genuine model update while keeping formal Scene roles intact.

### `LOW_INFORMATION_GAIN`

Ask:

> After learning this Scene, what can the viewer explain differently that they could not explain before it?

If the answer is only "the same hypothesis now has one more supporting fact," the Scene may have low Information Gain.

`support` is not automatically a failure. A required support Scene can be brief. Issue this finding when the **narrative weight or emphasis** is disproportionate to the understanding gained. At this pre-TTS review stage, do not infer actual runtime from word count; only use measured duration if it is explicitly present in the sealed review input.

### `PAYOFF_DROUGHT`

Issue when a multi-Scene stretch makes the viewer wait too long between meaningful understanding rewards.

A drought is not measured by seconds or a fixed Scene count alone. Judge whether the viewer receives a meaningful model update, useful narrowing, direct test, mechanism reveal, or consequential counterevidence often enough for the episode to keep advancing.

Two or more consecutive low-gain/support-heavy Scenes are a strong review signal, not an automatic failure.

### `WEAK_SURPRISE`

"Surprise" here means a meaningful Evidence-backed change in the viewer's prediction or explanatory model, not theatrical shock.

Issue when the nominated Understanding Upgrade exists structurally but has little explanatory consequence.

Ask:

> If this upgrade disappeared, would the final model materially change?

If no, the upgrade is weak even if it technically changes wording or adds evidence.

Do not use this finding simply because the episode lacks a twist. A strong verification, boundary, mechanism reveal, or reason-unknown conclusion can be highly interesting without surprise theater.

### Severity guidance for interest findings

`FACT_STACKING`, `LOW_INFORMATION_GAIN`, `PAYOFF_DROUGHT`, and `WEAK_SURPRISE` may be `minor` when localized and safely compressible.

Use `major` when the issue materially damages progression or discovery across multiple Scenes and the script should not PASS without a targeted rewrite.

If the same defect also means there is no real Understanding Upgrade or late payoff, use the stronger existing hard finding (`NO_UNDERSTANDING_UPGRADE` / `NO_LATE_PAYOFF`) rather than relying only on an interest diagnostic.

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

A PASS review should mark `payoff_delivered=true` and `belief_changed=true` for every Scene 1–7. If either is false, the Scene requires a matching finding and the review cannot PASS until fixed.

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

A PASS review requires Scene 8 to deliver a payoff, change understanding relative to the earlier provisional answer, close effectively, and recover the opening promise at a deeper level.

## Immediate narrative concerns

Detect especially:
- the opening fully exhausts the story
- adjacent Scenes repeat the same conclusion
- facts change but understanding does not
- consecutive Scenes stack facts without enough explanatory gain
- a Scene has no payoff
- a continuation exists only because an already-known answer was hidden
- a Scene dead-ends before Scene 8
- procedural transitions dominate
- Scene order is interchangeable
- no evidence-backed understanding upgrade
- the nominated upgrade is only an extra supporting fact
- a structurally valid upgrade has weak explanatory consequence
- Scenes 6–8 are appendices
- a multi-Scene stretch has a payoff drought
- Scene 8 is only a schedule/checklist
- Scene 8 does not recover the opening promise
- Scene 8 repeats the Scene 4 answer plus a disclaimer
- abstract editorial language replaces human explanation
- generic narrator voice replaces the fox

## Temporal Evidence Loop diagnostics

Run these after normal causal truth has been frozen. They may improve interest and clarity, but may not change Current Evidence, chronology, causal scope, counterevidence, confidence, VO meaning, or Cross-Market status.

### `TEMPORAL_RECAP_OVERLOAD`

Past-episode explanation is long enough that today's Current Evidence and contradiction arrive late. Compress the recap; do not delete a material carryover result.

### `TEMPORAL_CONTINUITY_WITHOUT_PAYOFF`

The script mentions a prior VO/episode, but Current Evidence does not update, narrow, weaken, contradict, or otherwise improve today's explanation. Keep it internal-only or remove the spoken recap.

### `CROSS_MARKET_DECORATION`

Asia/Cross-Market material is shown because it exists, not because it changes the NASDAQ explanation. `not_material` Cross-Market evidence must not be forced into the story.

### `TEMPORAL_VISUAL_EVIDENCE_MISSING`

A material Temporal claim is adopted as spoken/on-screen, but the reviewed Visual Evidence Plan does not bind the required `TVE-*` information need to an existing Visual Source/Financial Visual path.

### `FALSE_TEMPORAL_CAUSALITY`

The story treats an earlier market move as the cause merely because it happened first, or skips the material H1/H2/H3/H4 alternative test. This is **Critical** and returns to Causal Research / 02; never repair it as surface wording alone.

Temporal continuity is mandatory internally but optional on-screen. Scene 8 may state a falsification condition as closure; do not turn it into “明日の動画で答え合わせします”.

## Finding vocabulary

Use the schema vocabulary, including:

```text
NO_PAYOFF
NO_BELIEF_CHANGE
FAKE_OPEN_LOOP
DEAD_END_SCENE
PROCEDURAL_NARRATION
HOOK_EXHAUSTS_STORY
NO_UNDERSTANDING_UPGRADE
FAKE_UNDERSTANDING_UPGRADE
NO_LATE_PAYOFF
OPENING_PROMISE_NOT_RECOVERED
ENDING_NOT_BOOKENDED
NO_NEW_EVIDENCE_OR_MEANING
FACT_STACKING
LOW_INFORMATION_GAIN
PAYOFF_DROUGHT
WEAK_SURPRISE
TEMPORAL_RECAP_OVERLOAD
TEMPORAL_CONTINUITY_WITHOUT_PAYOFF
CROSS_MARKET_DECORATION
TEMPORAL_VISUAL_EVIDENCE_MISSING
```

Legacy `NO_MIDPOINT_TURN` may be used only when the Story Plan lacks any nominated upgrade at all. Prefer `NO_UNDERSTANDING_UPGRADE` when an upgrade exists structurally but does not actually change the explanatory model.

Causal-safety findings remain critical:

```text
CAUSALITY_DRIFT
COUNTEREVIDENCE_REMOVED
TIMELINE_DRIFT
NASDAQ_SCOPE_OVERREACH
FALSE_TEMPORAL_CAUSALITY
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

The Critic must instead ask whether Scenes 6–8 still add distinct value and whether Scene 8 is materially more informed than Scene 4.

Distinct late value can come from:
- market reaction test
- second causal engine
- mechanism reveal
- boundary / counterevidence
- uncertainty / falsification condition
- closing reframe

If Scene 4 makes the rest optional, issue `NO_LATE_PAYOFF`.

## Hard-finding severity rule

The following findings may not be downgraded to `minor` merely to preserve a PASS:

```text
HOOK_EXHAUSTS_STORY
NO_UNDERSTANDING_UPGRADE
FAKE_UNDERSTANDING_UPGRADE
NO_LATE_PAYOFF
OPENING_PROMISE_NOT_RECOVERED
ENDING_NOT_BOOKENDED
```

Use at least `major` unless the same defect is causal-safety critical.

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

For `FACT_STACKING`, `LOW_INFORMATION_GAIN`, or `PAYOFF_DROUGHT`, prefer `compress_scene`, `replace_connector`, or compatible movement of already-supported content before any broader rewrite.

For `WEAK_SURPRISE`, first ask whether existing evidence can play a more explanatory comparison/test/boundary role. Never invent a turn.

Forbidden:
- remove/reorder formal Scenes
- merge away a formal role
- patch Scene 9
- create a new causal explanation
- strengthen confidence
- remove important counterevidence

## Surface-only preference

For `PROCEDURAL_NARRATION`, `ABSTRACT_EDITORIAL_LANGUAGE`, `FOX_VOICE_ABSENT`, `FACT_STACKING`, `LOW_INFORMATION_GAIN`, `PAYOFF_DROUGHT`, or a weak continuation, prefer surface-only rewrite first when the Story Plan meaning is already sufficient.

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

A PASS 04 review plus a passing causal bundle validator is required for Story Engine creative acceptance.

A high numerical score cannot override a hard narrative gate.

When no external Critic executed, keep:

```text
reviewer = editorial_critic
critic_certified = false
external_critic_status = not_run
```

When a real external review is later executed, the external lineage/certification layer may upgrade the status. It must never rewrite the editorial judgment or causal contract merely to obtain certification.
