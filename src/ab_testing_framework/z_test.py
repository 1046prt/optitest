"""Two-proportion z-test implementation."""

from __future__ import annotations

from dataclasses import dataclass

from scipy.stats import norm

from .validation import ExperimentInput


@dataclass(frozen=True)
class ZTestResult:
    z_score: float
    p_value: float
    pooled_rate: float
    alternative: str


def perform_z_test(
    experiment: ExperimentInput,
    alternative: str = "two-sided",
) -> ZTestResult:
    successes_a = experiment.conversions_a
    successes_b = experiment.conversions_b
    n_a = experiment.visitors_a
    n_b = experiment.visitors_b

    pooled_rate = (successes_a + successes_b) / (n_a + n_b)
    standard_error = (pooled_rate * (1 - pooled_rate) * (1 / n_a + 1 / n_b)) ** 0.5
    observed_difference = (successes_b / n_b) - (successes_a / n_a)

    if standard_error == 0:
        z_score = 0.0 if observed_difference == 0 else float("inf")
    else:
        z_score = observed_difference / standard_error

    if alternative == "larger":
        p_value = 1 - norm.cdf(z_score)
    elif alternative == "smaller":
        p_value = norm.cdf(z_score)
    elif alternative == "two-sided":
        p_value = 2 * (1 - norm.cdf(abs(z_score)))
    else:
        raise ValueError("alternative must be one of: larger, smaller, two-sided")

    return ZTestResult(
        z_score=z_score,
        p_value=p_value,
        pooled_rate=pooled_rate,
        alternative=alternative,
    )
