"""
sgp4.py

Wraps the `sgp4` PyPI package (Vallado's reference implementation) to
turn a `TLE` + target epoch into a `SatelliteState`. SGP4 natively
outputs TEME; this module converts to ECI before returning, per
architecture.md, propagate/frames.py owns every rotation.
"""

from datetime import datetime

import numpy as np
from sgp4.api import Satrec, SGP4_ERRORS, jday

from ariadne.exceptions import PropagationError
from ariadne.models.state_vector import Frame, SatelliteState
from ariadne.models.tle import TLE
from ariadne.propagate.frames import teme_to_eci


def propagate(tle: TLE, epoch: datetime) -> SatelliteState:
    """
    Propagate a TLE to `epoch` using SGP4.

    Args:
        tle: parsed TLE. SGP4 requires the exact mean elements a TLE
            encodes, `line1`/`line2` are handed to the sgp4 package
            verbatim rather than reconstructed from `TLE`'s parsed
            fields.
        epoch: UTC datetime to propagate to.

    Returns:
        SatelliteState in the ECI (J2000) frame.

    Raises:
        PropagationError: SGP4 reports one of its own error codes
            (e.g. decayed orbit, out-of-range eccentricity).
    """
    satrec = Satrec.twoline2rv(tle.line1, tle.line2)

    jd, fr = jday(
        epoch.year, epoch.month, epoch.day,
        epoch.hour, epoch.minute, epoch.second + epoch.microsecond / 1e6,
    )
    error_code, r_teme, v_teme = satrec.sgp4(jd, fr)

    if error_code != 0:
        message = SGP4_ERRORS.get(error_code, "unknown SGP4 error")
        raise PropagationError(
            f"SGP4 error {error_code} propagating NORAD {tle.norad_id} "
            f"to {epoch.isoformat()}: {message}"
        )

    r_eci, v_eci = teme_to_eci(np.array(r_teme), np.array(v_teme), epoch)

    return SatelliteState(
        epoch=epoch,
        position=r_eci,
        velocity=v_eci,
        frame=Frame.ECI,
        norad_id=tle.norad_id,
        name=tle.name,
    )
