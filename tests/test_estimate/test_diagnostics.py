"""Tests for ariadne.estimate.diagnostics."""

import numpy as np

from ariadne.estimate.diagnostics import (
    compute_nees, compute_nis, chi_square_bounds, run_nis_consistency_check,
)


def test_compute_nees_zero_error_gives_zero():
    """Perfect estimate (error = 0) should give NEES = 0."""
    x_true = np.array([1.0, 2.0, 3.0, 0.1, 0.2, 0.3])
    P = np.eye(6)
    nees = compute_nees(x_true, x_true.copy(), P)
    assert nees == 0.0


def test_compute_nis_zero_innovation_gives_zero():
    """Zero innovation should give NIS = 0."""
    v = np.zeros(6)
    S = np.eye(6)
    assert compute_nis(v, S) == 0.0


def test_chi_square_bounds_ordering():
    """Lower bound must be strictly less than upper bound, and both
    positive, for standard confidence levels."""
    lower, upper = chi_square_bounds(dof=6, confidence=0.95)
    assert 0 < lower < upper


def test_nis_sequence_from_correctly_tuned_filter_is_consistent():
    """NIS values drawn from a chi-square(6) distribution (simulating
    a correctly-tuned filter) should be classified 'consistent'."""
    rng = np.random.default_rng(0)
    nis_sequence = rng.chisquare(df=6, size=500)

    result = run_nis_consistency_check(nis_sequence, dof=6, confidence=0.95)
    assert result["verdict"] == "consistent"
    assert result["fraction_in_bound"] > 0.85


def test_nis_sequence_overconfident_filter_detected():
    """Inflated NIS values (simulating an overconfident filter, i.e.
    Q/R too small) should be classified 'overconfident'."""
    rng = np.random.default_rng(1)
    # Scale up chi-square draws to push them above the upper bound.
    nis_sequence = rng.chisquare(df=6, size=500) * 5.0

    result = run_nis_consistency_check(nis_sequence, dof=6, confidence=0.95)
    assert result["verdict"] == "overconfident"


def test_nis_sequence_underconfident_filter_detected():
    """Deflated NIS values (simulating an underconfident filter, i.e.
    Q/R too large) should be classified 'underconfident'."""
    rng = np.random.default_rng(2)
    nis_sequence = rng.chisquare(df=6, size=500) * 0.05

    result = run_nis_consistency_check(nis_sequence, dof=6, confidence=0.95)
    assert result["verdict"] == "underconfident"
