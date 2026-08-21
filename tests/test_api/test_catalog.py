"""Tests for GET /catalog."""

from unittest.mock import patch

from tests.test_api.conftest import GROUP_TEXT


@patch("ariadne.fetch.celestrak.requests.get")
def test_get_catalog_returns_parsed_group(mock_get, client):
    mock_get.return_value.text = GROUP_TEXT
    mock_get.return_value.raise_for_status = lambda: None

    response = client.get("/catalog", params={"group": "stations", "no_cache": True})

    assert response.status_code == 200
    body = response.json()
    assert {obj["norad_id"] for obj in body} == {25544, 5}
    assert all({"norad_id", "name", "epoch"} <= obj.keys() for obj in body)


@patch("ariadne.fetch.celestrak.requests.get")
def test_get_catalog_maps_fetch_error_to_502(mock_get, client):
    mock_get.return_value.text = ""
    mock_get.return_value.raise_for_status = lambda: None

    response = client.get("/catalog", params={"group": "empty-group", "no_cache": True})

    assert response.status_code == 502
    assert "detail" in response.json()
