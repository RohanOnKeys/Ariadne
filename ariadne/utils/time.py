"""
utils.time

UTC <-> Julian Date conversion, Greenwich Mean Sidereal Time, and TLE
two-digit-year epoch decoding. `propagate/sgp4.py` and
`propagate/frames.py` both depend on this module for turning a
calendar time into the JD/GMST that SGP4 and the ECI<->ECEF rotation
need.
"""

import math
from datetime import datetime, timedelta, timezone

from ariadne.constants import DAYS_PER_CENTURY, JD_J2000


def datetime_to_jd(dt: datetime) -> float:
    """
    Convert a UTC datetime to Julian Date.

    Args:
        dt: datetime; naive values are assumed to already be UTC.

    Returns:
        Julian Date (days since -4712-01-01 12:00 UTC).
    """
    year, month = dt.year, dt.month
    day = dt.day + (
        (dt.hour + (dt.minute + (dt.second + dt.microsecond / 1e6) / 60.0) / 60.0) / 24.0
    )

    if month <= 2:
        year -= 1
        month += 12

    a = year // 100
    b = 2 - a + a // 4

    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day + b - 1524.5
    )


def jd_to_datetime(jd: float) -> datetime:
    """Convert a Julian Date to a UTC datetime (inverse of `datetime_to_jd`)."""
    jd_shifted = jd + 0.5
    z = int(math.floor(jd_shifted))
    f = jd_shifted - z

    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4

    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)

    day_frac = b - d - int(30.6001 * e) + f
    day = int(math.floor(day_frac))
    frac_day = day_frac - day

    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715

    hours_total = frac_day * 24.0
    hour = int(hours_total)
    minutes_total = (hours_total - hour) * 60.0
    minute = int(minutes_total)
    seconds_total = (minutes_total - minute) * 60.0
    second = int(seconds_total)
    microsecond = int(round((seconds_total - second) * 1e6))

    if microsecond >= 1_000_000:
        microsecond -= 1_000_000
        second += 1

    return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)


def gmst_from_jd(jd_ut1: float) -> float:
    """
    Greenwich Mean Sidereal Time (IAU-82 model) for a UT1 Julian Date.

    DUT1 (UT1 - UTC, at most ~0.9s) is ignored, treating the input JD as
    UT1 rather than first converting from UTC is the standard
    simplification at this level of fidelity.

    Args:
        jd_ut1: Julian Date (UT1, or UTC as an approximation).

    Returns:
        GMST angle in radians, wrapped to [0, 2*pi).
    """
    t_ut1 = (jd_ut1 - JD_J2000) / DAYS_PER_CENTURY

    theta_sec = (
        67310.54841
        + (876600.0 * 3600.0 + 8640184.812866) * t_ut1
        + 0.093104 * t_ut1 ** 2
        - 6.2e-6 * t_ut1 ** 3
    )

    theta_deg = (theta_sec % 86400.0) / 240.0
    return math.radians(theta_deg % 360.0)


def gmst_from_datetime(dt: datetime) -> float:
    """GMST (radians) at a UTC datetime; see `gmst_from_jd`."""
    return gmst_from_jd(datetime_to_jd(dt))


def tle_epoch_to_datetime(epoch_str: str) -> datetime:
    """
    Decode a TLE epoch field ('YYDDD.DDDDDDDD') into a UTC datetime.

    Two-digit years below 57 are read as 2000s, 57 and above as 1900s,
    the convention TLEs have used since NORAD introduced the format.

    Args:
        epoch_str: the TLE line 1 epoch field, e.g. '24045.50000000'.

    Returns:
        UTC datetime for the epoch.
    """
    yy = int(epoch_str[:2])
    day_of_year_frac = float(epoch_str[2:])

    year = 2000 + yy if yy < 57 else 1900 + yy

    day_of_year = int(day_of_year_frac)
    frac_day = day_of_year_frac - day_of_year

    return (
        datetime(year, 1, 1, tzinfo=timezone.utc)
        + timedelta(days=day_of_year - 1, seconds=frac_day * 86400.0)
    )
