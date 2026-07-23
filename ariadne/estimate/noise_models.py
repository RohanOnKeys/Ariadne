"""
noise_models.py

Constructs and tunes the process noise covariance (Q) and measurement
noise covariance (R) matrices used by the UKF.

Q represents uncertainty injected at each predict step to account for
un-modeled dynamics (higher-order gravity terms, drag, SRP, third-body
effects that the J2-only dynamics model does not capture).

R represents the noise characteristics of the (simulated) GPS-like
position/velocity sensor.
"""

import numpy as np


def build_measurement_noise(pos_sigma: float, vel_sigma: float) -> np.ndarray:
    """
    Build a 6x6 measurement noise covariance matrix R for a direct
    position/velocity (GPS-like) sensor.

    Assumes independent, zero-mean Gaussian noise on each of the three
    position axes and three velocity axes (no cross-correlation between
    axes or between position and velocity).

    Args:
        pos_sigma: 1-sigma position noise, per axis, in km.
        vel_sigma: 1-sigma velocity noise, per axis, in km/s.

    Returns:
        6x6 numpy array, R.
    """
    diag = np.array([pos_sigma**2] * 3 + [vel_sigma**2] * 3)
    return np.diag(diag)


def build_process_noise_discrete_white_noise(dt: float, sigma_accel: float,
                                              dim: int = 6) -> np.ndarray:
    """
    Build a discrete white-noise-acceleration process noise matrix Q.

    Models the un-modeled dynamics (J3+, drag, SRP, third-body) as a
    random acceleration with standard deviation `sigma_accel` acting
    over one timestep. Uses the standard piecewise-constant white noise
    acceleration (DWNA) block form per axis:

        Q_axis = [[dt^4/4, dt^3/2],
                  [dt^3/2, dt^2  ]] * sigma_accel^2

    applied independently to each of the 3 position/velocity axis pairs.

    Args:
        dt: timestep in seconds.
        sigma_accel: 1-sigma un-modeled acceleration, km/s^2. Tune this
            up if NIS diagnostics show the filter is overconfident
            (NIS consistently above the expected chi-square bound);
            tune it down if NIS is consistently below (underconfident).
        dim: state dimension, must be 6 (3 position + 3 velocity axes).

    Returns:
        dim x dim numpy array, Q, with position/velocity ordering
        matching the state vector [x, y, z, vx, vy, vz].
    """
    if dim != 6:
        raise ValueError("build_process_noise_discrete_white_noise only "
                          "supports the 6-state [pos, vel] case.")

    block = np.array([
        [dt**4 / 4, dt**3 / 2],
        [dt**3 / 2, dt**2],
    ]) * sigma_accel**2

    Q = np.zeros((6, 6))
    # State ordering is [x, y, z, vx, vy, vz], so position index i pairs
    # with velocity index i + 3 for each axis.
    for axis in range(3):
        pos_idx, vel_idx = axis, axis + 3
        Q[pos_idx, pos_idx] = block[0, 0]
        Q[pos_idx, vel_idx] = block[0, 1]
        Q[vel_idx, pos_idx] = block[1, 0]
        Q[vel_idx, vel_idx] = block[1, 1]

    return Q
