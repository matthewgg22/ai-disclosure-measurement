# The doctrine map: what qualifies as securities fraud, element by element

The engine measures regulatory surfaces; this document states the law those surfaces sit on.
For each core theory of securities fraud it gives (1) the elements as the statute, rule, or
controlling doctrine states them, (2) the evidence pattern in public filings that tends to
satisfy or defeat each element, and (3) the engine surface that measures that pattern
market-wide. Statutory and rule text below is quoted from the primary sources (U.S. Code and
CFR); case holdings are stated as their standard formulations with citations. Nothing here is
legal advice, and prevalence of any pattern is never a finding of fraud.

The design rule this map enforces: **a registry surface should correspond to an element the
government or a plaintiff must actually prove.** Signals that do not map to an element are
color; signals that do are evidence.

---

## 1. Rule 10b-5 fraud (private actions and SEC enforcement)

Rule 10b-5 (17 CFR 240.10b-5) makes it unlawful, in connection with the purchase or sale of
any security: "(a) To employ any device, scheme, or artifice to defraud, (b) To make any
untrue statement of a material fact or to omit to state a material fact necessary in order to
make the statements made ... not misleading, or (c) To engage in any act, practice, or course
of business which operates or would operate as a fraud or deceit upon any person."

A private damages claim requires six elements: (1) a material misrepresentation or omission;
(2) scienter; (3) a connection with the purchase or sale of a security; (4) reliance, which
fraud-on-the-market plaintiffs presume from an efficient market under Basic Inc. v. Levinson,
485 U.S. 224 (1988), as reaffirmed in Halliburton II, 573 U.S. 258 (2014); (5) economic loss;
and (6) loss causation (Dura Pharmaceuticals v. Broudo, 544 U.S. 336 (2005)).

**Pleading walls.** The PSLRA requires particularity: the complaint must specify each
misleading statement and why it is misleading, and must state with particularity facts giving
rise to a "strong inference" of scienter, which under Tellabs v. Makor Issues & Rights, 551
U.S. 308 (2007), must be cogent and at least as compelling as any opposing innocent inference.

| Element | Filing-evidence pattern that satisfies | Pattern that defeats | Engine surface |
|---|---|---|---|
| Misrepresentation | A present-tense factual claim contradicted by the issuer's own contemporaneous filings (the same fact described differently in a 10-K vs a registration statement, or a counterparty called unaffiliated that a later filing shows is related) | Puffery; forward-looking statements with meaningful cautions (section 6) | `theme_pivot`, the AI-label decoupling (F1-F5); contradiction detection is per-issuer, private |
| Scienter | Auditor replaced as doubt disappears; insider sales timed to announcements; disclosure structured around reporting thresholds (structure is hard to do accidentally) | Consistent disclosure; no insider benefit | `gc_reversal`, `auditor_churn`, `ownership_parking` |
| Materiality | Section 5 below | Quantitatively and qualitatively trivial | `eps_rounding` (SAB 99 factors are its logic) |
| Loss causation | Corrective disclosure followed by price decline | Price decline from market factors | Private (needs price series) |

## 2. Misrepresentation vs scheme liability

Under Janus Capital v. First Derivative Traders, 564 U.S. 135 (2011), only the "maker" of a
statement, the person with ultimate authority over it, faces 10b-5(b) liability. Under
Lorenzo v. SEC, 587 U.S. 71 (2019), one who disseminates a statement known to be false with
intent to defraud can be liable under the scheme prongs (a) and (c) even without being its
maker. The practical consequence for small-cap fraud: promoters, financiers, and conduits who
never sign a filing are reachable through scheme liability, which is why the engine measures
structures (who is arranged around the issuer), not just statements.

| Evidence pattern | Engine surface |
|---|---|
| The same shells, financiers, or filing agents recurring across issuers running one structure | Documented in the registry; the cross-issuer network work is per-issuer and private |
| A manufactured balance sheet used to support a listing and raises | `manufactured_asset`, `crypto_treasury` |

## 3. Section 9(a) market manipulation

Section 9(a)(1) (15 U.S.C. 78i(a)) prohibits, "for the purpose of creating a false or
misleading appearance of active trading": (A) "transactions in such security which involves
no change in the beneficial ownership thereof" (wash sales); (B) entering a purchase order
"with the knowledge that an order or orders of substantially the same size, at substantially
the same time, and at substantially the same price, for the sale" has been or will be entered
(matched orders); and (C) the mirror-image sale order. Section 9(a)(2) prohibits "a series of
transactions ... creating actual or apparent active trading in such security, or raising or
depressing the price," done "for the purpose of inducing the purchase or sale of such
security by others."

The elements live in trading data, not filings, so the engine does not measure them directly.
What filings do show is the *setup*: a float engineered to be thin and a promotion apparatus,
which is where manipulation economics come from.

| Evidence pattern | Engine surface |
|---|---|
| Reverse splits compressing the float before promotional cycles | `dilution_reset` |
| Drip-dilution machinery positioned to sell into induced demand | `toxic_dilution` (ATM, equity lines, standby equity) |

## 4. Section 17(a) offering fraud

Section 17(a) (15 U.S.C. 77q(a)) prohibits, in the offer or sale of securities: "(1) to
employ any device, scheme, or artifice to defraud, or (2) to obtain money or property by
means of any untrue statement of a material fact or any omission ..., or (3) to engage in any
transaction, practice, or course of business which operates or would operate as a fraud or
deceit upon the purchaser." The statute contains no state-of-mind language; under Aaron v.
SEC, 446 U.S. 680 (1980), scienter is required for (a)(1) but **negligence suffices for
(a)(2) and (a)(3)**. That is the SEC's lowest-friction path against offering documents, which
is why offering-adjacent surfaces (S-1/424B language, dilution machinery sold to the public)
matter even where intent would be hard to plead.

## 5. Materiality

The constitutional test: a fact is material if there is "a substantial likelihood that a
reasonable investor would consider it important," judged against the "total mix" of available
information (TSC Industries v. Northway, 426 U.S. 438 (1976); Basic, 485 U.S. 224). SAB No.
99 adds the staff's position for financial statements: "exclusive reliance on certain
quantitative benchmarks to assess materiality ... is inappropriate; misstatements are not
immaterial simply because they fall beneath a numerical threshold." Its qualitative factors,
quoted from the bulletin, include whether the misstatement "masks a change in earnings or
other trends," "hides a failure to meet analysts' consensus expectations," "changes a loss
into income or vice versa," affects "compliance with loan covenants or other contractual
requirements," has "the effect of increasing management's compensation," or "involves
concealment of an unlawful transaction."

The engine's `eps_rounding` surface is SAB 99 operationalized: a tenth-of-a-cent nudge is
quantitatively trivial and qualitatively material when it manufactures a reported cent, and
the SEC's EPS Initiative settled enforcement actions on exactly that pattern.

## 6. Puffery and the forward-looking safe harbor

Vague optimism ("committed to excellence") is generally non-actionable puffery; specificity
and repetition can convert tone into an actionable representation. For projections, Ninth
Circuit Model Civil Instruction 18.4 (codifying In re Apple and Wochos v. Tesla, 985 F.3d
1180 (9th Cir. 2021)) states the test: a forward-looking statement is actionable only if
"(1) the defendant did not actually believe the statement, (2) there was no reasonable basis
for the defendant to believe the statement, or (3) the defendant was aware of undisclosed
facts tending to seriously undermine the accuracy of the statement." The PSLRA safe harbor's
prongs are disjunctive: meaningful cautionary language protects a projection regardless of
speaker knowledge, and absent such language only actual knowledge of falsity defeats
protection. Cautions that warn of risks which have already materialized are not meaningful
(In re Alphabet Securities Litigation, 9th Cir. 2021).

**Engine consequence.** A projection alone can never evidence fraud. The fraud-relevant
object is the present-tense claim, and the strongest filings evidence is a present-tense
claim contradicted by the issuer's own contemporaneous filings. This is why the AI-label
measurement (F1-F5) separates marketing vocabulary from build vocabulary, and why the private
scoring layer gates on present-tense capability claims rather than aspirations.

## 7. Insider trading

Classical theory: a corporate insider trading on material nonpublic information breaches a
duty to shareholders (Chiarella v. United States, 445 U.S. 222 (1980)). Misappropriation
theory: an outsider trading on information taken in breach of a duty to its source (United
States v. O'Hagan, 521 U.S. 642 (1997)). Tippee liability requires the tipper to have
received a personal benefit (Dirks v. SEC, 463 U.S. 646 (1983)). Section 16(a) makes the
trades observable: officers, directors, and 10% owners must report on Forms 3, 4, and 5
within two business days.

| Evidence pattern | Engine surface |
|---|---|
| Structures that keep economic ownership under reporting thresholds so trades never surface | `sec16_evasion` (the paired pre-funded warrant + ownership blocker) |
| Section 16(a) delinquency while the 10-K certifies compliance | `insider_no_skin` (documented; per-issuer Form 4 work is private) |

## 8. Section 13(d) groups and parking

Rule 13d-5(b)(1) (17 CFR 240.13d-5): "When two or more persons agree to act together for the
purpose of acquiring, holding, voting or disposing of equity securities of an issuer, the
group formed thereby shall be deemed to have acquired beneficial ownership ... as of the date
of such agreement." A control block split across nominees so that each stays under 5% (with
the true concert of action undisclosed) is the "parking" pattern: the group exists as a legal
fact at the agreement date, and the missing Schedule 13D is itself the violation.

| Evidence pattern | Engine surface |
|---|---|
| Exhibit allocation schedules placing every recipient just below 5%; no 13D/Form 3 follows a control-block issuance | `ownership_parking` (documented; exhibit parsing deferred) |

## 9. Administrative triggers

- **Section 12(j)** (15 U.S.C. 78l(j)): after notice and opportunity for hearing, the
  Commission may suspend (up to twelve months) or revoke a security's registration where "the
  issuer ... has failed to comply with any provision of this chapter or the rules and
  regulations thereunder," as "necessary or appropriate for the protection of investors." In
  practice the delinquent-filer program applies it to issuers that stop filing periodic
  reports. This is the outcome label the engine's forward validation predicts (size-adjusted
  AUC 0.732; see RESULTS.md F7).
- **Section 12(k)** (15 U.S.C. 78l(k)): the Commission may "summarily suspend trading in any
  security ... for a period not exceeding 10 business days" when "the public interest and the
  protection of investors so require." Suspensions are the sharpest public signal that the
  Commission believes the market in a security is compromised.
- **Rule 102(e)** (17 CFR 201.102(e)): the Commission may censure or bar professionals who
  appear before it for lacking qualifications, "lacking in character or integrity," having
  "willfully violated ... the Federal securities laws," or, for accountants, "improper
  professional conduct," which includes intentional or reckless violations of professional
  standards, "a single instance of highly unreasonable conduct" where heightened scrutiny is
  warranted, or "repeated instances of unreasonable conduct." This is the gatekeeper
  discipline backdrop to the engine's auditor surfaces (`auditor_market`, `auditor_churn`).

---

## What this map is for

Every live surface in the registry now traces to an element some enforcement or private
theory must prove, and the two doctrines that constrain measurement are built into the
method: projections are excluded from fraud evidence (section 6), and issuer-level inference
is left to case work because public-data models cannot carry it (the false-positive economics
in [SCREEN.md](SCREEN.md)). The reverse direction is the roadmap: elements with no measurable
surface yet (scheme-liability networks, 13(d) group formation, loss causation) mark where the
engine grows next.
