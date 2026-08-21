"""Tests for GET /objects/{norad_id}/state and /orbit.czml."""

from unittest.mock import patch

from tests.test_api.conftest import ISS_TEXT


@patch("ariadne.fetch.celestrak.requests.get")
def test_get_object_state(mock_get, client):
    mock_get.return_value.text = ISS_TEXT
    mock_get.return_value.raise_for_status = lambda: None

    response = client.get(
        "/objects/25544/state",
        params={"epoch": "2024-02-14T12:00:00Z", "no_cache": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["norad_id"] == 25544
    assert body["frame"] == "ECI"
    assert len(body["position_km"]) == 3
    assert len(body["velocity_km_s"]) == 3


@patch("ariadne.fetch.celestrak.requests.get")
def test_get_object_state_defaults_epoch_to_now(mock_get, client):
    mock_get.return_value.text = ISS_TEXT
    mock_get.return_value.raise_for_status = lambda: None

    response = client.get("/objects/25544/state", params={"no_cache": True})

    assert response.status_code == 200


@patch("ariadne.fetch.celestrak.requests.get")
def test_get_object_czml(mock_get, client):
    mock_get.return_value.text = ISS_TEXT
    mock_get.return_value.raise_for_status = lambda: None

    response = client.get(
        "/objects/25544/orbit.czml",
        params={
            "epoch": "2024-02-14T12:00:00Z", "duration_s": 120, "step_s": 60, "no_cache": True,
        },
    )

    assert response.status_code == 200
    packets = response.json()
    assert packets[0]["id"] == "document"
    assert packets[1]["id"] == "satellite/25544"
    assert len(packets[1]["position"]["cartesian"]) == 3 * 4  # 3 samples, [t, x, y, z] per step


def test_get_object_czml_rejects_too_many_samples(client):
    response = client.get(
        "/objects/25544/orbit.czml",
        params={"duration_s": 1_000_000, "step_s": 0.01, "no_cache": True},
    )

    assert response.status_code == 422


def test_get_object_state_rejects_unknown_provider(client):
    response = client.get("/objects/25544/state", params={"provider": "not-a-provider"})

    assert response.status_code == 422


def test_get_object_state_rejects_bad_epoch(client):
    response = client.get("/objects/25544/state", params={"epoch": "not-a-date"})

    assert response.status_code == 422
