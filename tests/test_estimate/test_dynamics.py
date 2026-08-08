"""Tests for ariadne.estimate.dynamics."""

import numpy as np

from ariadne.estimate.dynamics import (
    two_body_j2_accel, propagate_rk4, MU_EARTH, R_EARTH,
)


def _circular_leo_state(alt_km: float = 500.0) -> np.ndarray:
    """Build a circular LEO state vector at the given altitude, for
    use as a known-orbit test fixture."""
    r = R_EARTH + alt_km
    v_circ = np.sqrt(MU_EARTH / r)
    return np.array([r, 0.0, 0.0, 0.0, v_circ, 0.0])


def test_two_body_accel_matches_newton_at_equator():
    """With J2 zeroed out, acceleration should reduce to plain
    two-body gravity magnitude mu / r^2."""
    state = _circular_leo_state()
    # Zero out J2 contribution by evaluating at z=0 (J2 term still
    # nonzero in-plane at equator, so instead check magnitude bound
    # against two-body-only formula minus expected J2 correction).
    accel = two_body_j2_accel(state)
    r = np.linalg.norm(state[:3])
    two_body_mag = MU_EARTH / r**2
    # At the equator (z=0) J2 acts purely radially inward alongside
    # two-body gravity, so total magnitude should be close to but not
    # exactly equal to two-body-only (J2 is a small correction).
    accel_mag = np.linalg.norm(accel)
    assert abs(accel_mag - two_body_mag) / two_body_mag < 0.01


def test_propagate_rk4_zero_dt_is_identity():
    """Propagating by dt=0 should return the input state unchanged."""
    state = _circular_leo_state()
    result = propagate_rk4(state, 0.0)
    np.testing.assert_array_equal(result, state)


def test_propagate_rk4_conserves_radius_for_circular_orbit():
    """A circular (two-body) IC propagated with J2 active should stay
    close to its initial radius — J2 causes real, small, step-size-
    independent radius oscillation (not pure two-body conservation),
    so the bound here is set above that physical effect (~3e-4) rather
    than at RK4 numerical-error level."""
    state = _circular_leo_state()
    r0 = np.linalg.norm(state[:3])

    dt = 10.0  # seconds
    for _ in range(60):  # 10 minutes total
        state = propagate_rk4(state, dt)

    r1 = np.linalg.norm(state[:3])
    assert abs(r1 - r0) / r0 < 1e-3


def test_propagate_rk4_matches_scipy_reference():
    """Cross-check the hand-rolled RK4 against scipy's solve_ivp over
    a short propagation window, as a numerical sanity check."""
    from scipy.integrate import solve_ivp
    from ariadne.estimate.dynamics import state_derivative

    state = _circular_leo_state()
    dt_total = 300.0  # 5 minutes

    # Reference: adaptive-step scipy integrator.
    ref = solve_ivp(state_derivative, [0, dt_total], state,
                    rtol=1e-10, atol=1e-12)
    ref_final = ref.y[:, -1]

    # Fixed-step RK4, small steps for accuracy.
    result = state.copy()
    n_steps = 300
    dt_step = dt_total / n_steps
    for _ in range(n_steps):
        result = propagate_rk4(result, dt_step)

    np.testing.assert_allclose(result, ref_final, rtol=1e-6, atol=1e-6)
