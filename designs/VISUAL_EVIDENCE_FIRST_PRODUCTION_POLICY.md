# 朝のNASDAQカフェ｜Visual Evidence First Production Policy

## 目的

動画の見た目を「抽象グラフの連続」から、**本物の証拠 → 本物の市場反応 → Remotionによる解説**へ戻す。

この文書は市場因果を決めない。02で確定した主役・Expected / Actual / Gap・時系列・反対材料を変えず、03のVisual Beatへ何を見せるかを決めるための制作ルールである。

## 基本順序

原則として、視聴者が証拠そのものを見る価値がある場合は次の順で組む。

1. 実際の一次資料・公式ページ・重要な公式投稿
2. 実際の価格反応・検証済み時系列
3. Expected / Actual / Gap、比較、因果経路などのRemotion解説
4. 企業・人物・機関カード、再利用背景、概念素材

抽象テンプレートは説明に使う。一次資料や実価格が存在するのに、それらを置き換える目的では使わない。

## 普通の日

重要な公式資料が主役・重要根拠なら、少なくとも一つは実資料Visual Sourceとして見せる。

検証済みの分足があり、ナレーションが発表時刻の初動を語る場合は、カードへ数値を転記するだけではなく、`event-reaction-timeline / verified-series`で実測点を見せる。

XやSNSは毎日のノルマにしない。投稿そのものがニュース・証拠・市場解釈の対象である場合だけ`social-post`として使う。

## 決算日

決算を主役または重要な増幅要因として扱う場合は、原則として次を検討する。

- 企業カードまたは企業識別Visual
- 企業IR・決算リリース・株主資料などの実資料
- Expected / Actual / Gapまたは実績・ガイダンス比較
- 取得できる場合は決算発表前後・時間外・通常取引の実価格反応

企業IRが存在するのに、決算数字をすべて自作カードへ転記して終わらせない。

## Fed・金融政策日

Fed/FOMCが主役または重要な経路である場合は、原則として次を検討する。

- Fed公式声明、議事要旨、講演、会見資料などの実資料
- 人物が実際に材料の発信者・政策判断主体である場合のみ公式人物カード
- 金利・政策期待とNASDAQへの経路
- 取得できる場合は発表時刻前後のQQQ・金利等の実反応
- `background_scene_fed`等の機関背景は理解補助として使用可能

「Fed」という語が出ただけで特定人物を自動表示しない。

## Visual Source Planning

当日固有素材が必要なBeatは、取得前にPrimaryとApproved Fallbackを両方完成させる。

Primary例：
- `official-url / webpage-screenshot`
- `collector-document / pdf-page-render`
- `social-post / social-capture`

Fallback例：
- 既存企業カード
- 既存人物・機関カード
- 既存ニュース背景
- 既存半導体・Fed・検証概念素材

Fallbackでも事実、因果、留保が変わらないことを確認する。

## 禁止する劣化

次をProduction PASSとして扱わない。

- 公式統計・企業IR・重要公式投稿を主根拠として使っているのにVisual Source Planが空
- 検証済み1分足で初動を説明しているのに、実系列を出さず数値カードだけで済ませる
- 決算回で企業IRがあるのに、IRを見せる計画自体がない
- social-postを証拠として採用したのに投稿Visualがない
- 同じカード・抽象グラフの連続を、画面多様性として数える
- Rendererに企業・人物・資料・チャートを推測させる

## 画面多様性

多様性はテンプレート数だけで判定しない。Scene 1〜8では、必要に応じて次の異なる表面を混ぜる。

- source-document / social-post
- verified price series
- entity / person / institution
- Expected / Actual / Gap
- causal path
- comparison / counterevidence
- verification

一次資料と実価格が使える回で、抽象画面だけが長く連続する場合は04の興味深さ・わかりやすさ審査へ戻す。

## 8/10受入基準

2026-08-10回では最低限、次がProduction authoringに存在すること。

- BLS Employment Situationの実資料Primary + Approved Fallback
- Microchip Q1 FY27 IRの実資料Primary + Approved Fallback
- QQQ 08:29 / 08:30 / 08:31 ETの検証済み1分足を`verified-series`で表示
- 1分足は因果証明ではないという既存留保を維持
- MCHPの同時刻ほぼ横ばいを反対・比較材料として維持
- Fed/金利Sceneで金融政策向け再利用背景を使えるが、無関係な人物は出さない

これらを満たしても市場因果・ナレーション・Scene順は変更しない。
