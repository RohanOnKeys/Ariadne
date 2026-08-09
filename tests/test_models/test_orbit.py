"""Tests for ariadne.models.orbit."""

import numpy as np
import pytest

from ariadne.constants import MU_EARTH, R_EARTH
from ariadne.models.orbit import KeplerianElements, coe_to_rv, rv_to_coe


def _iss_like_elements():
    """Matches the primer's worked ISS example (section 3)."""
    return KeplerianElements(
        a=6796.147, e=0.0006703, i=np.radians(51.6416), raan=np.radians(247.4627),
        arg_perigee=np.radians(130.5360), true_anomaly=np.radians(45.0),
    )


def test_period_matches_primer_worked_example():
    elements = _iss_like_elements()
    assert np.isclose(elements.period / 60.0, 92.93, atol=0.05)


def test_apogee_and_perigee_altitude_bracket_a_minus_re():
    elements = _iss_like_elements()
    assert elements.perigee_altitude < (elements.a - R_EARTH) < elements.apogee_altitude
    assert np.isclose(elements.apogee_altitude, 422.6, atol=0.1)
    assert np.isclose(elements.perigee_altitude, 413.5, atol=0.1)


def test_circular_orbit_has_equal_apogee_and_perigee():
    circular = KeplerianElements(
        a=7000.0, e=0.0, i=0.5, raan=1.0, arg_perigee=0.0, true_anomaly=2.0,
    )
    assert np.isclose(circular.apogee_radius, circular.perigee_radius)


@pytest.mark.parametrize("nu_deg", [0.0, 45.0, 130.0, 200.0, 300.0])
def test_coe_to_rv_position_magnitude_matches_orbit_equation(nu_deg):
    """|r| from coe_to_rv should match the polar orbit equation
    r = p / (1 + e*cos(nu)) directly, independent of the perifocal
    rotation."""
    elements = KeplerianElements(
        a=7000.0, e=0.01, i=0.9, raan=1.2, arg_perigee=0.3, true_anomaly=np.radians(nu_deg),
    )
    r, _ = coe_to_rv(elements)
    p = elements.a * (1 - elements.e**2)
    expected_r = p / (1 + elements.e * np.cos(elements.true_anomaly))
    assert np.isclose(np.linalg.norm(r), expected_r)


def test_coe_to_rv_then_rv_to_coe_round_trips():
    elements = _iss_like_elements()
    r, v = coe_to_rv(elements)
    recovered = rv_to_coe(r, v)

    assert np.isclose(recovered.a, elements.a, atol=1e-6)
    assert np.isclose(recovered.e, elements.e, atol=1e-9)
    assert np.isclose(recovered.i, elements.i, atol=1e-12)
    assert np.isclose(recovered.raan, elements.raan, atol=1e-12)
    assert np.isclose(recovered.arg_perigee, elements.arg_perigee, atol=1e-9)
    assert np.isclose(recovered.true_anomaly, elements.true_anomaly, atol=1e-9)


def test_rv_to_coe_energy_matches_vis_viva():
    """Independent cross-check: semi-major axis derived by rv_to_coe
    should satisfy the vis-viva equation for the same r, v."""
    elements = _iss_like_elements()
    r, v = coe_to_rv(elements)
    coe = rv_to_coe(r, v)

    r_mag, v_mag = np.linalg.norm(r), np.linalg.norm(v)
    v_expected = np.sqrt(MU_EARTH * (2.0 / r_mag - 1.0 / coe.a))
    assert np.isclose(v_mag, v_expected, rtol=1e-9)


def test_mean_anomaly_matches_true_anomaly_for_circular_orbit():
    """For e=0, eccentric and mean anomaly both equal true anomaly."""
    circular = KeplerianElements(
        a=7000.0, e=0.0, i=0.5, raan=0.0, arg_perigee=0.0, true_anomaly=1.0,
    )
    assert np.isclose(circular.eccentric_anomaly, 1.0)
    assert np.isclose(circular.mean_anomaly, 1.0)
