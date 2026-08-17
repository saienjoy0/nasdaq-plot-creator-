# 朝のNASDAQカフェ｜Daily Source Package 2026-08-17

- Episode date (JST): 2026-08-17
- Research trading date (US): 2026-08-14
- Information cutoff: 2026-08-17T04:59:02Z
- Collector issue: https://github.com/saienjoy0/nasdaq-cafe-news-collector/issues/25
- Collector child run: https://github.com/saienjoy0/nasdaq-cafe-news-collector/actions/runs/31996046759
- Collector artifact: nasdaq-cafe-2026-08-17
- Artifact SHA-256: 7d42696b209cb891ecbabc59be5490c6b9338aefd57d9ee753b25539fe85faf6
- Collector main: 42908709f8044ba8d7a836d67fbe9b715f4b7790

## 1. Fresh market facts from Collector / Longbridge

The collector resolved the latest completed regular U.S. session to 2026-08-14 (NYSE calendar).

### Nasdaq Composite
- ticker: .IXIC
- regular close: 26,729.164
- previous close: 26,803.025
- change: -73.861 / -0.28%
- open: 26,851.148
- high: 26,862.167
- low: 26,661.954
- volume: 6,405,507,373
- Note: the index opened above the previous close and finished lower.

### Semiconductor aggregate
Collector field name is `SOX`, but the actual instrument is **SOXX ETF** (`SOXX.US`), not the PHLX SOX index.
- SOXX close: 550.420
- previous close: 550.740
- change: -0.06%
- open: 549.580
- high: 552.890
- low: 542.930

### Selected semiconductor / large-tech moves
- AMAT: -5.12% (Nasdaq Market Activity mover)
- AVGO: -5.94% (Longbridge watch quote)
- AMD: +6.50% (Longbridge watch quote)
- NVDA: -0.06%
- TSM: -0.96%
- META: -0.86%
- AMZN: -0.94%

These prices show dispersion rather than a one-directional semiconductor collapse.

## 2. Applied Materials primary / major-reporting evidence

### Prior company guidance — official Applied Materials IR
Applied Materials Q2 FY2026 results, May 14, 2026:
https://investor.appliedmaterials.com/news-releases/news-release-details/applied-materials-announces-second-quarter-2026-results

For Q3 FY2026, Applied guided:
- Revenue: $8.95B ± $0.50B
- Non-GAAP diluted EPS: $3.36 ± $0.20

### Q3 timing — official Applied Materials IR
Q3 FY2026 earnings conference call:
https://investor.appliedmaterials.com/events/event-details/q3-2026-applied-materials-earnings-conference-call
- Aug. 13, 2026 at 4:30 PM EDT

### Q3 results and Street expectations — Reuters
https://www.reuters.com/business/applied-materials-forecasts-quarterly-revenue-above-estimates-2026-08-13/

Reuters reported:
- Q3 revenue: $9.12B, versus LSEG estimate $8.99B
- Q4 revenue guide: about $10.25B ± $0.50B, versus LSEG estimate $9.54B
- Q4 adjusted EPS guide: $4.02 ± $0.20, versus estimate $3.69
- Shares fell more than 5% in extended trading despite the beat-and-raise profile.
- Reuters described investor expectations as elevated after strong peer results and a more-than-doubling of AMAT shares in 2026.
- Applied expected calendar-2026 advanced-packaging revenue growth above 70%, up from its prior >50% view.
- Management said some customer visibility extended to 2030.

Interpretation boundary:
Formal consensus was beaten. “The market expected even more” is a reported market interpretation, not a fabricated numeric consensus.

## 3. Friday macro overlay and Nasdaq close

### Reuters U.S. market close
https://www.reuters.com/business/wall-st-futures-muted-higher-oil-prices-temper-risk-appetite-after-sp-record-2026-08-14/

Reuters reported:
- Nasdaq: -0.28% to 26,729.16
- Applied Materials: -5.1%
- Broadcom: -5.9%
- weak-than-expected July retail sales
- renewed Strait of Hormuz tension / higher oil prices
- high valuation nerves around AI-related stocks

Reuters also quoted the market interpretation that Applied had a “beat and raise,” but expectations were high and the stock sold off.

### Census release timing — official
https://www.census.gov/retail/release_schedule.html
- July 2026 Advance Monthly Retail Sales release: Aug. 14, 2026 at 8:30 AM ET

### Retail sales actual / expectation — Reuters
https://www.reuters.com/world/asia-pacific/yens-slide-weekly-loss-prompts-bets-another-intervention-2026-08-14/
- July U.S. retail sales: -0.6% m/m
- Economists had expected a slight rise.
- The weak data reduced the perceived chance of a September Fed rate hike.

This creates an offsetting channel for growth stocks: weaker consumption can hurt growth expectations, while lower hike expectations can support duration-sensitive technology valuations.

### Global markets / oil — Reuters
https://www.reuters.com/world/china/global-markets-wrapup-1-2026-08-14/
- Oil rose more than $1/bbl amid faltering U.S.-Iran talks / blockade risk.
- Nasdaq finished -0.28%.
- U.S. Treasury prices initially rallied after retail sales, but that move lost momentum.
- Geopolitical risk remained an important macro uncertainty.

## 4. Editorially safe conclusions from the evidence

Confirmed facts:
1. AMAT’s formal numbers and forward guide were above cited Street estimates, yet its stock fell sharply.
2. The negative AMAT reaction began in extended trading on Aug. 13, before the Aug. 14 8:30 ET retail-sales release.
3. On Aug. 14 the Nasdaq opened above its previous close, then finished -0.28%.
4. Semiconductor reactions were split: AMAT and AVGO fell hard, AMD rose, and SOXX ETF was nearly flat.
5. Retail sales were unexpectedly weak and oil / Hormuz risk was higher.

Supported interpretation:
- AMAT is the cleanest protagonist because it exposes an “expectations bar” problem: beat-and-raise was not enough for a stock with elevated AI expectations.
- Friday’s Nasdaq move cannot safely be attributed to AMAT alone.
- A two-engine explanation is more defensible: selective AI/semiconductor expectation repricing plus a macro overlay from weak consumption / oil-geopolitical uncertainty.
- Weak retail is not a one-way bearish technology catalyst because it also reduced rate-hike expectations.

Counterevidence that must remain:
- AMD +6.50%
- SOXX ETF -0.06%
- Nasdaq opened above the previous close after the retail release
- AMAT reported continued AI-related demand strength / advanced packaging growth
- Exact contribution weights among AMAT, broader chip valuation nerves, retail sales, and oil/Hormuz are unresolved.

## 5. Acquisition caveats

Collector `missing_data` includes unavailable FRED series, no SEC user agent, and missing SerpAPI/Tavily keys. Do not invent yields, VIX, WTI/Brent exact close values, or SEC facts from those unavailable channels.
The Collector field called `SOX` is backed by `SOXX.US`; production must call it **SOXX ETF**, not the PHLX SOX index.
