"""
state_vector.py

`SatelliteState`, the type every layer of Ariadne speaks: ingest and
fetch produce it, propagate and estimate consume and produce it, and
export/CLI read it back out. Landing this first is deliberate, per
architecture.md, everything downstream imports it.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import numpy as np


class Frame(Enum):
    """
    Reference frame a `SatelliteState`'s position/velocity are
    expressed in. See the primer (`docs/orbital-mechanics-and-
    estimation-primer.md`, section 4) for what each one is and why
    Ariadne needs all four; `propagate/frames.py` is the sole owner of
    converting between them.
    """
    TEME = "TEME"
    ECI = "ECI"
    ECEF = "ECEF"
    TOPOCENTRIC = "TOPOCENTRIC"


@dataclass
class SatelliteState:
    """
    Position, velocity, and epoch of a single object at a single
    instant, in a specific frame.

    Attributes:
        epoch: UTC datetime of this state.
        position: 3-vector, km.
        velocity: 3-vector, km/s.
        frame: which reference frame position/velocity are expressed in.
        norad_id: catalog number, if known.
        name: object name, if known.
    """
    epoch: datetime
    position: np.ndarray
    velocity: np.ndarray
    frame: Frame
    norad_id: Optional[int] = None
    name: Optional[str] = None

    def __post_init__(self) -> None:
        self.position = np.asarray(self.position, dtype=float)
        self.velocity = np.asarray(self.velocity, dtype=float)
        if self.position.shape != (3,) or self.velocity.shape != (3,):
            raise ValueError(
                "SatelliteState position and velocity must each be a "
                "3-vector, got shapes "
                f"{self.position.shape} and {self.velocity.shape}."
            )

    def as_vector(self) -> np.ndarray:
        """Return the 6-state [x, y, z, vx, vy, vz], the layout the
        UKF and the numerical propagator both operate on."""
        return np.concatenate([self.position, self.velocity])

    @classmethod
    def from_vector(
        cls,
        vector: np.ndarray,
        epoch: datetime,
        frame: Frame,
        norad_id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> "SatelliteState":
        """Build a SatelliteState from a 6-vector [x, y, z, vx, vy, vz]."""
        vector = np.asarray(vector, dtype=float)
        return cls(
            epoch=epoch,
            position=vector[:3],
            velocity=vector[3:6],
            frame=frame,
            norad_id=norad_id,
            name=name,
        )
