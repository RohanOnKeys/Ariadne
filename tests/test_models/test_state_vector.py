"""Tests for ariadne.models.state_vector."""

from datetime import datetime, timezone

import numpy as np
import pytest

from ariadne.models.state_vector import Frame, SatelliteState


def _epoch():
    return datetime(2024, 2, 14, 12, 0, 0, tzinfo=timezone.utc)


def test_as_vector_concatenates_position_and_velocity():
    state = SatelliteState(
        epoch=_epoch(),
        position=[1.0, 2.0, 3.0],
        velocity=[4.0, 5.0, 6.0],
        frame=Frame.ECI,
    )
    np.testing.assert_array_equal(state.as_vector(), [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])


def test_from_vector_splits_into_position_and_velocity():
    state = SatelliteState.from_vector(
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], epoch=_epoch(), frame=Frame.TEME,
        norad_id=25544, name="ISS",
    )
    np.testing.assert_array_equal(state.position, [1.0, 2.0, 3.0])
    np.testing.assert_array_equal(state.velocity, [4.0, 5.0, 6.0])
    assert state.frame is Frame.TEME
    assert state.norad_id == 25544
    assert state.name == "ISS"


def test_from_vector_round_trips_with_as_vector():
    vector = np.array([7000.0, 0.0, 0.0, 0.0, 7.5, 0.0])
    state = SatelliteState.from_vector(vector, epoch=_epoch(), frame=Frame.ECEF)
    np.testing.assert_array_equal(state.as_vector(), vector)


def test_wrong_shape_position_raises():
    with pytest.raises(ValueError):
        SatelliteState(
            epoch=_epoch(), position=[1.0, 2.0], velocity=[4.0, 5.0, 6.0], frame=Frame.ECI,
        )


def test_wrong_shape_velocity_raises():
    with pytest.raises(ValueError):
        SatelliteState(
            epoch=_epoch(), position=[1.0, 2.0, 3.0], velocity=[4.0, 5.0], frame=Frame.ECI,
        )
