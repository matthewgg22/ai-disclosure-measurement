"""PCAOB auditor-market extractor + Big-4 classification, offline."""
from conftest import FakePcaobClient
from screen.extractors import PcaobExtractor, extractor_for
from screen.pcaob import is_big4
from screen.registry import by_id
from screen.signal import DENOM_PCAOB_AUDITS, YearAggregate
import pytest


def test_is_big4():
    assert is_big4("Deloitte & Touche LLP")
    assert is_big4("KPMG LLP")
    assert is_big4("Ernst & Young LLP")
    assert is_big4("PricewaterhouseCoopers LLP")
    assert not is_big4("Marcum LLP")
    assert not is_big4("BF Borgers CPA PC")
    assert not is_big4("")


def _client():
    # 2023: 6 issuer-audits; ciks 1,2 Big-4; 3,4,5 by SmallFirm A; 6 by SmallFirm B
    recs = [
        (2023, "Deloitte & Touche LLP", 1, "Issuer"),
        (2023, "KPMG LLP", 2, "Issuer"),
        (2023, "SmallFirm A", 3, "Issuer"),
        (2023, "SmallFirm A", 4, "Issuer"),
        (2023, "SmallFirm A", 5, "Issuer"),
        (2023, "SmallFirm B", 6, "Issuer"),
    ]
    return FakePcaobClient(recs)


def test_nonbig4_share_and_concentration():
    ex = PcaobExtractor(by_id("auditor_market"), min_audits=1, top_n=1)
    rows = ex.signals(_client(), [2023])
    by_sig = {r.signal_id: r for r in rows}
    nb = by_sig["auditor_market.nonbig4_share"]
    assert nb.n == 4 and nb.n_filers == 6          # 4 of 6 audits are non-Big-4
    assert nb.denom_source == DENOM_PCAOB_AUDITS
    top1 = by_sig["auditor_market.top1_nonbig4_share"]
    assert top1.n == 3 and top1.n_filers == 4      # busiest small firm (A) did 3 of 4 non-Big-4
    assert isinstance(rows[0], YearAggregate) and rows[0].instrument == "C"


def test_min_audits_guard_and_year_filter():
    ex = PcaobExtractor(by_id("auditor_market"), min_audits=100)  # 6 < 100 -> skip
    assert ex.signals(_client(), [2023]) == []
    ex2 = PcaobExtractor(by_id("auditor_market"), min_audits=1)
    assert ex2.signals(_client(), [1999]) == []    # year not present


def test_dedup_one_auditor_per_issuer_year():
    # same issuer twice in a year -> counted once (last wins)
    recs = [(2023, "SmallFirm A", 9, "Issuer"), (2023, "SmallFirm B", 9, "Issuer"),
            (2023, "Deloitte LLP", 8, "Issuer")]
    ex = PcaobExtractor(by_id("auditor_market"), min_audits=1)
    rows = ex.signals(FakePcaobClient(recs), [2023])
    nb = next(r for r in rows if r.signal_id == "auditor_market.nonbig4_share")
    assert nb.n_filers == 2   # two distinct issuers (cik 9 deduped), not three


def test_factory_picks_pcaob():
    assert isinstance(extractor_for(by_id("auditor_market")), PcaobExtractor)
