"""Tests for ariadne.estimate.ukf."""

import numpy as np

from ariadne.estimate.ukf import UnscentedKalmanFilter
from ariadne.estimate.dynamics import propagate_rk4, MU_EARTH, R_EARTH
from ariadne.estimate.noise_models import (
    build_measurement_noise, build_process_noise_discrete_white_noise,
)


def _circular_leo_state(alt_km: float = 500.0) -> np.ndarray:
    r = R_EARTH + alt_km
    v_circ = np.sqrt(MU_EARTH / r)
    return np.array([r, 0.0, 0.0, 0.0, v_circ, 0.0])


def _make_filter(x0, P_scale=1.0):
    P0 = np.eye(6) * P_scale
    Q = build_process_noise_discrete_white_noise(dt=10.0, sigma_accel=1e-6)
    R = build_measurement_noise(pos_sigma=0.01, vel_sigma=1e-5)
    return UnscentedKalmanFilter(x0=x0, P0=P0, Q=Q, R=R)


def test_predict_moves_state_along_dynamics():
    """After predict(), the filter's mean should match the process
    model's propagation of the prior mean."""
    x0 = _circular_leo_state()
    ukf = _make_filter(x0.copy())

    expected = propagate_rk4(x0, dt=10.0)
    ukf.predict(dt=10.0)

    np.testing.assert_allclose(ukf.x, expected, rtol=1e-6, atol=1e-6)


def test_predict_grows_covariance():
    """Predict step should increase (or at least not shrink)
    uncertainty, since it adds process noise."""
    x0 = _circular_leo_state()
    ukf = _make_filter(x0.copy())

    trace_before = np.trace(ukf.P)
    ukf.predict(dt=10.0)
    trace_after = np.trace(ukf.P)

    assert trace_after >= trace_before


def test_update_reduces_covariance():
    """Incorporating a measurement should shrink uncertainty relative
    to the predicted covariance."""
    x0 = _circular_leo_state()
    ukf = _make_filter(x0.copy())

    ukf.predict(dt=10.0)
    trace_pred = np.trace(ukf.P)

    z = ukf.x + np.random.normal(scale=0.01, size=6)
    ukf.update(z)
    trace_updated = np.trace(ukf.P)

    assert trace_updated < trace_pred


def test_filter_converges_toward_truth_over_many_steps():
    """Running predict/update against a slightly-off initial guess,
    with noisy truth-based measurements, should converge the estimate
    toward the true trajectory."""
    rng = np.random.default_rng(42)

    x_true = _circular_leo_state()
    x0_guess = x_true + np.array([1.0, -1.0, 0.5, 1e-4, -1e-4, 5e-5])
    ukf = _make_filter(x0_guess, P_scale=1.0)

    dt = 10.0
    errors = []
    for _ in range(50):
        x_true = propagate_rk4(x_true, dt)
        ukf.predict(dt)

        z = x_true + rng.normal(scale=[0.01] * 3 + [1e-5] * 3)
        ukf.update(z)

        errors.append(np.linalg.norm(ukf.x[:3] - x_true[:3]))

    # Error should generally shrink — compare mean of first 5 vs last 5.
    assert np.mean(errors[-5:]) < np.mean(errors[:5])


def test_covariance_stays_positive_definite():
    """Over many predict/update cycles, P should remain a valid
    (positive-definite) covariance matrix — guards against the
    Cholesky-failure/divergence case."""
    rng = np.random.default_rng(7)
    x_true = _circular_leo_state()
    ukf = _make_filter(x_true.copy())

    dt = 10.0
    for _ in range(100):
        x_true = propagate_rk4(x_true, dt)
        ukf.predict(dt)
        z = x_true + rng.normal(scale=[0.01] * 3 + [1e-5] * 3)
        ukf.update(z)

        eigvals = np.linalg.eigvalsh(ukf.P)
        assert np.all(eigvals > 0), "Covariance lost positive-definiteness"


def test_update_stores_innovation_for_diagnostics():
    """update() should populate last_innovation / last_innovation_cov
    for use by diagnostics.compute_nis."""
    x0 = _circular_leo_state()
    ukf = _make_filter(x0.copy())
    ukf.predict(dt=10.0)

    z = ukf.x + np.array([0.01, 0.0, 0.0, 0.0, 0.0, 0.0])
    ukf.update(z)

    assert ukf.last_innovation is not None
    assert ukf.last_innovation_cov is not None
    assert ukf.last_innovation_cov.shape == (6, 6)
