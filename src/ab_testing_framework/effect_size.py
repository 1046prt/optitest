"""Effect size calculations for A/B tests."""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, sqrt

from .validation import ExperimentInput


@dataclass(frozen=True)
class EffectSizeResult:
    absolute_difference: float
    relative_improvement: float
    cohens_h: float


def calculate_effect_size(experiment: ExperimentInput) -> EffectSizeResult:
    rate_a = experiment.conversions_a / experiment.visitors_a
    rate_b = experiment.conversions_b / experiment.visitors_b
    absolute_difference = rate_b - rate_a
    relative_improvement = absolute_difference / rate_a if rate_a > 0 else float("inf")
    cohens_h = 2 * asin(sqrt(rate_b)) - 2 * asin(sqrt(rate_a))

    return EffectSizeResult(
        absolute_difference=absolute_difference,
        relative_improvement=relative_improvement,
        cohens_h=cohens_h,
    )
