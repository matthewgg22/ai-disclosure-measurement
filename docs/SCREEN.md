# A screen for capital-extraction structures in small-cap filings

This document specifies the detection methodology behind the project: a reproducible screen
for the **capital-extraction structures** that recur in nano, micro, and small-cap securities
fraud. The AI-label study (F1 to F5) is one narrative wrapper this screen sits under; the
screen itself is about the mechanics of extraction, not any single theme.

Everything here is **aggregate and methodological**. The screen's features are computed from
public data, and this repository reports their population-level prevalence and validity. It
names no issuer, ranks no issuer, and builds no case. Issuer-level scoring, ranking, network
mapping, and case files are deliberately out of scope and are not in this repository (see the
[Scope](../README.md#scope-what-is-not-here) section).

A caution that governs the whole method: **every feature below has legitimate uses.** A
pre-funded warrant, a going-concern opinion, or a small auditor is not fraud. The screen's
premise is that *the co-occurrence of many of these features, in the small-cap tail, at the
same issuer* is what carries signal. Any single feature is a screening input, never a finding.

The aggregate-only boundary is not just an ethical choice; it is what the statistics support.
Beneish and Vorst (The Accounting Review, 2022) evaluated seven public-data fraud-prediction
models, from the M-Score to modern machine learning, and found that even the best trade off
**168 to 324 false positives for every true positive** at the individual-issuer level. At
those error rates, publishing per-issuer fraud flags from public data manufactures false
accusations at industrial scale. Market-wide prevalence of fraud-associated surfaces, the
quantity this repository reports, is the output the data can actually bear; issuer-level
inference belongs downstream, where each candidate gets human case work before any conclusion.

The legal foundation is mapped separately in [DOCTRINE.md](DOCTRINE.md): each fraud theory's
elements as the statutes, rules, and controlling cases state them, the filing-evidence pattern
that satisfies or defeats each element, and the engine surface that measures it. The design
rule it enforces: a registry surface should correspond to an element the government or a
plaintiff must actually prove.

Two principles from fraud-risk practice organize the registry. First, the residual-risk
discipline of the COSO/ACFE Fraud Risk Management Guide: for every control, ask how it can be
circumvented. Applied to securities regulation, each surface in the registry is a disclosure
rule *paired with the way issuers route around it* (Section 16 and the blocker structure;
Schedule 13D and sub-threshold parking; the going-concern opinion and the auditor swap that
sheds it). Second, deterrence economics: prevention plus detection equals deterrence, and the
certainty of detection deters more than the severity of punishment, which is why this
measurement layer is public while the issuer-level casework stays private.

## Implementation

The screen is an engine, not a pile of scripts. The registry of regulatory surfaces and the
extractors that measure them live in [`../screen/`](../screen/): each SEC surface is a
declarative `SurfaceSpec` (rule citation, instrument group, description, and either a full-text
query, an XBRL concept, or a PCAOB source), and the matching extractor turns it into per-year
aggregate prevalence through one shared, cached client per source. Three extractor types exist:
`FtsExtractor` (phrase prevalence), `XbrlExtractor` (structured facts), and `PcaobExtractor`
(auditor market structure). The XBRL signal `share_explosion` reports the share of filers whose
common-shares-outstanding count grew past 2x / 5x / 10x year-over-year (the dilution mechanism as
a hard number, not a phrase; XBRL coverage begins around 2010, and the denominator is the set of
filers reporting shares in the Q4 instant frame in both years). The PCAOB signal `auditor_market`
reads Form AP (the auditor-of-record filing that Sarbanes-Oxley Section 102 requires for every
issuer audit) and reports, per year, the share of operating-issuer audits performed by non-Big-4
firms and the share of that non-Big-4 tail concentrated in the ten busiest small firms; the
denominator is every operating-issuer audit that year (Investment Company and Employee Benefit
Plan filings excluded). A companion PCAOB surface, `auditor_churn`, reads the same Form AP data
across consecutive years and reports the aggregate rate at which continuing issuers switch audit
firms, the rate at which they downgrade from a Big-4 to a non-Big-4 firm (the direction that
tends to precede distress), and how far those switches concentrate into the ten busiest incoming
small firms; the per-issuer auditor history is built in memory and never emitted. A publication
gate
guarantees only aggregate, issuer-free rows leave the engine, and a pytest suite drives the
extractors offline with recorded fixtures. Run it with `python3 -m screen.run`; the aggregate
output is `data/aggregates/screen_registry.csv`. See [`../screen/README.md`](../screen/README.md).

**Signal calibration (honest caveat).** The FTS signals are raw phrase-prevalence and their
specificity varies. Some are sharp (the paired pre-funded-warrant + ownership-blocker
structure); others are deliberately narrow and under-inclusive (the exact phrase "variable
rate convertible" catches only a fraction of toxic-convertible language), and a few phrase
choices were tightened after a first run inflated them with boilerplate ("identified a
material weakness", not the bare phrase; "regain compliance", not generic "listing"). The
engine's value is the framework and the sharp signals; per-signal calibration is ongoing, and
the raw prevalences are screening inputs, not calibrated fraud rates.

---

## 1. The feature set

Each feature is computable from public EDGAR (full-text search, the submissions API, XBRL
frames, and the financial-statement data sets). Grouped by what they capture:

**A. The extraction instrument (how value is pulled out).**
- Pre-funded warrants (a dilution instrument exercisable for a nominal price).
- Ownership blockers ("beneficial ownership limitation" language) that keep a holder below
  the Section 16 / 5% reporting threshold, so large economic positions avoid insider
  disclosure.
- The **paired structure** (both in the same filing), which routes dilution around Section 16.
- Sub-threshold structuring of a control block ("parking"): a large issuance split across
  recipients each allocated just under the 5% reporting line, so no Schedule 13D or Form 3
  ever surfaces the transfer (registry surface `ownership_parking`, per-issuer, deferred).
- Dilution magnitude (share-count growth, reverse-split frequency as the post-dilution reset),
  plus the standing drip-dilution machinery: at-the-market facilities, standby equity purchase
  agreements, and equity lines of credit (the engine's `toxic_dilution` surface; the standby
  equity phrase grew roughly 75x from 2021 to 2025).
- Measured market-wide and over time in **F6** (the engine's `sec16_evasion` surface,
  `python -m screen.run`); the issuer-level triad
  detector is `dilution_evasion.py`.

**B. Gatekeeper distress (who signs off).**
- Small non-Big-4 auditor; auditor churn; "backstop" auditors that recur after serial
  turnover; going-concern opinions; material-weakness disclosures; Item 4.01 auditor-change
  direction. Scripts: `gatekeeper_screen.py`, `auditor_opinions.py`, `auditor_4_01_direction.py`.
- The going-concern reversal: substantial doubt that disappears the same year the auditor is
  replaced, without the finances improving (registry surface `gc_reversal`, a cross-source
  join of the going-concern hit set with the Form AP auditor-change set; deferred).
- Balance-sheet integrity: an asset carried far above the stock given for it, with the gap
  booked as a related-party non-cash contribution (ASC 845 / SAB Topic 5:G; registry surface
  `manufactured_asset`, XBRL path deferred).
- Forensic-canon accrual markers, computed live from XBRL annual frames: **receivables
  outrunning revenue** (the days-sales-in-receivables index behind Beneish's DSRI; the
  engine's `receivables_outrun` surface, at 1.5x and 2x cuts) and **profit without cash**
  (positive net income over negative operating cash flow, the `paper_earnings` surface).
  Earnings are an opinion, cash is a fact; both markers are aggregate shares over the join of
  filers reporting the underlying concepts.
- **EPS rounding management** (the engine's `eps_rounding` surface): computed quarterly EPS in
  cents should have a uniform tenth-of-a-cent digit; firms nudging income up to gain a
  reported cent erase 4s. The firm-level version of this signal predicts restatements, AAERs,
  and class actions (Malenko, Grundfest and Shen, JFQA 2023) and is the basis of the SEC
  Division of Enforcement's EPS Initiative, which has settled enforcement actions on this
  fingerprint; the engine reports the market-wide digit-4 share per year, where the
  no-management null is 10%. In the engine's series the digit-4 share runs a clear deficit
  (8.6 to 9.7%) from 2010 through 2019, then returns to the 10% null from 2020 on, coincident
  with the Initiative's first enforcement actions: consistent with the deterrence effect of
  the SEC operationalizing the fingerprint.

**C. Financier concentration (who funds it).**
- A bipartite fund-to-issuer incidence: a small set of financiers touching many issuers.
  Scripts: `name_funds.py`, `financier_book.py`.

**D. Shell lineage (what the vehicle used to be).**
- Repainted dead operating companies, de-SPAC lineage, non-SPAC shells; vehicle vintage.
  Scripts: `nonspac_shells.py`, `spac_census.py`, `spac_vintage.py`.

**E. Narrative wrapper (what it claims to be now).**
- Theme-pivot into a hot narrative (AI, crypto, quantum, nuclear); simultaneous multi-theme
  claims; serial name changes (the EDGAR former-names record and a SIC code left stale across
  pivots are the structured trail). Scripts: `nano_pivot_screen.py`, `costume_rotation.py`;
  the AI-specific decoupling is F1 to F5.
- The digital-asset-treasury pivot: announcing that holding cryptocurrency IS the business,
  with fair-value accounting able to manufacture headline profit in an up quarter (the
  engine's `crypto_treasury` surface; near zero before 2024, then 5-6.7% of 8-K text in 2025).

**F. Cross-border structure (where the cash goes).**
- Genuine foreign control; offshore counterparty structure for low-substance "assets".
  Scripts: `foreign_control_census.py`, `foreign_control_refine.py`, `exfil_conduit.py`.
- CFIUS surfacing in current reports (the engine's `foreign_control` surface): the CFIUS
  docket itself is confidential by statute, so the issuer's own 8-K disclosure is the only
  public surface; steady 2-3.4% of 8-K filings mention it.

---

## 2. How the screen is scored

The screen combines the features into a per-filing risk profile: a count of independent
red-flags tripped, weighted toward the extraction instrument (group A) and gatekeeper
distress (group B), which are the hardest to explain innocently in combination. The output of
interest for this public repository is always a **distribution or a rate** over a population
(for example, the share of small-cap filers tripping at least N flags), never a ranked list.

---

## 3. Validation (does the screen predict harm?)

A screen is only worth the name if it predicts bad outcomes out of sample. The validation
design, which is the standard the project holds itself to:

- **Outcome (external, market-based):** a filer is a "bad outcome" if it later delists (its
  price series dies) or suffers a large forward drawdown (for example, a return of -50% or
  worse over a fixed forward window). This outcome is independent of the screen, so predicting
  it is not circular.
- **Predictor:** the red-flag score described above.
- **Control:** firm size. Small firms fail more often for reasons unrelated to extraction, so
  the screen must add predictive power **after** conditioning on size.
- **Estimation:** out-of-sample area under the ROC curve, lift by score decile, and
  calibration, reported as **aggregate statistics**.

**The harness is built.** [`../screen/validation.py`](../screen/validation.py) implements this:
a transparent-score AUC (rank-based, no model fit), a size-adjusted AUC (mean AUC within
size terciles, so the score must clear 0.5 *after* the size control), lift by decile, and a
fixed-seed bootstrap CI. It operates on an abstract labeled table (score, size, outcome) and
holds no issuer identity, so it lives here and is unit-tested on synthetic data (it recovers a
planted signal, shows the size-only baseline is weaker, and returns ~0.5 on noise).

**The harness has now run on real labels, and the gatekeeper dimension validates.** The
issuer-level run is private (per the wall); the aggregate result is committed here
(`data/aggregates/validation_summary.csv`, `validation_lift.csv`; figure F7 in
[RESULTS.md](RESULTS.md)):

- **Forward design.** A transparent 0-3 auditor-distress score (non-Big-4 auditor, Big-4 to
  non-Big-4 downgrade, auditor churn, all from PCAOB Form AP) measured strictly through fiscal
  2021; outcome = an SEC Section 12(j) delinquent-filer proceeding or trading suspension in
  2022+. Nothing from the outcome window enters the score or the size control.
- **Result:** size-adjusted AUC **0.732**, 95% bootstrap CI **(0.578, 0.773)**, n = 8,393,
  234 failures. Top deciles fail at ~6-7% vs 0.0% in the bottom two. Size alone is
  anti-predictive (AUC 0.11), so this is not a size story.
- **The paired nulls.** The same score against large-cap AAER enforcement is null (0.564, CI
  straddling 0.5): AAER targets skew large and Big-4-audited, the wrong population for this
  score, which is itself the population-match lesson. A deliberately noisy label (all Form
  25-NSE delistings, mixing failures with mergers and note redemptions) was predicted null in
  advance and came back 0.492. The harness says no when the labels are wrong.
- **Scope of the claim:** one dimension (gatekeeper distress) is validated against one class
  of regulatory outcome; the composite screen and the other groups still need their own
  labeled runs. The score is coarse and the CI wide, though clean of 0.5.

**A disciplining result the project keeps in front, not buried:** the naive "hollow firm =
washer" resource gap is **mostly a size effect**. A size-controlled classifier on that feature
alone gains only about +0.01 AUC. The discriminating power lives in the **structural** features
(the extraction instrument, gatekeeper distress, financier concentration, shell lineage), not
in "this firm looks small and hollow." This is why the screen is built on structure, and why
single-feature screens are reported as the weak baselines they are.

---

## 4. What is in this repo, and what is not

**In (public, aggregate):** the feature definitions above; the market-wide prevalence and
trend of the extraction-instrument language (F6); the AI-label decoupling that is one
narrative wrapper (F1 to F5); the disciplining nulls; and the validation *design*.

**Out (private, issuer-level):** any list, score, or ranking of individual issuers; the
Section 16(b) short-swing matcher; lead generation; entity-network mapping; and case files.
These belong to active, enforcement-facing work and are kept out of this public repository by
design. Nothing here identifies or targets a company as a fraud suspect.

The point of the public layer is to show that the **structures are detectable and their spread
is measurable from public data**, and to state the method precisely enough that the aggregate
results are reproducible. The issuer-level application is a separate, non-public matter.
