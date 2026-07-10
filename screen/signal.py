"""Core data types for the regulatory-surface screen.

A `SurfaceSpec` is one entry in the registry: a place in SEC regulation where small-cap
fraud leaves a fingerprint. A `YearAggregate` is the public, issuer-free output: how prevalent
that fingerprint is across 10-K filers in a given year. Nothing here holds an issuer identity;
the aggregate boundary is enforced by construction and checked by publication_gate.py.
"""
from dataclasses import dataclass


# Regulatory instruments (the grouping that gives the registry its breadth).
INSTRUMENTS = {
    "A": "Ownership & insider disclosure (Exchange Act Section 16, Schedule 13D/G, Rule 144)",
    "B": "Periodic disclosure quality (Reg S-K, Reg S-X, SOX 404 / Item 9A)",
    "C": "Auditor & gatekeeper (8-K Item 4.01, PCAOB inspections)",
    "D": "Capital formation (Securities Act, S-1/S-3/424B, Reg D, ATM facilities)",
    "E": "Trigger events (8-K Items 4.02, 3.01, 5.02, 1.03)",
    "F": "Entity & market structure (former names, SIC pivots, 20-F/6-K, Reg SHO)",
}


@dataclass(frozen=True)
class SurfaceSpec:
    """One regulatory surface. `fts_queries` maps a sub-signal label to an EDGAR full-text
    query; an empty dict means the surface is documented but not yet extractable from FTS
    alone (it needs structured data or per-issuer work, deferred to a later phase)."""
    id: str
    instrument: str            # key into INSTRUMENTS
    citation: str              # the SEC rule / form / item this surface sits on
    description: str           # what the fingerprint is and why fraud produces it
    fts_queries: dict          # {sub_signal_label: fts_query_string} (source="fts")
    forms: str = "10-K"        # EDGAR form filter for the FTS queries
    publishable: bool = True   # aggregate output may be published (always True here)
    source: str = "fts"        # which extractor drives this surface: fts | xbrl | index
    xbrl_concept: str = ""     # e.g. "dei:EntityCommonStockSharesOutstanding" (source="xbrl")
    thresholds: tuple = (2.0, 5.0, 10.0)   # year-over-year growth cut points (source="xbrl")
    index_form: str = ""       # EDGAR full-index form-type string, e.g. "NT 10-K" (source="index")

    def __post_init__(self):
        if self.instrument not in INSTRUMENTS:
            raise ValueError(f"{self.id}: unknown instrument {self.instrument!r}")
        if self.source not in ("fts", "xbrl", "index", "pcaob"):
            raise ValueError(f"{self.id}: unknown source {self.source!r}")


# What the denominator (n_filers) counts, so pct is never compared across incompatible bases.
DENOM_10K_FILERS = "10k_filers"            # n = filings matching the phrase; base = distinct 10-K filers
DENOM_FILING_OVER_10K = "filing_count_over_10k"  # n = count of a DIFFERENT form's filings; base = 10-K filers
DENOM_XBRL_Q4 = "xbrl_q4_intersection"     # n = filers over a growth threshold; base = the Q4-frame intersection
DENOM_PCAOB_AUDITS = "pcaob_audit_engagements"   # base = issuer audits (PCAOB Form AP) that year
DENOM_SOURCES = {DENOM_10K_FILERS, DENOM_FILING_OVER_10K, DENOM_XBRL_Q4, DENOM_PCAOB_AUDITS}


@dataclass(frozen=True)
class YearAggregate:
    """Public output row: one (surface, sub-signal, year) prevalence. Issuer-free by design.

    `n` is the numerator count and `n_filers` its denominator, but the *meaning* of both varies
    by `denom_source`, so `pct` is only comparable within the same denom_source. See DENOM_*."""
    year: int
    instrument: str
    signal_id: str          # "<surface_id>.<sub_signal_label>"
    n: int                  # numerator (matching filings, or filers over a threshold)
    n_filers: int           # denominator (meaning set by denom_source)
    denom_source: str = DENOM_10K_FILERS

    def __post_init__(self):
        if self.denom_source not in DENOM_SOURCES:
            raise ValueError(f"{self.signal_id}: unknown denom_source {self.denom_source!r}")

    @property
    def pct(self) -> float:
        return round(100.0 * self.n / self.n_filers, 3) if self.n_filers else 0.0
