# Predicting disclosure failure, and pricing it

Everything else in this repo measures how a *label* behaved. This page measures something harder and
more useful: whether standard warning signs in a small company's annual report predict that the
company will later be **forced by rule to correct the record** — and what the market pays when it
does.

Two things make this test worth more than the return-based validation in [RESULTS.md](RESULTS.md):

- **The outcome is not a price.** It is a mandatory SEC filing. A company is not accused of anything
  by anyone; it files an 8-K Item 4.02 stating that its own previously issued financial statements
  **should no longer be relied upon.** The date is set by the issuer's legal obligation, so it cannot
  be chosen with hindsight, and the classification is EDGAR's, not ours.
- **The screen was never fitted to it.** The warning signs were selected and validated against
  forward returns. Restatement is an out-of-sample outcome of a different kind.

![Revelation](figures/f8_revelation.png)

---

## The population

14,282 issuer-vintages: every 10-K filer for 2022, 2023 and 2024, sized from XBRL total assets, with
funds, BDCs, SPACs and crypto ETPs excluded by form type and SIC. Warning signs come from six phrase
surfaces in the 10-K plus two structural detectors, grouped as in [SCREEN.md](SCREEN.md).

18,972 dated revelation events were assembled for 4,224 of those issuers from the EDGAR submissions
API — non-reliance (Item 4.02), listing deficiency (Item 3.01), auditor change (Item 4.01), and late
filing (NT 10-K/10-Q). Every event postdates the 10-K it is scored against.

---

## Result 1 — the screen predicts who retracts

`data/aggregates/revelation_incidence.csv` · `revelation_discrimination.csv`

Among issuers with **no prior listing-deficiency notice**, share later filing a non-reliance 8-K
within 20 months:

| warning signs | n | retracted own financials |
|---|---|---|
| 0 | 8,072 | 1.6% |
| 1 | 3,509 | 6.3% |
| 2 | 855 | 8.5% |
| 3 | 123 | **12.2%** |

Size-adjusted AUC **0.606** (0.575–0.639). Monotone. **7.5× top to bottom.**

### How much of this is size?

Some of it. Reported here rather than argued away, because it is the first objection anyone should
raise.

The flagged firms are small — median total assets **$17.9M** at two warning signs against **$2.1B** at
zero — and small firms fail more. So part of the raw gradient is size:

| | non-reliance | listing deficiency | any revelation |
|---|---|---|---|
| raw AUC | 0.689 | 0.711 | 0.741 |
| **size-adjusted (within terciles)** | **0.605** | **0.606** | **0.621** |
| share of the raw edge that is size | 44% | 50% | 50% |

**The 0.605–0.621 is what survives, and it is the figure quoted everywhere in this repo.** Its CI is
clear of 0.5, so the screen is not only size — but it is not size-free either, and a claim that it
were would be wrong.

**A note on `auc_size_only`, which is easy to misread.** It reads 0.185–0.305 here. That does *not*
mean size is uninformative. AUC is P(a failure scores higher than a survivor), so a value far *below*
0.5 means small firms fail **much** more — size is highly informative, just in the protective
direction. All "anti-predictive" legitimately means is that using size directly as a risk score
(bigger = riskier) would perform worse than chance. It is the size-**stratified** AUC, not the sign
of the size coefficient, that separates a screen from a size proxy. Elsewhere in this repo that
distinction cuts the other way and favourably: F7's raw AUC is 0.735 against 0.732 size-adjusted, so
size explains almost none of *that* result.

### What did not survive, and why it is shown

The raw version of this result was much larger and is **withdrawn**. Listing-deficiency incidence ran
8.1% → 71.0% across warning-sign counts. Two attacks were run:

| attack | why | effect |
|---|---|---|
| **Size** | Nasdaq's continued-listing rules include a $1 minimum bid price, so a stock at $0.80 gets a notice almost mechanically | **Survives, but size does real work.** ~50% of the raw edge is size (0.711 → 0.606 within terciles); the size-controlled figure still clears chance decisively |
| **Circularity** | One surface fires on "reverse stock split" — and firms reverse-split *in order to cure* a bid-price deficiency, so it may detect a notice already received | **Partly lands.** AUC 0.606 → 0.579 dropping that surface, → 0.572 dropping the whole pillar |
| **Repeat notices** | An issuer already under a notice can receive another | **Lands hardest.** → 0.567, and combined with the surface drop → **0.550** |

Stressed, the listing-deficiency gradient flattens from 8.1%→71% to roughly **10%→27%**, and
monotonicity breaks in two of three vintages. **The 71% figure should not be quoted.**

Non-reliance is the outcome with no circular route — a reverse stock split cannot cause a restatement
— and it gets *stronger* under the restriction (7.5× vs 3.9× unrestricted), because removing issuers
already in distress removes a confounded group. That is why it is the headline and listing deficiency
is not.

### One detector is much sharper than the screen

`data/aggregates/tier_a_precision.csv`

Evaluated as a **trigger** rather than a ranking model, against non-reliance (base rate 4.13%):

| detector | firms flagged in 3 years | precision | **lift** | Fisher exact p |
|---|---|---|---|---|
| **manufactured asset** | 29 | **17.2%** | **4.17×** | 0.006 |
| share explosion | 539 | 9.1% | 2.20× | <0.0001 |
| period inconsistency | 4 | 0.0% | — | 1.00 |

Twenty-nine companies in three years, and one in six later retracts its financials.

**AUC cannot see this, and that is a property of AUC.** For a binary flag, AUC is
(sensitivity + specificity)/2, so a flag firing on 0.2% of the population is pinned near 0.5 whatever
its precision — the manufactured-asset detector scores 0.501. `screen/eventstudy.auc_ceiling` computes
the bound explicitly. Use precision and lift for triggers; keep AUC for ranking models.

The third detector is a **failure** and is reported at the same length as the two that work: four
firms, zero restatements. It was built from a single confirmed case and does not generalise.

---

## Result 2 — what retracting costs

`data/aggregates/car_by_event_type.csv` · `attributable_loss.csv`

Abnormal returns around each filing, benchmarked to the Russell 2000, with each firm's market model
estimated over the prior year. Three test statistics; a result counts only where the two robust ones
agree.

**Non-reliance, two-day window:**

| | |
|---|---|
| mean abnormal return | **−3.16%** |
| median | −0.72% |
| share negative | 65% |
| BMP / Corrado | **−4.39 / −5.38** |
| **placebo window [−10,−3]** | −0.86%, Corrado −0.60 — **null** |

The placebo is the argument. There is no drift before the filing, so this is information the market
did not already have. Restricting to the 174 issuers with no other revelation filing nearby, it holds
at −2.03% with the placebo dead flat.

**Aggregate attributable loss** — first revelation per issuer, so a company filing several notices is
not counted several times; public float rather than market cap, because insider-held shares are not
public losses:

| | |
|---|---|
| issuers | 2,115 |
| public float | $636.6B |
| float-weighted abnormal return | −1.65% |
| **attributable loss** | **−$10.47B** (95% CI −$15.29B, −$5.89B) |

**Auditor changes move nothing.** Item 4.01 is null on every window and every test — a useful null,
since an auditor resignation reads like bad news and is not priced as news.

### Why three tests

Nano-cap returns break the standard toolkit. In the first uncorrected run, mean CARs came back at
**−172% and +2,299%** while the medians sat near −1%: a stock going $0.01 → $0.60 enters a CAR as
+59.0 and decides the average by itself.

| test | what it survives |
|---|---|
| cross-sectional *t* | nothing in particular — reported for comparability, not relied on |
| **BMP** (1991) | event-induced variance, which a revelation causes mechanically and which the plain *t* reads as significance |
| **Corrado** (1989) rank | magnitude entirely — uses only ordering, so one extreme name cannot carry a result |

Plus 1/99 winsorization before any mean is taken. The estimators are in
[`screen/eventstudy.py`](../screen/eventstudy.py) and validated against synthetic data with planted
answers in [`tests/test_eventstudy.py`](../tests/test_eventstudy.py) — including that the rank test
ignores a planted +600% outlier that drags mean CAR to +3.3%, and that BMP does not fire under 6×
event-day variance with no mean effect.

---

## Limits

- **Three windows, one macro era** (2022–2026). The screen has not seen a credit event.
- **Modest discrimination.** AUC ≈ 0.61. This sorts a haystack; it is not a metal detector.
- **Predicts correction, not fraud.** Restatement is a statement about *disclosure*. Intent is not
  observable here, and nothing in this repo identifies anyone as a wrongdoer.
- **52% of events are unpriceable** — issuers already delisted cannot be priced, and those are the
  worst outcomes, so the dollar figure **understates**.
- **The dollar aggregate is not robust to dropping confounded events**; the percentage effect is.
  Treat the percentage as the estimate and the dollar figure as descriptive.
- **Listing-deficiency and late-filing events are partly anticipated** (significant pre-event drift).
  Non-reliance is not. Only non-reliance can be read as a clean surprise.
- **The 2022 vintage parses at 57.8%** against 84–87% for 2023–24, because cover-page XBRL was phased
  in by filer status. Checked for outcome selection: unparsed issuers stop filing at 75.8% vs 80.4%,
  so they fail *more* and the 2022 sample is marginally cleaner than the population.

---

## What follows

See [POLICY.md](POLICY.md). In short: this belongs in an examination queue and nowhere else. At 9.1%
precision the share-explosion detector produces ten false positives per true one, so a published
issuer-level score would brand nine solvent companies for each troubled one — with financing
consequences for exactly the firms least able to absorb them. **The output is a queue, not a verdict.**

## Reproduce

```bash
python3 pipeline/make_figures.py && python3 -m pytest tests/test_eventstudy.py -q
```

The aggregates under `data/aggregates/` are committed. Building the revelation calendar and
estimating issuer-level CARs happens in a separate private repository, per the scope note in the
[README](../README.md#scope-what-is-not-here); only population-level rates and statistics cross into
this one.
