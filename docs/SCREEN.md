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
- Dilution magnitude (share-count growth, reverse-split frequency as the post-dilution reset).
- Measured market-wide and over time in **F6** (`screen_signals.py`); the issuer-level triad
  detector is `dilution_evasion.py`.

**B. Gatekeeper distress (who signs off).**
- Small non-Big-4 auditor; auditor churn; "backstop" auditors that recur after serial
  turnover; going-concern opinions; material-weakness disclosures; Item 4.01 auditor-change
  direction. Scripts: `gatekeeper_screen.py`, `auditor_opinions.py`, `auditor_4_01_direction.py`.

**C. Financier concentration (who funds it).**
- A bipartite fund-to-issuer incidence: a small set of financiers touching many issuers.
  Scripts: `name_funds.py`, `financier_book.py`.

**D. Shell lineage (what the vehicle used to be).**
- Repainted dead operating companies, de-SPAC lineage, non-SPAC shells; vehicle vintage.
  Scripts: `nonspac_shells.py`, `spac_census.py`, `spac_vintage.py`.

**E. Narrative wrapper (what it claims to be now).**
- Theme-pivot into a hot narrative (AI, crypto, quantum, nuclear); simultaneous multi-theme
  claims; serial name changes. Scripts: `nano_pivot_screen.py`, `costume_rotation.py`;
  the AI-specific decoupling is F1 to F5.

**F. Cross-border structure (where the cash goes).**
- Genuine foreign control; offshore counterparty structure for low-substance "assets".
  Scripts: `foreign_control_census.py`, `foreign_control_refine.py`, `exfil_conduit.py`.

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
- **Estimation:** out-of-sample (cross-validated) area under the ROC curve, lift by score
  decile, and precision/recall, reported as **aggregate statistics** (`gap_classifier.py`).

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
