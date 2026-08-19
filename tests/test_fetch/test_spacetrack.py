"""Tests for ariadne.fetch.spacetrack."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from ariadne.exceptions import FetchError
from ariadne.fetch import spacetrack

_LINE1 = "1 25544U 98067A   24045.51782528  .00016717  00000-0  10270-3 0  9998"
_LINE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49560684436460"
_TLE_TEXT = f"{_LINE1}\n{_LINE2}\n"


def _fake_response(text, status_ok=True):
    response = MagicMock()
    response.text = text
    if status_ok:
        response.raise_for_status = MagicMock()
    else:
        response.raise_for_status.side_effect = requests.HTTPError("bad status")
    return response


def test_raises_fetch_error_when_credentials_missing():
    with patch.object(spacetrack, "SPACETRACK_USERNAME", None), \
         patch.object(spacetrack, "SPACETRACK_PASSWORD", None):
        with pytest.raises(FetchError, match="credentials"):
            spacetrack.fetch_norad_id_text(25544)


@patch("ariadne.fetch.spacetrack.requests.Session")
def test_fetch_norad_id_text_logs_in_then_queries(mock_session_cls):
    mock_session = MagicMock()
    mock_session.post.return_value = _fake_response("")
    mock_session.get.return_value = _fake_response(_TLE_TEXT)
    mock_session_cls.return_value = mock_session

    with patch.object(spacetrack, "SPACETRACK_USERNAME", "user"), \
         patch.object(spacetrack, "SPACETRACK_PASSWORD", "pass"):
        text = spacetrack.fetch_norad_id_text(25544)

    assert text == _TLE_TEXT
    mock_session.post.assert_called_once()
    login_kwargs = mock_session.post.call_args
    assert login_kwargs[0][0] == spacetrack.LOGIN_URL
    assert login_kwargs[1]["data"] == {"identity": "user", "password": "pass"}
    mock_session.get.assert_called_once()
    assert "25544" in mock_session.get.call_args[0][0]


@patch("ariadne.fetch.spacetrack.requests.Session")
def test_fetch_norad_id_parses_tle(mock_session_cls):
    mock_session = MagicMock()
    mock_session.post.return_value = _fake_response("")
    mock_session.get.return_value = _fake_response(_TLE_TEXT)
    mock_session_cls.return_value = mock_session

    with patch.object(spacetrack, "SPACETRACK_USERNAME", "user"), \
         patch.object(spacetrack, "SPACETRACK_PASSWORD", "pass"):
        tle = spacetrack.fetch_norad_id(25544)

    assert tle.norad_id == 25544


@patch("ariadne.fetch.spacetrack.requests.Session")
def test_raises_fetch_error_on_login_failure(mock_session_cls):
    mock_session = MagicMock()
    mock_session.post.side_effect = requests.ConnectionError("unreachable")
    mock_session_cls.return_value = mock_session

    with patch.object(spacetrack, "SPACETRACK_USERNAME", "user"), \
         patch.object(spacetrack, "SPACETRACK_PASSWORD", "pass"):
        with pytest.raises(FetchError):
            spacetrack.fetch_norad_id_text(25544)


@patch("ariadne.fetch.spacetrack.requests.Session")
def test_raises_fetch_error_on_empty_query_response(mock_session_cls):
    mock_session = MagicMock()
    mock_session.post.return_value = _fake_response("")
    mock_session.get.return_value = _fake_response("")
    mock_session_cls.return_value = mock_session

    with patch.object(spacetrack, "SPACETRACK_USERNAME", "user"), \
         patch.object(spacetrack, "SPACETRACK_PASSWORD", "pass"):
        with pytest.raises(FetchError):
            spacetrack.fetch_norad_id_text(99999999)
