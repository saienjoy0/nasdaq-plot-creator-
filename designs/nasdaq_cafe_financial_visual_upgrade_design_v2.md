# 朝のNASDAQカフェ｜Financial Visual Upgrade v2 実装設計・現在地・配送ロードマップ

- 文書名：`nasdaq_cafe_financial_visual_upgrade_design_v2.md`
- 作成日：2026-08-06
- 対象リポジトリ（台本・契約）：`saienjoy0/nasdaq-plot-creator-`
- 対象リポジトリ（レンダラー）：`saienjoy0/saienjoy0-nasdaq-cafe-remotion`
- 現在の作業ブランチ：`feat/financial-visual-intent-contract`
- 現在の契約：Financial Visual Intent Contract `1.0.0`
- 正本参照：01・02 `2.4.2`、03・04 `2.5.0`
- 文書の目的：現在実装した金融映像意図の入口を、最終Episode Package、コンパイル結果、`render_spec.json`、Remotion金融画面、正式validator、previewまで安全に接続する。

---

## 0. 結論

現在実装しているのは、**完成動画そのものではなく、台本側で人間が確定した金融映像意図を、決定的コードが勝手に解釈せず、安全に受け取る入口**である。

これは、朝のNASDAQカフェ全体ロードマップでは次の位置にある。

```text
調査・記憶基盤
→ causal research dossier
→ 02による市場因果の確定
→ 01による狐ナレーション
→ 03による9シーンEpisode Package
→ 04による審問・手直し
→ Financial Visual Intentの承認      ← 今回作った入口
→ 金融Recipe適格性コンパイル         ← 次に接続する
→ 最終制作パッケージ契約
→ render_spec整合検査
→ Remotion金融Recipe
→ validator済みhandoff
→ GitHub Actions preview
→ ユーザー目視確認
```

したがって、今回の実装は、以前から進めている

> 「因果調査まで完成した台本生成側」と「すでに固定Visual Templateを描画できるRemotion側」を、編集判断を失わずにつなぐ

工程の続きである。

次のゴールは、金融画面を増やすこと自体ではない。最終ゴールは次である。

> ChatGPTが確定したExpected / Actual / Gap、指数比較、銘柄差、マクロ波及、出典提示を、その意味と出典を変えず、検証済みの金融画面としてpreviewへ出せる一周を完成させる。

---

## 1. 今どこまでできているか

### 1.1 完成済み

`feat/financial-visual-intent-contract`には、次が実装済みである。

```text
approved Financial Visual Intent
↓
JSON Schema検査
↓
出典・数値・期間・企業・市場セッション検査
↓
preferred Recipeの使用可否判定
↓
条件不足なら宣言済みFallback Recipe
```

実装済みファイル：

```text
contracts/financial_visual_intent.schema.json
scripts/financial_visual_intent.py
designs/FINANCIAL_VISUAL_INTENT_CONTRACT.md
tests/test_financial_visual_intent.py
tests/financial-visual-intent/fixtures/
.github/workflows/financial-visual-intent.yml
```

実装済みIntent：

| Intent | Preferred Recipe | Safe Fallback |
|---|---|---|
| `market-snapshot` | `market-pulse-grid` | `opening-contradiction` |
| `expectation-gap` | `earnings-surprise` | `expected-anchor` |
| `entity-divergence` | `dual-asset-split` | `split-opposition` |
| `macro-transmission` | `macro-pressure` | `causal-build` |
| `source-evidence` | `source-receipt` | `news-media` |

現在のコードが判断するのは、**与えられた証拠形状がpreferred Recipeの条件を満たすか**だけである。

現在のコードは、次を行わない。

- 主役ニュースの選定
- Expectedの創作
- 市場因果の推論
- ナレーションの変更
- Sceneの自動選択
- Visual Beatの自動発明
- 画像生成
- 任意Reactコードの実行
- Remotionコンポーネントの動的指定

この境界は正しい。維持する。

### 1.2 まだ接続されていない

現時点では、次は未完成である。

- Final Episode Package内の正式なFinancial Visual Intent欄
- IntentとVisual Beat IDの一対一または明示的な対応
- preferred / fallback双方の完成画面計画
- Recipe IDとVisual Template IDの明確な分離
- Recipeコンパイル結果の正式schema
- Episode Package、Recipe Plan、`render_spec.json`の一致検査
- Remotion側の新規5金融テンプレート
- plot-creator側とrenderer側の契約version照合
- 実日のproduction bundle
- GitHub Actions preview受入試験

よって、現時点で

> 金融向けの安全な入口は完成したが、本番Episode Packageとレンダラーにはまだつながっていない。

が正しい説明である。

---

## 2. 何の続きなのか

この実装は単独の新機能ではない。既存の二つの流れを接続するための中間契約である。

### 2.1 台本生成側の続き

`nasdaq-plot-creator-`では、すでに次まで整備されている。

```text
memory query plan
→ 選択的な過去記憶検索
→ deterministic replay
→ SHA-bound research input manifest
→ current evidenceによる再検証
→ causal research dossier
```

ここから先に必要なのは、調査結果を次へ変える制作契約である。

```text
causal research dossier
→ 最終Episode Package
→ 04審問後の制作正本
→ Visual Beat確定
→ Primary / Approved Fallback確定
→ spoken script / asset manifest / render spec
```

Financial Visual Intentは、この中の

```text
最終Episode Package
→ Visual Beat確定
→ render spec
```

を金融データ向けに安全に強化するものになる。

### 2.2 Remotion側の続き

Remotion側には、すでに以下がある。

- `opening-contradiction`
- `expected-actual-bullet`
- `expected-actual-gap-flow`
- `metric-comparison-board`
- `index-return-bars`
- `diverging-stock-bars`
- `split-comparison`
- `focus-matrix`
- `causal-lane`
- `tailwind-headwind`
- `evidence-boundary`
- `verification-checklist`
- `verification-matrix`
- `news-media`
- その他の固定Visual Template

つまりRemotion側は「何もない」状態ではない。現在の課題は、既存テンプレートを増やす前に、**台本側が金融画面へ渡す意味、データ形状、出典、Fallbackを正式な契約として閉じること**である。

今回のIntent Contractは、そのための前段である。

---

## 3. 現在確認できた重要な問題

### 3.1 ブランチが最新mainより1コミット遅れている

調査時点で、`feat/financial-visual-intent-contract`は次の状態である。

```text
ahead: 9
behind: 1
status: diverged
```

遅れている1コミットは、現在地と制作ロードマップをmainへ追加した文書コミットである。

したがって、PR作成前に最新mainを取り込み、次を再確認する必要がある。

- Current State and Roadmapとの矛盾がない
- 次工程のPR順を壊していない
- AGENTSやREADMEの現在地説明が古くならない
- CIが最新main上でも全成功する

### 3.2 Recipe IDとVisual Template IDが混在している

現在のIntent Contractでは、preferred / fallbackへRecipe名を入れている。

一方、Remotion本番は`visualTemplate`で具体的な描画方法を固定する。

現時点で以下のpreferred RecipeはRemotion登録済みTemplate IDではない。

```text
market-pulse-grid
earnings-surprise
dual-asset-split
macro-pressure
source-receipt
```

さらに以下のfallback Recipeも、現行Remotionの登録済みTemplate IDとは一致しない。

```text
expected-anchor
split-opposition
causal-build
```

この状態で、Recipe名をそのまま`render_spec.visualTemplate`へ入れてはいけない。

解決策は、次の3層を分けることである。

```text
Financial Visual Intent
= 何を金融画面で伝えたいか

Financial Visual Recipe
= どの検証済み構成で伝えるか

Visual Template
= Remotionが実際に描く固定テンプレート
```

RecipeとTemplateを別フィールドにし、Recipe Compilerが**事前にEpisode Packageで宣言された候補からのみ**具体的Templateを確定する。

### 3.3 Scene IDだけでは粒度が粗い

現行Intent Schemaは`sceneIds`を持つが、03の正本では具体的な見せ方はVisual Beat単位で確定する。

一つのSceneに複数Visual Beatがあるため、SceneだけではどのBeatを置き換えるか決まらない。

次版では、次のターゲットを必須にする。

```json
"targets": [
  {
    "sceneId": "scene-04",
    "visualBeatId": "vb-04-02"
  }
]
```

MVPでは、原則として

```text
1 Intent = 1 Visual Beat
```

に固定する。

複数Beatを一Intentで操作する機能は、実日の受入試験後に別拡張とする。

### 3.4 コンパイラが表示文を発明できる余地を残してはいけない

数値と出典だけ渡しても、見出し、比較基準、表示順、強調対象が不足していれば、コード側が表示を推測することになる。

03では、Visual Beatごとに次をChatGPT側で確定する必要がある。

- 画面の問い
- Headline
- 視聴者向けテキスト
- Template Variant
- 表示順
- 比較基準
- 強調対象
- ノード順
- レーン名
- 最終到達点
- 開始・終了合図
- 復帰先

Financial Visual Intentはこれらを新しく作らず、Episode Package内の対象Visual Beatを参照し、その内容がRecipe条件を満たすか検査する。

### 3.5 04審問の位置を壊してはいけない

04は完成制作パッケージの興味深さとわかりやすさを審査する。金融Recipeが決まる前に最終審問を終えると、Fallback採用後の画面が単調になる可能性がある。

正しい順番は次である。

```text
preferred / fallback双方の画面計画をEpisode Packageで完成
↓
04通常審問
↓
Intent Compilerでselected recipeを決定
↓
Fallback採用時は画面多様性とVisual Beat完成ゲートを再検証
↓
最終Episode Packageをfreeze
↓
render spec生成
```

市場因果やナレーションをFallbackの都合で変更してはいけない。Fallback後に問題がある場合は、画面計画を修正し、必要な範囲だけ再審問する。

---

## 4. 設計原則

### 原則1｜編集判断はChatGPT側で完成させる

Intent、Recipe候補、画面の問い、見出し、数字、比較基準、出典、表示順、FallbackはEpisode Package作成時に決定する。

### 原則2｜コードは資格判定と一致検査だけを行う

決定的コードは、approved Intentと証拠形状を検査し、事前宣言されたpreferredまたはfallbackを選択する。

コードは第三の案を発明しない。

### 原則3｜Remotionは選ばない

Remotionは`render_spec.json`に残された一つの`visualTemplateId`と入力を描画するだけである。

Scene番号、文章、単語、数値の正負、単位、ノード数からTemplateを推測しない。

### 原則4｜終値しかないなら終値画面だけを作る

close-onlyデータから架空の折れ線、分足反応、反転タイミングを作らない。

### 原則5｜出典のない数字と因果は表示しない

すべてのmetric、causal step、source evidenceはEpisode Packageの`sourceIds`へ解決できなければならない。

### 原則6｜preferredとfallbackを両方先に完成させる

コンパイル失敗後にコードが適当なFallbackを作るのではなく、Episode Package内に意味を守るFallbackを事前記録する。

### 原則7｜render specには採用経路だけを残す

非採用Recipe、非採用Template、未使用数字、未採用ナレーションは本番`render_spec.json`へ入れない。

### 原則8｜金融画面追加で番組を数字スライド化しない

03の画面多様性ゲート、EntityFocus、News、PictureBook、復帰先、前半・後半の大きな画面変化を維持する。

---

## 5. 目標アーキテクチャ

```text
[ChatGPT editorial work]
causal research dossier
→ 02 market causality
→ 01 fox narration
→ 03 episode package draft
→ Visual Beat plan
→ approved Financial Visual Intent
→ preferred visual plan + approved fallback visual plan
→ 04 entertainment inquisition

[deterministic compile]
final episode package contract
→ financial intent validator
→ financial recipe eligibility compiler
→ selected financial recipe plan
→ production artifact compiler
→ spoken script
→ asset manifest
→ render spec
→ cross-artifact consistency validator

[handoff]
validator reports
→ contract compatibility check
→ handoff manifest
→ renderer repository

[renderer]
render spec schema validation
→ public view model
→ fixed financial template registry
→ Gemini TTS 2 blocks
→ Remotion preview
→ lightweight technical report
→ user visual review
```

---

## 6. 契約の階層

### 6.1 Financial Visual Intent

目的：編集側が何を金融画面で伝えたいかを記録する。

例：

- 市場全体のスナップショット
- Expected / Actual / Gap
- 二銘柄の反応差
- マクロからNASDAQへの波及
- 出典そのものの提示

Intentは意味の層であり、Remotionコンポーネントではない。

### 6.2 Financial Visual Candidate Plan

目的：preferredとfallbackそれぞれについて、具体的なVisual Template、Variant、対象Beat、表示データを完成させる。

Episode Package側で両方を作る。

### 6.3 Financial Recipe Plan

目的：Intent Compilerが選んだ一つの経路を、監査可能な機械出力として記録する。

このファイルは編集正本ではない。選択結果の監査記録である。

推奨ファイル：

```text
production/YYYY-MM-DD/financial_recipe_plan.json
```

### 6.4 Visual Template

目的：Remotionが実際に描く固定テンプレート。

`render_spec.json`には具体的なTemplate IDを一つだけ残す。

---

## 7. Financial Visual Intent Contract v1.1.0

現行1.0.0は安全な独立入口として維持できるが、Episode Package統合前に1.1.0へ更新する。

### 7.1 必須項目

```json
{
  "contractVersion": "1.1.0",
  "episodeDate": "2026-07-31",
  "intentId": "fvi-aws-expectation-gap",
  "kind": "expectation-gap",
  "targets": [
    {
      "sceneId": "scene-04",
      "visualBeatId": "vb-04-02"
    }
  ],
  "metrics": [],
  "causalSteps": [],
  "sourceIds": [],
  "dataPrecision": "reported-result",
  "chartPolicy": "no-series",
  "preferredPlanId": "fvp-aws-gap-preferred",
  "fallbackPlanId": "fvp-aws-gap-fallback",
  "status": "approved",
  "editorialNote": null
}
```

### 7.2 変更点

- `sceneIds`を`targets`へ置換する
- `visualBeatId`を必須にする
- `preferredRecipe` / `fallbackRecipe`をPlan参照へ変更する
- RecipeとTemplateをIntentから直接混同しない
- 1 Intent 1 BeatをMVP制約にする
- Episode Package側source registryへの完全参照を必須にする
- episode date、target scene、target beatの一致を検査する

### 7.3 status

```text
proposed
approved
```

本番コンパイルは`approved`だけを受け入れる。

`proposed`は必ずFallbackという現在の動作ではなく、Final Production Packageでは原則コンパイル停止にする。

理由：最終Episode Packageへ`proposed`が残っていること自体が未解決状態だからである。

ただし、Intent単体CLIの開発fixtureでは、`proposed → fallback`互換モードを残してよい。

本番モードとfixture互換モードを分ける。

---

## 8. Financial Visual Candidate Plan Schema

新規schema：

```text
contracts/financial_visual_candidate_plan.schema.json
```

例：

```json
{
  "planVersion": "1.0.0",
  "planId": "fvp-aws-gap-preferred",
  "intentId": "fvi-aws-expectation-gap",
  "path": "preferred",
  "recipeId": "earnings-surprise",
  "visualTemplateId": "earnings-surprise",
  "templateVariant": "zero-baseline",
  "sceneId": "scene-04",
  "visualBeatId": "vb-04-02",
  "screenState": "Chart",
  "metricIds": ["aws-expected", "aws-actual", "aws-gap"],
  "causalStepIds": [],
  "displayOrder": ["aws-expected", "aws-actual", "aws-gap"],
  "comparisonBasis": "AWS revenue, same quarter and currency",
  "highlightObjectIds": ["aws-gap"],
  "headlineRef": "episode://scene-04/vb-04-02/headline",
  "screenQuestionRef": "episode://scene-04/vb-04-02/screenQuestion",
  "startCueRef": "episode://scene-04/vb-04-02/startCue",
  "endCueRef": "episode://scene-04/vb-04-02/endCue",
  "returnTargetRef": "episode://scene-04/vb-04-02/returnTarget",
  "sourceIds": ["source-001", "source-004"]
}
```

Fallback例：

```json
{
  "planVersion": "1.0.0",
  "planId": "fvp-aws-gap-fallback",
  "intentId": "fvi-aws-expectation-gap",
  "path": "fallback",
  "recipeId": "expected-anchor",
  "visualTemplateId": "expected-actual-bullet",
  "templateVariant": "zero-baseline",
  "sceneId": "scene-04",
  "visualBeatId": "vb-04-02",
  "screenState": "Chart",
  "metricIds": ["aws-expected", "aws-actual"],
  "causalStepIds": [],
  "displayOrder": ["aws-expected", "aws-actual"],
  "comparisonBasis": "AWS revenue, same quarter and currency",
  "highlightObjectIds": ["aws-actual"],
  "headlineRef": "episode://scene-04/vb-04-02/fallbackHeadline",
  "screenQuestionRef": "episode://scene-04/vb-04-02/fallbackQuestion",
  "startCueRef": "episode://scene-04/vb-04-02/startCue",
  "endCueRef": "episode://scene-04/vb-04-02/endCue",
  "returnTargetRef": "episode://scene-04/vb-04-02/returnTarget",
  "sourceIds": ["source-001", "source-004"]
}
```

重要：Fallbackは単なるTemplate名ではない。見出し、問い、表示対象、比較基準、復帰先まで完成させる。

---

## 9. Recipe Registry

新規正本：

```text
contracts/financial_recipe_registry.json
```

またはコード定数：

```text
scripts/financial_recipe_registry.py
```

Recipe Registryは、IntentとRecipe、許可Template、必要データ形状を固定する。

### 9.1 推奨登録

| Recipe ID | 用途 | 許可Template | 条件 |
|---|---|---|---|
| `market-pulse-grid` | 指数・大型株・半導体の同一セッション比較 | `market-pulse-grid` | 3〜6 metrics、同日、同単位 |
| `opening-contradiction` | 市場方向と矛盾 | `opening-contradiction` | 1中心方向＋最大3材料 |
| `earnings-surprise` | Expected / Actual / Gap | `earnings-surprise` | E/A/G同一entity・unit・currency・period、Gap整合 |
| `expected-anchor` | ExpectedとActualを安全に比較 | `expected-actual-bullet`、`metric-comparison-board`、`text-focus` | Episode Packageで具体Templateを事前宣言 |
| `dual-asset-split` | 二銘柄の反応差 | `dual-asset-split` | 異なるentity、同日、同unit |
| `split-opposition` | 二対象を安全に左右比較 | `split-comparison` | Episode Packageで左右を事前宣言 |
| `macro-pressure` | マクロanchorからNASDAQまでの圧力経路 | `macro-pressure` | anchor 1、causal steps 2〜4、全出典あり |
| `causal-build` | 既存因果図Fallback | `causal-lane` | 2〜4 node、1〜3 arrow、一本道 |
| `source-receipt` | 出典の主体・時刻・確認内容を提示 | `source-receipt` | source metadata、表示するclaim/metricの出典一致 |
| `news-media` | 現実素材または出典カード | `news-media` | assetまたはsource metadataの完成 |

### 9.2 TemplateをCompilerが推測しない

Recipeに複数の許可Templateがある場合も、Compilerが内容を読んで選ばない。

Episode Packageでpreferred / fallback Candidate Planの具体Templateを選んでおき、Registryは許可されている組み合わせかだけ検査する。

---

## 10. Intent別の詳細仕様

### 10.1 market-snapshot

目的：一晩の市場方向、主役銘柄、比較対象を同じ市場セッションで整理する。

Preferred `market-pulse-grid`：

- 3〜6 metrics
- 同じsession date
- 原則同じunit（騰落率ならpercent）
- 指数、主役企業、比較企業、半導体指数などの役割を明示
- close-onlyでも使用可能
- 時系列線は使わない
- 中心対象を一つだけ強調

Fallback `opening-contradiction`：

- 中心指数方向
- 主役反応
- 相殺または非波及材料
- 最大4項目

### 10.2 expectation-gap

目的：良い悪いではなく、Expectedに対してActualが何を変えたかを見せる。

Preferred `earnings-surprise`：

- expected、actual、gapの3役割
- 同一entity
- 同一period
- 同一unit
- currencyが必要な場合は同一currency
- `gap = actual - expected`
- 差の方向を表示文とnumeric valueで一致
- Expected basis typeとsource IDsがEpisode Packageと一致

Fallback `expected-anchor`：

- Gapを表示しない
- ExpectedとActualの比較だけ、または確認済みの一方だけを表示
- なぜGapを使わないかを制作側のreasonへ残す
- 視聴者向け画面に「validator fail」のような制作情報を出さない

### 10.3 entity-divergence

目的：同じ夜に二つの企業・指数が異なる反応をしたことを見せる。

Preferred `dual-asset-split`：

- 左右2対象
- entity IDが異なる
- 同一市場セッション
- 同一unit
- 共通のゼロ基準
- 左右の役割、直接材料、共通背景を区別
- 一日の反応差だけで「勝者選別」を断定しない

Fallback `split-opposition`：

- 既存`split-comparison`
- 反応差の事実だけを安全に並べる
- 因果の強い結論を追加しない

### 10.4 macro-transmission

目的：金利、原油、政策、供給網などがAI・半導体・大型テックを通じてNASDAQへ届く経路を見せる。

Preferred `macro-pressure`：

- macro anchor 1つ
- causal step 2〜4
- 最終到達点をNASDAQ、SOX、または具体セクターへ固定
- 各stepにsource ID
- 直接事実、共有解釈、推論の区分を保持
- 重みや寄与率を根拠なしで定量化しない

Fallback `causal-build`：

- 既存`causal-lane`
- 左から右の一本道
- 最大4 node、3 arrow
- 反対材料は別Beatまたは`tailwind-headwind`で残す

### 10.5 source-evidence

目的：視聴者に、何をどの主体から確認したかを短く見せる。

Preferred `source-receipt`：

- publisher / issuer
- source type
- publishedAtまたはofficial filing date
- 確認した数字または短いclaim
- ナレーション帰属と一致
- 記事全文や長い引用を表示しない
- 内部URL、ローカルpath、認証情報を公開View Modelへ出さない

Fallback `news-media`：

- 既存の確認済みニュース素材またはsource card
- asset statusと権利状態を満たす
- source-evidenceの意味を維持する

---

## 11. Final Episode Packageへの組み込み

### 11.1 人間向けMarkdown

各対象Visual Beatへ次を追加する。

```text
Financial Visual Intent：fvi-...
Intent Kind：expectation-gap
Intent Status：approved
Preferred Candidate Plan：fvp-...-preferred
Approved Fallback Candidate Plan：fvp-...-fallback
Compiler Selection：未実行 / preferred / fallback
Compiler Reason：未実行 / reason code
Selected Recipe：未確定 / recipe ID
Selected Visual Template：未確定 / template ID
Fallback後の画面多様性再検証：未実行 / pass / fail / not-required
```

### 11.2 機械可読sidecar

Markdownを脆い正規表現で解析しない。

Final Production Package Contractで、同じ完成内容から次を生成する。

```text
production/YYYY-MM-DD/final_episode_contract.json
```

このJSONは第三の編集正本ではない。Episode Packageの機械可読mirrorである。

必須：

- `episode_package_YYYY-MM-DD.md`のSHA-256
- contract version
- episode date
- Scene 1〜9
- Visual Beat IDs
- narration cue references
- visual template candidate plans
- source registry
- asset references
- selected image path
- 04 verdict

MarkdownとJSONを別々に手編集しない。ChatGPTが同じ完成内容から同時生成し、validatorがSHAと内容一致を検査する。

---

## 12. Recipe Compiler出力

新規schema：

```text
contracts/financial_recipe_plan.schema.json
```

推奨出力：

```json
{
  "contractVersion": "1.0.0",
  "episodeDate": "2026-07-31",
  "episodePackageSha256": "...",
  "intentContractVersion": "1.1.0",
  "recipeRegistryVersion": "1.0.0",
  "selections": [
    {
      "intentId": "fvi-aws-expectation-gap",
      "sceneId": "scene-04",
      "visualBeatId": "vb-04-02",
      "eligibility": "eligible",
      "selectedPath": "preferred",
      "selectedPlanId": "fvp-aws-gap-preferred",
      "selectedRecipeId": "earnings-surprise",
      "selectedVisualTemplateId": "earnings-surprise",
      "sourceIds": ["source-001", "source-004"],
      "metricIds": ["aws-expected", "aws-actual", "aws-gap"],
      "reasonCodes": []
    }
  ]
}
```

Fallback時：

```json
{
  "eligibility": "fallback-required",
  "selectedPath": "fallback",
  "selectedPlanId": "fvp-aws-gap-fallback",
  "selectedRecipeId": "expected-anchor",
  "selectedVisualTemplateId": "expected-actual-bullet",
  "reasonCodes": ["GAP_VALUE_MISMATCH"]
}
```

### 12.1 reason code

最低限：

```text
INTENT_NOT_APPROVED
TARGET_BEAT_NOT_FOUND
TARGET_SCENE_MISMATCH
SOURCE_ID_NOT_FOUND
METRIC_SOURCE_NOT_DECLARED
CAUSAL_SOURCE_NOT_DECLARED
EXPECTED_ACTUAL_ENTITY_MISMATCH
EXPECTED_ACTUAL_UNIT_MISMATCH
EXPECTED_ACTUAL_CURRENCY_MISMATCH
EXPECTED_ACTUAL_PERIOD_MISMATCH
GAP_VALUE_MISMATCH
SESSION_DATE_MISMATCH
DIVERGENCE_ENTITY_NOT_DISTINCT
INTRADAY_SERIES_REQUIRED
SERIES_DATA_NOT_VERIFIED
RECIPE_TEMPLATE_PAIR_NOT_ALLOWED
PREFERRED_PLAN_INVALID
FALLBACK_PLAN_INVALID
```

本番ではFallback Planもinvalidなら停止する。第三の代替は作らない。

---

## 13. render_spec統合

Renderer schemaを`2.2.0`から互換性を確認してminor bumpする。推奨：`2.3.0`。

各対象Visual Beatへ、公開描画に不要な監査情報を内部フィールドとして追加する。

例：

```json
{
  "visualBeatId": "vb-04-02",
  "visualTemplate": "earnings-surprise",
  "templateVariant": "zero-baseline",
  "financialVisualTrace": {
    "intentId": "fvi-aws-expectation-gap",
    "selectedPlanId": "fvp-aws-gap-preferred",
    "selectedPath": "preferred",
    "recipeId": "earnings-surprise",
    "recipePlanSha256": "..."
  }
}
```

`financialVisualTrace`は公開View Modelへ渡さない。

### 13.1 必須一致

Episode Package、Final Episode Contract、Recipe Plan、render specで次を一致させる。

- episode date
- scene ID
- visual beat ID
- start cue / end cue
- screen state
- visual template ID
- template variant
- metric IDs
- causal step IDs
- source IDs
- display order
- comparison basis
- selected path
- return target

### 13.2 render specへ残さないもの

- non-selected Candidate Plan
- non-selected Recipe
- non-selected Template
- invalid metric
- invalid Gap
- proposed Intent
- editor-only reason text
- private source URL
- local filesystem path

---

## 14. Remotion側の新規金融Template

新規Templateは既存の固定画面シェル、色トークン、フォント、セーフマージン、字幕領域、狐位置を変更しない。

### 14.1 market-pulse-grid

構成：

- 3〜6セル
- 中心指数または主役を1セル強調
- 同一ゼロ基準または明示的な単位
- 指数、主役、半導体、比較対象を役割ラベルで区別
- 順次表示
- 完成ホールド0〜1500ms
- close-only対応

禁止：

- 終値だけでライン描画
- 異なる期間の騰落率混在
- 異なる通貨・単位の同一バー比較

### 14.2 earnings-surprise

構成：

- Expected基準線
- Actual到達表示
- Gapの差分表示
- 3段階の明確な順序
- 差の方向を数値と文言で一致

禁止：

- E/A/Gの期間不一致
- currency不一致
- Gapの再計算をRenderer側で行うこと

Rendererは渡されたvalidated numeric valueを描画し、意味を再計算しない。

### 14.3 dual-asset-split

構成：

- 左右2対象
- 共通ゼロライン
- 同一session label
- 左右の直接材料ラベル
- 中央に共通テーマまたは比較基準

禁止：

- 企業数を自動拡張
- 単位の異なる左右比較
- 一日の反応差から「勝者」を自動表示

### 14.4 macro-pressure

構成：

- macro anchor
- 2〜4 causal nodes
- 最終到達点
- 方向性のある矢印
- 反対材料が必要な場合は別の`tailwind-headwind` Beatへ分離

禁止：

- 根拠のない寄与率
- 5ノード以上への自動圧縮
- 矢印の接続推測

### 14.5 source-receipt

構成：

- source主体
- source type
- date/time
- 確認したclaimまたはmetric
- narration attribution

禁止：

- 記事全文
- 長い引用
- 内部URL
- 著作権状態不明のページスクリーンショットを自動表示

---

## 15. Remotion側の実装ファイル案

```text
src/spec/financial-recipe-contract.ts
src/spec/financial-recipe-registry.ts
src/spec/validate-financial-visual.ts
src/components/spec/financial/MarketPulseGrid.tsx
src/components/spec/financial/EarningsSurprise.tsx
src/components/spec/financial/DualAssetSplit.tsx
src/components/spec/financial/MacroPressure.tsx
src/components/spec/financial/SourceReceipt.tsx
src/components/spec/VisualTemplateRenderer.tsx
src/spec/visual-template-contract.ts
src/spec/public-view-model.ts
schemas/render_spec.schema.json
scripts/test-financial-visual-templates.ts
scripts/test-financial-visual-validator.ts
```

`VisualTemplateRenderer.tsx`へ任意動的importを追加しない。既存のallowlist registryへ明示的に登録する。

---

## 16. Cross-Repository Contract Compatibility

plot-creatorとrendererが別リポジトリであるため、契約versionとSHAをhandoffへ固定する。

`handoff_manifest.json`へ追加：

```json
{
  "plotCreatorContract": {
    "financialIntentVersion": "1.1.0",
    "financialRecipePlanVersion": "1.0.0",
    "finalEpisodeContractVersion": "1.0.0"
  },
  "rendererContract": {
    "renderSpecVersion": "2.3.0",
    "financialTemplateRegistryVersion": "1.0.0"
  },
  "compatibility": {
    "status": "pass",
    "matrixId": "financial-visual-compat-2026-08"
  }
}
```

互換表をどちらか一方のリポジトリにだけ置かず、plot-creator側のhandoff validatorとrenderer側のinput validatorで同じ許可組み合わせを検査する。

---

## 17. Validator構成

### Gate FV-0｜Schema

- Intent schema
- Candidate Plan schema
- Recipe Plan schema
- Final Episode Contract schema
- Render Spec schema

### Gate FV-1｜Editorial linkage

- Intentのtarget Beatが存在
- SceneとBeat所属が一致
- source IDがEpisode Packageに存在
- metricとcausal stepのsourceがtop-level source IDsに含まれる
- Expected basisがScene 4およびeditorial summaryと一致

### Gate FV-2｜Preferred eligibility

- kind別条件
- Gap計算
- unit / currency / period / entity
- session date
- data precision
- chart policy

### Gate FV-3｜Fallback completeness

- Fallback Candidate Planが存在
- Fallback RecipeとTemplate pairがRegistryで許可
- Fallbackの見出し、表示対象、比較基準、復帰先が完成
- Fallbackもsource完全参照

### Gate FV-4｜Selection freeze

- selected pathが一つ
- selected planが一つ
- non-selected pathをrender specへ混入させない

### Gate FV-5｜Cross-artifact consistency

- Episode Package
- Final Episode Contract
- Recipe Plan
- spoken script
- asset manifest
- render spec

の一致。

### Gate FV-6｜Visual diversity after fallback

- 画面状態3種類以上
- 非分析画面2Beat以上
- 前半・後半の大きな画面変化
- 同一画面状態4Beat連続なし
- 主役カード条件
- 復帰先

### Gate FV-7｜Renderer compatibility

- render spec version
- Template registry version
- Template ID存在
- Variant許可
- object count
- numericValue要件
- node / arrow上限

### Gate FV-8｜Preview technical check

- 必須ファイル
- TTS 2ブロック
- 音声生成
- MP4生成
- asset loading
- Remotion exit code

AI視覚検査は行わない。

---

## 18. テスト計画

### 18.1 Intent単体

既存7テストを維持し、次を追加する。

- target Beat不存在
- Scene / Beat mismatch
- duplicate target
- preferred Plan不存在
- fallback Plan不存在
- Recipe / Template不許可組み合わせ
- approvedだがFallback未完成
- source IDはtop-levelにあるがmetric側にない
- Episode Date不一致

### 18.2 Intent別正常系

- market-snapshot close-only
- market-snapshot verified intraday
- expectation-gap正しいGap
- expectation-gap Gap不一致でFallback
- entity-divergence同一session
- macro-transmission 2 step
- macro-transmission 4 step
- source-evidence official source

### 18.3 攻撃的負例

- path traversal
- React component名
- CSS文字列
- dynamic import
- external URLをTemplate指定へ注入
- numericValueとvalueText不一致
- sourceの差し替え
- Intent ID重複
- non-selected Planのrender spec混入
- close-onlyからseries Template指定

### 18.4 Cross-repo contract fixture

2026-07-31回を基準fixtureにし、次を固定する。

- AWS Expected / Actual / Gap
- NASDAQ / Amazon / Apple / SOXX close returns
- selected Recipe Plan
- expected render spec fragment
- renderer public view model

plot-creatorとrendererで同一fixture SHAを持ち、片方の更新時に契約差分を検知する。

### 18.5 Visual unit tests

各新Templateについて：

- min object
- max object
- long Japanese label
- positive / negative / zero
- missing optional fields
- motion sequence
- final hold
- 1920×1080 overflow

AI画像評価ではなく、型、overflow計算、要素数、React render、frame生成の機械検査を行う。

---

## 19. 実装順序

既存ロードマップを壊さず、次の順番で進む。

### Phase 0｜現在ブランチの安定化

対象：`feat/financial-visual-intent-contract`

1. 最新mainを取り込む
2. 既存7テストを再実行
3. 本設計書を追加
4. RecipeとTemplateが別概念であることを現行文書へ追記
5. PRを作成
6. reviewで安全境界を確認
7. 問題がなければmerge

このPRではEpisode Package、render spec、rendererを変更しない。

### Phase 1｜既存メインロードマップのPR #8

`Episode Package Memory Reference`を予定どおり実装する。

Financial Visual Intentは記憶機能の代替ではない。先に再検証済みmemoryをEpisode Packageへ安全接続する。

### Phase 2｜Final Production Package Contract

ここでFinancial Visual Intentを正式Episode Packageへ組み込む。

追加：

- `final_episode_contract.schema.json`
- `financial_visual_candidate_plan.schema.json`
- target Visual Beat linkage
- preferred / fallback完成検査
- 04 verdict linkage
- Episode Package SHA mirror

### Phase 3｜Financial Recipe Compiler

追加：

- Intent Contract 1.1.0
- Recipe Registry
- Candidate Plan validator
- Recipe Plan compiler
- reason code
- selected path freeze
- Fallback後の画面多様性再検証

### Phase 4｜Production Artifact Consistency

追加：

- Recipe Plan → render spec compile
- spoken script / asset manifest / render spec一致
- non-selected path除外
- SHA lineage
- official preflight

### Phase 5｜Remotion Financial Templates

renderer側の別PRで5Templateを実装する。

1. schemaとregistry
2. validator
3. public view model
4. component
5. tests
6. fixture acceptance

台本側契約がfreezeする前に自由実装しない。

### Phase 6｜Renderer Handoff Bundle

- contract compatibility
- handoff manifest
- target date
- file SHA
- asset existence
- old render spec prevention

### Phase 7｜Real-Day End-to-End Acceptance

実際の新しい当日資料一件で、次を通す。

```text
daily source
→ causal dossier
→ final episode package
→ 04 review
→ financial intent compile
→ selected recipe
→ final production artifacts
→ handoff
→ Actions preview
→ user visual review
```

### Phase 8｜Daily Operational Entry Point

日次入口を一つに固定する。

この入口は工程を制御するだけで、Intent、Recipe、Templateを自動決定しない。

---

## 20. PR分割案

実際のGitHub PR番号は作成時に決まるため、設計IDで管理する。

### FVU-0｜Intent Contract Stabilization

リポジトリ：plot-creator

- 現在ブランチ
- 最新main取込
- v1.0.0境界明記
- 本設計書

### FVU-1｜Episode Package Financial Visual Integration

リポジトリ：plot-creator

- Intent targets
- Candidate Plans
- Final Episode Contract
- Markdown / JSON mirror

### FVU-2｜Recipe Eligibility Compiler

リポジトリ：plot-creator

- Intent v1.1.0
- Recipe Registry
- Recipe Plan
- reason code
- tests

### FVU-3｜Cross-Artifact Validator

リポジトリ：plot-creator

- Episode / Recipe / spoken / asset / render一致
- selected path freeze
- preflight

### FVU-R1｜Financial Visual Template Registry

リポジトリ：renderer

- schema
- registry
- compatibility
- placeholderではなく全5Templateの契約を先に固定

### FVU-R2｜Financial Visual Components

リポジトリ：renderer

- 5 components
- public view model
- motion
- overflow tests

### FVU-R3｜Cross-Repo Acceptance

両リポジトリ

- shared fixture
- contract matrix
- handoff acceptance
- preview

### FVU-4｜Real-Day Acceptance

- 実日パッケージ
- preview artifact
- user review
- finalは未実行

---

## 21. 各PRの停止条件

次が一つでもあれば次へ進まない。

- branchが最新mainと整合していない
- RecipeとTemplateの区別が曖昧
- target Visual Beat未確定
- approved IntentにFallbackがない
- source ID参照切れ
- Gap計算不一致をpreferredで通す
- close-onlyからseriesを描く
- non-selected pathがrender specへ残る
- Episode Packageとrender specの表示数字が違う
- rendererに未登録Templateを渡す
- 04 verdictが合格条件を満たさない
- Fallback後の画面多様性fail
- asset状態が未解決
- contract version incompatible
- validator fail

---

## 22. MVP完成条件

次を一件の実日で満たした時点でFinancial Visual Upgrade MVP完成とする。

- 5 Intentのうち最低3種類を実際の1エピソードまたは複数エピソードで通す
- preferredとfallbackの双方を少なくとも一度ずつ受入試験する
- Expected / Actual / Gapの数値一致
- close-onlyで架空ラインなし
- entity divergenceの同一session確認
- macro transmissionの全step出典
- source evidenceの公開安全性
- Final Episode Packageとrender spec一致
- Remotion新Templateが登録済み
- Actions preview成功
- ユーザーが見た目を確認できる
- 自動finalへ進まない

---

## 23. 運用完成条件

毎朝、次の入口で安定すること。

```text
ユーザーがdaily sourceを渡す
→ ChatGPTが市場因果・狐台本・Visual Beatを完成
→ approved Financial Visual IntentとFallbackを完成
→ deterministic compiler
→ validator済みproduction bundle
→ renderer handoff
→ preview
→ ユーザー確認
```

運用時にユーザーが金融Template名を毎回指定する必要はない。ただし、ChatGPTは03に従いVisual Beatを設計し、その中でIntent、Candidate Plan、Templateを明示的に決める。

---

## 24. 今すぐ次に行うこと

現在ブランチに対して、次を行う。

1. 最新mainを取り込む
2. 本設計書を`designs/nasdaq_cafe_financial_visual_upgrade_design_v2.md`へ追加する
3. 現行`FINANCIAL_VISUAL_INTENT_CONTRACT.md`へRecipeとVisual Templateの分離を追記する
4. current 7 testsを最新main上で再実行する
5. 追加で「Recipe IDはrender spec Template IDではない」負例テストを入れる
6. Draft PRを作る
7. review後に問題を修正する
8. merge後、既存ロードマップのEpisode Package Memory Referenceへ戻る
9. その次のFinal Production Package ContractでFVU-1を開始する

つまり、直近の進行は次である。

```text
現在のIntent入口を安全にmerge
↓
Episode Package Memory Reference
↓
Final Production PackageへFinancial Visual Intentを統合
↓
Recipe Compiler
↓
render spec整合
↓
Remotion金融Template
↓
実日preview
```

---

## 25. 4観点レビュー

### 編集責任者の観点

- 市場因果やExpectedをコードへ委ねていない
- 一社の材料をNASDAQ全体へ拡大しない
- 反対材料と確信度を保持できる
- タイトルやサムネイルより強い画面結論を作らない

判定：設計上保護される。

### データ契約責任者の観点

- Intent、Recipe、Templateの層が分離される
- source ID、metric ID、Beat IDを追跡できる
- preferred / fallbackが事前宣言される
- SHA lineageとcross-artifact consistencyを検査できる

判定：v1.1.0とCandidate Plan導入が必要。

### Remotion責任者の観点

- Rendererが意味を推測しない
- 固定registryだけを使用する
- 既存シェルと多様性ゲートを維持する
- 新Templateを安全な入力形状へ限定できる

判定：plot-creator側契約freeze後に実装可能。

### 運用・安全責任者の観点

- validator済みだけをhandoffできる
- 古いrender specを防止できる
- preview前にfinalへ進まない
- AI視覚検査を追加せず、ユーザー目視確認を維持する

判定：既存運用方針と整合する。

---

## 26. 非目的

この設計では次を行わない。

- 市場因果の自動決定
- 主役ニュースの自動選定
- Expectedの自動生成
- 自動的な投資助言
- ニュース本文の自動引用
- 任意React / CSS / dynamic import
- 外部画像生成API
- RemotionによるFallback発明
- 代表フレームAI検査
- 完成動画AI視聴
- previewからの自動final

---

## 27. 最終到達点

Financial Visual Upgradeの完成形は、派手なチャートを増やすことではない。

完成形は次である。

> ChatGPTが確定した市場の矛盾、Expected / Actual / Gap、指数方向、銘柄差、世界からNASDAQへの経路、出典と不確実性を、データ形状に合う金融画面へ変換し、どの画面をなぜ使ったかを監査でき、条件不足なら意味を守るFallbackへ落とし、Remotionが一切の編集判断をせずpreviewへ描画できる。

現在は、そのための最初の安全な入口まで完成している。

次は、入口を最終Episode PackageとVisual Beatへ接続し、Recipe Planと`render_spec.json`を同じ正本から生成する段階へ進む。
