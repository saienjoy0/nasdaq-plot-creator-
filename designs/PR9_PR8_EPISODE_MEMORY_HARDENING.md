# PR #9｜PR #8 Episode Package Memory Hardening

## 背景

PR #8は、再検証済みeditorial memoryを最終episode packageの正確な利用箇所へ接続する基本契約をmainへ追加した。

最終照合では、基本validatorだけでは次を機械的に確定できないことが分かった。

- episode packageがScene 1〜9を正確に一度ずつ持つこと
- `04 興味深さ・わかりやすさ審問結果`が最終packageへ統合済みであること
- Editorial Memory Usage Annexが本当に最終sectionであること
- spoken script、caption、telop、render specなどの公開成果物へMEMREFやAnnex metadataが漏れていないこと
- 基本PR #8 validatorが失敗した場合、下流が必ず停止すること

このPRはPR #8を置き換えず、基本validatorの上へ最終制作ゲートを追加する。

## 正式validator順序

```text
validate_episode_package_memory.py
↓
validate_episode_package_memory_hardening.py
↓
PR #10以降のproduction package生成
```

hardening validatorは基本validatorを必ず再実行する。基本validatorのERRORを無視してhardeningだけを通すことはできない。

## 追加する停止条件

1. Scene 1〜9が不足、重複、順序違い
2. 04審問結果sectionがない、または複数
3. 04審問結果がAnnexより後ろにある
4. Annex終了後に別sectionまたは本文がある
5. Annex対象日とepisode packageファイル名の日付が一致しない
6. spoken script、captions、telop、render spec等へ次が混入する
   - `<!--MEMREF:`
   - Annex begin/end marker
   - memory reference internal fields
7. 公開成果物pathがrepo外
8. 基本PR #8 validatorがFAILまたは実行不能

## 実行例

```bash
python skills/nasdaq-cafe-episode-package-memory/validators/validate_episode_package_memory_hardening.py \
  --episode-package episodes/YYYY-MM-DD/episode_package_YYYY-MM-DD.md \
  --public-artifact episodes/YYYY-MM-DD/spoken_script_YYYY-MM-DD.md \
  --public-artifact render-specs/YYYY-MM-DD/render_spec.json \
  --output verification/YYYY-MM-DD/episode_memory_hardening.json
```

PR #9時点ではspoken scriptとrender specの生成は行わない。既に存在する場合に漏出検査へ渡せる契約だけを用意する。生成・全成果物整合は次PRの責任とする。

## テスト

- merged PR #8の55件
- hardening追加15件
- PR #6 memory revalidation 25件
- retrieval regression
- promotion regression
- editorial-memory contract validation

## 非目的

- 01〜04の変更
- 主役や市場因果の決定
- ナレーション変更
- render spec生成
- renderer変更
- preview実行

## ロードマップ番号

PR #8のhardeningを独立PRとして挿入したため、以降は次へ繰り下げる。

```text
PR #9  PR #8 Episode Memory Hardening
PR #10 Final Production Package Contract
PR #11 Renderer Handoff Bundle
PR #12 Real-Day End-to-End Acceptance（MVP）
PR #13 Daily Operational Entry Point
```

実装順の意味は変更しない。MVPは依然として、新しい実日の入力からpreview MP4まで通し、ユーザーが目視可能になった時点である。
