"""
exceptions

Exception hierarchy for Ariadne. Everything the library raises on bad
input or a failed computation derives from `AriadneError`,  so a CLI
entry point can catch that one type and print a clean message instead of
a traceback.
"""


class AriadneError(Exception):
    """Base class for every error raised by Ariadne."""


class TLEParseError(AriadneError):
    """A two-line element set is malformed,  truncated,  or fails checksum."""


class PropagationError(AriadneError):
    """An orbit propagator failed to produce a state (e.g. SGP4 decay)."""


class FrameTransformError(AriadneError):
    """A coordinate/frame transformation was given inconsistent input."""


class IngestError(AriadneError):
    """An input file could not be parsed into the unified state model."""


class FetchError(AriadneError):
    """A remote catalog provider could not be reached or returned garbage."""


class ConjunctionError(AriadneError):
    """A conjunction geometry or probability computation was given invalid input."""


class ExportError(AriadneError):
    """A result could not be serialized to the requested export format."""
