"""
diagnostics.py

Filter consistency diagnostics: NEES and NIS.

NEES (Normalized Estimation Error Squared) checks the filter's
covariance against the *true* error — only usable in simulation, where
ground truth is known.

NIS (Normalized Innovation Squared) checks the filter's covariance
against the *innovation* (measurement residual) — usable with real
data, since it needs no ground truth. This is the check exposed
through the CLI's `od` command diagnostics flag.

Both statistics should follow a chi-square distribution under a
correctly-tuned filter; consistent over/under-bound violations are the
signal to retune Q or R (see noise_models.py).
"""

import numpy as np
from scipy.stats import chi2


def compute_nees(x_true: np.ndarray, x_est: np.ndarray, P: np.ndarray) -> float:
    """
    Compute the Normalized Estimation Error Squared for one epoch.

    NEES = e^T P^-1 e, where e = x_true - x_est.

    Only usable when ground truth is available (i.e. in simulation).

    Args:
        x_true: true state, n-vector.
        x_est: filter's estimated state, n-vector.
        P: filter's state covariance at this epoch, nxn.

    Returns:
        Scalar NEES value for this epoch.
    """
    e = x_true - x_est
    return float(e.T @ np.linalg.inv(P) @ e)


def compute_nis(innovation: np.ndarray, innovation_cov: np.ndarray) -> float:
    """
    Compute the Normalized Innovation Squared for one epoch.

    NIS = v^T S^-1 v, where v is the innovation (measurement residual)
    and S is the innovation covariance — both produced by
    UnscentedKalmanFilter.update() and stored as last_innovation /
    last_innovation_cov.

    Usable with real (non-simulated) data, since it requires no ground
    truth.

    Args:
        innovation: measurement residual, m-vector (from
            ukf.last_innovation).
        innovation_cov: innovation covariance, mxm (from
            ukf.last_innovation_cov).

    Returns:
        Scalar NIS value for this epoch.
    """
    v = innovation
    return float(v.T @ np.linalg.inv(innovation_cov) @ v)


def chi_square_bounds(dof: int, confidence: float = 0.95) -> tuple:
    """
    Compute the two-sided chi-square consistency bounds for a NEES or
    NIS sequence, at the given confidence level.

    A NEES/NIS value falling outside [lower, upper] at a given epoch
    is a statistically significant sign the filter is inconsistent at
    that epoch (see run_nis_consistency_check for the sequence-level
    interpretation).

    Args:
        dof: degrees of freedom — state dimension for NEES,
            measurement dimension for NIS.
        confidence: two-sided confidence level (default 0.95 = 95%).

    Returns:
        (lower_bound, upper_bound) tuple.
    """
    alpha = 1 - confidence
    lower = chi2.ppf(alpha / 2, dof)
    upper = chi2.ppf(1 - alpha / 2, dof)
    return lower, upper


def run_nis_consistency_check(nis_sequence: list, dof: int,
                              confidence: float = 0.95) -> dict:
    """
    Evaluate a full sequence of NIS values against the chi-square
    consistency bound and report whether the filter is over- or
    under-confident.

    A well-tuned filter should have roughly `confidence` fraction of
    NIS values fall inside the bound. Consistently exceeding the upper
    bound means the filter is overconfident (Q or R too small);
    consistently falling below the lower bound means it is
    underconfident (Q or R too large).

    Args:
        nis_sequence: list of NIS values, one per update epoch.
        dof: measurement dimension (6, for the GPS-like model).
        confidence: two-sided confidence level (default 0.95).

    Returns:
        dict with keys:
            'lower_bound', 'upper_bound': the chi-square bounds used.
            'fraction_in_bound': fraction of the sequence within bound.
            'verdict': one of 'consistent', 'overconfident',
                'underconfident', based on where violations cluster.
    """
    lower, upper = chi_square_bounds(dof, confidence)
    nis_array = np.asarray(nis_sequence)

    in_bound = (nis_array >= lower) & (nis_array <= upper)
    fraction_in_bound = float(np.mean(in_bound))

    above = np.mean(nis_array > upper)
    below = np.mean(nis_array < lower)

    if fraction_in_bound >= confidence - 0.05:
        verdict = "consistent"
    elif above > below:
        verdict = "overconfident"
    else:
        verdict = "underconfident"

    return {
        "lower_bound": lower,
        "upper_bound": upper,
        "fraction_in_bound": fraction_in_bound,
        "verdict": verdict,
    }
