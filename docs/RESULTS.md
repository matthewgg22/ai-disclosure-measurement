# Results — figure → script → number

The three README figures are the market-wide backbone of the project: the "AI"
label **went everywhere, stayed hollow, and left its home sector.** Every number
here is aggregate (one row per year, or per year × sector) — no individual
issuer. All are regenerated from committed data under `data/aggregates/` by
[`pipeline/make_figures.py`](../pipeline/make_figures.py) (no network, no SEC
calls). The data itself is produced by the pure-standard-library scripts named
below, straight from public EDGAR endpoints.

For construction detail (denominators, phrase selection, identification), see
[`METHODOLOGY.md`](METHODOLOGY.md).

---

## F1 — The label went everywhere

![F1](figures/f1_adoption.png)

- **Number:** "artificial intelligence" appeared in **0.79%** of 10-K filers in
  2001 and **50.69%** in 2025. "generative AI" went from **0%** (through 2022) to
  **13.37%** in 2025 — the vocabulary itself churns.
- **Data script:** [`pipeline/ai_prevalence.py`](../pipeline/ai_prevalence.py) →
  `data/ai_prevalence.csv` (committed at `data/aggregates/ai_prevalence.csv`).
- **Numerator:** 10-Ks matching a quoted AI phrase per year (EDGAR full-text
  search). **Denominator:** distinct 10-K filers per year from the EDGAR master
  index — the complete filing-level population, not the FTS total (which caps at
  10,000). This denominator fix is the key correctness step.

## F2 — ...but the substance did not follow

![F2](figures/f2_marketing_vs_substance.png)

- **Number:** in 2025, cheap *marketing* vocabulary ("AI-powered", "AI-driven",
  "AI-native"...) reached **14.55%** of filers while costly *build* vocabulary
  (large language model, training compute, fine-tuning, RAG, mixture of
  experts...) stayed pinned at **1.77%**. In 2001 both were near zero (0.05% /
  0.32%). The widening marketing-minus-substance gap is the washing fingerprint
  at the population level.
- **Data script:** [`pipeline/ai_lexicon.py`](../pipeline/ai_lexicon.py) →
  `data/ai_buckets_by_year.csv` (committed at
  `data/aggregates/ai_buckets_by_year.csv`).
- **Note:** bucket values are the summed share of their member phrases (an upper
  bound, since a filing can use several), so the *levels* are generous but the
  *divergence* between marketing and substance is the robust object.
- **Caveat (ecological inference):** a population ratio cannot classify an
  individual filing. The per-filing version of this test lives in
  [`pipeline/cooccurrence.py`](../pipeline/cooccurrence.py); see METHODOLOGY §2.

## F3 — ...and it spread beyond software

![F3](figures/f3_sector_diffusion.png)

- **Number:** software's (SIC-73) share of all AI mentions **peaked near 57% in
  2018** and fell to **27% by 2025**. The series is genuinely noisy in the early
  2000s (few AI-mentioning filers → small denominators), so the honest reading is
  *peak-to-present decline*, not a smooth 25-year slide.
- **Data script:** [`pipeline/ai_sector.py`](../pipeline/ai_sector.py) →
  `data/ai_sector_by_year.csv` (committed at
  `data/aggregates/ai_sector_by_year.csv`), an EDGAR FTS `sic_filter`
  aggregation rolled up to 2-digit SIC.

## F4 — The label's link to real capability faded (a disciplining null)

![F4](figures/f4_informativeness.png)

- **Number:** measuring capability with **audited R&D** (hard to fake), as the AI
  label spread from **37** 10-K filers (2015) to **~2,400** (2024): the share of
  AI-labeled filers reporting *any* R&D fell to **42.4%** (2024), and their median
  R&D-intensity premium over the market baseline compressed from **+0.036** (2018)
  to **+0.022** (2021) to **+0.009** (2024) — toward zero.
- **Honesty flag:** the **2015** benchmark is only 37 firms (premium −0.059) — too
  small to trust, drawn faded in the figure. The defensible reading is the
  **post-2018 compression**, when the AI pool first exceeds a few hundred firms.
- **Why it's a null, not a hot take:** the claim is not "AI is hype" — it is that
  the label's *information content about real capability decayed* as it
  proliferated (a lemons precondition). This is one of several disciplining nulls
  the project keeps prominently (the return premium is large-cap only; enforcement
  does not re-separate the cross-section; the "hollow = washer" gap is mostly a
  size effect — see the README claim-map).
- **Data script:** [`pipeline/informativeness.py`](../pipeline/informativeness.py)
  → `data/informativeness.csv` (committed at
  `data/aggregates/informativeness.csv`). Self-contained: it builds the AI-labeled
  set per year from EDGAR full-text search and reads audited R&D / revenue from the
  XBRL `frames` cross-section — no pre-built universe file, no API key.
- **Note on the other nulls:** the market-data nulls (size/sector return premium,
  FF5+momentum alpha, the size-controlled classifier) depend on issuer-level
  universe and price data that is deliberately **not** in this public repo, so they
  are documented in the claim-map but not reproduced here.

---

## Reproduce

```bash
pip install matplotlib
python pipeline/make_figures.py        # reads data/aggregates/, writes docs/figures/
```

To regenerate the underlying aggregates from live EDGAR (slower; needs a real
User-Agent, see the README):

```bash
python pipeline/ai_prevalence.py       # F1 data
python pipeline/ai_lexicon.py          # F2 data (reuses ai_prevalence's denominator cache)
python pipeline/ai_sector.py           # F3 data
python pipeline/informativeness.py     # F4 data (heavier: pages the AI-filer set + XBRL R&D)
```

Absolute counts drift as new filings arrive on EDGAR; the **shapes and ratios**
are the stable objects.
