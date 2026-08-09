"""
measurement.py

`Measurement`, a generic observation container: a value vector plus
its noise covariance, and enough metadata to know what the values
mean. `estimate/`'s UKF already consumes a bare position/velocity
vector directly (identity measurement model); this type is what M4's
non-identity models (range/az/el) and measurement simulation build on.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import numpy as np


class MeasurementType(Enum):
    """What `Measurement.values` holds."""
    POSITION_VELOCITY = "POSITION_VELOCITY"
    """[x, y, z, vx, vy, vz], km and km/s."""
    RANGE_AZ_EL = "RANGE_AZ_EL"
    """[range, azimuth, elevation], km and radians."""


@dataclass
class Measurement:
    """
    A single observation: a value vector, its noise covariance, and
    what epoch/type/station it belongs to.

    Attributes:
        epoch: UTC datetime the observation was taken at.
        values: observation vector, shape and units depend on `type`.
        covariance: noise covariance matching `values`' dimension.
        type: what `values` holds.
        station_id: originating ground station/sensor, if any (unset
            for a direct position/velocity "sensor").
    """
    epoch: datetime
    values: np.ndarray
    covariance: np.ndarray
    type: MeasurementType = MeasurementType.POSITION_VELOCITY
    station_id: Optional[str] = None

    def __post_init__(self) -> None:
        self.values = np.asarray(self.values, dtype=float)
        self.covariance = np.asarray(self.covariance, dtype=float)

        if self.values.ndim != 1:
            raise ValueError(
                f"Measurement.values must be a 1-D vector, got shape "
                f"{self.values.shape}."
            )

        n = self.values.shape[0]
        if self.covariance.shape != (n, n):
            raise ValueError(
                f"Measurement.covariance must be {n}x{n} to match "
                f"values, got {self.covariance.shape}."
            )
