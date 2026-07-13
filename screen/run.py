#!/usr/bin/env python3
# Usage: python3 -m screen.run [contact_email]   # writes data/aggregates/screen_registry.csv
"""Run the regulatory-surface screen over the extractable registry and write the aggregate CSV.

This is the engine's entry point. It reads the 10-K denominator from the committed aggregate,
runs every FTS-extractable surface, passes the rows through the publication gate, and writes
per-year prevalence for each regulatory-surface sub-signal. Output is aggregate only.
"""
import os
import sys

from . import aggregate
from .edgar import EdgarClient
from .extractors import extractors_for
from .pcaob import PcaobClient
from .registry import extractable

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(_ROOT, "data", "aggregates", "screen_registry.csv")
YEARS = range(2001, 2026)


def main():
    # SEC fair access requires a real contact in the User-Agent. Take it from argv or the
    # SEC_CONTACT env var; never fall back to a hard-coded address, so a fork identifies itself.
    contact = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SEC_CONTACT")
    if not contact:
        sys.exit("Provide an SEC contact email: `python -m screen.run you@example.com` "
                 "(or set SEC_CONTACT). The SEC requires a real contact in the request User-Agent.")
    edgar, pcaob = EdgarClient(contact), PcaobClient(contact)
    clients = {"fts": edgar, "xbrl": edgar, "pcaob": pcaob}
    specs = extractable()
    extractors = extractors_for(specs)
    print(f"[screen] {len(specs)} extractable surfaces across sources {sorted({s.source for s in specs})}")
    rows = aggregate.run_all(clients, extractors, list(YEARS))
    aggregate.to_csv(rows, OUT)
    # per-surface summary at each surface's most recent year that actually has data
    for s in specs:
        s_rows = [r for r in rows if r.signal_id.startswith(s.id + ".")]
        if not s_rows:
            print(f"  [{s.instrument}] {s.id}: (no data)")
            continue
        latest = max(r.year for r in s_rows)
        vals = [r for r in s_rows if r.year == latest]
        summary = "  ".join(f"{r.signal_id.split('.')[1]}={r.pct}%" for r in vals)
        print(f"  [{s.instrument}] {s.id} ({latest}): {summary}")
    print(f"[done] {len(rows)} rows -> {os.path.relpath(OUT, _ROOT)}")
    # Loud on count truncation: a query over EDGAR's 10k cap is a floor, not an exact count.
    if edgar.truncated:
        print(f"\n[WARN] {len(edgar.truncated)} FTS count(s) hit EDGAR's 10,000 cap (reported as a "
              f"floor, not exact): {edgar.truncated[:5]}")
    # Loud on fetch failures: a transient error must not silently become a data gap.
    failures = edgar.failures + pcaob.failures
    if failures:
        print(f"\n[WARN] {len(failures)} fetch(es) failed after retries (data gaps):")
        for kind, key in failures[:20]:
            print(f"    {kind}: {key}")
        sys.exit(1)


if __name__ == "__main__":
    main()
