"""
tle.py

Ingest a TLE file (2-line format, one or many satellites) into a
list of parsed `TLE` objects. Splitting/format detection lives here;
the actual field parsing is `models/tle.py:TLE.from_lines`.
"""

from typing import List

from ariadne.exceptions import IngestError
from ariadne.models.tle import TLE


def parse_tle_text(text: str) -> List[TLE]:
    """
    Parse bare 2-line TLE records out of raw text, one or many
    satellites, no name line.

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
        else:
            raise IngestError(f"line {i + 1}: expected a TLE line 1/2 pair, got {line!r}.")

    return tles
