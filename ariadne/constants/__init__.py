"""
constants

Physical and geodetic constants shared across the propagation,  frame
transformation and conjunction modules.

Values are WGS-84 unless noted. Angles are radians and distances are
kilometres everywhere in Ariadne; these constants set that convention.

Note: `ariadne/estimate/dynamics.py` predates this module and carries its
own copies of MU_EARTH / R_EARTH / J2 (identical values) to stay a
self-contained inner loop for the UKF.
"""

import math

# --- Earth gravity ---------------------------------------------------------

# Gravitational parameter,  km^3/s^2 (WGS-84).
MU_EARTH = 398600.4418
# Second zonal harmonic (dimensionless).
J2 = 1.08262668e-3
# Third and fourth zonal harmonics,  kept for future force-model extensions.
J3 = -2.53265648e-6
J4 = -1.61962159e-6

# --- Earth shape and rotation ----------------------------------------------

# Equatorial radius,  km.
R_EARTH = 6378.137
# Flattening.
FLATTENING = 1.0 / 298.257223563
# Polar radius,  km.
R_EARTH_POLAR = R_EARTH * (1.0 - FLATTENING)
# First eccentricity squared of the reference ellipsoid.
ECC_EARTH_SQ = FLATTENING * (2.0 - FLATTENING)
# Rotation rate,  rad/s (IAU-82 mean sidereal rate).
OMEGA_EARTH = 7.292115146706979e-5

# --- Time ------------------------------------------------------------------

SECONDS_PER_DAY = 86400.0
MINUTES_PER_DAY = 1440.0
# Julian date of the J2000.0 epoch (2000-01-01 12:00:00 TT).
JD_J2000 = 2451545.0
# Julian days per Julian century.
DAYS_PER_CENTURY = 36525.0

# --- Angles ----------------------------------------------------------------

DEG2RAD = math.pi / 180.0
RAD2DEG = 180.0 / math.pi
# Arcseconds to radians, the precession/nutation series are tabulated in
# arcseconds,  so this conversion shows up a lot in `propagate/frames.py`.
ARCSEC2RAD = DEG2RAD / 3600.0
TWO_PI = 2.0 * math.pi
