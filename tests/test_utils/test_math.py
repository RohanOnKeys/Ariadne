"""Tests for ariadne.utils.math."""

import numpy as np
import pytest

from ariadne.exceptions import AriadneError
from ariadne.utils.math import unit_vector, rot1, rot2, rot3, wrap_to_2pi, wrap_to_pi


def test_unit_vector_normalizes():
    v = np.array([3.0, 4.0, 0.0])
    result = unit_vector(v)
    assert np.isclose(np.linalg.norm(result), 1.0)
    np.testing.assert_allclose(result, [0.6, 0.8, 0.0])


def test_unit_vector_zero_vector_raises():
    with pytest.raises(AriadneError):
        unit_vector(np.zeros(3))


@pytest.mark.parametrize("rot,axis", [
    (rot1, [1.0, 0.0, 0.0]),
    (rot2, [0.0, 1.0, 0.0]),
    (rot3, [0.0, 0.0, 1.0]),
])
def test_rotation_leaves_its_own_axis_fixed(rot, axis):
    """rot1/rot2/rot3 rotate about x/y/z, so the corresponding unit
    vector should be unaffected by that rotation."""
    axis_vec = np.array(axis)
    rotated = rot(0.7) @ axis_vec
    np.testing.assert_allclose(rotated, axis_vec, atol=1e-12)


@pytest.mark.parametrize("rot", [rot1, rot2, rot3])
def test_rotation_matrices_are_orthonormal(rot):
    R = rot(1.234)
    np.testing.assert_allclose(R @ R.T, np.eye(3), atol=1e-12)
    assert np.isclose(np.linalg.det(R), 1.0)


def test_rot3_zero_angle_is_identity():
    np.testing.assert_allclose(rot3(0.0), np.eye(3), atol=1e-12)


def test_wrap_to_2pi_handles_negative_and_large_angles():
    assert np.isclose(wrap_to_2pi(-0.5), 2 * np.pi - 0.5)
    assert np.isclose(wrap_to_2pi(2 * np.pi + 0.5), 0.5)
    assert wrap_to_2pi(0.0) == 0.0


def test_wrap_to_pi_handles_boundary_and_negative_angles():
    assert np.isclose(wrap_to_pi(np.pi + 0.5), 0.5 - np.pi)
    assert np.isclose(wrap_to_pi(-np.pi - 0.5), np.pi - 0.5)
    assert np.isclose(wrap_to_pi(np.pi), np.pi)
