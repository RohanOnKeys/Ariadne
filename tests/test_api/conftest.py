"""Shared fixtures for the API test suite."""

from unittest.mock import MagicMock

import pytest
import requests
from fastapi.testclient import TestClient

from api.app import app

ISS_LINE1 = "1 25544U 98067A   24045.51782528  .00016717  00000-0  10270-3 0  9998"
ISS_LINE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49560684436460"
ISS_TEXT = f"ISS (ZARYA)\n{ISS_LINE1}\n{ISS_LINE2}\n"

VANGUARD_LINE1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
VANGUARD_LINE2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"

GROUP_TEXT = (
    f"ISS (ZARYA)\n{ISS_LINE1}\n{ISS_LINE2}\n"
    f"VANGUARD 1\n{VANGUARD_LINE1}\n{VANGUARD_LINE2}\n"
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def fake_response(text: str, status_ok: bool = True) -> MagicMock:
    response = MagicMock()
    response.text = text
    if status_ok:
        response.raise_for_status = MagicMock()
    else:
        response.raise_for_status.side_effect = requests.HTTPError("bad status")
    return response


def celestrak_router(catnr_text: str, group_text: str):
    """A `requests.get` side_effect that replies by CATNR or GROUP param,
    the same request celestrak.py issues for norad-id vs. group fetches."""
    def _side_effect(*_args, params: dict, **_kwargs):
        if "CATNR" in params:
            return fake_response(catnr_text)
        return fake_response(group_text)
    return _side_effect
