# 朝のNASDAQカフェ source_pack

## 取得日時
- date: 2026-08-06
- generated_at: 2026-08-06T04:27:46+00:00

## キャッシュ利用状況
- cache_used: False
- refresh: True

## 取得状況
- Longbridge: loaded
- FRED: skipped
- FMP: skipped
- SEC / IR: skipped
- RSS: ok
- SerpAPI: skipped
- Tavily: skipped
- Market Movers: ok
- Economic Calendar: partial
- Raw Archive: partial
- Article Full Text: partial
- GDELT Radar: ok

## Collector Metadata
### API Key Status
- SERPAPI_API_KEY: not_set
- TAVILY_API_KEY: not_set
- FRED_API_KEY: not_set
- FMP_API_KEY: not_set
- SEC_USER_AGENT: not_set
- LONGBRIDGE: plugin_or_raw_preferred
### Search
- SERPAPI_API_KEY: not_set
- TAVILY_API_KEY: not_set
- query_count: {'SerpAPI': 2, 'Tavily': 2}
- raw_item_count: {'SerpAPI': 0, 'Tavily': 0}
- adopted_supplement_count: {'SerpAPI': 0, 'Tavily': 0}
- policy: Search supplements are secondary to RSS and only normalized items with source, published_at, url, and snippet may be adopted.
### RSS
- strategy: vendor_finance_news_aggregator primary; feedparser fallback; requests+ElementTree final fallback
- actual_route: feedparser
- vendor_repo_path: /home/runner/work/nasdaq-cafe-news-collector/nasdaq-cafe-news-collector/vendor/finance-news-aggregator
- vendor_repo_present: False
- vendor_repo_commit_hash: 
- vendor_license_present: False
- vendor_pyproject_present: False
- vendor_requirements_present: False
- vendor_finnews_importable: False
- implementation_note: Phase 1.11h uses the vendored GitHub repo vendor/finance-news-aggregator as the primary RSS adapter. The vendored repo is not updated during normal runs; its commit hash is recorded for reproducibility. pip packages fin-news / FinNews are not treated as the primary route. feedparser is the fallback for each RSS feed. requests+ElementTree is retained as a built-in final fallback so the run can continue without optional packages. vendor/finance-news-aggregator is missing; RSS collection will use fallback routes. Actual RSS route summary for this run: {'feedparser': 4}. Feed route details: Yahoo Finance: route=feedparser, status=ok, count=20; MarketWatch: route=feedparser, status=ok, count=10; NASDAQ: route=feedparser, status=ok, count=15; CNBC: route=feedparser, status=ok, count=20.
- route_summary: {'feedparser': 4}
- feed_routes:
  - Yahoo Finance: status=ok, route=feedparser, count=20
  - MarketWatch: status=ok, route=feedparser, count=10
  - NASDAQ: status=ok, route=feedparser, count=15
  - CNBC: status=ok, route=feedparser, count=20

## 市場データ
- NASDAQ: price=26363.439, change=-221.554, change_percent=-0.83, session=unknown
- SOX: price=530.700, change=-11.510, change_percent=-2.12, session=unknown
- 米10年金利: null
- ドル円: null

## 固定ウォッチ銘柄
- NVDA: price=219.220, change=7.280, change_percent=3.43, session=unknown
- MSFT: price=487.460, change=-5.350, change_percent=-1.09, session=unknown
- AAPL: price=311.000, change=1.620, change_percent=0.52, session=unknown
- AMZN: price=272.650, change=-4.770, change_percent=-1.72, session=unknown
- GOOGL: price=362.430, change=-15.220, change_percent=-4.03, session=unknown
- META: price=588.770, change=0.830, change_percent=0.14, session=unknown
- AVGO: price=418.280, change=0.120, change_percent=0.03, session=unknown
- TSM: price=414.000, change=-3.170, change_percent=-0.76, session=unknown
- AMD: price=482.050, change=-36.530, change_percent=-7.04, session=unknown
- TSLA: price=321.550, change=-5.800, change_percent=-1.77, session=unknown

## Market Movers候補
- MTRN: category=Top Gainers, change=30.8146, reason=Top Gainers; price move 30.81%; volume above usual level, confidence=medium, source=Yahoo Finance
- WTTR: category=Top Gainers, change=20.3243, reason=Top Gainers; price move 20.32%; volume above usual level, confidence=medium, source=Yahoo Finance
- SHOP: category=Top Gainers, change=16.983, reason=Top Gainers; price move 16.98%; large-cap candidate; volume above usual level, confidence=medium, source=Yahoo Finance
- BSP: category=Top Gainers, change=16.8224, reason=Top Gainers; price move 16.82%; volume above usual level, confidence=medium, source=Yahoo Finance
- URGN: category=Top Gainers, change=16.3076, reason=Top Gainers; price move 16.31%; volume above usual level, confidence=medium, source=Yahoo Finance
- SEDG: category=Top Losers, change=-30.4758, reason=Top Losers; price move -30.48%; volume above usual level, confidence=medium, source=Yahoo Finance
- TDC: category=Top Losers, change=-23.7278, reason=Top Losers; price move -23.73%; volume above usual level, confidence=medium, source=Yahoo Finance
- PODD: category=Top Losers, change=-20.1175, reason=Top Losers; price move -20.12%; volume above usual level, confidence=medium, source=Yahoo Finance
- EXTR: category=Top Losers, change=-19.0167, reason=Top Losers; price move -19.02%; volume above usual level, confidence=medium, source=Yahoo Finance
- CC: category=Top Losers, change=-18.628, reason=Top Losers; price move -18.63%; volume above usual level, confidence=medium, source=Yahoo Finance
- SPCX: category=Most Active, change=-13.6121, reason=Most Active; price move -13.61%; large-cap candidate; volume above usual level, confidence=medium, source=Yahoo Finance
- ZETA: category=Most Active, change=11.5828, reason=Most Active; price move 11.58%; volume above usual level, confidence=medium, source=Yahoo Finance
- LUMN: category=Most Active, change=-9.38897, reason=Most Active; price move -9.39%; volume above usual level, confidence=medium, source=Yahoo Finance
- SNAP: category=Most Active, change=-7.94473, reason=Most Active; price move -7.94%; volume above usual level, confidence=medium, source=Yahoo Finance
- DKNG: category=Most Active, change=-7.83566, reason=Most Active; price move -7.84%; volume above usual level, confidence=medium, source=Yahoo Finance
- ALAB: category=Nasdaq 100 movers, change=-11.96, reason=Nasdaq 100 movers; price move -11.96%; large-cap candidate, confidence=medium, source=Nasdaq Market Activity
- TRI: category=Nasdaq 100 movers, change=-9.66, reason=Nasdaq 100 movers; price move -9.66%, confidence=medium, source=Nasdaq Market Activity
- BKNG: category=Nasdaq 100 movers, change=6.56, reason=Nasdaq 100 movers; price move 6.56%; large-cap candidate, confidence=medium, source=Nasdaq Market Activity
- HONA: category=Nasdaq 100 movers, change=-5.93, reason=Nasdaq 100 movers; price move -5.93%; large-cap candidate, confidence=medium, source=Nasdaq Market Activity
- SNDK: category=Nasdaq 100 movers, change=-5.4, reason=Nasdaq 100 movers; price move -5.40%; large-cap candidate, confidence=medium, source=Nasdaq Market Activity
- GFS: category=SOX component movers, change=-4.92, reason=SOX component movers; price move -4.92%; theme: semiconductor, confidence=medium, source=Longbridge quote
- ON: category=SOX component movers, change=-4.79, reason=SOX component movers; price move -4.79%; theme: semiconductor, confidence=medium, source=Longbridge quote
- MCHP: category=SOX component movers, change=-3.57, reason=SOX component movers; price move -3.57%; theme: semiconductor, confidence=medium, source=Longbridge quote
- TER: category=SOX component movers, change=-3.51, reason=SOX component movers; price move -3.51%; theme: semiconductor, confidence=medium, source=Longbridge quote
- MRVL: category=SOX component movers, change=-3.46, reason=SOX component movers; price move -3.46%; theme: semiconductor, confidence=medium, source=Longbridge quote

## 経済イベント
### Past Events
- Cook, Outlook for the U.S. and Alaskan Economies
  - event_date: 2026-08-05
  - event_time: 20:05 UTC
  - event_window: recent_session
  - importance: medium
  - event_impact_score: 5
  - actual: None
  - forecast: None
  - previous: None
  - market_expectation: Markets watch whether Fed speakers shift rate-cut expectations, yields, or dollar direction.
  - why_viewer_should_care: Rate expectations and Treasury yields can quickly change valuation pressure on Nasdaq, AI, and semiconductor shares.
  - driver_type: context_macro_candidate
  - causal_bridge: Fed speech -> rate-cut expectations / yields / dollar -> Nasdaq 100 / AI stocks / semiconductors -> event was released by an official/public source near the target US session
  - confidence: high
  - source: Federal Reserve Speeches RSS
  - url: https://www.federalreserve.gov/newsevents/speech/cook20260805a.htm
  - filter_reason: Context only unless actual/forecast/previous and market reaction support causality.

### Upcoming Events
- GDP (Second Estimate) and Corporate Profits, 2nd Quarter 2026
  - event_date: 2026-08-26
  - event_time: 8:30 AM ET
  - event_window: next_major_event
  - importance: medium
  - event_impact_score: 5
  - actual: None
  - forecast: None
  - previous: None
  - market_expectation: Markets watch whether growth is resilient without forcing a more hawkish rate outlook.
  - why_viewer_should_care: Growth data helps separate soft-landing optimism from demand-slowdown risk for large tech.
  - driver_type: context_macro_candidate
  - causal_bridge: GDP -> growth outlook / rate expectations -> Nasdaq 100 / cyclical tech demand -> event is the next major official macro watch point; do not treat it as a prior-session cause
  - confidence: high
  - source: BEA Release Schedule
  - url: https://www.bea.gov/news/schedule
  - filter_reason: Next major scheduled macro event; use as a watch calendar item, not as a cause of the previous US session.
- Personal Income and Outlays, July 2026
  - event_date: 2026-09-03
  - event_time: 8:30 AM ET
  - event_window: next_major_event
  - importance: high
  - event_impact_score: 8
  - actual: None
  - forecast: None
  - previous: None
  - market_expectation: Markets watch whether the Fed's preferred inflation gauge supports rate-cut expectations.
  - why_viewer_should_care: Rate expectations and Treasury yields can quickly change valuation pressure on Nasdaq, AI, and semiconductor shares.
  - driver_type: context_macro_candidate
  - causal_bridge: PCE -> inflation expectations / Treasury yields -> Nasdaq 100 / growth stocks / semiconductors -> event is the next major official macro watch point; do not treat it as a prior-session cause
  - confidence: high
  - source: BEA Release Schedule
  - url: https://www.bea.gov/news/schedule
  - filter_reason: Next major scheduled macro event; use as a watch calendar item, not as a cause of the previous US session.

### Low Value Macro Summary
- BEA Release Schedule: count=12, reason=Outside the practical past/upcoming watch window or not a major official macro event.
- Federal Reserve Monetary Policy RSS: count=15, reason=Outside the practical past/upcoming watch window or not a major official macro event.
- Federal Reserve Speeches RSS: count=14, reason=Outside the practical past/upcoming watch window or not a major official macro event.
- Federal Reserve Speeches and Testimony RSS: count=2, reason=Outside the practical past/upcoming watch window or not a major official macro event.
- RSS News (NASDAQ): count=2, reason=Weak Nasdaq/SOX/semiconductor causal bridge.

## Article Review Targets
### Must Review Before Writing
- Nvidia’s stock is basking in the glow of a high-profile endorsement
  - source: MarketWatch
  - published_at: Wed, 05 Aug 2026 21:22:00 GMT
  - url: https://www.marketwatch.com/story/nvidias-stock-is-basking-in-the-glow-of-a-high-profile-endorsement-b7c48e7b?mod=mw_rss_topstories
  - snippet: SpaceX CEO Elon Musk said his company will only use Nvidia’s chips to build its AI.
  - review_priority: must
  - reason_to_review: Core Driver selected for the main NASDAQ/AI/semiconductor narrative; verify the article body before treating it as a main material.
  - expected_use: Use as a possible main-story fact base only after body review confirms the title/snippet and causal bridge.
  - related_tickers: NVDA
  - confidence: medium
  - causal_bridge: Nvidia’s stock is basking in the glow of a high-profile endorsement -> AI/semiconductor demand, expectations, or supply-chain repricing -> SOX, SMH, semiconductor watchlist, NVDA -> title/snippet evidence: chip, ai, nvidia
- Applied Digital Corp (APLD)’s 400% Revenue Surge — Breakout AI Infrastructure Play or Risky Bet?
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:41:48Z
  - url: https://finance.yahoo.com/technology/ai/articles/applied-digital-corp-apld-400-164148284.html
  - snippet: Applied Digital Corp (APLD)’s 400% Revenue Surge — Breakout AI Infrastructure Play or Risky Bet?
  - review_priority: must
  - reason_to_review: Core Driver selected for the main NASDAQ/AI/semiconductor narrative; verify the article body before treating it as a main material.
  - expected_use: Use as a possible main-story fact base only after body review confirms the title/snippet and causal bridge.
  - related_tickers: 
  - confidence: medium
  - causal_bridge: Applied Digital Corp (APLD)’s 400% Revenue Surge — Breakout AI Infrastructure Play or Risky Bet? -> AI/semiconductor demand, expectations, or supply-chain repricing -> SOX, SMH, semiconductor watchlist -> title/snippet evidence: ai

### Optional Review
- SpaceX ramps up Tesla Megapack purchases in Q2 to power its AI data centers
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 21:32:34 GMT
  - url: https://www.cnbc.com/2026/08/05/spacex-tesla-megapack-ai-data-centers.html
  - snippet: SpaceX is using Tesla's big Megapack backup batteries to help power its Colossus AI data centers in Greater Memphis.
  - review_priority: optional
  - reason_to_review: Context Candidate may reinforce a Core Driver theme if the body adds concrete support.
  - expected_use: Use only as background or a supporting bridge, not as the main cause, unless body review shows stronger evidence.
  - related_tickers: TSLA
  - confidence: medium
  - causal_bridge: SpaceX ramps up Tesla Megapack purchases in Q2 to power its AI data centers -> AI/semiconductor demand, expectations, or supply-chain repricing -> SOX, SMH, semiconductor watchlist, TSLA -> title/snippet evidence: ai, data center
- Alphabet’s stock drops as Google loses another key AI executive
  - source: MarketWatch
  - published_at: Wed, 05 Aug 2026 21:20:00 GMT
  - url: https://www.marketwatch.com/story/alphabets-stock-drops-as-google-loses-another-key-ai-executive-38de45a2?mod=mw_rss_topstories
  - snippet: Jeff Dean, Google’s chief scientist and one of its first employees, is leaving to launch his own company.
  - review_priority: optional
  - reason_to_review: Context Candidate may reinforce a Core Driver theme if the body adds concrete support.
  - expected_use: Use only as background or a supporting bridge, not as the main cause, unless body review shows stronger evidence.
  - related_tickers: GOOGL
  - confidence: medium
  - causal_bridge: Alphabet’s stock drops as Google loses another key AI executive -> AI/semiconductor demand, expectations, or supply-chain repricing -> SOX, SMH, semiconductor watchlist, GOOGL -> title/snippet evidence: ai
- Google's AI reshuffle: Chief scientist Jeff Dean exits and Demis Hassabis steps down as DeepMind CEO
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 18:51:53 GMT
  - url: https://www.cnbc.com/2026/08/05/google-chief-scientist-jeff-dean-leaving-company-after-27-years.html
  - snippet: Google's AI divisions are getting reshuffled, the search giant announced on Wednesday.
  - review_priority: optional
  - reason_to_review: Context Candidate may reinforce a Core Driver theme if the body adds concrete support.
  - expected_use: Use only as background or a supporting bridge, not as the main cause, unless body review shows stronger evidence.
  - related_tickers: GOOGL
  - confidence: medium
  - causal_bridge: Google's AI reshuffle: Chief scientist Jeff Dean exits and Demis Hassabis steps down as DeepMind CEO -> AI/semiconductor demand, expectations, or supply-chain repricing -> SOX, SMH, semiconductor watchlist, GOOGL -> title/snippet evidence: ai

### Usually Do Not Review
- Excluded / Low Value Summary: Usually skip; these items have weak causal bridge, low relevance, blocked URL shape, or insufficient fields.
  - expected_use: Do not use for scripts, Canva copy, thumbnails, or descriptions unless a human explicitly asks to inspect an excluded item.

## Article Full Text Status
- raw_path: output/2026-08-06/raw/article_fulltext.json
- manifest_path: output/2026-08-06/raw/manifest.json
- articles_path: output/2026-08-06/raw/articles/
- cache_used: False
- target_count: 112
- attempted_count: 25
- complete_count: 18
- failed_count: 7
- excluded_count: 0
- not_attempted_limit_count: 87
- pending_count: 0
- raw_html_count: 25
- extracted_text_count: 18
- readable_count: 18
- alternate_readable_count: 0
- unreadable_count: 7
- total_full_text_chars: 83573
- readable_count_before_fallback: 0
- unreadable_count_before_fallback: 0
- fallback_attempted_count: 0
- fallback_success_count: 0
- fallback_failed_count: 7
- fallback_query_count: 0

## GDELT Radar Status
- raw_path: output/2026-08-06/raw/gdelt_radar.json
- cache_used: False
- status: ok
- query_count: 8
- raw_result_count: 50
- candidate_count: 40
- accepted_count: 20
- rejected_count: 14
- fulltext_candidate_count: 10
- categories:
  - ai_model_watch: raw=10, accepted=1, rejected=2, fulltext_candidates=1
  - china_ai_watch: raw=10, accepted=8, rejected=5, fulltext_candidates=2
  - ai_chip_compute: raw=0, accepted=0, rejected=0, fulltext_candidates=0
  - platform_ai: raw=0, accepted=4, rejected=0, fulltext_candidates=4
  - elon_space_xai: raw=10, accepted=7, rejected=3, fulltext_candidates=3
  - robotics_autonomy: raw=0, accepted=0, rejected=0, fulltext_candidates=0
  - regulation_geopolitics: raw=10, accepted=0, rejected=2, fulltext_candidates=0
  - money_flow_deals: raw=10, accepted=0, rejected=2, fulltext_candidates=0
- candidates:
  - title: Meta chases OpenAI , Anthropic with new AI coding app
    category: ai_model_watch
    source: bssnews.net
    url: https://www.bssnews.net/news/412082
    published_at: 2026-08-06T03:00:00Z
    seen_at: 2026-08-06T03:00:00Z
    related_tickers: META, private_openai, private_anthropic
    radar_score: 105
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: True
  - title: Google - parent Alphabet shakes up AI division
    category: platform_ai
    source: bssnews.net
    url: https://www.bssnews.net/news/412093
    published_at: 2026-08-06T03:00:00Z
    seen_at: 2026-08-06T03:00:00Z
    related_tickers: GOOGL
    radar_score: 105
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: True
  - title: Meta AI model accessed Internet , hacked outside firm
    category: platform_ai
    source: thestar.com.my
    url: https://www.thestar.com.my/tech/tech-news/2026/08/06/meta-ai-model-accessed-internet-hacked-outside-firm
    published_at: 2026-08-06T02:45:00Z
    seen_at: 2026-08-06T02:45:00Z
    related_tickers: META
    radar_score: 105
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: True
  - title: Google Shakes up AI Division as DeepMind Chief Shifts Role
    category: platform_ai
    source: deccanchronicle.com
    url: https://www.deccanchronicle.com/world/americas/google-shakes-up-ai-division-as-deepmind-chief-shifts-role-1976968
    published_at: 2026-08-06T04:00:00Z
    seen_at: 2026-08-06T04:00:00Z
    related_tickers: GOOGL
    radar_score: 100
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: True
  - title: Google - parent Alphabet shakes up AI division
    category: platform_ai
    source: manilatimes.net
    url: https://www.manilatimes.net/2026/08/06/business/sunday-business-it/google-parent-alphabet-shakes-up-ai-division/2399575
    published_at: 2026-08-06T03:00:00Z
    seen_at: 2026-08-06T03:00:00Z
    related_tickers: GOOGL
    radar_score: 100
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: True
  - title: Lucid Aims To Knock Tesla Robotaxi Off Its Perch
    category: elon_space_xai
    source: cleantechnica.com
    url: https://cleantechnica.com/2026/08/05/lucid-evs-robotaxi-driverless-tesla-cybercab-elon-musk/
    published_at: 2026-08-06T03:30:00Z
    seen_at: 2026-08-06T03:30:00Z
    related_tickers: TSLA
    radar_score: 100
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: True
  - title: SpaceX reports its first financials as a public company today : Here are 4 key details to watch out for
    category: elon_space_xai
    source: finance.yahoo.com
    url: https://finance.yahoo.com/markets/stocks/articles/spacex-reports-first-financials-public-153100672.html
    published_at: 2026-08-06T03:30:00Z
    seen_at: 2026-08-06T03:30:00Z
    related_tickers: private_spacex
    radar_score: 100
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: True
  - title: Scientists Are Certain A Wayward SpaceX Rocket Slammed Into The Moon As Predicted
    category: elon_space_xai
    source: theyeshivaworld.com
    url: https://www.theyeshivaworld.com/news/general/2582827/scientists-are-certain-a-wayward-spacex-rocket-slammed-into-the-moon-as-predicted.html
    published_at: 2026-08-06T04:00:00Z
    seen_at: 2026-08-06T04:00:00Z
    related_tickers: private_spacex
    radar_score: 95
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: True
  - title: US plans restrictions on Chinese AI infrastructure devices
    category: china_ai_watch
    source: australiannews.net
    url: http://www.australiannews.net/news/279222505/us-plans-restrictions-on-chinese-ai-infrastructure-devices
    published_at: 2026-08-06T04:00:00Z
    seen_at: 2026-08-06T04:00:00Z
    related_tickers: no_us_ticker
    radar_score: 95
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: True
  - title: US plans restrictions on Chinese AI infrastructure devices
    category: china_ai_watch
    source: myanmarnews.net
    url: http://www.myanmarnews.net/news/279222505/us-plans-restrictions-on-chinese-ai-infrastructure-devices
    published_at: 2026-08-06T03:30:00Z
    seen_at: 2026-08-06T03:30:00Z
    related_tickers: no_us_ticker
    radar_score: 95
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: True
  - title: A Giant Piece Of SpaceX Junk Has Smashed Into The Moon
    category: elon_space_xai
    source: 4ro.com.au
    url: https://www.4ro.com.au/trending/stories/a-giant-piece-of-spacex-junk-has-smashed-into-the-moon/
    published_at: 2026-08-06T04:00:00Z
    seen_at: 2026-08-06T04:00:00Z
    related_tickers: private_spacex
    radar_score: 90
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: False
  - title: SpaceX - Rakete ist auf dem Mond eingeschlagen – Forscher bestätigen Aufprall
    category: elon_space_xai
    source: tlz.de
    url: https://www.tlz.de/panorama/article412636218/forscher-bestaetigen-spacex-raketenteil-ist-auf-dem-mond-eingeschlagen.html
    published_at: 2026-08-06T04:00:00Z
    seen_at: 2026-08-06T04:00:00Z
    related_tickers: private_spacex
    radar_score: 90
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: False
  - title: Científicos aseguran que cohete de Space X estrelló en la luna – Telemundo Dallas ( 39 )
    category: elon_space_xai
    source: telemundodallas.com
    url: https://www.telemundodallas.com/noticias/ciencia/cientificos-aseguran-cohete-spacex-estrello-contra-luna/2596431/
    published_at: 2026-08-06T03:30:00Z
    seen_at: 2026-08-06T03:30:00Z
    related_tickers: private_spacex
    radar_score: 90
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: False
  - title: A Giant Piece Of SpaceX Junk Has Smashed Into The Moon
    category: elon_space_xai
    source: 4bu.com.au
    url: https://www.4bu.com.au/trending/stories/a-giant-piece-of-spacex-junk-has-smashed-into-the-moon/
    published_at: 2026-08-06T03:30:00Z
    seen_at: 2026-08-06T03:30:00Z
    related_tickers: private_spacex
    radar_score: 90
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: False
  - title: NEO發表AI記憶體新技術 施振榮 ： 帶來半導體新可能 | 科技
    category: china_ai_watch
    source: cna.com.tw
    url: https://www.cna.com.tw:443/news/ait/202608060044.aspx
    published_at: 2026-08-06T04:00:00Z
    seen_at: 2026-08-06T04:00:00Z
    related_tickers: no_us_ticker
    radar_score: 85
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: False
  - title: CSU launches micro - credential pilot program in AI literacy
    category: china_ai_watch
    source: dailynews.com
    url: https://www.dailynews.com/2026/08/05/csu-launches-micro-credential-pilot-program-in-ai-literacy/
    published_at: 2026-08-06T03:00:00Z
    seen_at: 2026-08-06T03:00:00Z
    related_tickers: no_us_ticker
    radar_score: 85
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: False
  - title: US weighs ban on Chinese data center equipment imports
    category: china_ai_watch
    source: batonrougepost.com
    url: http://www.batonrougepost.com/news/279222505/us-weighs-ban-on-chinese-data-center-equipment-imports
    published_at: 2026-08-06T04:00:00Z
    seen_at: 2026-08-06T04:00:00Z
    related_tickers: 
    radar_score: 85
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: False
  - title: US weighs ban on Chinese data center equipment imports
    category: china_ai_watch
    source: parisguardian.com
    url: http://www.parisguardian.com/news/279222505/us-weighs-ban-on-chinese-data-center-equipment-imports
    published_at: 2026-08-06T04:00:00Z
    seen_at: 2026-08-06T04:00:00Z
    related_tickers: 
    radar_score: 85
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: False
  - title: US weighs ban on Chinese data center equipment imports
    category: china_ai_watch
    source: bostonstar.com
    url: http://www.bostonstar.com/news/279222505/us-weighs-ban-on-chinese-data-center-equipment-imports
    published_at: 2026-08-06T04:00:00Z
    seen_at: 2026-08-06T04:00:00Z
    related_tickers: 
    radar_score: 85
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: False
  - title: US weighs ban on Chinese data center equipment imports
    category: china_ai_watch
    source: newzealandstar.com
    url: http://www.newzealandstar.com/news/279222505/us-weighs-ban-on-chinese-data-center-equipment-imports
    published_at: 2026-08-06T04:00:00Z
    seen_at: 2026-08-06T04:00:00Z
    related_tickers: 
    radar_score: 85
    decision: accepted
    decision_reason: mechanical category, freshness, source, and URL checks passed
    fulltext_candidate: False
- daily_lead_theme_candidates:
  - candidate_theme: Elon / SpaceX / xAI
    main_category: elon_space_xai
    related_tickers: TSLA, private_spacex
    candidate_count: 7
    statement_signal_count: 1
    radar_score: 86
    body_verified: False
    use_as_script_evidence: False
    needs_fulltext_before_script: True
    market_causality_confirmed: False
  - candidate_theme: Platform AI
    main_category: platform_ai
    related_tickers: GOOGL, META
    candidate_count: 4
    statement_signal_count: 0
    radar_score: 79
    body_verified: False
    use_as_script_evidence: False
    needs_fulltext_before_script: True
    market_causality_confirmed: False
  - candidate_theme: China AI watch
    main_category: china_ai_watch
    related_tickers: no_us_ticker
    candidate_count: 8
    statement_signal_count: 0
    radar_score: 70
    body_verified: False
    use_as_script_evidence: False
    needs_fulltext_before_script: True
    market_causality_confirmed: False
  - candidate_theme: AI model watch
    main_category: ai_model_watch
    related_tickers: META, private_openai, private_anthropic
    candidate_count: 1
    statement_signal_count: 0
    radar_score: 57
    body_verified: False
    use_as_script_evidence: False
    needs_fulltext_before_script: True
    market_causality_confirmed: False
- statement_radar_status:
  - status: ok
  - candidate_count: 1
  - telop_candidate_count: 0
  - fulltext_candidate_count: 1
  - top_speakers: [{'name': 'Elon Musk', 'count': 1}]
  - top_topics: [{'name': 'Tesla', 'count': 1}]
- statement_radar_candidates:
  - speaker_name: Elon Musk
    statement_topic: Tesla
    title: Lucid Aims To Knock Tesla Robotaxi Off Its Perch
    source: cleantechnica.com
    url: https://cleantechnica.com/2026/08/05/lucid-evs-robotaxi-driverless-tesla-cybercab-elon-musk/
    verification_status: unverified
    telop_candidate: False
    body_verified: False
    use_as_script_evidence: False
    needs_fulltext_before_script: True
    market_causality_confirmed: False
- statement_fulltext_candidates:
  - speaker_name: Elon Musk
    statement_topic: Tesla
    url: https://cleantechnica.com/2026/08/05/lucid-evs-robotaxi-driverless-tesla-cybercab-elon-musk/
    needs_fulltext_before_script: True

## 取得ニュース一覧
- Missouri Is Latest State to Vote on Abolishing Income Tax
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:20:00Z
  - url: https://www.wsj.com/politics/policy/missouri-is-latest-state-to-vote-on-abolishing-income-tax-bd772de3?siteid=yhoof2&yptr=yahoo
  - snippet: Missouri Is Latest State to Vote on Abolishing Income Tax
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Is Lockheed Martin (LMT) a Buying Opportunity After Its 16% Drop?
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:19:11Z
  - url: https://finance.yahoo.com/markets/stocks/articles/lockheed-martin-lmt-buying-opportunity-161911062.html
  - snippet: Is Lockheed Martin (LMT) a Buying Opportunity After Its 16% Drop?
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- ICON plc (ICLR) Surged 57% in Q2 After Accounting Clarity
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:27:20Z
  - url: https://finance.yahoo.com/markets/stocks/articles/icon-plc-iclr-surged-57-162720285.html
  - snippet: ICON plc (ICLR) Surged 57% in Q2 After Accounting Clarity
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- 'Several steps ahead': Why Palantir stock is surging
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:22:24Z
  - url: https://finance.yahoo.com/markets/stocks/article/several-steps-ahead-why-palantir-stock-is-surging-162224977.html
  - snippet: 'Several steps ahead': Why Palantir stock is surging
  - related_tickers: 
  - why_relevant: theme: EV
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Is Elevance Health (ELV) Entering a Major Earnings Recovery?
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:21:57Z
  - url: https://finance.yahoo.com/healthcare/articles/elevance-health-elv-entering-major-162157370.html
  - snippet: Is Elevance Health (ELV) Entering a Major Earnings Recovery?
  - related_tickers: 
  - why_relevant: theme: EV
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- 3 Magnificent Artificial Intelligence (AI) Stocks to Buy Right Now and Hold for the Next Decade
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:20:00Z
  - url: https://finance.yahoo.com/technology/ai/articles/3-magnificent-artificial-intelligence-ai-162000683.html
  - snippet: 3 Magnificent Artificial Intelligence (AI) Stocks to Buy Right Now and Hold for the Next Decade
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- AI Integration Strengthens Alphabet’s (GOOG) Core Business
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:29:37Z
  - url: https://finance.yahoo.com/markets/stocks/articles/ai-integration-strengthens-alphabet-goog-162937753.html
  - snippet: AI Integration Strengthens Alphabet’s (GOOG) Core Business
  - related_tickers: GOOGL
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: context_candidate
  - relevance_score: 4
  - causal_bridge: AI Integration Strengthens Alphabet’s (GOOG) Core Business -> AI/semiconductor demand, expectations, or supply-chain repricing -> SOX, SMH, semiconductor watchlist, GOOGL -> title/snippet evidence: ai
  - selected_for_handoff: True
  - filter_reason: Background candidate only; use if it reinforces Core Drivers and market data.
- Why This Niche Energy Stock Delivered A Major Price Surge Post Earnings
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:30:33Z
  - url: https://www.investors.com/news/energy-stocks-why-amrc-is-delivering-a-major-price-surge-post-earnings/?src=A00220&yptr=yahoo
  - snippet: Why This Niche Energy Stock Delivered A Major Price Surge Post Earnings
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Danaher Beat Earnings Estimates, so Why Are Investors Still Concerned About Growth?
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:34:52Z
  - url: https://finance.yahoo.com/markets/stocks/articles/danaher-beat-earnings-estimates-why-163452865.html
  - snippet: Danaher Beat Earnings Estimates, so Why Are Investors Still Concerned About Growth?
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Is Intercontinental Exchange (ICE) a Buying Opportunity After Its 22% Drop?
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:16:48Z
  - url: https://finance.yahoo.com/markets/stocks/articles/intercontinental-exchange-ice-buying-opportunity-161648534.html
  - snippet: Is Intercontinental Exchange (ICE) a Buying Opportunity After Its 22% Drop?
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Here’s How Much Disney Stock Is Expected to Move After Earnings
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:28:26Z
  - url: https://finance.yahoo.com/markets/stocks/articles/much-disney-stock-expected-move-162826103.html
  - snippet: Here’s How Much Disney Stock Is Expected to Move After Earnings
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- US consumer watchdog supervisor warned staff of 'unpleasant' fallout if they go too hard on firms
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:38:49Z
  - url: https://finance.yahoo.com/economy/policy/articles/exclusive-us-consumer-watchdog-supervisor-101451547.html
  - snippet: US consumer watchdog supervisor warned staff of 'unpleasant' fallout if they go too hard on firms
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Markets see 'all hat, no cattle' in Fed's inflation credibility: Chart of the Day
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:40:28Z
  - url: https://finance.yahoo.com/markets/article/markets-see-all-hat-no-cattle-in-feds-inflation-credibility-chart-of-the-day-164028370.html
  - snippet: Markets see 'all hat, no cattle' in Fed's inflation credibility: Chart of the Day
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- This Analyst Just Downgraded eBay Stock. Here's Why.
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:14:27Z
  - url: https://finance.yahoo.com/markets/stocks/articles/analyst-just-downgraded-ebay-stock-161427692.html
  - snippet: This Analyst Just Downgraded eBay Stock. Here's Why.
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Applied Digital Corp (APLD)’s 400% Revenue Surge — Breakout AI Infrastructure Play or Risky Bet?
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:41:48Z
  - url: https://finance.yahoo.com/technology/ai/articles/applied-digital-corp-apld-400-164148284.html
  - snippet: Applied Digital Corp (APLD)’s 400% Revenue Surge — Breakout AI Infrastructure Play or Risky Bet?
  - related_tickers: 
  - why_relevant: theme: AI; theme: EV
  - confidence: medium
  - driver_type: core_driver
  - relevance_score: 6
  - causal_bridge: Applied Digital Corp (APLD)’s 400% Revenue Surge — Breakout AI Infrastructure Play or Risky Bet? -> AI/semiconductor demand, expectations, or supply-chain repricing -> SOX, SMH, semiconductor watchlist -> title/snippet evidence: ai
  - selected_for_handoff: True
  - filter_reason: Directly usable as a main material for today's NASDAQ/AI/semiconductor narrative.
- Arrive AI Targets the Future of Pharmacy Delivery with LifeSpan Pharmacy Collaboration
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:19:55Z
  - url: https://finance.yahoo.com/healthcare/articles/arrive-ai-targets-future-pharmacy-161955757.html
  - snippet: Arrive AI Targets the Future of Pharmacy Delivery with LifeSpan Pharmacy Collaboration
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Social Security is becoming the primary retirement plan for many Americans. But it's rarely enough money.
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:14:29Z
  - url: https://finance.yahoo.com/economy/article/social-security-is-becoming-the-primary-retirement-plan-for-many-americans-but-its-rarely-enough-money-161429269.html
  - snippet: Social Security is becoming the primary retirement plan for many Americans. But it's rarely enough money.
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- What is whole life insurance? How it works.
  - source: Yahoo Finance
  - published_at: 2023-12-15T22:11:25Z
  - url: https://finance.yahoo.com/personal-finance/insurance/article/what-is-whole-life-insurance-213448917.html
  - snippet: What is whole life insurance? How it works.
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Millrose Properties, Inc. Q2 2026 Earnings Call Summary
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:46:13Z
  - url: https://finance.yahoo.com/real-estate/articles/millrose-properties-inc-q2-2026-164613553.html
  - snippet: Millrose Properties, Inc. Q2 2026 Earnings Call Summary
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Superior Group of Companies, Inc. Q2 2026 Earnings Call Summary
  - source: Yahoo Finance
  - published_at: 2026-08-04T16:46:16Z
  - url: https://finance.yahoo.com/markets/stocks/articles/superior-group-companies-inc-q2-164616773.html
  - snippet: Superior Group of Companies, Inc. Q2 2026 Earnings Call Summary
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- I got two email invitations from friends. Is this a phishing scam — or am I suddenly popular?
  - source: MarketWatch
  - published_at: Thu, 06 Aug 2026 01:33:00 GMT
  - url: https://www.marketwatch.com/story/i-got-two-email-invitations-from-friends-is-this-a-phishing-scam-or-am-i-suddenly-popular-d9680aa8?mod=mw_rss_topstories
  - snippet: “I was surprised — and flattered — to find myself on the guest list.”
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- ‘I don’t wish to be cold-hearted’: My elderly relative can no longer care for himself. Am I wrong to leave his care to the state?
  - source: MarketWatch
  - published_at: Thu, 06 Aug 2026 01:31:00 GMT
  - url: https://www.marketwatch.com/story/i-dont-wish-to-be-cold-hearted-my-elderly-relative-can-no-longer-care-for-himself-am-i-wrong-to-leave-his-care-to-the-state-8d546b32?mod=mw_rss_topstories
  - snippet: “He has never been particularly generous or nurturing.”
  - related_tickers: 
  - why_relevant: theme: EV
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Sandisk’s stock falls as the company’s forecast doesn’t live up to high expectations
  - source: MarketWatch
  - published_at: Wed, 05 Aug 2026 22:25:00 GMT
  - url: https://www.marketwatch.com/story/sandisks-stock-falls-as-the-companys-forecast-doesnt-live-up-to-high-expectations-8fd13d9b?mod=mw_rss_topstories
  - snippet: The midpoint of the company’s revenue forecast was below what analysts had been modeling.
  - related_tickers: 
  - why_relevant: theme: EV
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Block slashed 40% of its workforce for AI — and its earnings suggest that’s paying off
  - source: MarketWatch
  - published_at: Wed, 05 Aug 2026 22:19:00 GMT
  - url: https://www.marketwatch.com/story/block-slashed-40-of-its-workforce-for-ai-and-earnings-suggest-thats-paying-off-852b7c54?mod=mw_rss_topstories
  - snippet: “We can ship higher-quality products much, much more quickly,” an executive said in the wake of the company’s better-than-expected earnings report
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Figma’s stock falls as the company’s AI push requires steep investments
  - source: MarketWatch
  - published_at: Wed, 05 Aug 2026 22:12:00 GMT
  - url: https://www.marketwatch.com/story/figmas-push-into-ai-agents-drives-an-earnings-beat-1f6e200a?mod=mw_rss_topstories
  - snippet: While Figma’s consumption-based AI monetization strategy is showing promise, the company’s margins are taking a hit.
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Why AT&T, Verizon and T-Mobile shares are down after SpaceX’s earnings
  - source: MarketWatch
  - published_at: Wed, 05 Aug 2026 21:28:00 GMT
  - url: https://www.marketwatch.com/story/why-at-t-verizon-and-t-mobile-shares-are-down-after-spacexs-earnings-033a07ce?mod=mw_rss_topstories
  - snippet: SpaceX thinks it will be able to build wireless capabilities without massive network investments.
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- SpaceX’s stock falls as Wall Street gets spooked by the extent of AI spending
  - source: MarketWatch
  - published_at: Wed, 05 Aug 2026 21:26:00 GMT
  - url: https://www.marketwatch.com/story/spacexs-stock-falls-as-wall-street-gets-spooked-by-the-extent-of-ai-spending-9ce9ddb8?mod=mw_rss_topstories
  - snippet: Morgan Stanley expects $64 billion in capital spending from SpaceX this year, as the company is dramatically ramping up AI investments.
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Nvidia’s stock is basking in the glow of a high-profile endorsement
  - source: MarketWatch
  - published_at: Wed, 05 Aug 2026 21:22:00 GMT
  - url: https://www.marketwatch.com/story/nvidias-stock-is-basking-in-the-glow-of-a-high-profile-endorsement-b7c48e7b?mod=mw_rss_topstories
  - snippet: SpaceX CEO Elon Musk said his company will only use Nvidia’s chips to build its AI.
  - related_tickers: NVDA
  - why_relevant: theme: AI; theme: semiconductors
  - confidence: medium
  - driver_type: core_driver
  - relevance_score: 10
  - causal_bridge: Nvidia’s stock is basking in the glow of a high-profile endorsement -> AI/semiconductor demand, expectations, or supply-chain repricing -> SOX, SMH, semiconductor watchlist, NVDA -> title/snippet evidence: chip, ai, nvidia
  - selected_for_handoff: True
  - filter_reason: Directly usable as a main material for today's NASDAQ/AI/semiconductor narrative.
- Missouri voters just rejected a bid to ditch income tax, while other tax votes loom in Florida and California this fall
  - source: MarketWatch
  - published_at: Wed, 05 Aug 2026 21:22:00 GMT
  - url: https://www.marketwatch.com/story/taxes-are-on-the-ballot-this-fall-as-republicans-and-democrats-grow-further-apart-on-whether-to-raise-them-c7990380?mod=mw_rss_topstories
  - snippet: Missouri voters rejected a bid to ditch the state’s income tax Tuesday, while big votes loom in Florida and California this fall.
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Alphabet’s stock drops as Google loses another key AI executive
  - source: MarketWatch
  - published_at: Wed, 05 Aug 2026 21:20:00 GMT
  - url: https://www.marketwatch.com/story/alphabets-stock-drops-as-google-loses-another-key-ai-executive-38de45a2?mod=mw_rss_topstories
  - snippet: Jeff Dean, Google’s chief scientist and one of its first employees, is leaving to launch his own company.
  - related_tickers: GOOGL
  - why_relevant: theme: AI; theme: ads
  - confidence: medium
  - driver_type: context_candidate
  - relevance_score: 4
  - causal_bridge: Alphabet’s stock drops as Google loses another key AI executive -> AI/semiconductor demand, expectations, or supply-chain repricing -> SOX, SMH, semiconductor watchlist, GOOGL -> title/snippet evidence: ai
  - selected_for_handoff: True
  - filter_reason: Background candidate only; use if it reinforces Core Drivers and market data.
- Stock Indices Fall from Early Highs and Settle Mixed
  - source: NASDAQ
  - published_at: Thu, 06 Aug 2026 03:53:13 +0000
  - url: https://www.nasdaq.com/articles/stock-indices-fall-early-highs-and-settle-mixed
  - snippet: The S&P 500 Index ($SPX ) (SPY ) on Wednesday closed down -0.17%, the Dow Jones Industrial Average ($DOWI ) (DIA ) closed up +0.49%, and the Nasdaq 100 Index ($IUXX ) (QQQ ) closed down -0.83%. September E-mini S&P futures (ESU26 ) fell -0.19%, and September E-mini Nasdaq future…
  - related_tickers: 
  - why_relevant: market: NASDAQ
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Dollar Slides on Stock Strength and Weakness in US Economic Reports
  - source: NASDAQ
  - published_at: Thu, 06 Aug 2026 03:16:50 +0000
  - url: https://www.nasdaq.com/articles/dollar-slides-stock-strength-and-weakness-us-economic-reports-0
  - snippet: The dollar index (DXY00 ) fell by -0.17% on Wednesday. The dollar fell on Wednesday after the S&P 500 climbed to a new record high, reducing demand for dollar liquidity. Also, Wednesday’s weaker-than-expected reports on July ADP employment and July ISM services were bearish for…
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Soybeans Bounce Off Intraday Weakness, Still Close with Losses
  - source: NASDAQ
  - published_at: Thu, 06 Aug 2026 01:51:41 +0000
  - url: https://www.nasdaq.com/articles/soybeans-bounce-intraday-weakness-still-close-losses-0
  - snippet: Soybeans saw losses of 2 to 3 ½ cents across most contracts on Wednesday, with deferreds fractionally mixed. The cmdtyView national average Cash Bean price was down 4 3/4 cents at $11.29 3/4. Soymeal futures were down $1.30 to $2.80, with Soy Oil 22 to 48 points lower. USDA will…
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Corn Extends Weakness to Wednesday
  - source: NASDAQ
  - published_at: Thu, 06 Aug 2026 01:03:46 +0000
  - url: https://www.nasdaq.com/articles/corn-extends-weakness-wednesday-0
  - snippet: Corn futures closed down a penny to 5 ¾ cents across most contracts at the Wednesday close, as pressure continues. The front months took the brunt of the hit. The CmdtyView national average Cash Corn price was down 5 1/2 cents at $4.07. USDA reported a private export sale of...
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Soybeans Bounce Off Intraday Weakness, Still Close with Losses
  - source: NASDAQ
  - published_at: Thu, 06 Aug 2026 01:03:46 +0000
  - url: https://www.nasdaq.com/articles/soybeans-bounce-intraday-weakness-still-close-losses
  - snippet: Soybeans saw losses of 2 to 3 ½ cents across most contracts on Wednesday, with deferreds fractionally mixed. The cmdtyView national average Cash Bean price was down 4 3/4 cents at $11.29 3/4. Soymeal futures were down $1.30 to $2.80, with Soy Oil 22 to 48 points lower. USDA will…
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Larger Ghana Cocoa Supplies Weigh on Prices
  - source: NASDAQ
  - published_at: Thu, 06 Aug 2026 01:03:46 +0000
  - url: https://www.nasdaq.com/articles/larger-ghana-cocoa-supplies-weigh-prices
  - snippet: September ICE NY cocoa (CCU26 ) on Wednesday closed down -42 (-0.71%), and September ICE London cocoa #7 (CAU26 ) closed down -16 (-0.37%). Cocoa prices fell from 3-week highs on Wednesday and settled lower as long liquidation pressures emerged on signs of larger cocoa supplies…
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Soybean Weakness Extends to Wednesday
  - source: NASDAQ
  - published_at: Thu, 06 Aug 2026 01:03:45 +0000
  - url: https://www.nasdaq.com/articles/soybean-weakness-extends-wednesday
  - snippet: Soybeans are trading with contracts down 3 to 5 ¼ cents at midday. The cmdtyView national average Cash Bean price is down 5 3/4 cents at $11.28 3/4. Soymeal futures are down $2.20 to $3.00, with Soy Oil 30 to 40 points lower. There were 137 deliveries issued against August...
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Cotton Rally Holding at Midday
  - source: NASDAQ
  - published_at: Thu, 06 Aug 2026 01:03:45 +0000
  - url: https://www.nasdaq.com/articles/cotton-rally-holding-midday
  - snippet: Cotton futures are back up 70 to 107 points in the front months at Wednesday’s midday. Crude oil is slipping 87 cents per barrel, with the US dollar index down $0.124. The NOAA 7-day QPF shows dryness continuing across much of TX in the next week, with very light totals...
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Coffee Prices Settle Higher on Global Weather Risks
  - source: NASDAQ
  - published_at: Thu, 06 Aug 2026 00:40:27 +0000
  - url: https://www.nasdaq.com/articles/coffee-prices-settle-higher-global-weather-risks
  - snippet: September arabica coffee (KCU26 ) closed up +2.80 (+0.86%) on Wednesday, and September ICE robusta coffee (RMU26 ) closed up +37 (+0.96%). Coffee prices settled higher on Wednesday, with robusta climbing to a 1-week high. Robusta coffee moved higher on Wednesday after rain chanc…
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Corn Extends Weakness to Wednesday
  - source: NASDAQ
  - published_at: Thu, 06 Aug 2026 00:34:08 +0000
  - url: https://www.nasdaq.com/articles/corn-extends-weakness-wednesday
  - snippet: Corn futures closed down a penny to 5 ¾ cents across most contracts at the Wednesday close, as pressure continues. The front months took the brunt of the hit. The CmdtyView national average Cash Corn price was down 5 1/2 cents at $4.07. USDA reported a private export sale of...
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Corn Losses Extend to Wednesday’s Midday
  - source: NASDAQ
  - published_at: Thu, 06 Aug 2026 00:34:07 +0000
  - url: https://www.nasdaq.com/articles/corn-losses-extend-wednesdays-midday
  - snippet: Corn futures are continuing to slide, with contracts down 5 to 6 cents so far on Wednesday’s midday. The CmdtyView national average Cash Corn price is down 5 cents at $4.07 1/2. USDA reported a private export sale of 120,000 MT of corn to Mexico this morning, with 30,000 MT...
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Winter Wheat Holds onto Gains into the Close, as Spring Wheat Slides
  - source: NASDAQ
  - published_at: Thu, 06 Aug 2026 00:06:25 +0000
  - url: https://www.nasdaq.com/articles/winter-wheat-holds-gains-close-spring-wheat-slides
  - snippet: The wheat complex saw mixed trade into the Wednesday close. Chicago SRW contracts were 3 3/4 to 10 cents higher to close out the midweek session. KC HRW futures were 6 ½ to 14 cents higher across the board. MPLS spring wheat was mixed, with front months down as much...
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Cattle Rally on Wednesday
  - source: NASDAQ
  - published_at: Wed, 05 Aug 2026 23:32:47 +0000
  - url: https://www.nasdaq.com/articles/cattle-rally-wednesday-2
  - snippet: Live cattle futures posted gains of 42 cents to $2.22 across the board on Wednesday. Cash trade has been quiet so far this week following the $232-235 last week. There was some $370-371 dressed trade reported, with southern bids at $230-235..The Wednesday Fed Cattle Exchange onl…
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Cattle Rally on Wednesday
  - source: NASDAQ
  - published_at: Wed, 05 Aug 2026 23:32:47 +0000
  - url: https://www.nasdaq.com/articles/cattle-rally-wednesday-1
  - snippet: Live cattle futures posted gains of 42 cents to $2.22 across the board on Wednesday. Cash trade has been quiet so far this week following the $232-235 last week. There was some $370-371 dressed trade reported, with southern bids at $230-235..The Wednesday Fed Cattle Exchange onl…
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Winter Wheat Holds onto Gains into the Close, as Spring Wheat Slides
  - source: NASDAQ
  - published_at: Wed, 05 Aug 2026 23:32:46 +0000
  - url: https://www.nasdaq.com/articles/winter-wheat-holds-gains-close-spring-wheat-slides-0
  - snippet: The wheat complex saw mixed trade into the Wednesday close. Chicago SRW contracts were 3 3/4 to 10 cents higher to close out the midweek session. KC HRW futures were 6 ½ to 14 cents higher across the board. MPLS spring wheat was mixed, with front months down as much...
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- U.S. ready to return to 'commitments,' Iran says, after Trump signals deal is near
  - source: CNBC
  - published_at: Thu, 06 Aug 2026 03:00:05 GMT
  - url: https://www.cnbc.com/2026/08/06/us-iran-war-hormuz-trump-bessent-deal.html
  - snippet: Iran denied it was in talks with Washington, despite claims by Trump to the contrary.
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- JPMorgan's Jamie Dimon warns of high leverage: 'Somebody will disrupt the market'
  - source: CNBC
  - published_at: Thu, 06 Aug 2026 02:02:39 GMT
  - url: https://www.cnbc.com/2026/08/06/jpmorgan-jamie-dimon-leverage-market-disruption.html
  - snippet: JPMorgan Chief Executive Officer Jamie Dimon warned that leverage across financial markets remains elevated, adding that investors should be mindful that hidden borrowing could amplify market disruptions.
  - related_tickers: 
  - why_relevant: theme: AI; theme: EV
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Inside India newsletter: What's behind India’s rush to sell shares in state-owned firms
  - source: CNBC
  - published_at: Thu, 06 Aug 2026 00:11:08 GMT
  - url: https://www.cnbc.com/2026/08/06/india-lic-shares-economy-disinvestment-.html
  - snippet: India is ramping up stake sales in state-owned companies to keep the growth engine running amid growing fiscal constraints
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Google's AI reshuffle: Chief scientist Jeff Dean exits and Demis Hassabis steps down as DeepMind CEO
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 18:51:53 GMT
  - url: https://www.cnbc.com/2026/08/05/google-chief-scientist-jeff-dean-leaving-company-after-27-years.html
  - snippet: Google's AI divisions are getting reshuffled, the search giant announced on Wednesday.
  - related_tickers: GOOGL
  - why_relevant: theme: AI; theme: ads
  - confidence: medium
  - driver_type: context_candidate
  - relevance_score: 4
  - causal_bridge: Google's AI reshuffle: Chief scientist Jeff Dean exits and Demis Hassabis steps down as DeepMind CEO -> AI/semiconductor demand, expectations, or supply-chain repricing -> SOX, SMH, semiconductor watchlist, GOOGL -> title/snippet evidence: ai
  - selected_for_handoff: True
  - filter_reason: Background candidate only; use if it reinforces Core Drivers and market data.
- We're downgrading Honeywell Aerospace after a shockingly bad earnings debut
  - source: CNBC
  - published_at: Thu, 06 Aug 2026 00:09:36 GMT
  - url: https://www.cnbc.com/2026/08/05/were-downgrading-honeywell-aerospace-after-a-shockingly-bad-earnings-debut.html
  - snippet: The company slashed its full-year guidance on key metrics in its first earnings report since separating from the Honeywell conglomerate in June.
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Disney weighs free, ad-supported streaming, says it has sold out Super Bowl ad spots
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 15:25:55 GMT
  - url: https://www.cnbc.com/2026/08/05/disney-free-ad-supported-streaming-super-bowl-ads.html
  - snippet: Disney is considering a free streaming product as advertising takes a bigger role in making streaming profitable.
  - related_tickers: 
  - why_relevant: theme: ads
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- How Disney parks are bucking a travel slowdown
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 21:22:36 GMT
  - url: https://www.cnbc.com/2026/08/05/disney-parks-travel-attendance-revenue.html
  - snippet: Disney posted record quarterly revenue at its parks division despite a continued slump in international travel to the U.S.
  - related_tickers: 
  - why_relevant: theme: EV
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Fed Governor Cook says she's 'prepared to act' on rate hike to address inflation
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 20:36:16 GMT
  - url: https://www.cnbc.com/2026/08/05/fed-governor-cook-says-shes-prepared-to-act-on-rate-hike-to-address-inflation.html
  - snippet: Cook was part of a 9-3 majority that voted last week to keep the central bank's benchmark borrowing rate in a range between 3.5%-3.75%.
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- SpaceX ramps up Tesla Megapack purchases in Q2 to power its AI data centers
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 21:32:34 GMT
  - url: https://www.cnbc.com/2026/08/05/spacex-tesla-megapack-ai-data-centers.html
  - snippet: SpaceX is using Tesla's big Megapack backup batteries to help power its Colossus AI data centers in Greater Memphis.
  - related_tickers: TSLA
  - why_relevant: theme: AI; theme: EV
  - confidence: medium
  - driver_type: context_candidate
  - relevance_score: 4
  - causal_bridge: SpaceX ramps up Tesla Megapack purchases in Q2 to power its AI data centers -> AI/semiconductor demand, expectations, or supply-chain repricing -> SOX, SMH, semiconductor watchlist, TSLA -> title/snippet evidence: ai, data center
  - selected_for_handoff: True
  - filter_reason: Background candidate only; use if it reinforces Core Drivers and market data.
- Jim Cramer says investors should consider buying SpaceX for their kids
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 23:26:03 GMT
  - url: https://www.cnbc.com/2026/08/05/jim-cramer-investors-should-consider-buying-spacex-kids.html
  - snippet: CNBC’s Jim Cramer said investors should view SpaceX as a multigenerational investment, whose biggest opportunities may take decades to fully materialize.
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Etsy laying off 12% of staff in bid to streamline business, position for growth
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 23:20:15 GMT
  - url: https://www.cnbc.com/2026/08/05/etsy-layoffs-q2-earnings.html
  - snippet: Etsy announced the layoffs along with second-quarter earnings.
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: -8
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Hollywood is cranking out billion-dollar movies again. 'Spider-Man' just joined the ranks
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 21:55:46 GMT
  - url: https://www.cnbc.com/2026/08/05/hollywood-2026-billion-dollar-movies.html
  - snippet: Box office analysts say the resurgence of billion-dollar releases bodes well for a film industry that's still chasing pre-Covid levels, even with higher prices.
  - related_tickers: 
  - why_relevant: theme: AI; theme: EV
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- As Warsh and the Fed contemplate fewer meetings, markets brace for potential volatility ahead
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 22:35:26 GMT
  - url: https://www.cnbc.com/2026/08/05/as-warsh-and-the-fed-contemplate-fewer-meetings-markets-brace-for-potential-volatility-ahead.html
  - snippet: Since taking office in May, Warsh has implemented several measures that reverse decades of Fed culture.
  - related_tickers: 
  - why_relevant: theme: EV
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- We're increasing our Eli Lilly price target after another beat-and-raise quarter
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 19:28:32 GMT
  - url: https://www.cnbc.com/2026/08/05/were-increasing-our-eli-lilly-price-target-after-another-beat-and-raise-quarter.html
  - snippet: The strength of its GLP-1 business suggests the stock still has more room to run.
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- China's super-rich 'in shock' and hunting for cash as Beijing issues surprise tax on offshore trusts
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 06:33:47 GMT
  - url: https://www.cnbc.com/2026/08/05/wealthy-chinese-race-for-tax-advice-as-beijing-targets-offshore-trusts.html
  - snippet: Beijing's move to tax offshore trusts, long used by China's ultra-rich to hold money, has set off a rush to lawyers and a scramble for cash.
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Marc Benioff gets a new operating chief, as Salesforce promotes Miguel Milano
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 20:48:20 GMT
  - url: https://www.cnbc.com/2026/08/05/marc-benioff-gets-a-new-coo-as-salesforce-promotes-miguel-milano-.html
  - snippet: Salesforce promoted revenue head and former Oracle executive Miguel Milano to role of operating chief.
  - related_tickers: 
  - why_relevant: theme: EV
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Europe's heatwave isn't cooling Asian travelers' holiday plans for the continent
  - source: CNBC
  - published_at: Tue, 04 Aug 2026 23:27:44 GMT
  - url: https://www.cnbc.com/2026/08/05/europe-heatwave-travel-demand-asia.html
  - snippet: Asian travelers' appetite for Europe remains resilient despite record-breaking heat, with spending in Northern Europe projected to increase.
  - related_tickers: 
  - why_relevant: theme: AI
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- E.l.f. Beauty sees $50 million windfall in tariff refunds as profits surge 100%
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 21:00:48 GMT
  - url: https://www.cnbc.com/2026/08/05/elf-beauty-elf-q1-2027-earnings.html
  - snippet: E.l.f. Beauty received $50 million in tariff refunds during its fiscal first quarter, leading profits to nearly double.
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Trump admin refunds $100 billion in 'liberation day' tariffs
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 19:31:26 GMT
  - url: https://www.cnbc.com/2026/08/05/trump-tariffs-refunds-ieepa-lawsuit.html
  - snippet: The Trump administration has taken steps to effectively re-create the IEEPA tariff regime using other legal authorities. They already face court challenges.
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.
- Wall Street's 'fear gauge' is doing something unusual as stocks hit record highs
  - source: CNBC
  - published_at: Wed, 05 Aug 2026 19:18:31 GMT
  - url: https://www.cnbc.com/2026/08/05/wall-streets-fear-gauge-is-doing-something-unusual-as-stocks-hit-record-highs.html
  - snippet: Stocks and the Cboe Volatility Index move together only about 20% of the time.
  - related_tickers: 
  - why_relevant: 
  - confidence: medium
  - driver_type: low_value_or_irrelevant
  - relevance_score: 0
  - causal_bridge: 
  - selected_for_handoff: False
  - filter_reason: Weak or missing causal bridge to NASDAQ/SOX/AI/large tech.

## 採用候補

### primary_candidates
- title: AI Integration Strengthens Alphabet’s (GOOG) Core Business
  - reason: theme: AI
  - confidence: medium
  - sources: Yahoo Finance, https://finance.yahoo.com/markets/stocks/articles/ai-integration-strengthens-alphabet-goog-162937753.html
- title: Applied Digital Corp (APLD)’s 400% Revenue Surge — Breakout AI Infrastructure Play or Risky Bet?
  - reason: theme: AI; theme: EV
  - confidence: medium
  - sources: Yahoo Finance, https://finance.yahoo.com/technology/ai/articles/applied-digital-corp-apld-400-164148284.html
- title: Nvidia’s stock is basking in the glow of a high-profile endorsement
  - reason: theme: AI; theme: semiconductors
  - confidence: medium
  - sources: MarketWatch, https://www.marketwatch.com/story/nvidias-stock-is-basking-in-the-glow-of-a-high-profile-endorsement-b7c48e7b?mod=mw_rss_topstories

### ticker_candidates
- ticker: MTRN
  - reason: Top Gainers; price move 30.81%; volume above usual level
  - confidence: medium
  - sources: Yahoo Finance
- ticker: WTTR
  - reason: Top Gainers; price move 20.32%; volume above usual level
  - confidence: medium
  - sources: Yahoo Finance
- ticker: SHOP
  - reason: Top Gainers; price move 16.98%; large-cap candidate; volume above usual level
  - confidence: medium
  - sources: Yahoo Finance
- ticker: BSP
  - reason: Top Gainers; price move 16.82%; volume above usual level
  - confidence: medium
  - sources: Yahoo Finance
- ticker: URGN
  - reason: Top Gainers; price move 16.31%; volume above usual level
  - confidence: medium
  - sources: Yahoo Finance

## 未取得情報
- Longbridge: Security news raw JSON is missing. (low)
- Longbridge: Market movers raw JSON is missing. (low)
- FRED: DGS2: FRED_API_KEY is not set. (low)
- FRED: DGS10: FRED_API_KEY is not set. (low)
- FRED: DGS30: FRED_API_KEY is not set. (low)
- FRED: T10Y2Y: FRED_API_KEY is not set. (low)
- FRED: T10Y3M: FRED_API_KEY is not set. (low)
- FRED: DFII10: FRED_API_KEY is not set. (low)
- FRED: T10YIE: FRED_API_KEY is not set. (low)
- FRED: VIXCLS: FRED_API_KEY is not set. (low)
- FRED: DTWEXBGS: FRED_API_KEY is not set. (low)
- FRED: DCOILWTICO: FRED_API_KEY is not set. (low)
- FRED: DCOILBRENTEU: FRED_API_KEY is not set. (low)
- FMP: FMP_API_KEY is not set. (low)
- SEC EDGAR / company IR: SEC_USER_AGENT is not set; SEC requests were not sent. (low)
- SerpAPI: SERPAPI_API_KEY is not set. Search supplement skipped. (medium)
- Tavily: TAVILY_API_KEY is not set. Search supplement skipped. (medium)
- Market Movers: Premarket Movers: No stable free RSS/JSON source is configured for this category in Phase 1.9. (low)
- Market Movers: After Hours Movers: No stable free RSS/JSON source is configured for this category in Phase 1.9. (low)
- Economic Calendar: BLS CPI RSS: HTTPError: 403 Client Error: Forbidden for url: https://www.bls.gov/feed/cpi.rss (low)
- Economic Calendar: BLS PPI RSS: HTTPError: 403 Client Error: Forbidden for url: https://www.bls.gov/feed/ppi.rss (low)
- Economic Calendar: BLS Employment Situation RSS: HTTPError: 403 Client Error: Forbidden for url: https://www.bls.gov/feed/empsit.rss (low)
- GDELT Radar: ai_chip_compute query failed: HTTPError: 429 Client Error: Too Many Requests for url: https://api.gdeltproject.org/api/v2/doc/doc?query=%28Nvidia+OR+AMD+OR+Broadcom+OR+TSMC+OR+%22AI+chip%22+OR+semiconductor+OR+GPU%29+%28AI+OR+datacenter+OR+compute%29&mode=ArtList&format=json&maxrecords=10&sort=DateDesc&timespan=3d (low)
- GDELT Radar: platform_ai query failed: HTTPError: 429 Client Error: Too Many Requests for url: https://api.gdeltproject.org/api/v2/doc/doc?query=%28Microsoft+OR+Google+OR+Alphabet+OR+Meta+OR+Amazon+OR+Apple%29+%28AI+OR+artificial+intelligence+OR+cloud%29&mode=ArtList&format=json&maxrecords=10&sort=DateDesc&timespan=3d (low)
- GDELT Radar: robotics_autonomy query failed: HTTPError: 429 Client Error: Too Many Requests for url: https://api.gdeltproject.org/api/v2/doc/doc?query=%28robotics+OR+robot+OR+autonomous+driving+OR+humanoid+robot%29+%28AI+OR+chip+OR+Tesla+OR+Nvidia%29&mode=ArtList&format=json&maxrecords=10&sort=DateDesc&timespan=3d (low)
