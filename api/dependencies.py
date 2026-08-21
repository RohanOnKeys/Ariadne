"""
dependencies.py

Shared helpers for the API routers: ISO-8601 epoch parsing and
fetch-plus-cache TLE resolution, the same two things
`ariadne/cli/_util.py` and `ariadne/cli/fetch.py` do for the CLI, in
one place so every router calls the same code instead of copies.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException

from ariadne.exceptions import AriadneError
from ariadne.fetch import celestrak, spacetrack
from ariadne.fetch.cache import get_cached
from ariadne.ingest.tle import parse_tle_text
from ariadne.models.tle import TLE

DEFAULT_TTL_HOURS = 6.0

_NORAD_ID_FETCHERS = {
    "celestrak": celestrak.fetch_norad_id_text,
    "spacetrack": spacetrack.fetch_norad_id_text,
}


def parse_epoch(value: Optional[str]) -> datetime:
    """Parse an ISO-8601 UTC epoch query param ('Z' accepted as
    shorthand for '+00:00'); `None` returns the current UTC time."""
    if value is None:
        return datetime.now(timezone.utc)

    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        epoch = datetime.fromisoformat(text)
    except ValueError:
        raise HTTPException(422, f"{value!r} is not a valid ISO-8601 datetime.")
    if epoch.tzinfo is None:
        raise HTTPException(422, f"{value!r} has no UTC offset (append 'Z' or '+00:00').")
    return epoch.astimezone(timezone.utc)


def resolve_tle(
    norad_id: int, provider: str = "celestrak",
    ttl_hours: float = DEFAULT_TTL_HOURS, no_cache: bool = False,
) -> TLE:
    """Fetch (disk-cached, unless `no_cache`) and parse a single
    object's latest TLE by NORAD catalog number.

    Raises:
        AriadneError: the provider request failed or returned nothing
            parsable.
    """
    fetch_text = _NORAD_ID_FETCHERS[provider]
    if no_cache:
        text = fetch_text(norad_id)
    else:
        result = get_cached(
            provider, f"CATNR={norad_id}", lambda: fetch_text(norad_id), ttl_hours=ttl_hours,
        )
        text = result.text

    tles = parse_tle_text(text)
    if not tles:
        raise AriadneError(f"{provider} returned no parsable TLE for NORAD ID {norad_id}.")
    return tles[0]


def format_epoch(epoch: datetime) -> str:
    """UTC datetime -> ISO-8601 string with a 'Z' suffix, the shape
    every JSON response on this API uses for timestamps."""
    return epoch.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def resolve_group(
    group: str, ttl_hours: float = DEFAULT_TTL_HOURS, no_cache: bool = False,
) -> List[TLE]:
    """Fetch (disk-cached, unless `no_cache`) and parse every object in
    a CelesTrak group (e.g. 'active', 'stations', 'starlink'); only
    CelesTrak exposes group lookups, Space-Track is single-object only.

    Raises:
        AriadneError: the request failed or returned nothing parsable.
    """
    if no_cache:
        text = celestrak.fetch_group_text(group)
    else:
        result = get_cached(
            "celestrak", f"GROUP={group}",
            lambda: celestrak.fetch_group_text(group), ttl_hours=ttl_hours,
        )
        text = result.text
    return parse_tle_text(text)
