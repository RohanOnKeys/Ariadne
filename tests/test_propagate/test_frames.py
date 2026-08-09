"""Tests for ariadne.propagate.frames."""

from datetime import datetime, timezone

import numpy as np

from ariadne.constants import R_EARTH
from ariadne.propagate import frames


def _epoch():
    return datetime(2024, 2, 14, 12, 25, 40, tzinfo=timezone.utc)


def _iss_like_teme_state():
    r = np.array([4123.205614145148, -1004.0143833977686, 5294.538154136962])
    v = np.array([2.501286951839832, 7.224826316290108, -0.5802661362196427])
    return r, v


def test_teme_eci_round_trip():
    r, v = _iss_like_teme_state()
    epoch = _epoch()

    r_eci, v_eci = frames.teme_to_eci(r, v, epoch)
    r_back, v_back = frames.eci_to_teme(r_eci, v_eci, epoch)

    np.testing.assert_allclose(r_back, r, atol=1e-8)
    np.testing.assert_allclose(v_back, v, atol=1e-10)


def test_teme_to_eci_preserves_vector_magnitude():
    """Precession is a rotation, magnitude (and speed) must be exactly
    preserved regardless of the epoch."""
    r, v = _iss_like_teme_state()
    r_eci, v_eci = frames.teme_to_eci(r, v, _epoch())
    assert np.isclose(np.linalg.norm(r_eci), np.linalg.norm(r))
    assert np.isclose(np.linalg.norm(v_eci), np.linalg.norm(v))


def test_teme_eci_identity_at_j2000_epoch():
    """Precession is measured from J2000, so at the J2000 epoch itself
    TEME and ECI (in this module's precession-only approximation)
    should coincide."""
    from ariadne.utils.time import jd_to_datetime
    from ariadne.constants import JD_J2000

    j2000_epoch = jd_to_datetime(JD_J2000)
    r, v = _iss_like_teme_state()
    r_eci, v_eci = frames.teme_to_eci(r, v, j2000_epoch)
    np.testing.assert_allclose(r_eci, r, atol=1e-9)
    np.testing.assert_allclose(v_eci, v, atol=1e-9)


def test_eci_ecef_round_trip():
    r, v = _iss_like_teme_state()
    epoch = _epoch()

    r_ecef, v_ecef = frames.eci_to_ecef(r, v, epoch)
    r_back, v_back = frames.ecef_to_eci(r_ecef, v_ecef, epoch)

    np.testing.assert_allclose(r_back, r, atol=1e-8)
    np.testing.assert_allclose(v_back, v, atol=1e-10)


def test_eci_to_ecef_preserves_position_magnitude():
    r, v = _iss_like_teme_state()
    r_ecef, _ = frames.eci_to_ecef(r, v, _epoch())
    assert np.isclose(np.linalg.norm(r_ecef), np.linalg.norm(r))


def test_geodetic_to_ecef_equator_prime_meridian():
    """At lat=lon=0, ECEF x should be Earth's radius + altitude, y and
    z should be ~0."""
    r = frames.geodetic_to_ecef(0.0, 0.0, 0.0)
    np.testing.assert_allclose(r, [R_EARTH, 0.0, 0.0], atol=1e-9)


def test_geodetic_to_ecef_north_pole():
    """At the pole, x and y vanish; z is the polar radius (WGS-84
    flattening makes this slightly less than R_EARTH)."""
    r = frames.geodetic_to_ecef(np.pi / 2, 0.0, 0.0)
    assert abs(r[0]) < 1e-6
    assert abs(r[1]) < 1e-6
    assert r[2] < R_EARTH
    assert np.isclose(r[2], 6356.752, atol=0.01)


def test_satellite_directly_overhead_gives_90deg_elevation():
    site_lat, site_lon, site_alt = np.radians(10.0), np.radians(20.0), 0.0
    site_ecef = frames.geodetic_to_ecef(site_lat, site_lon, site_alt)
    # The geodetic (ellipsoid-normal) zenith direction, not the
    # geocentric radial direction, these only coincide at the equator
    # and poles; away from them the WGS-84 flattening splits them.
    zenith_direction = np.array([
        np.cos(site_lat) * np.cos(site_lon),
        np.cos(site_lat) * np.sin(site_lon),
        np.sin(site_lat),
    ])

    r_sat = site_ecef + zenith_direction * 500.0
    az, el, rng = frames.ecef_to_topocentric(r_sat, site_lat, site_lon, site_alt)

    assert np.isclose(np.degrees(el), 90.0, atol=1e-8)
    assert np.isclose(rng, 500.0, atol=1e-8)


def test_satellite_on_horizon_gives_zero_elevation():
    site_lat, site_lon, site_alt = 0.0, 0.0, 0.0
    site_ecef = frames.geodetic_to_ecef(site_lat, site_lon, site_alt)
    # East direction at the equator/prime-meridian site is +y.
    r_sat = site_ecef + np.array([0.0, 1000.0, 0.0])

    az, el, rng = frames.ecef_to_topocentric(r_sat, site_lat, site_lon, site_alt)
    assert np.isclose(np.degrees(el), 0.0, atol=1e-8)
    assert np.isclose(np.degrees(az), 90.0, atol=1e-6)
