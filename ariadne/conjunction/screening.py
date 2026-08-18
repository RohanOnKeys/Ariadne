"""
screening.py

Screen a catalog of secondary objects against one primary object for
close approaches within a miss-distance threshold, drives the CLI's
`--threshold-km` option and the "Next Close Approach" panel.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np

from ariadne.conjunction.tca import TCAResult, find_tca


@dataclass
class ScreeningResult:
    """
    Attributes:
        secondary_norad_id: catalog number of the screened object, if
            known.
        secondary_name: object name, if known.
        tca: the TCAResult for this primary/secondary pair.
    """
    secondary_norad_id: Optional[int]
    secondary_name: Optional[str]
    tca: TCAResult


def screen_catalog(
    epoch0: datetime,
    primary_state: np.ndarray,
    secondaries: List[Tuple[Optional[int], Optional[str], np.ndarray]],
    threshold_km: float,
    window: tuple = (-1800.0, 1800.0),
    *,
    include_j2: bool = True,
) -> List[ScreeningResult]:
    """
    Find every secondary in `secondaries` whose TCA miss distance
    against `primary_state` is at or below `threshold_km`.

    Args:
        epoch0: reference UTC datetime `primary_state` and every
            secondary state is given at.
        primary_state: primary's 6-vector [x, y, z, vx, vy, vz], ECI,
            km and km/s.
        secondaries: (norad_id, name, state) per candidate secondary,
            each state a 6-vector at `epoch0`, same frame as
            `primary_state`.
        threshold_km: only return pairs with miss distance at or below
            this.
        window: TCA search window, seconds from epoch0, passed to
            `find_tca` for every secondary.
        include_j2: passed through to the propagator.

    Returns:
        Matching ScreeningResults, ascending miss distance.
    """
    results = []
    for norad_id, name, state in secondaries:
        tca = find_tca(epoch0, primary_state, state, window, include_j2=include_j2)
        if tca.miss_distance <= threshold_km:
            results.append(ScreeningResult(norad_id, name, tca))

    results.sort(key=lambda result: result.tca.miss_distance)
    return results
