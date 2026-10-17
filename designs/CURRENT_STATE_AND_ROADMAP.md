# 朝のNASDAQカフェ｜現在地と残る工程

確認日：2026-10-18（日本時間）。観測したmain：Plot `9c0b51a6ed15f51094b2c89a47a101ff2442fe83`、Renderer `536fbe8a139b2fa9f89cd9c76e9db71fa889c02e`、Collector `42908709f8044ba8d7a836d67fbe9b715f4b7790`。

運用上の案内であり、契約の正本はAGENTS、Canon Manifest、Current Entrypoints、Renderer Bindingである。以前の2026-08-05基準の「次はPR #8」という本文はGit履歴に残る。現在の着手指示として使わない。

## A. 現在状態

米国株の値動きの疑問から企業・産業・政策の仕組みをたどり、理解が変わる金融ドキュメンタリーを継続制作する。東アジアとの事業・供給網の関係は、当日価格の原因と分けて証拠を確認する。

Currentの機械工程は実装済みである。

```text
当日資料 → 現在証拠・記憶再検証 → 因果調査 → 02編集判断
→ Story / 01・03原稿 / 04審問 → Acceptance / Semantic Freeze
→ current_production_facade_v12.py → Visual Intelligence
→ RenderSpec / immutable handoff → Current Preview V4 → MP4
→ ユーザー目視確認 → 明示Final V2 → 承認後の記憶昇格
```

Director/Critic待ちのPREPARED・REVIEW_REQUIREDは正常な停止である。同じ入力のrequestを増やして解決しない。

| 項目 | 確認できた状態 | 限界 |
|---|---|---|
| Collector | 10月17日run 38986866992はsuccess | 収集内容の十分さや編集承認を意味しない |
| 因果graph | Plot #198 / Renderer #227で明示graphだけを受理する修正がmain採用済み | 独立二経路・表示順・null outcomeは機械E2Eで確認 |
| 字幕 | Renderer #224で単語・数字の分断を修正済み | 映像全体の見やすさは未承認 |
| 編集能力 | 既存Research / Story / Critic / Visual Intelligenceを強化済み | 新作の効果実測とは区別 |
| 回帰基準 | 主要Plot 99 tests・25 subtests、exact-pinned E2Eが基準mainでPASS | 合成fixtureによる契約証明 |
| 完成動画 | 2026-08-17回Final run 33533781970と保存MP4を確認 | 10月3日のコード修正を反映した新作ではない |
| 最近のRenderer success | run 39048732981は空Motion Preview queueの正常終了 | wake/render/outcomeはskipped。MP4生成実績に数えない |
| 視聴者実測 | 今回の監査ではCTR・維持率・理解度を未取得 | 改善効果を認定できない |

## B. 問題点

1. canon03は480〜540秒・旧TTSモデル、採用済みRendererは通常180〜420秒・gemini-3.8-flash-tts / Charonを要求していた。
2. Renderer lintに30 errors / 3 warningsが残り、Visual Story CIはlintを実行していなかった。
3. READMEと旧ロードマップに実装前の状態や「新しい実日previewが一度もない」という古い案内が残っていた。
4. コード・fixtureの合格と、最新コードによる制作・人間承認・視聴者反応が混同されやすかった。
5. 未採用の別案PRにはSkill責任の重複や未完成の契約移行がある。open/greenだけで採用済みとは扱えない。

## C. 根本原因

正本のバイト整合、Runtime互換性、説明文書、視聴体験を別々に検査し、同じ制作契約として照合していなかった。既に採用された因果・字幕修正をやり直す必要はない。

## D. 複数案比較

| 案 | 影響 | 判断 |
|---|---|---|
| 古い文書へRuntimeを戻す | 採用済み音声・尺・キャッシュを変更する | 不採用 |
| 検証を緩めて古い指示を通す | 契約不整合を隠す | 不採用 |
| 作者向け契約をRuntimeへそろえ、同じE2Eで照合する | 現行責任分担を保って入力側を修復する | 採用 |
| Skill追加やScene数移行を同時に導入する | 別の契約変更と責任重複を持ち込む | 別の版付き変更として評価 |

## E. 推奨案と今回の修正

`fix/project-recovery-20261018`で次を実施する。採用状態はPRのmergeとexact-head検査で確認し、ブランチ上の変更をmain反映済みと記載しない。

- canon03を2.6.0へ更新。執筆目標200〜400秒、通常180〜420秒、短縮回180秒未満、現行Charonモデルへ統一する。
- 既存exact-pinned Cross-Repo E2Eで、Canon Manifestから復元した03と実際のRendererのduration/voice設定を照合する。別の制作fixtureや政策ファイルを作らない。
- lint指摘を型・未使用束縛・正規表現表記・テストfixtureのCSS誤検出の範囲で修正し、同じRenderer CIへゼロ警告のlintを追加する。
- 現在地をこの文書とREADMEへ集約し、機械PASS、制作実績、人間承認、視聴者実測を区別する。

修正設計は[2026-10-18-project-recovery.md](../docs/reliability/plans/2026-10-18-project-recovery.md)、実行結果は[PROJECT_RECOVERY_VALIDATION_2026-10-18.md](PROJECT_RECOVERY_VALIDATION_2026-10-18.md)を参照する。

## F. 実装・運用の順番

1. 技術修復を通常PRの検査と独立レビューへ通す。
2. 当日資料から現行正本に従った新しい制作attemptを作る。歴史的episode・bundle・requestは書き換えない。
3. 唯一のCurrent facadeから進め、Director/Critic待ちでは既存requestへ意味成果物を追加する。
4. 実際のPreview MP4とtechnical reportを取得する。queueのsuccessやrequest受理だけで完了にしない。
5. ユーザーの目視確認、明示Final、公開承認を分けて記録する。
6. データが得られたら冒頭・重複・後半の発見のうち一つを対象に検証し、承認済み結果だけを記憶へ反映する。

### 責任と入出力

| 責任 | 既存の担当 | 入力 → 出力 |
|---|---|---|
| 情報収集 | Collector | 日付・明示request → 原文・市場データ・source pack |
| 編集判断 | 正本02・ChatGPT | 現在証拠・反対材料 → 主役・見る理由・仮説 |
| 過去記憶 | Editorial Memory | query plan・承認履歴 → replay可能な関連記憶 |
| 因果調査 | Causal Research | 当日証拠・許可された記憶 → dossier・証拠ID・代替仮説 |
| 構成・語り | Story Plan / Authoring / Engine・正本01/03 | 編集判断 → Scene/Beat・理解変化・完成原稿 |
| 興味・理解・Retention仮説 | 既存Entertainment Critic・正本04 | draft → Scene単位の指摘・修正要求 |
| 何を映すか | Visual Intelligence | 凍結済み意味・Registry → Candidate・Director/Critic承認 |
| 描画 | Renderer | RenderSpec・asset → 音声・production data・MP4 |
| 技術受入 | Current facade・既存Acceptance | request・証拠・出力 → 機械PASS/停止箇所 |
| 基盤診断 | Production Reliability | 実際のrun/log・契約 → 原因・修正設計・回帰結果 |
| 見た目・公開 | ユーザー | exact Preview・権利情報 → 目視確認・明示承認 |

### 別契約として残す移行

- Plot #191 / Renderer #223：semanticScope・schema 2.5。輸送だけでなくCandidate合法性とhandoff版一致まで必要。Renderer後方互換→exact qualification→Plot出力切替の順で扱う。
- 5〜12 Scene：PROGRAMME_REDESIGN_2026-09-07.mdで設計済み。本番は現在9 Scene。TTS、schema、freeze、intake、fixtureの同時移行が必要。
- Plot #194 / Renderer #220：Skill統合案。既存Skillで埋まる責任を新設する理由は未確定。既存の強化を優先する。

これらを実装済み・merge済みとは扱わない。一括mergeや、テストを通すための意味の推測は行わない。

## G. リスクと完了条件

新しい03に従うauthoringは新Canon Manifestへ結び付ける。過去のSemantic Freezeは発行時の根拠で検証し、現在のSHAへ差し替えない。lint修正だけではproduction bindingを自動更新しない。

技術修復はREDで不整合を検出し、修復後にcanon検証・主要回帰・同じexact-bound E2E・Renderer lint/typecheck/既存tests/buildが通ることを完了条件とする。番組改善は別に、新しいPreview、そのexact版のユーザー確認、取得可能な視聴者の理解・反応で判断する。未取得の実測を推測で埋めない。
