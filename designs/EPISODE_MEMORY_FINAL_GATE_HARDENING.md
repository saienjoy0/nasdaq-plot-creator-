# Episode Memory Final Gate Hardening

## 目的

PR #8のeditorial-memory監査、Final Production Package、Renderer Handoffの間に残る実行上の隙間を閉じる。

この変更は編集判断を追加しない。既にChatGPTが01〜04に従って完成させた内容について、最終package形状と公開成果物へのmetadata漏出を決定的に検査する。

## 解決する問題

- PR #8 base validatorだけではScene 1〜9の完全性と04審問統合を最終ゲートとして固定していなかった
- Memory AnnexとFinal Production Source Annexの順序を横断的に固定していなかった
- Final Production builderをPR #8検証なしで直接実行できた
- 生成後にMEMREFまたはmemory internal fieldsが漏れた場合、生成済みpreflightが残る余地があった

## 正式Annex順序

```text
公開編集内容
→ Scene 1〜9
→ 04 興味深さ・わかりやすさ審問結果
→ Editorial Memory Usage Annex
→ Final Production Source Annex（存在する場合）
→ EOF
```

Memory Annexの後は空白、またはFinal Production Source Annex一件だけを許可する。Final Production Source Annexがある場合、それが最終sectionである。

## 正式実行入口

```text
validate_episode_package_memory.py
→ validate_episode_package_memory_hardening.py
→ build_final_production_package_hardened.py
```

`build_final_production_package_hardened.py`は次を行う。

1. base PR #8 validatorとPR #6 replayを含むpre-build gate
2. base Final Production builderによる決定的生成
3. spoken script、asset manifest、render specのpost-build漏出検査
4. post-build FAIL時の生成物削除
5. hardening PASSを返さない限り下流handoffへ進ませない

## 追加停止条件

- Scene不足、重複、順序違い
- 04審問結果なし、または複数
- Memory Annex後の任意本文
- Final Production Source Annexの重複、逆順、末尾以外への配置
- package filenameとmemory episode dateの不一致
- public artifactsへのMEMREF、Annex marker、internal memory fields混入
- output rootまたはpublic artifact pathのrepo外脱出
- base PR #8 validatorのFAILまたは実行不能
- post-build FAIL後に生成物が残る状態

## 回帰検査

- merged PR #8 tests
- episode-memory hardening tests
- Final Production Package tests
- guarded Final Production tests
- PR #6 memory-revalidation tests
- retrieval tests
- promotion tests
- editorial-memory contract validator

## 非目的

- 01〜04の変更
- 主役、市場因果、Expected / Actual / Gapの決定
- 狐ナレーションの修正
- Visual Beatや画像経路の編集判断
- rendererの変更
- previewやfinalの自動承認

## 次の実運用ゲート

このhardeningがmainへ入った後、Real-Day End-to-End Acceptanceでは、hardening済みFinal Production成果物とSHA固定Renderer Handoff Bundleだけをpreview検査対象にする。
