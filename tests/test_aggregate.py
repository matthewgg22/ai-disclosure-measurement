"""run_all + to_csv: end-to-end over the fake client, no network."""
import csv

from screen import aggregate
from screen.extractors import FtsExtractor
from screen.registry import by_id


def test_run_all_sorted_and_gated(fake_client):
    exs = [FtsExtractor(by_id("dilution_reset")), FtsExtractor(by_id("going_concern"))]
    rows = aggregate.run_all(fake_client, exs, [2025, 2024])
    # sorted by (signal_id, year)
    keys = [(r.signal_id, r.year) for r in rows]
    assert keys == sorted(keys)


def test_to_csv_roundtrip(fake_client, tmp_path):
    exs = [FtsExtractor(by_id("dilution_reset"))]
    rows = aggregate.run_all(fake_client, exs, [2024, 2025])
    out = tmp_path / "screen_registry.csv"
    aggregate.to_csv(rows, str(out))
    got = list(csv.DictReader(open(out)))
    assert got[0]["signal_id"] == "dilution_reset.reverse_split"
    assert set(got[0]) == set(aggregate.HEADER)
    assert int(got[0]["n"]) == 1675
