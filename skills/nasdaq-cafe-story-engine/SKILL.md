---
name: nasdaq-cafe-story-engine
version: 1.3.0
description: Turn a validated causal dossier into a reviewed 9-Scene episode package by chaining viewer understanding without changing market causality, then hand the reviewed story to explicit Visual Evidence Planning.
---

# Unified Story Engine

Run after `causal_dossier_valid` and before `episode_package_final`.

Story Discovery, Understanding Progression, Authoring, Editorial Critic, Targeted Rewrite, Causal Diff and Re-review are internal Story Engine passes. They are not public Daily Production states.

After Pass G succeeds, the reviewed story must pass through the separate **Visual Evidence Planning handoff** defined below before `episode_package_final` is registered. Visual Evidence Planning is not a new Story Engine meaning pass and may not change the reviewed market story.

```text
causal_dossier_valid
→ Story Engine A–G
→ Visual Evidence Planning handoff
→ episode_package_final
```

## Core philosophy

> **朝のNASDAQカフェは、質問を連鎖させる番組ではない。視聴者の理解を連鎖させる番組である。**

Do not retain viewers by hiding a known answer. Give a real payoff, then let that new understanding make the next comparison, test, boundary, counterevidence, implication or verification valuable.

The strict layer is market meaning. The flexible layer is spoken delivery.

## Absolute boundary

The engine may change:
- explanation order when chronology is preserved
- Scene connections
- wording and compression
- short analogies
- surface delivery
- visual presentation
- publishing copy after final review

It may not change:
- lead
- facts or numbers
- Expected / Actual / Gap
- chronology
- Claim / Evidence bindings
- causal scope
- confidence
- material counterevidence
- unresolved uncertainty
- official Scene roles
- fox history

Factual or causal defects return to Causal Research / 02.

---

## Pass A — Story Discovery

Extract from the validated dossier:
- central contradiction
- plausible naive explanations
- evidence tests
- headline-beyond discovery
- after implications
- viable editorial angles

Do not write narration.
For reason_unknown, explain uncertainty rather than inventing a cause.

## Pass B — Understanding Progression / Story Plan v1.2

Keep 03's formal Scene 1–9 roles unchanged.

For each Scene store:

```text
viewer_belief_before
new_evidence_ids
new_meaning
viewer_belief_after
continuation_reason
connector
```

### Scenes 1–7

Each Scene must deliver a real understanding payoff and a rational continuation reason.
`continuation_reason` is not required to be a question.

Valid continuation forms:

```text
question
comparison
test
boundary
counterevidence
implication
verification
```

### Scene 8

Scene 8 is closure, not another hook.

```text
continuation_reason = ""
```

It must:
- preserve strengthen/weaken conditions
- retain material uncertainty and counterevidence
- recover the opening promise as a more informed interpretation
- remain inside the dossier confidence ceiling

### Scene 9

Fixed close only. No new evidence, meaning, causal claim or continuation.

### `new_meaning` safety

A payoff does not require a new causal explanation. It can be:
- rejecting a simple explanation
- narrowing uncertainty
- fixing chronology
- understanding Expected / Actual / Gap
- making a comparison concrete
- testing the hypothesis against prices
- limiting causal scope
- understanding counterevidence
- understanding what remains unknown
- learning falsification conditions

Never create causality to manufacture late value.

## Pass C — Fox Script Authoring

The Story Plan is an internal meaning contract, not spoken copy.

Avoid procedural narration such as:
- 「次に見ます」
- 「続いて確認します」
- 「時系列を固定します」
- 「ここまでが確認済み事実です」
- 「仮説を検証します」

Use one fox voice and first person `僕`.
The fox is a guide, not a teacher or outside announcer.

After the factual draft, run exactly one surface-only Spoken Delivery Pass.

Allowed surface changes:
- word order
- sentence length
- connectors
- spoken phrasing
- short fox reaction
- explicit vs implicit question
- short analogy
- punctuation / pause

Forbidden changes:
- Claim ID
- Evidence ID
- numbers
- Expected / Actual / Gap
- chronology
- claim type
- confidence
- scope
- counterevidence
- formal role

Run causal before/after validation after the pass.

## Pass D — 04 Editorial Critic

The 04 entertainment/clarity review is always required.
It is required even when no paid external Independent Critic is connected.

### Scenes 1–7 Progression Check

Check:
- `payoff_delivered`
- `belief_changed`
- `continuation_reason_natural`
- `procedural_language_dominant`

### Scene 8 Closure Check

Check:
- `payoff_delivered`
- `belief_changed`
- `closure_effective`
- `opening_promise_recovered`
- `procedural_language_dominant`

Do not require a Scene 8 next-hook.

Important failures include:

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
FOX_VOICE_ABSENT
ABSTRACT_EDITORIAL_LANGUAGE
```

Causal-safety findings remain Critical:

```text
CAUSALITY_DRIFT
COUNTEREVIDENCE_REMOVED
TIMELINE_DRIFT
NASDAQ_SCOPE_OVERREACH
```

## Pass E — Targeted Rewrite

Patch only finding-linked fields.
Full regeneration is not the default.
Formal Scene order cannot change.
Scene 9 cannot be patched.

For surface failures, prefer a surface-only fix first.

## Pass F — Causality Preservation

Reject any rewrite that causes:
- evidence loss
- modality strengthening
- confidence strengthening
- counterevidence removal
- chronology distortion
- company→NASDAQ scope promotion
- investment advice
- invented fox history

## Pass G — Final Re-review

Maximum two review/rewrite rounds.
If a Critical issue remains, block and return to the owning stage.

---

# Required handoff — Visual Evidence Planning

This handoff happens **after Pass G and before `episode_package_final`**. It is outside Story Engine A–G and cannot reopen lead selection, causality, chronology, Expected / Actual / Gap, confidence, counterevidence, narration meaning, or Scene roles.

Its only question is:

> For each already-authored Visual Beat, what medium best communicates the reviewed meaning without inventing a new claim?

For each Visual Beat, consider:

```text
real source evidence
financial visual
real-world photo
social post
generated illustration
existing asset
```

Prefer original evidence when the viewer needs to see the evidence itself. Prefer Financial Visual when the job is to understand numbers, comparison, Gap, transmission, or verified price timing. A social post is preferred only when the post itself is materially part of the story.

## Mandatory planning artifact

Every production attempt must author:

```text
working/YYYY-MM-DD/visual_source_intents.json
```

Even when no external or day-specific Visual Source is useful, create the explicit empty document:

```json
{
  "contractVersion": "1.0.0",
  "episodeDate": "YYYY-MM-DD",
  "intents": []
}
```

Therefore:

```text
missing intent document ≠ not required
explicit empty intents = planning completed, no Visual Source required
```

A missing intent document is `E_VISUAL_SOURCE_PLANNING_MISSING` and blocks production.

## Intent safety

When an intent is authored:

- target an existing Scene / Visual Beat only;
- use only evidence/source IDs already present in the reviewed production source registry;
- use exact locators, never a generic search query;
- state a purpose that mirrors existing reviewed meaning;
- define Primary and Approved Fallback before acquisition/generation;
- keep rights status explicit;
- do not add a fact, causal edge, price attribution, confidence strengthening, or NASDAQ-wide promotion;
- do not change narration just to justify an image;
- do not use a social screenshot or source page merely to satisfy a visual quota.

If the Visual Evidence planner discovers that the reviewed story itself lacks required factual support, return to Causal Research / 02 instead of repairing the story through visuals.

The exact-locator resolver and renderer remain mechanical. They may resolve, verify, project and render the selected medium, but they may not decide what the story means.

---

# External Independent Critic policy

The normal 04 editorial review above is mandatory.
A real external Independent Critic is an optional quality/certification upgrade.

## Default daily mode

`materialize_story_engine.py` defaults to:

```text
--external-critic off
```

No old receipt is consumed and no independent review is claimed.
The acceptance must report:

```text
critic_certified = false
external_critic_status = not_run
```

Daily Production may continue only through the explicit optional policy:

```text
require_production=True
allow_uncertified_production=True
```

This still requires the hash-bound Story Plan, Story Script, 04 editorial review, causality guards, Scene guards and projection checks to PASS.

## Optional existing receipt mode

```text
--external-critic auto
```

Use a request/receipt only when present and valid.
If their reviewed-input blob SHAs do not match current inputs, fail closed.
Never attach a historical receipt to a revised draft.

A `repository_provenance` receipt is not certification.
It must remain:

```text
critic_certified = false
external_critic_status = not_certified
```

## Strict certification mode

```text
--external-critic required
```

Strict production requires:
- a distinct external Critic execution
- `separate_invocation`
- valid sealed request / review lineage
- Ed25519-verified `orchestrator_signed` attestation
- trusted active public key

Only then may:

```text
production_eligible = true
critic_certified = true
external_critic_status = certified
```

The private signing key stays outside the repository and outside Author context.
GitHub Actions may verify hashes/signatures but must not invent review judgment or certification.

## External pipeline retained for future budget

Provider-neutral entry point:

```text
scripts/story-engine/run_external_critic_pipeline.py
```

OpenAI adapter path:

```text
scripts/story-engine/run_openai_critic_pipeline.py
critic-adapters/openai/
```

The external path is not called by default Daily Production and must not be used without explicit paid-model authorization.

---

# Unified acceptance gate

`story_engine_acceptance.json` always binds:
- causal dossier
- materialized Story Plan
- materialized Story Script
- final 04 creative review
- causal / Scene guards

External request/receipt artifacts are optional and must appear as a pair.

`validate_story_engine_acceptance_v1_1.py` always re-runs the editorial bundle validator from the hash-bound core artifacts.
Therefore absence of external certification does not remove editorial or causal validation.

Two production policies remain:

1. **strict external certification** — `--require-production`
2. **daily optional certification** — `--require-production --allow-uncertified-production`

The Daily Production wrapper uses policy 2.

The legacy `production_eligible` field means external-Critic-certified eligibility only. It may remain false while `production_allowed_by_policy=true` in optional mode.

---

# Final title / thumbnail audit

Story Engine Critic checks recovery of `opening_promise`.
Do not inspect final title/thumbnail promises before those surfaces are finalized.

After the final episode package is assembled, the final 04 review checks:

```text
FINAL_TITLE_PROMISE_NOT_RECOVERED
THUMBNAIL_PROMISE_NOT_RECOVERED
```

Titles/thumbnails may never imply stronger causality than the body.

---

# 2026-08-06 regression requirement

The revised episode must preserve all market facts and causal metadata while improving spoken progression.

Required progression:

1. AI semiconductor moves diverged
2. simple bad-results explanation weakens
3. ordinary consensus miss explanation also weakens
4. evaluation-axis difference becomes visible
5. NVIDIA gets a concrete relative adoption proof
6. price action tests the hypothesis
7. broader tech evidence limits NASDAQ scope
8. uncertainty / strengthen-weaken conditions + opening callback
9. fixed close

Scene 1–2 are not sacred. Rewrite only Scenes that fail the same Critic criteria.

---

# Required validations

- Story Plan v1.2 validator
- Story Script / causal bundle validator
- Understanding Progression scene checks
- material counterevidence guard
- fixed Scene order / Scene 9 guard
- Visual Evidence Planning intent-document presence gate
- optional external Critic policy tests
- v1.1 strict external attestation tests
- final episode projection / production package validation

Passing deterministic validators does not prove a story is interesting. Interestingness is judged by 04, then calibrated against real audience-retention data after publication.
