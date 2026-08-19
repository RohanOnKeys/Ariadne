"""
json.py

Structured JSON dumps of satellite states, orbit parameters, and
conjunction results, the same shapes the (future) API layer serves
directly. Every numpy array and datetime is converted to a plain
list/ISO-8601 string before handing off to the standard `json` module,
so no custom encoder is needed.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Union

from ariadne.conjunction.screening import ScreeningResult
from ariadne.conjunction.tca import TCAResult
from ariadne.models.orbit import KeplerianElements
from ariadne.models.state_vector import SatelliteState


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def state_to_dict(state: SatelliteState) -> dict:
    """`SatelliteState` -> JSON-serializable dict."""
    return {
        "epoch": _iso(state.epoch),
        "position_km": state.position.tolist(),
        "velocity_km_s": state.velocity.tolist(),
        "frame": state.frame.value,
        "norad_id": state.norad_id,
        "name": state.name,
    }


def orbit_to_dict(elements: KeplerianElements) -> dict:
    """`KeplerianElements` -> JSON-serializable dict, the "Orbit
    Parameters" panel's shape."""
    return {
        "semi_major_axis_km": elements.a,
        "eccentricity": elements.e,
        "inclination_rad": elements.i,
        "raan_rad": elements.raan,
        "arg_perigee_rad": elements.arg_perigee,
        "true_anomaly_rad": elements.true_anomaly,
        "mean_anomaly_rad": elements.mean_anomaly,
        "period_s": elements.period,
        "apogee_altitude_km": elements.apogee_altitude,
        "perigee_altitude_km": elements.perigee_altitude,
    }


def tca_to_dict(result: TCAResult) -> dict:
    """`TCAResult` -> JSON-serializable dict."""
    return {
        "epoch": _iso(result.epoch),
        "dt_s": result.dt,
        "miss_distance_km": result.miss_distance,
        "primary_state_km": result.primary_state.tolist(),
        "secondary_state_km": result.secondary_state.tolist(),
    }


def screening_result_to_dict(result: ScreeningResult) -> dict:
    """`ScreeningResult` -> JSON-serializable dict."""
    return {
        "secondary_norad_id": result.secondary_norad_id,
        "secondary_name": result.secondary_name,
        "tca": tca_to_dict(result.tca),
    }


def write_json(obj: Union[dict, List[dict]], path: Union[str, Path]) -> None:
    """Write a JSON-serializable object (as built by the `*_to_dict`
    functions above) to `path`, pretty-printed."""
    Path(path).write_text(json.dumps(obj, indent=2))
