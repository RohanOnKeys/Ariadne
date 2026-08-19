"""
sniff.py

Detect an ingest file's format from its content, not its extension,
and dispatch to the matching parser. A TLE's lines always start with
'1 '/'2 ' in a fixed column layout, checked first since a CSV name
column could otherwise coincidentally contain a comma-free line that
looks like other formats; a CSV's header row matches at least one of
schema.py's recognized column aliases; anything else falls through to
the whitespace-delimited txt.py parser.
"""

from enum import Enum
from pathlib import Path
from typing import List, Tuple, Union

from ariadne.exceptions import IngestError
from ariadne.ingest.csv import parse_csv_text
from ariadne.ingest.schema import resolve_header
from ariadne.ingest.tle import parse_tle_text
from ariadne.ingest.txt import parse_txt_text
from ariadne.models.state_vector import SatelliteState
from ariadne.models.tle import TLE


class IngestFormat(Enum):
    TLE = "TLE"
    CSV = "CSV"
    TXT = "TXT"


def sniff_format(text: str) -> IngestFormat:
    """
    Detect which of TLE/CSV/TXT `text` is, from its content.

    Raises:
        IngestError: `text` has no non-blank lines to inspect.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise IngestError("Cannot sniff format: input has no non-blank lines.")

    for line in lines:
        if line.startswith("1 ") or line.startswith("2 "):
            return IngestFormat.TLE

    first_line = lines[0]
    if "," in first_line and resolve_header(first_line.split(",")):
        return IngestFormat.CSV

    return IngestFormat.TXT


def load_file(
    path: Union[str, Path],
) -> Tuple[List[Union[TLE, SatelliteState]], List[str]]:
    """
    Sniff `path`'s format and parse it with the matching parser.

    Returns:
        (records, warnings): `records` is `list[TLE]` for a TLE file,
        `list[SatelliteState]` for CSV/TXT. `warnings` is always empty
        for TLE (that parser has no partial-success mode, a malformed
        TLE record is a hard failure, see its module docstring) and
        holds one message per skipped row for CSV/TXT.
    """
    text = Path(path).read_text()
    fmt = sniff_format(text)

    if fmt is IngestFormat.TLE:
        return parse_tle_text(text), []
    if fmt is IngestFormat.CSV:
        return parse_csv_text(text)
    return parse_txt_text(text)
