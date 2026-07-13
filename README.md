# AI Disclosure Measurement

[![ci](https://github.com/matthewgg22/ai-disclosure-measurement/actions/workflows/ci.yml/badge.svg)](https://github.com/matthewgg22/ai-disclosure-measurement/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A reproducible screen for the **capital-extraction structures that recur in nano, micro, and small-cap securities fraud**, built from public SEC filings, with out-of-sample evidence that it works: **the engine's gatekeeper signals, measured through fiscal 2021, predict SEC regulatory failure in 2022+ with a size-adjusted AUC of 0.73** (F7 in [`docs/RESULTS.md`](docs/RESULTS.md)). The "AI" label is one narrative *wrapper* the screen sits under: this repo measures how far that label has decoupled from substance (F1 to F5), and, at the level that matters more, tracks the extraction *mechanism* the wrapper hides, the pre-funded-warrant and ownership-blocker structure that routes dilution around Section 16 (F6, [`docs/SCREEN.md`](docs/SCREEN.md)). Every surface the engine measures traces to an element of a securities-fraud theory the government or a plaintiff must actually prove; the element-by-element map is [`docs/DOCTRINE.md`](docs/DOCTRINE.md).

This is also, at bottom, **measurement of a societal impact of AI**: it quantifies how a claim *about AI capability* propagates through a disclosure system and decouples from substance, and it tracks the market-integrity harm that follows when it does. The methods are securities-specific, but the object — measuring where AI language outruns AI reality, at population scale, from primary sources — is AI-impacts research.

Built over the EDGAR corpus and the Russell 3000. Everything here is **aggregate and reproducible**; no individual issuer is named or ranked. That boundary is statistical, not just ethical: even the best public-data fraud models produce **168 to 324 false positives per true positive** at issuer level (Beneish and Vorst, The Accounting Review 2022), so market-wide prevalence is the defensible output and issuer-level inference is left to downstream case work. This repository is the public *measurement layer* of a larger research project; issuer-level scoring, the §16(b) matcher, lead-generation, network mapping, and case files are deliberately excluded and kept private (see [Scope](#scope-what-is-not-here)).

> **Reviewing this repo in ten minutes?** The validated result is [F7 below](#out-of-sample-validation-f7) (details: [`docs/RESULTS.md`](docs/RESULTS.md)). The honesty checks are the disciplining nulls (F4, F5, and the AAER null that *failed* first). The legal grounding is [`docs/DOCTRINE.md`](docs/DOCTRINE.md). To run something: `pip install matplotlib && python pipeline/make_figures.py` regenerates every figure from committed aggregates in about a minute, no network; `pytest` runs 55 offline tests (the same suite as [CI](https://github.com/matthewgg22/ai-disclosure-measurement/actions)).

---

## The result, in figures

Across 25 years of 10-K filings, the "AI" label **went everywhere, stayed hollow, and left its home sector** — and the screen built underneath it predicts real regulatory failure out of sample (F7). Every figure below is aggregate (no individual issuer), regenerated from committed data by [`pipeline/make_figures.py`](pipeline/make_figures.py). Full figure→script→number map in [`docs/RESULTS.md`](docs/RESULTS.md).

**1. The label went everywhere.** "Artificial intelligence" appeared in **0.8%** of 10-K filers in 2001 and **50.7%** in 2025.

![AI label adoption in 10-K filings, 2001–2025](docs/figures/f1_adoption.png)

**2. ...but the substance did not follow.** *Marketing* vocabulary ("AI-powered", "AI-driven") reached **14.6%** of filers while the more costly *build* vocabulary (LLM, training compute, fine-tuning) stayed pinned at **1.8%**. That gap is the washing signature.

![Marketing vs. substance vocabulary in 10-K filings](docs/figures/f2_marketing_vs_substance.png)

**3. ...and it spread beyond software.** Software's (SIC-73) share of all AI mentions peaked near **57%** in 2018 and fell to **27%** by 2025 as the label appeared across more sectors.

![Software's share of AI mentions over time](docs/figures/f3_sector_diffusion.png)

These three are the market-wide backbone; the disciplining nulls and the small-cap tail are below.

### The disciplining null: the label's *information content* decayed

The claim is not "AI is hype." It is that the label stopped carrying information about real capability. Measured with **audited R&D** (hard to fake): as the AI label spread from 37 to ~2,400 10-K filers, the share of AI-labeled filers reporting *any* R&D fell to **42%** (2024), and their R&D-intensity edge over the market fell toward zero. With **95% bootstrap confidence intervals** (error bars in the figure), the 2018 premium is **+0.036 [0.014, 0.066]**, which excludes zero, and by 2024 it is **+0.009 [−0.014, 0.030]**, which includes zero: the premium was real in 2018 and is gone by 2024. The 2015 point is a small sample (37 firms, CI running to +2.3) and is flagged. **Size control:** comparing AI firms only to non-AI firms in the same total-assets tercile, the premium is *higher* (0.067 in 2018, 0.031 in 2024) and still declines, so the fall is not just the pool filling with larger, low-R&D firms; the size-adjusted estimates are noisier (wider CIs). Details in [`docs/RESULTS.md`](docs/RESULTS.md) and the working paper.

![The label's link to real capability faded](docs/figures/f4_informativeness.png)

This is one of several *disciplining nulls* the project keeps prominently (the AI return premium is a large-cap phenomenon; enforcement does not re-separate the cross-section; the "hollow = washer" gap is mostly a size effect). See the [Script → claim map](#script--claim-map) and [`docs/RESULTS.md`](docs/RESULTS.md).

### Is this just buzzword behavior? No.

Applying the **same** marketing template ("<term>-powered" / "<term>-driven") to AI and to control buzzwords, in 2025 the AI form reached **12.9%** of 10-K filers versus **0.18%** (blockchain), **0.09%** (cloud), and **0.03%** (quantum). AI's marketing form is about **70x** the nearest control, while bare mentions differ only ~3x. Only AI produced a large marketing vocabulary (`placebo_terms.py`).

![Only AI got the marketing treatment](docs/figures/f5_placebo.png)

### The mechanism: detecting the extraction structure

The AI label is the wrapper. The value is pulled out through a specific, measurable structure: **pre-funded warrants** (a nominal-price dilution instrument) paired with an **ownership blocker** ("beneficial ownership limitation" language) that keeps a holder below the Section 16 / 5% reporting threshold, so large economic positions avoid insider disclosure. Using the same full-text-search method, the pre-funded-warrant instrument went from near zero before 2016 to **8.6%** of 10-K filers by 2025, and the **paired** structure (both in one filing, routing dilution around Section 16) went from ~0 to **2.0%**, almost all of it since 2020 (the `screen/` engine, `python -m screen.run`).

![The extraction instrument spread through filings](docs/figures/f6_extraction.png)

These phrases have legitimate uses, so their prevalence is a **screening input, not a finding of fraud**. The detection method combines this with gatekeeper distress, financier concentration, shell lineage, and cross-border structure; the full feature set, scoring, and out-of-sample validation design are in [`docs/SCREEN.md`](docs/SCREEN.md). Issuer-level scoring stays private, by design. The screen builds on the forensic-detection canon — Beneish's M-Score, Sloan accruals, Piotroski's F-Score, the Loughran–McDonald 10-K dictionary method, and the "quadrophobia" earnings-digit discontinuity — and reuses its validated markers rather than inventing metrics; the lineage and the specific contribution are set out in [`docs/SCREEN.md`](docs/SCREEN.md#related-work-and-contribution).

### Out-of-sample validation (F7)

Does the screen detect anything real? The claim is made falsifiable and tested forward: a transparent 0–3 auditor-distress score (non-Big-4, Big-4→non-Big-4 downgrade, churn — from PCAOB Form AP), measured **strictly through fiscal 2021**, predicts which issuers are hit by an SEC trading suspension or Section 12(j) proceeding **in 2022 or later**. Nothing from the outcome window enters the score.

![Out-of-sample validation: gatekeeper distress measured through FY2021 predicts 2022+ regulatory failure](docs/figures/f7_validation.png)

**Size-adjusted AUC 0.732, 95% bootstrap CI (0.578, 0.773)**, n = 8,393 issuers, 234 failures; top score deciles fail at ~6–7% vs 0.0% in the bottom two, and size alone is *anti*-predictive (AUC 0.11), so this is not "small firms fail more" restated. What makes the positive result credible is that the same harness **returned nulls when the labels were wrong**: against large-cap AAER enforcement it read 0.564 (chance), and against raw Form 25 delistings (which mix mergers into "failure") it read 0.492 — both reported, not buried. Honest boundary: one dimension is validated here, the CI is wide though clean of 0.5, and the score is deliberately coarse; full caveats in [`docs/RESULTS.md`](docs/RESULTS.md) and [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md#7-reproducibility-and-caveats).

---

## What it measures (headline results)

All figures are reproducible from the named scripts. The unit of analysis is the filing corpus and a screened cohort of nano/micro-cap "theme-pivot" shells, **not** any individual issuer.

**The label decoupled from substance (market-wide):**
- "Artificial intelligence" in 10-Ks rose from **0.8% (2001) to ~50–77%** of filers (`ai_prevalence.py`).
- Marketing vocabulary ("AI-powered") reached **~14.5%** of filings while costly *build* vocabulary (LLM, training compute) stayed pinned at **1–2%** (`ai_lexicon.py`).
- The label diffused *out* of software: SIC-73's share of AI mentions fell **57% → 27%** (`ai_sector.py`).
- Year-over-year, the label's incremental information about firm capability **declines** (`informativeness.py`).

**The extraction cohort (the tail where the decoupling is naked).** These cohort-level figures are reported from the **private issuer-level pipeline** (excluded here per [Scope](#scope-what-is-not-here)); they are aggregate and name no issuer, but they are not reproducible from this public repo, which ships the market-wide aggregates and the screen engine:
- A theme-pivot screen surfaces 456 candidates → a market-cap/prior-collapse filter yields **244 clean nano/micro shells**.
- **~82%** are repainted dead operating companies; **~21%** are de-SPAC lineage.
- **41%** of clawback-tier pivots carry the full pre-funded-warrant + ownership-blocker + ≥5× dilution triad that routes extraction around §16 insider disclosure. *(The market-wide version of this triad IS reproducible here: the engine's `sec16_evasion` surface, F6.)*
- A concentrated financier layer: **7 funds touch 265 issuers**.
- **71%** of the cohort is audited by small non-Big-4 firms; the sharpest recur as terminal "backstop" auditors after serial churn. *(Market-wide auditor structure is reproducible here: the engine's `auditor_market` / `auditor_churn` surfaces.)*
- Capital: **~$3.04B raised / ~$213M placement fees / median −95% post-raise drawdown / median ~567× dilution**; **~$24.3B** peak market value destroyed (envelope).

**Disciplining nulls (kept prominently):**
- The "hollow = washer" resource gap is **mostly a size effect**: a size-controlled classifier gains only ~+0.01 AUC.
- The sustained AI return premium is a **large/mega-cap** phenomenon (~+7.5% sector-neutral); small-cap AI-mentioners earn **negative** annual returns (`sector_premium.py`, `size_premium.py`, `ff_alpha.py`).
- Provable nano shells are **absent from AI ETFs**: the tail is not the ETF channel's harm.
- Securities-enforcement events **do not re-separate** the AI cross-section (a well-identified null with clean placebos) (`event_study/`).

**Cross-border structure (measured, not asserted; cohort-level figures from the private pipeline):**
- A foreign-control census finds **~26%** of the cohort is genuinely foreign-controlled, but with a **disciplined severity null**: foreign-controlled shells show the *same* drawdown as domestic ones; the difference is *recoverability*, not harm magnitude.
- Narrative-costume rotation is measured two ways: **23%** wear ≥2 hot themes (crypto/quantum/AI/nuclear) simultaneously, and serial name-rotation is real but rare (~5%), the AI-era replication of the dot-com name-change literature.
- Cross-border *counterparty* structure (US-raised cash routed offshore for low-substance "assets") is screened at cohort level.

---

## Script → claim map

Public scripts ship in this repo; issuer-level cohort/network analysis is in the **private** pipeline (excluded per [Scope](#scope-what-is-not-here)) and is marked *private* below.

| Group | Scripts | Supports |
|---|---|---|
| Label prevalence & informativeness | `ai_prevalence.py`, `ai_lexicon.py`, `ai_sector.py`, `informativeness.py`, `ai_sophistication.py` | the decoupling of the label from substance, market-wide |
| Screen engine (market-wide surfaces) | `screen/` (see [`docs/SCREEN.md`](docs/SCREEN.md)) | §16-evasion, auditor market/churn, dilution, accrual, EPS-rounding, crypto-treasury, CFIUS surfaces + validation |
| Cohort construction | *private* | the 244-shell tail; shell sources; self-replenishing supply |
| Extraction instrument | *private* (market-wide version: `screen/` `sec16_evasion`) | the pre-funded-warrant/blocker §16-evasion triad |
| Financier concentration | *private* | 7 funds → 265 issuers |
| Gatekeeper concentration | *private* (market-wide version: `screen/` `auditor_market`/`auditor_churn`) | small-auditor skew; going-concern/material-weakness rates; churn direction |
| Capital destruction | *private* | $3.04B raised / −95% / $24.3B destroyed |
| Capability-gap classifier | *private* | the size-collinearity null (public data resolves only the shell tail) |
| AI return premium | `sector_premium.py`, `size_premium.py`, `ff_alpha.py` | premium is large-cap; small-cap AI is negative |
| ETF channel | *private* | nano shells absent from AI ETFs |
| Enforcement event study | `event_study.py`, `event_study/` | enforcement does not re-separate the cross-section (null) |
| Cross-border structure | *private* | foreign-control census + severity null; costume rotation; offshore counterparty structure |

---

## Reproducibility

**Fastest path (about a minute, no network):** all seven figures regenerate from the committed aggregate CSVs in `data/aggregates/`:

```
pip install matplotlib
python pipeline/make_figures.py      # reads data/aggregates/, writes docs/figures/
```

**Full public pipeline:** the scripts here are standalone Python 3 and pull directly from public SEC/market sources; each caches to a local `data/` directory (regenerated on first run, not checked in). They produce the market-wide aggregates and figures; the issuer-level cohort/network pipeline is private (see [Scope](#scope-what-is-not-here)). Rough order:

```
python pipeline/ai_prevalence.py     # AI-label prevalence time series (F1)
python pipeline/ai_lexicon.py        # marketing vs build vocabulary (F2)
python pipeline/ai_sector.py         # sector diffusion (F3)
python pipeline/informativeness.py   # label information content (F4)
python pipeline/placebo_terms.py     # placebo buzzwords (F5)
python -m screen.run you@example.com # the regulatory-surface screen engine (F6/F7 inputs); pass your SEC contact
python pipeline/make_figures.py      # renders docs/figures/ from data/aggregates/
```

**Before running:** each script's EDGAR `User-Agent` declares a real contact (the SEC requires one). If you fork this repo, replace the `matthewgreergentis@gmail.com` contact string with your own before running. Requests are rate-limited to stay within SEC fair-access limits.

Dependencies: standard library plus what's in `requirements.txt`. The one script that pulls market prices (`ff_alpha.py`) needs a free Tiingo token (`TIINGO_TOKEN` env var); it populates the local price caches the premium and event-study scripts read. Factor data comes from Ken French's public library.

**Computational requirements.** Python 3.9+; no GPU, no cluster, no paid data. The figure-regeneration path needs only `matplotlib` and runs in about a minute on a laptop; `pytest` (55 tests) runs offline in ~5 seconds. Full pipeline runs from public SEC/PCAOB/XBRL endpoints over an ordinary connection and caches locally. Every committed aggregate CSV is documented in [`docs/CODEBOOK.md`](docs/CODEBOOK.md).

For construction details (data sources, population definitions, the estimating equations, and the disciplining nulls), see [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md). For how the findings map to disclosure-policy levers, see [`docs/POLICY.md`](docs/POLICY.md).

---

## Scope: what is *not* here

This is the **measurement layer**. Deliberately excluded, because it belongs to an active securities-fraud disclosure submitted to the SEC and to ongoing enforcement-facing work:

- individual-issuer ranking / lead-generation,
- the §16(b) short-swing transaction matcher,
- entity-network mapping,
- case-specific dossiers.

Nothing here names or targets an individual company as a fraud suspect. The cohort is a screened population of public filers; the findings are statistical.

This split is a deliberate **responsible-disclosure** design, not just legal caution: the same public data that yields useful market-wide measurement also yields an issuer-targeting capability whose false-positive rate (168–324 per true positive) makes public per-issuer output net-harmful. So the repository publishes the measurement and the reproducible method, and withholds the targeting layer — a capability-vs-measurement line drawn on evidence about error rates, enforced in code by a publication gate rather than by promise. It is the same shape of judgment that governs disclosure decisions elsewhere: release what informs, hold back what mostly manufactures harm.

## Note on AI-assisted development

This pipeline was built working with Claude (Anthropic's Claude Code) in an agentic workflow. The division of labor, concretely: the research design, the measurement choices, the legal framing, the interpretation, and the final verification are the author's; Claude implemented the pipeline, ran large-scale corpus review, and ran **adversarial review passes against its own code** — one of which caught, before it ever shipped, a filter bug that would have silently dropped the entire operating-issuer population from the PCAOB signal (the positive-selection fix is in `screen/pcaob.py`; a later pass produced the "Harden the screen engine after adversarial review" commit). Guardrails are structural rather than trust-based: results regenerate from committed aggregates and public data, the validation harness is unit-tested on synthetic data with known answers, a publication gate (`scripts/check_public_safe.py`) blocks issuer-identifying output from ever shipping, and CI runs the full offline suite on every push. The disciplining nulls reported throughout (the AAER null, the delisting null, F4/F5) came out of the same workflow: the harness was built to be able to say *no*, and sometimes it did.

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
