---
name: nasdaq-cafe-story-engine
version: 1.1.0
description: Turn a validated causal dossier into an independently reviewed 9-Scene episode package without changing market causality.
---

# Unified Story Engine

Run after `causal_dossier_valid` and before `episode_package_final`. This first implementation is shadow-only and does not modify Daily Production state.

## Absolute boundary

The engine may change explanation order, Scene connections, wording, compression, visual presentation and publishing copy. It may not change the lead, facts, numbers, Expected / Actual / Gap, chronology, causal scope, confidence, counterevidence, uncertainty, official Scene roles or fox history.

When evidence or causality is defective, return to Causal Research or 02. Do not repair factual defects as entertainment edits.

## Pass A — Story Discovery

Do not write narration. Extract before context, central contradiction, naive explanations, evidence tests, explanation update, headline-beyond discovery and after implications. Produce 2–3 angle candidates only when multiple angles survive. One angle plus a reason is valid. For reason-unknown episodes, compare ways to explain uncertainty rather than inventing a cause.

## Pass B — Narrative Architecture

Keep the official Scene 1–9 roles from 03. Record the viewer belief before and after each Scene, new evidence or new meaning, connector, deletion consequence and open-loop movement. Use no more than two open loops; resolve or evidence-back them by Scene 8. Scene 9 opens none.

Scenes 4–7 require at least one real understanding update: `turn`, `complication`, `boundary`, `counterevidence`, `disproof` or `reveal`. Do not force a dramatic reversal.

Scene 1–2 may state direction, contradiction and the central question. Use `HOOK_EXHAUSTS_THE_STORY` when the opening consumes the proof, limitations, counterevidence and validation conditions needed later.

## Pass C — Draft Episode Package

Complete narration, acting intention, expressions, Visual Beats, screen states, telops, numbers, title, thumbnail, description and Primary/Fallback records. Freeze the draft path and SHA-256.

The fox uses `僕`, remains an equal guide, explains meaning after numbers, uses IT analogies 0–2 times and never invents trades or personal history. Avoid procedural narration that merely announces the outline.

## Pass D — Independent Critic

Start a separate invocation/context. Give it the baseline, Claim Ledger, selected angle, completed Draft Episode Package, 01–04, evidence references and draft SHA. Do not provide Author self-scoring or thought notes.

Review the complete production package, not narration alone. Each finding must name exact Scene IDs/field paths, viewer effect, required fix and claims/evidence to preserve. Any unresolved Critical finding blocks finalization.

## Pass E — Targeted Rewrite

Patch only finding-linked fields. Full regeneration is not the default. General Scene reordering is forbidden. `move_explanation_block` may move comparison or explanation only when real chronology remains unchanged.

## Pass F — Causality Preservation

Compare draft and rewrite against the Claim Ledger. Reject evidence loss, modality strengthening, counterevidence removal, chronology distortion, company-to-Nasdaq scope promotion, investment advice or invented fox history.

## Pass G — Final Re-review

Normally use one Critic → patch → re-review cycle. A second round is allowed only while Critical findings remain. Never exceed two rounds. If Critical findings remain, block and return to Pass A/B/C or upstream research.

## Required artifacts

- `working/YYYY-MM-DD/story_engine_package_YYYY-MM-DD.json`
- `episodes/YYYY-MM-DD/episode_package_YYYY-MM-DD.md`
- `verification/YYYY-MM-DD/story_engine_validation_report.json`

Run `validators/validate_story_engine_hardening.py`. Passing the validator does not itself prove the story is interesting; that judgment belongs to the independent Critic.
