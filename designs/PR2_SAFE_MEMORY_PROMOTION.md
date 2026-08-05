# PR2｜承認済み回を安全に記憶へ昇格する書き込み層

## 1. 目的

PR1で定義した記憶契約を使い、承認済みの完成回だけを、監査可能・再実行可能・訂正可能な形で長期記憶へ昇格する。

このPRは台本を作らない。市場因果を判断しない。LLMを呼ばない。承認済み成果物を検証し、保存計画を作り、衝突がない場合だけ機械的に記憶ファイルへ反映する。

## 2. PR1から引き継ぐ前提

PR1には次がある。

- `publication_record.schema.json`
- `immutable_episode.schema.json`
- `temporal_claim.schema.json`
- `entity_aliases.schema.json`
- `memory_promotion_plan.schema.json`
- `memory_policy.md`
- `scripts/promote_episode_memory.py`

PR2では、既存の一段階promotionをそのまま拡張せず、計画と適用を分離する。

```text
現状
publication_record
→ promote_episode_memory.py
→ daily / thread / claimを直接更新

PR2
publication_record
→ source preflight
→ immutable episode archive
→ conflict detection
→ promotion plan（dry-run）
→ staged outputs validation
→ explicit apply
→ promotion report
```

## 3. 参考プロジェクトから採用する原則

### Graphiti

- 派生記憶を必ず元episodeへ遡れるようにする
- 古い仮説を削除せず、時系列と失効状態を残す
- episodeを記憶形成の原単位にする

### Event Sourcing

- 過去の確定記録を上書きしない
- 修正は新しいrevisionまたは新しいeventとして追加する
- 現在状態は不変記録から再構築できるようにする

### Git

- 成果物ごとにSHA-256を保持する
- 同じ内容の再投入をno-opとして扱う
- 複数ファイルの変更を一つのGit commitで確定する

### LangMem

- 制作中のhot pathで恒久記憶を書き換えない
- 承認後のbackground promotionだけを正式書き込み経路にする

### Letta / MemGPT

- core memoryとarchiveを分離する
- PR2ではarchiveとsemantic memoryだけを更新し、core memoryの自動更新は行わない

## 4. 絶対条件

記憶へ昇格できるのは、次をすべて満たす場合だけ。

1. `approval.status`が`approved_preview`または`published`
2. episode package、render spec、validator reportが実在する
3. validator reportが正式PASSを示す
4. episode packageとrender specの対象日が一致する
5. episode packageとrender specのScene順・ナレーション・採用経路の整合が確認済み
6. 最終採用画像経路が一つに確定している
7. 入力ファイルのSHA-256とbyte数を計算できる
8. unresolved conflictが0件
9. promotion planのmodeが`apply`
10. apply前にdry-run reportが生成済み

外部記事、daily source、調査途中のdossier、04審問前の台本から直接promotionしてはいけない。

## 5. 不変episode archive

各承認済み回を次の構成で保存する。

```text
editorial-memory/episodes/YYYY-MM-DD/
├── index.json
└── revisions/
    ├── v001/
    │   ├── publication_record.json
    │   ├── episode_package.md
    │   ├── render_spec.json
    │   ├── validator_report.json
    │   ├── episode_summary.md
    │   └── provenance.json
    └── v002/
        └── ...
```

### 初回

- `v001`を作る
- `index.json.current_revision = "v001"`

### 訂正

- 既存revisionを上書きしない
- `v002`を作る
- `correction_reason`を必須にする
- `supersedes_revision = "v001"`を保存する
- indexのcurrent revisionだけを更新する

### 同一内容の再実行

入力3成果物とpublication recordのhashが既存revisionと完全一致する場合は、`no-op`として成功終了する。新しいrevisionは作らない。

## 6. provenance

`provenance.json`には最低限次を保存する。

```json
{
  "episode_date": "2026-08-05",
  "revision": "v001",
  "approval_status": "approved_preview",
  "approved_at": "...",
  "promoted_at": "...",
  "source_artifacts": {
    "episode_package": {
      "original_path": "...",
      "archive_path": "...",
      "sha256": "...",
      "bytes": 0
    },
    "render_spec": {},
    "validator_report": {}
  },
  "generated_memory_ids": {
    "threads": [],
    "claims": [],
    "aliases": [],
    "lessons": []
  },
  "promotion_plan_sha256": "..."
}
```

thread、claim、alias、lessonから、このepisode revisionへ戻れるようにする。

## 7. promotionを二段階に分ける

### Phase A｜plan / dry-run

入力：

```text
publication_record_YYYY-MM-DD.json
```

出力：

```text
working/memory-promotion/<run_id>/
├── source_preflight.json
├── conflict_report.json
├── promotion_plan.json
├── staged/
│   └── 反映予定の完全ファイル群
└── dry_run_report.md
```

この段階では`editorial-memory/`を変更しない。

### Phase B｜apply

入力：

- schema PASS済みpromotion plan
- unresolved conflict 0件
- stagedファイル群
- applyの明示指定

処理：

1. lock取得
2. 現在の対象ファイルhashを再確認
3. plan作成時から変更がないか確認
4. staged出力を再validate
5. memory filesへ反映
6. promotion report作成
7. lock解放

plan作成後にclaim ledgerなどが変更された場合は、古いplanを拒否して再planする。

## 8. 競合検査

### Blocker

次はapply禁止。

- 同じ日付に異なる内容があり、revision指定がない
- correctionなのに理由またはsupersedesがない
- source artifactが存在しない
- source hashがpublication record記載値と異なる
- validator reportがPASSではない
- 同じclaim IDなのに主張本文が別物へ変わっている
- 許可されていないclaim status遷移
- `invalidated` claimを理由なしに`active`へ戻す
- 同じaliasが複数canonical entityへ割り当てられる
- 同じthread IDが異なる問いを表す
- 記憶ファイルがplan作成後に変更されている
- path traversalまたはrepo外パス

### Warning

人間確認を残すが、規則上apply可能なもの。

- confidenceが2段階以上変化
- active claimが180日以上更新されていない
- thread titleだけが変更される
- production lessonが既存lessonと近似
- evidence pathが同じepisodeへ偏っている

## 9. claim status遷移

許可する基本遷移：

```text
unknown → active / invalidated
active → strengthened / weakened / resolved / invalidated
strengthened → strengthened / weakened / resolved / invalidated
weakened → strengthened / weakened / resolved / invalidated
resolved → resolved
invalidated → invalidated
```

`resolved`または`invalidated`から再開する場合は、同じclaim IDを再利用せず、新しいclaim IDを作り、`supersedes`または`related_claim_ids`で接続する。

これにより、過去に否定された仮説を無言で復活させない。

## 10. atomicity

複数ファイルを直接順番に書くと、途中失敗で部分更新が起こる。

PR2では次を採用する。

1. 全出力を`working/.../staged`へ作る
2. staged内でschema、参照、hashを検査する
3. apply時に対象ファイルのbefore hashを再検査する
4. 全ファイルをworktreeへ反映する
5. 一つのGit commitとして確定する

Git commit前に失敗した場合は、worktree変更を破棄できる。GitHub Actionsが自動で市場判断や記憶内容を変更することはない。ChatGPT側で完成したplanを機械的に適用するだけとする。

v1ではGitHub Contents APIによる複数回の直接書き込みを正式apply経路にしない。

## 11. 実装ファイル

```text
scripts/
├── plan_memory_promotion.py
├── apply_memory_promotion.py
├── memory_promotion_lib.py
└── promote_episode_memory.py  # 互換ラッパー化または廃止予定表示

skills/nasdaq-cafe-editorial-memory/contracts/
├── memory_source_preflight.schema.json
├── memory_conflict_report.schema.json
├── memory_promotion_report.schema.json
└── immutable_episode.schema.json  # revision/provenanceを強化

tests/memory-promotion/
├── fixtures/
└── test_memory_promotion.py

.github/workflows/
└── editorial-memory-promotion-tests.yml
```

## 12. CLI案

### dry-run

```bash
python scripts/plan_memory_promotion.py \
  publication_record_2026-08-05.json \
  --output working/memory-promotion/2026-08-05
```

### apply

```bash
python scripts/apply_memory_promotion.py \
  working/memory-promotion/2026-08-05/promotion_plan.json \
  --apply
```

`--apply`なしでは絶対に記憶ファイルを書き換えない。

## 13. テストケース

### 正常系

1. 空のmemoryへ初回v001を昇格
2. 同じ入力を再実行してno-op
3. correctionとしてv002を追加
4. active claimをstrengthenedへ更新
5.新規threadとentity aliasを追加

### 拒否系

1. 未承認publication record
2. validator report非PASS
3. source file欠損
4. source SHA不一致
5. same-date different-contentでrevisionなし
6. claim本文衝突
7. invalidatedからactiveへの復活
8. alias衝突
9. thread意味衝突
10. unresolved conflict付きapply
11. plan後にledgerが変更されたstale plan
12. path traversal

### 原子性

1. apply途中の模擬例外で恒久memoryが変化しない
2. staged validation失敗で変更なし
3. lock取得済み時に二重applyを拒否

## 14. CI

PR上では次だけを実行する。

- Python compile
- schema validation
- unit tests
- fixtureを使ったdry-run
- applyを一時ディレクトリ内で実行
- idempotency test
- atomicity test

PR CIでは実リポジトリの`editorial-memory/`をcommit・pushしない。

実際のmemory promotionは、完成回の明示承認後にChatGPTがplanを作り、dry-run内容を確認してからapplyする。

## 15. PR2に含めないもの

- embedding検索
- Graph DB
- weekly/monthly compaction
- retrieval採点改善
- episode package内のmemory reference欄
- LLMによる自動conflict解決
- 自動でcore memoryを書き換える処理
- GitHub Actionsによる無人の毎日promotion

これらはPR3以降とする。

## 16. 実装順

1. source preflightとhash計算
2. immutable episode archive writer
3. conflict detector
4. promotion plan生成
5. staged output builder
6. apply writerとlock
7. report生成
8. 旧scriptを互換ラッパー化
9. fixture・unit test
10. CI

## 17. 完了条件

- 承認済み回からv001 archiveを作れる
- 訂正はv002として追加され、v001が残る
- 全archive artifactにSHA-256とbyte数がある
- 全thread / claim更新が元episode revisionへ遡れる
- dry-runでは恒久memoryが一切変わらない
- unresolved conflictがあればapplyできない
- 同一入力の再実行がno-opになる
- stale planが拒否される
- apply失敗時に部分更新が残らない
- CIの正常系・拒否系・原子性テストがすべてPASSする
