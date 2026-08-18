"""
tca.py

Time of closest approach (TCA) between two objects: minimize relative
range over a search window via bounded scalar optimization (Brent's
method, as implemented by `scipy.optimize.minimize_scalar`).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
from scipy.optimize import minimize_scalar

from ariadne.propagate.numerical import propagate


@dataclass
class TCAResult:
    """
    Attributes:
        epoch: UTC datetime of closest approach.
        dt: seconds from the reference epoch to TCA (same sign
            convention as the search window it was found in).
        miss_distance: range at TCA, km.
        primary_state: primary's 6-vector [x, y, z, vx, vy, vz] at TCA.
        secondary_state: secondary's 6-vector at TCA.
    """
    epoch: datetime
    dt: float
    miss_distance: float
    primary_state: np.ndarray
    secondary_state: np.ndarray


def _range_at(dt: float, state0_primary: np.ndarray, state0_secondary: np.ndarray,
              include_j2: bool) -> float:
    r_primary = propagate(state0_primary, dt, include_j2=include_j2)[:3]
    r_secondary = propagate(state0_secondary, dt, include_j2=include_j2)[:3]
    return float(np.linalg.norm(r_secondary - r_primary))


def find_tca(
    epoch0: datetime,
    state0_primary: np.ndarray,
    state0_secondary: np.ndarray,
    window: tuple = (-1800.0, 1800.0),
    *,
    include_j2: bool = True,
) -> TCAResult:
    """
    Find the time of closest approach between two objects within
    `window` seconds of `epoch0`, both given as ECI 6-vectors at that
    same reference epoch.

    Well-behaved as long as `window` brackets a single close approach.
    A window spanning multiple orbital periods can contain more than
    one local minimum in range, use a coarse grid search (see
    `screening.py`) to narrow the window to one pass first in that
    case, bounded scalar minimization only finds one minimum per call.

    Args:
        epoch0: reference UTC datetime state0_primary/state0_secondary
            are given at.
        state0_primary, state0_secondary: 6-vectors [x, y, z, vx, vy,
            vz], ECI, km and km/s.
        window: (t_min, t_max) seconds from epoch0 to search within.
        include_j2: passed through to the propagator.

    Returns:
        TCAResult.
    """
    solution = minimize_scalar(
        _range_at,
        bounds=window,
        method="bounded",
        args=(state0_primary, state0_secondary, include_j2),
        options={"xatol": 1e-3},
    )

    dt = float(solution.x)
    primary_state = propagate(state0_primary, dt, include_j2=include_j2)
    secondary_state = propagate(state0_secondary, dt, include_j2=include_j2)
    miss_distance = float(np.linalg.norm(secondary_state[:3] - primary_state[:3]))

    return TCAResult(
        epoch=epoch0 + timedelta(seconds=dt),
        dt=dt,
        miss_distance=miss_distance,
        primary_state=primary_state,
        secondary_state=secondary_state,
    )
