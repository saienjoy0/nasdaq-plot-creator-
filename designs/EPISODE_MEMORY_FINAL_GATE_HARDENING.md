# Episode Memory Final Gate Hardening

## 現在地

mainには次まで実装済みである。

```text
PR #8  Episode Package Memory Reference
PR #9  Financial Visual Intent boundary
PR #10 Final Production Package Contract
```

このhardeningは、PR #8とPR #10の間に残った実行上の隙間を閉じる。

## 解決する問題

PR #8の基本validatorはmemory ID、status、Evidence ID、MEMREF marker、Scene/surfaceを監査する。
PR #10のbuilderはfinal production artifactsを決定的に生成する。

ただし、両者を別々に呼べる状態では次が保証されない。

- 人間向けepisode packageにScene 1〜9が正確に一度ずつある
- 04審問結果が最終packageへ一度だけ統合されている
- Memory AnnexとFinal Production Source Annexの順序が固定される
- PR #8 validatorを通さずPR #10 builderだけを呼ばない
- 生成後のspoken script、asset manifest、render specへmemory metadataが漏れた場合、preflight PASSを残さない

## 正式なAnnex順序

```text
公開編集内容
→ Scene 1〜9
→ 04 興味深さ・わかりやすさ審問結果
→ Editorial Memory Usage Annex
→ Final Production Source Annex（存在する場合）
→ EOF
```

Memory Annexの後は、空白またはFinal Production Source Annex一件だけを許可する。
Final Production Source Annexが存在する場合、それが最終sectionである。

## 正式実行入口

```text
validate_episode_package_memory.py
→ validate_episode_package_memory_hardening.py
→ build_final_production_package_hardened.py
```

`build_final_production_package_hardened.py`は次を行う。

1. PR #8 base validatorとPR #6 replayを含むpre-build hardening
2. PR #10 base builderによる成果物生成
3. spoken script、asset manifest、render specのmetadata漏出再検査
4. post-build検査失敗時は生成物を削除
5. preflight PASSを残さずFAILで停止

## 追加停止条件

- Scene不足、重複、順序違い
- 04審問結果なし、または複数
- Memory Annex後の任意本文
- Final Production Source Annexの重複、逆順、末尾以外への配置
- packageファイル名とmemory episode dateの不一致
- public artifactsへのMEMREF、Annex marker、internal memory fields混入
- output rootまたはpublic artifact pathのrepo外脱出
- base PR #8 validatorの失敗または実行不能
- post-build gate失敗後も生成物が残る状態

## 検査集合

```text
PR #8 tests                         55
Episode-memory hardening tests      17
Final-production package tests      30
Guarded final-production tests       6
PR #6 memory-revalidation tests     25
Retrieval / promotion / contracts regressions
```

## 境界

このhardeningは次を変更しない。

- 01〜04
- 主役、市場因果、Expected / Actual / Gap
- 狐ナレーション
- Visual Beatの意味
- Primary / Approved Fallbackの編集判断
- renderer
- preview / final承認

## 次の工程

このgateがmainへ入った後、次はRenderer Handoff Bundleである。

```text
validator済みproduction artifacts
→ handoff_manifest.json
→ 対象日・契約版・SHA固定
→ renderer preview workflow
```

Real-Day End-to-End Acceptanceで、新しい当日資料一件をpreview MP4まで通した時点をMVPとする。
