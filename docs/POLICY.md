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

## 5. Non-reliance disclosure is the only revelation the market cannot anticipate (F8) → a bar on weakening it

Evidence: [`REVELATION.md`](REVELATION.md); `data/aggregates/car_by_event_type.csv`.

Four kinds of mandatory revelation were dated from issuers' own filings and priced against the
Russell 2000. **Only one is a surprise.**

| revelation | pre-event drift | reading |
|---|---|---|
| **non-reliance** (8-K Item 4.02) | **none** (placebo −0.86%, Corrado −0.60) | the market did **not** know the books were wrong |
| listing deficiency (Item 3.01) | significant | the market had already worked out the firm was in listing trouble |
| late filing (NT 10-K/Q) | significant | same |
| auditor change (Item 4.01) | — | **null on every window**: not treated as news at all |

By the time an exchange says a company has fallen below a listing standard, the price has already
moved. By the time a company says its financial statements cannot be relied upon, it has not — and
the announcement is worth **−3.16% in two trading days**, with $10.5B (CI $5.9–15.3B) of value
destruction across revelation days in this population.

**The lever.** Item 4.02 is carrying information the market has no other route to. That makes it a
poor candidate for the scaled-disclosure treatment smaller reporting companies receive elsewhere:
any proposal to soften, delay, or raise the materiality threshold for non-reliance reporting for
smaller filers should have to answer that number. The symmetric point is that the *auditor-change*
null suggests Item 4.01 is doing little pricing work in this population — which is where relief, if
any is wanted, would cost least.

**Scope discipline.** This measures what the market learns, not whether anyone did anything wrong. A
restatement is a statement about **disclosure**. Nothing here identifies an issuer as a wrongdoer,
and the false-positive economics in §4 apply with equal force to the F8 screen: at 9.1% precision on
its highest-recall detector, publishing issuer-level scores would brand nine solvent companies for
each troubled one, with financing consequences for exactly the firms least able to absorb them.

---

## 6. Why this belongs in a public agency, in market-failure terms

The claim throughout has been that this screen's natural home is a regulator. That is not a
preference — it follows from two standard market failures, and the empirical results supply evidence
that both bind.

**A disclosure-failure screen is a public good in the technical sense.** It is **non-rival** — one
user's use does not diminish another's — and once published **non-excludable**. Costs of production
are private; benefits are common. That is the free-rider configuration, and the prediction is
under-provision by private markets.

**The trading nulls are evidence the condition binds, not a disappointment.** The signal has real
predictive content (7.5× on restatement; 4.17× lift for the manufactured-asset detector; CARs
significant on both robust tests) and essentially no capturable private return: ruinous as a short
(median flagged firm −60.8% but **mean +89.7%**, with one name up 55,456% erasing the book) and no
alpha long (float-weighted +1.0%/−0.8%; trails the Russell 2000 by 8.1% and 1.9%). So the private
return to building it is near zero while the social return is not — which is why it does not already
exist privately. The remedy for that configuration is direct public provision.

*Honest limit:* two naive strategies were tested. A lender's covenant screen, a D&O underwriting
input, or a securities-lending borrow-pricing model were not, and could plausibly find value. The
defensible statement is "the two obvious trading uses fail, and the failure mode is structural to the
population," not "this has no private value."

**The second failure is an externality.** A misreporting issuer does not bear the full cost of its
misreporting: part falls on other small issuers, whose disclosures become less informative because
investors cannot separate them. Private marginal cost of low-quality disclosure sits below social
marginal cost, so too much is produced. [`REVELATION.md`](REVELATION.md) puts a number on one slice
of that external cost — **$10.5B** on revelation days alone — which is the magnitude any corrective
intervention would be trying to internalise, and the reason the measurement matters independently of
whether a screen is ever deployed.

---

### The through-line

Findings 1–2 say a *vocabulary* went free and the fix is to re-price the term (guidance, narrowly
scoped). Finding 3 says a *structure* routes around an existing rule and the fix is an anti-evasion
gloss where the prevalence justifies it. Finding 4 says a *screen works but only for triage*, which
is an argument about who should hold it and how it should be used, not about publishing scores.
Finding 5 says one *disclosure obligation* is doing informational work nothing else replaces, and
the lever there is protective rather than additive — do not weaken it. Finding 6 says the reason a
public body should hold any of this is a public-good and externality argument, not a preference. In every case the market-wide
measurement is what tells a regulator whether the gap is real and growing — which is the
contribution a public, reproducible measurement layer can make that issuer-level casework cannot.

**One caution that applies to all five.** The screen is a way to sort a haystack, not a metal
detector: discrimination is modest (AUC ≈ 0.58 on returns, 0.61 on restatement), and the strongest
raw version of Finding 5 was **withdrawn** after two attacks broke it — a listing-deficiency gradient
of 8.1% → 71% that fell to roughly 10% → 27% once repeat notices and a circular signal surface were
removed. The withdrawal is reported at the same length as the result that survived.

*This note states policy implications of the measurements; it is analysis, not legal advice, and
the levers are framed for discussion.*

---

## The recovery gap: every SEC dollar remedy is indexed to the wrongdoer's gain

`data/aggregates/recovery_gap.csv`

The measured harm is **$10.47B** on revelation days, 2022–2026. How much of it comes back is a
structural question, and "the SEC is underfunded" does not answer it — that explanation predicts a
uniform shortfall, and the shortfall is not uniform.

**No monetary remedy in the securities laws is measured by what investors lost.** Disgorgement is
capped at the wrongdoer's net profits after legitimate expenses (*Liu v. SEC*, 591 U.S. 71 (2020)).
Civil penalties under **15 U.S.C. §78u(d)(3)** are capped, in all three tiers, at *"the greater of"*
a fixed per-violation figure *"or the gross amount of pecuniary gain to such defendant."* The third
tier is *triggered* by *"substantial losses"* to others and never *measured* by them.

***Sripetch v. SEC*, 608 U.S. ___ (4 June 2026)** — unanimous — holds that *"a showing of pecuniary
loss to investors is not required before the SEC may obtain a disgorgement award."* That removes a
proof burden about loss. It does not create a remedy measured by loss: the Court expressly reserved
the §78u(d)(7) scope question and left *Liu*'s net-profits cap intact.

Five layers sit between harm and recovery. Four are real; the fifth was tested and is not.

| layer | measured |
|---|---|
| **Detection** — no case is brought | **0.4%–2.2%** of issuers with a dated revelation ever appear as an SEC defendant |
| **Indexation** — remedy measures gain, harm is loss | measurable gain is **13.5%** of investor loss |
| **Ordering** — the amount is small | **median $0.70M** per case; **57.9%** under $1m |
| **Return** — ordered money never reaches investors | **151** cases in the SEC's distributions index, all years, against **1,600** district-court cases in 2021–2026 alone |
| *Limitations period* | ***null*** — revelation follows the signalling filing by a median of **0.6 years**, inside the five years of §78u(d)(8) |

**Indexation is the layer no budget closes.** Across 615 issuers measurable on both sides, investor
loss is $3.69B against $0.50B of measurable insider gain. Perfect detection, perfect litigation and
perfect collection would reach roughly **one-seventh** of what investors lost — before *Liu* deducts
legitimate expenses and restricts joint-and-several liability. Both figures are on the basis least
favourable to the argument: signed loss rather than the larger negatives-only measure, and a gain
measure counting only insider open-market sales.

**The median case cannot pay the person who reported it.** §78u-6(a)(1) defines a covered action as
one *"that results in monetary sanctions exceeding $1,000,000"*, and 57.9% of district-court cases
order less. The award under §78u-6(b)(1) is a share *"of what has been collected"*, so a reporter
carries collection risk on top of threshold risk. In the population where an insider tip has the
largest informational advantage — no analyst coverage, no way for a private actor to monetise the
research — the whistleblower statute is switched off by its own floor.

**What follows is a trade-off, not a fix.** A loss-indexed remedy would likely be penal rather than
equitable, and a legal characterisation carries a post-*Jarkesy* Seventh Amendment jury right — noted
in Thomas, J.'s *Sripetch* concurrence. That raises the cost of every contested case and cuts against
bringing marginal ones. A loss-indexed remedy and a high-volume enforcement programme are in tension.
The honest alternative is to state plainly that these statutes deter and punish but do not
compensate, and to locate compensation elsewhere.

**Scope and limits.** District-court actions only — settled administrative proceedings carry
substantial additional Commission-wide disgorgement and are excluded, so the ordering figures are a
floor on agency output. Dollar amounts are parsed from 1,592 SEC litigation releases at sentence
level, with each figure retained beside the sentence it was read from. The detection bracket is wide
because company-name matching is collision-prone, and a single figure would be false precision.
