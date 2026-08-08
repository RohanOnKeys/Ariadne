"""Tests for ariadne.utils.time."""

import math
from datetime import datetime, timezone

from ariadne.constants import JD_J2000
from ariadne.utils.time import (
    datetime_to_jd,
    jd_to_datetime,
    gmst_from_jd,
    tle_epoch_to_datetime,
)


def test_datetime_to_jd_at_j2000_epoch():
    """2000-01-01 12:00:00 UTC is the J2000.0 epoch, JD 2451545.0 by
    definition; ariadne.constants.JD_J2000 should agree exactly."""
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert datetime_to_jd(dt) == JD_J2000


def test_datetime_to_jd_at_midnight_2000():
    """JD for 2000-01-01 00:00:00 UTC is the well-known 2451544.5."""
    dt = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert math.isclose(datetime_to_jd(dt), 2451544.5, abs_tol=1e-9)


def test_jd_to_datetime_round_trips():
    """jd_to_datetime should invert datetime_to_jd to within a
    microsecond, across an arbitrary non-epoch timestamp."""
    dt = datetime(2024, 3, 17, 6, 42, 13, 123456, tzinfo=timezone.utc)
    jd = datetime_to_jd(dt)
    recovered = jd_to_datetime(jd)

    assert recovered.year == dt.year
    assert recovered.month == dt.month
    assert recovered.day == dt.day
    assert recovered.hour == dt.hour
    assert recovered.minute == dt.minute
    assert abs((recovered - dt).total_seconds()) < 1e-3


def test_gmst_at_j2000_matches_published_constant():
    """GMST at J2000.0 (T=0 in the IAU-82 model) is the widely-cited
    280.46061837 degrees constant used as the base term of the
    low-precision GMST series."""
    gmst_rad = gmst_from_jd(JD_J2000)
    expected_deg = 280.460618375
    assert math.isclose(math.degrees(gmst_rad), expected_deg, abs_tol=1e-6)


def test_gmst_is_wrapped_to_2pi():
    """GMST should always come back in [0, 2*pi), even far from J2000."""
    far_future_jd = JD_J2000 + 100 * 365.25
    gmst_rad = gmst_from_jd(far_future_jd)
    assert 0.0 <= gmst_rad < 2.0 * math.pi


def test_tle_epoch_two_digit_year_below_57_is_2000s():
    """Epoch '24045.5...' is day 45 (Feb 14) of 2024, half a day in."""
    dt = tle_epoch_to_datetime("24045.50000000")
    assert dt == datetime(2024, 2, 14, 12, 0, 0, tzinfo=timezone.utc)


def test_tle_epoch_two_digit_year_57_and_above_is_1900s():
    """Epoch '99001.0...' is day 1 of 1999, per the NORAD convention."""
    dt = tle_epoch_to_datetime("99001.00000000")
    assert dt == datetime(1999, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
