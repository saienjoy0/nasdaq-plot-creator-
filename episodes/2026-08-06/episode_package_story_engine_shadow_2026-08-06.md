# 朝のNASDAQカフェ｜2026-08-06 Story Engine Shadow制作パッケージ

## A. エピソード概要
- 対象日：2026-08-06
- 市場セッション：2026-08-05 US market
- モード：shadow A/B。render_specと本番動画には未接続
- エピソード種別：単独ニュース＋増幅要因
- 主役ニュース：AMDの好決算後下落
- 対象指数：Nasdaq Composite / SOXX
- ストーリーの背骨：AMDは売上と見通しで通常予想を超えたのに、高まったAI期待とSpaceXのNVIDIA専属採用によって競争上の追加証拠が不足したと評価され下落し、その半導体安にAlphabetとMicrosoftの下落も重なってNASDAQは0.83%下落した。
- 中心仮説：昨夜のAI半導体市場は需要の有無ではなく、次の巨大需要を誰が確実に取るかを評価し、通常予想を超えたAMDよりSpaceXの採用証拠を得たNVIDIAを高く評価した。
- Expected：Q3売上約125.2億ドル。主要報道では大型顧客・AI投資回収・利益率の追加証拠も注目
- Actual：Q3見通し約130億ドル、Q2売上115.4億ドル、DC67.2億ドル、AMD -7.04%、SpaceX採用証拠はNVIDIA
- Gap：数値Gap +4.8億ドル。高まったAI期待の追加証拠は不足との市場解釈
- 確信度：Medium
- 重要な反対材料：AMD通常予想超過、NVIDIA上昇、Dow上昇、金利・VIX・分足不足
- 画像採用経路：not-required
- Visual Beat総数：18

### Story Engine progression
| Scene | Story role | 理解の更新 |
|---|---|---|
| 1 | Hook | 好決算なのにAMDだけ急落した問いを残す |
| 2 | Proof | 悪決算という単純説明を退ける |
| 3 | Complication | 数値Gapはプラスなのに株価は逆方向 |
| 4 | Turn | 通常予想とは別のAI競争テストが見える |
| 5 | Reveal | NVIDIAへSpaceX採用証拠が加わった |
| 6 | Boundary | 時系列は整合するが分足因果は断定不可 |
| 7 | Counterevidence | NASDAQ全体はAMD一社で説明できない |
| 8 | Implication | 仮説が強まる・弱まる条件を示す |
| 9 | Callback | 冒頭の矛盾を受注証拠の差として再解釈 |

## B1. Scene 1｜寝ている間に何が起きた？

- Story role：hook
- 視聴者の理解 Before：数字は良かったのに売られた理由はまだ分からない
- 視聴者の理解 After：矛盾を一つの問いへ絞る
- 狐の演技意図：軽い驚き
- 狐の表情：軽い驚き
- 画面状態列：Data → Data
- 接続：冒頭

### Visual Beats
- **scene-01-beat-001**
  - 画面状態：Data
  - Visual Template ID：opening-contradiction
  - 画面の問い：NASDAQ -0.83%
  - 視聴者向けテキスト：NASDAQ -0.83%
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-001,E-004
- **scene-01-beat-002**
  - 画面状態：Data
  - Visual Template ID：question-card
  - 画面の問い：SOXX -2.12% / NVIDIA +3.43% / AMD -7.04%
  - 視聴者向けテキスト：SOXX -2.12% / NVIDIA +3.43% / AMD -7.04%
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-001,E-004

### 完成ナレーション

おはようございます。僕が昨夜の数字を開いて最初に引っかかったのは、この逆方向でした。Nasdaq Compositeは〇・八三パーセント安、半導体ETFのSOXXは二・一二パーセント安。ところがNVIDIAは三・四三パーセント上昇し、AMDは七・〇四パーセント下落しました。

しかもAMDの売上見通しは、市場予想を上回っていました。良い数字なのに、なぜ七パーセントも売られたのか。今朝は、この矛盾を一つずつほどきます。

- 大テロップ：NASDAQ -0.83%
- 補助テロップ：SOXX -2.12% / NVIDIA +3.43% / AMD -7.04%
- 使用する数字：SOXX -2.12% / NVIDIA +3.43% / AMD -7.04%
- 根拠ID：E-001,E-004
- 不確実性：終値中心。ここでは原因を確定しない。

## B2. Scene 2｜今朝の矛盾

- Story role：proof
- 視聴者の理解 Before：悪い決算だったから下落したのだろう
- 視聴者の理解 After：悪決算という単純説明を数字で退ける
- 狐の演技意図：分析
- 狐の表情：分析
- 画面状態列：EntityFocus → Chart
- 接続：前Sceneの未解決点からBUT / THEREFOREで接続

### Visual Beats
- **scene-02-beat-001**
  - 画面状態：EntityFocus
  - Visual Template ID：entity-card-full
  - 画面の問い：悪決算ではない
  - 視聴者向けテキスト：悪決算ではない
  - 使用アセットID：company_amd
  - アセット状態：ready
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-002,E-004
- **scene-02-beat-002**
  - 画面状態：Chart
  - Visual Template ID：metric-comparison-board
  - 画面の問い：Q3見通し 130億ドル / 予想 125.2億ドル
  - 視聴者向けテキスト：Q3見通し 130億ドル / 予想 125.2億ドル
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-002,E-004

### 完成ナレーション

最初に消しておきたい説明は、『AMDの決算が悪かった』です。第二四半期売上は百十五・四億ドル。データセンター売上は六十七・二億ドルで、前年の二倍を超えました。

第三四半期の売上見通しも約百三十億ドルで、Reutersが示した市場予想百二十五・二億ドルを約四・八億ドル上回っています。悪決算だから下がった、では説明が合いません。どうやら市場は、答案だけでなく別の採点表も持っていたようです。

- 大テロップ：悪決算ではない
- 補助テロップ：Q3見通し 130億ドル / 予想 125.2億ドル
- 使用する数字：Q3見通し 130億ドル / 予想 125.2億ドル
- 根拠ID：E-002,E-004
- 不確実性：市場予想はReuters記載値。

## B3. Scene 3｜何が起きた？

- Story role：complication
- 視聴者の理解 Before：予想を上回れば普通は十分なはず
- 視聴者の理解 After：数値Gapはプラスなのに価格反応は逆だと理解する
- 狐の演技意図：困惑
- 狐の表情：困惑
- 画面状態列：Chart → Data
- 接続：前Sceneの未解決点からBUT / THEREFOREで接続

### Visual Beats
- **scene-03-beat-001**
  - 画面状態：Chart
  - Visual Template ID：expected-actual-gap-flow
  - 画面の問い：数字のGapはプラス
  - 視聴者向けテキスト：数字のGapはプラス
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-002,E-004,E-001
- **scene-03-beat-002**
  - 画面状態：Data
  - Visual Template ID：diverging-stock-bars
  - 画面の問い：それでも AMD -7.04%
  - 視聴者向けテキスト：それでも AMD -7.04%
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-002,E-004,E-001

### 完成ナレーション

普通のExpectedは、第三四半期売上が百二十五・二億ドル前後になることでした。Actualは約百三十億ドル。数字のGapはプラスです。会社の以前の第二四半期見通しと比べても、実績は上振れでした。

それでも時間外で約九パーセント下げ、翌日も七・〇四パーセント安です。入力は合格なのに、出力が落第。ソフトウェアなら、途中に別のテストケースが追加されたと疑う場面です。では市場は、何を追加で試していたのか。

- 大テロップ：数字のGapはプラス
- 補助テロップ：それでも AMD -7.04%
- 使用する数字：それでも AMD -7.04%
- 根拠ID：E-002,E-004,E-001
- 不確実性：IT比喩は理解補助。分足寄与は未確認。

## B4. Scene 4｜Expected / Actual / Gap

- Story role：turn
- 視聴者の理解 Before：追加テストの中身はまだ不明
- 視聴者の理解 After：通常予想とは別に大型顧客・利益率・AI回収の証拠が求められたと理解する
- 狐の演技意図：警戒
- 狐の表情：警戒
- 画面状態列：Data → Chart
- 接続：前Sceneの未解決点からBUT / THEREFOREで接続

### Visual Beats
- **scene-04-beat-001**
  - 画面状態：Data
  - Visual Template ID：evidence-boundary
  - 画面の問い：普通の予想には勝った
  - 視聴者向けテキスト：普通の予想には勝った
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-004,E-005
- **scene-04-beat-002**
  - 画面状態：Chart
  - Visual Template ID：evaluation-axis-shift
  - 画面の問い：高まったAI期待の証拠は不足
  - 視聴者向けテキスト：高まったAI期待の証拠は不足
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-004,E-005

### 完成ナレーション

Reutersが伝えた市場の解釈は、ここです。投資家は売上成長だけでなく、大型顧客、AI投資の回収、利益率の追加証拠を求めていました。一方、調整後粗利率の見通しは五十六パーセントで横ばい。供給制約への懸念も残りました。

つまり、公式の数値テストには合格した。でも、最近高くなったAI競争のテストでは、証明が足りないと見られた可能性があります。ここで初めて、好決算と下落が同じ画面に入ります。

- 大テロップ：普通の予想には勝った
- 補助テロップ：高まったAI期待の証拠は不足
- 使用する数字：高まったAI期待の証拠は不足
- 根拠ID：E-004,E-005
- 不確実性：高まった期待は主要報道の市場解釈。公式コンセンサス値ではない。

## B5. Scene 5｜世界からNASDAQへの経路

- Story role：reveal
- 視聴者の理解 Before：AMD側の不足だけが理由かもしれない
- 視聴者の理解 After：同じ夜にNVIDIAへSpaceX採用証拠が加わり相対差が見えたと理解する
- 狐の演技意図：軽い驚き
- 狐の表情：軽い驚き
- 画面状態列：EntityFocus → Chart
- 接続：前Sceneの未解決点からBUT / THEREFOREで接続

### Visual Beats
- **scene-05-beat-001**
  - 画面状態：EntityFocus
  - Visual Template ID：entity-card-full
  - 画面の問い：SpaceXはNVIDIAを採用
  - 視聴者向けテキスト：SpaceXはNVIDIAを採用
  - 使用アセットID：company_nvda
  - アセット状態：ready
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-006,E-007,E-004
- **scene-05-beat-002**
  - 画面状態：Chart
  - Visual Template ID：causal-lane
  - 画面の問い：成長数字 vs 次の顧客証拠
  - 視聴者向けテキスト：成長数字 vs 次の顧客証拠
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-006,E-007,E-004

### 完成ナレーション

そして同じ夜、比較相手のNVIDIAには具体的な証拠が一つ増えました。SpaceXが今後、NVIDIAのGPUだけを使う方針を示したと報じられたことです。

これはAMDの成長を否定するニュースではありません。ただ、大規模な利用者が『次もNVIDIAを選ぶ』と示した。AMDには成長の数字、NVIDIAには次の採用証拠。昨夜の明暗は、この一段の差で説明しやすくなります。

- 大テロップ：SpaceXはNVIDIAを採用
- 補助テロップ：成長数字 vs 次の顧客証拠
- 使用する数字：成長数字 vs 次の顧客証拠
- 根拠ID：E-006,E-007,E-004
- 不確実性：NVIDIA上昇の全要因をSpaceXだけへ帰属しない。

## B6. Scene 6｜値動きが示したこと

- Story role：boundary
- 視聴者の理解 Before：これで全ての値動きを説明できる
- 視聴者の理解 After：発表順は整合するが分足がなく瞬間因果は断定できないと理解する
- 狐の演技意図：慎重
- 狐の表情：慎重
- 画面状態列：Chart → Data
- 接続：前Sceneの未解決点からBUT / THEREFOREで接続

### Visual Beats
- **scene-06-beat-001**
  - 画面状態：Chart
  - Visual Template ID：event-reaction-timeline
  - 画面の問い：発表順と終値は整合
  - 視聴者向けテキスト：発表順と終値は整合
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-003,E-004,E-006,E-007,E-001,E-009
- **scene-06-beat-002**
  - 画面状態：Data
  - Visual Template ID：evidence-boundary
  - 画面の問い：分足なし：瞬間因果は断定しない
  - 視聴者向けテキスト：分足なし：瞬間因果は断定しない
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-003,E-004,E-006,E-007,E-001,E-009

### 完成ナレーション

時系列も大きくは矛盾しません。SpaceXの説明会は八月四日午後四時半、AMDの説明会は五時。AMDは決算後の時間外で約九パーセント下げ、翌日を七・〇四パーセント安で終えました。NVIDIAは三・四三パーセント高です。

ただし分足がないので、どの発言が何分に何パーセント動かしたとは言えません。ここで言えるのは、採用証拠の差と終値の方向が整合した、というところまでです。

- 大テロップ：発表順と終値は整合
- 補助テロップ：分足なし：瞬間因果は断定しない
- 使用する数字：分足なし：瞬間因果は断定しない
- 根拠ID：E-003,E-004,E-006,E-007,E-001,E-009
- 不確実性：発言ごとの寄与は不明。

## B7. Scene 7｜反対材料とNASDAQ境界

- Story role：counterevidence
- 視聴者の理解 Before：AMDとNVIDIAの差がNASDAQ全体も説明した
- 視聴者の理解 After：NASDAQ安にはAlphabet・Microsoft安も重なりAMD一社は主因にできないと理解する
- 狐の演技意図：分析
- 狐の表情：分析
- 画面状態列：Chart → Data
- 接続：前Sceneの未解決点からBUT / THEREFOREで接続

### Visual Beats
- **scene-07-beat-001**
  - 画面状態：Chart
  - Visual Template ID：market-pulse-grid
  - 画面の問い：AMD一社でNASDAQを説明しない
  - 視聴者向けテキスト：AMD一社でNASDAQを説明しない
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-001,E-008,E-009
- **scene-07-beat-002**
  - 画面状態：Data
  - Visual Template ID：dual-asset-split
  - 画面の問い：Alphabet -4.03% / Microsoft -1.09% / Dow上昇
  - 視聴者向けテキスト：Alphabet -4.03% / Microsoft -1.09% / Dow上昇
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-001,E-008,E-009

### 完成ナレーション

もう一つ、範囲を広げすぎないようにします。SOXXは二・一二パーセント安でしたが、NASDAQ全体の〇・八三パーセント安をAMD一社では説明できません。Alphabetは四・〇三パーセント安、Microsoftも一・〇九パーセント安でした。

一方でDowは上昇しています。昨夜は米国株の全面安でも、AI株の全面安でもありません。半導体では採用証拠の差が見え、NASDAQには別の大型テック安も重なった。ここを一つの原因へ畳むと、説明が壊れます。

- 大テロップ：AMD一社でNASDAQを説明しない
- 補助テロップ：Alphabet -4.03% / Microsoft -1.09% / Dow上昇
- 使用する数字：Alphabet -4.03% / Microsoft -1.09% / Dow上昇
- 根拠ID：E-001,E-008,E-009
- 不確実性：指数寄与度、金利、VIXは不足。

## B8. Scene 8｜今夜の検証ポイント

- Story role：implication
- 視聴者の理解 Before：昨夜の解釈は完成した答えだ
- 視聴者の理解 After：仮説が強まる条件と弱まる条件を具体的に持つ
- 狐の演技意図：通常
- 狐の表情：通常
- 画面状態列：Data → Data
- 接続：前Sceneの未解決点からBUT / THEREFOREで接続

### Visual Beats
- **scene-08-beat-001**
  - 画面状態：Data
  - Visual Template ID：verification-matrix
  - 画面の問い：仮説が弱まる条件
  - 視聴者向けテキスト：仮説が弱まる条件
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-004,E-005,E-007,E-001
- **scene-08-beat-002**
  - 画面状態：Data
  - Visual Template ID：verification-checklist
  - 画面の問い：AMD大型顧客・粗利率・供給 / SOXXへの広がり
  - 視聴者向けテキスト：AMD大型顧客・粗利率・供給 / SOXXへの広がり
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-004,E-005,E-007,E-001

### 完成ナレーション

この見方が正しいかは、次の決算と受注で確かめられます。AMDがSpaceX級の大型顧客を獲得し、粗利率が五十六パーセントから上向けば、『証拠不足』という評価は弱まります。供給制約の改善も同じです。

反対に、大型AI設備の採用がNVIDIAへ集中し、半導体の強さがNVIDIA一社から広がらないなら、需要の量より受注の確実性を重く見た、という仮説は強まります。予言ではなく、次に確かめる場所です。

- 大テロップ：仮説が弱まる条件
- 補助テロップ：AMD大型顧客・粗利率・供給 / SOXXへの広がり
- 使用する数字：AMD大型顧客・粗利率・供給 / SOXXへの広がり
- 根拠ID：E-004,E-005,E-007,E-001
- 不確実性：株価予測や売買判断ではない。

## B9. Scene 9｜いってらっしゃい、おやすみ

- Story role：callback
- 視聴者の理解 Before：好決算なのに下落という不可解な夜だった
- 視聴者の理解 After：普通の予想超過と次の受注証拠の差として冒頭を再解釈する
- 狐の演技意図：眠そう
- 狐の表情：眠そう
- 画面状態列：Data → Data
- 接続：前Sceneの未解決点からBUT / THEREFOREで接続

### Visual Beats
- **scene-09-beat-001**
  - 画面状態：Data
  - Visual Template ID：closing-recap
  - 画面の問い：普通の予想超過だけでは足りない
  - 視聴者向けテキスト：普通の予想超過だけでは足りない
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-001,E-004,E-005,E-007,E-008,E-009
- **scene-09-beat-002**
  - 画面状態：Data
  - Visual Template ID：fixed-ending
  - 画面の問い：次の受注証拠を確認
  - 視聴者向けテキスト：次の受注証拠を確認
  - 使用アセットID：not-required
  - アセット状態：not-required
  - Primary / Approved Fallback：not-required
  - selected_path：not-required
  - 根拠ID：E-001,E-004,E-005,E-007,E-008,E-009

### 完成ナレーション

今朝の矛盾は、AMDの数字が悪かったことではありません。普通の予想には勝った。でも市場が追加で重く見た可能性があるのは、『次の巨大顧客を誰が確実に取るのか』という点でした。そこではSpaceXの採用証拠を得たNVIDIAが一歩先に見えました。

ただし、NASDAQ全体はAMD一社の話ではなく、別の大型テック安も重なっています。答えを一つにしすぎず、次の受注と利益率で確かめる。以上、朝のNASDAQカフェでした。今日も気をつけて、いってらっしゃい。こちらはそろそろ、おやすみなさい。

- 大テロップ：普通の予想超過だけでは足りない
- 補助テロップ：次の受注証拠を確認
- 使用する数字：次の受注証拠を確認
- 根拠ID：E-001,E-004,E-005,E-007,E-008,E-009
- 不確実性：新情報は追加しない。

## C. タイトル
- 推奨案：AMDは予想超えなのに7%安　NVIDIAとの明暗を分けた「次の受注証拠」
- 候補2：好決算でも売られたAMD　SpaceXが見せたAI半導体の新しい採点表
- 候補3：NASDAQ -0.83%　AMD一社では説明できない半導体の明暗

## D. サムネイル文言
- 推奨案：予想超えでも7%安
- 候補2：次の受注証拠
- 候補3：NVIDIAだけ上昇

## E. 概要欄
昨夜のNasdaq Compositeは0.83%下落し、SOXXは2.12%安でした。AMDはQ3売上見通しで通常の市場予想を上回ったのに7.04%下落し、NVIDIAはSpaceXの専属採用方針が報じられるなか3.43%上昇しました。この動画では、悪決算という単純説明を数字で退け、通常予想と高まったAI競争期待を分け、SpaceXの採用証拠が相対評価へどう届いたかを確認します。NASDAQ全体にはAlphabetとMicrosoftの下落も重なっており、AMD一社を指数下落の原因にはしません。今後はAMDの大型顧客、粗利率と供給制約、SOXXへの広がりを見れば、この見方が強まるか弱まるか確認できます。本動画はニュース解説であり、売買を勧めるものではありません。

## F. 制作上の注意
- Shadow用途。render_spec、TTS、Preview、Finalへ未接続。
- 主役カード：company_amd / ready。比較カード：company_nvda / ready。
- 当日固有画像：not-required。採用経路：not-required。
- 変更禁止：Expected / Actual / Gap、Medium確信度、分足欠損、AMD一社とNASDAQ全体の分離。
- 読み方：AMD=エーエムディー、NVIDIA=エヌビディア、SOXX=ソックス。

## G. 使用情報源
- E-001〜E-009：`causal_baseline_snapshot.json`のEvidence Digestを正本とする。
- 外部情報は追加していない。

## H. Story Engine審問結果
- Author invocation：shadow-author-2026-08-06-v1
- Critic invocation：shadow-critic-2026-08-06-v1
- Critic isolation：logical-shadow。入力artifactは分離したが、別モデルプロセスでの実行は未証明。
- Production eligibility：false。実際の独立Critic実行とユーザーA/B確認前は本番へ進めない。
- Round 1：旧台本へCritical 6件。対象修正を適用。
- Round 2：Critical 0件、Major 0件、PASS。
- Claim Ledger：6件すべて保持。
- Causality Diff：PASS。
- 本番採用：未決定。ユーザーA/B確認前にDaily Productionへ接続しない。
