"""
tle.py

Two-Line Element set parsing: TLE line text -> structured `TLE`.

SGP4 only produces correct results from the exact mean elements a TLE
encodes (see the primer, section 5), so `line1`/`line2` are kept
verbatim on the returned `TLE` for `propagate/sgp4.py` to hand
straight to the `sgp4` package, everything else on `TLE` is this
module's own parse of the same text, for validation, display, and
anything that wants the elements without re-parsing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ariadne.constants import DEG2RAD, TWO_PI
from ariadne.exceptions import TLEParseError
from ariadne.utils.time import tle_epoch_to_datetime

_LINE_LENGTH = 69


@dataclass
class TLE:
    """
    A parsed Two-Line Element set.

    Angles are radians and mean_motion is rad/s, per Ariadne's global
    convention, everything else keeps its native TLE unit (documented
    per field) since it's only ever handed back to SGP4 or displayed,
    never used in this project's own orbital mechanics.
    """
    line1: str
    line2: str
    name: Optional[str]
    norad_id: int
    classification: str
    intl_designator: str
    epoch: datetime
    mean_motion_dot: float
    """First derivative of mean motion / 2, rev/day^2."""
    mean_motion_ddot: float
    """Second derivative of mean motion / 6, rev/day^3."""
    bstar: float
    """Drag term, 1/earth radii."""
    ephemeris_type: int
    element_set_number: int
    inclination: float
    """Radians."""
    raan: float
    """Right ascension of ascending node, radians."""
    eccentricity: float
    arg_perigee: float
    """Radians."""
    mean_anomaly: float
    """Radians."""
    mean_motion: float
    """rad/s."""
    rev_number: int

    @classmethod
    def from_lines(
        cls,
        line1: str,
        line2: str,
        name: Optional[str] = None,
    ) -> "TLE":
        """
        Parse a two-line element set.

        Args:
            line1: TLE line 1, exactly as issued (trailing newline ok).
            line2: TLE line 2, exactly as issued.
            name: object name, if available (from a 3-line TLE file or
                a catalog lookup); not itself validated.

        Returns:
            Parsed TLE.

        Raises:
            TLEParseError: malformed length, checksum, or line number,
                or a numeric field that doesn't parse, always naming
                which line (1 or 2) and what's wrong.
        """
        line1 = line1.rstrip("\n\r")
        line2 = line2.rstrip("\n\r")

        _validate_line(line1, 1, expected_line_number="1")
        _validate_line(line2, 2, expected_line_number="2")

        norad_id_1 = _parse_int(line1[2:7], 1, "satellite number")
        norad_id_2 = _parse_int(line2[2:7], 2, "satellite number")
        if norad_id_1 != norad_id_2:
            raise TLEParseError(
                f"line 1/2: satellite number mismatch ({norad_id_1} vs "
                f"{norad_id_2})."
            )

        epoch_field = line1[18:32]
        try:
            epoch = tle_epoch_to_datetime(epoch_field)
        except ValueError as exc:
            raise TLEParseError(f"line 1: malformed epoch {epoch_field!r}: {exc}") from exc

        return cls(
            line1=line1,
            line2=line2,
            name=name.strip() if name else None,
            norad_id=norad_id_1,
            classification=line1[7] or "U",
            intl_designator=line1[9:17].strip(),
            epoch=epoch,
            mean_motion_dot=_parse_float(line1[33:43], 1, "mean motion first derivative"),
            mean_motion_ddot=_parse_assumed_decimal_exp(
                line1[44:52], 1, "mean motion second derivative",
            ),
            bstar=_parse_assumed_decimal_exp(line1[53:61], 1, "BSTAR"),
            ephemeris_type=_parse_int(line1[62:63], 1, "ephemeris type"),
            element_set_number=_parse_int(line1[64:68], 1, "element set number"),
            inclination=_parse_float(line2[8:16], 2, "inclination") * DEG2RAD,
            raan=_parse_float(line2[17:25], 2, "RAAN") * DEG2RAD,
            eccentricity=_parse_eccentricity(line2[26:33]),
            arg_perigee=_parse_float(line2[34:42], 2, "argument of perigee") * DEG2RAD,
            mean_anomaly=_parse_float(line2[43:51], 2, "mean anomaly") * DEG2RAD,
            mean_motion=_parse_float(line2[52:63], 2, "mean motion") * TWO_PI / 86400.0,
            rev_number=_parse_int(line2[63:68], 2, "revolution number"),
        )


def _validate_line(line: str, line_number: int, expected_line_number: str) -> None:
    if len(line) != _LINE_LENGTH:
        raise TLEParseError(
            f"line {line_number}: expected {_LINE_LENGTH} characters, got "
            f"{len(line)}."
        )
    if line[0] != expected_line_number:
        raise TLEParseError(
            f"line {line_number}: expected line number "
            f"{expected_line_number!r} in column 1, got {line[0]!r}."
        )

    expected_checksum = _checksum(line)
    actual_checksum = _parse_int(line[68:69], line_number, "checksum")
    if expected_checksum != actual_checksum:
        raise TLEParseError(
            f"line {line_number}: checksum mismatch, computed "
            f"{expected_checksum}, line says {actual_checksum}."
        )


def _checksum(line: str) -> int:
    """TLE checksum: sum of all digits mod 10, '-' counts as 1,
    everything else (letters, spaces, '.', '+') counts as 0. Computed
    over columns 1-68 (the checksum digit itself, column 69, isn't
    included)."""
    total = 0
    for char in line[:68]:
        if char.isdigit():
            total += int(char)
        elif char == "-":
            total += 1
    return total % 10


def _parse_int(field: str, line_number: int, field_name: str) -> int:
    try:
        return int(field.strip())
    except ValueError as exc:
        raise TLEParseError(
            f"line {line_number}: malformed {field_name} {field!r}."
        ) from exc


def _parse_float(field: str, line_number: int, field_name: str) -> float:
    try:
        return float(field.strip())
    except ValueError as exc:
        raise TLEParseError(
            f"line {line_number}: malformed {field_name} {field!r}."
        ) from exc


def _parse_assumed_decimal_exp(field: str, line_number: int, field_name: str) -> float:
    """Parse the TLE's assumed-decimal-point exponential notation,
    e.g. '10270-3' -> 0.10270 * 10^-3. Used for BSTAR and the second
    derivative of mean motion, never a plain decimal."""
    raw = field.strip()
    if not raw:
        return 0.0

    sign = 1.0
    if raw[0] in "+-":
        sign = -1.0 if raw[0] == "-" else 1.0
        raw = raw[1:]

    if len(raw) < 3:
        raise TLEParseError(f"line {line_number}: malformed {field_name} {field!r}.")

    mantissa_digits, exp_sign, exp_digits = raw[:-2], raw[-2], raw[-1]
    try:
        mantissa = float(f"0.{mantissa_digits}")
        exponent = int(exp_digits)
    except ValueError as exc:
        raise TLEParseError(f"line {line_number}: malformed {field_name} {field!r}.") from exc

    if exp_sign == "-":
        exponent = -exponent
    elif exp_sign != "+":
        raise TLEParseError(f"line {line_number}: malformed {field_name} {field!r}.")

    return sign * mantissa * (10.0 ** exponent)


def _parse_eccentricity(field: str) -> float:
    """Eccentricity has an implied leading '0.', TLEs never write it."""
    raw = field.strip()
    if not raw:
        raise TLEParseError(f"line 2: malformed eccentricity {field!r}.")
    try:
        return float(f"0.{raw}")
    except ValueError as exc:
        raise TLEParseError(f"line 2: malformed eccentricity {field!r}.") from exc
