"""Tests for ariadne.export.plots."""

from datetime import datetime, timezone

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

from ariadne.conjunction.tca import TCAResult  # noqa: E402
from ariadne.exceptions import ExportError  # noqa: E402
from ariadne.export.plots import plot_ground_track, plot_ric  # noqa: E402
from ariadne.models.state_vector import Frame, SatelliteState  # noqa: E402
from ariadne.propagate.frames import geodetic_to_ecef  # noqa: E402


def _ecef_states():
    epoch = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        SatelliteState(
            epoch=epoch,
            position=geodetic_to_ecef(np.radians(lat), np.radians(lon), 500.0),
            velocity=np.array([0.0, 0.0, 0.0]),
            frame=Frame.ECEF,
            norad_id=1,
            name="TEST",
        )
        for lat, lon in [(0.0, 0.0), (10.0, 20.0), (-5.0, 40.0)]
    ]


def test_plot_ground_track_returns_axes_with_expected_bounds():
    ax = plot_ground_track(_ecef_states())

    assert ax.get_xlim() == (-180.0, 180.0)
    assert ax.get_ylim() == (-90.0, 90.0)


def test_plot_ground_track_rejects_non_ecef_frame():
    states = _ecef_states()
    states[0].frame = Frame.ECI

    with pytest.raises(ExportError):
        plot_ground_track(states)


def test_plot_ground_track_rejects_empty_state_list():
    with pytest.raises(ExportError):
        plot_ground_track([])


def test_plot_ric_plots_the_miss_point():
    tca = TCAResult(
        epoch=datetime(2026, 1, 1, tzinfo=timezone.utc),
        dt=0.0,
        miss_distance=1.0,
        primary_state=np.array([7000.0, 0.0, 0.0, 0.0, 7.5, 0.0]),
        secondary_state=np.array([7000.0, 1.0, 0.0, 0.0, 7.5, 0.0]),
    )

    ax = plot_ric(tca, hard_body_radius=0.02)

    assert ax.get_xlabel() == "In-track (km)"
    assert ax.get_ylabel() == "Radial (km)"
    # One line for the primary marker, one for the secondary marker.
    assert len(ax.lines) == 2
