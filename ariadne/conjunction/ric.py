"""
ric.py

Rotate a relative state from ECI into the primary object's
Radial/In-track/Cross-track (RIC) frame at a given instant, conjunction
geometry reads far more naturally in RIC (radial = along the primary's
position vector, cross-track = orbit normal) than in raw ECI
components.
"""

import numpy as np

from ariadne.utils.math import unit_vector


def ric_rotation_matrix(r_primary: np.ndarray, v_primary: np.ndarray) -> np.ndarray:
    """
    Rotation matrix from ECI into the primary's RIC frame at the
    instant it has position/velocity `r_primary`/`v_primary`.

    Returns:
        3x3 matrix R such that `R @ v_eci` re-expresses an ECI vector
        in RIC (rows are the radial, in-track, cross-track unit
        vectors, in that order).
    """
    radial = unit_vector(r_primary)
    cross_track = unit_vector(np.cross(r_primary, v_primary))
    in_track = np.cross(cross_track, radial)
    return np.array([radial, in_track, cross_track])


def eci_to_ric(
    r_rel: np.ndarray,
    v_rel: np.ndarray,
    r_primary: np.ndarray,
    v_primary: np.ndarray,
) -> tuple:
    """
    Relative position/velocity, ECI -> RIC.

    `v_ric` is the inertial relative velocity re-expressed in the RIC
    unit vectors, not corrected for the frame's own rotation rate,
    matching the RTN velocity convention used in conjunction data
    messages.

    Args:
        r_rel, v_rel: relative state, ECI, km and km/s (secondary
            minus primary, see `relative_state.py`).
        r_primary, v_primary: primary's own ECI state, defines the RIC
            frame's orientation.

    Returns:
        (r_ric, v_ric): 3-vectors, km and km/s.
    """
    rotation = ric_rotation_matrix(r_primary, v_primary)
    return rotation @ r_rel, rotation @ v_rel
