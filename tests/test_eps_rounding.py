"""EPS-rounding (quadrophobia) extractor: digit math + aggregation, offline."""
from conftest import FakeClient
from screen.extractors import EpsRoundingExtractor, extractor_for
from screen.registry import by_id
from screen.signal import DENOM_XBRL_QTR
import pytest


def test_tenth_of_cent_digit():
    d = EpsRoundingExtractor.tenth_of_cent_digit
    # NI 234,500 / 1,000,000 shares -> $0.2345 -> 23.45 cents -> digit 4
    assert d(234_500, 1_000_000) == 4
    # 23.55 cents -> digit 5
    assert d(235_500, 1_000_000) == 5
    # 23.40 cents exactly -> digit 4 (floor semantics)
    assert d(234_000, 1_000_000) == 4
    # sub-cent EPS is degenerate -> excluded
    assert d(5_000, 1_000_000) is None
    # losses and unusable inputs -> excluded
    assert d(-234_500, 1_000_000) is None
    assert d(234_500, 0) is None
    assert d(None, 1_000_000) is None


def _client():
    # 2024 Q1 only: ciks 1,2 digit-4; cik 3 digit-5; cik 4 sub-cent (excluded);
    # cik 5 has NI but no share count (excluded from join).
    ni = {1: 234_500, 2: 114_200, 3: 235_500, 4: 5_000, 5: 999_999}
    dil = {1: 1_000_000, 3: 1_000_000, 4: 1_000_000}
    basic = {2: 1_000_000}   # cik 2 only tags basic shares -> merge must catch it
    frames_duration = {
        ("NetIncomeLoss", 2024, 1): ni,
        ("WeightedAverageNumberOfDilutedSharesOutstanding", 2024, 1): dil,
        ("WeightedAverageNumberOfSharesOutstandingBasic", 2024, 1): basic,
    }
    return FakeClient({}, {}, frames_duration=frames_duration)


def test_digit4_share_aggregation():
    ex = EpsRoundingExtractor(by_id("eps_rounding"), min_obs=1)
    rows = ex.signals(_client(), [2024])
    assert len(rows) == 1
    r = rows[0]
    assert r.signal_id == "eps_rounding.digit4_share"
    # joined, >= 1 cent observations: ciks 1 (23.45 -> 4), 2 (11.42 -> 4), 3 (23.55 -> 5)
    assert r.n == 2 and r.n_filers == 3
    assert r.denom_source == DENOM_XBRL_QTR
    assert r.instrument == "B"


def test_min_obs_guard_and_dispatch():
    ex = EpsRoundingExtractor(by_id("eps_rounding"), min_obs=100)
    assert ex.signals(_client(), [2024]) == []      # 3 obs < 100
    assert isinstance(extractor_for(by_id("eps_rounding")), EpsRoundingExtractor)
    with pytest.raises(ValueError):
        EpsRoundingExtractor(by_id("paper_earnings"))
