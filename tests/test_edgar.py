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


def test_fts_count_flags_10k_cap_truncation(tmp_path, monkeypatch):
    """A response with Elasticsearch relation 'gte' (count capped at 10,000) is recorded as a
    floor in .truncated, not silently reported as exact."""
    import io
    client = EdgarClient("test@example.com", cache_path=str(tmp_path / "c.json"))

    def fake_capped(_req, timeout=0):
        body = json.dumps({"hits": {"total": {"value": 10000, "relation": "gte"}}})
        return io.BytesIO(body.encode())

    monkeypatch.setattr("screen.edgar.urllib.request.urlopen", fake_capped)
    n = client.fts_count('"very common phrase"', 2025, forms="10-K")
    assert n == 10000                       # the floor value is still returned
    assert len(client.truncated) == 1       # but the truncation is surfaced

    def fake_exact(_req, timeout=0):
        body = json.dumps({"hits": {"total": {"value": 42, "relation": "eq"}}})
        return io.BytesIO(body.encode())

    monkeypatch.setattr("screen.edgar.urllib.request.urlopen", fake_exact)
    assert client.fts_count('"rare phrase"', 2025, forms="10-K") == 42
    assert len(client.truncated) == 1       # an exact count adds nothing to .truncated
