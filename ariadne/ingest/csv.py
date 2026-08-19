"""
csv.py

Header-driven state-vector CSV -> list[SatelliteState]. Column order
is read from the header row and matched against schema.py's aliases,
so column order doesn't matter and a handful of common header
spellings are all accepted.

Malformed data rows are collected as warnings rather than aborting the
whole file (a bad row in a 10,000-object catalog shouldn't lose the
other 9,999); a header missing a required column is a hard failure,
there's no reasonable row to fall back to in that case.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Union

import numpy as np

from ariadne.exceptions import IngestError
from ariadne.ingest.schema import resolve_header, validate_required_fields
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


def _parse_row(row: List[str], columns: dict, line_number: int) -> SatelliteState:
    try:
        epoch = _parse_epoch(row[columns["epoch"]], line_number)
        position = np.array([float(row[columns[c]]) for c in ("x", "y", "z")])
        velocity = np.array([float(row[columns[c]]) for c in ("vx", "vy", "vz")])
    except (ValueError, IndexError) as exc:
        raise IngestError(f"line {line_number}: {exc}") from exc

    frame = Frame.ECI
    if "frame" in columns:
        raw_frame = row[columns["frame"]].strip()
        if raw_frame:
            try:
                frame = Frame(raw_frame.upper())
            except ValueError as exc:
                raise IngestError(f"line {line_number}: unknown frame {raw_frame!r}.") from exc

    norad_id = None
    if "norad_id" in columns and row[columns["norad_id"]].strip():
        try:
            norad_id = int(row[columns["norad_id"]])
        except ValueError as exc:
            raise IngestError(
                f"line {line_number}: malformed norad_id {row[columns['norad_id']]!r}."
            ) from exc

    name = None
    if "name" in columns:
        name = row[columns["name"]].strip() or None

    return SatelliteState(
        epoch=epoch, position=position, velocity=velocity, frame=frame,
        norad_id=norad_id, name=name,
    )


def parse_csv_text(text: str) -> Tuple[List[SatelliteState], List[str]]:
    """
    Parse a header-driven state-vector CSV.

    Returns:
        (states, warnings): successfully parsed states, and one
        message per data row that was skipped for being malformed.

    Raises:
        IngestError: the file is empty, or the header is missing a
            required column.
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise IngestError("CSV text is empty, no header row found.")

    columns = resolve_header(rows[0])
    validate_required_fields(columns, line_number=1)

    states: List[SatelliteState] = []
    warnings: List[str] = []
    for line_number, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        try:
            states.append(_parse_row(row, columns, line_number))
        except IngestError as exc:
            warnings.append(str(exc))

    return states, warnings


def load_csv_file(path: Union[str, Path]) -> Tuple[List[SatelliteState], List[str]]:
    """Read and parse a state-vector CSV file from disk."""
    return parse_csv_text(Path(path).read_text())
