"""
tle.py

Ingest a TLE file (2-line or 3-line/named format, one or many
satellites) into a list of parsed `TLE` objects. Splitting/format
detection lives here; the actual field parsing is
`models/tle.py:TLE.from_lines`.
"""

from pathlib import Path
from typing import List, Union

from ariadne.exceptions import IngestError
from ariadne.models.tle import TLE


def parse_tle_text(text: str) -> List[TLE]:
    """
    Parse TLE records out of raw text, one or many satellites, with or
    without a name line before each 2-line element set.

    Raises:
        IngestError: a record doesn't resolve to a valid 2-line pair.
    """
    lines = [line for line in text.splitlines() if line.strip()]

    tles: List[TLE] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("1 ") and i + 1 < len(lines) and lines[i + 1].startswith("2 "):
            tles.append(TLE.from_lines(line, lines[i + 1]))
            i += 2
        elif i + 2 < len(lines) and lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 "):
            tles.append(TLE.from_lines(lines[i + 1], lines[i + 2], name=line))
            i += 3
        else:
            raise IngestError(f"line {i + 1}: expected a TLE line 1/2 pair, got {line!r}.")

    return tles


def load_tle_file(path: Union[str, Path]) -> List[TLE]:
    """
    Read and parse a TLE file from disk.

    Raises:
        IngestError: same conditions as `parse_tle_text`.
    """
    return parse_tle_text(Path(path).read_text())
