"""EdgarClient: cache behavior and the committed denominator, both without network."""
import json

from screen.edgar import EdgarClient


def test_cache_hit_returns_without_network(tmp_path):
    cache = tmp_path / "c.json"
    key = "10-K|2024|\"pre-funded warrant\""
    cache.write_text(json.dumps({key: 477}))
    client = EdgarClient("test@example.com", cache_path=str(cache))
    # value is served from cache; no network call is made
    assert client.fts_count('"pre-funded warrant"', 2024, forms="10-K") == 477


def test_denominator_reads_committed_aggregate(tmp_path):
    # uses the real committed data/aggregates/ai_prevalence.csv
    client = EdgarClient("test@example.com", cache_path=str(tmp_path / "c.json"))
    assert client.denominator(2025) == 6558
    assert client.denominator(2001) == 6180
    assert client.denominator(1999) is None
