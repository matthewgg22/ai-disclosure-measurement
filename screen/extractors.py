"""Extractors turn a SurfaceSpec into per-year aggregate prevalence.

An FTS extractor is a pure function of (client, spec, years): for each sub-signal query and
each year it asks the client for a count and divides by the 10-K filer denominator. No network
lives here; the client is the only I/O surface, so tests pass a fake client. Any SurfaceSpec
with FTS queries is handled generically by FtsExtractor, so adding an extractable surface to
the registry needs no new code here.
"""
from .signal import YearAggregate


class FtsExtractor:
    """Generic full-text-search prevalence extractor. Works for every SurfaceSpec that has
    `fts_queries`; the registry drives it."""

    def __init__(self, spec):
        if not spec.fts_queries:
            raise ValueError(f"{spec.id}: no fts_queries; not FTS-extractable")
        self.spec = spec

    def signals(self, client, years):
        rows = []
        for year in years:
            denom = client.denominator(year)
            if not denom:
                continue
            for label, query in self.spec.fts_queries.items():
                n = client.fts_count(query, year, forms=self.spec.forms)
                if n is None:
                    continue
                rows.append(YearAggregate(
                    year=int(year),
                    instrument=self.spec.instrument,
                    signal_id=f"{self.spec.id}.{label}",
                    n=int(n),
                    n_filers=int(denom),
                ))
        return rows


def extractors_for(specs):
    """Build an FtsExtractor for each extractable surface."""
    return [FtsExtractor(s) for s in specs if s.fts_queries]
