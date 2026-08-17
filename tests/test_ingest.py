"""Tests for ariadne.ingest.tle."""

from ariadne.ingest.tle import parse_tle_text

_LINE1 = "1 25544U 98067A   24045.51782528  .00016717  00000-0  10270-3 0  9998"
_LINE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49560684436460"


def test_parses_bare_2line_record():
    tles = parse_tle_text(f"{_LINE1}\n{_LINE2}\n")
    assert len(tles) == 1
    assert tles[0].norad_id == 25544
    assert tles[0].name is None


def test_parses_named_3line_record():
    tles = parse_tle_text(f"ISS (ZARYA)\n{_LINE1}\n{_LINE2}\n")
    assert len(tles) == 1
    assert tles[0].name == "ISS (ZARYA)"


def test_parses_multiple_records_back_to_back():
    text = f"ISS (ZARYA)\n{_LINE1}\n{_LINE2}\n{_LINE1}\n{_LINE2}\n"
    tles = parse_tle_text(text)
    assert len(tles) == 2
    assert tles[0].name == "ISS (ZARYA)"
    assert tles[1].name is None
