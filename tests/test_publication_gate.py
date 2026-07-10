"""The gate must let aggregates through and block anything issuer-level."""
from dataclasses import dataclass

from screen import publication_gate as gate
from screen.signal import YearAggregate
import pytest


def test_aggregate_rows_pass():
    rows = [YearAggregate(2024, "D", "dilution_reset.reverse_split", 100, 6768)]
    assert gate.assert_rows_safe(rows) is True


def test_header_aggregate_passes():
    assert gate.assert_header_safe(["year", "instrument", "signal_id", "n", "n_filers", "pct"]) is True


def test_header_with_issuer_column_blocked():
    with pytest.raises(gate.PublicationError):
        gate.assert_header_safe(["year", "cik", "signal_id"])


def test_header_with_unexpected_column_blocked():
    with pytest.raises(gate.PublicationError):
        gate.assert_header_safe(["year", "signal_id", "secret_score"])


def test_issuer_level_row_blocked():
    @dataclass
    class IssuerRow:
        year: int
        cik: int
        signal_id: str

    with pytest.raises(gate.PublicationError):
        gate.assert_rows_safe([IssuerRow(2024, 320193, "x")])
