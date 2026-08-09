"""Tests for ariadne.models.measurement."""

from datetime import datetime, timezone

import numpy as np
import pytest

from ariadne.models.measurement import Measurement, MeasurementType


def _epoch():
    return datetime(2024, 2, 14, 12, 0, 0, tzinfo=timezone.utc)


def test_default_type_is_position_velocity():
    m = Measurement(epoch=_epoch(), values=np.zeros(6), covariance=np.eye(6))
    assert m.type is MeasurementType.POSITION_VELOCITY
    assert m.station_id is None


def test_range_az_el_measurement_with_station():
    m = Measurement(
        epoch=_epoch(), values=[500.0, 0.1, 0.5], covariance=np.eye(3) * 0.01,
        type=MeasurementType.RANGE_AZ_EL, station_id="site-1",
    )
    np.testing.assert_array_equal(m.values, [500.0, 0.1, 0.5])
    assert m.station_id == "site-1"


def test_covariance_shape_mismatch_raises():
    with pytest.raises(ValueError):
        Measurement(epoch=_epoch(), values=np.zeros(6), covariance=np.eye(3))


def test_non_vector_values_raises():
    with pytest.raises(ValueError):
        Measurement(epoch=_epoch(), values=np.eye(3), covariance=np.eye(3))
