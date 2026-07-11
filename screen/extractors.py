"""Extractors turn a SurfaceSpec into per-year aggregate prevalence.

An FTS extractor is a pure function of (client, spec, years): for each sub-signal query and
each year it asks the client for a count and divides by the 10-K filer denominator. No network
lives here; the client is the only I/O surface, so tests pass a fake client. Any SurfaceSpec
with FTS queries is handled generically by FtsExtractor, so adding an extractable surface to
the registry needs no new code here.
"""
from collections import Counter

from .pcaob import is_big4, firm_key
from .signal import (YearAggregate, DENOM_10K_FILERS, DENOM_FILING_OVER_10K,
                     DENOM_XBRL_Q4, DENOM_PCAOB_AUDITS, DENOM_XBRL_JOIN)


class FtsExtractor:
    """Generic full-text-search prevalence extractor. Works for every SurfaceSpec that has
    `fts_queries`; the registry drives it."""

    def __init__(self, spec):
        if not spec.fts_queries:
            raise ValueError(f"{spec.id}: no fts_queries; not FTS-extractable")
        self.spec = spec

    def signals(self, client, years):
        # A 10-K phrase is ~one match per filer (comparable to the filer base); a non-10-K
        # form (8-K, NT 10-K) is a raw filing count over the same base, a different unit.
        denom_source = DENOM_10K_FILERS if self.spec.forms == "10-K" else DENOM_FILING_OVER_10K
        rows = []
        for year in years:
            denom = client.denominator(year)
            if not denom:
                continue
            for label, query in self.spec.fts_queries.items():
                n = client.fts_count(query, year, forms=self.spec.forms)
                if n is None:   # fetch failed (distinct from a real 0); recorded by run_all
                    continue
                rows.append(YearAggregate(
                    year=int(year),
                    instrument=self.spec.instrument,
                    signal_id=f"{self.spec.id}.{label}",
                    n=int(n),
                    n_filers=int(denom),
                    denom_source=denom_source,
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
                    denom_source=DENOM_XBRL_Q4,
                ))
        return rows


class PcaobExtractor:
    """Auditor-market structure from PCAOB Form AP. For each year: the share of issuer-audits
    done by non-Big-4 firms, and how concentrated the non-Big-4 audits are in the ten busiest
    small firms (the 'backstop auditor' pattern). Issuer<->auditor pairs stay in the client's
    ignored cache; only the yearly shares are emitted."""

    def __init__(self, spec, min_audits=100, top_n=10):
        if spec.source != "pcaob":
            raise ValueError(f"{spec.id}: not a pcaob surface")
        self.spec = spec
        self.min_audits = min_audits   # skip thin early Form AP years
        self.top_n = top_n

    def signals(self, client, years):
        # one auditor per (year, issuer); the client already yields the latest Form AP filing
        by_year = {}
        for year, firm, cik, _rtype in client.audits():
            by_year.setdefault(year, {})[cik] = firm
        rows, want = [], set(int(y) for y in years)
        for year, firm_by_cik in by_year.items():
            if year not in want:
                continue
            total = len(firm_by_cik)
            if total < self.min_audits:
                continue
            nonbig4 = [f for f in firm_by_cik.values() if not is_big4(f)]
            nb = len(nonbig4)
            rows.append(YearAggregate(year, self.spec.instrument,
                                      f"{self.spec.id}.nonbig4_share", nb, total,
                                      denom_source=DENOM_PCAOB_AUDITS))
            if nb:
                top = sum(c for _, c in Counter(nonbig4).most_common(self.top_n))
                rows.append(YearAggregate(year, self.spec.instrument,
                                          f"{self.spec.id}.top{self.top_n}_nonbig4_share", top, nb,
                                          denom_source=DENOM_PCAOB_AUDITS))
        rows.sort(key=lambda r: (r.signal_id, r.year))
        return rows


class AuditorChurnExtractor:
    """Auditor churn and backstop recurrence from PCAOB Form AP, aggregate only. Building each
    issuer's auditor across years in memory, then for each year Y over the issuers audited in
    BOTH Y-1 and Y (continuing issuers) it emits:
      change_rate          share that switched to a different audit firm (Big-4 network name
                           variants collapse via firm_key, so they do not read as a change)
      big4_to_nonbig4      of continuing issuers that had a Big-4 in Y-1, the share now on a
                           non-Big-4 firm (the 'auditor downgrade' that often precedes distress)
      backstop_top{N}_share of the issuers that switched to a non-Big-4 firm, the share whose
                           new firm is one of the N busiest incoming small firms that year
    Per-issuer histories never leave; only the yearly shares are emitted."""

    def __init__(self, spec, min_pairs=100, top_n=10):
        if spec.source != "pcaob" or spec.id != "auditor_churn":
            raise ValueError(f"{spec.id}: not the auditor_churn surface")
        self.spec = spec
        self.min_pairs = min_pairs   # skip years with too few continuing issuers
        self.top_n = top_n

    def signals(self, client, years):
        by_year = {}   # year -> {cik: (firm_key, firm_name)}
        for year, firm, cik, _rtype in client.audits():
            by_year.setdefault(year, {})[cik] = (firm_key(firm), firm)
        inst, sid = self.spec.instrument, self.spec.id
        rows = []
        for year in sorted({int(y) for y in years}):
            cur, prev = by_year.get(year), by_year.get(year - 1)
            if not cur or not prev:
                continue
            pairs = [(prev[cik], cur[cik]) for cik in cur if cik in prev]  # (prev, cur) per issuer
            n_cont = len(pairs)
            if n_cont < self.min_pairs:
                continue
            switched = [(p, c) for p, c in pairs if p[0] != c[0]]
            rows.append(YearAggregate(year, inst, f"{sid}.change_rate",
                                      len(switched), n_cont, denom_source=DENOM_PCAOB_AUDITS))
            had_big4 = [(p, c) for p, c in pairs if is_big4(p[1])]
            if had_big4:
                down = sum(1 for _, c in had_big4 if not is_big4(c[1]))
                rows.append(YearAggregate(year, inst, f"{sid}.big4_to_nonbig4",
                                          down, len(had_big4), denom_source=DENOM_PCAOB_AUDITS))
            incoming = Counter(c[0] for _, c in switched if not is_big4(c[1]))
            nb_switched = sum(incoming.values())
            if nb_switched:
                top = sum(k for _, k in incoming.most_common(self.top_n))
                rows.append(YearAggregate(year, inst, f"{sid}.backstop_top{self.top_n}_share",
                                          top, nb_switched, denom_source=DENOM_PCAOB_AUDITS))
        rows.sort(key=lambda r: (r.signal_id, r.year))
        return rows


class AccrualExtractor:
    """Forensic-canon accrual signals from XBRL annual frames, aggregate only. Two surfaces:

    receivables_outrun: share of filers whose receivables growth outruns revenue growth by
      1.5x / 2x year over year (a days-sales-in-receivables index, the classic marker of
      booking sales customers are not paying for). Revenue is Revenues merged with
      RevenueFromContractWithCustomerExcludingAssessedTax (filers tag either).
    paper_earnings: share of filers with positive net income and negative operating cash
      flow (profit as an accounting opinion with no cash underneath).

    Per-CIK values stay in memory; only the yearly shares leave."""

    REV_CONCEPTS = ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax")

    def __init__(self, spec, min_filers=100):
        if spec.source != "xbrl" or spec.id not in ("receivables_outrun", "paper_earnings"):
            raise ValueError(f"{spec.id}: not an accrual surface")
        self.spec = spec
        self.min_filers = min_filers   # skip thin early-XBRL years

    def _revenue(self, client, year):
        merged = dict(client.xbrl_frames_duration(self.REV_CONCEPTS[1], year))
        for cik, v in client.xbrl_frames_duration(self.REV_CONCEPTS[0], year).items():
            merged.setdefault(cik, v)
        return merged

    def _row(self, year, label, n, base):
        return YearAggregate(int(year), self.spec.instrument, f"{self.spec.id}.{label}",
                             int(n), int(base), denom_source=DENOM_XBRL_JOIN)

    def signals(self, client, years):
        rows = []
        for year in years:
            if self.spec.id == "receivables_outrun":
                ar_c = client.xbrl_frames_instant("AccountsReceivableNetCurrent", year, unit="USD")
                ar_p = client.xbrl_frames_instant("AccountsReceivableNetCurrent", year - 1, unit="USD")
                rev_c = self._revenue(client, year)
                rev_p = self._revenue(client, year - 1)
                dsri = []
                for cik, a1 in ar_c.items():
                    a0, r1, r0 = ar_p.get(cik), rev_c.get(cik), rev_p.get(cik)
                    if all(v and v > 0 for v in (a0, a1, r0, r1)):
                        dsri.append((a1 / a0) / (r1 / r0))
                if len(dsri) < self.min_filers:
                    continue
                rows.append(self._row(year, "over_1_5x", sum(1 for d in dsri if d > 1.5), len(dsri)))
                rows.append(self._row(year, "over_2x", sum(1 for d in dsri if d > 2.0), len(dsri)))
            else:  # paper_earnings
                ni = client.xbrl_frames_duration("NetIncomeLoss", year)
                ocf = client.xbrl_frames_duration(
                    "NetCashProvidedByUsedInOperatingActivities", year)
                joined = [(ni[c], ocf[c]) for c in ni if c in ocf]
                if len(joined) < self.min_filers:
                    continue
                n = sum(1 for i, o in joined if i > 0 and o < 0)
                rows.append(self._row(year, "profit_no_cash", n, len(joined)))
        rows.sort(key=lambda r: (r.signal_id, r.year))
        return rows


def extractor_for(spec):
    """Return the extractor that drives a surface, by its source (and, where one source has
    several extraction shapes, by its id)."""
    if spec.source == "xbrl":
        if spec.id in ("receivables_outrun", "paper_earnings"):
            return AccrualExtractor(spec)
        return XbrlExtractor(spec)
    if spec.source == "pcaob":
        return AuditorChurnExtractor(spec) if spec.id == "auditor_churn" else PcaobExtractor(spec)
    return FtsExtractor(spec)  # source == "fts" (index source is a later phase)


def extractors_for(specs):
    """Build the right extractor for each surface (pass extractable() specs)."""
    return [extractor_for(s) for s in specs]
