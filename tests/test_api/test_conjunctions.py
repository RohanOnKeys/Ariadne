"""Tests for GET /conjunctions/screen and /conjunctions/next."""

from unittest.mock import patch

from tests.test_api.conftest import GROUP_TEXT, ISS_TEXT, celestrak_router


@patch("ariadne.fetch.celestrak.requests.get")
def test_get_conjunctions_screen_excludes_primary_and_reports_secondary(mock_get, client):
    mock_get.side_effect = celestrak_router(ISS_TEXT, GROUP_TEXT)

    response = client.get("/conjunctions/screen", params={
        "primary_id": 25544, "group": "stations", "epoch": "2024-02-14T12:00:00Z",
        "threshold_km": 1.0e8, "no_cache": True,
    })

    assert response.status_code == 200
    body = response.json()
    assert [r["secondary_norad_id"] for r in body] == [5]


@patch("ariadne.fetch.celestrak.requests.get")
def test_get_conjunctions_next_returns_closest(mock_get, client):
    mock_get.side_effect = celestrak_router(ISS_TEXT, GROUP_TEXT)

    response = client.get("/conjunctions/next", params={
        "primary_id": 25544, "group": "stations", "epoch": "2024-02-14T12:00:00Z", "no_cache": True,
    })

    assert response.status_code == 200
    body = response.json()
    assert body["secondary_norad_id"] == 5
    assert "tca" in body


@patch("ariadne.fetch.celestrak.requests.get")
def test_get_conjunctions_next_404s_when_catalog_is_only_the_primary(mock_get, client):
    mock_get.side_effect = celestrak_router(ISS_TEXT, ISS_TEXT)

    response = client.get("/conjunctions/next", params={
        "primary_id": 25544, "group": "stations", "epoch": "2024-02-14T12:00:00Z", "no_cache": True,
    })

    assert response.status_code == 404


@patch("ariadne.fetch.celestrak.requests.get")
def test_get_conjunctions_screen_empty_below_threshold(mock_get, client):
    mock_get.side_effect = celestrak_router(ISS_TEXT, GROUP_TEXT)

    response = client.get("/conjunctions/screen", params={
        "primary_id": 25544, "group": "stations", "epoch": "2024-02-14T12:00:00Z",
        "threshold_km": 0.0001, "no_cache": True,
    })

    assert response.status_code == 200
    assert response.json() == []


def test_get_conjunctions_screen_requires_threshold(client):
    response = client.get("/conjunctions/screen", params={"primary_id": 25544})

    assert response.status_code == 422
