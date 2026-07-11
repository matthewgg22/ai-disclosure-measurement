"""The regulatory-surface registry: the breadth of SEC regulation, made computable.

Each entry is a SurfaceSpec tied to a specific rule/form/item. Surfaces with a non-empty
`fts_queries` are extractable now from public EDGAR full-text search (Phase 1+2); the rest are
documented here so the registry IS the full breadth, and are wired to structured-data or
per-issuer extractors in later phases. Adding regulatory coverage = adding a SurfaceSpec (and,
when extractable, an extractor), never a new pipeline.
"""
from .signal import SurfaceSpec

REGISTRY = [
    # --- A. Ownership & insider disclosure ---
    SurfaceSpec(
        id="sec16_evasion",
        instrument="A",
        citation="Exchange Act Section 16(a); Rule 16a-1; Schedule 13D/13G",
        description=(
            "Pre-funded warrant paired with a 'beneficial ownership limitation' blocker keeps a "
            "holder under the 5%/10% threshold, avoiding Form 3/4/5 and 13D beneficial-ownership "
            "disclosure. The paired structure routes dilution around insider reporting."),
        fts_queries={
            "prefunded_warrant": '"pre-funded warrant"',
            "ownership_blocker": '"beneficial ownership limitation"',
            "paired": '"pre-funded warrant" "beneficial ownership limitation"',
        },
    ),
    SurfaceSpec(
        id="insider_no_skin",
        instrument="A",
        citation="Exchange Act Section 16(a); Form 4",
        description=(
            "A capital raise with near-zero insider open-market Form 4 purchases: insiders take "
            "cash via warrants rather than buying equity. A companion measure is Section 16(a) "
            "delinquency itself: Form 4s filed far past the two-business-day deadline, or never, "
            "while the 10-K certifies compliance. Needs per-issuer Form 4 parsing."),
        fts_queries={},  # per-issuer, deferred
    ),
    SurfaceSpec(
        id="ownership_parking",
        instrument="A",
        citation="Exchange Act Section 13(d); Schedule 13D; Item 403 ownership tables",
        description=(
            "A control block issued to many recipients each allocated just under the 5% "
            "reporting threshold, so no Schedule 13D, Form 3, or ownership-table line ever "
            "surfaces the transfer: sub-threshold structuring of beneficial ownership "
            "('parking'). Detection needs exhibit-level allocation schedules read against the "
            "issuer's share count; per-issuer, deferred."),
        fts_queries={},
    ),
    # --- B. Periodic disclosure quality ---
    SurfaceSpec(
        id="going_concern",
        instrument="B",
        citation="Reg S-X; PCAOB AS 2415 (going concern)",
        description="Auditor substantial-doubt / going-concern language: solvency distress.",
        fts_queries={"going_concern": '"substantial doubt" "going concern"'},
    ),
    SurfaceSpec(
        id="material_weakness",
        instrument="B",
        citation="SOX Section 404; Reg S-K Item 308; Item 9A",
        description="Disclosed material weakness in internal control over financial reporting.",
        # Specific to an actual disclosure; the bare phrase "material weakness" is 10-K
        # boilerplate (it appears in risk factors even absent a finding).
        fts_queries={"material_weakness": '"identified a material weakness"'},
    ),
    SurfaceSpec(
        id="late_filing",
        instrument="B",
        citation="Exchange Act Rule 12b-25; Form NT 10-K",
        description=(
            "Late-filing notifications: the count of Form NT 10-K filings (a filer telling the SEC "
            "it cannot file its 10-K on time) per year, as a share of 10-K filers. A structured "
            "form-type count (empty full-text query, filtered to the NT 10-K form), not a phrase."),
        fts_queries={"nt_10k": ""},   # empty query = count all filings of the `forms` type
        forms="NT 10-K",
    ),
    SurfaceSpec(
        id="resource_mismatch",
        instrument="B",
        citation="Reg S-X (financial statements); XBRL frames",
        description=(
            "A technology claim with R&D near zero and revenue near zero (the capability-signal "
            "test). Computed from XBRL, not FTS; see pipeline/informativeness.py."),
        fts_queries={},  # XBRL-based, handled by the informativeness path
    ),
    SurfaceSpec(
        id="manufactured_asset",
        instrument="B",
        citation="ASC 845 (nonmonetary transactions); SEC SAB Topic 5:G; Reg S-X",
        description=(
            "A balance sheet built by related-party non-cash entries: an asset acquired from "
            "related sellers in an all-stock exchange, carried far above the value of the stock "
            "given, with the gap booked as a related-party capital contribution for which no "
            "consideration was paid. SAB Topic 5:G's historical-cost principle is the yardstick. "
            "The structured trail is the equity statement and the non-cash section of the cash "
            "flow statement; XBRL extraction deferred (exact phrases are too issuer-specific "
            "for full-text search, measured prevalence ~0)."),
        fts_queries={},
    ),
    SurfaceSpec(
        id="receivables_outrun",
        instrument="B",
        citation="Reg S-X (financial statements); XBRL frames; forensic canon (Beneish DSRI)",
        description=(
            "Receivables growing much faster than revenue: the classic accrual-manipulation "
            "marker (sales booked that customers are not paying for). Computed from XBRL as "
            "the share of filers whose year-over-year receivables growth outruns revenue "
            "growth by 1.5x / 2x (a days-sales-in-receivables index), over the join of filers "
            "reporting both concepts in both years."),
        fts_queries={},
        source="xbrl",
        xbrl_concept="AccountsReceivableNetCurrent",
    ),
    SurfaceSpec(
        id="paper_earnings",
        instrument="B",
        citation="Reg S-X (statement of cash flows); XBRL frames; 'follow the money'",
        description=(
            "Profit without cash: filers reporting positive net income while operating cash "
            "flow is negative. Earnings are an opinion, cash is a fact; a persistent gap is "
            "the accrual signature that precedes many restatements. Share of filers with "
            "NI > 0 and operating cash flow < 0 over the join reporting both."),
        fts_queries={},
        source="xbrl",
        xbrl_concept="NetIncomeLoss",
    ),
    # --- C. Auditor & gatekeeper ---
    SurfaceSpec(
        id="auditor_market",
        instrument="C",
        citation="PCAOB Form AP (auditor reporting); Sarbanes-Oxley Section 102",
        description=(
            "Auditor-market structure from PCAOB Form AP: the share of issuer-audits done by "
            "non-Big-4 firms, and how concentrated the non-Big-4 book is in the ten busiest small "
            "firms (the 'backstop auditor' pattern). Small-cap fraud clusters at marginal and "
            "concentrated auditors. Form AP coverage begins ~2016."),
        fts_queries={},
        source="pcaob",
    ),
    SurfaceSpec(
        id="auditor_churn",
        instrument="C",
        citation="PCAOB Form AP (auditor reporting); Sarbanes-Oxley Section 102",
        description=(
            "Auditor churn and backstop recurrence from PCAOB Form AP, year over year: the share "
            "of continuing issuers that switched audit firms, the share that dismissed a Big-4 for "
            "a non-Big-4 firm (the 'auditor downgrade' that often precedes distress), and how far "
            "the switches concentrate into the ten busiest incoming small firms. Aggregate only; "
            "the per-issuer auditor history stays in memory."),
        fts_queries={},
        source="pcaob",
    ),
    SurfaceSpec(
        id="gc_reversal",
        instrument="C",
        citation="PCAOB AS 2415 (going concern); Form 8-K Item 4.01; PCAOB Form AP",
        description=(
            "A going-concern doubt that disappears in the same year the auditor is replaced, "
            "without the finances improving: the doubt is shed with the opinion-giver, not "
            "resolved. Measurable as an aggregate by joining the going-concern full-text hit "
            "set with the Form AP auditor-change set per year; cross-source extractor "
            "deferred."),
        fts_queries={},
    ),
    # --- D. Capital formation ---
    SurfaceSpec(
        id="toxic_dilution",
        instrument="D",
        citation="Securities Act; Forms S-1/S-3/424B; Reg D Form D",
        description=(
            "Variable-rate / death-spiral convertible language and at-the-market (ATM) facilities: "
            "structures that convert at a discount to a falling price, compounding dilution."),
        fts_queries={
            "atm_facility": '"at-the-market offering"',
            "variable_rate_convertible": '"variable rate convertible"',
            # Standby equity purchase agreements / equity lines: a financier commits to buy
            # shares on demand at a discount to market, the nano-cap drip-dilution machine.
            "standby_equity": '"standby equity purchase agreement"',
            "equity_line": '"equity line of credit"',
        },
    ),
    SurfaceSpec(
        id="dilution_reset",
        instrument="D",
        citation="Exchange listing standards (bid-price compliance); 8-K",
        description="Reverse stock split: the post-dilution reset used to regain bid-price compliance.",
        fts_queries={"reverse_split": '"reverse stock split"'},
    ),
    SurfaceSpec(
        id="share_explosion",
        instrument="D",
        citation="Reg S-X; XBRL dei:EntityCommonStockSharesOutstanding",
        description=(
            "Year-over-year shares-outstanding growth: the dilution mechanism as a hard number. "
            "Reads the Q4 instant frame for year and year-1, joins on the CIK intersection, and "
            "reports the share of filers whose count grew past 2x / 5x / 10x."),
        fts_queries={},
        source="xbrl",
        xbrl_concept="dei:EntityCommonStockSharesOutstanding",
        thresholds=(2.0, 5.0, 10.0),
    ),
    # --- E. Trigger events ---
    SurfaceSpec(
        id="restatement",
        instrument="E",
        citation="Form 8-K Item 4.02 (non-reliance on previously issued financials)",
        description=(
            "Count of 8-K filings citing Item 4.02, the actual non-reliance / restatement "
            "announcement form, per year. This is the precise trigger on the correct form (it "
            "matches the count from the non-reliance language, ~280 in 2024), replacing the older "
            "10-K text proxy. Denominator is the 10-K filer base, so the rate is per public "
            "company per year."),
        fts_queries={"item_4_02": '"Item 4.02"'},
        forms="8-K",
    ),
    SurfaceSpec(
        id="delist_notice",
        instrument="E",
        citation="Exchange listing standards; Form 8-K Item 3.01 (delisting / listing-rule failure)",
        description=(
            "An actual exchange deficiency the filer is working to cure. 'regain compliance' is "
            "specific to a live deficiency remediation, unlike generic 'listing' risk-factor text."),
        fts_queries={"regain_compliance": '"regain compliance"'},
    ),
    SurfaceSpec(
        id="enforcement_pipeline",
        instrument="E",
        citation="Exchange Act Section 21 (investigations); Rule 10b-5 half-truth doctrine",
        description=(
            "The enforcement pipeline surfacing in periodic reports: filers disclosing receipt "
            "of a Wells notice (the SEC staff's advance warning of a recommended enforcement "
            "action) or a subpoena. There is no clean line-item duty to disclose an "
            "investigation, so under the half-truth doctrine the disclosure itself is a signal "
            "the issuer judged the matter material or already 'in play'. Both phrases are "
            "deliberately narrow; prevalence is a floor, not the rate of investigations."),
        fts_queries={
            "wells_notice": '"Wells notice"',
            "subpoena": '"received a subpoena"',
        },
    ),
    # --- F. Entity & market structure ---
    SurfaceSpec(
        id="theme_pivot",
        instrument="F",
        citation="Reg S-K Item 101 (business description); EDGAR former-names record; SIC codes",
        description=(
            "Narrative rotation into a hot theme (AI/crypto/quantum). The structured trail is "
            "the EDGAR former-names record (one CIK, serial renamings tracking each theme) and "
            "a SIC code left stale across pivots; the submissions API exposes both per issuer. "
            "See F1-F5 for the AI cut; the former-names census is deferred (needs a per-CIK "
            "submissions sweep)."),
        fts_queries={},  # covered by the AI-label pipeline; other themes deferred
    ),
    SurfaceSpec(
        id="crypto_treasury",
        instrument="F",
        citation="Form 8-K; ASU 2023-08 (crypto assets at fair value); Reg S-K Item 101",
        description=(
            "The digital-asset-treasury pivot: an issuer announces that holding cryptocurrency "
            "IS the business. Fair-value accounting under ASU 2023-08 lets a coin position "
            "manufacture headline profit in an up quarter, and an unverifiable or offshore "
            "holding can prop a listing while equity is sold against it. Phrase prevalence on "
            "8-K announcements; the wave is new (near zero before 2024)."),
        fts_queries={
            "bitcoin_treasury": '"bitcoin treasury"',
            "digital_asset_treasury": '"digital asset treasury"',
        },
        forms="8-K",
    ),
    SurfaceSpec(
        id="foreign_control",
        instrument="F",
        citation="DPA Section 721 (CFIUS); FIRRMA; Forms 20-F / 6-K; Reg S-K Item 101",
        description=(
            "Foreign control and national-security review surfacing in current reports: the "
            "share of 8-K filings that mention CFIUS (deals conditioned on, cleared by, or "
            "risk-disclosing a CFIUS review). CFIUS's own docket is confidential by statute, so "
            "the issuer's disclosure is the only public surface. A screening input: most "
            "mentions are routine deal conditions; the fraud-relevant case is a "
            "CFIUS-conditioned counterparty with no filing ever disclosed, which is per-issuer "
            "and out of scope here."),
        fts_queries={"cfius": '"CFIUS"'},
        forms="8-K",
    ),
]


def extractable():
    """Surfaces that can be measured now: FTS surfaces with queries, or XBRL surfaces with a
    concept."""
    out = []
    for s in REGISTRY:
        if s.source == "fts" and s.fts_queries:
            out.append(s)
        elif s.source == "xbrl" and s.xbrl_concept:
            out.append(s)
        elif s.source == "pcaob":
            out.append(s)
    return out


def by_id(surface_id):
    for s in REGISTRY:
        if s.id == surface_id:
            return s
    raise KeyError(surface_id)
