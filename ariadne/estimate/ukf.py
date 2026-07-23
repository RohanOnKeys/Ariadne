"""
ukf.py

Unscented Kalman Filter (UKF) core for orbit state estimation.

Turns noisy, direct position/velocity observations into a filtered
state estimate (position + velocity) and its uncertainty (covariance),
using the J2-perturbed two-body dynamics model in `dynamics.py` as the
process model and an identity measurement model (GPS-like sensor).

Uses the scaled unscented transform (Van der Merwe form) for sigma
point generation.
"""

import numpy as np

from ariadne.estimate.dynamics import propagate_rk4


class UnscentedKalmanFilter:
    """
    Unscented Kalman Filter for 6-state [x, y, z, vx, vy, vz] orbit
    estimation with a direct position/velocity measurement model.

    Attributes:
        n: state dimension (6).
        alpha, beta, kappa: sigma point spread/weighting parameters.
        x: current state estimate, 6-vector.
        P: current state covariance, 6x6.
        Q: process noise covariance, 6x6.
        R: measurement noise covariance, 6x6.
    """

    def __init__(self, x0: np.ndarray, P0: np.ndarray, Q: np.ndarray,
                 R: np.ndarray, alpha: float = 1e-3, beta: float = 2.0,
                 kappa: float = 0.0):
        """
        Initialize the filter.

        Args:
            x0: initial state estimate, 6-vector [x, y, z, vx, vy, vz].
            P0: initial state covariance, 6x6. Should not be too tight —
                an overconfident initial covariance can cause early
                divergence before the filter has enough updates to
                correct itself.
            Q: process noise covariance, 6x6 (see noise_models.py).
            R: measurement noise covariance, 6x6 (see noise_models.py).
            alpha: sigma point spread parameter, typically small
                positive value (1e-4 to 1). Controls how far sigma
                points spread from the mean.
            beta: incorporates prior knowledge of state distribution;
                2.0 is optimal for Gaussian distributions.
            kappa: secondary scaling parameter, typically 0 or 3-n.
        """
        self.n = x0.shape[0]
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa

        self.x = x0.astype(float).copy()
        self.P = P0.astype(float).copy()
        self.Q = Q.astype(float).copy()
        self.R = R.astype(float).copy()

        self._compute_lambda_and_weights()

        # Track the innovation and its covariance from the most recent
        # update, for use by diagnostics.py (NIS check).
        self.last_innovation = None
        self.last_innovation_cov = None

    def _compute_lambda_and_weights(self) -> None:
        """
        Compute the scaling parameter lambda and the sigma point mean
        and covariance weight vectors (Wm, Wc), per the scaled
        unscented transform (Van der Merwe).
        """
        n = self.n
        self.lam = self.alpha**2 * (n + self.kappa) - n

        self.Wm = np.full(2 * n + 1, 1.0 / (2 * (n + self.lam)))
        self.Wc = np.full(2 * n + 1, 1.0 / (2 * (n + self.lam)))
        self.Wm[0] = self.lam / (n + self.lam)
        self.Wc[0] = self.lam / (n + self.lam) + (1 - self.alpha**2 + self.beta)

    def _generate_sigma_points(self, x: np.ndarray, P: np.ndarray) -> np.ndarray:
        """
        Generate the 2n+1 sigma points for the given mean and
        covariance, via Cholesky decomposition of the scaled
        covariance.

        Guards against a non-positive-definite P (which can arise from
        numerical drift over many predict/update cycles) by
        symmetrizing P and adding a small jitter term before the
        Cholesky decomposition, retrying with increasing jitter if
        needed.

        Args:
            x: mean, n-vector.
            P: covariance, nxn.

        Returns:
            (2n+1) x n array of sigma points, one per row.
        """
        n = self.n
        scale = n + self.lam

        # Symmetrize to guard against numerical asymmetry.
        P_sym = 0.5 * (P + P.T)

        jitter = 0.0
        for attempt in range(5):
            try:
                sqrt_P = np.linalg.cholesky((scale) * (P_sym + jitter * np.eye(n)))
                break
            except np.linalg.LinAlgError:
                jitter = 1e-10 if jitter == 0.0 else jitter * 10
        else:
            raise np.linalg.LinAlgError(
                "Covariance not positive-definite even after jitter "
                "regularization — check for filter divergence."
            )

        sigma_points = np.zeros((2 * n + 1, n))
        sigma_points[0] = x
        for i in range(n):
            sigma_points[i + 1] = x + sqrt_P[:, i]
            sigma_points[n + i + 1] = x - sqrt_P[:, i]

        return sigma_points

    def predict(self, dt: float) -> None:
        """
        Propagate the state estimate and covariance forward by dt
        seconds, using the J2-perturbed two-body process model.

        Args:
            dt: timestep, seconds.
        """
        sigma_points = self._generate_sigma_points(self.x, self.P)

        # Propagate each sigma point through the nonlinear dynamics.
        propagated = np.array([propagate_rk4(sp, dt) for sp in sigma_points])

        # Recombine into predicted mean and covariance.
        x_pred = np.sum(self.Wm[:, None] * propagated, axis=0)

        P_pred = self.Q.copy()
        for i in range(2 * self.n + 1):
            diff = propagated[i] - x_pred
            P_pred += self.Wc[i] * np.outer(diff, diff)

        self.x = x_pred
        self.P = P_pred
        # Stash propagated sigma points for reuse in update() so we
        # don't regenerate/re-propagate them redundantly.
        self._last_propagated_sigma_points = propagated

    def update(self, z: np.ndarray) -> None:
        """
        Incorporate a new measurement, updating the state estimate and
        covariance. Also stores the innovation and its covariance for
        the NIS diagnostic (see diagnostics.py).

        Uses an identity measurement model: the sensor observes
        position and velocity directly (GPS-like), so h(x) = x and no
        separate sigma-point re-propagation through h() is needed
        beyond reusing the predicted sigma points.

        Args:
            z: measurement, 6-vector [x, y, z, vx, vy, vz].
        """
        sigma_points = self._last_propagated_sigma_points
        # Identity measurement model: predicted measurements equal the
        # propagated state sigma points.
        z_sigma = sigma_points

        z_pred = np.sum(self.Wm[:, None] * z_sigma, axis=0)

        Pzz = self.R.copy()
        Pxz = np.zeros((self.n, self.n))
        for i in range(2 * self.n + 1):
            dz = z_sigma[i] - z_pred
            dx = sigma_points[i] - self.x
            Pzz += self.Wc[i] * np.outer(dz, dz)
            Pxz += self.Wc[i] * np.outer(dx, dz)

        K = Pxz @ np.linalg.inv(Pzz)

        innovation = z - z_pred
        self.x = self.x + K @ innovation
        self.P = self.P - K @ Pzz @ K.T
        # Re-symmetrize to guard against numerical asymmetry drift.
        self.P = 0.5 * (self.P + self.P.T)

        self.last_innovation = innovation
        self.last_innovation_cov = Pzz
