# 朝のNASDAQカフェ｜Story Engine直接取り込み判断表

- 作成日: 2026-08-06
- 対象リポジトリ: `saienjoy0/nasdaq-plot-creator-`
- 対象ブランチ: `design/story-engine-overhaul`
- 目的: 外部Story Creationプロジェクトから、直接取り込める資産、クリーンルーム再実装する資産、採用しない資産を固定する

## 1. 結論

外部プロジェクト本体は依存関係として導入しない。

採用方法は次の三分類とする。

1. `direct-vendor`
   - MIT / Apache-2.0など互換性を確認できた小さな独立資産だけ
   - 元ファイル、元commit、LICENSE、NOTICE、変更点を保存する
2. `clean-room-adaptation`
   - 設計思想、一般的な工程、評価軸だけを参考にし、NASDAQカフェ用に独自実装する
3. `reference-only`
   - ライセンス不明、強いcopyleft、目的不一致、または導入コストが高いもの

初期Story Engineでは、実コードの大量vendoringを行わない。

最も安全で保守しやすい方法は、外部実装から得た一般原則を、01〜04と既存Evidence契約へ合わせて独自のSkill、schema、validatorとして実装することだからである。

---

## 2. 採用マトリクス

| Project | Pinned commit | License確認 | 方式 | 初期採用 | 判断 |
|---|---|---|---|---|---|
| Doza Assist | `cac564e616f92436af2909e9021925d085ef3f5f` | MIT | clean-room-adaptation中心、必要なら小規模direct-vendor | Story role、Turn、重複排除、情報だけのScene拒否 | Storytelling文書は後に公開repoから削除されたため、文書丸ごとのvendoringは行わない |
| OpenMontage | `4eab34c5cfcccaa4f1970554928feccce73ee930` | AGPL-3.0 | clean-room-adaptationのみ | Angle competition、BUT/THEREFORE、Progressive Revelation、具体的Reviewer | code、schema、prompt本文をコピーしない |
| video_explainer | `c033e28d6eccae43c1762f4653f9c320b16b050e` | pinned commitでLICENSE未確認 | reference-onlyからclean-room-adaptation | Issue→Patch→Verification、gap analysis | ライセンス確認前にcode、enum、schema、文書をコピーしない |
| Toonflow | `bc61ec7a1b5df31293b286981a5f4ad4635464ee` | Apache-2.0 | clean-room-adaptation中心、独立資産はdirect-vendor可 | Decision / Execution / Supervision、Event Graph、Skill外出し | UI、provider、novel adaptationは導入しない |
| ViMax | `05a48943878312d88fe5a016c12a9654940ecc43` | MIT | clean-room-adaptation中心、独立資産はdirect-vendor可 | checkpoint、resume、artifact preview、creative-intent preservation | 画像・動画生成基盤は導入しない |
| FireRed-OpenStoryline | `c9e945215586f45c12a61c1951ee9a8e9c43a027` | Apache-2.0 | 後段候補 | 承認済み編集workflowのSkill化 | 初期Story Engineには入れない |

---

## 3. 初期実装で直接取り込むもの

### 3.1 取り込むのは「コード」より「契約の形」

初期PRで直接採用するのは次である。

- `Issue → Proposed Fix → Applied Patch → Verification`という修正記録の形
- `Decision / Execution / Supervision`という責任分離
- `checkpoint / resume`というartifactの状態管理
- `review_focus / success_criteria`をStageごとに固定する方式
- Story role vocabulary
- Angle候補を複数比較し、採用・不採用理由を記録する方式

これらはNASDAQカフェ用に独自の名称、schema、validatorで実装する。

### 3.2 直接vendoring可能だが初期には不要なもの

MIT / Apache-2.0の次のような独立helperは、必要性が出た場合だけ取り込める。

- idempotentなSkill / rule loader
- artifact checkpoint utility
- generic issue / patch serializer
- generic resume metadata helper

取り込む場合は必ず次を置く。

```text
references/external/<project>/
├── SOURCE.md
├── PINNED_COMMIT
├── LICENSE
├── NOTICE.md
└── MODIFICATIONS.md
```

直接コピーしたソースファイルにも、元project、元path、元commit、license、変更内容をheaderで残す。

---

## 4. 直接取り込まないもの

### 4.1 OpenMontageのcode / schema / prompt

AGPL-3.0のため、既存リポジトリへ部分コピーしない。

採用するのは一般的な編集原則だけとし、次は独自に書く。

- `story_discovery.schema.json`
- `narrative_arc.schema.json`
- `creative_review.schema.json`
- Story Discovery Skill
- Script Authoring Skill
- Critic Skill
- validators

### 4.2 video_explainerのcode / enum / docs本文

pinned commitでライセンスを確認できていないため、直接コピーしない。

次の一般的な発想だけを独自実装する。

```text
analyze
→ findings
→ patch plan
→ apply
→ verify
```

### 4.3 Doza Assistの削除済みStorytelling文書

過去commitでMITだったとしても、後に公開repoから削除されているため、文書丸ごとを本repoへコピーしない。

次だけをNASDAQ用に独自記述する。

- Turnのない並びはリスト
- 隣接重複は削除または統合
- 情報だけではScene採用理由にならない
- Hook / Reveal / Turn / ButtonなどのStory role
- Scene deletion test

### 4.4 外部runtime dependency

次を禁止する。

- submodule
- 外部repoを日次にcloneして読む
- 外部APIへ台本判断を委任する
- 外部Skillのlatestを自動取得する
- 外部projectの更新で日次出力が変わる構成

---

## 5. NASDAQ側で新規作成する正式資産

外部からコピーせず、次をこのリポジトリの正式資産として作る。

```text
skills/nasdaq-cafe-story-discovery/
skills/nasdaq-cafe-script-authoring/
skills/nasdaq-cafe-entertainment-critic/

contracts/story-engine/
├── story_discovery.schema.json
├── selected_story_angle.schema.json
├── narrative_arc.schema.json
├── creative_review.schema.json
├── rewrite_patch.schema.json
└── story_engine_lineage.schema.json

scripts/story-engine/
├── validate_story_discovery.py
├── validate_selected_story_angle.py
├── validate_narrative_arc.py
├── validate_creative_review.py
├── validate_causality_diff.py
└── build_story_engine_acceptance.py
```

---

## 6. Attribution policy

概念だけを参考にした場合も、採用文書へ次を残す。

- project名
- repository
- pinned commit
- 参照したfile
- license
- 採用した考え方
- NASDAQ向け変更
- 採用しなかった部分

コードまたは文書を直接コピーした場合は、license本文とcopyright noticeを同梱する。

---

## 7. License gate

新しい外部assetを直接取り込む前に、次をすべて満たす。

- pinned commitを固定した
- license fileを取得した
- コピー対象fileが同じlicense範囲にある
- repository全体のlicenseとfile固有headerが衝突しない
- NOTICE義務を確認した
- dependency追加が不要または許容可能
- 既存repoの公開・配布方式と互換性がある
- コピーではなく独自実装で十分でない理由がある

一つでも不明なら`reference-only`へ倒す。

---

## 8. 最終判断

初期Story Engineの品質は、外部コード量ではなく、次で決める。

- 2026-08-06の退屈な旧台本を正しくFAILできる
- 原因となるSceneと文を特定できる
- 修正Patchが具体的である
- 修正後もEvidence、時系列、確信度、反対材料を保持できる
- 9Sceneが九段階の理解変化になる
- Story Engineなしでは`episode_package_final`へ進めない

したがって初期実装は、外部projectの大規模vendoringではなく、ライセンス上安全なクリーンルーム実装を正式方針とする。
