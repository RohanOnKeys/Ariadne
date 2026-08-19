"""
celestrak.py

CelesTrak's free, unauthenticated GP (General Perturbations) element
API: https://celestrak.org/NORAD/elements/gp.php. Group and individual
NORAD ID lookups. This module's only job is the HTTP request and
turning a bad response into `FetchError`; parsing is `ingest/tle.py`'s.
"""

from typing import List

import requests

from ariadne.exceptions import FetchError
from ariadne.ingest.tle import parse_tle_text
from ariadne.models.tle import TLE

BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"
_TIMEOUT_S = 15


def _get(params: dict) -> str:
    try:
        response = requests.get(
            BASE_URL, params={**params, "FORMAT": "tle"}, timeout=_TIMEOUT_S,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"CelesTrak request failed: {exc}") from exc

    text = response.text.strip()
    if not text or text.upper().startswith("NO GP DATA FOUND"):
        raise FetchError(f"CelesTrak returned no data for {params}.")

    return response.text


def fetch_group_text(group: str) -> str:
    """Fetch every object in a CelesTrak group (e.g. 'active',
    'stations', 'starlink') as raw TLE text."""
    return _get({"GROUP": group})


def fetch_group(group: str) -> List[TLE]:
    """Fetch and parse every object in a CelesTrak group.

    Raises:
        FetchError: the request failed or CelesTrak returned no data.
    """
    return parse_tle_text(fetch_group_text(group))


def fetch_norad_id_text(norad_id: int) -> str:
    """Fetch a single object's raw TLE text by NORAD catalog number."""
    return _get({"CATNR": norad_id})


def fetch_norad_id(norad_id: int) -> TLE:
    """Fetch and parse a single object by NORAD catalog number.

    Raises:
        FetchError: the request failed, CelesTrak returned no data, or
            the response had no parsable TLE.
    """
    tles = parse_tle_text(fetch_norad_id_text(norad_id))
    if not tles:
        raise FetchError(f"CelesTrak returned no parsable TLE for NORAD ID {norad_id}.")
    return tles[0]
