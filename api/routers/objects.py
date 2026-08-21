"""
objects.py

GET /objects/{norad_id}/state: a single object's propagated state.
GET /objects/{norad_id}/orbit.czml: a single object's CZML path, the
dashboard's animated-globe feed for one satellite.
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query

from api.dependencies import DEFAULT_TTL_HOURS, parse_epoch, resolve_tle
from ariadne.export.czml import to_czml
from ariadne.export.json import state_to_dict
from ariadne.propagate.sgp4 import propagate as sgp4_propagate

router = APIRouter()

_MAX_CZML_STEPS = 5000


@router.get("/objects/{norad_id}/state")
def get_object_state(
    norad_id: int = Path(..., description="NORAD catalog number."),
    epoch: Optional[str] = Query(None, description="ISO-8601 UTC epoch; defaults to now."),
    provider: str = Query("celestrak", pattern="^(celestrak|spacetrack)$"),
    ttl_hours: float = Query(DEFAULT_TTL_HOURS),
    no_cache: bool = Query(False),
) -> dict:
    epoch0 = parse_epoch(epoch)
    tle = resolve_tle(norad_id, provider=provider, ttl_hours=ttl_hours, no_cache=no_cache)
    state = sgp4_propagate(tle, epoch0)
    return state_to_dict(state)


@router.get("/objects/{norad_id}/orbit.czml")
def get_object_czml(
    norad_id: int = Path(..., description="NORAD catalog number."),
    epoch: Optional[str] = Query(None, description="ISO-8601 UTC start epoch; defaults to now."),
    duration_s: float = Query(5400.0, gt=0, description="Path length, seconds from `epoch`."),
    step_s: float = Query(60.0, gt=0, description="Sample interval, seconds."),
    provider: str = Query("celestrak", pattern="^(celestrak|spacetrack)$"),
    ttl_hours: float = Query(DEFAULT_TTL_HOURS),
    no_cache: bool = Query(False),
) -> list:
    num_steps = int(duration_s // step_s) + 1
    if num_steps > _MAX_CZML_STEPS:
        raise HTTPException(
            422, f"duration_s/step_s would sample {num_steps} points, exceeds the "
            f"{_MAX_CZML_STEPS} limit; widen step_s or shorten duration_s.",
        )

    epoch0 = parse_epoch(epoch)
    tle = resolve_tle(norad_id, provider=provider, ttl_hours=ttl_hours, no_cache=no_cache)
    states = [
        sgp4_propagate(tle, epoch0 + timedelta(seconds=i * step_s))
        for i in range(num_steps)
    ]
    name = tle.name or str(norad_id)
    return to_czml(f"{name} orbit", [states])
