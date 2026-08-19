"""
txt.py

Whitespace-delimited state files -> list[SatelliteState], no header:
each non-blank, non-comment line is `epoch x y z vx vy vz [norad_id]`,
whitespace-separated. Lines starting with '#' are comments. Unlike
csv.py there's no header to carry an object name (a whitespace-
delimited name field would be ambiguous), this format is for bulk
numeric ephemeris rather than a labeled catalog.

As with csv.py, malformed lines are collected as warnings rather than
aborting the whole file.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Union

import numpy as np

from ariadne.exceptions import IngestError
from ariadne.models.state_vector import Frame, SatelliteState


def _parse_epoch(raw: str, line_number: int) -> datetime:
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        epoch = datetime.fromisoformat(text)
    except ValueError as exc:
        raise IngestError(f"line {line_number}: malformed epoch {raw!r}.") from exc

    if epoch.tzinfo is None:
        raise IngestError(
            f"line {line_number}: epoch {raw!r} is naive, an explicit UTC "
            "offset is required."
        )
    return epoch.astimezone(timezone.utc)


def _parse_line(fields: List[str], line_number: int) -> SatelliteState:
    if len(fields) not in (7, 8):
        raise IngestError(
            f"line {line_number}: expected 7 or 8 whitespace-separated fields "
            f"(epoch x y z vx vy vz [norad_id]), got {len(fields)}."
        )

    epoch = _parse_epoch(fields[0], line_number)
    try:
        position = np.array([float(v) for v in fields[1:4]])
        velocity = np.array([float(v) for v in fields[4:7]])
        norad_id = int(fields[7]) if len(fields) == 8 else None
    except ValueError as exc:
        raise IngestError(f"line {line_number}: {exc}") from exc

    return SatelliteState(
        epoch=epoch, position=position, velocity=velocity, frame=Frame.ECI,
        norad_id=norad_id,
    )


def parse_txt_text(text: str) -> Tuple[List[SatelliteState], List[str]]:
    """
    Parse whitespace-delimited state lines.

    Returns:
        (states, warnings): successfully parsed states, and one
        message per line that was skipped for being malformed.
    """
    states: List[SatelliteState] = []
    warnings: List[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            states.append(_parse_line(stripped.split(), line_number))
        except IngestError as exc:
            warnings.append(str(exc))

    return states, warnings


def load_txt_file(path: Union[str, Path]) -> Tuple[List[SatelliteState], List[str]]:
    """Read and parse a whitespace-delimited state file from disk."""
    return parse_txt_text(Path(path).read_text())
