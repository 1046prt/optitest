"""Confidence interval utilities for two-proportion comparisons."""

from __future__ import annotations

from dataclasses import dataclass

from scipy.stats import norm

from .validation import ExperimentInput


@dataclass(frozen=True)
class ConfidenceInterval:
    lower_bound: float
    upper_bound: float
    margin_of_error: float
    confidence_level: float


def calculate_ci(
    experiment: ExperimentInput,
    confidence_level: float = 0.95,
) -> ConfidenceInterval:
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1")

    rate_a = experiment.conversions_a / experiment.visitors_a
    rate_b = experiment.conversions_b / experiment.visitors_b
    difference = rate_b - rate_a
    standard_error = (
        rate_a * (1 - rate_a) / experiment.visitors_a
        + rate_b * (1 - rate_b) / experiment.visitors_b
    ) ** 0.5
    z_critical = norm.ppf(1 - (1 - confidence_level) / 2)
    margin_of_error = z_critical * standard_error

    return ConfidenceInterval(
        lower_bound=difference - margin_of_error,
        upper_bound=difference + margin_of_error,
        margin_of_error=margin_of_error,
        confidence_level=confidence_level,
    )
