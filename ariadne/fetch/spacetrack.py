"""
spacetrack.py

Space-Track's authenticated query API: POST credentials to
/ajaxauth/login for a session cookie, then GET the query URL with that
cookie attached. Credentials come from `config/settings.py`
(the `SPACETRACK_USERNAME`/`SPACETRACK_PASSWORD` environment
variables), never from a function argument, so they can't end up in a
CLI arg list or shell history.
"""

import requests

from ariadne.config.settings import SPACETRACK_PASSWORD, SPACETRACK_USERNAME
from ariadne.exceptions import FetchError
from ariadne.ingest.tle import parse_tle_text
from ariadne.models.tle import TLE

LOGIN_URL = "https://www.space-track.org/ajaxauth/login"
_QUERY_URL_TEMPLATE = (
    "https://www.space-track.org/basicspacedata/query/class/gp/"
    "NORAD_CAT_ID/{norad_id}/orderby/EPOCH%20desc/limit/1/format/tle"
)
_TIMEOUT_S = 30


def _authenticated_session() -> requests.Session:
    if not SPACETRACK_USERNAME or not SPACETRACK_PASSWORD:
        raise FetchError(
            "Space-Track credentials not set, set SPACETRACK_USERNAME and "
            "SPACETRACK_PASSWORD (see .env.example)."
        )

    session = requests.Session()
    try:
        response = session.post(
            LOGIN_URL,
            data={"identity": SPACETRACK_USERNAME, "password": SPACETRACK_PASSWORD},
            timeout=_TIMEOUT_S,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"Space-Track login failed: {exc}") from exc

    return session


def fetch_norad_id_text(norad_id: int) -> str:
    """Authenticate and fetch the latest TLE for a single object by
    NORAD catalog number, as raw TLE text.

    Raises:
        FetchError: credentials are missing, login failed, or the
            query request failed.
    """
    session = _authenticated_session()
    try:
        response = session.get(_QUERY_URL_TEMPLATE.format(norad_id=norad_id), timeout=_TIMEOUT_S)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"Space-Track query failed: {exc}") from exc

    text = response.text.strip()
    if not text:
        raise FetchError(f"Space-Track returned no data for NORAD ID {norad_id}.")

    return response.text


def fetch_norad_id(norad_id: int) -> TLE:
    """Authenticate, fetch, and parse the latest TLE for a single
    object by NORAD catalog number.

    Raises:
        FetchError: see `fetch_norad_id_text`, or the response had no
            parsable TLE.
    """
    tles = parse_tle_text(fetch_norad_id_text(norad_id))
    if not tles:
        raise FetchError(f"Space-Track returned no parsable TLE for NORAD ID {norad_id}.")
    return tles[0]
