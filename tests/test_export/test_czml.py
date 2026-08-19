"""Tests for ariadne.export.czml."""

import json
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from ariadne.conjunction.tca import TCAResult
from ariadne.exceptions import ExportError
from ariadne.export.czml import (
    conjunction_packet,
    document_packet,
    satellite_position_packet,
    to_czml,
)
from ariadne.models.state_vector import Frame, SatelliteState


def _states(norad_id, n=3):
    epoch0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        SatelliteState(
            epoch=epoch0 + timedelta(seconds=60 * i),
            position=np.array([7000.0 + i, 0.0, 0.0]),
            velocity=np.array([0.0, 7.5, 0.0]),
            frame=Frame.ECI,
            norad_id=norad_id,
            name=f"SAT-{norad_id}",
        )
        for i in range(n)
    ]


def _tca():
    return TCAResult(
        epoch=datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc),
        dt=300.0,
        miss_distance=1.5,
        primary_state=np.array([7000.0, 0.0, 0.0, 0.0, 7.5, 0.0]),
        secondary_state=np.array([7000.5, 0.2, 0.0, 0.0, 7.4, 0.05]),
    )


def test_document_packet_sets_clock_interval_from_epochs():
    states = _states(1)
    packet = document_packet("test", states)

    start_iso, stop_iso = packet["clock"]["interval"].split("/")
    assert start_iso == "2026-01-01T00:00:00Z"
    assert stop_iso == "2026-01-01T00:02:00Z"
    assert packet["id"] == "document"


def test_document_packet_rejects_empty_state_list():
    with pytest.raises(ExportError):
        document_packet("test", [])


def test_satellite_position_packet_converts_km_to_metres():
    packet = satellite_position_packet(_states(25544, n=1))

    assert packet["id"] == "satellite/25544"
    assert packet["name"] == "SAT-25544"
    cartesian = packet["position"]["cartesian"]
    assert cartesian[0] == 0.0  # first sample's time offset
    np.testing.assert_allclose(cartesian[1:4], [7000.0 * 1000.0, 0.0, 0.0])


def test_satellite_position_packet_time_tags_are_seconds_from_epoch():
    packet = satellite_position_packet(_states(1, n=3))
    cartesian = packet["position"]["cartesian"]

    # 4 values (t, x, y, z) per sample.
    assert cartesian[0] == 0.0
    assert cartesian[4] == 60.0
    assert cartesian[8] == 120.0


def test_satellite_position_packet_rejects_non_eci_frame():
    states = _states(1, n=1)
    states[0].frame = Frame.ECEF

    with pytest.raises(ExportError):
        satellite_position_packet(states)


def test_satellite_position_packet_rejects_empty_state_list():
    with pytest.raises(ExportError):
        satellite_position_packet([])


def test_conjunction_packet_has_midpoint_and_endpoints():
    tca = _tca()
    packet = conjunction_packet(tca, primary_id="A", secondary_id="B")

    expected_midpoint = (
        (tca.primary_state[:3] + tca.secondary_state[:3]) / 2.0 * 1000.0
    )
    np.testing.assert_allclose(packet["position"]["cartesian"], expected_midpoint)

    polyline = packet["polyline"]["positions"]["cartesian"]
    np.testing.assert_allclose(polyline[:3], tca.primary_state[:3] * 1000.0)
    np.testing.assert_allclose(polyline[3:], tca.secondary_state[:3] * 1000.0)
    assert "1.500" in packet["name"]


def test_to_czml_assembles_document_and_all_packets_as_json_serializable():
    packets = to_czml(
        "test doc",
        [_states(1), _states(2)],
        conjunctions=[("1", "2", _tca())],
    )

    assert packets[0]["id"] == "document"
    ids = [p["id"] for p in packets]
    assert "satellite/1" in ids
    assert "satellite/2" in ids
    assert "conjunction/1-2" in ids
    json.dumps(packets)  # must not raise
