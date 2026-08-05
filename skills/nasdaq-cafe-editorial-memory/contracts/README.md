# Editorial Memory Contracts

このディレクトリは、「記憶がある狐」の読み取り・検索・昇格を機械検証する契約です。

## PR1で追加した契約

- `immutable_episode.schema.json`：承認済み過去回の不変archive
- `temporal_claim.schema.json`：有効期間、状態変化、元episodeを持つclaim v2
- `entity_aliases.schema.json`：企業、製品、政策、指数などの表記揺れ
- `memory_query_plan.schema.json`：当日入力から何を検索するか
- `memory_retrieval_report.schema.json`：何を採用・却下したか
- `memory_promotion_plan.schema.json`：恒久記憶へ何を変更するか

既存の`publication_record.schema.json`は、現在のpromotionスクリプトとの互換契約です。SHA-256付きimmutable episodeへの移行はPR2で行います。

## 境界

schema PASSは、市場因果や過去claimが現在も正しいことを証明しません。

保証するのは次だけです。

- 必須項目が存在する
- 記憶から元episode・成果物へ遡れる形になっている
- invalidated claimを現在前提として扱わない
- 衝突を抱えたpromotionをapplyできない
- 検索結果の採用・却下理由を記録できる

## Validator

```bash
python -m pip install jsonschema
python skills/nasdaq-cafe-editorial-memory/validators/validate_memory_contracts.py --require-jsonschema
```

validatorは正常fixtureに加え、次の危険ケースが拒否されることも検査します。

- `invalidated`なのに`valid_to=null`かつ現在前提として使うclaim
- conflictが残り、`safe_to_apply=false`なのに`mode=apply`のpromotion plan
