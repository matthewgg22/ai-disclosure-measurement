# Codebook — `data/aggregates/`

Every file here is a **market-wide aggregate**: one row per year (or per year × category), no
individual issuer named or ranked. These CSVs are the committed inputs to
[`pipeline/make_figures.py`](../pipeline/make_figures.py) and the only data that crosses the
public wall (see the [Scope](../README.md#scope-what-is-not-here) section and
[`docs/METHODOLOGY.md`](METHODOLOGY.md)). Issuer-level intermediates are regenerated into
a local `data/` cache on run and are never committed.

**Common conventions.** `year` is the filing/fiscal year. `n_10k_filers` is the denominator of
distinct 10-K filers that year (EDGAR full-text search universe). Percentages are in **percentage
points** (e.g. `50.7` = 50.7%), not fractions, unless a column name ends in a units suffix noted
below. Coverage is 2001–2025 for the text series; the screen and validation series start later
(data availability noted per file). Missing/undefined values are the literal string `None`.

**Provenance.** Text series: EDGAR full-text search (`efts.sec.gov`) over 10-K filings. Screen
series: EDGAR FTS + PCAOB Form AP (auditor engagements) + SEC XBRL frames (`data.sec.gov`).
Validation: exported aggregate statistics from the private issuer-level run (PCAOB Form AP
histories, XBRL assets, SEC enforcement/suspension listings resolved to CIK); only the aggregate
AUC/lift rows cross into this repo.

---

## `ai_prevalence.csv` — AI-label prevalence (F1)
One row per year, 2001–2025.

| column | unit | meaning |
|---|---|---|
| `year` | year | filing year |
| `n_10k_filers` | count | distinct 10-K filers that year (denominator) |
| `n_artificial_intelligence` | count | filers using "artificial intelligence" |
| `n_machine_learning` | count | filers using "machine learning" |
| `n_generative_ai` | count | filers using "generative AI" |
| `pct_artificial_intelligence` | pp | `n_artificial_intelligence / n_10k_filers × 100` |
| `pct_machine_learning` | pp | share using "machine learning" |
| `pct_generative_ai` | pp | share using "generative AI" |

## `ai_buckets_by_year.csv` — functional vocabulary buckets (F2)
One row per year. Each bucket is the share of 10-K filers using **any** term in that bucket; a
filer can appear in several buckets, so columns do not sum to 100. Bucket term lists are defined in
[`pipeline/ai_lexicon.py`](../pipeline/ai_lexicon.py).

| column | unit | meaning |
|---|---|---|
| `year` | year | filing year |
| `n_10k_filers` | count | denominator |
| `A_core` | pp | core terms ("artificial intelligence", "machine learning", "deep learning") |
| `B_marketing` | pp | **marketing** framing ("AI-powered", "AI-driven", "AI-native", "powered by AI") |
| `C_substance` | pp | **build/substance** terms ("large language model", "foundation model", "transformer model") — the costly-to-fake vocabulary |
| `D_aspirational` | pp | aspirational ("artificial general intelligence", "superintelligence", "frontier model") |
| `E_governance` | pp | governance ("responsible AI", "explainable AI", "AI governance") |
| `F_hype_new` | pp | recent hype ("generative AI", "agentic AI", "AI agent", "prompt engineering") |

The washing signature is `B_marketing ≫ C_substance`: marketing vocabulary spreads without the
build vocabulary following.

## `ai_sector_by_year.csv` — sector diffusion (F3)
One row per year × 2-digit SIC sector.

| column | unit | meaning |
|---|---|---|
| `year` | year | filing year |
| `sic2` | code | 2-digit SIC code |
| `sector` | text | human-readable sector label |
| `ai_mention_count` | count | AI-mentioning filers in that sector-year |
| `pct_of_ai_filings` | pp | that sector's share of all AI-mentioning filers that year |

Software (SIC-73) `pct_of_ai_filings` falling from ~57% (2018) to ~27% (2025) is the diffusion-out-
of-software result.

## `informativeness.csv` — label information content (F4)
One row per measured year (2015, 2018, 2021, 2024, and one pooled). The disciplining null: the
AI-label's link to audited R&D decays to insignificance.

| column | unit | meaning |
|---|---|---|
| `year` | year | fiscal year |
| `ai_firms` | count | AI-labeled 10-K filers in the R&D sample |
| `pct_ai_reporting_rnd` | pp | share of AI filers reporting **any** R&D expense |
| `ai_median_rnd_intensity` | ratio | median R&D / assets among AI filers |
| `baseline_median_rnd_intensity` | ratio | median R&D / assets, all filers |
| `substance_premium` | ratio | AI minus baseline median R&D-intensity (the information content) |
| `premium_ci_lo`, `premium_ci_hi` | ratio | 95% bootstrap CI on `substance_premium` |
| `premium_size_adj` | ratio | premium vs non-AI firms in the **same total-assets tercile** (`None` where undefined) |
| `premium_size_adj_lo`, `premium_size_adj_hi` | ratio | 95% CI on the size-adjusted premium |
| `rnd_reporters_total` | count | total R&D reporters that year (context) |

Premium `+0.036 [0.014, 0.066]` in 2018 (excludes 0) → `+0.009 [−0.014, 0.030]` in 2024 (includes
0): real then, gone by 2024.

## `placebo_terms.csv` — buzzword placebo (F5)
One row per year × term. Same marketing template applied to AI and to control buzzwords.

| column | unit | meaning |
|---|---|---|
| `year` | year | filing year |
| `term` | text | buzzword tested (`AI`, `blockchain`, `cloud`, `quantum`, …) |
| `n_10k_filers` | count | denominator |
| `mention_pct` | pp | share of filers with a **bare** mention of the term |
| `marketing_pct` | pp | share with the **"<term>-powered"/"<term>-driven"** marketing form |

Only AI shows a large `marketing_pct` (12.9% in 2025 vs ≤0.18% for controls): the marketing
behavior is AI-specific, not generic buzzword behavior.

## `screen_registry.csv` — regulatory-surface prevalence (F6 and the screen)
One row per year × signal. The market-wide prevalence of each regulatory surface the engine
tracks. Surface definitions, citations, and instrument groups are in
[`screen/registry.py`](../screen/registry.py) and [`docs/SCREEN.md`](SCREEN.md).

| column | unit | meaning |
|---|---|---|
| `year` | year | filing/fiscal year |
| `instrument` | A–F | regulatory instrument group (see below) |
| `signal_id` | text | surface + sub-signal (e.g. `sec16_evasion.paired`, `auditor_churn.backstop_top10_share`) |
| `n` | count | numerator (filers/engagements exhibiting the signal) |
| `n_filers` | count | signal-specific denominator (see `denom_source`) |
| `pct` | pp | `n / n_filers × 100` |
| `denom_source` | text | which denominator `pct` uses (see below) — kept explicit because surfaces draw on different universes |

**Instrument groups** (breadth of SEC regulation made computable): **A** Ownership & insider
disclosure (§16/§13(d)) · **B** Periodic-disclosure quality (going concern, material weakness) ·
**C** Auditor & gatekeeper (PCAOB Form AP: market share, churn) · **D** Capital formation (dilution
instruments) · **E** Trigger events (restatements, late filings, enforcement) · **F** Entity &
market structure (shell lineage, cross-border).

**`denom_source` values.** `10k_filers` = distinct 10-K filers · `filing_count_over_10k` = filings
normalized by filer count · `pcaob_audit_engagements` = PCAOB Form AP engagements ·
`xbrl_annual_join` = issuers with the needed annual XBRL facts · `xbrl_firm_quarters` = firm-quarter
XBRL observations · `xbrl_q4_intersection` = issuers present in the Q4-instant XBRL frame. Per-
signal denominators are reported honestly rather than forcing one denominator across surfaces of
different origin.

## `validation_summary.csv` — out-of-sample validation (F7)
One row per (label, design). The forward-validation headline: an auditor-distress score measured
through FY2021 predicts 2022+ regulatory failure. See [`docs/RESULTS.md`](RESULTS.md) F7.

| column | unit | meaning |
|---|---|---|
| `year` | year | outcome-window start (2022) or cross-section year (2016 for AAER) |
| `label` | text | outcome label: `aaer`, `twelve_j`, `failure` (12(j) ∪ suspension), `delisting` |
| `design` | text | `forward_score_thru_2021` (temporal split) or `cross_sectional` |
| `n` | count | issuers in the scored universe |
| `positives` | count | issuers hit by the outcome |
| `base_rate_pct` | pp | `positives / n × 100` |
| `auc_size_only` | AUC | AUC of firm size alone. **0.11 means small firms fail *much* more**, not that size is irrelevant — see the note below |
| `auc_score_raw` | AUC | AUC of the distress score, unadjusted |
| `auc_score_size_adj` | AUC | **headline**: AUC computed within size terciles (Mann-Whitney) |
| `ci_lo`, `ci_hi` | AUC | 95% bootstrap CI on the size-adjusted AUC |

`failure` reads AUC 0.732, CI (0.578, 0.773). The `aaer` (0.564) and `delisting` (0.492) rows are
the **pre-registered nulls** that came back null — the labels the score should *not* predict, and
doesn't.

## `validation_lift.csv` — decile lift for F7
One row per (label, score decile).

| column | unit | meaning |
|---|---|---|
| `year` | year | outcome-window start (2022) |
| `label` | text | outcome label (matches `validation_summary.csv`) |
| `decile` | 1–10 | score decile (1 = lowest distress score, 10 = highest) |
| `bad_rate_pct` | pp | failure rate within that decile |

Monotone lift — ~0% in the bottom deciles rising to ~6–7% in the top — is the visual of the AUC.

---

# Revelation and event-study aggregates (F8)

Population-level outputs behind [`REVELATION.md`](REVELATION.md). Building the revelation calendar
and estimating issuer-level abnormal returns happens in a separate private repository; only these
group-level counts and statistics cross into this one. The `year` column carries a vintage where a
result is per-vintage and the span `2022-2024` where it is pooled.

## `forward_vintage_summary.csv` — the screen, forward, per vintage
One row per feature year.

| column | unit | meaning |
|---|---|---|
| `year` | year | feature year; outcomes run the following 20 months |
| `n` | count | issuers with a price series and XBRL assets |
| `base_rate_pct` | % | share suffering a 50% loss or delisting |
| `auc_size_adj` | AUC | **headline**: computed within size terciles |
| `ci_lo`, `ci_hi` | AUC | 95% bootstrap CI |
| `auc_size_only` | AUC | size alone; 0.23 means small firms fail *much* more (see note under `validation_summary.csv`) |

## `forward_by_warning_signs.csv` — the ordering
One row per (year, warning-sign count).

| column | unit | meaning |
|---|---|---|
| `warning_signs` | 0–4 | count of pillars firing in that year's 10-K |
| `median_fwd_return_pct` | % | median return over the following 20 months |
| `severe_rate_pct` | % | share suffering a 50% loss or delisting |
| `loss_pct_of_float` | % | realized loss as a share of public float |

The first sign-count whose median falls below −25% is **2** in all three vintages. That the
threshold does not drift by regime matters more than the AUC point estimate.

## `revelation_calendar.csv` — the events
One row per event type. Mandatory SEC filings whose trigger is defined by rule, so dates are set by
the issuer's legal obligation rather than chosen with hindsight.

| value of `event_type` | filing | meaning |
|---|---|---|
| `R_NONRELIANCE` | 8-K Item 4.02 | previously issued financials should no longer be relied upon |
| `R_LISTING` | 8-K Item 3.01 | failure to satisfy a continued-listing rule |
| `R_AUDITOR` | 8-K Item 4.01 | change in certifying accountant |
| `R_LATE` | NT 10-K / NT 10-Q | inability to file on time |

## `revelation_incidence.csv` — who gets caught
One row per (year, outcome, variant, sample, warning-sign count).

| column | unit | meaning |
|---|---|---|
| `outcome` | text | `y_nonrel`, `y_listing`, `y_any` (within 20 months), `y_listing_12m` |
| `variant` | text | signal set: `FULL`, `NO_RSS` (drops the reverse-split surface), `NO_P4`, `TEXT_ONLY` |
| `sample` | text | `ALL`, or `NOPRIOR` = issuers with no listing notice before the 10-K |
| `rate_pct` | % | share of that bucket with the outcome |

**Quote the `NOPRIOR` / `y_nonrel` rows.** The `ALL` / `y_listing` rows are inflated by two
artefacts documented in [`REVELATION.md`](REVELATION.md): firms reverse-split *to cure* a bid-price
deficiency, and issuers already under a notice can receive another.

## `revelation_discrimination.csv` — the same, as AUC
One row per (year, outcome, variant, sample).

| column | unit | meaning |
|---|---|---|
| `auc_size_adj`, `ci_lo`, `ci_hi` | AUC | size-stratified AUC and 95% bootstrap CI |
| `auc_size_only` | AUC | size alone; 0.19–0.33 means small firms fail *much* more, so ~44–50% of the raw gradient is size |
| `monotone` | 0/1 | whether incidence rises at every step |
| `lift_top_over_bottom` | ratio | top bucket rate ÷ bottom bucket rate |

## `tier_a_precision.csv` — the structural detectors, as triggers
One row per (detector, outcome).

| column | unit | meaning |
|---|---|---|
| `detector` | text | `A1` share explosion, `A3` manufactured asset, `A4` period inconsistency |
| `precision_pct` | % | share of flagged issuers with the outcome |
| `lift` | ratio | precision ÷ base rate — **the comparable statistic** |
| `recall_pct` | % | share of all outcomes the flag caught |
| `fisher_p` | p | one-sided Fisher exact test |
| `auc_observed` | AUC | reported only to be compared against the next column |
| `auc_ceiling` | AUC | highest AUC a binary flag at this firing rate could reach |

**Do not read `auc_observed` on its own.** For a binary flag AUC is (sensitivity + specificity)/2,
so a flag firing on 0.2% of the population is pinned near 0.5 whatever its precision. Compare it to
`auc_ceiling` (`screen/eventstudy.auc_ceiling`), and use `precision_pct` and `lift` for triggers.
`A4` is a **failure** — four firms, zero outcomes — and is kept for that reason.

## `car_by_event_type.csv` — what the market pays
One row per (event type, window).

| column | unit | meaning |
|---|---|---|
| `window` | text | trading days relative to the filing; `PLACEBO[-10,-3]` is the pre-event check |
| `mean_car_pct` | % | mean cumulative abnormal return vs the Russell 2000, **winsorized 1/99** |
| `median_car_pct` | % | median, untreated |
| `t_crosssec` | t | plain cross-sectional t — reported for comparability, not relied on |
| `t_bmp` | t | BMP (1991); survives event-induced variance |
| `z_corrado` | Z | Corrado (1989) rank test; survives magnitude entirely |
| `significant` | 0/1 | 1 only where **both** BMP and Corrado exceed \|1.96\| |

The placebo row is the load-bearing check. `R_NONRELIANCE` is null there; `R_LISTING` and `R_LATE`
are not, so those events are partly anticipated and cannot be read as clean surprises.

## `attributable_loss.csv` — the dollar figure
One row per event type, plus a `UNION` row (first revelation of any type per issuer).

| column | unit | meaning |
|---|---|---|
| `n_events` | count | one event per issuer per type; float capped at $2B |
| `float_usd_bn` | $bn | public float, **not** market cap — insider shares are not public losses |
| `attributable_usd_mn` | $mn | Σ (CAR × float), signed; positives included, not dropped |
| `ci_lo_usd_mn`, `ci_hi_usd_mn` | $mn | 95% bootstrap CI |

**Quote the `UNION` row**, not a sum of the type rows: an issuer filing both a non-reliance and a
listing notice appears in two type rows. Coverage is 52% — issuers already delisted cannot be
priced, and those are the worst outcomes, so the figure **understates**.

---

# Multivariate model output

Logistic models of each outcome on the individual signal surfaces plus controls. **Standard errors
are clustered by issuer** — 14,282 issuer-vintages but only 6,192 distinct issuers, most appearing
two or three times. `outcome` takes `y_nonrel` (8-K Item 4.02 within 20 months), `y_any` (any
revelation), or `y_severe` (50% loss or delisting).

Coefficients are population-level parameters: they describe the filer population, not any issuer in
it.

## `model_coefficients.csv`
One row per (outcome, term).

| column | unit | meaning |
|---|---|---|
| `term` | text | regressor; signal surfaces plus `log_assets`, `log_float`, `free_float`, `shell`, `prior_any` |
| `coef` | log-odds | raw logistic coefficient |
| `odds_ratio` | ratio | exp(coef) — the reported effect size |
| `se`, `z`, `p` | — | cluster-robust standard error, z-statistic, two-sided p-value |
| `or_lo`, `or_hi` | ratio | 95% CI on the odds ratio |

Rows with empty numeric fields are **non-estimable**: the signal has a zero-outcome cell, so its MLE
coefficient diverges. They are listed rather than dropped, because "fires on 4 issuers and none had
the outcome" is a finding.

## `model_marginal_effects.csv`
Average marginal effects, in **percentage points**. Odds ratios are the natural scale for a logit and
the wrong scale for a policy reader: "+2.6pp against a 4.13% base rate" is actionable in a way "odds
ratio 2.0" is not.

## `model_fit.csv`
One row per (outcome, specification) for the nested ladder — `size alone`, `+ structure controls`,
`+ signals (full)`.

| column | meaning |
|---|---|
| `auc_in_sample` | AUC of that specification, in sample |
| `joint_lr_chi2`, `joint_p` | likelihood-ratio test of the whole signal block against controls only |
| `auc_out_of_sample` | fit on 2022+2023, scored on 2024 — **the comparison that counts** |
| `auc_count_score_oos` | the incumbent count score on the same held-out data |
| `brier_oos` | Brier score; lower is better calibrated |

In-sample AUC always flatters a regression relative to a count score. Read the out-of-sample pair.
These AUCs include size as a predictor and are **not** comparable to the size-stratified figures in
`revelation_discrimination.csv`, which strip it out.

## `model_calibration.csv`
Predicted vs actual event rate by predicted-risk decile, out of sample. **The model over-warns**:
for non-reliance the top decile predicts 19.4% and delivers 10.4%. Discrimination and calibration are
different properties — a model can rank well and still be wrong in level. Treat the output as an
ordering, not a probability.
