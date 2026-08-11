---
name: nasdaq-cafe-story-engine
version: 1.3.3
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

> **結論を遅らせるのではなく、結論を進化させる。**

> **面白さは、Evidenceによって視聴者の説明モデルが有意味に更新される量で作る。**

Do not retain viewers by hiding a known answer. Give a real payoff, then let that new understanding make the next comparison, test, boundary, counterevidence, implication or verification valuable.

The opening may give the direction and a provisional answer. The late section must still change, branch, narrow, reveal mechanism, or materially test that answer. A repeated answer plus extra examples or disclaimers is not progression.

Information Gain is a semantic editorial concept, not a numeric formula. New facts are valuable when they change, narrow, branch, test, or clarify the viewer's explanatory model enough to make the next Scene more valuable. Evidence count, question count, text length, or dramatic wording may not stand in for this judgment.

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

Choose an angle for explanatory value, not for theatrical reversals. The same evidence can support a compelling causal chain, comparison, branch, boundary, mechanism reveal, or reason-unknown story without a fake surprise.

When several angles are causally valid, prefer the one that can create multiple distinct Evidence-backed model updates across Scenes 1–8 rather than one reveal surrounded by factual filler. Do not choose a weaker causal angle merely because it looks more surprising.

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

A new number or another supporting headline does not automatically count as progress. The viewer's explanatory model must actually move.

### Honest Information Gap

The opening may state the provisional driver and a concrete unresolved mismatch without immediately reciting every later numeric receipt.

Allowed:

```text
金利がまず鍵です。
ただ、半導体を全部この説明に入れると、一銘柄だけ発表時刻と値動きが合いません。
```

This gives early value plus a real reason to inspect the evidence.

Forbidden:

```text
答えは分かっているけれど後半まで隠します。
```

Information Gap may organize disclosure. It may not hide evidence required to make the provisional statement truthful, manufacture ignorance, or distort chronology.

### Internal Understanding Gain classification

Before narration, classify the main gain of each Scene internally. This is a planning aid and is not yet a required Story Plan JSON field.

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

- `support`: strengthens an already-understood model without materially changing it
- `narrow`: limits scope, confidence, or applicability
- `branch`: separates one apparent explanation into multiple engines
- `disproof`: rejects a plausible simple explanation
- `mechanism_reveal`: shows how the effect travels
- `verification`: tests the provisional model against timing, price, peers, or direct observation
- `uncertainty_reduction`: makes remaining uncertainty more specific
- `synthesis`: combines prior updates into the final interpretation

`support` is valid but usually low Information Gain. A required support Scene can remain short. Do not relabel support as a stronger gain type to make the arc look better.

### Payoff-drought planning check

Inspect Scenes 1–8 before authoring. If two or more consecutive Scenes mainly accumulate facts or support without materially moving the explanatory model:
- preserve every fixed formal role,
- keep mandatory facts and Evidence bindings,
- plan those support-heavy Scenes concisely,
- bring the next truthful comparison, test, boundary, or model update forward within chronology-compatible Scene roles when possible.

Do not invent a surprise to fill a drought. A short low-gain Scene is preferable to fake drama.

### Evidence-backed Understanding Upgrade

The legacy Story Plan field remains named `midpoint_turn` for schema compatibility. Its semantic meaning is now **Understanding Upgrade**, not mandatory dramatic reversal.

It must occur in Scene 4–6 and must be backed by real Evidence IDs.

Valid upgrade forms:

```text
turn
branch
boundary
scale_reveal
mechanism_reveal
disproof
reason_unknown_payoff
```

A valid upgrade changes, branches, narrows, or materially tests the provisional explanation.

Examples:
- a simple explanation is rejected by evidence
- one apparent sector move separates into macro and company-specific engines
- a company explanation is narrowed by peer/index evidence
- actual price timing materially tests the hypothesis
- a mechanism becomes visible that the headline did not reveal
- competing explanations fail enough that reason_unknown is the strongest conclusion

Invalid:

```text
暫定解：弱い雇用 → 利上げ観測後退
追加情報：原油も下落
最終解：弱い雇用 → 利上げ観測後退
```

That is additional support, not an Understanding Upgrade.

Do not create a reversal to satisfy the contract. If no reversal is supported, use a real branch, boundary, mechanism, price test, or reason-unknown payoff. If the evidence cannot support any meaningful late upgrade, shorten the episode rather than inventing drama.

### Scene 4 → Scene 8 delta

Scene 4 may already reveal the central hypothesis. That is allowed.

But Scene 8 must be materially more informed than Scene 4. Before authoring, state internally:

```text
Scene 4 provisional understanding:
Scene 8 final understanding:
What evidence-backed understanding was added or changed:
```

If the third line cannot be answered concretely, the plan has no sufficient late value.

### Scenes 6–8 deletion test

Before authoring, ask:

> If Scenes 6–8 were removed, what important understanding would the viewer lose?

Valid lost value includes:
- a second causal engine
- a scope limit
- a peer contradiction
- an actual price-reaction test
- a mechanism reveal
- a falsification condition
- a defensible reason_unknown conclusion

If the answer is only extra examples, another supporting statistic, repeated caution, or a schedule/checklist, the late section is an appendix and the plan must be reworked or shortened.

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

The fox should sound like a guide updating an explanation with the viewer, not a narrator reading the already-completed audit trail. Do not invent a personal past belief such as 「僕も最初は〜と思った」 unless that experience is actually recorded.

### ABT / fact-stacking compression

Use And / But / Therefore as a diagnostic, not a mandatory sentence template.

If adjacent Scenes mainly read as:

```text
fact
AND fact
AND another fact
```

while the explanatory model stays the same, compress the spoken surface so the next real contrast or implication becomes visible sooner.

When supported by the frozen Evidence, a useful pattern is:

```text
known fact
BUT mismatch / boundary
THEREFORE updated interpretation
```

Do not invent a `BUT`, remove a required formal Scene, omit Expected / Actual / Gap, or strengthen the `THEREFORE` beyond the Story Plan. Low-gain support Scenes may simply be short.

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
- compression of repeated factual setup when all guarded meaning remains present

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

**Run narrative hard gates before numeric scoring. A high score cannot override a failed gate.**

### Hard Gate A — Hook Exhaustion

If Scenes 1–2 already state the driver, major amplifiers, important boundary/counterevidence, and final synthesis so completely that the rest is only evidence receipts, issue:

```text
HOOK_EXHAUSTS_STORY
```

Early direction is good. Early exhaustion is not.

### Hard Gate B — Understanding Upgrade Authenticity

Review the legacy `midpoint_turn` as the Evidence-backed Understanding Upgrade defined in Pass B.

If it is only an extra supporting fact and does not change/branch/narrow/test the model, issue:

```text
NO_UNDERSTANDING_UPGRADE
```

If the apparent upgrade exists only because already-known evidence was artificially withheld, issue:

```text
FAKE_UNDERSTANDING_UPGRADE
```

or `FAKE_OPEN_LOOP` as appropriate.

### Hard Gate C — Scene 4 → Scene 8 Delta

Ask:

> What does the viewer understand in Scene 8 that they did not already understand by Scene 4?

If there is no concrete evidence-backed answer, issue `NO_LATE_PAYOFF`.

A Scene 8 that repeats the Scene 4 conclusion plus 「ただし断定はできません」 does not pass.

### Hard Gate D — Late Value Deletion Test

Ask:

> If Scenes 6–8 were removed, what important understanding would the viewer lose?

If no material understanding is lost, issue `NO_LATE_PAYOFF`.

### Hard Gate E — No Forced Drama

Do not penalize an episode merely because it lacks a theatrical reversal. A real branch, boundary, mechanism reveal, price test, or reason-unknown payoff is enough.

### Interest-quality diagnostics

Run these after the hard gates and before numeric scoring. They detect scripts that are causally safe but still feel like evidence receipts or lectures.

#### `FACT_STACKING`

Adjacent Scenes mainly add facts or support while the explanatory model remains effectively unchanged.

#### `LOW_INFORMATION_GAIN`

Ask what the viewer can explain differently after this Scene. If the answer is only that the same hypothesis now has one more supporting fact, the Scene may be low gain. `support` is valid; issue this finding when **narrative weight/emphasis** is disproportionate to the gain. At this pre-TTS review stage, do not infer actual runtime from word count; use measured duration only when it is explicitly present in the sealed review input.

#### `PAYOFF_DROUGHT`

A multi-Scene stretch goes too long without a meaningful model update, useful narrowing, direct test, mechanism reveal, or consequential counterevidence. Do not judge this by a fixed number of seconds or words.

#### `WEAK_SURPRISE`

The nominated Understanding Upgrade technically exists but has little explanatory consequence. Ask whether removing it would materially change the final model. Surprise means a meaningful model update, not a theatrical twist.

These four diagnostics may be `minor` when localized and safely compressible, or `major` when they materially damage progression. If the same defect actually means there is no real Understanding Upgrade or late payoff, use the stronger hard finding instead.

### Scenes 1–7 Progression Check

Check:
- `payoff_delivered`
- `belief_changed`
- `continuation_reason_natural`
- `procedural_language_dominant`

A PASS requires all three positive progression checks to succeed for every Scene 1–7.

### Scene 8 Closure Check

Check:
- `payoff_delivered`
- `belief_changed`
- `closure_effective`
- `opening_promise_recovered`
- `procedural_language_dominant`

A PASS requires Scene 8 to deliver a payoff, change understanding relative to the provisional answer, close effectively, and recover the opening promise at a deeper level.

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
FOX_VOICE_ABSENT
ABSTRACT_EDITORIAL_LANGUAGE
```

The following may not be downgraded to minor merely to preserve a PASS:

```text
HOOK_EXHAUSTS_STORY
NO_UNDERSTANDING_UPGRADE
FAKE_UNDERSTANDING_UPGRADE
NO_LATE_PAYOFF
OPENING_PROMISE_NOT_RECOVERED
ENDING_NOT_BOOKENDED
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

For `FACT_STACKING`, `LOW_INFORMATION_GAIN`, or `PAYOFF_DROUGHT`, first compress repeated setup, improve connectors, or move already-supported content within compatible Scene roles. Do not change frozen meaning merely to increase pace.

For `WEAK_SURPRISE`, first ask whether existing Evidence can play a more explanatory comparison/test/boundary role. Do not invent a turn.

For `NO_UNDERSTANDING_UPGRADE` or `NO_LATE_PAYOFF`, do not invent new evidence or causal claims. Reuse already-supported Evidence in a better explanatory role, move compatible explanation blocks, or shorten the episode. If the evidence itself is insufficient, return upstream.

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

A final PASS requires the hard narrative gates and the normal 04 score threshold. Numerical score never overrides the hard gates. Major interest-quality findings also block PASS through the normal major-finding rule; localized minor interest findings may remain when they do not invalidate the episode.

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

# 2026-08-10 interest regression requirement

Use the **real historical H4 output** as the benchmark for "correct but potentially lecture-like" episodes. The historical H4 review was 29/30, PASS, with no findings. That historical score is evidence of the old review behavior, not proof that the script is optimally interesting under the new Information Gain policy.

The baseline is reproduced from immutable acceptance fixture commit `b986888660aa8efd64428aa8119200965351c047` and must match the recorded historical core SHA-256 values before any revised A/B is accepted. The revised side must keep the causal dossier byte-identical and satisfy the separate Editorial Invariant Manifest. Claim IDs may change in a full Story Engine rerun; market meaning may not.

Frozen market meaning:

```text
weak payroll miss
→ rate-hike expectations fall
→ macro support for tech
```

must remain provisional, not final synthesis.

Required interest progression:

1. contradiction + provisional rate explanation
2. payroll weakness becomes materially concrete
3. index/sector strength rejects a simple risk-off reading
4. Expected / Actual / Gap + rate-hike path reveal the macro mechanism
5. oil/yield context remains concise support
6. QQQ/SOXX/NVDA 8:30 response vs MCHP non-response creates the highest-gain branch/verification
7. MCHP earnings define the company-specific engine while AMD/Alphabet limit blanket-tech generalization
8. synthesis: different causal engines aligned in the same index direction; one-minute alignment remains chronology evidence, not causal proof
9. fixed close

The Engine must be able to issue `FACT_STACKING`, `LOW_INFORMATION_GAIN`, `PAYOFF_DROUGHT`, or `WEAK_SURPRISE` when the facts are preserved but the explanatory progress is too weak. These findings may never be resolved by inventing causality or withholding truth.

Deterministic CI proves lineage, structure, chronology, Evidence retention, scope boundaries and A/B invariants. It does **not** prove that either script is interesting. The actual semantic judgment remains the 04 Editorial Critic responsibility.

---

# Required validations

- Story Plan v1.2 validator
- Story Script / causal bundle validator
- Understanding Progression scene checks
- Evidence-backed Understanding Upgrade structural guards
- Scene 4 → Scene 8 understanding delta guard
- Information Gain interest-quality diagnostics in 04
- real historical 2026-08-10 H4 SHA-bound interest A/B regression
- Editorial Invariant Manifest comparison for full Story Engine reruns
- material counterevidence guard
- fixed Scene order / Scene 9 guard
- 04 hard narrative gates before scoring
- Visual Evidence Planning intent-document presence gate
- optional external Critic policy tests
- v1.1 strict external attestation tests
- final episode projection / production package validation

Passing deterministic validators does not prove a story is interesting. Interestingness is judged by 04, then calibrated against real audience-retention data after publication.
