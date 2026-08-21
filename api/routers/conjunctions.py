"""
conjunctions.py

GET /conjunctions/next: the single closest approach between one
primary object and a CelesTrak group, the "Next Close Approach" panel.
GET /conjunctions/screen: every approach within a miss-distance
threshold, the same panel's full list / catalog screen.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import DEFAULT_TTL_HOURS, parse_epoch, resolve_group, resolve_tle
from ariadne.conjunction.screening import screen_catalog
from ariadne.export.json import screening_result_to_dict
from ariadne.propagate.sgp4 import propagate as sgp4_propagate

router = APIRouter()


def _screen(
    primary_id: int, group: str, epoch: Optional[str],
    window_min_s: float, window_max_s: float, threshold_km: float, include_j2: bool,
    provider: str, ttl_hours: float, no_cache: bool,
) -> tuple:
    epoch0 = parse_epoch(epoch)
    primary = resolve_tle(primary_id, provider=provider, ttl_hours=ttl_hours, no_cache=no_cache)
    primary_state = sgp4_propagate(primary, epoch0).as_vector()

    secondaries = [
        (tle.norad_id, tle.name, sgp4_propagate(tle, epoch0).as_vector())
        for tle in resolve_group(group, ttl_hours=ttl_hours, no_cache=no_cache)
        if tle.norad_id != primary.norad_id
    ]

    results = screen_catalog(
        epoch0, primary_state, secondaries, threshold_km,
        window=(window_min_s, window_max_s), include_j2=include_j2,
    )
    return epoch0, results


@router.get("/conjunctions/screen")
def get_conjunctions_screen(
    primary_id: int = Query(..., description="Primary object's NORAD catalog number."),
    group: str = Query("stations", description="CelesTrak group to screen against."),
    epoch: Optional[str] = Query(
        None, description="ISO-8601 UTC reference epoch; defaults to now.",
    ),
    threshold_km: float = Query(
        ..., description="Only report pairs at or below this miss distance.",
    ),
    window_min_s: float = Query(-1800.0),
    window_max_s: float = Query(1800.0),
    include_j2: bool = Query(
        True, description="Include the J2 perturbation term in the TCA search.",
    ),
    provider: str = Query("celestrak", pattern="^(celestrak|spacetrack)$"),
    ttl_hours: float = Query(DEFAULT_TTL_HOURS),
    no_cache: bool = Query(False),
) -> List[dict]:
    _, results = _screen(
        primary_id, group, epoch, window_min_s, window_max_s, threshold_km, include_j2,
        provider, ttl_hours, no_cache,
    )
    return [screening_result_to_dict(r) for r in results]


@router.get("/conjunctions/next")
def get_conjunctions_next(
    primary_id: int = Query(..., description="Primary object's NORAD catalog number."),
    group: str = Query("stations", description="CelesTrak group to screen against."),
    epoch: Optional[str] = Query(
        None, description="ISO-8601 UTC reference epoch; defaults to now.",
    ),
    threshold_km: Optional[float] = Query(
        None, description="Only consider pairs at or below this miss distance; unset means any.",
    ),
    window_min_s: float = Query(-1800.0),
    window_max_s: float = Query(1800.0),
    include_j2: bool = Query(
        True, description="Include the J2 perturbation term in the TCA search.",
    ),
    provider: str = Query("celestrak", pattern="^(celestrak|spacetrack)$"),
    ttl_hours: float = Query(DEFAULT_TTL_HOURS),
    no_cache: bool = Query(False),
) -> dict:
    effective_threshold = threshold_km if threshold_km is not None else float("inf")
    _, results = _screen(
        primary_id, group, epoch, window_min_s, window_max_s, effective_threshold, include_j2,
        provider, ttl_hours, no_cache,
    )
    if not results:
        raise HTTPException(404, "No conjunction found within the given threshold/window.")
    return screening_result_to_dict(results[0])
