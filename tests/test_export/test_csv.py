"""Tests for ariadne.export.csv."""

import csv as stdlib_csv
from datetime import datetime, timezone

import numpy as np

from ariadne.conjunction.screening import ScreeningResult
from ariadne.conjunction.tca import TCAResult
from ariadne.export.csv import (
    SCREENING_FIELDS,
    STATE_FIELDS,
    write_screening_results_csv,
    write_states_csv,
)
from ariadne.models.state_vector import Frame, SatelliteState


def _state(norad_id):
    return SatelliteState(
        epoch=datetime(2026, 1, 1, tzinfo=timezone.utc),
        position=np.array([7000.0, 0.0, 0.0]),
        velocity=np.array([0.0, 7.5, 0.0]),
        frame=Frame.ECI,
        norad_id=norad_id,
        name=f"SAT-{norad_id}",
    )


def test_write_states_csv_round_trips(tmp_path):
    states = [_state(1), _state(2)]
    path = tmp_path / "states.csv"

    write_states_csv(states, path)

    with open(path, newline="") as f:
        rows = list(stdlib_csv.DictReader(f))

    assert rows[0].keys() == set(STATE_FIELDS)
    assert len(rows) == 2
    assert rows[0]["norad_id"] == "1"
    assert rows[1]["norad_id"] == "2"
    assert float(rows[0]["x_km"]) == 7000.0
    assert float(rows[0]["vy_km_s"]) == 7.5


def test_write_screening_results_csv_round_trips(tmp_path):
    tca = TCAResult(
        epoch=datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc),
        dt=300.0,
        miss_distance=2.5,
        primary_state=np.zeros(6),
        secondary_state=np.zeros(6),
    )
    results = [ScreeningResult(secondary_norad_id=42, secondary_name="DEBRIS", tca=tca)]
    path = tmp_path / "screening.csv"

    write_screening_results_csv(results, path)

    with open(path, newline="") as f:
        rows = list(stdlib_csv.DictReader(f))

    assert rows[0].keys() == set(SCREENING_FIELDS)
    assert rows[0]["secondary_norad_id"] == "42"
    assert float(rows[0]["miss_distance_km"]) == 2.5
