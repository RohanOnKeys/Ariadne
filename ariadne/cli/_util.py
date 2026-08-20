"""
_util.py

Small helpers shared by Ariadne's CLI subcommands: ISO-8601 epoch
parsing and TLE selection by NORAD ID. Internal to `ariadne/cli/`,
nothing outside this package should import it.
"""

from datetime import datetime, timezone
from typing import List, Optional

import click

from ariadne.models.tle import TLE


def parse_iso_epoch(value: str) -> datetime:
    """Parse an ISO-8601 UTC epoch (a trailing 'Z' is accepted as
    shorthand for '+00:00'); requires an explicit UTC offset."""
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        epoch = datetime.fromisoformat(text)
    except ValueError as exc:
        raise click.BadParameter(f"{value!r} is not a valid ISO-8601 datetime.") from exc
    if epoch.tzinfo is None:
        raise click.BadParameter(
            f"{value!r} has no UTC offset (append 'Z' or '+00:00')."
        )
    return epoch.astimezone(timezone.utc)


def select_tle(tles: List[TLE], norad_id: Optional[int], source: str) -> TLE:
    """Pick one TLE out of a parsed file: by `norad_id` if given,
    otherwise the sole entry if the file has exactly one."""
    if norad_id is not None:
        matches = [tle for tle in tles if tle.norad_id == norad_id]
        if not matches:
            raise click.ClickException(f"NORAD ID {norad_id} not found in {source}.")
        return matches[0]
    if len(tles) == 1:
        return tles[0]
    raise click.ClickException(
        f"{source} has {len(tles)} objects, pass --norad-id to select one."
    )
