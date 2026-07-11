"""Forensic-canon accrual extractors (receivables_outrun, paper_earnings), offline."""
from conftest import FakeClient
from screen.extractors import AccrualExtractor, XbrlExtractor, extractor_for
from screen.registry import by_id
from screen.signal import DENOM_XBRL_JOIN
import pytest


def _receivables_client():
    # cik 1: AR 100->300 (3x), rev 100->120 (1.2x) -> dsri 2.5 (trips both cuts)
    # cik 2: AR 100->170 (1.7x), rev 100->100 (1x) -> dsri 1.7 (trips 1.5x only)
    # cik 3: AR 100->110, rev 100->120 -> dsri ~0.92 (clean)
    # cik 4: missing prior-year revenue -> excluded from the join
    frames = {
        ("AccountsReceivableNetCurrent", 2024): {1: 300, 2: 170, 3: 110, 4: 500},
        ("AccountsReceivableNetCurrent", 2023): {1: 100, 2: 100, 3: 100, 4: 400},
    }
    frames_duration = {
        ("RevenueFromContractWithCustomerExcludingAssessedTax", 2024): {1: 120, 2: 100},
        ("RevenueFromContractWithCustomerExcludingAssessedTax", 2023): {1: 100, 2: 100},
        ("Revenues", 2024): {3: 120, 4: 100},
        ("Revenues", 2023): {3: 100},          # cik 4 has no 2023 revenue
    }
    return FakeClient({}, {}, frames=frames, frames_duration=frames_duration)


def test_receivables_outrun_dsri():
    ex = AccrualExtractor(by_id("receivables_outrun"), min_filers=1)
    rows = {r.signal_id: r for r in ex.signals(_receivables_client(), [2024])}
    r15 = rows["receivables_outrun.over_1_5x"]
    assert r15.n == 2 and r15.n_filers == 3      # ciks 1,2 trip; cik 4 excluded from join
    assert r15.denom_source == DENOM_XBRL_JOIN
    r20 = rows["receivables_outrun.over_2x"]
    assert r20.n == 1                            # only cik 1's dsri 2.5 > 2.0


def test_revenue_concepts_merged():
    # cik 3 is tagged under Revenues, ciks 1-2 under RevenueFromContractWithCustomer...:
    # the join must see all three (n_filers == 3 above proves the merge).
    ex = AccrualExtractor(by_id("receivables_outrun"), min_filers=4)
    assert ex.signals(_receivables_client(), [2024]) == []   # 3 joined < min_filers guard


def test_paper_earnings():
    frames_duration = {
        ("NetIncomeLoss", 2024): {1: 50, 2: 10, 3: -5, 4: 30},
        ("NetCashProvidedByUsedInOperatingActivities", 2024): {1: -20, 2: 15, 3: -9},
        # cik 4 has no OCF -> excluded from the join
    }
    client = FakeClient({}, {}, frames_duration=frames_duration)
    ex = AccrualExtractor(by_id("paper_earnings"), min_filers=1)
    rows = ex.signals(client, [2024])
    r = rows[0]
    assert r.signal_id == "paper_earnings.profit_no_cash"
    assert r.n == 1 and r.n_filers == 3          # only cik 1: NI>0 and OCF<0
    assert r.instrument == "B"


def test_factory_dispatch():
    assert isinstance(extractor_for(by_id("receivables_outrun")), AccrualExtractor)
    assert isinstance(extractor_for(by_id("paper_earnings")), AccrualExtractor)
    assert isinstance(extractor_for(by_id("share_explosion")), XbrlExtractor)  # unchanged


def test_rejects_wrong_surface():
    with pytest.raises(ValueError):
        AccrualExtractor(by_id("share_explosion"))
