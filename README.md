# AI Disclosure Measurement

[![ci](https://github.com/matthewgg22/ai-disclosure-measurement/actions/workflows/ci.yml/badge.svg)](https://github.com/matthewgg22/ai-disclosure-measurement/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A reproducible pipeline for measuring the **information content of the "AI" label in U.S. securities filings**: how far the label has decoupled from substance, and what that decoupling looks like in the small-cap tail where it is most exposed.

Built over the EDGAR corpus and the Russell 3000. Every script produces a **cohort-level or market-level measurement**; the finding each one supports is listed below. This repository is the public *measurement layer* of a larger research project; lead-generation and enforcement-referral tooling is deliberately excluded (see [Scope](#scope-what-is-not-here)).

---

## The result, in three figures

Across 25 years of 10-K filings, the "AI" label **went everywhere, stayed hollow, and left its home sector.** Every figure below is aggregate (no individual issuer), regenerated from committed data by [`pipeline/make_figures.py`](pipeline/make_figures.py). Full figure→script→number map in [`docs/RESULTS.md`](docs/RESULTS.md).

**1. The label went everywhere.** "Artificial intelligence" appeared in **0.8%** of 10-K filers in 2001 and **50.7%** in 2025.

![AI label adoption in 10-K filings, 2001–2025](docs/figures/f1_adoption.png)

**2. ...but the substance did not follow.** *Marketing* vocabulary ("AI-powered", "AI-driven") reached **14.6%** of filers while the more costly *build* vocabulary (LLM, training compute, fine-tuning) stayed pinned at **1.8%**. That gap is the washing signature.

![Marketing vs. substance vocabulary in 10-K filings](docs/figures/f2_marketing_vs_substance.png)

**3. ...and it spread beyond software.** Software's (SIC-73) share of all AI mentions peaked near **57%** in 2018 and fell to **27%** by 2025 as the label appeared across more sectors.

![Software's share of AI mentions over time](docs/figures/f3_sector_diffusion.png)

These three are the market-wide backbone; the disciplining nulls and the small-cap tail are below.

### The disciplining null: the label's *information content* decayed

The claim is not "AI is hype." It is that the label stopped carrying information about real capability. Measured with **audited R&D** (hard to fake): as the AI label spread from 37 to ~2,400 10-K filers, the share of AI-labeled filers reporting *any* R&D fell to **42%** (2024), and their R&D-intensity edge over the market fell toward zero (+0.036 to +0.009 across 2018–2024). The 2015 point is a small sample (37 firms) and is flagged as such, so the reading to trust is the post-2018 decline, not the noisy early year. One caveat: part of that decline can come from the pool filling with larger, less R&D-intensive firms, a composition effect a size control would separate (see limitations in the working paper).

![The label's link to real capability faded](docs/figures/f4_informativeness.png)

This is one of several *disciplining nulls* the project keeps prominently (the AI return premium is a large-cap phenomenon; enforcement does not re-separate the cross-section; the "hollow = washer" gap is mostly a size effect). See the [Script → claim map](#script--claim-map) and [`docs/RESULTS.md`](docs/RESULTS.md).

---

## What it measures (headline results)

All figures are reproducible from the named scripts. The unit of analysis is the filing corpus and a screened cohort of nano/micro-cap "theme-pivot" shells, **not** any individual issuer.

**The label decoupled from substance (market-wide):**
- "Artificial intelligence" in 10-Ks rose from **0.8% (2001) to ~50–77%** of filers (`ai_prevalence.py`).
- Marketing vocabulary ("AI-powered") reached **~14.5%** of filings while costly *build* vocabulary (LLM, training compute) stayed pinned at **1–2%** (`ai_lexicon.py`).
- The label diffused *out* of software: SIC-73's share of AI mentions fell **57% → 27%** (`ai_sector.py`).
- Year-over-year, the label's incremental information about firm capability **declines** (`informativeness.py`).

**The extraction cohort (the tail where the decoupling is naked):**
- A theme-pivot screen surfaces 456 candidates → a market-cap/prior-collapse filter yields **244 clean nano/micro shells** (`nano_pivot_screen.py`, `nano_clean.py`).
- **~82%** are repainted dead operating companies; **~21%** are de-SPAC lineage (`nonspac_shells.py`, `spac_census.py`, `spac_vintage.py`).
- **41%** of clawback-tier pivots carry the full pre-funded-warrant + ownership-blocker + ≥5× dilution triad that routes extraction around §16 insider disclosure (`dilution_evasion.py`).
- A concentrated financier layer: **7 funds touch 265 issuers** (`name_funds.py`, `financier_book.py`).
- **71%** of the cohort is audited by small non-Big-4 firms; the sharpest recur as terminal "backstop" auditors after serial churn (`gatekeeper_screen.py`, `auditor_opinions.py`, `auditor_4_01_direction.py`).
- Capital: **~$3.04B raised / ~$213M placement fees / median −95% post-raise drawdown / median ~567× dilution**; **~$24.3B** peak market value destroyed (envelope) (`capture_decomp.py`, `value_destroyed.py`).

**Disciplining nulls (kept prominently):**
- The "hollow = washer" resource gap is **mostly a size effect**: a size-controlled classifier gains only ~+0.01 AUC (`gap_classifier.py`).
- The sustained AI return premium is a **large/mega-cap** phenomenon (~+7.5% sector-neutral); small-cap AI-mentioners earn **negative** annual returns (`sector_premium.py`, `size_premium.py`, `ff_alpha.py`).
- Provable nano shells are **absent from AI ETFs**: the tail is not the ETF channel's harm (`etf_intersect.py`).
- Securities-enforcement events **do not re-separate** the AI cross-section (a well-identified null with clean placebos) (`event_study/`).

**Cross-border structure (measured, not asserted):**
- A foreign-control census finds **~26%** of the cohort is genuinely foreign-controlled, but with a **disciplined severity null**: foreign-controlled shells show the *same* drawdown as domestic ones; the difference is *recoverability*, not harm magnitude (`foreign_control_census.py`, `foreign_control_refine.py`).
- Narrative-costume rotation is measured two ways: **23%** wear ≥2 hot themes (crypto/quantum/AI/nuclear) simultaneously, and serial name-rotation is real but rare (~5%), the AI-era replication of the dot-com name-change literature (`costume_rotation.py`).
- Cross-border *counterparty* structure (US-raised cash routed offshore for low-substance "assets") is screened at cohort level (`exfil_conduit.py`).

---

## Script → claim map

| Group | Scripts | Supports |
|---|---|---|
| Label prevalence & informativeness | `edgar_fts.py`, `ai_prevalence.py`, `ai_lexicon.py`, `ai_sector.py`, `informativeness.py`, `ai_sophistication.py`, `cooccurrence.py` | the decoupling of the label from substance, market-wide |
| Cohort construction | `nano_pivot_screen.py`, `nano_clean.py`, `nonspac_shells.py`, `spac_census.py`, `spac_vintage.py` | the 244-shell tail; shell sources; self-replenishing supply |
| Extraction instrument | `dilution_evasion.py` | the pre-funded-warrant/blocker §16-evasion triad |
| Financier concentration | `name_funds.py`, `financier_book.py` | 7 funds → 265 issuers |
| Gatekeeper concentration | `gatekeeper_screen.py`, `auditor_opinions.py`, `auditor_4_01_direction.py` | small-auditor skew; going-concern/material-weakness rates; churn direction |
| Capital destruction | `capture_decomp.py`, `value_destroyed.py` | $3.04B raised / −95% / $24.3B destroyed |
| Capability-gap classifier | `gap_classifier.py`, `composite_prep.py` | the size-collinearity null (public data resolves only the shell tail) |
| AI return premium | `sector_premium.py`, `size_premium.py`, `ff_alpha.py` | premium is large-cap; small-cap AI is negative |
| ETF channel | `etf_intersect.py` | nano shells absent from AI ETFs |
| Enforcement event study | `event_study.py`, `event_study/` | enforcement does not re-separate the cross-section (null) |
| Cross-border structure | `foreign_control_census.py`, `foreign_control_refine.py`, `costume_rotation.py`, `exfil_conduit.py` | foreign-control census + severity null; costume rotation; offshore counterparty structure |

---

## Reproducibility

**Fastest path (60 seconds, no network):** the three headline figures regenerate from the committed aggregate CSVs in `data/aggregates/`:

```
pip install matplotlib
python pipeline/make_figures.py      # reads data/aggregates/, writes docs/figures/
```

**Full pipeline:** scripts are standalone Python 3 and pull directly from public SEC/market sources; each caches to a local `data/` directory (regenerated on first run, not checked in). Rough order:

```
python pipeline/edgar_fts.py         # full-text-search infrastructure + phrase/year counts
python pipeline/ai_prevalence.py     # prevalence time series
python pipeline/nano_pivot_screen.py # theme-pivot candidate set
python pipeline/nano_clean.py        # -> the 244-shell cohort
python pipeline/foreign_control_census.py && python pipeline/foreign_control_refine.py
python pipeline/costume_rotation.py
# ...see the script→claim map above
```

**Before running:** each script's EDGAR `User-Agent` declares a real contact (the SEC requires one). If you fork this repo, replace the `matthewgreergentis@gmail.com` contact string with your own before running. Requests are rate-limited to stay within SEC fair-access limits.

Dependencies: standard library plus what's in `requirements.txt`. Market-data steps use free sources (yfinance/stooq) for prototyping; the event study reads Ken French factors (public).

For construction details (data sources, population definitions, the estimating equations, and the disciplining nulls), see [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

---

## Scope: what is *not* here

This is the **measurement layer**. Deliberately excluded, because it belongs to an active securities-fraud disclosure submitted to the SEC and to ongoing enforcement-facing work:

- individual-issuer ranking / lead-generation,
- the §16(b) short-swing transaction matcher,
- entity-network mapping,
- case-specific dossiers.

Nothing here names or targets an individual company as a fraud suspect. The cohort is a screened population of public filers; the findings are statistical.

## Note on AI-assisted development

This pipeline was built with AI-assisted analysis and coding. The research design, the measurement choices, the interpretation, and the verification are the author's; AI was used as a coding and large-scale-review tool. All results are reproducible from the code and public data.

## Working paper

A short, aggregate-only working paper, *The Decoupling of the "AI" Label from Substance in U.S. Securities Filings, 2001–2025*, is drafted from these results in [`paper/`](paper/). It reuses figures F1–F4 and every number is reproducible from this repo. Full draft: [`paper/PAPER.md`](paper/PAPER.md) (outline: [`paper/OUTLINE.md`](paper/OUTLINE.md); abstract: [`paper/abstract.md`](paper/abstract.md)).

## How to cite

If you use this work, please cite it. GitHub renders a "Cite this repository" button from [`CITATION.cff`](CITATION.cff). A permanent DOI badge will appear here once the first release is archived on Zenodo.

```
Greer-Gentis, M. (2026). AI Disclosure Measurement. https://github.com/matthewgg22/ai-disclosure-measurement
```

## Author & license

Matthew Greer-Gentis · Harvard Kennedy School (MPP) · research advised by Hal Scott and Daniel Tarullo.
Released under the MIT License (see `LICENSE`).
