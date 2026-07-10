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
from .registry import extractable

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(_ROOT, "data", "aggregates", "screen_registry.csv")
YEARS = range(2001, 2026)


def main():
    contact = sys.argv[1] if len(sys.argv) > 1 else "matthewgreergentis@gmail.com"
    client = EdgarClient(contact)
    specs = extractable()
    extractors = extractors_for(specs)
    print(f"[screen] {len(specs)} extractable surfaces, {sum(len(s.fts_queries) for s in specs)} sub-signals")
    rows = aggregate.run_all(client, extractors, list(YEARS))
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
    # Loud on fetch failures: a transient EDGAR error must not silently become a data gap.
    if client.failures:
        print(f"\n[WARN] {len(client.failures)} fetch(es) failed after retries (data gaps):")
        for kind, key in client.failures[:20]:
            print(f"    {kind}: {key}")
        sys.exit(1)


if __name__ == "__main__":
    main()
