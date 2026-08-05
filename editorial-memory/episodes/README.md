# Immutable episode archive

承認済みの過去回をrevision単位で保存します。

```text
editorial-memory/episodes/YYYY-MM-DD/
├── publication_record.v1.json
├── episode_summary.md
└── provenance.json
```

既存revisionは上書きしません。訂正時は`publication_record.v2.json`のように新しいrevisionを追加し、`supersedes`で前版を参照します。

このディレクトリへ書けるのは、schema検証・approval確認・source SHA-256照合・conflict検査を通過したpromotionだけです。
