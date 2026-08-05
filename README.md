# 朝のNASDAQカフェ｜調査・記憶・台本スキル作業庫

このリポジトリは、朝のNASDAQカフェの情報源正本、因果深掘りスキル、OpenClaw型の選択的長期記憶、台本制作契約を管理する作業庫です。

## 目的

毎日の`daily_source_package_YYYY-MM-DD.md`をそのまま要約するのではなく、関連背景、過去経緯、企業関係、供給網、マクロ要因、代替仮説を追加調査し、NASDAQへ届いた因果だけを9シーン台本へ変換します。

同時に、最終承認された過去回から、継続テーマ、当時の仮説、反対材料、次の検証点を記憶します。全履歴を毎回読むのではなく、今日の話題に関係する記憶だけを選択します。

## 基本フロー

```text
daily_source_package
→ relevant editorial memory
→ causal_research_dossier
→ 02_editorial_bible による編集判断
→ 01_fox_character_bible による狐の語り
→ 03_episode_production_spec による9シーン制作
→ 04_entertainment_inquisitor による審問・手直し
→ render_spec.json
→ previewとユーザー確認
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

## 記憶の使い方

調査前の取得：

```bash
python scripts/build_memory_context.py \
  --date 2026-08-05 \
  --topic "AI設備投資" \
  --entity "Microsoft"
```

最終承認後の昇格：

```bash
python scripts/promote_episode_memory.py \
  publication_record_2026-08-05.json
```

記憶は現在の証拠ではありません。過去の仮説を当日台本へ使う場合は、現在も有効かを再調査します。

## 絶対ルール

- GitHub Actions、Codex、Remotion、外部研究フレームワーク、記憶層へ市場因果や台本の意味を判断させない
- `daily_source_package`だけを言い換えて台本にしない
- 事実、共有解釈、推論、不明を分ける
- 一社の材料をNASDAQ全体の原因へ自動昇格させない
- 売買助言、目標株価、確定的な将来予測を出さない
- ドラフト、却下された因果、未採用画像経路を恒久記憶へ入れない
- 記録のない狐の保有、損益、取引、大学生活上の出来事を記憶として創作しない
