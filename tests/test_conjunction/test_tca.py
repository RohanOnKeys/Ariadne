"""Tests for ariadne.conjunction.tca."""

from datetime import datetime, timedelta, timezone

import numpy as np

from ariadne.conjunction.tca import find_tca
from ariadne.models.orbit import KeplerianElements, coe_to_rv
from ariadne.propagate.numerical import propagate

_EPOCH0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_WINDOW = (-1500.0, 1500.0)


def _state(true_anomaly: float, inclination: float = 0.3) -> np.ndarray:
    r, v = coe_to_rv(KeplerianElements(
        a=7000.0, e=0.05, i=inclination, raan=0.5, arg_perigee=0.7,
        true_anomaly=true_anomaly,
    ))
    return np.concatenate([r, v])


def test_tca_is_a_local_minimum_of_range():
    primary = _state(true_anomaly=0.0)
    secondary = _state(true_anomaly=0.05, inclination=0.35)

    result = find_tca(_EPOCH0, primary, secondary, _WINDOW, include_j2=False)

    def range_at(dt):
        r_p = propagate(primary, dt, include_j2=False)[:3]
        r_s = propagate(secondary, dt, include_j2=False)[:3]
        return np.linalg.norm(r_s - r_p)

    assert range_at(result.dt - 1.0) >= result.miss_distance - 1e-9
    assert range_at(result.dt + 1.0) >= result.miss_distance - 1e-9


def test_tca_matches_a_coarse_grid_search():
    primary = _state(true_anomaly=0.0)
    secondary = _state(true_anomaly=0.05, inclination=0.35)

    result = find_tca(_EPOCH0, primary, secondary, _WINDOW, include_j2=False)

    grid = np.linspace(_WINDOW[0], _WINDOW[1], 301)
    ranges = [
        np.linalg.norm(
            propagate(secondary, dt, include_j2=False)[:3]
            - propagate(primary, dt, include_j2=False)[:3]
        )
        for dt in grid
    ]
    grid_min_dt = grid[int(np.argmin(ranges))]

    assert result.miss_distance <= min(ranges) + 1e-6
    assert abs(result.dt - grid_min_dt) < (grid[1] - grid[0])


def test_tca_epoch_matches_dt_offset():
    primary = _state(true_anomaly=0.0)
    secondary = _state(true_anomaly=0.05, inclination=0.35)

    result = find_tca(_EPOCH0, primary, secondary, _WINDOW, include_j2=False)

    assert result.epoch == _EPOCH0 + timedelta(seconds=result.dt)


def test_tca_states_match_direct_propagation():
    primary = _state(true_anomaly=0.0)
    secondary = _state(true_anomaly=0.05, inclination=0.35)

    result = find_tca(_EPOCH0, primary, secondary, _WINDOW, include_j2=False)

    np.testing.assert_allclose(
        result.primary_state, propagate(primary, result.dt, include_j2=False),
    )
    np.testing.assert_allclose(
        result.secondary_state, propagate(secondary, result.dt, include_j2=False),
    )
