"""
plots.py

Matplotlib ground-track and RIC-plane plots, for static reports rather
than the live dashboard (which reads `czml.py`'s output instead).
Requires the `plots` extra (`pip install ariadne[plots]`).
"""

from typing import List, Optional

import numpy as np

from ariadne.conjunction.relative_state import relative_state
from ariadne.conjunction.ric import eci_to_ric
from ariadne.conjunction.tca import TCAResult
from ariadne.exceptions import ExportError
from ariadne.models.state_vector import Frame, SatelliteState
from ariadne.propagate.frames import ecef_to_geodetic

try:
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover, exercised only without the extra installed.
    raise ExportError(
        "plots.py requires matplotlib; install with `pip install ariadne[plots]`."
    ) from exc


def plot_ground_track(states: List[SatelliteState], ax: Optional["plt.Axes"] = None):
    """
    Ground track (longitude vs. latitude) from a chronological list of
    ECEF states for one object.

    Args:
        states: one object's states over time, all ECEF.
        ax: axes to draw on; a new figure/axes is created if omitted.

    Returns:
        The `Axes` the track was drawn on.

    Raises:
        ExportError: `states` is empty or not all in the ECEF frame.
    """
    if not states:
        raise ExportError("Cannot plot a ground track from an empty state list.")
    if any(state.frame != Frame.ECEF for state in states):
        raise ExportError(
            "plot_ground_track requires ECEF states; convert with "
            "propagate/frames.py first."
        )

    if ax is None:
        _, ax = plt.subplots()

    lon_deg, lat_deg = [], []
    for state in states:
        lat, lon, _ = ecef_to_geodetic(state.position)
        lat_deg.append(np.degrees(lat))
        lon_deg.append(np.degrees(lon))

    ax.plot(lon_deg, lat_deg, ".", markersize=2)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel("Longitude (deg)")
    ax.set_ylabel("Latitude (deg)")
    ax.set_title(states[0].name or "Ground track")

    return ax


def plot_ric(tca: TCAResult, hard_body_radius: float, ax: Optional["plt.Axes"] = None):
    """
    Radial/in-track relative-position plot at TCA: the miss point plus
    a hard-body-radius circle, the standard "how close did it actually
    come" conjunction report view.

    Args:
        tca: the TCA result to visualize.
        hard_body_radius: combined hard-body radius, km, drawn as a
            circle around the origin (the primary).
        ax: axes to draw on; a new figure/axes is created if omitted.

    Returns:
        The `Axes` the plot was drawn on.
    """
    r_rel, v_rel = relative_state(tca.primary_state, tca.secondary_state)
    r_ric, _ = eci_to_ric(r_rel, v_rel, tca.primary_state[:3], tca.primary_state[3:6])

    if ax is None:
        _, ax = plt.subplots()

    ax.plot(0.0, 0.0, "k+", label="Primary")
    ax.plot(r_ric[1], r_ric[0], "rx", label=f"Secondary ({tca.miss_distance:.3f} km miss)")
    circle = plt.Circle((0.0, 0.0), hard_body_radius, fill=False, linestyle="--", color="gray")
    ax.add_patch(circle)

    ax.set_xlabel("In-track (km)")
    ax.set_ylabel("Radial (km)")
    ax.set_aspect("equal")
    ax.legend()
    ax.set_title(f"RIC at TCA ({tca.epoch.isoformat()})")

    return ax
