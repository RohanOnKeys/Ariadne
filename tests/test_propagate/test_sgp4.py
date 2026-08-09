"""Tests for ariadne.propagate.sgp4.

Correctness of the SGP4 math itself is the `sgp4` PyPI package's
responsibility, it's cross-validated in its own test suite against
Vallado's published verification vectors (SGP4-VER.TLE). What this
module needs to get right, and what these tests check, is the
wrapping: handing it the right epoch, converting its native TEME
output to ECI without introducing an error, and turning its error
codes into PropagationError.
"""

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest
from sgp4.api import Satrec, jday

from ariadne.constants import R_EARTH
from ariadne.exceptions import PropagationError
from ariadne.models.state_vector import Frame
from ariadne.models.tle import TLE
from ariadne.propagate import sgp4 as ariadne_sgp4
from ariadne.propagate.frames import eci_to_teme

_LINE1 = "1 25544U 98067A   24045.51782528  .00016717  00000-0  10270-3 0  9998"
_LINE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49560684436460"


def _iss_tle():
    return TLE.from_lines(_LINE1, _LINE2, name="ISS (ZARYA)")


def _epoch():
    return datetime(2024, 2, 14, 12, 25, 40, tzinfo=timezone.utc)


def test_propagate_returns_eci_frame_state():
    state = ariadne_sgp4.propagate(_iss_tle(), _epoch())
    assert state.frame is Frame.ECI
    assert state.norad_id == 25544
    assert state.name == "ISS (ZARYA)"
    assert state.epoch == _epoch()


def test_propagated_altitude_is_realistic_leo():
    state = ariadne_sgp4.propagate(_iss_tle(), _epoch())
    altitude = np.linalg.norm(state.position) - R_EARTH
    assert 350.0 < altitude < 450.0


def test_eci_output_matches_raw_teme_output_converted_by_frames():
    """Confirms the wrapper's only added step, TEME->ECI, is applied
    correctly: converting the returned ECI state back to TEME should
    reproduce exactly what the bare sgp4 package returns."""
    epoch = _epoch()
    satrec = Satrec.twoline2rv(_LINE1, _LINE2)
    jd, fr = jday(epoch.year, epoch.month, epoch.day, epoch.hour, epoch.minute, float(epoch.second))
    error_code, r_teme_raw, v_teme_raw = satrec.sgp4(jd, fr)
    assert error_code == 0

    state = ariadne_sgp4.propagate(_iss_tle(), epoch)
    r_teme_back, v_teme_back = eci_to_teme(state.position, state.velocity, epoch)

    np.testing.assert_allclose(r_teme_back, r_teme_raw, atol=1e-9)
    np.testing.assert_allclose(v_teme_back, v_teme_raw, atol=1e-9)


def test_propagating_far_future_decayed_orbit_raises_propagation_error():
    far_future = _epoch() + timedelta(days=365 * 80)
    with pytest.raises(PropagationError, match="SGP4 error"):
        ariadne_sgp4.propagate(_iss_tle(), far_future)


def test_short_arc_stays_close_to_epoch_state():
    """Sanity check on propagation direction/scale: one orbit later
    (~93 minutes for the ISS), the satellite should be back near its
    starting altitude, not off by orders of magnitude."""
    epoch = _epoch()
    state0 = ariadne_sgp4.propagate(_iss_tle(), epoch)
    one_period_later = ariadne_sgp4.propagate(_iss_tle(), epoch + timedelta(minutes=93))

    r0 = np.linalg.norm(state0.position)
    r1 = np.linalg.norm(one_period_later.position)
    assert abs(r1 - r0) < 50.0
