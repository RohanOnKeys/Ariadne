"""
schema.py

Column-name aliases and required-field validation shared by
`ingest/csv.py` and `ingest/txt.py`, both parse the same underlying
"state vector row" shape, this module is the single place that shape
and its accepted header spellings are defined.
"""

from typing import Dict, List

from ariadne.exceptions import IngestError

# Canonical field name -> accepted header spellings (case-insensitive,
# matched after stripping whitespace).
FIELD_ALIASES: Dict[str, List[str]] = {
    "epoch": ["epoch", "datetime", "time", "utc"],
    "x": ["x", "x_km", "position_x"],
    "y": ["y", "y_km", "position_y"],
    "z": ["z", "z_km", "position_z"],
    "vx": ["vx", "vx_km_s", "velocity_x"],
    "vy": ["vy", "vy_km_s", "velocity_y"],
    "vz": ["vz", "vz_km_s", "velocity_z"],
    "frame": ["frame", "reference_frame"],
    "norad_id": ["norad_id", "norad", "catalog_number", "satnum"],
    "name": ["name", "object_name", "satellite"],
}

REQUIRED_FIELDS = ["epoch", "x", "y", "z", "vx", "vy", "vz"]


def resolve_header(header: List[str]) -> Dict[str, int]:
    """
    Map canonical field names to column indices, given a header row.

    Args:
        header: column names as read from the file, in order.

    Returns:
        {canonical field name: column index}, only for canonical
        fields that matched some column, callers check for missing
        required fields themselves (see `validate_required_fields`).
    """
    lowered = [column.strip().lower() for column in header]

    resolved: Dict[str, int] = {}
    for canonical, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in lowered:
                resolved[canonical] = lowered.index(alias)
                break

    return resolved


def validate_required_fields(resolved: Dict[str, int], line_number: int = 1) -> None:
    """
    Raise IngestError if any of REQUIRED_FIELDS is missing from
    `resolved` (as returned by `resolve_header`).
    """
    missing = [field for field in REQUIRED_FIELDS if field not in resolved]
    if missing:
        raise IngestError(
            f"line {line_number}: missing required column(s): {', '.join(missing)}."
        )
