# 朝のNASDAQカフェ｜Viewer Surface Hardening Master Design v2.0

- 文書種別：二リポジトリ横断・実装設計正本
- Status：READY FOR IMPLEMENTATION REVIEW
- 作成日：2026-08-12
- 編集・制作リポジトリ：`saienjoy0/nasdaq-plot-creator-`
- Renderer：`saienjoy0/saienjoy0-nasdaq-cafe-remotion`
- 対象契約：Final Episode Contract / Financial Visual / Visual Source / Visual Director / render_spec 2.4.0
- 対象外：市場因果の変更、狐人物像の変更、Scene順変更、Final自動実行、Rendererによる編集判断

---

## 0. 結論

2026-08-12 Previewで露出した以下の3問題を、日次パッチではなく契約境界で再発防止する。

1. 字幕・公開画面に数値用途の漢数字が残る。
2. `source-receipt` で定性的な日本語文章が数値オブジェクトとして扱われ、文字衝突する。
3. ChatGPTが `split-comparison` として確定した比較意味が、Visual Directorで疑似棒グラフへ変わる。

修正後の責任分界は次とする。

```text
ChatGPT / 01〜04
  市場因果・9Scene・Visual Beat・画面意味・Primary/Fallbackを確定
        ↓
Plot Viewer Surface Projection
  speechは保持 / displayだけ決定論的に正規化
        ↓
Plot public-surface validator
        ↓
Financial Visual projection
  定量値と定性値をrenderer object型へ正しく投影
        ↓
Visual Source resolution
        ↓
render_spec draft
        ↓
Visual Director Candidate Builder
  Evidence Capability + ChatGPT承認済みTemplate制約から合法候補だけ生成
        ↓
Visual Direction Plan
        ↓
Protected Semantic Diff
        ↓
Renderer layout / public-surface preflight
        ↓
formal validator
        ↓
freeze → immutable handoff → Preview
        ↓
ユーザー目視確認
```

Finalはユーザーの明示依頼がある場合だけ実行する。

---

# 1. 設計原則

## 1.1 既存正本を壊さない

本設計は以下を変更しない。

- `01_fox_character_bible.md`
- `02_editorial_bible.md`
- `03_episode_production_spec.md`
- `04_entertainment_inquisitor.md`
- Expected / Actual / Gap の内部意味
- Visual Grammarの意味分類
- Visual SourceのPrimary / Approved Fallback責任
- immutable handoff
- Renderer 2.4.0の「指定された意味を描画するだけ」という境界

## 1.2 Rendererは意味を修正しない

Rendererが許されるのは以下だけ。

- 入力型の検査
- レイアウト幾何の選択
- 文字量に応じた同一Template内variant選択
- 不正入力のFAIL
- 確定済みTemplateの描画

Rendererは以下を行わない。

- 定性的文章をNumberからCardへ意味変換
- 比較の意味を推測
- 棒グラフにすべきか判断
- 字幕の曖昧な数字を推測変換
- Primary/Fallback選択

## 1.3 Visual Directorは自由な再解釈層ではない

Visual Directorは合法Candidateから選ぶが、Candidate BuilderはChatGPTが確定した画面意味を壊す候補を出してはいけない。

特に「比較対象数」「正負」「Scene番号」「文字列」から別Templateの意味を推測しない。

---

# 2. 現状の問題と根因

## 2.1 speechText / captionTextが同一

現行 `scripts/materialize_chatgpt_daily_authoring.py` は、同一 `chunk["text"]` を `speechText` と `captionText` へ投影している。

このためTTS向けに書かれた、たとえば以下が公開字幕へ漏れる。

```text
〇・六パーセント
二・〇五パーセント
十五時五十九分
二十一時三十分
一分足
```

既存テストは本来 `speechText` と `captionText` を別surfaceとして扱う思想を持っているため、現行materializerが設計に追随できていない。

## 2.2 source-evidenceの定性metricがPublicNumberへ到達

2026-08-12のReuters source evidenceは、Financial Intentでは次のような定性metricである。

```json
{
  "valueText": "再開には米国側の条件履行が必要",
  "numericValue": null
}
```

この値がRendererではNumber系表示へ到達し、`AnimatedMetric` の大きな文字面へ流れる。

根因はCSSではなく、Financial Intent上の「metric」とRenderer public object上の「number」を同一視しているprojectionである。

## 2.3 Visual Directorのcomparison候補が広すぎる

現行Candidate Builderは `comparison-set` capabilityから以下を広く候補化できる。

```text
index-return-bars
diverging-stock-bars
split-comparison
focus-matrix
```

しかし2026-08-12 Scene 2 Beat 2はChatGPT authoringで `split-comparison` として「Brent上昇とNASDAQ下落の方向対比」を明示している。

それでもbars候補が合法になるため、画面意味がVisual Directorで別の比較表現へ漂流する。

---

# 3. Viewer Surface Projection

## 3.1 新規モジュール

Plotへ以下を追加する。

```text
scripts/viewer_surface_projection.py
contracts/viewer_surface_policy.json
contracts/viewer_surface_policy.schema.json
tests/viewer-surface/
```

このモジュールは編集判断をしない。承認済みテキストから、公開表示形式だけを決定論的に投影する。

## 3.2 2種類のsurfaceを明示する

### Speech surface

対象：

```text
speechText
spoken_script
TTS入力
```

原則変更しない。

### Viewer surface

対象：

```text
captionText
headline
supportingTexts
screenQuestion
primaryElement
viewerTexts
card title / value
固定UIラベル
```

公開表示に適したアラビア数字・日本語UIへ正規化する。

## 3.3 実行位置

Viewer Surface Projectionは2段階に分ける。

### A. Authoring-visible copy projection

episode package生成前に以下を正規化する。

```text
headline
supportingTexts
screenQuestion
primaryElement
viewerTexts
card-visible copy
```

これによりepisode packageとrender_specの公開テロップが同じ正規化済み文字列から生成される。

### B. Caption projection

`materialize_chatgpt_daily_authoring.py` が `speechText` を作る際、同じspeechから `captionText` を決定論的に生成する。

captionはTTS原文そのものではないため、episode package内の完成ナレーションとbyte-identicalである必要はない。ただしspeechTextは完成ナレーションと一致させる。

---

# 4. 数値表記正規化

## 4.1 原則

Viewer surfaceでは、数量・時刻・年月日・割合・順位・回数などの数値用途に漢数字を使わない。

例：

```text
〇・六パーセント       → 0.6%
二・〇五パーセント     → 2.05%
二万六千四百四十五・四五 → 26,445.45
一分足                 → 1分足
十五時五十九分         → 15:59
二十一時三十分         → 21:30
七月                   → 7月
四段                   → 4段
三つ                   → 3つ
五千億ドル             → 5,000億ドル
二十五・八億ドル       → 25.8億ドル
```

## 4.2 非対象

以下のような語彙は変換しない。

```text
一方
唯一
一体
三菱
四半期
```

「四半期」は数詞ではなく市場用語として保持する。

## 4.3 決定論的パーサ

外部AIやLLMを使わない。

対応字：

```text
〇 零 一 二 三 四 五 六 七 八 九 十 百 千 万 億 兆
```

数値候補は、以下の確認済み文脈にある場合だけ変換する。

```text
% / パーセント
ドル / 円 / 億ドル / 万ドル
時 / 分 / 秒
年 / 月 / 日
回 / 件 / 社 / 人 / 位 / 番目 / 段 / つ
分足
第<numeric>
```

小数点として `・` を許すのは、両側が数値トークンであり、数値単位へ接続する場合だけ。

## 4.4 曖昧値はFAIL

変換結果を次に分類する。

```text
converted
unchanged-non-numeric
ambiguous
```

`ambiguous` がviewer surfaceへ残った場合：

```text
E_VIEWER_NUMERIC_AMBIGUOUS
```

で停止する。

「たぶん2.5」などの推測変換は禁止。

---

# 5. Viewer Surface Validator

Plot側へ、episode package / render spec freeze前の検査を追加する。

## 5.1 検査対象

```text
captionText
headline
supportingTexts
screenQuestion
primaryElement
viewerTexts
cards[].title
cards[].lines[].label/value
公開固定UI
```

speechTextは本validatorの漢数字禁止対象から外す。

## 5.2 FAIL条件

```text
E_VIEWER_NUMERIC_KANJI_REMAINS
E_VIEWER_NUMERIC_AMBIGUOUS
E_VIEWER_FIXED_UI_ENGLISH
E_VIEWER_FIXED_UI_VARIANT_DRIFT
```

## 5.3 Renderer側の二重防御

Renderer formal validationでも同じviewer surfaceを再検査する。

Rendererは自動修正しない。Plotで漏れたらFAILする。

---

# 6. Expected / Actual / Gap 公開UI統一

内部契約名は変更しない。

```text
expected
actual
gap
```

公開UIは完全に以下へ統一する。

```text
予想
実際
差分
```

禁止する公開固定ラベル：

```text
EXPECTED
ACTUAL
GAP
実績
差
```

ただし記事本文、固有引用、企業名等に偶然含まれる語を禁止するものではなく、金融テンプレートの固定UIラベルだけを対象とする。

Rendererの `docs/15_financial_visual_japanese_ui.md`、Stage系UI、Financial Visual components、回帰テストを同じ正本へ合わせる。

---

# 7. Financial IntentとRenderer Objectの型境界

## 7.1 Semantic metricは維持可能

Financial Intentでは `numericValue: null` の定性metricを許してよい。

これは「Financial Intentの根拠項目」であり、RendererのNumber objectと同義ではない。

## 7.2 Projection規則

Financial selectionをrender objectsへ投影するとき：

```text
numericValue is finite number
  → scene.numbers[]

numericValue is null
  → scene.cards[] または public text object
```

選択されたFinancial metric ID・source ID・表示順の追跡情報は保持する。

数値でないFinancial metricを `scene.numbers[]` に入れない。

## 7.3 SourceReceiptの期待形

Reuters例：

```text
左：
確認済みの根拠
Reutersのホルムズ報道
何が楽観を崩したのか

右：
✓ 再開には米国側の条件履行が必要
✓ 楽観後退
```

「再開には米国側の条件履行が必要」をAnimatedMetricへ送らない。

## 7.4 Renderer防御

`source-receipt` に非数値PublicNumberが到達した場合：

```text
E_SOURCE_RECEIPT_NON_NUMERIC_NUMBER
```

でFAIL。

RendererがCardへ自動移動してはいけない。

---

# 8. SourceReceipt Layout Contract

## 8.1 Renderer pure planner

Rendererへ次を追加する。

```text
src/spec/template-layout/source-receipt-layout.ts
```

中心関数：

```ts
planSourceReceiptLayout(input) -> {
  mode: "side-by-side" | "stacked";
  textMetrics: ...;
}
```

収容不能なら例外を返す。

この関数を以下で共有する。

```text
validate-render-layout.ts
FinancialVisualTemplates.tsx
```

## 8.2 レイアウトmode

### side-by-side

短い見出し・質問向け。

```text
┌────────────┬──────────────┐
│ 見出し     │ 確認済み資料 │
│ 質問       │ ✓ 証拠       │
│            │ ✓ 証拠       │
└────────────┴──────────────┘
```

### stacked

長い日本語向け。

```text
┌──────────────────────────┐
│ 確認済みの根拠           │
│ 見出し                   │
│ 質問                     │
├──────────────────────────┤
│ ✓ 証拠                   │
│ ✓ 証拠                   │
└──────────────────────────┘
```

これは同一 `source-receipt` Template内の幾何variantであり、編集意味は変えない。

## 8.3 text budget

初期安全値を次とする。実装時に既存Stage寸法へ合わせて定数化する。

```text
Primary title      最大2行
Screen question    最大2行
Evidence count     最大4件
Evidence item      最大2行
Comparison/footer  最大1行
```

最低font sizeを下回る縮小は禁止。

## 8.4 横方向の物理衝突禁止

各grid cellへ `minWidth: 0` を必須化し、長文は隣接cellへ侵入させない。

非数値文章に `whiteSpace: nowrap` を適用しない。

## 8.5 overflow

収まらない場合：

```text
E_SOURCE_RECEIPT_TEXT_OVERFLOW
```

省略記号で意味を消す、文字を極小化する、隣領域へ重ねる、の3つは禁止。

---

# 9. Visual Director Candidate Constraint

## 9.1 新しいSemantic Grammarは作らない

`presentationIntent` のような第二の意味階層は追加しない。

既存設計の以下を維持する。

```text
Visual Grammar = 何を理解させるか
visualTemplate = ChatGPTが選んだ具体的な見せ方
Evidence Capability = そのBeatで利用可能な証拠能力
```

本修正で追加するのは「Visual Directorがどこまで代替Templateへ広げてよいか」という**非公開のCandidate制約**だけ。

## 9.2 visualCapabilityHints v1.1

Renderer `src/spec/visual-director-contract.ts` の `visualCapabilityHints` をv1.1へ拡張する。

例：

```json
{
  "contractVersion": "1.1.0",
  "episodeDate": "2026-08-12",
  "beats": [
    {
      "visualBeatId": "scene-02-beat-002",
      "capabilities": ["comparison-set"],
      "templatePolicy": {
        "mode": "allow-list",
        "allowedTemplateIds": ["split-comparison"]
      }
    }
  ]
}
```

`templatePolicy` は公開render_specの意味データではない。Visual Director freeze前だけに使用する。

## 9.3 policy mode

```text
authored-only
allow-list
```

### authored-only

Candidateは現在の `beat.visualTemplate` のみ。

### allow-list

現在のTemplateに加えて、ChatGPTが明示した `allowedTemplateIds` だけをCandidate化できる。

## 9.4 デフォルト

新規daily productionでは、各BeatにtemplatePolicyを必須とする。

候補の広げ方をCandidate Builderが勝手に決めない。

Visual DirectorはcandidateIdだけを選ぶ既存契約を維持する。

## 9.5 8/12 Brent / NASDAQ

Scene 2 Beat 2：

```text
authored visualTemplate = split-comparison
capability = comparison-set
templatePolicy = authored-only
```

Candidate catalog期待値：

```text
split-comparison       YES
index-return-bars      NO
diverging-stock-bars   NO
focus-matrix           NO
```

## 9.6 bars自体は削除しない

別日にChatGPTが「同一セッションの複数銘柄をゼロ基準の大きさで比較する」と判断し、barsをauthoringで選ぶかallow-listへ入れた場合は利用可能。

つまりbarsは「存在するから候補」ではなく「ChatGPTが意味を承認したときだけ候補」とする。

---

# 10. 実時系列と疑似チャート

既存のverified-series制約を維持する。

```text
verified intraday seriesあり
→ event-reaction-timeline候補可

seriesなし
→ ラインチャートを生成しない
```

以下の原則を日次正本へ明文化する。

```text
本物の時系列       → 本物のtimeline / chart
単なる2対象比較    → 承認済みcomparison Template
複数終値一覧       → market snapshot / table系
因果                → causal lane
証拠                → source document / receipt
```

「画面をそれっぽくするためだけの疑似グラフ」は使用しない。

---

# 11. Visual Source再利用

既存 `VISUAL_SOURCE_UPGRADE_MASTER_DESIGN_v1_1.md` の責任分界を変更しない。

source-evidence Beatでは、ChatGPTが事前に以下を完成させる。

```text
Primary
Approved Fallback
選択理由
Fallbackでも因果・留保が保たれる理由
```

実資料が解決済みなら：

```text
Primary = source-document / news-media
```

取得不能・権利未確認・locator不足なら：

```text
Approved Fallback = source-receipt
```

Actions / Renderer / resolverはPrimary/Fallbackを自動選択しない。

---

# 12. episode_package / render_spec整合

## 12.1 Spoken narration

`episode_package` の完成ナレーションとrender_spec `speechText` は一致させる。

Viewer captionは読みやすさのためアラビア数字へ投影可能で、speechTextとbyte-identicalである必要はない。

## 12.2 Telop / viewer copy

以下はepisode package生成前に正規化し、episode packageとrender_specで完全一致させる。

```text
headline
supportingTexts
screenQuestion
primaryElement
viewerTexts
```

## 12.3 Protected Semantic Diff

Visual Director後も以下を不変とする。

```text
speechText
captionText
headline
supportingTexts
screenQuestion
primaryElement
viewerTexts
数字
source IDs
Scene順
Expected / Actual / Gap
因果
反対材料
確信度
```

Template/variant/screen state等、承認Candidateが持つvisual fieldだけ変更可能。

---

# 13. 監査ログ

Plotで以下を生成する。

```text
working/YYYY-MM-DD/viewer_surface_projection_report.json
```

最低項目：

```json
{
  "contractVersion": "1.0.0",
  "episodeDate": "YYYY-MM-DD",
  "speechTextChanged": false,
  "conversions": [],
  "ambiguousCount": 0,
  "viewerKanjiNumericCount": 0,
  "fixedUiViolations": 0,
  "status": "PASS"
}
```

各conversionはsource path、before、after、rule IDを残す。

市場意味や因果の変更ログとしては扱わない。

---

# 14. Failure Codes

## Plot

```text
E_VIEWER_NUMERIC_AMBIGUOUS
E_VIEWER_NUMERIC_KANJI_REMAINS
E_VIEWER_FIXED_UI_ENGLISH
E_VIEWER_FIXED_UI_VARIANT_DRIFT
E_FINANCIAL_QUALITATIVE_PROJECTED_AS_NUMBER
E_VISUAL_DIRECTOR_TEMPLATE_POLICY_MISSING
E_VISUAL_DIRECTOR_TEMPLATE_NOT_ALLOWED
```

## Renderer

```text
E_SOURCE_RECEIPT_NON_NUMERIC_NUMBER
E_SOURCE_RECEIPT_TEXT_OVERFLOW
E_VIEWER_NUMERIC_KANJI_REMAINS
E_VIEWER_FIXED_UI_ENGLISH
E_VISUAL_DIRECTOR_TEMPLATE_NOT_ALLOWED
```

FAIL時に自動fallback、Template変更、テキスト短縮を行わない。

---

# 15. 実装PR構成

## PR-R1｜Renderer Viewer & Visual Hardening

Repository：`saienjoy0/saienjoy0-nasdaq-cafe-remotion`

変更予定：

```text
src/spec/visual-director-contract.ts
src/spec/visual-candidate-builder.ts
src/spec/validate-render-layout.ts
src/spec/template-layout/source-receipt-layout.ts          NEW
src/components/spec/FinancialVisualTemplates.tsx
src/components/spec/StageSafeArea.tsx
scripts/test-visual-director.ts
scripts/test-financial-visual-templates.tsx
scripts/test-stage-legibility-contract.tsx
docs/15_financial_visual_japanese_ui.md
docs/16_visual_director_contract.md
```

必要に応じてschema generator / checked-in schemaを更新する。

責任：

- `予想 / 実際 / 差分` 統一
- SourceReceipt非数値Number拒否
- SourceReceipt layout planner
- text budget
- visualCapabilityHints v1.1 / templatePolicy
- Candidate Builder allow-list enforcement
- Renderer viewer-surface fail-closed

## PR-P1｜Plot Viewer Surface Projection

Repository：`saienjoy0/nasdaq-plot-creator-`

変更予定：

```text
scripts/viewer_surface_projection.py                    NEW
contracts/viewer_surface_policy.json                   NEW
contracts/viewer_surface_policy.schema.json            NEW
tests/viewer-surface/                                  NEW
scripts/materialize_chatgpt_daily_authoring.py
scripts/fixup_chatgpt_daily_materialization.py
scripts/build_final_production_package.py              必要最小限
Financial Visual render object projection箇所
Visual Director hint生成箇所
skills/nasdaq-cafe-daily-production/SKILL.md           必要なら工程追記
```

責任：

- viewer-visible copyの正規化
- speech/caption分離
- 漢数字validator
- qualitative Financial metric → Card/Text
- Visual Director templatePolicy出力
- projection audit log
- episode_package/render_spec整合保持

## PR-I1｜Pinned Integration / Real-Day Acceptance

Repository：`saienjoy0/nasdaq-plot-creator-`

R1とP1のCI通過・main merge後にのみ実施。

変更：

```text
.github/workflows/chatgpt-daily-preview-production.yml
.github/workflows/daily-renderer-closure-gate.yml
scripts/run_daily_renderer_closure.py
```

新Rendererの**1つのmerge SHA**へまとめてpinする。

途中のRenderer SHAへ何度もpinしない。

8/12のcandidate catalog / direction planは新specから正規に再生成し、SHA bindingを弱めない。

---

# 16. 回帰テスト

## 16.1 数字表示

必須：

```text
speech: 〇・六パーセント
caption: 0.6%

speech: 二・〇五パーセント
caption: 2.05%

speech: 一分足
caption: 1分足

speech: 十五時五十九分
caption: 15:59

speech: 五千億ドル
caption: 5,000億ドル
```

非変換：

```text
一方
唯一
三菱
四半期
```

## 16.2 Fixed UI

Renderer static markupに以下だけ存在：

```text
予想
実際
差分
```

固定UIとして以下が存在しない：

```text
EXPECTED
ACTUAL
GAP
実績
差
```

## 16.3 SourceReceipt

ケースA：短文

```text
side-by-side PASS
```

ケースB：長い日本語

```text
stacked PASS
```

ケースC：定性metricがNumberへ混入

```text
FAIL E_SOURCE_RECEIPT_NON_NUMERIC_NUMBER
```

ケースD：最大容量超過

```text
FAIL E_SOURCE_RECEIPT_TEXT_OVERFLOW
```

## 16.4 Visual Director

8/12 fixture：

```text
Beat: scene-02-beat-002
authored template: split-comparison
policy: authored-only
```

catalog：

```text
split-comparison       present
index-return-bars      absent
diverging-stock-bars   absent
focus-matrix           absent
```

別fixtureで明示allow-list時だけbars候補が生成されることを確認する。

## 16.5 Protected Diff

Visual Director compile前後で次のSHAが一致：

```text
speech / caption
all viewer copy
numbers
sources
Scene order
causal fields
counterevidence
```

---

# 17. 2026-08-12 Real-Day Acceptance

8/12を恒久fixtureとして使用する。

Preview前の必須結果：

```text
viewer_surface_projection_report.status = PASS
ambiguousCount = 0
viewerKanjiNumericCount = 0
fixedUiViolations = 0
Financial qualitative-as-number violations = 0
Visual Director catalog SHA = plan binding SHA
Protected Semantic Diff = PASS
Renderer layout validation = PASS
Renderer formal validator = PASS
image selection unresolved = 0
```

Preview目視で確認する項目：

```text
1. 字幕数値がアラビア数字
2. 予想 / 実際 / 差分
3. Reuters SourceReceiptの文字衝突なし
4. Reuters定性文章が巨大数値表示されない
5. Brent / NASDAQの疑似棒グラフが出ない
6. 実1分足は実時系列として表示
7. Primary/Fallback採用経路が確定
8. 画面多様性が既存基準を維持
```

Preview成功後もFinalへ自動進行しない。

---

# 18. Rollout順序

```text
R1 Renderer実装
  ↓ CI
R1 merge
  ↓
P1 Plot実装（R1 contractを参照）
  ↓ CI / exact-day local closure
P1 merge
  ↓
I1 renderer pin更新
  ↓
8/12再materialize
  ↓
Viewer Surface validation
  ↓
Financial / Visual Source
  ↓
Visual Director catalog再生成
  ↓
Direction Plan再生成
  ↓
Protected Diff
  ↓
Renderer formal validator
  ↓
immutable handoff
  ↓
Preview
  ↓
ユーザー目視
```

---

# 19. 非目標

本設計では行わない。

- 01〜04の市場因果書き換え
- 9Scene再設計
- 新しい第二Semantic Grammar階層の導入
- 棒グラフTemplateの全面削除
- Reuters等の第三者素材を自動でrights-cleared扱い
- RendererによるPrimary/Fallback選択
- Rendererによる文章要約
- 文字が収まらない場合の自動省略
- PreviewのAI視覚採点
- PreviewからFinalへの自動遷移

---

# 20. Definition of Done

本workstreamは以下が全て満たされたときのみ完了とする。

- [ ] speechTextを変更せずcaptionTextを表示用数字へ投影できる
- [ ] viewer surfaceの数値用途漢数字をpreflightで検出できる
- [ ] 公開固定UIが `予想 / 実際 / 差分` に統一される
- [ ] qualitative Financial metricがRenderer Number objectにならない
- [ ] SourceReceiptが短文/長文とも物理衝突しない
- [ ] SourceReceipt overflowは自動縮小ではなくFAILする
- [ ] Visual DirectorがChatGPT未承認TemplateへCandidateを広げない
- [ ] 8/12 Brent/NASDAQでbars candidateが生成されない
- [ ] verified series以外で時系列グラフを捏造しない
- [ ] Visual Source Primary/Fallbackの既存境界を維持する
- [ ] episode_packageとrender_specの公開テロップが一致する
- [ ] Visual Director Protected Semantic DiffがPASSする
- [ ] Renderer formal validatorがPASSする
- [ ] exact-day closureがPASSする
- [ ] 新しい8/12 Preview MP4が生成される
- [ ] ユーザー目視確認前にFinalへ進まない

---

# 21. 実装者向け最終注意

この設計の目的は「8/12のスクリーンショットをきれいにすること」ではない。

再発防止対象は次の3つの契約欠陥である。

```text
漢数字再発
→ Viewer Surface Contractの欠陥として直す

文字衝突
→ Financial object type + Template Layout Contractの欠陥として直す

ダサい疑似グラフへの漂流
→ Visual Director Candidate Constraintの欠陥として直す
```

日次 `*_layout_text_fixes.json` を追加して症状だけ隠すこと、Renderer CSSだけで長文を押し込むこと、Candidate Builderが項目数や符号から別Templateを推測することは禁止する。

意味はChatGPTが完成させ、コードは正規化・資格判定・検証・描画だけを行う。
