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
    fts_queries: dict          # {sub_signal_label: fts_query_string}
    forms: str = "10-K"        # EDGAR form filter for the FTS queries
    publishable: bool = True   # aggregate output may be published (always True here)

    def __post_init__(self):
        if self.instrument not in INSTRUMENTS:
            raise ValueError(f"{self.id}: unknown instrument {self.instrument!r}")


@dataclass(frozen=True)
class YearAggregate:
    """Public output row: one (surface, sub-signal, year) prevalence. Issuer-free by design."""
    year: int
    instrument: str
    signal_id: str      # "<surface_id>.<sub_signal_label>"
    n: int              # count of 10-K filers tripping the signal that year
    n_filers: int       # denominator (distinct 10-K filers that year)

    @property
    def pct(self) -> float:
        return round(100.0 * self.n / self.n_filers, 3) if self.n_filers else 0.0
