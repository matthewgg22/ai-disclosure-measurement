# From measurement to policy levers

This project is a measurement layer, not an advocacy document. But each finding sits directly
against a specific regulatory instrument, and the point of measuring at market scale is to tell
whether a disclosure rule is doing its work. This note maps the four headline findings to the
lever each one implicates, in ascending order of intervention cost. Nothing here names an issuer;
the mappings are structural.

The organizing premise is standard information economics: mandatory disclosure improves market
efficiency only while the *vocabulary* of disclosure stays tied to substance. When a term becomes
free to use, it stops separating firms and starts letting weaker firms pool with stronger ones
(Akerlof's lemons dynamic). Three of the four findings are evidence that a term has gone free; the
fourth is evidence that a structural rule is being routed around. The levers differ accordingly.

---

## 1. The label's information content decayed (F4) → the definitional gap in AI disclosure

**Finding.** The AI label's measurable link to audited R&D fell from a real premium in 2018
(+0.036, CI excluding zero) to statistical zero by 2024, even as the label spread to a majority of
filers. Marketing vocabulary reached 14.6% of filers while the costly build vocabulary stayed at
1.8%.

**Why the current rule permits it.** Item 101/303 disclosure of technology and trends is
principles-based, and "artificial intelligence" has no defined meaning in Regulation S-K. A firm
can write "AI-powered" with no obligation to characterize what, if anything, the term denotes in
its operations. Principles-based disclosure works when a term is costly to assert; it fails exactly
when the term goes free, which is what F4 measures.

**Lever (lowest cost).** Interpretive guidance, not rulemaking: an SEC staff statement — the same
instrument used for cybersecurity and climate before those matured into rules — that a material AI
capability claim carries an obligation to describe its basis (data, model, deployment stage,
revenue dependence), and that undifferentiated "AI-powered" framing without such basis may be
misleading under existing 10b-5 and Item 303 standards. This costs no new rule; it re-prices the
free term by attaching a characterization duty to it. The March 2024 Delphia / Global Predictions
settlements already assert this theory against advisers; guidance would extend the same logic to
issuer disclosure before it requires case-by-case enforcement.

## 2. The pattern is AI-specific, not generic buzzword behavior (F5) → scope discipline

**Finding.** Applying the identical marketing template to control buzzwords, only AI produced a
large marketing vocabulary (12.9% of filers in 2025 vs ≤0.18% for blockchain, cloud, quantum).

**Policy relevance.** This is a scoping result, and it cuts *against* over-broad rulemaking. A
generic "emerging-technology hype" rule would sweep in terms that show no washing pattern. The
evidence supports a **narrow, AI-specific** interpretive posture rather than a broad new disclosure
category — a discipline that makes the intervention more defensible and less burdensome.

## 3. Extraction routes around Section 16 / Section 13(d) (F6) → a genuine rule gap

**Finding.** The pre-funded-warrant instrument reached 8.6% of 10-K filers by 2025, and the
**paired** structure — a pre-funded warrant plus a "beneficial ownership limitation" blocker in the
same filing — reached 2.0%, almost entirely since 2020. The blocker keeps a holder nominally below
the 5%/10% beneficial-ownership threshold, so a large economic position avoids the Section 16 and
Schedule 13D insider-disclosure regime.

**Why this is different from 1 and 2.** This is not a vocabulary going free; it is a **structural
rule being engineered around**. Beneficial ownership under Rule 13d-3 turns on voting and
investment power, and a contractual exercise cap is used to argue a holder never "beneficially
owns" the underlying shares — so economic exposure and disclosed ownership diverge by design.

**Lever (higher cost, but a real gap).** This is the finding with a rulemaking case, and it is
narrowly framable: revisit whether a fixed exercise blocker should defeat beneficial-ownership
attribution when the holder retains the economic interest and the right to remove the cap on
notice — i.e., an anti-evasion gloss on Rule 13d-3(b), which already reaches arrangements whose
purpose is to prevent 13(d) attribution. The measurement matters here precisely because a rule
change should be justified by prevalence and trend, not by anecdote; F6 supplies both, market-wide.

## 4. The screen predicts regulatory failure out of sample (F7) → screening economics for triage

**Finding.** A transparent gatekeeper-distress score, measured through FY2021, predicts 2022+ SEC
trading suspensions and 12(j) proceedings at size-adjusted AUC 0.73, against a 2.8% base rate.

**The policy content is in the base rate, not the AUC.** At a 2.8% base rate, even a good screen
produces many false positives per true positive (the Beneish–Vorst 168–324:1 ceiling on
public-data models). The correct institutional use is therefore **triage, not adjudication**:
ordering scarce examination and enforcement attention, not flagging firms to the public. This is an
argument for the SEC and PCAOB to run forward-validated public-data screens **internally** to
allocate inspection resources — the PCAOB already targets inspections, and auditor-churn /
backstop-auditor structure (Group C surfaces) is a directly usable targeting input — while the same
false-positive economics argue against any public issuer-level scoring, including by third parties.
The responsible-disclosure split this repository enforces (publish the measurement, withhold the
targeting) is the same line an agency would draw.

---

### The through-line

Findings 1–2 say a *vocabulary* went free and the fix is to re-price the term (guidance, narrowly
scoped). Finding 3 says a *structure* routes around an existing rule and the fix is an anti-evasion
gloss where the prevalence justifies it. Finding 4 says a *screen works but only for triage*, which
is an argument about who should hold it and how it should be used, not about publishing scores. In
every case the market-wide measurement is what tells a regulator whether the gap is real and
growing — which is the contribution a public, reproducible measurement layer can make that
issuer-level casework cannot.

*This note states policy implications of the measurements; it is analysis, not legal advice, and
the levers are framed for discussion.*
