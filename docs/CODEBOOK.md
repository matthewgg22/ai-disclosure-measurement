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
| `auc_size_only` | AUC | AUC of firm size alone (a control; ~0.11 means size is *anti*-predictive) |
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
