---
name: nasdaq-cafe-causal-research
description: Build an evidence-grounded causal research dossier from a daily NASDAQ source package before editorial selection and script writing.
version: 0.2.0
---

# NASDAQ Cafe Causal Research

## Purpose

This skill sits between daily information collection and the editorial decision governed by `02_editorial_bible.md`.

It prevents the system from turning a surface-level list of overnight events directly into a script. It expands the evidence, tests competing explanations, revalidates relevant editorial memory against current evidence, and produces a structured research dossier for the editor.

This skill does **not**:

- choose the final lead as an unquestionable truth
- write the final fox narration
- generate the nine-scene episode package
- recommend trades, prices, or portfolio actions
- overwrite 01–04
- treat remembered claims as current evidence
- allow memory retrieval to decide market causality

## Inputs

Required:

- `daily_source_package_YYYY-MM-DD.md`
- `working/memory_query_plan_YYYY-MM-DD.json`
- `working/memory_context_YYYY-MM-DD.md`
- `working/memory_retrieval_report_YYYY-MM-DD.json`
- `research/YYYY-MM-DD/research_input_manifest.json`
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

The research input manifest must bind the daily package, query plan, memory context, and retrieval report to the same episode date and their SHA-256 values. The builder and dossier validator both replay deterministic retrieval and compare the generated Context and Report byte-for-byte. Do not proceed with a mismatched, stale, external, or path-traversing input.

## Outputs

Required:

- `research/causal_research_dossier_YYYY-MM-DD.md`
- `research/causal_research_dossier_YYYY-MM-DD.json`
- memory revalidation results for every selected non-core memory
- validator result

The dossier is an editorial research artifact, not public narration.

## Core workflow

### Stage 0 — Contract and input gate

1. Read project instructions and 01–04.
2. Record the exact input files, versions, session date, cutoff time, timezone, and research input manifest.
3. Confirm that the manifest hashes match the supplied files.
4. Replay retrieval and confirm that Query Plan, Context, and Report are one deterministic retrieval result.
5. Confirm that all input paths are repository-relative and remain inside the workspace root.
6. Confirm that the daily package, query plan, retrieval report, and dossier use the same episode date.
7. Confirm that the daily package contains enough basic data to begin.
8. Do not write narration or scene copy at this stage.
9. Treat `memory_context` as historical research leads only.

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

Past memory may suggest questions or comparison points, but it may not raise a candidate's rank without current-session evidence.

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
- remembered claim revalidation and change from the prior episode

Do not generate a fixed quota merely to fill space. The default range is 8–16 material questions.

Questions must include follow-up potential. A question should be revised when new evidence changes the research direction.

A remembered claim should normally become a research question such as:

```text
Past memory
→ what current evidence would support, weaken, or invalidate it?
→ what has changed since the prior episode?
```

It must not become an answer by itself.

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
   - use selected memory only to identify prior claims and comparison questions
   - collect new current evidence before assigning a current revalidation status

7. **Counter-Hypothesis Researcher**
   - alternative causes, contradictory assets, pre-existing price move, absent sector spillover, source dependence
   - actively test whether a remembered claim has weakened or become invalid

Researchers return evidence items and memory revalidation findings, not polished narrative.

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

Paths under `editorial-memory/`, memory IDs, memory-context files, and retrieval reports are not current evidence. They must never be assigned `E-###` merely to satisfy the contract.

Every Evidence ID referenced from research questions, Expected / Actual, timeline, causal edges, alternative hypotheses, contrary evidence, or memory revalidation must exist in the dossier.

### Stage 5 — Memory revalidation

Every selected non-core item in the retrieval report must receive exactly one result. The manifest must preserve the exact Report metadata and place each selected item in exactly one permitted bucket.

Required fields:

- `memory_reference_type`
- `memory_reference_id`
- `historical_confidence`
- `retrieval_use_mode`
- `revalidation_status`
- `current_evidence_ids`
- `difference_from_previous`
- `editorial_use`
- `notes`

Allowed `revalidation_status` values:

- `not_used`
- `supported`
- `partially_supported`
- `weakened`
- `invalidated`
- `unresolved`
- `historical_context_only`

Rules:

- `supported`, `partially_supported`, `weakened`, and `invalidated` require current tier-1 or tier-2 fact or reported-interpretation evidence.
- discovery-only, unavailable, tier-3, unknown, grounded-inference, and memory references cannot alone establish a revalidation conclusion.
- `historical_context_only` may support comparison or explanation context, but not a current causal edge.
- `not_used` is valid, must have `editorial_use=not_used`, and must not retain current evidence IDs.
- `unresolved` is valid when current evidence is insufficient.
- a memory with retrieval status `invalidated` or `resolved` cannot be used as a current premise.
- `difference_from_previous` must explain what changed, remained unconfirmed, or could not be compared.

Core procedural memory is classified in the research input manifest and is not repeated as an editorial claim revalidation entry.

### Stage 6 — Dynamic causal map

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
- supporting current evidence IDs
- timing alignment
- confidence
- strongest alternative explanation
- whether the edge is required for the final story
- scope: company direct, sector support, NASDAQ-wide, or context only

Do not keep an edge only because it makes the story smoother.

Memory IDs and memory paths cannot appear as causal-edge evidence. A NASDAQ-wide edge must have current tier-1 or tier-2 evidence and cannot be supported only by historical context.

### Stage 7 — Expected / Actual / Gap

Expected must use one of the categories defined by 02:

- official consensus
- prior company guidance
- major reporting
- analyst view
- price-derived inference
- unconfirmed

Record a concrete current source for Expected. If it cannot be verified, set it to unconfirmed and do not fabricate a gap.

Actual must come from verifiable releases, statistics, decisions, or statements.

Gap explains what changed in the market's understanding, not merely whether a number was above or below a forecast.

Editorial memory may identify what was discussed in a prior episode, but it cannot be the sole evidence for Expected, Actual, or Gap.

### Stage 8 — Timeline and alternative-cause test

Before connecting a story to price:

- check whether the move started before the event
- check whether another event occurred in the interval
- check related stocks and indices
- check rates, dollar, oil, VIX, and sector behavior when relevant
- avoid precise intraday wording when intraday data is unavailable
- test whether remembered explanations still fit the current timing

Classify factors as:

- primary cause candidate
- amplifier
- offsetting factor
- unresolved factor

### Stage 9 — Research compression

Compress specialist findings before editorial synthesis.

Remove:

- duplicate syndicated evidence
- facts that do not affect the causal path
- background that cannot reach NASDAQ
- interesting but nonessential company trivia
- unsupported interpretations
- remembered claims that were not revalidated or deliberately retained as historical-only

Preserve:

- the strongest evidence for the provisional lead
- the strongest contrary evidence
- the most credible alternative hypothesis
- uncertainty that changes wording strength
- one or more headline-beyond discoveries
- material differences from prior remembered claims

### Stage 10 — Editorial handoff

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
- `memory_differences`: the limited, revalidated comparison points that may be considered by the editor

The editor then applies 02 and may reject or revise the provisional lead.

The editor must not copy a remembered claim into narration unless its revalidation result permits the intended use and current evidence IDs are available.

## Stopping conditions

Research can stop when all of the following are true:

- the leading contradiction is explicit
- the main causal path has evidence for every material edge
- Expected is sourced or explicitly unconfirmed
- event and price timing are checked to the available resolution
- at least one credible alternative explanation has been tested
- important contrary evidence is retained
- the lead can be separated from a NASDAQ-wide cause when necessary
- every selected non-core memory has a revalidation result
- additional searches are returning mostly duplicate or non-causal information

Do not stop simply because a predetermined number of links was collected.

## Failure modes

Return an incomplete dossier rather than inventing content when:

- the primary source cannot be read
- the relevant time series is unavailable
- Expected cannot be established
- related assets do not support the proposed transmission
- multiple explanations remain equally plausible
- a remembered claim cannot be revalidated with current evidence
- input hashes, retrieval replay, or episode dates do not match

`reason_unknown`, `unresolved`, and `not_used` are acceptable editorial outcomes.

## Validation

Run the v0.2 dossier validator before handing off to 02.

A dossier fails validation when it lacks or violates:

- source provenance
- a contradiction or explicit reason-unknown statement
- alternative hypothesis testing
- a causal edge list
- uncertainty and contrary evidence
- separation of company-direct and NASDAQ-wide claims
- Expected source classification
- research input manifest integrity
- deterministic Query Plan / Context / Report lineage
- repository-relative path safety
- exact Report-to-Manifest selected-memory metadata
- complete classification of selected non-core memory
- current quality evidence for a supported, partially supported, weakened, or invalidated remembered claim
- complete Evidence ID referential integrity
- prohibition on memory-only Expected or NASDAQ-wide causal edges
- prohibition on invalidated/resolved memory as a current premise

Passing validation means the research artifact is structurally complete and memory provenance is controlled. It does not prove that the market interpretation is true.
