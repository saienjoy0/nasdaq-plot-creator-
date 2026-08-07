---
name: nasdaq-cafe-story-plan
description: Transform a validated causal research dossier into an evidence-bound nine-scene belief arc before fox narration is written.
version: 1.1.0
---

# NASDAQ Cafe Story Plan

## Purpose

This skill sits between the validated causal research dossier and Fox Script Authoring.

It does not redo market research. It does not write final narration.

Its job is narrower:

> Preserve the facts, causality, timeline, confidence, and counterevidence already accepted under 02, then arrange that material so the viewer's understanding changes across the fixed nine-scene structure defined by 03.

Story Plan converts a correct causal dossier into an explainable story architecture.

## Authority boundary

Priority:

```text
Project Instructions
→ 02_editorial_bible.md
→ 01_fox_character_bible.md
→ 03_episode_production_spec.md
→ 04_entertainment_inquisitor.md
→ this Skill
→ external storytelling references
```

External Storytelling OSS is never an editorial authority.

The vendored Doza Assist Storytelling Foundation and the adapted patterns from Toonflow, ViMax, FireRed-OpenStoryline, video_explainer, and OpenMontage are implementation aids only.

## Inputs

Required:

- validated causal research dossier JSON
- episode date and information cutoff
- `source-of-truth/02_editorial_bible.md`
- `source-of-truth/03_episode_production_spec.md`
- `references/external/doza-assist/storytelling-foundation-oss.md`
- `references/STORY_ENGINE_DIRECT_IMPORT_MATRIX.md`

The causal dossier must already contain the evidence needed to make the editorial decision.

If the dossier is incomplete, return to Causal Research. Do not use Story Plan to fill evidence gaps.

## Output

Required:

```text
working/YYYY-MM-DD/story-engine/story_plan.json
```

The artifact must validate against:

```text
skills/nasdaq-cafe-story-plan/contracts/story_plan.schema.json
```

and:

```text
skills/nasdaq-cafe-story-plan/validators/validate_story_plan.py
```

No narration is generated at this stage.

---

## Stage 0 — Lock the dossier

Before designing a story:

1. Read the validated causal dossier.
2. Record its repository-relative path and SHA-256.
3. Freeze:
   - lead / lead theme
   - Expected / Actual / Gap
   - Evidence IDs
   - timeline
   - confidence
   - factor roles
   - company-vs-sector-vs-NASDAQ scope
   - counterevidence
   - unresolved questions
4. Do not add a new Expected.
5. Do not strengthen confidence.
6. Do not promote a company-specific explanation into a NASDAQ-wide primary cause.
7. Do not reorder actual events to improve drama.

If any of those inputs are wrong, return to 02 / Causal Research instead of fixing them here.

---

## Stage 1 — Select the central contradiction

Select one existing `CON-*` item from the dossier.

Store:

- `central_contradiction_id`
- exact contradiction statement
- one central viewer question

Do not invent a new contradiction that the dossier did not support.

The contradiction should express the important overnight tension, for example:

```text
Good result
BUT
bad price reaction
```

or:

```text
AI demand remained strong
BUT
related suppliers diverged
```

The central question should be answerable by the existing evidence chain.

---

## Stage 2 — Naive Explanation Test

Generate 1–4 simple explanations that a viewer might reasonably assume from the headline.

Examples:

- the result was simply bad
- the whole semiconductor sector sold off uniformly
- one company alone explains the index move
- rates alone explain the move

Each explanation must be classified with existing Evidence IDs as:

```text
survives
weakened
rejected
unresolved
```

This is not permission to invent a strawman.
Use plausible first-pass explanations tied to the actual contradiction.

A naive explanation is useful when later evidence changes the viewer's understanding.

---

## Stage 3 — Headline-beyond discovery

Use the dossier's `editorial_handoff.headline_beyond_discovery` as the locked discovery.

Do not rewrite it into a stronger causal claim.

This is the minimum insight the final episode must deliver beyond the headline.

If the dossier has no defensible headline-beyond discovery, return to Causal Research / 02.

---

## Stage 4 — Angle Competition

Create 3–5 genuinely different editorial angles using the same locked facts.

Allowed initial types:

```text
contradiction
comparison
evaluation_axis_shift
misconception_disproof
causal_chain
reason_unknown
```

Each angle must contain:

- central question
- story spine
- opening promise
- midpoint turn claim
- Scene 8 closing reframe
- causality scope
- confidence
- Evidence IDs
- counterevidence IDs
- risk
- why it is structurally different from the other angles

Different wording is not a different angle.

A valid difference changes at least one of:

- entry question
- comparison frame
- order of explanation
- location of the explanatory turn
- final reframe

without changing the underlying facts.

### Selection rule

Select the angle that best:

1. explains the central contradiction
2. reaches NASDAQ without causal overreach
3. creates a real explanatory turn
4. preserves important counterevidence
5. leaves useful verification value for Scenes 6–8
6. delivers the dossier's headline-beyond discovery

The chosen angle may never exceed the dossier's confidence.

---

## Stage 5 — Opening Promise

The opening promise must establish, within Scenes 1–2:

- direction
- contradiction
- question

It must not reveal the whole proof before the viewer reaches the later evidence.

Doza's hook principle is adapted here as an information gap, not as sensationalism.

Bad:

```text
Here is the full answer and every supporting number.
```

Better:

```text
The index fell and AMD dropped hard.
But the reported outlook was above the normal forecast.
So what was the market actually grading?
```

The final wording is written later by Fox Script Authoring.
Story Plan only defines the promise.

---

## Stage 6 — Build the fixed nine-scene belief arc

The formal scene order comes from 03 and is not negotiable.

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

- viewer belief before
- new Evidence IDs
- new meaning created from existing evidence
- viewer belief after
- remaining question
- connector

### Scene acceptance rule

Scenes 1–8 must do at least one:

1. add new evidence
2. add new meaning from existing evidence

If neither occurs, the Scene is a repetition problem.

Scene 9 is the exception: it is a fixed closing and must add neither new evidence nor new argument.

### Belief progression

The viewer should not remain in the same explanatory state across multiple Scenes.

Typical progression:

```text
Scene 1: I know what kind of night it was.
Scene 2: The obvious explanation does not fit cleanly.
Scene 3: I know the confirmed facts.
Scene 4: I understand the expectation gap.
Scene 5: I understand why that gap mattered in the wider system.
Scene 6: The price/timeline tests the hypothesis and creates the turn.
Scene 7: Comparison shows the scope and limits of the hypothesis.
Scene 8: I know what would strengthen or weaken this interpretation.
Scene 9: fixed close.
```

This is a default reasoning model, not replacement names for 03 Scenes.

---

## Stage 7 — Midpoint Turn

A real explanatory turn must exist in Scene 4, 5, or 6.

Preferred order:

1. Scene 6
2. Scene 5
3. Scene 4

A turn means the explanation changes, not merely that another fact appears.

Valid turn examples:

- the naive explanation is rejected
- peer comparison changes the evaluation axis
- market reaction shows the company story is not enough to explain NASDAQ alone
- a reason-unknown conclusion becomes the most defensible answer

Invalid turn:

- repeat the same conclusion with another number
- introduce an unsupported surprise
- reorder events for drama

Doza's "a sequence without a turn is a list" is adopted as an explanatory rule.

---

## Stage 8 — Open Loops

Maximum: 2.

Each open loop records:

- open Scene
- question
- promised Evidence IDs
- close Scene
- resolution

Rules:

- close after it opens
- close by Scene 8
- never carry a fresh unresolved dramatic question into Scene 9
- do not hide already-known evidence merely to create suspense

The goal is guided discovery, not artificial withholding.

---

## Stage 9 — Scene 8 Closing Reframe

The bookend belongs in Scene 8, not Scene 9.

The closing reframe should answer the opening promise using the meaning accumulated across Scenes 2–8.

It must not be a stronger claim than the dossier.

Example structure:

```text
Opening:
This looked like a bad-results story.

Scene 8 reframe:
The evidence says the more useful interpretation was not whether AI demand existed, but what proof the market required before rewarding it.
```

Scene 8 also preserves 03's required strengthen/weaken verification points.

---

## Stage 10 — Scene 9 Guard

Scene 9 is fixed closing.

It must have:

- no new Evidence IDs
- no new narrative meaning
- no remaining question
- connector `closing`

Do not use Scene 9 to repair an unresolved story.

If the story is not resolved by Scene 8, Story Plan fails.

---

## External rule adapter

### Doza Assist

Use:

- explicit role
- adjacent redundancy rejection
- Turn requirement
- information-only rejection
- topic vs theme/claim distinction

Do not use:

- breath/filler/tense documentary heuristics
- emotional arc requirements that change the facts

### Toonflow

Use responsibility separation:

```text
Decision → Execution → Supervision
```

Story Plan is Decision architecture.
Fox Script later executes it.
Independent Critic later supervises it.

### ViMax

Use targeted revision and stale invalidation.
A Story Plan change makes all downstream Story Engine artifacts stale.

### FireRed-OpenStoryline

Use stage-localized rerun.
A Story Plan failure returns here, not automatically to the beginning of daily production.

### video_explainer / OpenMontage

Use clean-room concepts only:

- plan before script
- information gap
- BUT / THEREFORE
- guided discovery
- progressive revelation
- artifact-specific review

Do not copy their prompt text or schemas into runtime.

---

## Deterministic validation

The validator checks what code can safely know:

- schema
- date
- dossier path and SHA-256
- Evidence ID existence
- exact contradiction binding
- exact headline-beyond discovery binding
- at least 3 angle candidates
- selected angle binding
- no confidence strengthening
- causal scope guard
- material counterevidence preservation
- fixed Scene 1–9 order and formal roles
- each Scene 1–8 advances by evidence or meaning
- Scene 4–6 midpoint turn
- Scene 8 closing reframe
- maximum 2 loops and closure order
- Scene 9 no new evidence / meaning / question

The validator does not decide whether prose is interesting.
That belongs to the Independent Critic and 04.

## Failure codes for later Critic integration

Story Plan should make these detectable downstream:

```text
REPEATED_CONCLUSION
NO_BELIEF_CHANGE
ANSWER_REVEALED_TOO_EARLY
NO_MIDPOINT_TURN
NO_LATE_PAYOFF
OPEN_LOOP_UNRESOLVED
NASDAQ_SCOPE_OVERREACH
COUNTEREVIDENCE_REMOVED
TIMELINE_DRIFT
```

## Shadow-mode rule

Until the Story Engine A/B acceptance is complete, this Skill does not replace the current daily production state machine.

Generate and validate Story Plan as a sidecar from the same causal dossier.

Only after the 2026-08-06 failure fixture and later author/critic stages pass should `story_plan_valid` become a production state.
