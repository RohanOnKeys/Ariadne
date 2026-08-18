"""Tests for ariadne.conjunction.probability."""

import numpy as np
import pytest

from ariadne.conjunction.probability import (
    encounter_plane_basis,
    probability_of_collision,
)


@pytest.mark.parametrize("v_rel", [
    np.array([1.0, 0.0, 0.0]),
    np.array([0.0, 0.0, 1.0]),
    np.array([3.0, -2.0, 5.0]),
])
def test_encounter_plane_basis_is_orthonormal_and_perpendicular_to_v_rel(v_rel):
    u, w = encounter_plane_basis(v_rel)
    v_hat = v_rel / np.linalg.norm(v_rel)

    assert np.linalg.norm(u) == pytest.approx(1.0)
    assert np.linalg.norm(w) == pytest.approx(1.0)
    assert np.dot(u, w) == pytest.approx(0.0, abs=1e-12)
    assert np.dot(u, v_hat) == pytest.approx(0.0, abs=1e-12)
    assert np.dot(w, v_hat) == pytest.approx(0.0, abs=1e-12)


def test_zero_miss_circular_covariance_matches_closed_form():
    # Isotropic 3D covariance projects to an isotropic 2D covariance
    # regardless of v_rel's direction, and r_rel parallel to v_rel
    # projects to a zero miss vector, so this reduces to the classic
    # centered-circular-Gaussian-over-a-disk closed form:
    # Pc = 1 - exp(-hbr^2 / (2 * sigma^2)).
    sigma = 0.1
    hbr = 0.02
    v_rel = np.array([1.0, 0.0, 0.0])
    r_rel = 2.0 * v_rel

    covariance_primary = (sigma**2 / 2.0) * np.eye(3)
    covariance_secondary = (sigma**2 / 2.0) * np.eye(3)

    pc = probability_of_collision(r_rel, v_rel, covariance_primary, covariance_secondary, hbr)

    expected = 1.0 - np.exp(-hbr**2 / (2.0 * sigma**2))
    assert pc == pytest.approx(expected, abs=1e-8)


def test_large_miss_distance_gives_near_zero_probability():
    v_rel = np.array([1.0, 0.0, 0.0])
    r_rel = np.array([0.0, 10.0, 0.0])
    covariance_primary = 0.01 * np.eye(3)
    covariance_secondary = 0.01 * np.eye(3)

    pc = probability_of_collision(r_rel, v_rel, covariance_primary, covariance_secondary, 0.02)

    assert pc == pytest.approx(0.0, abs=1e-8)


def test_probability_increases_with_hard_body_radius():
    v_rel = np.array([1.0, 0.0, 0.0])
    r_rel = np.array([0.0, 0.05, 0.0])
    covariance_primary = 0.005 * np.eye(3)
    covariance_secondary = 0.005 * np.eye(3)

    pc_small = probability_of_collision(
        r_rel, v_rel, covariance_primary, covariance_secondary, 0.01,
    )
    pc_large = probability_of_collision(
        r_rel, v_rel, covariance_primary, covariance_secondary, 0.05,
    )

    assert 0.0 <= pc_small < pc_large <= 1.0
