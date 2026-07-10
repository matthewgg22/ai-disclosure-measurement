"""The registry is the breadth; these tests keep it well-formed."""
from screen.registry import REGISTRY, extractable, by_id
from screen.signal import INSTRUMENTS, SurfaceSpec
import pytest


def test_ids_unique():
    ids = [s.id for s in REGISTRY]
    assert len(ids) == len(set(ids)), "duplicate surface ids"


def test_every_spec_valid_instrument_and_citation():
    for s in REGISTRY:
        assert s.instrument in INSTRUMENTS, f"{s.id}: bad instrument"
        assert s.citation.strip(), f"{s.id}: empty citation"
        assert s.description.strip(), f"{s.id}: empty description"


def test_all_six_instruments_covered():
    covered = {s.instrument for s in REGISTRY}
    assert covered == set(INSTRUMENTS), f"missing instruments: {set(INSTRUMENTS) - covered}"


def test_extractable_have_queries():
    for s in extractable():
        assert s.fts_queries, f"{s.id} in extractable() but has no queries"
    # and at least the extraction instrument is extractable now
    assert any(s.id == "sec16_evasion" for s in extractable())


def test_bad_instrument_rejected():
    with pytest.raises(ValueError):
        SurfaceSpec(id="x", instrument="Z", citation="c", description="d", fts_queries={})


def test_by_id_roundtrip_and_miss():
    assert by_id("sec16_evasion").instrument == "A"
    with pytest.raises(KeyError):
        by_id("does_not_exist")
