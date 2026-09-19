# NASDAQ Cafe: programme-first redesign

## Programme promise

米国株の値動きを入口に、企業・産業・政策・サプライチェーンの仕組みを映像で理解する金融ドキュメンタリー。東アジアとの重要なつながりがある回は、そのつながりが米国市場を見る目をどう変えるかを見せる。

## Evidence and limits of the audit

Reviewed the 2026-08-17 final render (277.5 seconds, 1920×1080), sampled frames, production JSON, Story/Visual reviews and current code. Frame sampling is not continuous motion/audio review. No audience retention data was available. No score below implies measured audience performance.

Observed: subtitle fragmentation of Applied Materials and 102.5; source-receipt templates occupy about 58.6 seconds; S5 draws company-specific expectations → macro oil/retail → NASDAQ, while narration explicitly separates those scopes; S8 comparison has an empty result lane; existing reviews PASS without corresponding findings. The graph defect is reproducible in scripts/remotion_template_data.py, which synthesizes arrows from ordered card lines.

## Changes and ownership

| Problem | Root / owning layer | Change | Acceptance |
|---|---|---|---|
| False causal chain | Plot projection treats adjacency as causality | Current Visual Intelligence accepts explicitly authored graph only; reject cards without graph | Independent company/macro branches never gain a connecting arrow |
| Broken words/numbers | Renderer character slicing | Token-aware bounded subtitle wrapping | Wording preserved, tokens intact when they fit, contiguous timing |
| Little distinctive discovery | Research confuses price transmission with structural links | Independently screen revenue/customer/supply-chain/policy exposure | No automatic omission of Asia solely because intraday cause is US-specific |
| Repeated cards and empty panels | Visual choice/review judges declared intent | Compare real media/data/existing/generated per beat; inspect actual object contents and rendered evidence | Empty claimed comparison or unsupported arrow cannot earn visual approval |
| Story padded into fixed positions | Nine-scene assumptions across contracts | Separate story-function design from versioned production migration | No advertised variable-length production until complete gate matrix passes |

## Scene migration design (not enabled by this patch)

The supported 2.4.0 renderer and Current v1.2 production remain nine-scene. A new version must cover the following together; old frozen packages retain the legacy validator.

1. Story Plan / Script / creative review schemas: ordered unique scene IDs, 5–12 scenes, explicit functions (hook/question/development/discovery/meaning/closing). Functions may share scenes; each scene must change understanding or be removed. Closing means the final scene, not ID 09. Compare 5/7/9/12 alternatives on evidence/payoff, not length quotas.
2. Materialized canon 03/04, authoring/critic operations, package parser, final source annex and scene hardening: make roles semantic, preserve canonical annex ordering and complete evidence references. Freeze the chosen scene list and roles.
3. Renderer render-spec/production/timeline schemas and static validators: branch by contract version; enforce exact chosen IDs/order rather than infer from count. Opening and closing constraints bind explicit role; verification binds the selected payoff scene. No renderer role inference.
4. TTS: explicitly freeze two contiguous non-empty scene blocks at a natural narrative boundary, with each scene exactly once. Include block membership in the new cache identity, retain old two-block caches for legacy input. No API call per scene/chunk and no rate/voice changes.
5. Diversity and motion: evaluate proportionate beginning/end windows and meaningful reveal times, not S1–4/S5–9 or raw beat count. Repetition is justified by explanatory purpose. A shorter episode must not fail merely for fewer arbitrary template families.
6. Intake/freeze receipts and acceptance: bind the new contract and renderer commit; exact-SHA replay. Preview approval must identify that exact output. No mutation of historical artifacts.
7. Gate matrix: valid 5,7,9,12 scenes across authoring → freeze → intake → TTS segmentation → compile → preview; reject missing function, duplicated IDs, orphan edges, missing sources, bad block coverage, stale receipt. Nine-scene legacy tests must remain passing.

This is a production capability gap, not permission to silently weaken nine-scene validators. Ship migration separately from the immediately verifiable subtitle and causal-safety fixes.

## Seven-scene editorial redesign example (design only)

This is not a render_spec, approved script or current market research. Existing claims must be revalidated against immutable current sources before production.

| Scene | Viewer question / change | Best visual | Evidence limit |
|---|---|---|---|
| 1 | How can better earnings coexist with a falling stock? | AMAT reaction large, actual vs expected only; index small context | Keep report timing and price interval explicit |
| 2 | What improved, and what had already been expected? | One expected/actual comparison, reveal gap after values | Consensus must predate release |
| 3 | Where does this US business earn its money? | Geographic revenue comparison + geographic context | The official Q3 release contains regional revenue; geography is exposure, not cause of the selloff or named-customer proof |
| 4 | Does one falling supplier mean all AI demand is weak? | Comparable peer returns plus demand evidence, clearly separated | Peer prices/company forecasts alone do not disprove demand weakness |
| 5 | What explains the company, and what may explain the index? | Two separate explanation panels; explicit evidenced arrows only | High-expectation explanation remains an inference; no company→oil arrow |
| 6 | What does event order establish, and what remains unknown? | Timeline aligned with a verified market series, progressive reveal | Earlier does not mean causal; omit unavailable intraday claims |
| 7 | What has changed in our understanding? | Reassemble the original contradiction with scope/uncertainty visible | Resolve opening promise; identify observable falsifier; concise closing |

An East Asia segment is omitted if the structural evidence adds no meaningful understanding. The example's release reference is https://investor.appliedmaterials.com/news-releases/news-release-details/applied-materials-announces-third-quarter-2026-results ; any published chart needs dated values, units, denominator and bound evidence, not this design link alone.

## Visual capability selection

Choose by question: reality proof → licensed original material/document; magnitude/trend/comparison → deterministic data visualization; location/flow → accurate map or explicit graph; abstract analogy or unavailable lawful imagery → generated conceptual image. Generated content must be recognizable as illustration and cannot fabricate a real document, person/event, exact geographic relationship, number or evidence. Choose Primary and Approved Fallback before generation; bind chosen asset bytes and rights/source status before freeze. Do not generate decoration to satisfy variety counts.

No new standalone Skill is needed. Strengthen Causal Research, Story Plan, Story Authoring, Visual Intelligence and Entertainment Critic. Image generation remains a tool/capability of Visual Intelligence. Keep research, editorial judgment and mechanical rendering responsibilities distinct. Retain independent critique; do not merge it into authoring merely to reduce steps.

## Output evaluation

Evaluate interest, understandability and watchability separately. Record concrete scene/object/frame/timestamp observations and the viewer misunderstanding or payoff; do not treat a JSON PASS, 18 beats or template variety as a viewing result. Review audio and motion continuously before marking them assessed. Collect authentic first-30-second and scene-boundary retention plus comprehension feedback when available; record unavailable data as unassessed. Hypotheses from drop-offs need comparison and investigation, not automatic causal conclusions.
