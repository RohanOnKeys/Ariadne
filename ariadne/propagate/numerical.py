"""
numerical.py

Numerical integration of two-body + J2 dynamics: fixed-step RK4 and
adaptive RK45 (via `scipy.integrate.solve_ivp`), for propagation
independent of SGP4, non-TLE state vectors, or a truth trajectory to
validate SGP4/OD against.

`estimate/dynamics.py` implements the same physics as its own
self-contained fixed-step RK4 inner loop for the UKF (see that
module's docstring for why it isn't imported from here); this module
is the general-purpose propagator everything else should reach for.
"""

import numpy as np
from scipy.integrate import solve_ivp

from ariadne.constants import J2, MU_EARTH, R_EARTH


def two_body_j2_accel(state: np.ndarray, include_j2: bool = True) -> np.ndarray:
    """
    Inertial acceleration from two-body gravity, plus J2 if requested.

    Args:
        state: 6-vector [x, y, z, vx, vy, vz], ECI frame, km and km/s.
        include_j2: include the J2 (Earth oblateness) correction.
            False gives pure two-body acceleration, useful as a
            conservation-law sanity check: the simple specific-energy
            and angular-momentum formulas are only conserved quantities
            under pure two-body motion, J2 conserves a *different*
            quantity (energy including the J2 potential term), so
            checking the plain two-body formulas against J2-perturbed
            motion isn't meaningful.

    Returns:
        3-vector [ax, ay, az], km/s^2.
    """
    x, y, z = state[0], state[1], state[2]
    r = np.sqrt(x**2 + y**2 + z**2)

    accel = -MU_EARTH / r**3 * np.array([x, y, z])

    if include_j2:
        factor = 1.5 * J2 * MU_EARTH * R_EARTH**2 / r**5
        z_r2 = (z / r) ** 2
        accel = accel + factor * np.array([
            x * (5 * z_r2 - 1),
            y * (5 * z_r2 - 1),
            z * (5 * z_r2 - 3),
        ])

    return accel


def state_derivative(t: float, state: np.ndarray, include_j2: bool = True) -> np.ndarray:
    """
    Full 6-state derivative [vx, vy, vz, ax, ay, az]. Signature matches
    `scipy.integrate.solve_ivp`'s `fun(t, y)` convention (t unused,
    dynamics are time-invariant in the ECI frame).
    """
    velocity = state[3:6]
    accel = two_body_j2_accel(state, include_j2=include_j2)
    return np.concatenate([velocity, accel])


def propagate_rk4(
    state: np.ndarray,
    dt: float,
    *,
    step: float = 60.0,
    include_j2: bool = True,
) -> np.ndarray:
    """
    Propagate a state vector forward by `dt` seconds using fixed-step
    RK4, split into substeps of at most `step` seconds so long arcs
    don't lose accuracy to a single oversized step.

    Args:
        state: 6-vector [x, y, z, vx, vy, vz], km and km/s.
        dt: total propagation time, seconds. May be negative.
        step: maximum RK4 substep size, seconds.
        include_j2: see `two_body_j2_accel`.

    Returns:
        6-vector, propagated state at t + dt.
    """
    if dt == 0:
        return state.copy()

    n_steps = max(1, int(np.ceil(abs(dt) / step)))
    h = dt / n_steps

    result = state.copy()
    for _ in range(n_steps):
        k1 = state_derivative(0.0, result, include_j2)
        k2 = state_derivative(0.0, result + 0.5 * h * k1, include_j2)
        k3 = state_derivative(0.0, result + 0.5 * h * k2, include_j2)
        k4 = state_derivative(0.0, result + h * k3, include_j2)
        result = result + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

    return result


def propagate(
    state: np.ndarray,
    dt: float,
    *,
    method: str = "RK45",
    rtol: float = 1e-10,
    atol: float = 1e-12,
    include_j2: bool = True,
) -> np.ndarray:
    """
    Propagate a state vector forward by `dt` seconds using an adaptive
    integrator (`scipy.integrate.solve_ivp`).

    Args:
        state: 6-vector [x, y, z, vx, vy, vz], km and km/s.
        dt: total propagation time, seconds. May be negative.
        method: any `solve_ivp` method, "RK45" by default.
        rtol, atol: `solve_ivp` tolerances.
        include_j2: see `two_body_j2_accel`.

    Returns:
        6-vector, propagated state at t + dt.
    """
    if dt == 0:
        return state.copy()

    solution = solve_ivp(
        state_derivative, (0.0, dt), state,
        method=method, rtol=rtol, atol=atol, args=(include_j2,),
    )
    return solution.y[:, -1]
