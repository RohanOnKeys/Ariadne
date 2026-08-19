"""Fetch: live catalog retrieval from CelesTrak/Space-Track, disk-cached."""

from ariadne.fetch.cache import CachedResult, get_cached
from ariadne.fetch.celestrak import fetch_group, fetch_norad_id

__all__ = [
    "fetch_group",
    "fetch_norad_id",
    "get_cached",
    "CachedResult",
]
