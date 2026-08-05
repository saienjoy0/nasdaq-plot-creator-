# nasdaq-cafe-causal-research

## 位置づけ

```text
daily_source_package
→ このスキル
→ causal_research_dossier
→ 02編集判断
→ 01狐の語り
→ 03制作パッケージ
→ 04審問
```

このスキルは情報収集結果を深掘りする調査員です。最終台本AIや投資判断AIではありません。

## 毎日の入力

従来どおり、基本入力は1つです。

```text
daily_source_package_YYYY-MM-DD.md
```

ユーザーが深掘りMDを別途作る必要はありません。スキル側がWeb・一次資料・市場データ・過去資料を確認し、中間成果物を生成します。

## 毎日の出力

```text
research/causal_research_dossier_YYYY-MM-DD.md
research/causal_research_dossier_YYYY-MM-DD.json
```

## Validator

```bash
python skills/nasdaq-cafe-causal-research/validators/validate_causal_dossier.py \
  research/causal_research_dossier_YYYY-MM-DD.json \
  --json-report research/causal_research_validator_YYYY-MM-DD.json
```

完全なJSON Schema検査には`jsonschema`を使用します。

```bash
python -m pip install "jsonschema>=4.0"
```

## PASSの意味

PASSは、証拠、Expectedの根拠区分、時系列、因果エッジ、代替仮説、反対材料、NASDAQへの範囲分離が構造上そろっていることを示します。

PASSは、市場因果が真実であることや、02の編集判断を通過したことを意味しません。

## 禁止

- `daily_source_package`の言い換えだけで終了する
- 一媒体の説明を市場全体の合意へ変える
- 個別企業の材料を自動的にNASDAQ全体の主因へする
- Expectedを価格反応から後付けする
- 読めない記事を証拠にする
- Buy / Sell / Holdや目標株価を出す
- このスキルから直接`render_spec.json`を生成する
