"""
orbit.py

Classical (Keplerian) orbital elements <-> Cartesian state, plus the
period/apogee/perigee derived quantities the "Orbit Parameters" panel
needs. See the primer, sections 1-2, for the elements themselves.

Degenerate cases (exactly circular e=0 or exactly equatorial i=0,
where RAAN and/or argument of perigee are undefined) aren't
special-cased, real catalog objects have small but nonzero
eccentricity/inclination, so the formulas below stay numerically
well-defined for anything Ariadne actually ingests.
"""

from dataclasses import dataclass

import numpy as np

from ariadne.constants import MU_EARTH, R_EARTH, TWO_PI
from ariadne.utils.math import rot1, rot3, wrap_to_2pi


@dataclass
class KeplerianElements:
    """
    Classical orbital elements, referenced to whatever inertial frame
    (typically ECI) the position/velocity they came from used.

    Attributes:
        a: semi-major axis, km.
        e: eccentricity.
        i: inclination, radians.
        raan: right ascension of ascending node, radians.
        arg_perigee: argument of perigee, radians.
        true_anomaly: radians.
    """
    a: float
    e: float
    i: float
    raan: float
    arg_perigee: float
    true_anomaly: float

    @property
    def period(self) -> float:
        """Orbital period, seconds (Kepler's third law)."""
        return TWO_PI * np.sqrt(self.a**3 / MU_EARTH)

    @property
    def apogee_radius(self) -> float:
        """km, from Earth's center."""
        return self.a * (1.0 + self.e)

    @property
    def perigee_radius(self) -> float:
        """km, from Earth's center."""
        return self.a * (1.0 - self.e)

    @property
    def apogee_altitude(self) -> float:
        """km, above the WGS-84 equatorial radius."""
        return self.apogee_radius - R_EARTH

    @property
    def perigee_altitude(self) -> float:
        """km, above the WGS-84 equatorial radius."""
        return self.perigee_radius - R_EARTH

    @property
    def eccentric_anomaly(self) -> float:
        """Radians, derived from true_anomaly."""
        return _true_to_eccentric_anomaly(self.true_anomaly, self.e)

    @property
    def mean_anomaly(self) -> float:
        """Radians, derived from true_anomaly via Kepler's equation."""
        ea = self.eccentric_anomaly
        return wrap_to_2pi(ea - self.e * np.sin(ea))


def coe_to_rv(elements: KeplerianElements) -> tuple:
    """
    Classical orbital elements -> Cartesian position/velocity, in
    whatever inertial frame the elements are referenced to.

    Returns:
        (r, v): 3-vectors, km and km/s.
    """
    p = elements.a * (1.0 - elements.e**2)
    nu = elements.true_anomaly

    cos_nu, sin_nu = np.cos(nu), np.sin(nu)
    r_mag = p / (1.0 + elements.e * cos_nu)

    r_pf = np.array([r_mag * cos_nu, r_mag * sin_nu, 0.0])
    v_pf = np.sqrt(MU_EARTH / p) * np.array([-sin_nu, elements.e + cos_nu, 0.0])

    rotation = rot3(-elements.raan) @ rot1(-elements.i) @ rot3(-elements.arg_perigee)
    return rotation @ r_pf, rotation @ v_pf


def rv_to_coe(r: np.ndarray, v: np.ndarray) -> KeplerianElements:
    """
    Cartesian position/velocity -> classical orbital elements
    (Vallado Algorithm 9).

    Args:
        r: position, km.
        v: velocity, km/s.

    Returns:
        KeplerianElements, in the same frame r/v were given in.
    """
    r_mag = np.linalg.norm(r)
    v_mag = np.linalg.norm(v)

    h_vec = np.cross(r, v)
    h_mag = np.linalg.norm(h_vec)

    node_vec = np.cross([0.0, 0.0, 1.0], h_vec)
    node_mag = np.linalg.norm(node_vec)

    e_vec = ((v_mag**2 - MU_EARTH / r_mag) * r - np.dot(r, v) * v) / MU_EARTH
    e = np.linalg.norm(e_vec)

    energy = v_mag**2 / 2.0 - MU_EARTH / r_mag
    a = -MU_EARTH / (2.0 * energy)

    i = np.arccos(np.clip(h_vec[2] / h_mag, -1.0, 1.0))

    raan = np.arccos(np.clip(node_vec[0] / node_mag, -1.0, 1.0))
    if node_vec[1] < 0:
        raan = TWO_PI - raan

    arg_perigee = np.arccos(np.clip(np.dot(node_vec, e_vec) / (node_mag * e), -1.0, 1.0))
    if e_vec[2] < 0:
        arg_perigee = TWO_PI - arg_perigee

    true_anomaly = np.arccos(np.clip(np.dot(e_vec, r) / (e * r_mag), -1.0, 1.0))
    if np.dot(r, v) < 0:
        true_anomaly = TWO_PI - true_anomaly

    return KeplerianElements(
        a=a, e=e, i=i, raan=raan, arg_perigee=arg_perigee, true_anomaly=true_anomaly,
    )


def _true_to_eccentric_anomaly(nu: float, e: float) -> float:
    return wrap_to_2pi(2.0 * np.arctan2(
        np.sqrt(1.0 - e) * np.sin(nu / 2.0),
        np.sqrt(1.0 + e) * np.cos(nu / 2.0),
    ))
