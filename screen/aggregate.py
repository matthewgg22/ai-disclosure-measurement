"""Run the extractors and write the aggregate CSV, through the publication gate."""
import csv
import os

from . import publication_gate as gate

HEADER = ["year", "instrument", "signal_id", "n", "n_filers", "pct"]


def run_all(client, extractors, years):
    """Collect YearAggregate rows from every extractor, sorted for stable output."""
    rows = []
    for ex in extractors:
        rows.extend(ex.signals(client, years))
    rows.sort(key=lambda r: (r.signal_id, r.year))
    gate.assert_rows_safe(rows)
    return rows


def to_csv(rows, path):
    """Write aggregate rows to CSV. The header passes the publication gate first."""
    gate.assert_header_safe(HEADER)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for r in rows:
            w.writerow([r.year, r.instrument, r.signal_id, r.n, r.n_filers, r.pct])
    return path
