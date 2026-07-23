"""
dynamics.py

State transition (process) model for orbit propagation inside the UKF.

Implements two-body gravity plus the J2 perturbation (Earth oblateness),
integrated numerically with RK4. This is deliberately separate from any
`propagation/` module used by the CLI's `propagate` command: the UKF
needs a fast, self-contained state transition function it can call once
per sigma point, per predict step.
"""

import numpy as np

# Earth gravitational parameter, km^3/s^2 (WGS-84)
MU_EARTH = 398600.4418
# Earth equatorial radius, km (WGS-84)
R_EARTH = 6378.137
# J2 zonal harmonic coefficient (dimensionless, WGS-84)
J2 = 1.08262668e-3


def two_body_j2_accel(state: np.ndarray) -> np.ndarray:
    """
    Compute inertial acceleration from two-body gravity + J2 perturbation.

    Args:
        state: 6-vector [x, y, z, vx, vy, vz] in ECI frame, km and km/s.

    Returns:
        3-vector [ax, ay, az], km/s^2, in ECI frame.
    """
    x, y, z = state[0], state[1], state[2]
    r = np.sqrt(x**2 + y**2 + z**2)

    # Two-body point-mass gravity.
    a_two_body = -MU_EARTH / r**3 * np.array([x, y, z])

    # J2 perturbation (standard closed-form expression).
    factor = 1.5 * J2 * MU_EARTH * R_EARTH**2 / r**5
    z_r2 = (z / r) ** 2
    a_j2 = factor * np.array([
        x * (5 * z_r2 - 1),
        y * (5 * z_r2 - 1),
        z * (5 * z_r2 - 3),
    ])

    return a_two_body + a_j2


def state_derivative(t: float, state: np.ndarray) -> np.ndarray:
    """
    Full 6-state derivative [vx, vy, vz, ax, ay, az] for use with an
    ODE integrator. Signature matches scipy.integrate.solve_ivp's
    fun(t, y) convention (t unused — dynamics are time-invariant).

    Args:
        t: time, seconds (unused, kept for solve_ivp compatibility).
        state: 6-vector [x, y, z, vx, vy, vz], km and km/s.

    Returns:
        6-vector [vx, vy, vz, ax, ay, az].
    """
    velocity = state[3:6]
    accel = two_body_j2_accel(state)
    return np.concatenate([velocity, accel])


def propagate_rk4(state: np.ndarray, dt: float) -> np.ndarray:
    """
    Propagate a single state vector forward by dt seconds using
    fixed-step RK4 integration of the J2-perturbed two-body dynamics.

    Used as the UKF's process model f(x, dt): called once per sigma
    point at every predict step, so it needs to be self-contained and
    fast rather than relying on an adaptive external integrator.

    Args:
        state: 6-vector [x, y, z, vx, vy, vz], km and km/s.
        dt: timestep, seconds. Must be positive.

    Returns:
        6-vector, propagated state at t + dt.
    """
    if dt == 0:
        return state.copy()

    k1 = state_derivative(0.0, state)
    k2 = state_derivative(0.0, state + 0.5 * dt * k1)
    k3 = state_derivative(0.0, state + 0.5 * dt * k2)
    k4 = state_derivative(0.0, state + dt * k3)

    return state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
