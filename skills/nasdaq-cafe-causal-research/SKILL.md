---
name: nasdaq-cafe-causal-research
description: Build an evidence-grounded causal research dossier from a daily NASDAQ source package before editorial selection and script writing.
version: 0.1.0
---

# NASDAQ Cafe Causal Research

## Purpose

This skill sits between daily information collection and the editorial decision governed by `02_editorial_bible.md`.

It prevents the system from turning a surface-level list of overnight events directly into a script. It expands the evidence, tests competing explanations, and produces a structured research dossier for the editor.

This skill does **not**:

- choose the final lead as an unquestionable truth
- write the final fox narration
- generate the nine-scene episode package
- recommend trades, prices, or portfolio actions
- overwrite 01–04

## Inputs

Required:

- `daily_source_package_YYYY-MM-DD.md`
- current market session/date and information cutoff
- `source-of-truth/02_editorial_bible.md`
- available primary sources and market data

Optional:

- prior episode packages
- prior company guidance and transcripts
- historical source packages
- entity/relation index
- minute or intraday data

Missing inputs must not be invented. Record them as missing or unknown.

## Outputs

Required:

- `research/causal_research_dossier_YYYY-MM-DD.md`
- `research/causal_research_dossier_YYYY-MM-DD.json`
- validator result

The dossier is an editorial research artifact, not public narration.

## Core workflow

### Stage 0 — Contract and input gate

1. Read project instructions and 01–04.
2. Record the exact input files, versions, session date, cutoff time, and timezone.
3. Confirm that the daily package contains enough basic data to begin.
4. Do not write narration or scene copy at this stage.

### Stage 1 — Overnight contradiction detection

Identify up to three candidate contradictions that require explanation, for example:

- strong results but a falling stock
- lower yields but weak megacap technology
- a rising Nasdaq Composite but falling SOX
- strong AI demand but diverging supplier reactions
- a major headline with little index response

Rank candidates by:

1. explanatory power for the overnight session
2. relevance to AI, semiconductors, and large technology
3. existence of a real Expected / Actual / Gap or another verifiable tension
4. ability to connect to NASDAQ without overextending a single-company event
5. strength of contrary evidence that can be honestly retained

Output a provisional lead only. Final selection remains under 02.

### Stage 2 — Perspective-guided question generation

Use the STORM pattern: discover distinct perspectives before searching deeply.

Generate questions from at least these perspectives when relevant:

- company official / filing
- prior guidance and historical change
- consensus and expectations
- price and timing
- customers and demand
- suppliers and bottlenecks
- competitors and comparison cases
- rates, dollar, oil, policy, and macro
- index/sector transmission
- counter-hypothesis and disconfirming evidence

Do not generate a fixed quota merely to fill space. The default range is 8–16 material questions.

Questions must include follow-up potential. A question should be revised when new evidence changes the research direction.

### Stage 3 — Parallel specialist research

Use a supervisor/researcher pattern inspired by Open Deep Research.

Recommended research roles:

1. **Official Evidence Researcher**
   - IR, SEC, earnings release, transcript, government statistics, central bank, exchange

2. **Expectation Researcher**
   - consensus, prior company outlook, repeated pre-event market focus, options-implied move when available

3. **Timeline Researcher**
   - event time, publication time, premarket/session/after-hours classification, first observable reaction, competing events

4. **Company Network Researcher**
   - customers, suppliers, competitors, platform dependencies, capex and revenue exposure

5. **Macro Transmission Researcher**
   - yields, dollar, oil, policy, inflation, power, logistics, export controls

6. **Historical Context Researcher**
   - prior quarters, prior guidance, when the market evaluation axis changed, unresolved older concerns

7. **Counter-Hypothesis Researcher**
   - alternative causes, contradictory assets, pre-existing price move, absent sector spillover, source dependence

Researchers return evidence items, not polished narrative.

### Stage 4 — Evidence normalization

Every material evidence item must record:

- `evidence_id`
- claim
- evidence class: `fact`, `reported_interpretation`, `grounded_inference`, or `unknown`
- source tier
- source title and publisher/issuer
- source URL or stable reference
- publication/event timestamp and timezone when relevant
- directness: `direct`, `supporting`, or `context`
- independence group to avoid counting syndicated copies as separate evidence
- confidence
- notes and limitations

Unreadable pages and headline-only material cannot support final causal claims.

### Stage 5 — Dynamic causal map

Build a causal map rather than a news list.

Typical path:

```text
event
→ changed expectation or concern
→ rates / dollar / oil / policy / supply chain / capex / demand
→ AI / semiconductor / large-technology companies
→ SOX / Nasdaq-100 / Nasdaq Composite
```

Each edge must include:

- from and to nodes
- mechanism
- supporting evidence IDs
- timing alignment
- confidence
- strongest alternative explanation
- whether the edge is required for the final story

Do not keep an edge only because it makes the story smoother.

### Stage 6 — Expected / Actual / Gap

Expected must use one of the categories defined by 02:

- official consensus
- prior company guidance
- major reporting
- analyst view
- price-derived inference
- unconfirmed

Record a concrete source for Expected. If it cannot be verified, set it to unconfirmed and do not fabricate a gap.

Actual must come from verifiable releases, statistics, decisions, or statements.

Gap explains what changed in the market's understanding, not merely whether a number was above or below a forecast.

### Stage 7 — Timeline and alternative-cause test

Before connecting a story to price:

- check whether the move started before the event
- check whether another event occurred in the interval
- check related stocks and indices
- check rates, dollar, oil, VIX, and sector behavior when relevant
- avoid precise intraday wording when intraday data is unavailable

Classify factors as:

- primary cause candidate
- amplifier
- offsetting factor
- unresolved factor

### Stage 8 — Research compression

Compress specialist findings before editorial synthesis.

Remove:

- duplicate syndicated evidence
- facts that do not affect the causal path
- background that cannot reach NASDAQ
- interesting but nonessential company trivia
- unsupported interpretations

Preserve:

- the strongest evidence for the provisional lead
- the strongest contrary evidence
- the most credible alternative hypothesis
- uncertainty that changes wording strength
- one or more headline-beyond discoveries

### Stage 9 — Editorial handoff

The dossier must end with:

- provisional lead and why it best explains the contradiction
- central hypothesis
- confidence
- Expected / Actual / Gap status
- direct company material versus NASDAQ-wide cause/support
- primary, amplifier, offsetting, unresolved factors
- strongest contrary evidence
- recommended causal spine
- facts that must not enter narration
- questions still unresolved
- what to monitor next to validate or weaken the hypothesis

The editor then applies 02 and may reject or revise the provisional lead.

## Stopping conditions

Research can stop when all of the following are true:

- the leading contradiction is explicit
- the main causal path has evidence for every material edge
- Expected is sourced or explicitly unconfirmed
- event and price timing are checked to the available resolution
- at least one credible alternative explanation has been tested
- important contrary evidence is retained
- the lead can be separated from a NASDAQ-wide cause when necessary
- additional searches are returning mostly duplicate or non-causal information

Do not stop simply because a predetermined number of links was collected.

## Failure modes

Return an incomplete dossier rather than inventing content when:

- the primary source cannot be read
- the relevant time series is unavailable
- Expected cannot be established
- related assets do not support the proposed transmission
- multiple explanations remain equally plausible

`reason_unknown` is an acceptable editorial outcome.

## Validation

Run the dossier validator before handing off to 02.

A dossier fails validation when it lacks:

- source provenance
- a contradiction or explicit reason-unknown statement
- alternative hypothesis testing
- a causal edge list
- uncertainty and contrary evidence
- separation of company-direct and NASDAQ-wide claims
- Expected source classification

Passing validation means the research artifact is structurally complete. It does not prove that the market interpretation is true.
