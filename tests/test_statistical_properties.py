from __future__ import annotations

from hypothesis import given, settings, strategies as st
from pytest import approx

from ab_testing_framework.analysis import run_ab_test
from ab_testing_framework.chi_square import perform_chi_square_test
from ab_testing_framework.confidence_interval import calculate_ci
from ab_testing_framework.effect_size import calculate_effect_size
from ab_testing_framework.metrics import calculate_metrics
from ab_testing_framework.power_analysis import estimate_power
from ab_testing_framework.validation import validate_input
from ab_testing_framework.z_test import perform_z_test


@st.composite
def valid_experiments(draw):
    visitors_a = draw(st.integers(min_value=1, max_value=20_000))
    visitors_b = draw(st.integers(min_value=1, max_value=20_000))
    conversions_a = draw(st.integers(min_value=0, max_value=visitors_a))
    conversions_b = draw(st.integers(min_value=0, max_value=visitors_b))
    alpha = draw(st.sampled_from([0.01, 0.05, 0.1]))
    return validate_input(visitors_a, conversions_a, visitors_b, conversions_b, alpha=alpha)


@settings(max_examples=60, deadline=None)
@given(valid_experiments())
def test_metrics_and_effect_size_remain_consistent(experiment):
    metrics = calculate_metrics(experiment)
    effect_size = calculate_effect_size(experiment)

    assert metrics.absolute_difference == approx(metrics.conversion_rate_b - metrics.conversion_rate_a)
    if metrics.conversion_rate_a == 0:
        assert metrics.relative_improvement is None
        assert effect_size.relative_improvement is None
    else:
        expected_relative = metrics.absolute_difference / metrics.conversion_rate_a
        assert metrics.relative_improvement == approx(expected_relative)
        assert effect_size.relative_improvement == approx(expected_relative)


@settings(max_examples=60, deadline=None)
@given(valid_experiments())
def test_z_test_two_sided_matches_chi_square_and_is_symmetric(experiment):
    swapped = validate_input(
        experiment.visitors_b,
        experiment.conversions_b,
        experiment.visitors_a,
        experiment.conversions_a,
        alpha=experiment.alpha,
    )

    z_original = perform_z_test(experiment, alternative="two-sided")
    z_swapped = perform_z_test(swapped, alternative="two-sided")
    chi_square = perform_chi_square_test(experiment, yates=False)

    assert z_original.p_value == approx(chi_square.p_value, rel=1e-10, abs=1e-12)
    assert z_original.p_value == approx(z_swapped.p_value, rel=1e-10, abs=1e-12)
    assert z_original.z_score == approx(-z_swapped.z_score, rel=1e-10, abs=1e-12)


@settings(max_examples=40, deadline=None)
@given(valid_experiments())
def test_confidence_interval_contains_observed_lift(experiment):
    metrics = calculate_metrics(experiment)
    ci = calculate_ci(experiment)

    assert ci.lower_bound <= ci.upper_bound
    assert ci.lower_bound <= metrics.absolute_difference <= ci.upper_bound


@settings(max_examples=40, deadline=None)
@given(valid_experiments())
def test_run_ab_test_and_power_stay_finite(experiment):
    result = run_ab_test(
        experiment.visitors_a,
        experiment.conversions_a,
        experiment.visitors_b,
        experiment.conversions_b,
        alpha=experiment.alpha,
    )
    power = estimate_power(
        experiment.visitors_a,
        experiment.conversions_a,
        experiment.visitors_b,
        experiment.conversions_b,
        alpha=experiment.alpha,
    )

    assert result.is_statistically_significant == (result.z_test.p_value < experiment.alpha)
    assert 0.0 <= power <= 1.0
    assert result.confidence_interval.lower_bound <= result.confidence_interval.upper_bound
