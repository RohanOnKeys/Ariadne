"""
relative_state.py

Relative position/velocity between two objects at a common epoch, the
shared building block `ric.py` and `probability.py` both start from.
Everything downstream (TCA search, RIC rotation, Pc) works on plain
6-vectors [x, y, z, vx, vy, vz] rather than `SatelliteState`, matching
`propagate/numerical.py`'s own convention.
"""

import numpy as np


def relative_state(primary_state: np.ndarray, secondary_state: np.ndarray) -> tuple:
    """
    Relative position/velocity of the secondary with respect to the
    primary, secondary minus primary. Both states must already be at
    the same epoch and in the same frame (that's what `find_tca`'s
    output already guarantees).

    Args:
        primary_state: primary's 6-vector [x, y, z, vx, vy, vz], km
            and km/s.
        secondary_state: secondary's 6-vector, same frame/epoch.

    Returns:
        (r_rel, v_rel): 3-vectors, km and km/s.
    """
    r_rel = secondary_state[:3] - primary_state[:3]
    v_rel = secondary_state[3:6] - primary_state[3:6]
    return r_rel, v_rel
