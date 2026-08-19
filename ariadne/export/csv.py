"""
csv.py

CSV dumps of satellite states and conjunction screening results, the
plain-text counterpart to `export/json.py`'s structured dumps.
"""

import csv
from pathlib import Path
from typing import List, Union

from ariadne.conjunction.screening import ScreeningResult
from ariadne.models.state_vector import SatelliteState

STATE_FIELDS = [
    "epoch", "norad_id", "name", "frame",
    "x_km", "y_km", "z_km", "vx_km_s", "vy_km_s", "vz_km_s",
]

SCREENING_FIELDS = [
    "secondary_norad_id", "secondary_name", "tca_epoch", "miss_distance_km",
]


def write_states_csv(states: List[SatelliteState], path: Union[str, Path]) -> None:
    """Write one row per `SatelliteState`, columns per `STATE_FIELDS`."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(STATE_FIELDS)
        for state in states:
            writer.writerow([
                state.epoch.isoformat(), state.norad_id, state.name, state.frame.value,
                *state.position, *state.velocity,
            ])


def write_screening_results_csv(
    results: List[ScreeningResult], path: Union[str, Path],
) -> None:
    """Write one row per `ScreeningResult`, columns per
    `SCREENING_FIELDS`, in the order given (callers wanting ascending
    miss distance should sort before calling, as `screen_catalog`
    already returns)."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(SCREENING_FIELDS)
        for result in results:
            writer.writerow([
                result.secondary_norad_id, result.secondary_name,
                result.tca.epoch.isoformat(), result.tca.miss_distance,
            ])
