"""Tests for ariadne.propagate.numerical."""

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from ariadne.constants import MU_EARTH, R_EARTH
from ariadne.models.tle import TLE
from ariadne.propagate import sgp4 as ariadne_sgp4
from ariadne.propagate.numerical import propagate, propagate_rk4, two_body_j2_accel

_LINE1 = "1 25544U 98067A   24045.51782528  .00016717  00000-0  10270-3 0  9998"
_LINE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49560684436460"


def _circular_leo_state(alt_km: float = 500.0) -> np.ndarray:
    r = R_EARTH + alt_km
    v_circ = np.sqrt(MU_EARTH / r)
    return np.array([r, 0.0, 0.0, 0.0, v_circ, 0.0])


def _specific_energy(state: np.ndarray) -> float:
    r, v = np.linalg.norm(state[:3]), np.linalg.norm(state[3:6])
    return 0.5 * v**2 - MU_EARTH / r


def _angular_momentum(state: np.ndarray) -> np.ndarray:
    return np.cross(state[:3], state[3:6])


def test_zero_dt_is_identity():
    state = _circular_leo_state()
    np.testing.assert_array_equal(propagate(state, 0.0), state)
    np.testing.assert_array_equal(propagate_rk4(state, 0.0), state)


def test_pure_two_body_conserves_energy_over_multi_day_arc():
    """(J2 aside): with include_j2=False the plain two-body specific-
    energy formula is an exact conserved quantity, so any drift here
    is integrator error, not real physics."""
    state = _circular_leo_state()
    e0 = _specific_energy(state)

    final = propagate(state, 3 * 86400.0, include_j2=False, rtol=1e-12, atol=1e-12)
    assert abs(_specific_energy(final) - e0) / abs(e0) < 1e-8


def test_pure_two_body_conserves_angular_momentum_over_multi_day_arc():
    state = _circular_leo_state()
    l0 = np.linalg.norm(_angular_momentum(state))

    final = propagate(state, 3 * 86400.0, include_j2=False, rtol=1e-12, atol=1e-12)
    l1 = np.linalg.norm(_angular_momentum(final))
    assert abs(l1 - l0) / l0 < 1e-8


def test_j2_perturbed_orbit_still_conserves_angular_momentum_magnitude():
    """J2's secular theory keeps inclination fixed to first order, so
    |L| (unlike the plain two-body energy formula) stays conserved
    even with J2 active."""
    state = _circular_leo_state()
    l0 = np.linalg.norm(_angular_momentum(state))

    final = propagate(state, 3 * 86400.0, include_j2=True, rtol=1e-12, atol=1e-12)
    l1 = np.linalg.norm(_angular_momentum(final))
    assert abs(l1 - l0) / l0 < 1e-6


def test_j2_perturbed_orbit_breaks_plain_two_body_energy_conservation():
    """The reverse of the above: J2 conserves energy *including* the
    J2 potential term, not the plain two-body formula, so this should
    show measurable (if small) drift, confirming J2 is actually being
    applied."""
    state = _circular_leo_state()
    e0 = _specific_energy(state)

    final = propagate(state, 3 * 86400.0, include_j2=True, rtol=1e-12, atol=1e-12)
    relative_drift = abs(_specific_energy(final) - e0) / abs(e0)
    assert relative_drift > 1e-8


def test_two_body_j2_accel_j2_term_vanishes_without_flag():
    state = _circular_leo_state()
    with_j2 = two_body_j2_accel(state, include_j2=True)
    without_j2 = two_body_j2_accel(state, include_j2=False)
    assert not np.allclose(with_j2, without_j2)

    pure_two_body_expected = -MU_EARTH / np.linalg.norm(state[:3])**3 * state[:3]
    np.testing.assert_allclose(without_j2, pure_two_body_expected)


def test_propagate_rk4_matches_adaptive_propagate_closely():
    """Fixed-step RK4 (30s substeps) vs. a tight-tolerance adaptive
    integrator over 6 hours: expect agreement at the tens-of-meters
    level (RK4 truncation error), not adaptive-integrator precision."""
    state = _circular_leo_state()
    dt = 6 * 3600.0
    rk4_result = propagate_rk4(state, dt, step=30.0)
    adaptive_result = propagate(state, dt, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(rk4_result, adaptive_result, atol=0.05)


def test_tracks_sgp4_to_a_sane_bound_over_a_six_hour_arc():
    """Cross-check against SGP4 (M1's other propagator): pure J2
    physics won't capture drag, so some divergence over hours is
    expected, but it should stay small relative to LEO's ~6800 km
    orbital radius."""
    epoch0 = datetime(2024, 2, 14, 12, 25, 40, tzinfo=timezone.utc)
    tle = TLE.from_lines(_LINE1, _LINE2)
    state0 = ariadne_sgp4.propagate(tle, epoch0)

    six_hours = timedelta(hours=6)
    sgp4_state = ariadne_sgp4.propagate(tle, epoch0 + six_hours)
    numerical_final = propagate(
        state0.as_vector(), six_hours.total_seconds(), rtol=1e-12, atol=1e-12,
    )

    position_error = np.linalg.norm(numerical_final[:3] - sgp4_state.position)
    assert position_error < 20.0


@pytest.mark.parametrize("include_j2", [True, False])
def test_propagate_rk4_and_adaptive_agree_regardless_of_j2_flag(include_j2):
    state = _circular_leo_state()
    dt = 3600.0
    rk4_result = propagate_rk4(state, dt, include_j2=include_j2)
    adaptive_result = propagate(state, dt, include_j2=include_j2, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(rk4_result, adaptive_result, atol=0.05)
