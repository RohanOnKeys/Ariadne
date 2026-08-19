"""
frames.py

TEME -> ECI -> ECEF -> topocentric (az/el/range) transforms. Sole
owner of every rotation in Ariadne (per architecture.md); nothing else
should hand-roll a frame conversion.

Known simplification, documented here rather than hidden: the TEME ->
ECI step applies IAU-76 precession only and treats TT as UTC (skips
the ~69s TT-UTC offset). Nutation is dropped, its effect is at most a
few arcseconds, well under SGP4's own error budget and consistent with
the "Deliberately out of scope" call in the roadmap for other
sub-arcsecond/sub-metre refinements (full nutation series, polar
motion). If Ariadne ever needs sub-km frame accuracy this is the first
place to revisit.
"""

import math

import numpy as np

from ariadne.constants import (
    ARCSEC2RAD,
    DAYS_PER_CENTURY,
    ECC_EARTH_SQ,
    JD_J2000,
    OMEGA_EARTH,
    R_EARTH,
    R_EARTH_POLAR,
    TWO_PI,
)
from ariadne.utils.math import rot2, rot3
from ariadne.utils.time import datetime_to_jd, gmst_from_datetime

_EARTH_OMEGA_VECTOR = np.array([0.0, 0.0, OMEGA_EARTH])


def _precession_matrix(epoch) -> np.ndarray:
    """
    IAU-76 precession matrix, J2000 mean equator/equinox -> mean
    equator/equinox of `epoch` (Vallado Algorithm 24). Applying this
    and stopping short of nutation is this module's TEME
    approximation, see the module docstring.
    """
    t = (datetime_to_jd(epoch) - JD_J2000) / DAYS_PER_CENTURY

    zeta = (2306.2181 * t + 0.30188 * t**2 + 0.017998 * t**3) * ARCSEC2RAD
    theta = (2004.3109 * t - 0.42665 * t**2 - 0.041833 * t**3) * ARCSEC2RAD
    z = (2306.2181 * t + 1.09468 * t**2 + 0.018203 * t**3) * ARCSEC2RAD

    return rot3(-z) @ rot2(theta) @ rot3(-zeta)


def teme_to_eci(r: np.ndarray, v: np.ndarray, epoch) -> tuple:
    """
    TEME -> ECI (J2000 mean equator/equinox).

    Args:
        r: position, km, TEME.
        v: velocity, km/s, TEME.
        epoch: UTC datetime the state is valid at.

    Returns:
        (r_eci, v_eci).
    """
    precession = _precession_matrix(epoch)
    return precession.T @ r, precession.T @ v


def eci_to_teme(r: np.ndarray, v: np.ndarray, epoch) -> tuple:
    """Inverse of `teme_to_eci`."""
    precession = _precession_matrix(epoch)
    return precession @ r, precession @ v


def eci_to_ecef(r: np.ndarray, v: np.ndarray, epoch) -> tuple:
    """
    ECI (J2000) -> ECEF, rotating by Greenwich Mean Sidereal Time.
    Polar motion (sub-arcsecond) is neglected.

    Args:
        r: position, km, ECI.
        v: velocity, km/s, ECI.
        epoch: UTC datetime the state is valid at.

    Returns:
        (r_ecef, v_ecef).
    """
    rotation = rot3(gmst_from_datetime(epoch))
    r_ecef = rotation @ r
    v_ecef = rotation @ v - np.cross(_EARTH_OMEGA_VECTOR, r_ecef)
    return r_ecef, v_ecef


def ecef_to_eci(r: np.ndarray, v: np.ndarray, epoch) -> tuple:
    """Inverse of `eci_to_ecef`."""
    rotation = rot3(gmst_from_datetime(epoch))
    r_eci = rotation.T @ r
    v_eci = rotation.T @ (v + np.cross(_EARTH_OMEGA_VECTOR, r))
    return r_eci, v_eci


def geodetic_to_ecef(lat: float, lon: float, alt: float) -> np.ndarray:
    """
    Geodetic (WGS-84) site coordinates -> ECEF position.

    Args:
        lat: geodetic latitude, radians.
        lon: longitude, radians.
        alt: height above the WGS-84 ellipsoid, km.

    Returns:
        3-vector, km, ECEF.
    """
    sin_lat = math.sin(lat)
    n = R_EARTH / math.sqrt(1.0 - ECC_EARTH_SQ * sin_lat**2)

    return np.array([
        (n + alt) * math.cos(lat) * math.cos(lon),
        (n + alt) * math.cos(lat) * math.sin(lon),
        (n * (1.0 - ECC_EARTH_SQ) + alt) * sin_lat,
    ])


def ecef_to_geodetic(r_ecef: np.ndarray) -> tuple:
    """
    ECEF position -> geodetic (WGS-84) latitude/longitude/altitude,
    Bowring's method (closed-form; accurate to sub-millimetre altitude
    for any terrestrial-range input, no iteration needed). Inverse of
    `geodetic_to_ecef`.

    Args:
        r_ecef: position, km, ECEF.

    Returns:
        (lat, lon, alt): geodetic latitude and longitude, radians;
        height above the WGS-84 ellipsoid, km.
    """
    x, y, z = r_ecef
    p = math.hypot(x, y)
    lon = math.atan2(y, x)

    second_ecc_sq = ECC_EARTH_SQ * R_EARTH**2 / R_EARTH_POLAR**2
    theta = math.atan2(z * R_EARTH, p * R_EARTH_POLAR)
    lat = math.atan2(
        z + second_ecc_sq * R_EARTH_POLAR * math.sin(theta) ** 3,
        p - ECC_EARTH_SQ * R_EARTH * math.cos(theta) ** 3,
    )

    n = R_EARTH / math.sqrt(1.0 - ECC_EARTH_SQ * math.sin(lat) ** 2)
    # The p/cos(lat) form of altitude is 0/0 near the poles; z/sin(lat)
    # is the equivalent well-conditioned form there (and ill-conditioned
    # near the equator, where p/cos(lat) is used instead).
    if abs(math.cos(lat)) > 1e-6:
        alt = p / math.cos(lat) - n
    else:
        alt = z / math.sin(lat) - n * (1.0 - ECC_EARTH_SQ)

    return lat, lon, alt


def ecef_to_topocentric(
    r_sat_ecef: np.ndarray,
    site_lat: float,
    site_lon: float,
    site_alt: float,
) -> tuple:
    """
    ECEF satellite position, as seen from a ground site -> az/el/range.

    Args:
        r_sat_ecef: satellite position, km, ECEF.
        site_lat: site geodetic latitude, radians.
        site_lon: site longitude, radians.
        site_alt: site height above the WGS-84 ellipsoid, km.

    Returns:
        (azimuth, elevation, range): azimuth and elevation in radians
        (azimuth measured clockwise from north, elevation from the
        local horizon), range in km.
    """
    site_ecef = geodetic_to_ecef(site_lat, site_lon, site_alt)
    rho = r_sat_ecef - site_ecef

    sin_lat, cos_lat = math.sin(site_lat), math.cos(site_lat)
    sin_lon, cos_lon = math.sin(site_lon), math.cos(site_lon)

    south = sin_lat * cos_lon * rho[0] + sin_lat * sin_lon * rho[1] - cos_lat * rho[2]
    east = -sin_lon * rho[0] + cos_lon * rho[1]
    zenith = cos_lat * cos_lon * rho[0] + cos_lat * sin_lon * rho[1] + sin_lat * rho[2]

    range_km = math.sqrt(south**2 + east**2 + zenith**2)
    elevation = math.asin(zenith / range_km)
    azimuth = math.atan2(east, -south) % TWO_PI

    return azimuth, elevation, range_km
