# Methodology

This document expands the [README](../README.md)'s methodology. It describes **how each
measurement is constructed**, the data sources, the population definitions, the
statistical objects, and the caveats, at the level of the filing corpus and screened
cohorts. Consistent with the project's scope, nothing here names or characterizes an
individual issuer; every quantity is a count, share, distribution, or regression
coefficient over a population.

---

## 1. Data sources (all public)

| Source | Endpoint / dataset | Used for |
|---|---|---|
| EDGAR full-text search (FTS) | `efts.sec.gov/LATEST/search-index` | Filing-level phrase counts; SIC aggregations. Covers filings from 2001 onward. |
| EDGAR full-index | `www.sec.gov/Archives/edgar/full-index/{year}/QTR{q}/master.idx` | The rigorous filing-level **denominator** (distinct 10-K filers per year). |
| EDGAR submissions API | `data.sec.gov/submissions/CIK{cik}.json` | Filing history, form types, dates, former names. |
| EDGAR XBRL company facts | `data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` | Fundamentals (R&D, revenue, cash, net income) for resource-mismatch measures. |
| Ken French Data Library | `mba.tuck.dartmouth.edu/.../ken.french/...` | FF5 + momentum daily/monthly factors for abnormal returns. |
| Free market data | stooq (default), yfinance (fallback) | Daily adjusted closes for event-study and premia prototyping. |

**SEC fair access.** Every EDGAR request declares a real `User-Agent` contact string and
is rate-limited to stay under the SEC's 10 requests/second guidance. Scripts cache every
response under a local `data/` directory (git-ignored) so reruns are instant and jobs are
resumable if a source throttles. No source requires an API key.

**A note on FTS caps.** EDGAR FTS returns a capped total (`hits.total.value`, relation
`gte` at the cap). Where an exact filer count matters (e.g., the prevalence denominator),
the pipeline uses the **master index**, the complete filing-level population, rather
than the FTS total. This is the single most important correctness fix in the label-
measurement layer.

---

## 2. The label-decoupling measurements (market-wide)

The claim is that the *information content* of the "AI" label has fallen: the label
spread faster than the substance behind it. Four independent cuts, each a ratio or trend
over the full corpus:

- **Prevalence** (`ai_prevalence.py`). Numerator: 10-Ks matching a quoted AI phrase in
  year *t*, from FTS. Denominator: distinct 10-K filers in year *t*, from the master
  index. Phrases are **quoted** so phrase search avoids token false positives (electrical
  "transformers", sales "agents"). Output is a share-of-filers time series.

- **Marketing vs. substance lexicon** (`ai_lexicon.py`). The same filer denominator, but
  the numerator is split into buckets: *core* AI terms, *marketing* superlatives
  ("AI-powered", "AI-driven"), *substance/build* vocabulary ("large language model",
  "training compute", "fine-tuning"), *aspirational*, *governance*, and *new-hype*
  phrases. The **marketing:substance ratio** is the washing fingerprint at the population
  level, cheap marketing language diffuses while costly build vocabulary stays pinned.

- **Sector diffusion** (`ai_sector.py`). FTS `sic_filter` aggregation for the core AI
  phrase, by year. The measurement is the **share of AI mentions originating in SIC-73
  (software)** over time; a falling share means the label diffused *out* of its native
  sector ("AI tourists").

- **Informativeness** (`informativeness.py`). A year-over-year measure of how much the
  label still predicts firm capability. A declining series means each marginal use of the
  label carries less information than it did the year before.

**Ecological-inference guard** *(per-filing version private)*. Population ratios cannot classify an
individual filing (that would be an ecological-inference error). The per-*filing*
statistic, among filings that use marketing AI language, what share contain **zero**
technical-substance language in the same document, is computed separately and validated
on a labeled set, so the discriminating claim is made at the level where it is identified.

---

## 3. Cohort construction (the nano/micro-cap tail)

The "naked decoupling" lives in the small-cap tail. The cohort is built by a transparent
screen, **not** by selecting individual names. The cohort-construction and structural-measure
code below is the **private issuer-level pipeline** (excluded from this repo per the
[Scope](../README.md#scope-what-is-not-here) section); the descriptions are kept here because the
*method* is not secret and the *findings* are aggregate, but the scripts and any per-issuer
output stay private:

1. **Theme-pivot screen** *(private)*. Surfaces candidate filers whose disclosure pivots into a
   hot narrative, from FTS + submission history.
2. **Cleaning filter** *(private)*. Applies market-cap and prior-collapse thresholds to reduce
   the candidate set to a clean nano/micro-cap population.
3. **Shell-source attribution** *(private)*. Classifies each cohort member's lineage (repainted
   operating company vs. de-SPAC vs. non-SPAC shell) and dates the vintage.

The cohort is the *output of the screen* and is treated throughout as a **population** whose
properties (shares, rates, distributions) are reported, never as a roster of suspects.

---

## 4. Structural measures over the cohort

Each of these is a rate or distribution over the screened population:

- **Dilution / disclosure-routing instrument** *(private; market-wide version ships in
  `screen/` as `sec16_evasion`)*. The share of the cohort carrying the pre-funded-warrant +
  ownership-blocker + high-dilution combination, from filing text and capital-structure
  disclosures.
- **Financier concentration** *(private)*. A bipartite fund↔issuer incidence count; the headline
  is a concentration statistic (few funds touching many issuers), not a named list.
- **Gatekeeper concentration** *(private; market-wide version ships in `screen/` as
  `auditor_market` / `auditor_churn`)*. Auditor-size skew, going-concern / material-weakness
  rates, and the **direction** of auditor churn (Item 4.01), as population rates.
- **Capital decomposition** *(private)*. Aggregate raised, placement fees, post-raise drawdown
  distribution, dilution multiples, and an order-of-magnitude **envelope** of peak market value
  destroyed. Envelope, not a point estimate.
- **Cross-border structure** *(private; market-wide CFIUS/foreign version ships in `screen/` as
  `foreign_control`)*. A foreign-control census share, a narrative-rotation rate (issuers wearing
  ≥2 hot themes), and a cohort-level screen of offshore counterparty structure.

---

## 5. The disciplining nulls (kept prominently)

Good measurement reports what it **fails** to find. These nulls are first-class results:

- **Size, not "hollowness"** *(private)*. The apparent "hollow firm = washer" resource gap is
  largely a **size effect**: a size-controlled classifier adds only ~+0.01 AUC. Public data
  resolves the washing signal only in the extreme small-cap tail; it does not separate mid/large
  caps.
- **The premium is a large-cap phenomenon** (`sector_premium.py`, `size_premium.py`,
  `ff_alpha.py`). The sustained AI return premium is concentrated in large/mega caps
  (sector-neutral, positive); small-cap AI-mentioners earn **negative** abnormal returns.
- **Enforcement does not re-separate the cross-section** (`event_study.py`,
  `event_study/`). A cross-sectional event study with **event fixed effects** tests
  whether AI-washing enforcement news restores a substance gradient in returns. It does
  not, with clean placebos: (a) non-AI firms show no gradient; (b) the pre-event window
  shows no gradient.
- **Severity is not the cross-border margin** *(private)*. Foreign-controlled shells show the
  **same** drawdown as domestic ones; the difference is *recoverability*, not harm magnitude, a
  disciplined severity null.

---

## 6. Event-study identification

The enforcement event study (`event_study/`) is the most identification-sensitive piece,
so its design is spelled out:

- **Abnormal returns.** FF5 + momentum factor model; CAR over an event window per
  (firm, event) pair.
- **Estimating equation.** `CAR_{i,e} = α_e + β·Substance_i + δ·ln(MktCap)_i + sectorFE +
  ε`. Event fixed effects `α_e` absorb the common per-event shock; the coefficient of
  interest `β` is identified off the **cross-sectional substance gradient**, not the
  average event reaction.
- **Matched controls** (`event_study/matching.py`). For each event firm, K "clean" peers
  that did not make an AI capability claim, matched on industry (2-digit SIC), size, and
  price, a Cooper–Dimitrov–Rau-style counterfactual for the name/label effect.
- **Placebos.** Non-AI firms (no gradient expected) and a pre-event window `[-5,-2]`
  (no gradient expected). Both are reported alongside the main estimate.

---

## 7. Reproducibility and caveats

- **Determinism.** Given the same public sources on the same date, the scripts reproduce
  the same numbers. Because EDGAR and market data accrue over time, absolute counts drift
  as new filings arrive; the **shapes and ratios** are the stable objects.
- **Caching.** All raw pulls are cached under `data/` (git-ignored). Delete a cache file
  to force a re-fetch. Jobs are resumable after throttling.
- **Free market data.** stooq/yfinance are used for prototyping the premia and event
  study; coverage gaps in free sources are a known limitation and are handled by the
  matched-control design rather than assumed away. A CRSP path exists for users with a
  license.
- **Uncertainty.** The one figure computed from a firm-level sample, the
  informativeness R&D-intensity premium (`informativeness.py`, F4), is reported with
  95% bootstrap confidence intervals (2,000 resamples, fixed seed). The prevalence,
  lexicon, sector, and placebo figures are near-complete counts of filings, not
  samples, so they carry no sampling error; their uncertainty is in the phrase
  definitions, not in sampling, and no interval is drawn for them.
- **Size control (F4).** To separate the premium's decline from a change in the size
  mix of AI-labeled firms, the premium is also recomputed within total-assets terciles
  (cut on the baseline, from the XBRL `Assets` instantaneous frame) and averaged across
  terciles, comparing AI firms only to non-AI firms of similar size. It is reported with
  its own stratified bootstrap CI. The size-adjusted premium is higher than the raw and
  still declines, so composition does not explain the fall, though its CI is wider.
- **Envelopes vs. point estimates.** Capital-destruction figures are explicitly
  order-of-magnitude envelopes with stated bounds, not precise damages estimates.
- **Population framing.** Every cohort statistic is a property of a screened population.
  No number here identifies, ranks, or characterizes an individual issuer; that
  separation is deliberate and load-bearing (see the README's Scope section).

---

*This measurement layer is reproducible entirely from public SEC and market data. The
research design, measurement choices, interpretation, and verification are the author's;
AI was used as a coding and large-scale-review tool.*
