# 朝のNASDAQカフェ｜調査・記憶・台本スキル作業庫

このリポジトリは、朝のNASDAQカフェの情報源正本、因果深掘りスキル、OpenClaw型の選択的長期記憶、台本制作契約を管理する作業庫です。

## 目的

毎日の`daily_source_package_YYYY-MM-DD.md`をそのまま要約するのではなく、関連背景、過去経緯、企業関係、供給網、マクロ要因、代替仮説を追加調査し、NASDAQへ届いた因果だけを9シーン台本へ変換します。

同時に、最終承認された過去回から、継続テーマ、当時の仮説、反対材料、次の検証点を記憶します。全履歴を毎回読むのではなく、今日の話題に関係する記憶だけを選択します。

## 現在地

2026-08-05時点では、次までmainで完成しています。

```text
memory query plan
→ 関連記憶検索
→ 決定的retrieval replay
→ SHA-bound research input manifest
→ 現在証拠によるmemory revalidation
→ causal research dossier v0.2
```

まだ、因果調査から最終episode package、画像採用経路、render spec、renderer previewまでを一つの制作契約として接続する工程は完成していません。

現在地、次の実装、MVPゴール、運用ゴールは次を正本とします。

- [`designs/CURRENT_STATE_AND_ROADMAP.md`](designs/CURRENT_STATE_AND_ROADMAP.md)

文書化はPR #7です。次に着手する実装は、再検証済み記憶を最終episode packageへ安全に接続するPR #8です。

## 基本フロー

```text
daily_source_package
→ memory query plan
→ selective editorial-memory retrieval
→ deterministic retrieval replay
→ research input manifest
→ causal research dossier with memory revalidation
→ 02_editorial_bible による編集判断
→ 01_fox_character_bible による狐の語り
→ 03_episode_production_spec による9シーン制作
→ 04_entertainment_inquisitor による審問・手直し
→ Primary / Approved Fallbackの最終採用
→ spoken script / asset manifest / render spec
→ 全成果物の整合validator
→ rendererへの配送
→ previewとユーザー確認
→ 明示依頼がある場合だけfinal
→ approved publication record
→ daily / weekly / thread / claim memoryへの昇格
```

## ディレクトリ

- `source-of-truth/`：番組の01〜04正本
- `editorial-memory/`：日次・週次・継続テーマ・仮説・制作知識の記憶
- `skills/nasdaq-cafe-causal-research/`：台本前段の因果深掘りスキル
- `skills/nasdaq-cafe-editorial-memory/`：関連記憶の取得と最終回からの記憶昇格
- `references/`：外部プロジェクトの採用・不採用判断
- `examples/`：検証用入力と期待出力
- `verification/`：軽量検査が成功した場合の記録
- `designs/`：実装設計、現在地、ロードマップ

## 記憶の使い方

調査前の取得は、Query Planからauthoritative retrieverを実行します。

```bash
python scripts/editorial_memory_retrieval.py \
  --query-plan working/memory_query_plan_2026-08-05.json \
  --context-output working/memory_context_2026-08-05.md \
  --report-output working/memory_retrieval_report_2026-08-05.json
```

その後、同一検索結果のreplay確認とSHA固定を行います。

```bash
python scripts/build_research_input_manifest.py \
  --episode-date 2026-08-05 \
  --market-date 2026-08-04 \
  --timezone Asia/Tokyo \
  --information-cutoff 2026-08-05T07:30:00+09:00 \
  --daily-source-package daily/daily_source_package_2026-08-05.md \
  --memory-query-plan working/memory_query_plan_2026-08-05.json \
  --memory-context working/memory_context_2026-08-05.md \
  --memory-retrieval-report working/memory_retrieval_report_2026-08-05.json \
  --output research/2026-08-05/research_input_manifest.json
```

最終承認後の昇格：

```bash
python scripts/promote_episode_memory.py \
  publication_record_2026-08-05.json
```

記憶は現在の証拠ではありません。過去の仮説を当日台本へ使う場合は、現在のtier 1 / tier 2証拠で再検証します。

## 絶対ルール

- GitHub Actions、Codex、Remotion、外部研究フレームワーク、記憶層へ市場因果や台本の意味を判断させない
- `daily_source_package`だけを言い換えて台本にしない
- 事実、共有解釈、推論、不明を分ける
- 一社の材料をNASDAQ全体の原因へ自動昇格させない
- 売買助言、目標株価、確定的な将来予測を出さない
- ドラフト、却下された因果、未採用画像経路を恒久記憶へ入れない
- 記録のない狐の保有、損益、取引、大学生活上の出来事を記憶として創作しない
- preview確認前にfinalへ進まない
- validator FAIL、未解決画像経路、対象日不一致、古いrender specをrendererへ渡さない
