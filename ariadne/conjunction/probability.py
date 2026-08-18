"""
probability.py

2D probability of collision (Foster/Alfano-style): project the
combined position covariance and miss vector onto the encounter plane
(perpendicular to the relative velocity at TCA) and integrate the
resulting 2D Gaussian over a disk of the combined hard-body radius.

Done by direct numerical integration rather than the closed-form
circular-covariance series (Alfano 2005) or the error-function form
(Foster 1992), both of which assume a circularly symmetric encounter-
plane covariance; integrating directly handles the general elliptical
case without that assumption, at the cost of a `dblquad` call per Pc.
"""

import numpy as np
from scipy.integrate import dblquad

from ariadne.utils.math import unit_vector


def encounter_plane_basis(v_rel: np.ndarray) -> tuple:
    """
    Two orthonormal vectors spanning the plane perpendicular to the
    relative velocity, the plane conjunction geometry is conventionally
    projected onto since relative motion is ~entirely within it at TCA.

    Args:
        v_rel: relative velocity, ECI, km/s.

    Returns:
        (u, w): orthonormal 3-vectors, both perpendicular to `v_rel`.
    """
    v_hat = unit_vector(v_rel)
    # Any reference vector not parallel to v_hat works; pick whichever
    # of +z/+x has the smaller component along v_hat to stay
    # well-conditioned near either pole.
    reference = np.array([0.0, 0.0, 1.0]) if abs(v_hat[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = unit_vector(np.cross(v_hat, reference))
    w = np.cross(v_hat, u)
    return u, w


def probability_of_collision(
    r_rel: np.ndarray,
    v_rel: np.ndarray,
    covariance_primary: np.ndarray,
    covariance_secondary: np.ndarray,
    hard_body_radius: float,
) -> float:
    """
    2D probability of collision at TCA.

    Args:
        r_rel, v_rel: relative position/velocity at TCA, ECI, km and
            km/s (secondary minus primary, see `relative_state.py`).
        covariance_primary, covariance_secondary: each object's ECI
            position covariance at TCA, 3x3 (or 6x6, only the leading
            3x3 position block is used).
        hard_body_radius: combined hard-body radius (sum of both
            objects' physical radii, plus any desired margin), km.

    Returns:
        Probability of collision, in [0, 1].
    """
    u, w = encounter_plane_basis(v_rel)
    basis = np.array([u, w])

    combined_cov = covariance_primary[:3, :3] + covariance_secondary[:3, :3]
    cov_2d = basis @ combined_cov @ basis.T
    miss_2d = basis @ r_rel

    return _integrate_gaussian_over_disk(miss_2d, cov_2d, hard_body_radius)


def _integrate_gaussian_over_disk(mean: np.ndarray, cov: np.ndarray, radius: float) -> float:
    inv_cov = np.linalg.inv(cov)
    norm_factor = 1.0 / (2.0 * np.pi * np.sqrt(np.linalg.det(cov)))

    def pdf(y: float, x: float) -> float:
        d = np.array([x, y]) - mean
        return norm_factor * np.exp(-0.5 * d @ inv_cov @ d)

    def y_lower(x: float) -> float:
        return -np.sqrt(max(radius**2 - x**2, 0.0))

    def y_upper(x: float) -> float:
        return np.sqrt(max(radius**2 - x**2, 0.0))

    probability, _ = dblquad(
        pdf, -radius, radius, y_lower, y_upper, epsabs=1e-12, epsrel=1e-10,
    )
    return float(probability)
