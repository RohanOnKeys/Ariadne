"""Tests for ariadne.models.tle.

Reference TLE and decoded values are the ISS example from
docs/orbital-mechanics-and-estimation-primer.md section 3 (checksums
corrected, see that doc for the worked-by-hand numbers this checks
against).
"""

import math

import pytest

from ariadne.exceptions import TLEParseError
from ariadne.models.tle import TLE

_LINE1 = "1 25544U 98067A   24045.51782528  .00016717  00000-0  10270-3 0  9998"
_LINE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49560684436460"


def _iss_tle():
    return TLE.from_lines(_LINE1, _LINE2, name="ISS (ZARYA)")


def test_parses_norad_id_and_name():
    tle = _iss_tle()
    assert tle.norad_id == 25544
    assert tle.name == "ISS (ZARYA)"
    assert tle.classification == "U"
    assert tle.intl_designator == "98067A"


def test_parses_epoch_matching_primer_worked_example():
    tle = _iss_tle()
    assert tle.epoch.year == 2024
    assert tle.epoch.month == 2
    assert tle.epoch.day == 14
    # day 45.51782528 of 2024 -> 0.51782528 * 86400 s into the day
    seconds_into_day = 0.51782528 * 86400.0
    actual_seconds = (
        tle.epoch.hour * 3600 + tle.epoch.minute * 60
        + tle.epoch.second + tle.epoch.microsecond / 1e6
    )
    assert math.isclose(actual_seconds, seconds_into_day, abs_tol=1e-3)


def test_parses_keplerian_elements_matching_primer_table():
    tle = _iss_tle()
    assert math.isclose(math.degrees(tle.inclination), 51.6416, abs_tol=1e-4)
    assert math.isclose(math.degrees(tle.raan), 247.4627, abs_tol=1e-4)
    assert math.isclose(tle.eccentricity, 0.0006703, abs_tol=1e-7)
    assert math.isclose(math.degrees(tle.arg_perigee), 130.5360, abs_tol=1e-4)
    assert math.isclose(math.degrees(tle.mean_anomaly), 325.0288, abs_tol=1e-4)

    mean_motion_rev_per_day = tle.mean_motion * 86400.0 / (2 * math.pi)
    assert math.isclose(mean_motion_rev_per_day, 15.49560684, abs_tol=1e-8)


def test_parses_bstar_matching_primer_example():
    tle = _iss_tle()
    assert math.isclose(tle.bstar, 0.10270e-3, rel_tol=1e-9)


def test_parses_mean_motion_first_derivative():
    tle = _iss_tle()
    assert math.isclose(tle.mean_motion_dot, 0.00016717, rel_tol=1e-9)


def test_line1_and_line2_preserved_verbatim_for_sgp4():
    tle = _iss_tle()
    assert tle.line1 == _LINE1
    assert tle.line2 == _LINE2


def test_bad_checksum_raises_with_line_number():
    bad_line1 = _LINE1[:-1] + "0"  # corrupt the checksum digit
    with pytest.raises(TLEParseError, match="line 1"):
        TLE.from_lines(bad_line1, _LINE2)


def test_bad_checksum_on_line2_raises_with_line_number():
    bad_line2 = _LINE2[:-1] + "9"
    with pytest.raises(TLEParseError, match="line 2"):
        TLE.from_lines(_LINE1, bad_line2)


def test_wrong_length_raises():
    with pytest.raises(TLEParseError, match="line 1"):
        TLE.from_lines(_LINE1[:-5], _LINE2)


def test_wrong_line_number_marker_raises():
    swapped = "2" + _LINE1[1:]
    with pytest.raises(TLEParseError, match="line 1"):
        TLE.from_lines(swapped, _LINE2)


def test_mismatched_satellite_numbers_raises():
    other_sat_line2 = "2 00005" + _LINE2[7:]
    # recompute checksum for the mutated line so this fails on the
    # satellite-number check, not an incidental checksum mismatch
    body = other_sat_line2[:68]
    checksum = sum(int(c) if c.isdigit() else (1 if c == "-" else 0) for c in body) % 10
    other_sat_line2 = body + str(checksum)
    with pytest.raises(TLEParseError, match="mismatch"):
        TLE.from_lines(_LINE1, other_sat_line2)
