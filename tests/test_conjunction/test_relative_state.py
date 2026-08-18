"""Tests for ariadne.conjunction.relative_state."""

import numpy as np

from ariadne.conjunction.relative_state import relative_state


def test_relative_state_is_secondary_minus_primary():
    primary = np.array([7000.0, 0.0, 0.0, 0.0, 7.5, 0.0])
    secondary = np.array([7001.0, 2.0, -1.0, 0.1, 7.4, 0.05])

    r_rel, v_rel = relative_state(primary, secondary)

    np.testing.assert_allclose(r_rel, [1.0, 2.0, -1.0])
    np.testing.assert_allclose(v_rel, [0.1, -0.1, 0.05])


def test_relative_state_of_identical_states_is_zero():
    state = np.array([7000.0, 100.0, -50.0, 0.5, 7.4, 0.2])

    r_rel, v_rel = relative_state(state, state)

    np.testing.assert_allclose(r_rel, [0.0, 0.0, 0.0])
    np.testing.assert_allclose(v_rel, [0.0, 0.0, 0.0])
