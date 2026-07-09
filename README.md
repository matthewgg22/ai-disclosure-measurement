# AI Disclosure Measurement

A reproducible pipeline for measuring the **information content of the "AI" label in U.S. securities filings** — how far the label has decoupled from substance, and what that decoupling looks like in the small-cap tail where it is most naked.

Built over the EDGAR corpus and the Russell 3000. Every script produces a **cohort-level or market-level measurement**; the finding each one supports is listed below. This repository is the public *measurement layer* of a larger research project; lead-generation and enforcement-referral tooling is deliberately excluded (see [Scope](#scope--what-is-not-here)).

---

## What it measures (headline results)

All figures are reproducible from the named scripts. The unit of analysis is the filing corpus and a screened cohort of nano/micro-cap "theme-pivot" shells — **not** any individual issuer.

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
- The "hollow = washer" resource gap is **mostly a size effect** — a size-controlled classifier gains only ~+0.01 AUC (`gap_classifier.py`).
- The sustained AI return premium is a **large/mega-cap** phenomenon (~+7.5% sector-neutral); small-cap AI-mentioners earn **negative** annual returns (`sector_premium.py`, `size_premium.py`, `ff_alpha.py`).
- Provable nano shells are **absent from AI ETFs** — the tail is not the ETF channel's harm (`etf_intersect.py`).
- Securities-enforcement events **do not re-separate** the AI cross-section (a well-identified null with clean placebos) (`event_study/`).

**Cross-border structure (measured, not asserted):**
- A foreign-control census finds **~26%** of the cohort is genuinely foreign-controlled, but with a **disciplined severity null** — foreign-controlled shells show the *same* drawdown as domestic ones; the difference is *recoverability*, not harm magnitude (`foreign_control_census.py`, `foreign_control_refine.py`).
- Narrative-costume rotation is measured two ways: **23%** wear ≥2 hot themes (crypto/quantum/AI/nuclear) simultaneously, and serial name-rotation is real but rare (~5%) — the AI-era replication of the dot-com name-change literature (`costume_rotation.py`).
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

Scripts are standalone Python 3 and pull directly from public SEC/market sources; each caches to a local `data/` directory (regenerated on first run, not checked in). Rough order:

```
python pipeline/edgar_fts.py         # full-text-search infrastructure + phrase/year counts
python pipeline/ai_prevalence.py     # prevalence time series
python pipeline/nano_pivot_screen.py # theme-pivot candidate set
python pipeline/nano_clean.py        # -> the 244-shell cohort
python pipeline/foreign_control_census.py && python pipeline/foreign_control_refine.py
python pipeline/costume_rotation.py
# ...see the script→claim map above
```

**Before running:** set a real contact string in each script's EDGAR `User-Agent` (the SEC requires one). A placeholder `YOUR_EMAIL@example.com` marks where. Requests are rate-limited to stay within SEC fair-access limits.

Dependencies: standard library plus what's in `requirements.txt`. Market-data steps use free sources (yfinance/stooq) for prototyping; the event study reads Ken French factors (public).

---

## Scope — what is *not* here

This is the **measurement layer**. Deliberately excluded, because it belongs to an active securities-fraud disclosure submitted to the SEC and to ongoing enforcement-facing work:

- individual-issuer ranking / lead-generation,
- the §16(b) short-swing transaction matcher,
- entity-network mapping,
- case-specific dossiers.

Nothing here names or targets an individual company as a fraud suspect. The cohort is a screened population of public filers; the findings are statistical.

## Note on AI-assisted development

This pipeline was built with AI-assisted analysis and coding. The research design, the measurement choices, the interpretation, and the verification are the author's; AI was used as a coding and large-scale-review tool. All results are reproducible from the code and public data.

## Author & license

Matthew Greer-Gentis · Harvard Kennedy School (MPP) · research advised by Hal Scott and Daniel Tarullo.
Released under the MIT License (see `LICENSE`).
