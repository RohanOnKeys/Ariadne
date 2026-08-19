"""Tests for ariadne.fetch.celestrak."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from ariadne.exceptions import FetchError
from ariadne.fetch import celestrak

_LINE1 = "1 25544U 98067A   24045.51782528  .00016717  00000-0  10270-3 0  9998"
_LINE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49560684436460"
_TLE_TEXT = f"ISS (ZARYA)\n{_LINE1}\n{_LINE2}\n"


def _fake_response(text, status_ok=True):
    response = MagicMock()
    response.text = text
    if status_ok:
        response.raise_for_status = MagicMock()
    else:
        response.raise_for_status.side_effect = requests.HTTPError("bad status")
    return response


@patch("ariadne.fetch.celestrak.requests.get")
def test_fetch_group_text_queries_by_group(mock_get):
    mock_get.return_value = _fake_response(_TLE_TEXT)

    text = celestrak.fetch_group_text("stations")

    assert text == _TLE_TEXT
    args, kwargs = mock_get.call_args
    assert args[0] == celestrak.BASE_URL
    assert kwargs["params"]["GROUP"] == "stations"
    assert kwargs["params"]["FORMAT"] == "tle"


@patch("ariadne.fetch.celestrak.requests.get")
def test_fetch_group_parses_tles(mock_get):
    mock_get.return_value = _fake_response(_TLE_TEXT)

    tles = celestrak.fetch_group("stations")

    assert len(tles) == 1
    assert tles[0].norad_id == 25544


@patch("ariadne.fetch.celestrak.requests.get")
def test_fetch_norad_id_queries_by_catnr(mock_get):
    mock_get.return_value = _fake_response(_TLE_TEXT)

    tle = celestrak.fetch_norad_id(25544)

    assert tle.norad_id == 25544
    args, kwargs = mock_get.call_args
    assert kwargs["params"]["CATNR"] == 25544


@patch("ariadne.fetch.celestrak.requests.get")
def test_raises_fetch_error_on_network_failure(mock_get):
    mock_get.side_effect = requests.ConnectionError("no route to host")

    with pytest.raises(FetchError):
        celestrak.fetch_group_text("active")


@patch("ariadne.fetch.celestrak.requests.get")
def test_raises_fetch_error_on_bad_status(mock_get):
    mock_get.return_value = _fake_response("", status_ok=False)

    with pytest.raises(FetchError):
        celestrak.fetch_group_text("active")


@patch("ariadne.fetch.celestrak.requests.get")
def test_raises_fetch_error_on_no_gp_data(mock_get):
    mock_get.return_value = _fake_response("No GP data found")

    with pytest.raises(FetchError):
        celestrak.fetch_norad_id_text(99999999)


@patch("ariadne.fetch.celestrak.requests.get")
def test_raises_fetch_error_on_empty_response(mock_get):
    mock_get.return_value = _fake_response("   ")

    with pytest.raises(FetchError):
        celestrak.fetch_group_text("active")
