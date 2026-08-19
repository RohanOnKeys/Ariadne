"""Tests for ariadne.ingest.csv."""

import pytest

from ariadne.exceptions import IngestError
from ariadne.ingest.csv import parse_csv_text
from ariadne.models.state_vector import Frame


def test_parses_required_columns_only():
    text = "epoch,x,y,z,vx,vy,vz\n2026-01-01T00:00:00Z,7000,0,0,0,7.5,0\n"
    states, warnings = parse_csv_text(text)

    assert warnings == []
    assert len(states) == 1
    assert states[0].position.tolist() == [7000.0, 0.0, 0.0]
    assert states[0].velocity.tolist() == [0.0, 7.5, 0.0]
    assert states[0].frame == Frame.ECI
    assert states[0].norad_id is None
    assert states[0].name is None


def test_column_order_does_not_matter():
    text = "vz,vy,vx,z,y,x,epoch\n0,7.5,0,0,0,7000,2026-01-01T00:00:00Z\n"
    states, warnings = parse_csv_text(text)

    assert warnings == []
    assert states[0].position.tolist() == [7000.0, 0.0, 0.0]


def test_parses_optional_norad_id_name_and_frame():
    text = "epoch,x,y,z,vx,vy,vz,norad_id,name,frame\n"
    text += "2026-01-01T00:00:00Z,7000,0,0,0,7.5,0,25544,ISS (ZARYA),ecef\n"
    states, warnings = parse_csv_text(text)

    assert warnings == []
    assert states[0].norad_id == 25544
    assert states[0].name == "ISS (ZARYA)"
    assert states[0].frame == Frame.ECEF


def test_accepts_header_alias_spellings():
    text = "datetime,x_km,y_km,z_km,vx_km_s,vy_km_s,vz_km_s\n"
    text += "2026-01-01T00:00:00Z,7000,0,0,0,7.5,0\n"
    states, warnings = parse_csv_text(text)

    assert warnings == []
    assert len(states) == 1


def test_missing_required_column_raises_ingest_error():
    text = "epoch,x,y,z,vx,vy\n2026-01-01T00:00:00Z,7000,0,0,0,7.5\n"
    with pytest.raises(IngestError, match="vz"):
        parse_csv_text(text)


def test_malformed_row_is_collected_as_a_warning_not_raised():
    text = "epoch,x,y,z,vx,vy,vz\n"
    text += "2026-01-01T00:00:00Z,7000,0,0,0,7.5,0\n"
    text += "not-a-date,7000,0,0,0,7.5,0\n"
    text += "2026-01-01T00:01:00Z,7001,0,0,0,7.4,0\n"

    states, warnings = parse_csv_text(text)

    assert len(states) == 2
    assert len(warnings) == 1
    assert "line 3" in warnings[0]


def test_naive_epoch_is_rejected():
    text = "epoch,x,y,z,vx,vy,vz\n2026-01-01T00:00:00,7000,0,0,0,7.5,0\n"
    states, warnings = parse_csv_text(text)

    assert states == []
    assert "naive" in warnings[0]


def test_blank_rows_are_skipped_silently():
    text = "epoch,x,y,z,vx,vy,vz\n\n2026-01-01T00:00:00Z,7000,0,0,0,7.5,0\n\n"
    states, warnings = parse_csv_text(text)

    assert len(states) == 1
    assert warnings == []


def test_empty_text_raises_ingest_error():
    with pytest.raises(IngestError):
        parse_csv_text("")
