"""Tests for ariadne.ingest.schema."""

import pytest

from ariadne.exceptions import IngestError
from ariadne.ingest.schema import resolve_header, validate_required_fields


def test_resolve_header_matches_canonical_names():
    resolved = resolve_header(["epoch", "x", "y", "z", "vx", "vy", "vz"])
    assert resolved == {"epoch": 0, "x": 1, "y": 2, "z": 3, "vx": 4, "vy": 5, "vz": 6}


def test_resolve_header_matches_aliases_case_insensitively():
    resolved = resolve_header(["Time", "X_KM", "Y_KM", "Z_KM", "VX", "VY", "VZ", "SATNUM"])
    assert resolved["epoch"] == 0
    assert resolved["x"] == 1
    assert resolved["norad_id"] == 7


def test_resolve_header_ignores_unrecognized_columns():
    resolved = resolve_header(["epoch", "mystery_column"])
    assert resolved == {"epoch": 0}


def test_validate_required_fields_passes_when_all_present():
    resolved = {f: i for i, f in enumerate(["epoch", "x", "y", "z", "vx", "vy", "vz"])}
    validate_required_fields(resolved)  # must not raise


def test_validate_required_fields_raises_on_missing_columns():
    resolved = {"epoch": 0, "x": 1}
    with pytest.raises(IngestError, match="y, z, vx, vy, vz"):
        validate_required_fields(resolved)
