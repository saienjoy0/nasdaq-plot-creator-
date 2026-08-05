# 朝のNASDAQカフェ｜調査・台本スキル作業庫

このリポジトリは、朝のNASDAQカフェの情報源正本、因果深掘りスキル、台本制作契約を管理する作業庫です。

## 目的

毎日の `daily_source_package_YYYY-MM-DD.md` をそのまま要約するのではなく、関連背景、過去経緯、企業関係、供給網、マクロ要因、代替仮説を追加調査し、NASDAQへ届いた因果だけを9シーン台本へ変換します。

## 基本フロー

```text
daily_source_package
→ causal_research_dossier
→ 02_editorial_bible による編集判断
→ 01_fox_character_bible による狐の語り
→ 03_episode_production_spec による9シーン制作
→ 04_entertainment_inquisitor による審問・手直し
→ render_spec.json
```

## ディレクトリ

- `source-of-truth/`：番組の01〜04正本
- `skills/nasdaq-cafe-causal-research/`：台本前段の因果深掘りスキル
- `references/`：外部プロジェクトの採用・不採用判断
- `examples/`：検証用入力と期待出力

## 絶対ルール

- GitHub Actions、Codex、Remotionへ市場因果や台本の意味を判断させない
- `daily_source_package`だけを言い換えて台本にしない
- 事実、共有解釈、推論、不明を分ける
- 一社の材料をNASDAQ全体の原因へ自動昇格させない
- 売買助言、目標株価、確定的な将来予測を出さない
