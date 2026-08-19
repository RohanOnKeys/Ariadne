"""Tests for ariadne.ingest.sniff."""

import pytest

from ariadne.exceptions import IngestError
from ariadne.ingest.sniff import IngestFormat, load_file, sniff_format
from ariadne.models.state_vector import SatelliteState
from ariadne.models.tle import TLE

_LINE1 = "1 25544U 98067A   24045.51782528  .00016717  00000-0  10270-3 0  9998"
_LINE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49560684436460"


def test_sniffs_bare_tle():
    assert sniff_format(f"{_LINE1}\n{_LINE2}\n") is IngestFormat.TLE


def test_sniffs_named_tle():
    assert sniff_format(f"ISS (ZARYA)\n{_LINE1}\n{_LINE2}\n") is IngestFormat.TLE


def test_sniffs_csv():
    text = "epoch,x,y,z,vx,vy,vz\n2026-01-01T00:00:00Z,7000,0,0,0,7.5,0\n"
    assert sniff_format(text) is IngestFormat.CSV


def test_sniffs_txt():
    text = "2026-01-01T00:00:00Z 7000 0 0 0 7.5 0\n"
    assert sniff_format(text) is IngestFormat.TXT


def test_sniff_empty_text_raises_ingest_error():
    with pytest.raises(IngestError):
        sniff_format("   \n\n")


def test_load_file_dispatches_to_tle_parser(tmp_path):
    path = tmp_path / "sat.tle"
    path.write_text(f"ISS (ZARYA)\n{_LINE1}\n{_LINE2}\n")

    records, warnings = load_file(path)

    assert warnings == []
    assert len(records) == 1
    assert isinstance(records[0], TLE)


def test_load_file_dispatches_to_csv_parser(tmp_path):
    path = tmp_path / "states.csv"
    path.write_text("epoch,x,y,z,vx,vy,vz\n2026-01-01T00:00:00Z,7000,0,0,0,7.5,0\n")

    records, warnings = load_file(path)

    assert warnings == []
    assert len(records) == 1
    assert isinstance(records[0], SatelliteState)


def test_load_file_dispatches_to_txt_parser(tmp_path):
    path = tmp_path / "states.txt"
    path.write_text("2026-01-01T00:00:00Z 7000 0 0 0 7.5 0\n")

    records, warnings = load_file(path)

    assert warnings == []
    assert len(records) == 1
    assert isinstance(records[0], SatelliteState)
