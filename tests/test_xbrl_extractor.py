"""XbrlExtractor: the Q4 instant-frame intersection join and threshold counts, offline."""
from conftest import FakeClient
from screen.extractors import XbrlExtractor, extractor_for, extractors_for
from screen.registry import by_id, extractable
from screen.signal import YearAggregate
import pytest

CONCEPT = "dei:EntityCommonStockSharesOutstanding"


def _client():
    # year 2023 vs 2024 share counts, by cik:
    #  cik 1: 100 -> 250   (2.5x, over 2x, not 5x)
    #  cik 2: 100 -> 600   (6x,   over 5x, not 10x)
    #  cik 3: 100 -> 1500  (15x,  over 10x)
    #  cik 4: 100 -> 120   (flat, over none)
    #  cik 5: only in 2024 (dropped, no prior)
    #  cik 6: prior 0 (dropped)
    frames = {
        (CONCEPT, 2023): {1: 100, 2: 100, 3: 100, 4: 100, 6: 0},
        (CONCEPT, 2024): {1: 250, 2: 600, 3: 1500, 4: 120, 5: 999, 6: 50},
    }
    return FakeClient(counts={}, denom={2024: 6768}, frames=frames)


def test_threshold_counts_on_intersection():
    ex = XbrlExtractor(by_id("share_explosion"), min_filers=1)
    rows = ex.signals(_client(), [2024])
    by_sig = {r.signal_id: r for r in rows}
    # intersection with both > 0 is ciks 1..4 => n_filers = 4
    assert all(r.n_filers == 4 for r in rows)
    assert by_sig["share_explosion.pct_over_2x"].n == 3   # ciks 1,2,3
    assert by_sig["share_explosion.pct_over_5x"].n == 2   # ciks 2,3
    assert by_sig["share_explosion.pct_over_10x"].n == 1  # cik 3
    assert isinstance(rows[0], YearAggregate)
    assert rows[0].instrument == "D"


def test_pct_property():
    ex = XbrlExtractor(by_id("share_explosion"), min_filers=1)
    rows = ex.signals(_client(), [2024])
    r2 = next(r for r in rows if r.signal_id == "share_explosion.pct_over_2x")
    assert r2.pct == round(100 * 3 / 4, 3)


def test_missing_year_skipped():
    ex = XbrlExtractor(by_id("share_explosion"), min_filers=1)
    # 2099 has no frame -> prev/cur empty -> no rows, no crash
    assert ex.signals(_client(), [2099]) == []


def test_factory_and_extractors_for_pick_xbrl():
    assert isinstance(extractor_for(by_id("share_explosion")), XbrlExtractor)
    kinds = {type(e).__name__ for e in extractors_for(extractable())}
    assert "XbrlExtractor" in kinds and "FtsExtractor" in kinds


def test_non_xbrl_rejected():
    with pytest.raises(ValueError):
        XbrlExtractor(by_id("dilution_reset"))  # source="fts"
