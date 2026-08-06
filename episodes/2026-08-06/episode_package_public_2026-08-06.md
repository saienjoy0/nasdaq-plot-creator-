# 朝のNASDAQカフェ｜2026-08-06 制作パッケージ

## A. エピソード概要
- 対象日：2026-08-06
- 市場セッション：2026-08-05 US market
- 情報締切：2026-08-06T04:31:00Z
- エピソード種別：単独ニュース＋増幅要因
- 主役ニュース：AMDの好決算後下落
- 主役テーマ：not-applicable
- 対象指数：Nasdaq Composite / SOXX
- 目標音声尺：明示的な短縮回
- Charon実測音声尺：未実行
- 短縮理由：主役因果、反対材料、検証条件を9シーンで完結できる一方、金利・VIX・分足が欠損しており、480秒へ合わせる背景ニュース追加は水増しになるため。
- ストーリーの背骨：AMDは売上と見通しで通常予想を超えたのに、高まったAI期待とSpaceXのNVIDIA専属採用によって競争上の追加証拠が不足したと評価され下落し、その半導体安にAlphabetとMicrosoftの下落も重なってNASDAQは0.83%下落した。
- 中心仮説：昨夜のAI半導体市場は需要の有無ではなく、次の巨大需要を誰が確実に取るかを評価し、通常予想を超えたAMDよりSpaceXの採用証拠を得たNVIDIAを高く評価した。
- 主役銘柄の直接材料：Q2売上115.4億ドル、データセンター67.2億ドル、Q3見通し130億ドル、それでもAMD -7.04%
- NASDAQ全体の主因・支援材料：SOXX -2.12%、Alphabet -4.03%、Microsoft -1.09%。AMD一社をNASDAQ全体の主因へ拡大しない
- 増幅要因：SpaceXのNVIDIA専属採用、粗利率横ばい、供給制約
- 相殺・反対材料：NVIDIA +3.43%、AMDの通常予想超過、Dow +0.5%
- Expected：Q3売上125.2億ドル前後のアナリスト予想。報道上の高まった期待は大型顧客と利益率の追加証拠
- Actual：Q3見通し130億ドル、Q2売上115.4億ドル、データセンター67.2億ドル、粗利率見通し56%。SpaceX専属採用はNVIDIA
- Gap：数値Gapは+4.8億ドル、期待Gapは不足
- Expectedの根拠区分：アナリストコンセンサス＋主要報道の市場解釈
- 時系列の根拠：8月4日16:30 ET SpaceX、17:00 ET AMD、時間外反応、8月5日終値。分足なし
- 確信度：Medium
- 重要な反対材料：NVIDIA上昇、Dow上昇、AMDの予想超過、金利・VIX・分足欠損
- 正本背景：mainBackground / ready
- 正本狐：foxNormalを基準に既存7表情 / ready
- 音声プロファイル：gemini-charon
- TTSブロックA：Scene 1〜4
- TTSブロックB：Scene 5〜9
- TTS再実行方針：失敗ブロックのみ
- 画像依頼票：なし
- 画像採用経路：not-required
- Visual Beat総数：18
- Scene 1〜8の画面状態種類：Data / Chart / EntityFocus
- 非分析画面Beat数：2（AMD、NVIDIAのEntityFocus）
- 前半の大きな画面変化：Scene 2 AMD EntityFocus、Scene 4 Gap Chart
- 後半の大きな画面変化：Scene 5 NVIDIA EntityFocus、Scene 6 reaction timeline
- 最長同一画面状態連続数：3以下
- 主役カード：company_amd / ready
- 比較カード：company_nvda / ready、company_googlは登録済みだが本番Beatでは未使用
- render_spec validator：未実行。ローカル構造・整合検査pass、正式CI待ち
- episode_package・render_spec整合：ローカルpass

### 画面構成表

| Scene | 画面状態列 | 主な役割 |
|---|---|---|
| 1 | Data → Data | 方向、矛盾、中心仮説を30秒以内に提示する |
| 2 | EntityFocus → Chart | AMDの好決算と株価下落を分けて示す |
| 3 | Data → Chart | AMD決算の確認済み数値を解釈前に置く |
| 4 | Chart → Data | 通常の予想超過と高まったAI期待の未達を分ける |
| 5 | EntityFocus → Chart → Data | SpaceXの採用判断が半導体競争へ届く経路を示す |
| 6 | Chart → Data | 発表順と終値を使い、主役反応とNASDAQ全体を分ける |
| 7 | Chart → Data | 仮説の限界を三銘柄比較で示す |
| 8 | Data → Data | 仮説が強まる条件と弱まる条件を対で示す |
| 9 | Data | 中心結論を回収し固定エンディングへつなぐ |

## B1. Scene 1｜寝ている間に何が起きた？

- 目的：方向、矛盾、中心仮説を30秒以内に提示する
- 目安時間：執筆目安のみ。実測はTTS後
- 因果の対象：multiple
- 狐の演技意図：驚きを短く置き、結論へ進む
- 狐の表情：軽い驚き
- 表情切り替え：『結論から言うと』で分析へ
- 画面モード：conclusion-card
- 前後の接続文：冒頭

### Visual Beats

- **scene-01-beat-001**
  - 開始合図：おはようございます。僕が時差で少し早く見ておいたので、一緒に整理しましょう。昨夜のNasdaq 
  - 終了合図：三・四三パーセント上昇し、AMDは七・〇四パーセント下落。同じAI半導体でも、値動きは真逆です。
  - 主要視覚機能：Anchor
  - 画面状態：Data
  - Visual Grammar：contradiction / major-shift
  - Visual Template ID：opening-contradiction
  - Template Variant：default
  - 入力構造：NASDAQ -0.83% / SOXX -2.12% / NVIDIA +3.43% / AMD -7.04%
  - 画面の問い：昨夜の矛盾は何か
  - 主要要素：NASDAQ下落と半導体二極化
  - 視聴者向けテキスト：NASDAQ -0.83% / SOXX -2.12% / NVIDIA +3.43% / AMD -7.04%
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-001

- **scene-01-beat-002**
  - 開始合図：結論から言うと、昨夜はAI需要があるかではなく、その次の巨大需要を誰が確実に取れるかが採点されま
  - 終了合図：MDの数字は予想を超えましたが、NVIDIAにはSpaceXという新しい採用証拠が加わりました。
  - 主要視覚機能：Explain
  - 画面状態：Data
  - Visual Grammar：evidence / continuation
  - Visual Template ID：hero-number
  - Template Variant：default
  - 入力構造：AI需要の有無ではない / 次の巨大需要を誰が取るか
  - 画面の問い：市場が見た論点は何か
  - 主要要素：需要の有無から受注証拠へ
  - 視聴者向けテキスト：AI需要の有無ではない / 次の巨大需要を誰が取るか
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-001, source-005, source-007

### 完成ナレーション

おはようございます。僕が時差で少し早く見ておいたので、一緒に整理しましょう。昨夜のNasdaq Compositeは〇・八三パーセント下落し、半導体ETFのSOXXは二・一二パーセント安でした。ところがNVIDIAは三・四三パーセント上昇し、AMDは七・〇四パーセント下落。同じAI半導体でも、値動きは真逆です。

結論から言うと、昨夜はAI需要があるかではなく、その次の巨大需要を誰が確実に取れるかが採点されました。AMDの数字は予想を超えましたが、NVIDIAにはSpaceXという新しい採用証拠が加わりました。


- ナレーションで示す出典主体・媒体：当日の市場データ
- 大テロップ：NASDAQ -0.83%
- 補助テロップ：SOXX -2.12% / NVIDIA +3.43% / AMD -7.04%
- 使用する数字：SOXX -2.12% / NVIDIA +3.43% / AMD -7.04%
- 画面で見せる内容：NASDAQ下落と半導体二極化; 需要の有無から受注証拠へ
- 根拠：当日の市場データ
- 不確実性：終値中心で、分足の反応時刻は確認できない

## B2. Scene 2｜今朝の矛盾

- 目的：AMDの好決算と株価下落を分けて示す
- 目安時間：執筆目安のみ。実測はTTS後
- 因果の対象：lead-stock
- 狐の演技意図：企業カードで対象を固定し、悪決算という誤読を防ぐ
- 狐の表情：分析
- 表情切り替え：『それでも』で困惑へ
- 画面モード：text-focus
- 前後の接続文：まずAMDです。

### Visual Beats

- **scene-02-beat-001**
  - 開始合図：まずAMDです。CPUとGPUを設計する半導体会社で、今回の四半期売上は百十五・四億ドル。データ
  - 終了合図：七・二億ドルで、前年の二倍を超えました。数字だけを見れば、AI需要が弱かった決算ではありません。
  - 主要視覚機能：Anchor
  - 画面状態：EntityFocus
  - Visual Grammar：entity / major-shift
  - Visual Template ID：entity-card-full
  - Template Variant：prebuilt-card
  - 入力構造：AMD / CPUとGPUを設計する半導体会社
  - 画面の問い：主役企業は誰か
  - 主要要素：AMD企業カード
  - 視聴者向けテキスト：AMD / CPUとGPUを設計する半導体会社
  - 使用アセットID：company_amd
  - アセット状態：ready
  - 表示後の復帰先：Data
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-004

- **scene-02-beat-002**
  - 開始合図：それでも株価は七パーセント下落しました。売上は増え、見通しも市場予想を超え、それでも売られる。市
  - 終了合図：られる。市場、要求が多いです。ここで決算が悪かったと読み替えると、昨夜の本当の矛盾を見失います。
  - 主要視覚機能：Explain
  - 画面状態：Chart
  - Visual Grammar：comparison / continuation
  - Visual Template ID：diverging-stock-bars
  - Template Variant：default
  - 入力構造：Q2売上 115.4億ドル / AMD -7.04%
  - 画面の問い：業績と株価は同じ方向だったか
  - 主要要素：好決算と株価下落
  - 視聴者向けテキスト：Q2売上 115.4億ドル / AMD -7.04%
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-001, source-004

### 完成ナレーション

まずAMDです。CPUとGPUを設計する半導体会社で、今回の四半期売上は百十五・四億ドル。データセンター売上は六十七・二億ドルで、前年の二倍を超えました。数字だけを見れば、AI需要が弱かった決算ではありません。

それでも株価は七パーセント下落しました。売上は増え、見通しも市場予想を超え、それでも売られる。市場、要求が多いです。ここで決算が悪かったと読み替えると、昨夜の本当の矛盾を見失います。


- ナレーションで示す出典主体・媒体：AMD IR / Reuters / 当日の市場データ
- 大テロップ：AMD -7.04%
- 補助テロップ：売上は過去最高 / データセンターは2倍超
- 使用する数字：データセンターは2倍超
- 画面で見せる内容：AMD企業カード; 好決算と株価下落
- 根拠：AMD IR / Reuters / 当日の市場データ
- 不確実性：株価下落を一つの決算項目だけへ帰属しない

## B3. Scene 3｜何が起きた？

- 目的：AMD決算の確認済み数値を解釈前に置く
- 目安時間：執筆目安のみ。実測はTTS後
- 因果の対象：lead-stock
- 狐の演技意図：数字を落ち着いて並べ、評価を急がない
- 狐の表情：分析
- 表情切り替え：なし
- 画面モード：number-comparison
- 前後の接続文：確認できた数字を置きます。

### Visual Beats

- **scene-03-beat-001**
  - 開始合図：確認できた数字を置きます。前の四半期にAMDが示していた第二四半期売上の中心値は百十二億ドルでし
  - 終了合図：、中心値を三・四億ドル上回りました。データセンター売上の六十七・二億ドルも、前年から二倍超です。
  - 主要視覚機能：Explain
  - 画面状態：Data
  - Visual Grammar：evidence / major-shift
  - Visual Template ID：metric-comparison-board
  - Template Variant：default
  - 入力構造：会社見通し中心 112億ドル / 実績 115.4億ドル / 差 +3.4億ドル
  - 画面の問い：Q2実績は会社見通しを超えたか
  - 主要要素：Q2会社見通しと実績
  - 視聴者向けテキスト：会社見通し中心 112億ドル / 実績 115.4億ドル / 差 +3.4億ドル
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-002, source-004

- **scene-03-beat-002**
  - 開始合図：さらに第三四半期の売上見通しは約百三十億ドル。Reutersが示した市場予想百二十五・二億ドルを
  - 終了合図：八億ドル上回りました。一方、調整後粗利率の見通しは五十六パーセントで、第二四半期から横ばいです。
  - 主要視覚機能：Explain
  - 画面状態：Chart
  - Visual Grammar：evidence / continuation
  - Visual Template ID：metric-comparison-board
  - Template Variant：default
  - 入力構造：会社見通し 130億ドル / 市場予想 125.2億ドル / 粗利率 56%
  - 画面の問い：Q3見通しは市場予想を超えたか
  - 主要要素：Q3売上見通しと粗利率
  - 視聴者向けテキスト：会社見通し 130億ドル / 市場予想 125.2億ドル / 粗利率 56%
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-004

### 完成ナレーション

確認できた数字を置きます。前の四半期にAMDが示していた第二四半期売上の中心値は百十二億ドルでした。実績は百十五・四億ドルで、中心値を三・四億ドル上回りました。データセンター売上の六十七・二億ドルも、前年から二倍超です。

さらに第三四半期の売上見通しは約百三十億ドル。Reutersが示した市場予想百二十五・二億ドルを四・八億ドル上回りました。一方、調整後粗利率の見通しは五十六パーセントで、第二四半期から横ばいです。


- ナレーションで示す出典主体・媒体：AMD IR / Reuters
- 大テロップ：Q3見通し 130億ドル
- 補助テロップ：市場予想 125.2億ドル / Q2売上 115.4億ドル
- 使用する数字：市場予想 125.2億ドル / Q2売上 115.4億ドル
- 画面で見せる内容：Q2会社見通しと実績; Q3売上見通しと粗利率
- 根拠：AMD IR / Reuters
- 不確実性：非GAAP粗利率とGAAP数値を混同しない

## B4. Scene 4｜Expected / Actual / Gap

- 目的：通常の予想超過と高まったAI期待の未達を分ける
- 目安時間：執筆目安のみ。実測はTTS後
- 因果の対象：lead-stock
- 狐の演技意図：矛盾を一段深い評価軸へ変える
- 狐の表情：分析
- 表情切り替え：『ところが』で警戒へ
- 画面モード：expected-actual-gap
- 前後の接続文：普通のExpectedは、第三四半期売上が百二十五・二億ドル前後になることでした。

### Visual Beats

- **scene-04-beat-001**
  - 開始合図：普通のExpectedは、第三四半期売上が百二十五・二億ドル前後になることでした。Actualの
  - 終了合図：。数字のGapはプラスです。第二四半期実績も会社の事前見通しを上回りました。ここまでは合格です。
  - 主要視覚機能：Explain
  - 画面状態：Chart
  - Visual Grammar：gap / major-shift
  - Visual Template ID：expected-actual-gap-flow
  - Template Variant：default
  - 入力構造：Expected 125.2億ドル / Actual 130億ドル / Gap +4.8億ドル
  - 画面の問い：通常予想とのGapは何か
  - 主要要素：Expected / Actual / Gap
  - 視聴者向けテキスト：Expected 125.2億ドル / Actual 130億ドル / Gap +4.8億ドル
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-004

- **scene-04-beat-002**
  - 開始合図：ところがReutersは、最近の大型AI提携と株価上昇で、投資家がさらに大きなAIの回収を求めて
  - 終了合図：。つまり通常の予想には勝ったのに、高くなった採点基準には届かなかった。これが株価とのGapです。
  - 主要視覚機能：Explain
  - 画面状態：Data
  - Visual Grammar：evidence / continuation
  - Visual Template ID：evidence-boundary
  - Template Variant：default
  - 入力構造：確認済み：売上・見通しは上振れ / 報道解釈：AIの追加証拠が不足
  - 画面の問い：確認済みと市場解釈をどう分けるか
  - 主要要素：数値超過と期待未達の境界
  - 視聴者向けテキスト：確認済み：売上・見通しは上振れ / 報道解釈：AIの追加証拠が不足
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-004, source-005

### 完成ナレーション

普通のExpectedは、第三四半期売上が百二十五・二億ドル前後になることでした。Actualの会社見通しは百三十億ドル。数字のGapはプラスです。第二四半期実績も会社の事前見通しを上回りました。ここまでは合格です。

ところがReutersは、最近の大型AI提携と株価上昇で、投資家がさらに大きなAIの回収を求めていたと伝えています。実際には粗利率見通しが横ばいで、供給制約も残りました。つまり通常の予想には勝ったのに、高くなった採点基準には届かなかった。これが株価とのGapです。


- ナレーションで示す出典主体・媒体：Reuters / AMD IR
- 大テロップ：数字のGapはプラス
- 補助テロップ：期待のGapはマイナス / 普通の合格点では足りなかった
- 使用する数字：なし
- 画面で見せる内容：Expected / Actual / Gap; 数値超過と期待未達の境界
- 根拠：Reuters / AMD IR
- Expectedの根拠区分：アナリストコンセンサス＋主要報道の市場解釈。数値Expectedと高まった期待を混在させない
- 不確実性：『高まった期待』は主要報道による市場解釈で、公式コンセンサス値ではない

## B5. Scene 5｜世界からNASDAQへの経路

- 目的：SpaceXの採用判断が半導体競争へ届く経路を示す
- 目安時間：執筆目安のみ。実測はTTS後
- 因果の対象：sector
- 狐の演技意図：NVIDIAカードで世界ニュースを実体化する
- 狐の表情：軽い驚き
- 表情切り替え：『重要なのは』で分析へ
- 画面モード：text-focus
- 前後の接続文：では、なぜNVIDIAだけ上がったのか。

### Visual Beats

- **scene-05-beat-001**
  - 開始合図：では、なぜNVIDIAだけ上がったのか。SpaceXは八月四日の初めての公開決算説明会で、今後は
  - 終了合図：けを使う方針を示しました。イーロン・マスク氏は次世代のVera Rubinを高く評価しています。
  - 主要視覚機能：Anchor
  - 画面状態：EntityFocus
  - Visual Grammar：entity / major-shift
  - Visual Template ID：entity-card-full
  - Template Variant：prebuilt-card
  - 入力構造：NVIDIA / SpaceXがGPUを専属採用
  - 画面の問い：比較対象の勝者候補は誰か
  - 主要要素：NVIDIA企業カード
  - 視聴者向けテキスト：NVIDIA / SpaceXがGPUを専属採用
  - 使用アセットID：company_nvda
  - アセット状態：ready
  - 表示後の復帰先：Data
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-007

- **scene-05-beat-002**
  - 開始合図：重要なのは、有名人の一言だけではありません。SpaceXは計算能力を年末の二ギガワットから、二〇
  - 終了合図：広げる計画を示しました。大規模な利用者が、次の増設先をNVIDIAへ固定したという採用証拠です。
  - 主要視覚機能：Explain
  - 画面状態：Chart
  - Visual Grammar：causal / continuation
  - Visual Template ID：causal-lane
  - Template Variant：default
  - 入力構造：SpaceX計算増設 / NVIDIA専属採用 / 将来需要の具体化
  - 画面の問い：SpaceXの発言はどう半導体評価へ届くか
  - 主要要素：顧客採用から受注期待への経路
  - 視聴者向けテキスト：SpaceX計算増設 / NVIDIA専属採用 / 将来需要の具体化
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-006, source-007

- **scene-05-beat-003**
  - 開始合図：このニュースはAMDの売上成長を消しません。ただ、同じ夜にNVIDIAへ具体的な顧客証拠が加わっ
  - 終了合図：Aへ具体的な顧客証拠が加わったため、AMDには『成長している』より一段強い証明が要求されました。
  - 主要視覚機能：Explain
  - 画面状態：Data
  - Visual Grammar：bridge-text / continuation
  - Visual Template ID：text-focus
  - Template Variant：default
  - 入力構造：AMDの成長は事実 / 相対評価ではNVIDIAが優位
  - 画面の問い：AMDの成長とどう両立するか
  - 主要要素：成長は確認、競争証拠はNVIDIA
  - 視聴者向けテキスト：AMDの成長は事実 / 相対評価ではNVIDIAが優位
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-004, source-005, source-007

### 完成ナレーション

では、なぜNVIDIAだけ上がったのか。SpaceXは八月四日の初めての公開決算説明会で、今後はNVIDIAのGPUだけを使う方針を示しました。イーロン・マスク氏は次世代のVera Rubinを高く評価しています。

重要なのは、有名人の一言だけではありません。SpaceXは計算能力を年末の二ギガワットから、二〇二七年に約十ギガワットへ広げる計画を示しました。大規模な利用者が、次の増設先をNVIDIAへ固定したという採用証拠です。

このニュースはAMDの売上成長を消しません。ただ、同じ夜にNVIDIAへ具体的な顧客証拠が加わったため、AMDには『成長している』より一段強い証明が要求されました。


- ナレーションで示す出典主体・媒体：SpaceX IR / MarketWatch / Reuters
- 大テロップ：SpaceXはNVIDIA専属
- 補助テロップ：Vera Rubinを評価 / 計算能力 2GW → 約10GW計画
- 使用する数字：計算能力 2GW → 約10GW計画
- 画面で見せる内容：NVIDIA企業カード; 顧客採用から受注期待への経路; 成長は確認、競争証拠はNVIDIA
- 根拠：SpaceX IR / MarketWatch / Reuters
- 不確実性：将来のGPU購入額は確定値として扱わない

## B6. Scene 6｜値動きが示したこと

- 目的：発表順と終値を使い、主役反応とNASDAQ全体を分ける
- 目安時間：執筆目安のみ。実測はTTS後
- 因果の対象：multiple
- 狐の演技意図：時系列の限界を明示しながら結論を絞る
- 狐の表情：警戒
- 表情切り替え：『ただし』で通常へ
- 画面モード：timeline
- 前後の接続文：順番も確認します。

### Visual Beats

- **scene-06-beat-001**
  - 開始合図：順番も確認します。SpaceXの説明会は八月四日午後四時半、AMDの説明会は五時でした。AMD株
  - 終了合図：ーセント安で終えました。NVIDIAは三・四三パーセント高、SOXXは二・一二パーセント安です。
  - 主要視覚機能：Explain
  - 画面状態：Chart
  - Visual Grammar：reaction / major-shift
  - Visual Template ID：event-reaction-timeline
  - Template Variant：default
  - 入力構造：16:30 ET SpaceX説明会 / 17:00 ET AMD説明会 / 翌日 AMD -7.04% / NVDA +3.43%
  - 画面の問い：発表と価格反応の順番は何か
  - 主要要素：SpaceX→AMD→翌日終値
  - 視聴者向けテキスト：16:30 ET SpaceX説明会 / 17:00 ET AMD説明会 / 翌日 AMD -7.04% / NVDA +3.43%
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-001, source-003, source-004, source-006

- **scene-06-beat-002**
  - 開始合図：ただし、分足データがないので、どの発言が何分に何パーセント動かしたとは言えません。またNASDA
  - 終了合図：三パーセント安、Microsoftも一・〇九パーセント安で、大型テックの別の弱さが重なりました。
  - 主要視覚機能：Explain
  - 画面状態：Data
  - Visual Grammar：reaction / continuation
  - Visual Template ID：market-pulse-grid
  - Template Variant：default
  - 入力構造：SOXX -2.12% / Alphabet -4.03% / Microsoft -1.09%
  - 画面の問い：AMDとNASDAQ全体をどう分けるか
  - 主要要素：主役反応と大型テック別要因
  - 視聴者向けテキスト：SOXX -2.12% / Alphabet -4.03% / Microsoft -1.09%
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-001, source-008

### 完成ナレーション

順番も確認します。SpaceXの説明会は八月四日午後四時半、AMDの説明会は五時でした。AMD株は決算後の時間外で約九パーセント下落し、翌日の通常取引を七・〇四パーセント安で終えました。NVIDIAは三・四三パーセント高、SOXXは二・一二パーセント安です。

ただし、分足データがないので、どの発言が何分に何パーセント動かしたとは言えません。またNASDAQ全体の下落をAMD一社では説明できません。Alphabetは四・〇三パーセント安、Microsoftも一・〇九パーセント安で、大型テックの別の弱さが重なりました。


- ナレーションで示す出典主体・媒体：AMD IR / SpaceX IR / Reuters / 当日の市場データ
- 大テロップ：発表順と終値
- 補助テロップ：AMD 引け後 約-9% / 翌日 AMD -7.04% / NVDA +3.43%
- 使用する数字：AMD 引け後 約-9% / 翌日 AMD -7.04% / NVDA +3.43%
- 画面で見せる内容：SpaceX→AMD→翌日終値; 主役反応と大型テック別要因
- 根拠：AMD IR / SpaceX IR / Reuters / 当日の市場データ
- 時系列の根拠：SpaceX IR、AMD IR、Reuters、Longbridge終値。分足データなし
- 不確実性：分足がないため発言ごとの瞬間的寄与は断定しない

## B7. Scene 7｜反対材料と銘柄差

- 目的：仮説の限界を三銘柄比較で示す
- 目安時間：執筆目安のみ。実測はTTS後
- 因果の対象：multiple
- 狐の演技意図：選別という言葉を断定せず、確認範囲を示す
- 狐の表情：困惑
- 表情切り替え：『だから』で分析へ
- 画面モード：number-comparison
- 前後の接続文：三つだけ並べます。

### Visual Beats

- **scene-07-beat-001**
  - 開始合図：三つだけ並べます。NVIDIAは三・四三パーセント高。AMDは七・〇四パーセント安。Alphab
  - 終了合図：phabetは四・〇三パーセント安でした。AIという共通語だけでは、この三方向を説明できません。
  - 主要視覚機能：Explain
  - 画面状態：Chart
  - Visual Grammar：comparison / major-shift
  - Visual Template ID：diverging-stock-bars
  - Template Variant：default
  - 入力構造：NVIDIA +3.43% / AMD -7.04% / Alphabet -4.03%
  - 画面の問い：三銘柄の反応差は何を示すか
  - 主要要素：NVIDIA・AMD・Alphabet比較
  - 視聴者向けテキスト：NVIDIA +3.43% / AMD -7.04% / Alphabet -4.03%
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-001

- **scene-07-beat-002**
  - 開始合図：だから昨夜を『AI全面安』とも『NVIDIAがNASDAQを全部動かした』とも言えません。確認で
  - 終了合図：oftの下落も重なったことです。Dowが上昇した混合相場だった点も、単一原因への断定を弱めます。
  - 主要視覚機能：Explain
  - 画面状態：Data
  - Visual Grammar：comparison / continuation
  - Visual Template ID：dual-asset-split
  - Template Variant：default
  - 入力構造：半導体：採用証拠の差 / NASDAQ：大型テック安も重なる / Dow +0.5%の混合相場
  - 画面の問い：どこまで因果を言えるか
  - 主要要素：半導体の相対評価とNASDAQ別要因
  - 視聴者向けテキスト：半導体：採用証拠の差 / NASDAQ：大型テック安も重なる / Dow +0.5%の混合相場
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-001, source-008

### 完成ナレーション

三つだけ並べます。NVIDIAは三・四三パーセント高。AMDは七・〇四パーセント安。Alphabetは四・〇三パーセント安でした。AIという共通語だけでは、この三方向を説明できません。

だから昨夜を『AI全面安』とも『NVIDIAがNASDAQを全部動かした』とも言えません。確認できるのは、半導体では顧客採用の証拠がNVIDIAへ寄り、NASDAQ全体ではAlphabetやMicrosoftの下落も重なったことです。Dowが上昇した混合相場だった点も、単一原因への断定を弱めます。


- ナレーションで示す出典主体・媒体：当日の市場データ / AP
- 大テロップ：AI株は一方向ではない
- 補助テロップ：NVIDIA +3.43% / AMD -7.04% / Alphabet -4.03%
- 使用する数字：NVIDIA +3.43% / AMD -7.04% / Alphabet -4.03%
- 画面で見せる内容：NVIDIA・AMD・Alphabet比較; 半導体の相対評価とNASDAQ別要因
- 根拠：当日の市場データ / AP
- 不確実性：Alphabet安の全要因をAI人事だけへ帰属しない

## B8. Scene 8｜今夜の検証ポイント

- 目的：仮説が強まる条件と弱まる条件を対で示す
- 目安時間：執筆目安のみ。実測はTTS後
- 因果の対象：multiple
- 狐の演技意図：予言せず、次に確認する場所を案内する
- 狐の表情：通常
- 表情切り替え：なし
- 画面モード：verification
- 前後の接続文：僕たちが次に見るのは三点です。

### Visual Beats

- **scene-08-beat-001**
  - 開始合図：僕たちが次に見るのは三点です。第一に、AMDがSpaceX級の大型導入を新たに取れるか。第二に、
  - 終了合図：WoSの供給制約が緩むか。第三に、半導体の上昇がNVIDIA一社からSOXX全体へ広がるかです。
  - 主要視覚機能：Explain
  - 画面状態：Data
  - Visual Grammar：verification / major-shift
  - Visual Template ID：verification-matrix
  - Template Variant：default
  - 入力構造：大型顧客の獲得 / 粗利率・供給制約 / SOXXへの広がり
  - 画面の問い：仮説を何で検証するか
  - 主要要素：三つの検証軸
  - 視聴者向けテキスト：大型顧客の獲得 / 粗利率・供給制約 / SOXXへの広がり
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-004, source-005, source-007

- **scene-08-beat-002**
  - 開始合図：AMDの顧客獲得と利益率が改善し、半導体全体が反応すれば、昨夜の相対評価は弱まります。反対に、大
  - 終了合図：DIAへ集中し、AMDの利益率が横ばいなら、需要の量より受注の確実性を重く見る仮説が強まります。
  - 主要視覚機能：Explain
  - 画面状態：Data
  - Visual Grammar：verification / continuation
  - Visual Template ID：verification-checklist
  - Template Variant：default
  - 入力構造：弱まる：AMDの受注・利益率・セクター反応が改善 / 強まる：大型採用がNVIDIAへ集中
  - 画面の問い：仮説が弱まる条件は何か
  - 主要要素：強まる条件と弱まる条件
  - 視聴者向けテキスト：弱まる：AMDの受注・利益率・セクター反応が改善 / 強まる：大型採用がNVIDIAへ集中
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-001, source-005

### 完成ナレーション

僕たちが次に見るのは三点です。第一に、AMDがSpaceX級の大型導入を新たに取れるか。第二に、粗利率が五十六パーセントから上向き、N3やCoWoSの供給制約が緩むか。第三に、半導体の上昇がNVIDIA一社からSOXX全体へ広がるかです。

AMDの顧客獲得と利益率が改善し、半導体全体が反応すれば、昨夜の相対評価は弱まります。反対に、大型AI設備の採用がNVIDIAへ集中し、AMDの利益率が横ばいなら、需要の量より受注の確実性を重く見る仮説が強まります。


- ナレーションで示す出典主体・媒体：AMD / Reuters / 当日の市場データ
- 大テロップ：次に見る3点
- 補助テロップ：AMDの大型顧客 / 粗利率と供給制約 / NVIDIA以外への広がり
- 使用する数字：なし
- 画面で見せる内容：三つの検証軸; 強まる条件と弱まる条件
- 根拠：AMD / Reuters / 当日の市場データ
- 不確実性：検証条件であり株価予測ではない

## B9. Scene 9｜いってらっしゃい、おやすみ

- 目的：中心結論を回収し固定エンディングへつなぐ
- 目安時間：執筆目安のみ。実測はTTS後
- 因果の対象：multiple
- 狐の演技意図：安心できる温度で短く締める
- 狐の表情：眠そう
- 表情切り替え：なし
- 画面モード：closing-recap
- 前後の接続文：昨夜は、AMDの数字が悪かったのではなく、AI競争で要求される証拠が一段上がった夜でした。

### Visual Beats

- **scene-09-beat-001**
  - 開始合図：昨夜は、AMDの数字が悪かったのではなく、AI競争で要求される証拠が一段上がった夜でした。NVI
  - 終了合図：NASDAQカフェでした。今日も気をつけて、いってらっしゃい。こちらはそろそろ、おやすみなさい。
  - 主要視覚機能：Anchor
  - 画面状態：Data
  - Visual Grammar：assembly / closing
  - Visual Template ID：closing-recap
  - Template Variant：default
  - 入力構造：AMD：予想超過でも下落 / NVIDIA：SpaceX採用で上昇 / NASDAQ：大型テック安も重なる
  - 画面の問い：今朝の結論は何か
  - 主要要素：本編の三点回収
  - 視聴者向けテキスト：AMD：予想超過でも下落 / NVIDIA：SpaceX採用で上昇 / NASDAQ：大型テック安も重なる
  - 使用アセットID：not-required
  - アセット状態：not-required
  - 表示後の復帰先：該当なし
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：source-001, source-004, source-005, source-007, source-008

### 完成ナレーション

昨夜は、AMDの数字が悪かったのではなく、AI競争で要求される証拠が一段上がった夜でした。NVIDIAにはSpaceXの採用が加わり、AMDには次の大型受注と利益率の改善が求められています。以上、朝のNASDAQカフェでした。今日も気をつけて、いってらっしゃい。こちらはそろそろ、おやすみなさい。


- ナレーションで示す出典主体・媒体：本編の回収
- 大テロップ：数字より、次の受注証拠
- 補助テロップ：AMDは予想超過でも下落 / NVIDIAはSpaceX採用で上昇 / NASDAQ安は大型テック別要因も
- 使用する数字：なし
- 画面で見せる内容：本編の三点回収
- 根拠：本編の回収
- 不確実性：新情報は追加しない

## C. タイトル
- 推奨案：AMD好決算でも7%安　NVIDIAだけ上がったAI半導体の採点表
- 候補2：予想超えでも売られたAMD　SpaceXが変えた半導体の評価
- 候補3：NASDAQ -0.83%　AI需要より重かった『次の大型受注』

## D. サムネイル文言
- 推奨案：好決算でも7%安
- 候補2：NVIDIAだけ上昇
- 候補3：採点基準が変わった

## E. 概要欄

昨夜のNasdaq Compositeは0.83%下落し、SOXXは2.12%安でした。AMDは売上と次四半期見通しで通常予想を上回ったのに7.04%下落し、NVIDIAはSpaceXの専属採用方針を材料に3.43%上昇しました。動画では、AMDの決算数値、Expected / Actual / Gap、SpaceXから半導体競争への経路、Alphabet・Microsoft安を含むNASDAQ全体の別要因を分けて確認します。今後はAMDの大型顧客、粗利率と供給制約、SOXXへの広がりを検証します。本動画はニュース解説であり、個別銘柄の売買を勧めるものではありません。

## F. 制作上の注意
- アセット完成ゲート：mainBackground、狐7表情、company_amd、company_nvdaは既存レジストリready。
- 画面多様性ゲート：Data / Chart / EntityFocus、非分析2Beat、前後半major-shiftあり。
- 人物・企業・製品カード一覧：company_amd（Scene 2）、company_nvda（Scene 5）。
- FoxPictureBookIllustration一覧：not-required。たとえ画像を必要とする比喩を採用していない。
- 画像生成結果と採用経路：not-required。
- 素材不足と停止事項：正式validatorのCI検証対象。previewはvalidator合格後にのみ実行する。
- 訂正事項：collectorの`SOX`欄はsource_symbol `SOXX.US`のため、全成果物でSOXX ETFと表記する。
- 読み方：AMD=エーエムディー、NVIDIA=エヌビディア、SOXX=ソックス、Vera Rubin=ヴェラ・ルービン、CoWoS=コウォス。
- 実装時に変更禁止：AMDの通常予想超過と高まった期待未達の分離、AMD一社とNASDAQ全体要因の分離、分足欠損の留保、selected_path=not-required。

## G. 使用情報源
- source-001｜朝のNASDAQカフェ source collector｜NASDAQ Cafe Source Pack 2026-08-06｜source_pack.json｜用途：Nasdaq Composite、SOXX、ウォッチ銘柄の終値と騰落率 / 取得制約と欠損項目
- source-002｜AMD Investor Relations｜AMD Reports First Quarter 2026 Financial Results｜https://ir.amd.com/news-events/press-releases/detail/1284/amd-reports-first-quarter-2026-financial-results｜用途：Q2会社ガイダンス110〜115億ドル、中心112億ドル / Q2非GAAP粗利率見通し56%
- source-003｜AMD Investor Relations｜AMD to Report Fiscal Second Quarter 2026 Financial Results｜https://ir.amd.com/news-events/press-releases/detail/1289/amd-to-report-fiscal-second-quarter-2026-financial-results｜用途：AMD決算発表が8月4日引け後、説明会が17時ET
- source-004｜Reuters｜AMD's AI-powered revenue forecast fails to wow investors｜https://www.reuters.com/business/amd-forecasts-upbeat-revenue-ai-data-center-demand-beats-quarterly-estimates-2026-08-04/｜用途：Q2売上115.4億ドル、データセンター67.2億ドル / Q3売上見通し約130億ドルと市場予想125.2億ドル / 引け後約9%下落
- source-005｜Reuters｜AMD falls as investors demand bigger AI payoff｜https://www.reuters.com/business/amd-falls-investors-seek-bigger-ai-payoff-2026-08-05/｜用途：通常予想を超えても高まったAI期待に届かなかったとの市場解釈 / 供給制約とSpaceXのNVIDIA専属採用がAMDの相対評価を弱めたこと
- source-006｜SpaceX Investor Relations｜SpaceX to Post Second Quarter 2026 Results and Host Webcast on August 4, 2026｜https://ir.spacex.com/updates/releases-details/2026/SpaceX-to-Post-Second-Quarter-2026-Results-and-Host-Webcast-on-August-4-2026-2026-g8layJlbFm/default.aspx｜用途：SpaceX説明会が8月4日16時30分ET
- source-007｜MarketWatch｜Nvidia's stock is basking in the glow of a high-profile endorsement｜https://www.marketwatch.com/story/nvidias-stock-is-basking-in-the-glow-of-a-high-profile-endorsement-b7c48e7b｜用途：SpaceXがNVIDIA GPUだけを使うとの発言 / Vera Rubin評価、計算能力2GWから2027年約10GW計画 / NVIDIA上昇の報道解釈
- source-008｜Associated Press｜US stocks hold near records on hopes of an agreement with Iran｜https://apnews.com/article/53179dc1c0148c5afeb47379b8f5b5c5｜用途：NASDAQ下落にはAlphabetとMicrosoft安も重なったこと / Dow上昇を含む混合相場
- memory-001｜nasdaq-plot-creator editorial memory｜Claim ledger: AI設備投資の評価軸｜editorial-memory/claim_ledger.json#ai-capex-evaluation-axis｜用途：過去回との差分確認のみ。現在証拠として不使用

## H. 04 興味深さ・わかりやすさ審問結果
- 判定：合格（内容審問・修正反映済み）。
- 得点：29 / 30
- 冒頭フック：5
- Scene間の進展：5
- 見出し以上の発見：5
- わかりやすさ：5
- 狐らしさ：4
- 最後まで見る理由：5
- 最大の離脱候補：Scene 4で数値コンセンサスと高まった期待を混同する可能性。
- 必須修正と反映結果：『数字のGapはプラス、期待のGapはマイナス』へ分離。Scene 6でAMDとNASDAQ全体を分離。
- タイトル・サムネイルの約束と回収：Scene 2〜5で『好決算でも7%安』『NVIDIAだけ上昇』を回収。
- 即時不合格条件：該当なし。
- 実行正本整合ゲート：ローカルpass。正式CIで再検証する。
- GitHub Actionsへ渡す条件：正式validator合格後にpreviewへ進む。
