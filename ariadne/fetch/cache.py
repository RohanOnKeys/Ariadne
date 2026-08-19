"""
cache.py

Disk cache in front of fetch/celestrak.py and fetch/spacetrack.py, so
a polling dashboard doesn't hammer a free public API. Composable
rather than baked into either provider: callers pass whichever
`fetch_*_text` function they want cached. Freshness is the cache
file's mtime rather than a fetch-date-suffixed filename, simpler and
equally correct for a TTL cache. A network failure that raises
`FetchError` falls back to a stale entry if one exists, with the
staleness reported to the caller rather than hidden.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from ariadne.config.settings import CACHE_DIR
from ariadne.exceptions import FetchError

DEFAULT_TTL_HOURS = 6.0


@dataclass
class CachedResult:
    """
    Attributes:
        text: the cached (or freshly fetched) payload.
        is_stale: True if a fresh fetch failed and this is a
            (TTL-expired or not) cache entry served as a fallback.
        age_hours: how old the cache entry is, hours (0.0 for a fresh
            fetch that wasn't stale).
    """
    text: str
    is_stale: bool
    age_hours: float


def _cache_path(provider: str, query: str) -> Path:
    safe_query = "".join(c if c.isalnum() else "_" for c in query)
    return CACHE_DIR / f"{provider}_{safe_query}.txt"


def get_cached(
    provider: str,
    query: str,
    fetch_fn: Callable[[], str],
    *,
    ttl_hours: float = DEFAULT_TTL_HOURS,
) -> CachedResult:
    """
    Return a cached payload if one exists and is within `ttl_hours`,
    otherwise call `fetch_fn` for a fresh one and cache it.

    Args:
        provider: cache namespace, e.g. "celestrak".
        query: identifies the request within `provider`, e.g.
            "GROUP=active".
        fetch_fn: no-argument callable performing the actual fetch,
            e.g. `lambda: celestrak.fetch_group_text("active")`.
        ttl_hours: how long a cache entry is considered fresh.

    Returns:
        CachedResult.

    Raises:
        FetchError: `fetch_fn` failed and there is no cache entry
            (stale or otherwise) to fall back to.
    """
    path = _cache_path(provider, query)
    cached_age_hours: Optional[float] = None
    if path.exists():
        cached_age_hours = (time.time() - path.stat().st_mtime) / 3600.0
        if cached_age_hours <= ttl_hours:
            return CachedResult(text=path.read_text(), is_stale=False, age_hours=cached_age_hours)

    try:
        text = fetch_fn()
    except FetchError:
        if cached_age_hours is not None:
            return CachedResult(text=path.read_text(), is_stale=True, age_hours=cached_age_hours)
        raise

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return CachedResult(text=text, is_stale=False, age_hours=0.0)
