from __future__ import annotations

import math

import pytest

from ab_testing_framework.analysis import run_ab_test
from ab_testing_framework.chi_square import perform_chi_square_test
from ab_testing_framework.confidence_interval import calculate_ci
from ab_testing_framework.effect_size import calculate_effect_size
from ab_testing_framework.metrics import calculate_conversion_rate
from ab_testing_framework.power_analysis import analyze_power, estimate_power, estimate_sample_size
from ab_testing_framework.validation import validate_input
from ab_testing_framework.z_test import perform_z_test


@pytest.mark.parametrize(
    "experiment",
    [
        validate_input(100, 0, 100, 0),
        validate_input(100, 100, 100, 100),
    ],
)
def test_boundary_rate_cases_stay_finite(experiment):
    metrics = run_ab_test(
        experiment.visitors_a,
        experiment.conversions_a,
        experiment.visitors_b,
        experiment.conversions_b,
    )

    assert math.isfinite(metrics.z_test.p_value)
    assert math.isfinite(metrics.z_test.z_score)
    assert math.isfinite(metrics.chi_square.p_value)
    assert math.isfinite(metrics.chi_square.chi2_stat)
    assert math.isfinite(metrics.confidence_interval.lower_bound)
    assert math.isfinite(metrics.confidence_interval.upper_bound)
    assert math.isfinite(metrics.effect_size.cohens_h)


def test_calculate_conversion_rate_rejects_zero_divisor():
    with pytest.raises(ValueError, match="visitors must be greater than zero"):
        calculate_conversion_rate(1, 0)


def test_validate_input_rejects_non_numeric_values():
    with pytest.raises(ValueError, match="must be an integer"):
        validate_input("bad", 1, 10, 1)


@pytest.mark.parametrize(
    "visitors_a, conversions_a, visitors_b, conversions_b",
    [
        (100, 0, 100, 0),
        (100, 100, 100, 100),
        (1000, 10, 1000, 15),
    ],
)
def test_analysis_functions_handle_boundary_inputs(visitors_a, conversions_a, visitors_b, conversions_b):
    experiment = validate_input(visitors_a, conversions_a, visitors_b, conversions_b)

    z_test = perform_z_test(experiment)
    chi_square = perform_chi_square_test(experiment)
    confidence_interval = calculate_ci(experiment)
    effect_size = calculate_effect_size(experiment)
    power = analyze_power(visitors_a, conversions_a, visitors_b, conversions_b)

    assert math.isfinite(z_test.p_value)
    assert math.isfinite(chi_square.p_value)
    assert confidence_interval.lower_bound <= confidence_interval.upper_bound
    assert math.isfinite(effect_size.cohens_h)
    assert 0.0 <= power.power <= 1.0


def test_z_test_smaller_branch_returns_left_tail_probability():
    experiment = validate_input(1000, 120, 1000, 80)

    smaller = perform_z_test(experiment, alternative="smaller")
    two_sided = perform_z_test(experiment, alternative="two-sided")

    assert smaller.p_value < two_sided.p_value
    assert smaller.z_score < 0


def test_estimate_power_returns_alpha_for_equal_rates():
    assert estimate_power(1000, 50, 1000, 50) == pytest.approx(0.05)


def test_estimate_sample_size_rejects_invalid_ratio():
    with pytest.raises(ValueError, match="ratio must be greater than zero"):
        estimate_sample_size(0.05, 0.06, ratio=0)


def test_estimate_sample_size_rejects_invalid_expected_rate():
    with pytest.raises(ValueError, match="expected_rate must be between 0 and 1"):
        estimate_sample_size(0.05, 1.0)


def test_estimate_power_zero_effect_branch(monkeypatch):
    monkeypatch.setattr("ab_testing_framework.power_analysis.proportion_effectsize", lambda *args, **kwargs: 0.0)

    assert estimate_power(100, 5, 100, 5) == pytest.approx(0.05)


def test_estimate_sample_size_zero_effect_branch(monkeypatch):
    monkeypatch.setattr("ab_testing_framework.power_analysis.proportion_effectsize", lambda *args, **kwargs: 0.0)

    with pytest.raises(ValueError, match="no detectable effect"):
        estimate_sample_size(0.1, 0.1)
