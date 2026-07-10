"""The publication gate: the one place aggregate results become public output.

It refuses to emit anything issuer-level. YearAggregate rows are issuer-free by construction,
but the gate re-checks the emitted CSV header against a denylist of issuer-identifying columns
and asserts the shape is per-year aggregate, so a future extractor cannot accidentally leak an
issuer column into data/aggregates/. This complements scripts/check_public_safe.py, which
runs the same idea as a repo-wide pre-commit gate.
"""

FORBIDDEN_COLS = {
    "cik", "cik_str", "ticker", "tickers", "cusip", "isin", "lei",
    "name", "company", "companyname", "issuer", "issuername",
    "accession", "accession_no", "accessionnumber", "filer",
}
ALLOWED_COLS = {"year", "instrument", "signal_id", "n", "n_filers", "pct"}


class PublicationError(Exception):
    pass


def assert_rows_safe(rows):
    """Every row must be a YearAggregate-shaped object with no issuer identity."""
    for r in rows:
        fields = set(getattr(r, "__dataclass_fields__", {}) or {})
        bad = fields & FORBIDDEN_COLS
        if bad:
            raise PublicationError(f"issuer-level field(s) on output row: {sorted(bad)}")
    return True


def assert_header_safe(header):
    """The emitted CSV header may only contain aggregate columns."""
    cols = {c.strip().lower() for c in header}
    bad = cols & FORBIDDEN_COLS
    if bad:
        raise PublicationError(f"issuer-level column(s) in output: {sorted(bad)}")
    extra = cols - ALLOWED_COLS
    if extra:
        raise PublicationError(f"unexpected column(s) in aggregate output: {sorted(extra)}")
    return True
