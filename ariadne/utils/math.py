"""
utils.math

Small vector/rotation/angle helpers shared by `propagate/frames.py`,
`propagate/numerical.py`, and the conjunction geometry modules.

Rotation matrices follow Vallado's convention: R1/R2/R3 rotate the
*coordinate frame* (a passive rotation) by `angle` radians about the
x/y/z axis respectively, so e.g. `rot3(theta) @ r_eci` re-expresses
`r_eci` in a frame rotated by `theta` about z (as with ECI -> ECEF via
GMST).
"""

import numpy as np

from ariadne.exceptions import AriadneError


def unit_vector(v: np.ndarray) -> np.ndarray:
    """
    Normalize a vector to unit length.

    Args:
        v: n-vector.

    Returns:
        v / ||v||.

    Raises:
        AriadneError: if `v` is (numerically) the zero vector.
    """
    norm = np.linalg.norm(v)
    if norm < 1e-15:
        raise AriadneError("Cannot normalize a zero-length vector.")
    return v / norm


def rot1(angle: float) -> np.ndarray:
    """Elementary rotation matrix about the x-axis, radians."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([
        [1.0, 0.0, 0.0],
        [0.0, c, s],
        [0.0, -s, c],
    ])


def rot2(angle: float) -> np.ndarray:
    """Elementary rotation matrix about the y-axis, radians."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([
        [c, 0.0, -s],
        [0.0, 1.0, 0.0],
        [s, 0.0, c],
    ])


def rot3(angle: float) -> np.ndarray:
    """Elementary rotation matrix about the z-axis, radians."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([
        [c, s, 0.0],
        [-s, c, 0.0],
        [0.0, 0.0, 1.0],
    ])


def wrap_to_2pi(angle: float) -> float:
    """Wrap an angle (radians) into [0, 2*pi)."""
    return angle % (2.0 * np.pi)


def wrap_to_pi(angle: float) -> float:
    """Wrap an angle (radians) into (-pi, pi]."""
    wrapped = wrap_to_2pi(angle)
    return wrapped - 2.0 * np.pi if wrapped > np.pi else wrapped
