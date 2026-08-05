# AGENTS.md

## Repository role

This repository is the editorial research and script-contract workspace for 朝のNASDAQカフェ.

It does not render video and it does not delegate editorial judgment to GitHub Actions, Codex, Remotion, or external research frameworks.

## Source-of-truth order

When instructions conflict, apply this order:

1. Current ChatGPT project instructions
2. `source-of-truth/02_editorial_bible.md`
3. `source-of-truth/01_fox_character_bible.md`
4. Materialized `03_episode_production_spec.md`
5. Materialized `04_entertainment_inquisitor.md`
6. Daily input and examples

External projects are references only. They may improve research mechanics, but they may not override market causality, uncertainty, the fox character, the nine-scene contract, or the no-investment-advice rule.

## Required production flow

```text
daily_source_package
→ causal research dossier
→ editorial decision under 02
→ fox narration under 01
→ nine-scene episode package under 03
→ entertainment inquisition under 04
→ image path resolution
→ render_spec generation and validation
→ preview
→ user visual review
→ final only after explicit request
```

Never skip the causal research dossier when the daily input contains more than a simple confirmed single-cause event.

## Research behavior

- Treat the daily package as a starting set of evidence, not as a finished explanation.
- Generate multiple research perspectives before drafting.
- Ask follow-up questions from newly discovered evidence.
- Search historical context, company relationships, supply chain, macro transmission, timeline, and counter-hypotheses.
- Attach a source, evidence class, timestamp, and confidence to every material causal edge.
- Separate fact, reported interpretation, grounded inference, and unknown.
- Preserve important contrary evidence.
- Do not create an Expected value after the fact.
- Do not elevate a single-company event into a NASDAQ-wide cause without index, sector, timing, and alternative-explanation checks.

## External project adoption

The repository may adopt useful patterns from other projects aggressively, but only as isolated mechanics:

- STORM / Co-STORM: perspective-guided questions, simulated follow-up dialogue, dynamic concept map
- Open Deep Research: supervisor/researcher separation, parallel research, compression before synthesis, evaluation
- GraphRAG / Graphiti: entity-relation and temporal evidence retrieval when justified by scale
- Financial multi-agent projects: specialist role separation only

Do not import trading recommendations, target prices, autonomous portfolio decisions, or unsupported sentiment-to-price causality.

## Output contract

The causal research skill produces evidence and candidate explanations. It does not make the final editorial decision and does not write the final narration.

The final decision remains governed by 02, then converted by 01 and 03, then reviewed by 04.
