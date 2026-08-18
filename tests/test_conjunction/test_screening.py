"""Tests for ariadne.conjunction.screening."""

from datetime import datetime, timezone

import numpy as np

from ariadne.conjunction.screening import screen_catalog
from ariadne.conjunction.tca import find_tca
from ariadne.models.orbit import KeplerianElements, coe_to_rv

_EPOCH0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_WINDOW = (-1500.0, 1500.0)


def _state(true_anomaly: float, inclination: float) -> np.ndarray:
    r, v = coe_to_rv(KeplerianElements(
        a=7000.0, e=0.05, i=inclination, raan=0.5, arg_perigee=0.7,
        true_anomaly=true_anomaly,
    ))
    return np.concatenate([r, v])


def test_screen_catalog_filters_by_threshold_and_sorts_ascending():
    primary = _state(true_anomaly=0.0, inclination=0.3)
    secondaries = [
        (10001, "CLOSE", _state(true_anomaly=0.02, inclination=0.31)),
        (10002, "FAR", _state(true_anomaly=1.0, inclination=0.9)),
        (10003, "MEDIUM", _state(true_anomaly=0.05, inclination=0.35)),
    ]

    expected = {
        norad_id: find_tca(_EPOCH0, primary, state, _WINDOW, include_j2=False).miss_distance
        for norad_id, _, state in secondaries
    }
    threshold_km = sorted(expected.values())[1] + 1.0  # keeps the two closest, drops the farthest

    results = screen_catalog(
        _EPOCH0, primary, secondaries, threshold_km, _WINDOW, include_j2=False,
    )

    assert [r.secondary_norad_id for r in results] == sorted(
        (nid for nid in expected if expected[nid] <= threshold_km),
        key=lambda nid: expected[nid],
    )
    assert all(r.tca.miss_distance <= threshold_km for r in results)
    assert all(a.tca.miss_distance <= b.tca.miss_distance for a, b in zip(results, results[1:]))


def test_screen_catalog_returns_empty_when_nothing_within_threshold():
    primary = _state(true_anomaly=0.0, inclination=0.3)
    secondaries = [(10001, "FAR", _state(true_anomaly=2.0, inclination=1.2))]

    results = screen_catalog(_EPOCH0, primary, secondaries, 0.001, _WINDOW, include_j2=False)

    assert results == []
