"""Tests for ariadne.export.json."""

import json as stdlib_json
from datetime import datetime, timezone

import numpy as np
import pytest

from ariadne.conjunction.screening import ScreeningResult
from ariadne.conjunction.tca import TCAResult
from ariadne.export.json import (
    orbit_to_dict,
    screening_result_to_dict,
    state_to_dict,
    tca_to_dict,
    write_json,
)
from ariadne.models.orbit import KeplerianElements
from ariadne.models.state_vector import Frame, SatelliteState


def _state():
    return SatelliteState(
        epoch=datetime(2026, 1, 1, tzinfo=timezone.utc),
        position=np.array([7000.0, 0.0, 0.0]),
        velocity=np.array([0.0, 7.5, 0.0]),
        frame=Frame.ECI,
        norad_id=25544,
        name="ISS (ZARYA)",
    )


def _tca_result():
    return TCAResult(
        epoch=datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc),
        dt=600.0,
        miss_distance=1.234,
        primary_state=np.array([7000.0, 0.0, 0.0, 0.0, 7.5, 0.0]),
        secondary_state=np.array([7001.0, 0.5, 0.0, 0.0, 7.4, 0.1]),
    )


def test_state_to_dict_is_json_serializable_and_round_trips_values():
    state = _state()
    d = state_to_dict(state)

    stdlib_json.dumps(d)  # must not raise
    assert d["norad_id"] == 25544
    assert d["name"] == "ISS (ZARYA)"
    assert d["frame"] == "ECI"
    assert d["position_km"] == [7000.0, 0.0, 0.0]
    assert d["epoch"] == "2026-01-01T00:00:00Z"


def test_orbit_to_dict_includes_derived_quantities():
    elements = KeplerianElements(
        a=7000.0, e=0.001, i=0.9, raan=0.1, arg_perigee=0.2, true_anomaly=0.3,
    )
    d = orbit_to_dict(elements)

    stdlib_json.dumps(d)
    assert d["semi_major_axis_km"] == 7000.0
    assert d["period_s"] == pytest.approx(elements.period)
    assert d["apogee_altitude_km"] == pytest.approx(elements.apogee_altitude)


def test_tca_to_dict_round_trips_values():
    result = _tca_result()
    d = tca_to_dict(result)

    stdlib_json.dumps(d)
    assert d["miss_distance_km"] == 1.234
    assert d["dt_s"] == 600.0
    assert d["primary_state_km"] == result.primary_state.tolist()


def test_screening_result_to_dict_nests_tca():
    result = ScreeningResult(secondary_norad_id=99999, secondary_name="DEBRIS", tca=_tca_result())
    d = screening_result_to_dict(result)

    stdlib_json.dumps(d)
    assert d["secondary_norad_id"] == 99999
    assert d["tca"]["miss_distance_km"] == 1.234


def test_write_json_round_trips_through_disk(tmp_path):
    payload = [state_to_dict(_state())]
    path = tmp_path / "states.json"

    write_json(payload, path)

    assert stdlib_json.loads(path.read_text()) == payload
