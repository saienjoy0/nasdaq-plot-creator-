# 朝のNASDAQカフェ｜PR #8〜#12 実装設計書
## 4専門家協議版：Episode PackageからPreview運用まで

- 基準日: 2026-08-05
- 基準main SHA: `386aa22b03af5664f418e70d1bd37ec90cef3a40`
- 対象リポジトリ: `saienjoy0/nasdaq-plot-creator-`
- 実装開始ブランチ: `feat/pr8-episode-package-memory-references`
- 現在地: PR #7まで完了。調査・記憶基盤から制作パッケージ統合へ移る
- 最初の実装対象: **PR #8｜Episode Package Memory Reference**
- MVP到達PR: **PR #11｜Real-Day End-to-End Acceptance**
- 日次運用固定PR: **PR #12｜Daily Operational Entry Point**

---

## 1. 4人の専門家

この設計は、次の4役で検討した結果を一つに統合したものとする。

### 専門家A｜編集因果・証拠責任者

担当:

- `02_editorial_bible`の市場因果
- Expected / Actual / Gap
- 主役銘柄とNASDAQ全体の因果範囲
- 反対材料と確信度
- 現在証拠と過去記憶の分離

最重要要求:

> 過去回の記憶を台本へ使ったという事実だけでは、現在の因果を強めてはいけない。

### 専門家B｜狐・9シーン制作契約責任者

担当:

- `01_fox_character_bible`
- `03_episode_production_spec`
- Scene 1〜9
- 狐一人の語り
- 接続文、Visual Beat、テロップ、画面意図
- 人間向け編集正本としてのepisode package

最重要要求:

> memory metadataを視聴者向け文面へ露出させず、どのSceneのどの文章で過去記憶を使ったかだけは追跡可能にする。

### 専門家C｜契約・provenance・validator責任者

担当:

- PR #5〜#6のretrieval / replay / manifest / dossier
- SHA-256
- schema
- cross-file consistency
- deterministic parser
- 不正入力拒否

最重要要求:

> 自己申告のstatusやvalidation結果を信用せず、PR #6の検証鎖を再実行してからepisode packageを認証する。

### 専門家D｜審問・攻撃的QA・運用責任者

担当:

- `04_entertainment_inquisitor`
- タイトル・サムネイルの誇張防止
- 審問後の最終版のみを正本化
- adversarial test
- renderer配送
- preview / final / publication / memory promotionのゲート

最重要要求:

> 正常系だけでなく、status改ざん、Scene差し替え、古いdossier、未登録過去言及、marker漏れ、stale render specを必ず拒否する。

---

## 2. 4人の全員一致事項

### 決定1｜episode packageを人間向け編集正本のまま維持する

`episode_package_YYYY-MM-DD.md`を捨ててJSONを編集正本にしない。

理由:

- 03がepisode packageを人間が確認する編集正本と定義している
- 04の審問結果を同一ファイルへ統合する
- 市場因果、狐の演技意図、画面意図、反対材料を人間が読める必要がある

ただし、機械検査用の厳密なannexをepisode package末尾へ追加する。

### 決定2｜memory利用は「機械可読annex＋不可視marker」で追跡する

文章の意味をregexやLLMで推測して監査しない。

採用方式:

1. episode package末尾に厳密なJSON annexを1件だけ置く
2. 過去記憶を使った文章の直後にHTML comment markerを置く
3. markerはspoken scriptとrender specへ出力しない
4. validatorがannexとmarkerを双方向照合する

例:

```markdown
前回はAI投資の回収速度が評価軸として残りました。<!--MEMREF:MR-001:U-001-->
```

視聴者向けMarkdown表示ではcommentは見えず、制作側では正確な利用位置を特定できる。

### 決定3｜PR #8 validatorはPR #6 validatorを再実行する

次の自己申告だけでは合格させない。

- dossierの`validation.status=pass`
- episode packageの「確認済み」
- annexのstatus
- 手書きされたEvidence ID

PR #8 validatorは、dossierが参照するmanifestとretrieval reportを読み、PR #6の`validate_dossier()`を再実行する。

### 決定4｜過去記憶のstatusごとに公開用途を固定する

同じmemoryでも、statusによって使い方が変わる。

- supported
- partially_supported
- weakened
- invalidated
- unresolved
- historical_context_only
- not_used

を同じ強さで台本へ入れてはいけない。

### 決定5｜タイトル・サムネイルは最も厳しく制限する

タイトル・サムネイルは本文より強い印象を作りやすい。

そのため:

- `weakened`
- `invalidated`
- `unresolved`
- `historical_context_only`

を現在の主張としてタイトル・サムネイルへ使用しない。

`partially_supported`も原則禁止し、PR #8では安全側へ倒す。

### 決定6｜PR #9まではrender specを変更しない

PR #8はmemory利用監査だけを実装する。

次を同時に実装しない。

- spoken script生成
- asset manifest生成
- render spec生成
- renderer配送
- GitHub Actions変更

一つのPRへ多く詰めると、memory利用違反とrender不整合の原因を分離できないため。

### 決定7｜PR #11で初めてMVP完成と判定する

schemaやunit testだけではMVP完成ではない。

新しい実日の一件を使い、

```text
daily source
→ causal dossier
→ final episode package
→ image path resolution
→ production bundle
→ renderer handoff
→ preview MP4
```

まで通し、ユーザーが目視可能になった時点をMVPとする。

---

# Part I｜PR #8 詳細設計
## Episode Package Memory Reference

---

## 3. PR #8の目的

validated causal research dossierに存在する再検証済みmemoryだけを、最終episode packageの特定箇所へ安全に接続する。

PR #8が答える問い:

- どの過去記憶を使ったか
- その記憶は現在どう再検証されたか
- どのEvidence IDで支えられているか
- どのScene・文面・画面で使ったか
- 現在事実、過去比較、訂正、反対材料、監視点のどれか
- タイトル・サムネイル・概要欄へ使ってよいか

PR #8が答えない問い:

- 今日の主役は何か
- 市場因果は何か
- どんなナレーションを書くか
- どの画像を生成するか
- render specをどう構築するか

これらはChatGPTが01〜04に従って決める。

---

## 4. PR #8の入力

必須:

```text
episode_package_YYYY-MM-DD.md
research/YYYY-MM-DD/causal_research_dossier_YYYY-MM-DD.json
research/YYYY-MM-DD/research_input_manifest.json
working/memory_retrieval_report_YYYY-MM-DD.json
```

間接的に必要:

```text
working/memory_query_plan_YYYY-MM-DD.json
working/memory_context_YYYY-MM-DD.md
daily_source_package_YYYY-MM-DD.md
```

PR #8 validatorはdossierからmanifestへたどり、manifestからreportとQuery Planへたどる。

---

## 5. PR #8の成果物

新規候補:

```text
skills/nasdaq-cafe-episode-package-memory/
├── SKILL.md
├── contracts/
│   └── episode_package_memory_annex.schema.json
├── parsers/
│   └── episode_package_memory_parser.py
└── validators/
    └── validate_episode_package_memory.py

tests/episode-package-memory/
├── fixtures/
└── test_episode_package_memory.py

.github/workflows/episode-package-memory.yml

designs/PR8_TO_PR12_IMPLEMENTATION_BLUEPRINT.md
```

01〜04正本は変更しない。

---

## 6. episode packageへ追加する正式section

episode packageの末尾、04審問結果の後に次を置く。

````markdown
## I. Editorial Memory Usage Annex

<!--BEGIN_EPISODE_MEMORY_ANNEX-->
```json
{
  "contract_version": "1.0.0",
  "episode_date": "2026-08-06",
  "causal_dossier": {
    "path": "research/2026-08-06/causal_research_dossier_2026-08-06.json",
    "sha256": "..."
  },
  "references": []
}
```
<!--END_EPISODE_MEMORY_ANNEX-->
````

規則:

- annexはexactly one
- begin / end markerはexactly one
- JSON fenceはexactly one
- JSONは手動で複数箇所へ分散しない
- annex markerはspoken scriptへ出さない
- annexは視聴者向け画面へ表示しない
- memoryを使わない回も`references: []`でPASSできる

---

## 7. Annex top-level schema

```json
{
  "contract_version": "1.0.0",
  "episode_date": "2026-08-06",
  "causal_dossier": {
    "path": "research/2026-08-06/causal_research_dossier_2026-08-06.json",
    "sha256": "64hex"
  },
  "references": [],
  "validation_intent": {
    "past_mentions_complete": true,
    "title_thumbnail_checked": true
  }
}
```

### 必須ルール

- `episode_date`はepisode package対象日およびdossier対象日と一致
- dossier pathはrepo相対
- dossier path traversal禁止
- SHA一致
- `references`の`reference_id`は一意
- `usage_id`はepisode内で一意
- memoryを使わない場合は空配列を明示

---

## 8. Memory Reference schema

```json
{
  "reference_id": "MR-001",
  "memory_reference_type": "claim",
  "memory_reference_id": "ai-capex-evaluation-axis",
  "historical_confidence": "medium",
  "current_revalidation_status": "supported",
  "dossier_editorial_use": "research_lead",
  "dossier_current_evidence_ids": ["E-001", "E-004"],
  "difference_from_previous": "当日は別企業の公式売上データでも回収論点を再確認した。",
  "public_usage_mode": "historical_comparison",
  "scope_limit": "",
  "usages": []
}
```

### `memory_reference_type`

```text
thread
claim
episode
lesson
daily
weekly
```

### `current_revalidation_status`

dossierと同一:

```text
supported
partially_supported
weakened
invalidated
unresolved
historical_context_only
not_used
```

### `public_usage_mode`

```text
current_supported_context
historical_comparison
change_from_previous
counterevidence
correction
monitoring_point
internal_only
```

### `scope_limit`

- `partially_supported`では必須
- どこまで支持され、どこから未確認かを書く
- `supported`でも対象企業や期間が異なる場合は記載
- 視聴者向けナレーションへ必要な留保を反映する

---

## 9. Usage schema

```json
{
  "usage_id": "U-001",
  "surface": "scene_narration",
  "scene_id": "SCENE-04",
  "anchor_text": "前回はAI投資の回収速度が評価軸として残りました。",
  "marker": "<!--MEMREF:MR-001:U-001-->",
  "claim_mode": "historical",
  "evidence_ids": ["E-001"],
  "requires_source_attribution": false,
  "wording_strength": "qualified",
  "title_thumbnail_permission": "not_applicable"
}
```

### `surface`

```text
scene_narration
scene_connection
main_telop
support_telop
visual_text
title
thumbnail
description
```

### `scene_id`

- Scene surfaceでは`SCENE-01`〜`SCENE-09`
- title / thumbnail / descriptionでは`null`

### `claim_mode`

```text
current_fact
current_reported_interpretation
current_grounded_inference
historical
change
correction
counterevidence
monitoring
```

### `wording_strength`

```text
direct
qualified
historical
corrective
uncertain
```

### `anchor_text`

- episode package内の完全一致文字列
- 該当surface内でexactly one
- 空文字禁止
- 省略記号で特定しない
- Scene全体を丸ごと入れず、利用文またはテロップを入れる

---

## 10. 不可視marker契約

使用文の直後へ次を置く。

```text
<!--MEMREF:MR-001:U-001-->
```

必須:

- annexのreference IDとusage IDに一致
- 同一markerはexactly one
- markerの直前にanchor textがある
- usage surfaceと実際のsectionが一致
- markerはspoken script、字幕、テロップ公開文字列へ入れない
- render specへmarkerを渡さない

Validatorは次を双方向に検査する。

```text
annex usage → markerがある
marker → annex usageがある
```

未登録markerも未marked usageもFAIL。

---

## 11. Statusと利用可能範囲

### 11.1 許可表

| dossier status | 許可public_usage_mode | 現在事実として利用 | 過去比較 | タイトル・サムネイル |
|---|---|---:|---:|---:|
| supported | current_supported_context / historical_comparison / monitoring_point | 可 | 可 | 条件付き可 |
| partially_supported | historical_comparison / change_from_previous / monitoring_point | 原則不可 | 可 | 不可 |
| weakened | change_from_previous / counterevidence / monitoring_point | 不可 | 可 | 不可 |
| invalidated | correction / counterevidence | 不可 | 訂正時のみ可 | 不可 |
| unresolved | monitoring_point / internal_only | 不可 | 留保付きのみ | 不可 |
| historical_context_only | historical_comparison / internal_only | 不可 | 可 | 不可 |
| not_used | internal_onlyのみ | 不可 | 不可 | 不可 |

### 11.2 supported

`current_supported_context`には次が必要。

- dossier statusがsupported
- current tier 1 / tier 2 Evidence IDが1件以上
- usage evidenceがdossier entryのcurrent evidence subset
- anchor wordingがEvidenceの範囲を超えない
- dossierの対象企業・期間と異なる場合はscope limit

### 11.3 partially_supported

PR #8では安全側へ倒し、現在事実の断定へ使用しない。

許可:

- 「前回の見方の一部は残っています」
- 「ただし今回は対象企業が異なります」
- 「回収論点は確認できましたが、NASDAQ全体への波及は未確認です」

必須:

- `scope_limit`
- qualified wording
- title / thumbnail使用禁止

### 11.4 weakened

許可:

- 過去仮説が弱まった説明
- 反対材料
- 次回検証点

禁止:

- 過去仮説を現在の中心因果の根拠にする
- 「やはり前回の通り」と使う
- タイトル・サムネイルの断定

### 11.5 invalidated

許可:

- 明示的訂正
- 反対材料
- 「以前の見方は現在の証拠では維持できない」

必須:

- corrective wording
- current contrary evidence
- 何が誤りまたは不成立だったか

禁止:

- 過去仮説の再利用
- 曖昧な「見方が変わりました」だけで済ませる
- タイトル・サムネイルによる過去主張の再掲

### 11.6 unresolved

許可:

- Scene 8の監視点
- internal only

禁止:

- Scene 1の結論
- Scene 4のExpectedの根拠
- Scene 6の価格因果
- title / thumbnail

### 11.7 historical_context_only

許可:

- 過去比較
- 背景説明

禁止:

- Actual
- current causal edge
- NASDAQ全体の主因
- 現在形の大テロップ

### 11.8 not_used

episode package公開面へ一切出さない。

Annexへ含める必要もない。
含める場合は`internal_only`かつ`usages: []`に限定する。

---

## 12. 狐の人物記憶との境界

01に基づき、次の具体的過去は、対応する正式memory recordがない限り使用禁止。

- 履修登録の失敗
- グループワークの揉め事
- 香港で乗り換えを間違えた経験
- 特定の買い物で損をした経験
- 料理・生活上の具体的失敗
- 投資成功・失敗
- 保有銘柄、損益、取得価格、取引履歴

PR #8では市場editorial memoryだけでなく、`fox_personal_memory`の将来拡張を予約するが実装しない。

当面は:

- 具体的な狐の過去を検出した場合、専用記録契約がないためFAILまたは人間確認
- 一般的なたとえ「履修登録のように」はmemory reference不要
- 「僕も履修登録で失敗した」は正式記録なしでは禁止

---

## 13. Scene別利用ルール

### Scene 1

- 過去記憶を主結論の代わりに使わない
- supportedであっても「前回の続き」だけをhookにしない
- 視聴理由は当日の方向・矛盾・問いで作る

### Scene 2

- historical comparisonは可
- 前回の説明を繰り返してScene進展を止めない

### Scene 3

- Actualはcurrent evidenceのみ
- historical contextは補助に限定

### Scene 4

- Expectedの根拠にmemoryを使わない
- 前回の評価軸を比較する場合もExpected sourceとは分離

### Scene 5

- 供給網や背景の継続性にmemoryを使う場合、現在の関係が継続している証拠を確認
- historical-onlyを現在の供給関係として見せない

### Scene 6

- 値動き因果にmemoryを使わない
- 発表時刻、価格反応、現在Evidenceを優先
- past memoryは反対材料または比較のみ

### Scene 7

- 銘柄差の説明を過去の「選別」物語で自動補完しない
- 当前Evidenceがない場合はunresolved

### Scene 8

- unresolved / weakened memoryの監視点利用を許可
- strengthen / weakenの両条件を残す

### Scene 9

- 新しいmemory claimを導入しない
- 当日の結論を短く閉じる

---

## 14. タイトル・サムネイル・概要欄

### タイトル

許可条件:

- supported
- title usageがannexへ登録
- 本編で回収
- 現在Evidenceあり
- 本文より強くない

禁止:

- 「前回予測が的中」
- 「また同じことが起きた」
- weakened / unresolvedを確定表現
- 記憶だけでNASDAQ全体へ拡大

### サムネイル

supportedでも原則として記憶の存在を主役にしない。

使用する場合:

- 当日の矛盾が中心
- memoryは比較補助
- 本文の結論より強くしない

### 概要欄

訂正や過去回参照を置く場合もannexへusage登録する。

公開後訂正はPR #8対象外だが、PR #12のpublication workflowへ接続する。

---

## 15. PR #8 validator処理順

```text
1. repo rootと入力path検証
2. episode package読み込み
3. annex marker抽出
4. JSON schema検証
5. dossier path / SHA検証
6. PR #6 dossier validator再実行
7. episode date一致
8. dossier memory revalidation index作成
9. annex referenceとdossier entry完全照合
10. status / public usage matrix検証
11. Evidence ID subset・品質検証
12. anchor text位置検証
13. marker双方向検証
14. Scene / surface位置検証
15. title / thumbnail禁止条件検証
16. 未登録marker検査
17. production metadata公開漏れ検査
18. validation report出力
```

---

## 16. 完全照合するfield

Annexとdossierで次を一致させる。

```text
memory_reference_type
memory_reference_id
historical_confidence
current_revalidation_status
dossier_editorial_use
dossier_current_evidence_ids
difference_from_previous
```

`difference_from_previous`は文字列完全一致を原則とする。

episode package側で読みやすく要約したい場合は別field:

```text
public_difference_summary
```

をusageへ置く。

元のdifferenceを勝手に書き換えない。

---

## 17. Validator ERROR条件

最低限次をERRORにする。

1. annexがない、または複数
2. JSON解析失敗
3. schema不一致
4. dossier path / SHA不一致
5. repo外path
6. dossier validator FAIL
7. episode date不一致
8. dossierにないmemory reference
9. status改ざん
10. historical confidence改ざん
11. Evidence ID改ざん
12. dossier editorial use改ざん
13. difference改ざん
14. duplicate reference ID
15. duplicate usage ID
16. markerなしusage
17. annexなしmarker
18. anchor textがない
19. anchor textが複数箇所
20. Scene ID不一致
21. surface不一致
22. supported以外をcurrent supported contextへ使用
23. partially supportedを直接断定
24. weakenedを肯定材料へ使用
25. invalidatedを現在前提へ使用
26. unresolvedを現在事実へ使用
27. historical onlyをActual / causal claimへ使用
28. not usedを公開面へ使用
29. title / thumbnail禁止status
30. current usageなのにEvidenceなし
31. Evidenceがdossier entryのsubsetでない
32. memory pathをE-###として使用
33. markerがspoken public textとして記述される計画
34. Scene 4 Expected sourceをmemoryへ置換
35. Scene 6 timeline根拠をmemoryへ置換
36. タイトル・サムネイルが本文より強い利用mode
37. 具体的な狐の過去を正式記録なしで使用

---

## 18. WARNING条件

- supportedだがtier 2のみ
- scope limitが必要と推定されるが短い
- historical comparisonが複数Sceneへ重複
- 同じmemoryが3箇所以上で使われる
- titleまたはthumbnailにmemory usageがある
- Scene 1〜2で過去説明が長い
- Scene 8以外でunresolved monitoringを使用
- anchor textが長すぎる
- public difference summaryがdossier differenceより強い

WARNINGは自動合格を妨げないが、04審問時の確認項目に渡す。

---

## 19. テスト計画

### 正常系

1. memory不使用回
2. supportedをScene 4の過去比較で使用
3. supportedをcurrent contextで使用
4. partially supportedを留保付き比較
5. weakenedをScene 7の反対材料
6. invalidatedを明示訂正
7. unresolvedをScene 8 monitoring
8. historical onlyをScene 2背景
9. descriptionで過去回を適切に参照
10. 複数memoryを別Sceneで使用

### 拒否系

11. dossierにないmemory ID
12. status改ざん
13. Evidence ID追加
14. Evidence ID欠落
15. difference改ざん
16. marker欠落
17. orphan marker
18. duplicate marker
19. duplicate anchor
20. wrong Scene
21. wrong surface
22. partially supportedを現在断定
23. weakenedを中心仮説の根拠
24. invalidatedを大テロップで肯定
25. unresolvedをタイトル
26. historical onlyをActual
27. not usedをナレーション
28. Scene 4 Expectedをmemoryだけで説明
29. Scene 6価格因果をmemoryだけで説明
30. stale dossier SHA
31. dossier date mismatch
32. repo外path
33. PR #6 validator FAILのdossier
34. annexが2個
35. malformed JSON
36. markerを公開テロップ文字列へ混入
37. 記録のない狐の具体的失敗談
38. title / thumbnail overclaim
39. memory referenceを使ったが04審問前のpackage
40. same memoryを不整合な2 statusで重複

最低40件を目標とする。

---

## 20. PR #8 CI

workflow候補:

```text
.github/workflows/episode-package-memory.yml
```

実行:

1. Python compile
2. schema syntax
3. PR #6 bridge tests
4. PR #8 unit tests
5. real AWS seed dossier fixture
6. memory不使用episode fixture
7. adversarial fixtures
8. 01〜04 materialization/hash check
9. existing memory contract
10. existing promotion / retrieval regression

PR #8はPR #6を壊してはいけない。

---

## 21. PR #8の実装順

### Commit 1｜設計

- この文書
- 変更対象の確定
- schema draft

### Commit 2｜Parser

- annex extractor
- marker parser
- section / Scene locator
- deterministic error paths

### Commit 3｜Schema

- annex schema
- reference / usage schema
- status-use enum

### Commit 4｜Validator core

- dossier replay
- SHA
- field equality
- Evidence subset
- usage matrix

### Commit 5｜Marker / Scene validation

- exact anchor
- exact marker
- Scene / surface

### Commit 6｜Tests

- 40件以上
- real seed
- memory-free case

### Commit 7｜CI / docs

- permanent workflow
- SKILL
- AGENTS最小更新
- roadmap進捗更新

一度に全ファイルを巨大commitへ入れない。

---

## 22. PR #8完了条件

- memory不使用回がPASS
- dossierにないmemoryを使用できない
- statusを弱めたり強めたり改ざんできない
- current Evidence IDを勝手に変更できない
- usage位置をScene単位で追跡できる
- historical onlyを現在事実にできない
- weakened / invalidatedを肯定材料にできない
- unresolvedをタイトルにできない
- markerが公開成果物へ漏れない契約がある
- 01〜04を変更していない
- rendererを変更していない
- 全既存CIがPASS

---

# Part II｜PR #9 詳細設計
## Final Production Package Contract

---

## 23. PR #9の目的

04審問と画像採用経路確定後のepisode packageを唯一の編集正本とし、同じ完成内容から機械的に次を生成・検証する。

```text
spoken_script_YYYY-MM-DD.md
asset_manifest.json
render-specs/YYYY-MM-DD/render_spec.json
official_execution_preflight.json
```

---

## 24. PR #9の中心設計

episode packageを直接何度もregex parsingして各成果物を別々に作らない。

採用経路:

```text
final episode package
→ deterministic episode_package_ir.json
→ spoken script
→ asset manifest
→ render spec
→ consistency report
```

`episode_package_ir.json`は手動編集しない派生成物。

episode packageが人間向け編集正本であり続ける。

---

## 25. episode package IR

候補:

```text
working/YYYY-MM-DD/episode_package_ir.json
```

含む:

- episode metadata
- causal spine
- Expected / Actual / Gap
- Scene 1〜9
- narration
- connection lines
- expressions
- visual beats
- telops
- numbers
- evidence
- memory references
- asset IDs
- Primary / Fallback
- selected path
- 04 result
- title / thumbnail / description

IRにない情報を下流成果物へ追加しない。

---

## 26. PR #9のgenerator

候補:

```text
scripts/build_episode_package_ir.py
scripts/generate_spoken_script.py
scripts/generate_asset_manifest.py
scripts/generate_render_spec.py
scripts/validate_final_production_package.py
```

原則:

- pure deterministic transform
- LLMなし
- renderer component推測なし
- missing fieldは停止
- fallback推測なし
- narration言い換えなし

---

## 27. PR #9整合検査

次を一致させる。

```text
Scene順
ナレーション
接続文
表情
表情切替
Visual Beat
画面状態
テロップ
数字
Evidence
memory usage
asset ID
開始・終了合図
復帰先
selected_path
```

特にmemory markerとannexはspoken script / render specから除去し、意味だけ維持する。

---

## 28. PR #9停止条件

- 04審問が合格・条件付き合格後の反映済みでない
- 必須修正未反映
- Primary / Fallback未確定
- selected_path複数
- unsupported asset status
- Scene不足
- narration marker漏出
- episode packageとIR不一致
- IRとrender spec不一致
- memory usage status不一致

---

## 29. PR #9完了条件

- final episode packageから全成果物を再生成可能
- MarkdownとJSONを別々に手編集しない
- rerunがbyte-identical
- fallback切替後に全成果物が同じpathへ揃う
- memory markersが公開面へ出ない
- official consistency validator PASS

---

# Part III｜PR #10 詳細設計
## Renderer Handoff Bundle

---

## 30. PR #10の目的

validator済み成果物だけをrendererへ配送し、対象日・契約版・SHA・配送先を固定する。

---

## 31. handoff manifest

```json
{
  "contract_version": "1.0.0",
  "episode_date": "2026-08-06",
  "mode": "preview",
  "plot_creator": {
    "repository": "saienjoy0/nasdaq-plot-creator-",
    "commit": "..."
  },
  "renderer": {
    "repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion",
    "expected_contract_version": "...",
    "expected_base_commit": "..."
  },
  "files": [],
  "validation": {
    "production_package": "pass",
    "unresolved_states": 0
  },
  "final_authorized": false
}
```

### 必須file fields

```text
role
source_path
destination_path
sha256
size
required
```

---

## 32. 配送ルール

- Actions入力はrender specと参照アセット
- ZIPは保存用であり実行入力にしない
- renderer commit / schema versionを固定
- target date一致
- stale render spec拒否
- unresolved state 0
- preview mode固定
- final authorized false
- 同一bundleの再配送はidempotent
- 内容変更があれば新bundle hash

---

## 33. 受信側ルール

rendererは:

- manifest SHAを検査
- destination pathを検査
- asset存在を検査
- contract versionを検査
- previewだけ実行
- 市場因果や文面を変更しない
- missingを推測補完しない
- finalへ自動昇格しない

---

## 34. PR #10完了条件

- 正しいbundleのみ配送可能
- 古い日付を拒否
- 古いrender specを拒否
- path traversal拒否
- asset hash mismatch拒否
- preview / final混同なし
- renderer側で意味変更なし

---

# Part IV｜PR #11 詳細設計
## Real-Day End-to-End Acceptance

---

## 35. PR #11の目的

新しい実日の当日資料を一件使い、previewまでの全経路を証明する。

このPRで初めてMVP完成判定を行う。

---

## 36. 実日選定条件

- 2026-07-31 seedを再利用しない
- daily source packageが実在
- 一次情報と市場データが確認可能
- Expected / Actual / Gapまたは明示的reason-unknownを扱える
- memoryが関連する場合としない場合のどちらでもよい
- 画像が必要ならPrimary / Fallbackを事前完成
- previewをユーザーが目視できる

---

## 37. Acceptance経路

```text
daily source
→ query plan
→ retrieval
→ replay
→ research input manifest
→ causal dossier
→ memory revalidation
→ episode package
→ memory annex
→ 04 inquisition
→ final episode package
→ image path resolution
→ IR
→ spoken script
→ asset manifest
→ render spec
→ final package validator
→ handoff manifest
→ renderer
→ preview MP4
→ user visual review
```

finalは実行しない。

---

## 38. Acceptance記録

候補:

```text
verification/real-day-acceptance/YYYY-MM-DD/
├── acceptance_report.md
├── input_hashes.json
├── validator_results.json
├── handoff_result.json
├── renderer_technical_report.json
└── user_review_status.json
```

記録:

- 使用commit
- 対象日
- 全SHA
- validator結果
- unresolved
- image path
- preview artifact
- user review pending / approved / rejected
- final not run

---

## 39. PR #11 MVP合格条件

- 一件の新実日でpreview生成成功
- narration / telop / asset / sceneが一致
- memory利用が正しい
- Primary / Fallbackが一つ
- rendererが意味を変更していない
- technical checks pass
- ユーザーがpreviewへアクセス可能
- finalは未実行

---

# Part V｜PR #12 詳細設計
## Daily Operational Entry Point

---

## 40. PR #12の目的

日次制作の機械工程を一つの安全な入口にまとめる。

これは編集AIではない。

---

## 41. 日次state machine

```text
intake_ready
research_inputs_bound
causal_dossier_valid
episode_package_final
memory_usage_valid
assets_resolved
production_package_valid
handoff_ready
preview_dispatched
preview_ready
user_review_pending
user_preview_approved
final_requested
final_completed
publication_approved
memory_promoted
```

各stateは前stateの証拠hashを持つ。

---

## 42. CLI候補

```bash
python scripts/run_daily_production.py \
  --episode-date YYYY-MM-DD \
  --daily-source-package PATH \
  --mode preview
```

このCLIが行うこと:

- 必須ファイル検出
- 対象日確認
- validator順序制御
- bundle作成
- handoff
- preview workflow dispatch
- status report

このCLIが行わないこと:

- 主役選定
- 因果決定
- ナレーション作成
- 04審問
- 画像生成
- Primary / Fallback選択
- final自動実行

---

## 43. Failure codes

```text
E_DATE_MISMATCH
E_STALE_INPUT
E_RESEARCH_INVALID
E_MEMORY_USAGE_INVALID
E_EPISODE_NOT_FINAL
E_INQUISITION_UNRESOLVED
E_ASSET_UNRESOLVED
E_SELECTED_PATH_UNRESOLVED
E_RENDER_SPEC_INVALID
E_PACKAGE_MISMATCH
E_HANDOFF_INVALID
E_RENDERER_CONTRACT_MISMATCH
E_PREVIEW_FAILED
E_FINAL_NOT_AUTHORIZED
E_PUBLICATION_NOT_APPROVED
E_MEMORY_PROMOTION_BLOCKED
```

停止時は、正確なJSON path、Markdown section、対象fileを表示する。

---

## 44. Idempotency

同一入力hashと同一stateでは:

- 同じbundleを再利用
- TTSを不要に再生成しない
- previewを重複dispatchしない
- memory promotionを重複適用しない

内容変更時は:

- 下流stateをinvalidate
- episode package変更なら04再審問
- render specだけの意味変更は禁止
- image path変更ならspoken / asset / renderを再生成

---

## 45. Final gate

finalへ進む条件:

```text
preview_ready
AND user_preview_approved
AND explicit final request
AND current bundle hash unchanged
```

一つでも欠ければ停止。

---

## 46. Publication / memory promotion gate

memory promotion条件:

```text
publication record approved
AND preview approved
AND final status recorded
AND no rejected causality
AND no unused image path
AND final episode package hash pinned
```

---

# Part VI｜PR間の依存関係

---

## 47. 固定順序

```text
PR #8
Episode Package Memory Reference
↓
PR #9
Final Production Package Contract
↓
PR #10
Renderer Handoff Bundle
↓
PR #11
Real-Day End-to-End Acceptance
↓
PR #12
Daily Operational Entry Point
```

順番を入れ替えない。

### PR #8より前にPR #9をしない理由

memory利用を追跡できないままIR / render specへ落とすと、過去主張の誤用が下流へ固定される。

### PR #9より前にPR #10をしない理由

episode packageとrender specの正本関係が閉じていないまま配送契約を作ると、不整合なbundleを正しく配送してしまう。

### PR #10より前にPR #11をしない理由

手作業のコピーでpreviewが出ても、再現可能なhandoffを証明できない。

### PR #11より前にPR #12をしない理由

実日で通っていない工程を自動化すると、失敗を高速化するだけになる。

---

# Part VII｜リスクと対策

---

## 48. Markdown parserの脆弱性

対策:

- exact section headings
- exact begin / end marker
- JSON annex
- anchor exact match
- line / section diagnostics
- Markdown全体の意味解析をしない

## 49. Marker漏出

対策:

- PR #9 generatorでHTML commentを除去
- spoken scriptに`MEMREF`があればFAIL
- render spec public textに`MEMREF`があればFAIL

## 50. 記憶の誤った現在化

対策:

- PR #6 validator replay
- status-use matrix
- current Evidence subset
- Scene 4 / 6特別検査
- title / thumbnail厳格制限

## 51. 04審問によるmemory意味変更

04は因果や根拠を変更できない。

対策:

- 審問前後でannex reference fieldsを比較
- 変更可能なのはanchor位置や読みやすい表現
- status / Evidence / difference変更は02へ差し戻し
- 必須修正後にPR #8 validatorを再実行

## 52. PR肥大化

対策:

- PR #8はmemory usageだけ
- PR #9はproduction source consistency
- PR #10はhandoffだけ
- PR #11はacceptanceだけ
- PR #12はorchestrationだけ

## 53. 過剰な自動化

対策:

- codeは検証・変換・配送のみ
- ChatGPTが編集判断
- rendererは実行のみ
- userがpreview / final / publicationを承認

---

# Part VIII｜4人の最終合意

---

## 54. 専門家Aの結論

PR #8は、過去記憶を追加情報として便利に使う機能ではなく、過去記憶が現在の市場因果へ不正昇格しないための編集安全装置として実装する。

## 55. 専門家Bの結論

episode packageを編集正本として維持し、memory metadataは不可視markerと末尾annexへ隔離する。狐の語りや画面へ制作情報を出さない。

## 56. 専門家Cの結論

annexを信用せず、PR #6のdossier validation chainを再実行し、SHA、status、Evidence、利用位置を完全照合する。

## 57. 専門家Dの結論

PR #8を40件以上の正常系・攻撃的テストで固め、PR #9〜#12を順番通りに進める。MVPはunit testではなく、実日のpreview成功で判定する。

---

# 58. 次のAIへの直接指示

次に実装するのはPR #8である。

```text
branch:
feat/pr8-episode-package-memory-references
```

最初に行うこと:

1. この設計書を読む
2. `AGENTS.md`を読む
3. 01〜04を読む
4. PR #6 validatorとschemaを読む
5. episode package annex schemaを実装
6. parserを実装
7. PR #6 replayを組み込む
8. status-use matrixを実装
9. marker / anchor / Scene validationを実装
10. 40件以上のtestsを追加
11. existing CIを回帰確認
12. レビュー後にのみReadyへする

禁止:

- 01〜04の変更
- 自動台本生成
- LLMによるvalidator
- regexだけで過去言及の意味を推測
- render spec変更
- renderer変更
- PR #9〜#12の先取り実装
- preview前のfinal
- publication承認前のmemory promotion

---

# 59. 最終ゴール

```text
当日資料
→ 現在証拠と記憶再検証
→ 編集判断済みepisode package
→ memory利用監査
→ 04審問後の最終正本
→ 全成果物の決定的生成
→ validator PASS
→ renderer handoff
→ preview
→ user review
→ explicit final
→ publication approval
→ approved memory promotion
```

この一周を、意味を変えず、安全に、再現可能に、毎日繰り返せる状態を完成とする。
