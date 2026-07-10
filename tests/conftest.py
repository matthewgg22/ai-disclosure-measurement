"""Shared test fixtures. A FakeClient replaces EdgarClient so tests run with no network."""
import pytest


class FakeClient:
    """Implements the methods extractors depend on, from preset dicts."""

    def __init__(self, counts, denom, frames=None):
        # counts: {(query, year, forms): n}; denom: {year: n_filers};
        # frames: {(concept, year): {cik: shares}}
        self._counts = counts
        self._denom = denom
        self._frames = frames or {}
        self.calls = []

    def fts_count(self, query, year, forms="10-K"):
        self.calls.append((query, year, forms))
        return self._counts.get((query, int(year), forms))

    def denominator(self, year):
        return self._denom.get(int(year))

    def xbrl_frames_instant(self, concept, year, unit="shares"):
        return self._frames.get((concept, int(year)), {})


@pytest.fixture
def fake_client():
    # Key the preset counts off the registry's current query strings so the fixture cannot
    # drift from the specs it tests.
    from screen.registry import by_id
    q_rev = by_id("dilution_reset").fts_queries["reverse_split"]
    q_gc = by_id("going_concern").fts_queries["going_concern"]
    q_mw = by_id("material_weakness").fts_queries["material_weakness"]
    q_nt = by_id("late_filing").fts_queries["nt_10k"]        # "" (empty = form count)
    q_r = by_id("restatement").fts_queries["item_4_02"]       # '"Item 4.02"' on 8-K
    counts = {
        (q_rev, 2024, "10-K"): 1675,
        (q_rev, 2025, "10-K"): 1500,
        (q_gc, 2024, "10-K"): 900,
        (q_gc, 2025, "10-K"): 800,
        (q_mw, 2024, "10-K"): 300,
        (q_mw, 2025, "10-K"): 280,
        (q_nt, 2024, "NT 10-K"): 978,   # late-filing form count (empty query, NT 10-K form)
        (q_nt, 2025, "NT 10-K"): 900,
        (q_r, 2024, "8-K"): 280,        # precise 8-K Item 4.02 restatement count
    }
    denom = {2024: 6768, 2025: 6558}
    return FakeClient(counts, denom)
