# Paper outline

*Working title:* **The Decoupling of the "AI" Label from Substance in US Securities
Filings, 2001–2025.**

A short, aggregate-only empirical note. The repository is its reproducibility
appendix: every claim below points to a committed figure (F1–F4 in
[`../docs/figures/`](../docs/figures/)) and an exact number (see
[`../docs/RESULTS.md`](../docs/RESULTS.md)). The author writes the prose; this is the
skeleton. **Wall: market-level only, no individual issuer named or characterized.**

---

## 1. Introduction
- The question: does the "AI" label in securities filings carry information about a
  firm's actual capability?
- Why it matters: disclosure quality, investor protection, and "AI washing" (cheap
  claims that outrun substance).
- Contribution: a clean, reproducible, market-wide measurement from public data.
- *No figure.*

## 2. Data
- EDGAR full-text search (phrase counts) + EDGAR full-index master (the filing-level
  denominator, distinct 10-K filers per year; note the FTS 10,000-result cap, which
  is why the master index, not the FTS total, is the denominator).
- XBRL `frames` for audited R&D and revenue.
- Period: 2001–2025. Aggregate-only framing stated up front.
- *No figure.*

## 3. Results

### 3.1 Prevalence: the label went everywhere
- **F1.** "artificial intelligence" in 0.79% of 10-K filers (2001) → 50.69% (2025);
  "generative AI" 0% (through 2022) → 13.37% (2025).
- Numerator = FTS phrase hits; denominator = distinct 10-K filers (master index).

### 3.2 Marketing vs. substance: the hollow fingerprint
- **F2.** In 2025, marketing vocabulary 14.55% of filers vs. build/substance
  vocabulary 1.77%; both near zero in 2001.
- Note: bucket values are summed member-phrase shares (upper bounds); the *divergence*
  between marketing and substance is the robust object.

### 3.3 Sector diffusion: out of software
- **F3.** SIC-73 (software) share of AI mentions: ~57% peak (2018) → 27% (2025).
- Honest note: early-2000s values are noisy (few AI-mentioning filers → small
  denominators); the defensible reading is the post-2018 decline, not a smooth slide.

### 3.4 Informativeness decay: the lemons precondition
- **F4.** Share of AI-labeled filers reporting any R&D: 51% (2015) → 42% (2024).
  R&D-intensity premium over the market: +0.036 (2018) → +0.022 (2021) → +0.009 (2024).
  AI-labeled pool grows n = 37 (2015) → 278 (2018) → 744 (2021) → 2,396 (2024).
- The 2015 benchmark (n=37) is a small sample, flagged; the defensible reading is the
  post-2018 compression.

### 3.5 Is the decoupling specific to AI? (placebo)
- **F5.** Same marketing template ("<term>-powered" / "<term>-driven") applied to AI and to
  controls (blockchain, cloud, quantum). 2025 marketing-form share: AI 12.9% vs 0.18% /
  0.09% / 0.03%. AI is ~70x the nearest control; bare mentions differ only ~3x. Only AI grew
  a large marketing vocabulary, which locates the effect in AI, not buzzwords generally.

## 4. Interpretation
- What the decoupling implies for disclosure quality, using **only** F1–F5.
- The honest boundary of the claim: it shows the label's *average* information content
  fell at the market level. It does **not** identify individual "washers", quantify
  investor harm, or establish causation.
- Ecological-inference caveat, stated explicitly: a population ratio cannot classify
  any single filing.
- Do **not** import issuer-level or cohort results (return-premium, enforcement, or
  extraction findings) here. Those rest on data off the public aggregate layer and
  are out of this paper's scope.

## 5. Limitations
- Phrase-based measurement; FTS caps; bucket upper bounds; count drift as filings
  accrue on EDGAR; XBRL R&D coverage; the small 2015 informativeness sample.

## 6. Conclusion
- The label's information content about real capability decayed as it proliferated;
  disclosure-policy relevance.

## 7. Reproducibility appendix
- Points to the repository, [`../docs/RESULTS.md`](../docs/RESULTS.md),
  [`../docs/METHODOLOGY.md`](../docs/METHODOLOGY.md), and
  [`../pipeline/make_figures.py`](../pipeline/make_figures.py). Every number regenerates
  from committed aggregate data.
