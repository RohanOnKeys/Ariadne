"""Tests for ariadne.conjunction.ric."""

import numpy as np

from ariadne.conjunction.ric import eci_to_ric, ric_rotation_matrix


def test_rotation_matrix_is_identity_for_equatorial_prograde_state():
    # Primary on the +x axis moving in +y: radial = +x, cross-track
    # (orbit normal) = +z, in-track = +y, i.e. the standard basis.
    r_primary = np.array([7000.0, 0.0, 0.0])
    v_primary = np.array([0.0, 7.5, 0.0])

    rotation = ric_rotation_matrix(r_primary, v_primary)

    np.testing.assert_allclose(rotation, np.eye(3), atol=1e-12)


def test_rotation_matrix_rows_are_orthonormal():
    r_primary = np.array([4000.0, -3000.0, 5200.0])
    v_primary = np.array([1.2, 6.9, -2.4])

    rotation = ric_rotation_matrix(r_primary, v_primary)

    np.testing.assert_allclose(rotation @ rotation.T, np.eye(3), atol=1e-10)


def test_cross_track_is_perpendicular_to_position_and_velocity():
    r_primary = np.array([4000.0, -3000.0, 5200.0])
    v_primary = np.array([1.2, 6.9, -2.4])

    cross_track = ric_rotation_matrix(r_primary, v_primary)[2]

    assert abs(np.dot(cross_track, r_primary)) < 1e-8
    assert abs(np.dot(cross_track, v_primary)) < 1e-8


def test_eci_to_ric_matches_direct_rotation():
    r_primary = np.array([4000.0, -3000.0, 5200.0])
    v_primary = np.array([1.2, 6.9, -2.4])
    r_rel = np.array([1.0, -0.5, 0.2])
    v_rel = np.array([0.01, -0.02, 0.03])

    r_ric, v_ric = eci_to_ric(r_rel, v_rel, r_primary, v_primary)

    rotation = ric_rotation_matrix(r_primary, v_primary)
    np.testing.assert_allclose(r_ric, rotation @ r_rel)
    np.testing.assert_allclose(v_ric, rotation @ v_rel)
