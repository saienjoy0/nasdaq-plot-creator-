# 朝のNASDAQカフェ｜Visual Grammar VG-0 契約

## 1. 目的

VG-0は、完成済みの市場因果やVisual Beatについて、視聴者の理解をどのように一段進める画面かを明示するための構造契約である。

Visual Grammarは、主役ニュース、Expected / Actual / Gap、時系列、中心仮説、反対材料、確信度を決めない。これらは編集工程で確定する。

Renderer、GitHub Actions、Compilerは、Scene番号、ナレーションの単語、数値の正負、項目数などからGrammarを推測してはならない。

## 2. 責任境界

```text
Visual Grammar
= 何を理解させるか

Financial Recipe
= どの証拠構造で見せるか

Stage
= 画面空間をどう使うか

Visual Template
= Rendererが実際に描く部品
```

VG-0では、Visual GrammarとMVP Stageの互換性までを定義する。Financial RecipeおよびVisual Templateとの接続は後続PRで行う。

## 3. Grammar ID

| Grammar ID | 役割 | 標準候補Scene |
|---|---|---|
| `contradiction` | 方向・矛盾・問いを固定する | 1〜2 |
| `evidence` | 確認済み資料・事実・数字・境界を示す | 3、6 |
| `gap` | Expected / Actual / Gapを同一基準で示す | 4 |
| `causal` | 世界からNASDAQまでの経路を示す | 5〜6 |
| `reaction` | 発表時刻と価格反応を時系列で示す | 6 |
| `comparison` | 銘柄・企業・材料の反応差を比較する | 7 |
| `verification` | 仮説が強まる／弱まる条件を示す | 8 |
| `assembly` | 既出要素だけで結論を回収する | 9 |

候補Sceneは制作時の標準であり、RendererがGrammarを自動選択するルールではない。

## 4. Declaration

```json
{
  "grammarVersion": "1.0.0",
  "grammarId": "gap",
  "grammarPhase": "resolve",
  "transitionRole": "major-shift"
}
```

### grammarPhase

- `establish`: 論点または基準を置く
- `develop`: 理解を一段深める
- `resolve`: 問い、比較、経路を回収する

### transitionRole

- `continue`: 同じ理解を継続する
- `major-shift`: 画面構造を大きく切り替える
- `return`: 指定した既出Beatへ戻る
- `close`: Sceneまたはエピソードを閉じる

`return`だけが`returnTargetBeatId`を持つ。その他のTransitionでは指定を禁止する。

## 5. MVP Stage互換性

| Grammar | Stage |
|---|---|
| `contradiction` | `contradiction-stage` |
| `evidence` | `evidence-stage` |
| `gap` | `gap-stage` |
| `causal` | `causal-stage` |
| `reaction` | `reaction-stage` |
| `comparison` | `comparison-stage` |
| `verification` | `verification-stage` |
| `assembly` | `assembly-stage` |

VG-0では1 Grammarにつき1 Stageへ固定する。これはMVPの暗黙Fallbackをなくすためであり、将来のVariant追加を禁止するものではない。追加時は契約Versionを更新し、互換性表と正負テストを同時に変更する。

## 6. 明示的に禁止すること

- Scene番号からGrammarを自動決定する
- ナレーション本文のキーワードからGrammarを推測する
- 数字の正負や項目数からStageを選ぶ
- 未登録StageへGenericカードでFallbackする
- Visual Grammarで市場因果、数字、出典、留保を変更する
- `assembly`で新しい数字・証拠・因果を追加する

## 7. VG-0の成果物

- `contracts/visual_grammar.schema.json`
- `contracts/visual_grammar_registry.schema.json`
- `contracts/visual_grammar_registry.json`
- `scripts/visual_grammar_contract.py`
- 正例・負例fixture
- unit test
- GitHub Actions contract workflow

既存のFinal Episode Contract、Financial Visual Intent、Recipe Compiler、Renderer出力には変更を加えない。

## 8. 後続PR

1. VG-1: Final Episode ContractのVisual Beatへ`visualGrammar`を追加
2. VG-R1: Renderer schemaとStage registryへ接続
3. VG-R2A〜C: 8 Stageを物理的に実装
4. VG-X1: 同じ台本・数字・字幕・TTSによるA/B Preview
5. VG-4: 実日のdaily source packageで受入確認

finalレンダーはPreview目視確認後の明示依頼まで実行しない。
