"""
catalog.py

GET /catalog: every object in a CelesTrak group, disk-cached, the
dashboard's object list / count.
"""

from fastapi import APIRouter, Query

from api.dependencies import DEFAULT_TTL_HOURS, format_epoch, resolve_group

router = APIRouter()


@router.get("/catalog")
def get_catalog(
    group: str = Query("stations", description="CelesTrak group name, e.g. 'active', 'stations'."),
    ttl_hours: float = Query(DEFAULT_TTL_HOURS, description="Cache freshness window, hours."),
    no_cache: bool = Query(False, description="Bypass the cache and force a fresh fetch."),
) -> list:
    tles = resolve_group(group, ttl_hours=ttl_hours, no_cache=no_cache)
    return [
        {"norad_id": tle.norad_id, "name": tle.name, "epoch": format_epoch(tle.epoch)}
        for tle in tles
    ]
