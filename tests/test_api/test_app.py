"""Tests for app-level wiring: health check and AriadneError -> HTTP mapping."""

from unittest.mock import patch

from tests.test_api.conftest import fake_response


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("ariadne.fetch.celestrak.requests.get")
def test_fetch_error_maps_to_502(mock_get, client):
    response = fake_response("", status_ok=False)
    mock_get.return_value = response

    result = client.get("/objects/25544/state", params={"no_cache": True})

    assert result.status_code == 502
    assert "detail" in result.json()


@patch("ariadne.fetch.celestrak.requests.get")
def test_ingest_error_maps_to_400(mock_get, client):
    mock_get.return_value = fake_response("garbage, not a TLE\n")

    result = client.get("/objects/25544/state", params={"no_cache": True})

    assert result.status_code == 400
    assert "detail" in result.json()
