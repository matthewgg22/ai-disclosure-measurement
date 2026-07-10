"""Tests for the hardening pass: denom_source honesty, min_filers guard, loud-failure
plumbing. All offline."""
from conftest import FakeClient
from screen.extractors import FtsExtractor, XbrlExtractor
from screen.registry import by_id
from screen.signal import (YearAggregate, DENOM_10K_FILERS, DENOM_FILING_OVER_10K,
                           DENOM_XBRL_Q4)
import pytest

CONCEPT = "dei:EntityCommonStockSharesOutstanding"


def test_denom_source_by_signal_kind(fake_client):
    # a 10-K phrase => 10k_filers; a non-10-K form (NT 10-K) => filing_count_over_10k
    rev = FtsExtractor(by_id("dilution_reset")).signals(fake_client, [2024])[0]
    assert rev.denom_source == DENOM_10K_FILERS
    nt = FtsExtractor(by_id("late_filing")).signals(fake_client, [2024])[0]
    assert nt.denom_source == DENOM_FILING_OVER_10K


def test_share_explosion_denom_source():
    frames = {(CONCEPT, 2023): {i: 100 for i in range(200)},
              (CONCEPT, 2024): {i: 100 * (1 + i % 12) for i in range(200)}}
    client = FakeClient(counts={}, denom={2024: 6768}, frames=frames)
    rows = XbrlExtractor(by_id("share_explosion")).signals(client, [2024])
    assert rows and all(r.denom_source == DENOM_XBRL_Q4 for r in rows)


def test_min_filers_default_skips_tiny_intersection():
    # only 4 firms in the intersection; the default min_filers (100) must skip the year
    frames = {(CONCEPT, 2023): {1: 100, 2: 100, 3: 100, 4: 100},
              (CONCEPT, 2024): {1: 250, 2: 600, 3: 1500, 4: 120}}
    client = FakeClient(counts={}, denom={2024: 6768}, frames=frames)
    assert XbrlExtractor(by_id("share_explosion")).signals(client, [2024]) == []
    # but with the guard relaxed, it produces rows
    assert XbrlExtractor(by_id("share_explosion"), min_filers=1).signals(client, [2024])


def test_bad_denom_source_rejected():
    with pytest.raises(ValueError):
        YearAggregate(2024, "D", "x.y", 1, 10, denom_source="made_up")


def test_edgar_client_tracks_failures_attribute():
    from screen.edgar import EdgarClient
    c = EdgarClient("t@example.com", cache_path="/tmp/_screen_test_cache.json")
    assert c.failures == []   # starts empty; run.py exits non-zero if it fills
