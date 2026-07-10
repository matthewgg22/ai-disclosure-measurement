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


class XbrlExtractor:
    """Structured share-dilution extractor. Reads the shares-outstanding instant frame for
    year and year-1, joins on the CIK intersection (both values > 0), and emits the AGGREGATE
    count of filers whose share count grew past each threshold. The per-CIK growth is never
    emitted; only the counts leave. `signals` is a pure function of the client."""

    def __init__(self, spec, min_filers=100):
        if spec.source != "xbrl" or not spec.xbrl_concept:
            raise ValueError(f"{spec.id}: not an xbrl surface")
        self.spec = spec
        self.min_filers = min_filers  # skip years with too small an intersection (early XBRL)

    def signals(self, client, years):
        rows = []
        for year in years:
            cur = client.xbrl_frames_instant(self.spec.xbrl_concept, year)
            prev = client.xbrl_frames_instant(self.spec.xbrl_concept, year - 1)
            if not cur or not prev:
                continue
            growth = [cur[c] / prev[c] for c in cur
                      if c in prev and prev[c] and prev[c] > 0 and cur.get(c, 0) > 0]
            n_filers = len(growth)
            if n_filers < self.min_filers:
                continue
            for t in self.spec.thresholds:
                n = sum(1 for g in growth if g > t)
                rows.append(YearAggregate(
                    year=int(year),
                    instrument=self.spec.instrument,
                    signal_id=f"{self.spec.id}.pct_over_{int(t)}x",
                    n=int(n),
                    n_filers=int(n_filers),
                ))
        return rows


def extractor_for(spec):
    """Return the extractor that drives a surface, by its source."""
    if spec.source == "xbrl":
        return XbrlExtractor(spec)
    return FtsExtractor(spec)  # source == "fts" (index source is a later phase)


def extractors_for(specs):
    """Build the right extractor for each extractable surface."""
    out = []
    for s in specs:
        if s.source == "fts" and s.fts_queries:
            out.append(FtsExtractor(s))
        elif s.source == "xbrl" and s.xbrl_concept:
            out.append(XbrlExtractor(s))
    return out
