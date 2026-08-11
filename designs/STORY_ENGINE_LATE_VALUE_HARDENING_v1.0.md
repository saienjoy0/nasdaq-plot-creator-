# 朝のNASDAQカフェ｜Story Engine Late Value Hardening v1.0

- Date: 2026-08-11
- Scope: Story Plan / Unified Story Engine / Entertainment Critic / validators / external critic adapter
- Status: implementation record
- Branch: `fix/story-engine-late-value-gate`

## 1. 問題

2026-08-10制作パッケージでは、市場因果・Expected / Actual / Gap・反対材料・時系列はよく整理されていた一方、Scene 4付近で中心回答がほぼ完成し、その後のSceneが「追加の支援材料・留保・検証」に寄った。

その結果、構造上は理解更新として扱える情報追加が存在しても、視聴者体験としては後半の発見が弱いまま高得点PASSし得た。

根本問題は01〜04に興味深さの思想が存在しないことではない。

既存正本にはすでに以下がある。

- 重要な矛盾を主役にする
- 見出し以上の発見を作る
- Sceneごとに理解を更新する
- Scene 6〜8まで見る理由を残す
- 冒頭で答えを隠さないが、説明し切って後半価値を消さない
- 反対材料・時系列・因果範囲を面白さのために変えない

不足していたのは、これらを日次Story EngineとCriticが逃げられない形で強制する実行契約である。

## 2. 最終思想

> **結論を遅らせるのではなく、結論を進化させる。**

Scene 1〜4で方向や暫定回答を渡すことは許可する。

ただしScene 6〜8まで見ることで、少なくとも一つ、Evidenceに基づいて説明モデルが次のいずれかへ進む必要がある。

- turn
- branch
- boundary
- scale reveal
- mechanism reveal
- disproof
- reason-unknown payoff
- material price-reaction test

単なる追加ニュース、追加統計、同じ結論の補強、注意書きの追加はUnderstanding Upgradeではない。

## 3. Midpoint Turnの再定義

既存JSON互換性のためfield名`midpoint_turn`は維持する。

しかし意味契約は次へ変更する。

```text
旧誤解:
劇的反転を一つ置く

新:
Evidence-backed Understanding Upgradeを一つ置く
```

劇的反転は必須ではない。

市場Evidenceに反転がなければ、branch / boundary / mechanism / test / reason_unknownでよい。

EvidenceがどのUpgradeも支えない場合、ドラマを創作せず短尺化する。

## 4. Hard Narrative Gates

04 Criticは点数を付ける前に次を審問する。

### A. Hook Exhaustion

Scene 1〜2で最終合成まで説明し切り、残りが証拠資料の読み上げになっていないか。

### B. Understanding Upgrade Authenticity

指定されたUpgradeが、本当に説明モデルを変化・分岐・限定・検証しているか。

追加情報だけなら不合格。

### C. Scene 4 → Scene 8 Understanding Delta

Scene 8で、Scene 4時点ではまだ分からなかった何を理解できるようになったか。

具体的に答えられなければ不合格。

### D. Late Value Deletion Test

Scene 6〜8を削除した場合、視聴者が失う重要な理解は何か。

「追加例」「追加統計」「同じ留保」しか失わないなら不合格。

### E. No Forced Drama

反転Evidenceが存在しない回へ、視聴維持のためだけの反転を創作しない。

## 5. Scoreの位置づけ

従来の30点採点は残す。

ただし点数はHard Gateより下位とする。

```text
29 / 30
+
NO_LATE_PAYOFF major
=
PASS禁止
```

PASS時はScene 1〜8について、少なくとも以下が成立する。

- payoff_delivered = true
- belief_changed = true

Scene 1〜7:
- continuation_reason_natural = true

Scene 8:
- closure_effective = true
- opening_promise_recovered = true

## 6. 01〜04を直接改変しない理由

今回の原因調査では、01〜04の正本に必要思想の大部分が既に存在することを確認した。

そのため、Packed正本03/04を同義反復で大型改変することはしない。

今回の修正対象は、その思想を実際の日次制作へ適用する実行層とする。

- `skills/nasdaq-cafe-story-plan/SKILL.md`
- `skills/nasdaq-cafe-story-plan/validators/validate_story_plan.py`
- `skills/nasdaq-cafe-story-engine/SKILL.md`
- `skills/nasdaq-cafe-entertainment-critic/SKILL.md`
- `skills/nasdaq-cafe-entertainment-critic/contracts/creative_review.schema.json`
- `scripts/story-engine/validate_story_engine_bundle.py`
- `critic-adapters/openai/main.py`
- related regression tests

01〜04の正本を将来改訂する場合も、この実行契約を重複記述するのではなく、上位思想を短く明文化する範囲に留める。

## 7. 2026-08-10回に対する期待挙動

旧評価では、雇用下振れ→利上げ観測後退という中心回答が早期に完成し、後半の原油・Microchip・反対材料を追加支援として扱っても高得点PASSし得た。

新契約では、例えば次のような理解進展を要求する。

```text
暫定理解:
弱い雇用 → 利上げ観測後退 → テック追い風

Upgrade Evidence:
QQQ / SOXX / NVDAは8:30 ETで上向く一方、MCHPは同じ1分でほぼ横ばい

理解更新:
同じ半導体高でもマクロ反応と企業固有材料を分ける必要がある

Late Value:
MCHPの決算という別エンジン + AMD / Alphabetの逆行により「テック全面高」の一般化も限定される

Final Reframe:
一つの悪材料が一方向へ全銘柄を動かした夜ではなく、複数エンジンが同じ指数方向へ重なった夜
```

このようなEvidence-backed upgradeを作れない場合は、無理に創作せず、より短いエピソードへする。

## 8. 非目標

今回の変更では以下を行わない。

- 市場因果の再判定
- Expected / Actual / Gapの変更
- 9Scene formal roleの変更
- Scene順の時系列偽装
- 毎回の劇的反転強制
- 新Evidenceの創作
- 視聴維持目的のFake Open Loop
- Remotionによるストーリー判断
- 01〜04のPacked正本の不用意な再生成

## 9. 完了条件

- Story Plan validatorが構造上のbefore/after同一を拒否する
- EvidenceなしUnderstanding Upgradeを拒否する
- Scene 4とScene 8が構造上同一理解のまま終わる計画を拒否する
- CriticがHard Narrative findingsをminorへ格下げできない
- 29/30でもLate Payoff不成立ならPASSできない
- external Critic adapterも同じ契約を使用する
- 市場因果・Evidence・confidence・counterevidence保全契約は変更しない
