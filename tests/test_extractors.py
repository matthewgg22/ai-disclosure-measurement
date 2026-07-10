"""Extractors are pure functions of the client; drive them with the fake client."""
from screen.extractors import FtsExtractor, extractors_for
from screen.registry import by_id, extractable
from screen.signal import YearAggregate
import pytest


def test_fts_extractor_prevalence(fake_client):
    ex = FtsExtractor(by_id("dilution_reset"))
    rows = ex.signals(fake_client, [2024, 2025])
    assert all(isinstance(r, YearAggregate) for r in rows)
    r24 = next(r for r in rows if r.year == 2024)
    assert r24.signal_id == "dilution_reset.reverse_split"
    assert r24.n == 1675 and r24.n_filers == 6768
    assert r24.pct == round(100 * 1675 / 6768, 3)
    assert r24.instrument == "D"


def test_multi_signal_surface(fake_client):
    # going_concern + material_weakness are separate surfaces, both group B
    rows = []
    for sid in ("going_concern", "material_weakness"):
        rows += FtsExtractor(by_id(sid)).signals(fake_client, [2024])
    labels = {r.signal_id for r in rows}
    assert labels == {"going_concern.going_concern", "material_weakness.material_weakness"}


def test_missing_denominator_year_skipped(fake_client):
    # 2099 has no denominator -> no rows, no crash
    rows = FtsExtractor(by_id("dilution_reset")).signals(fake_client, [2099])
    assert rows == []


def test_none_count_skipped(fake_client):
    # a query the fake client doesn't know returns None -> that sub-signal is skipped
    rows = FtsExtractor(by_id("going_concern")).signals(fake_client, [2099, 2024])
    assert all(r.year == 2024 for r in rows)


def test_non_extractable_surface_rejected():
    with pytest.raises(ValueError):
        FtsExtractor(by_id("insider_no_skin"))  # no fts_queries


def test_extractors_for_only_builds_extractable():
    exs = extractors_for(extractable())
    assert len(exs) == len(extractable())
    assert all(e.spec.fts_queries for e in exs)
