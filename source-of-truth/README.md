# Source of Truth

## 保存状態

- `01_fox_character_bible.md`：平文正本
- `02_editorial_bible.md`：平文正本
- `03_episode_production_spec.md`：`packed/`から復元する正本
- `04_entertainment_inquisitor.md`：`packed/`から復元する正本

03・04はGitHub書き込み時のサイズ制約を避けるため、gzip圧縮後にbase64化して分割保存しています。`packed_sources.json`に、部品順、元サイズ、復元後SHA-256を固定しています。

## 復元と検査

```bash
python scripts/materialize_sources.py --check-only
python scripts/materialize_sources.py
```

`--check-only`は、全パーツの存在、base64、gzip、元サイズ、SHA-256を検査します。

検査に成功する前に、分割ファイルの一部だけを03・04として読んではいけません。

## 更新ルール

1. 変更後の原本を確定する
2. 原本のSHA-256を計算する
3. gzip + base64へ変換する
4. 固定順で分割する
5. `packed_sources.json`を更新する
6. `materialize_sources.py --check-only`を通す
7. 復元した平文と原本のSHA-256が一致することを確認する

### transport-only repair

packed部品だけが破損し、手元の正本が`packed_sources.json`に記録された`raw_bytes`と復元後SHA-256へ完全一致する場合は、原本文書を編集せずpacked transportだけを再生成してよいです。この場合は部品パス、`raw_bytes`、復元後SHA-256を変更せず、再生成後に必ず`materialize_sources.py --check-only`を通します。

01〜04の内容を外部プロジェクトの仕様へ自動変換しません。外部プロジェクトは調査機構の参考であり、正本ではありません。