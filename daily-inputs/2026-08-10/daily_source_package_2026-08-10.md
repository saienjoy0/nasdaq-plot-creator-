# 朝のNASDAQカフェ｜Daily Source Package｜2026-08-10

## Collector provenance
- Collector repo: `saienjoy0/nasdaq-cafe-news-collector`
- Broad collection issue: #5
- Broad collection run: `31351839881`
- Artifact: `nasdaq-cafe-2026-08-10`
- Artifact digest: `sha256:0d75a08870e531cc417f9fe9b3386694502a912a8c3ef697a434b86b17ed2d44`
- Generated at: 2026-08-10T03:14:52Z
- Acceptance note: collector handoff declared `market_session_date_us: 2026-08-09`, but 2026-08-09 is Sunday. Quote timestamps and market context correspond to the Friday 2026-08-07 US session. Treat 2026-08-07 as the candidate market session pending validation.

## Broad market
- NASDAQ Composite: 26,690.615, +342.263, +1.30%; open 26,534.660; high 26,712.617; low 26,478.006; previous close 26,348.352. Raw source: Longbridge.
- SOXX: 543.270, +10.750, +2.02%; open 545.200; high 547.904; low 531.270; previous close 532.520. Raw source: Longbridge.
- SOXX pre-market last: 545.200; post-market last: 544.110; overnight last at 2026-08-10T03:08:50Z: 545.780.

## Fixed watchlist
- NVDA 223.960, +2.27%
- MSFT 499.990, +0.03%
- AAPL 313.330, +0.29%
- AMZN 274.480, +0.82%
- GOOGL 354.300, -0.96%
- META 592.100, +0.37%
- AVGO 427.760, +1.71%
- TSM 420.040, +0.44%
- AMD 483.360, -1.21%
- TSLA 328.580, +2.83%

## Market movers
- MCHP +13.89% (Nasdaq Market Activity). Semiconductor-related.
- GFS +7.09% (Longbridge quote).
- ENTG +6.61% (Longbridge quote).
- MRVL +3.89% (Longbridge quote).
- SWKS +5.66% (Longbridge quote).
- QCOM +4.66% (Longbridge quote).
- ABNB +17.43% (Nasdaq Market Activity).

## Broad collector lead suggestion — NOT YET ACCEPTED
Collector mechanically selected an AMD article as a core driver:
- Yahoo Finance: `AMD Tops Q2 Estimates, but Investors Still Hit the Sell Button. What's Next for AMD Stock.`
- URL: https://finance.yahoo.com/markets/stocks/articles/amd-tops-q2-estimates-investors-151502222.html
- Published: 2026-08-08T15:15:02Z
- AMD itself was -1.21% while NASDAQ was +1.30% and SOXX +2.02%; therefore this material must not be promoted automatically to a NASDAQ-wide cause.

## Current Causal Research candidates
### Candidate A — July US Employment Situation / rates channel
- BLS scheduled the July 2026 Employment Situation for Friday 2026-08-07 at 8:30 AM ET.
- Reuters reported that US payrolls unexpectedly fell by 23,000 versus an expectation for +80,000, reducing perceived odds of a September Fed rate hike; Nasdaq closed +1.30%.
- Reuters market report: https://www.reuters.com/business/sp-500-dow-futures-muted-ahead-jobs-data-chips-software-stocks-rise-2026-08-07/
- Official BLS release target for exact-url retrieval: https://www.bls.gov/news.release/empsit.nr0.htm

### Candidate B — Microchip earnings as semiconductor amplifier
- Microchip Q1FY27 conference call was scheduled for Thursday 2026-08-06 at 5:00 PM ET.
- Official IR calendar: https://ir.microchip.com/news-events/ir-calendar/detail/20260806-microchips-q1fy27-financial-results-conference-call
- MCHP rose about 13.9% on Friday. Major reporting says stronger-than-expected earnings and guidance contributed to the semiconductor rally.
- Treat as a sector amplifier unless evidence shows it explains NASDAQ-wide movement.

### Candidate C — AMD divergence / counterevidence
- AMD -1.21% while SOXX +2.02% and NASDAQ +1.30%.
- This weakens a simple story that AMD-specific earnings disappointment was the session-wide driver.

## Missing evidence / follow-up candidates
- QQQ minute data around 8:30 AM ET and regular open on 2026-08-07.
- SOXX minute data around 8:30 AM ET and regular open.
- MCHP minute data to distinguish company-specific earnings reaction from macro move.
- NVDA minute data as a large AI/semiconductor comparator.
- BLS July Employment Situation exact official text.
- If available, official Microchip earnings release / filing for Q1FY27.

## Current missing broad inputs
- QQQ broad quote missing from collector package.
- FRED DGS10/DGS2/VIX unavailable because FRED_API_KEY was not set.
- SEC/IR collector path unavailable because SEC_USER_AGENT was not set.
- SerpAPI/Tavily unavailable in collector run.

## Editorial constraint
Do not write the final 9-scene script before the follow-up acquisition is closed. Use minute data as chronology evidence only; it does not prove causality by itself.
