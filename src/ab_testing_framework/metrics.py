"""Core conversion metrics."""

from __future__ import annotations

from dataclasses import dataclass

from .validation import ExperimentInput


@dataclass(frozen=True)
class ConversionMetrics:
    conversion_rate_a: float
    conversion_rate_b: float
    absolute_difference: float
    # None when control rate is zero (avoids inf / NaN in display layer)
    relative_improvement: float | None


def calculate_conversion_rate(conversions: int, visitors: int) -> float:
    if visitors <= 0:
        raise ValueError("visitors must be greater than zero")
    return conversions / visitors


def calculate_metrics(experiment: ExperimentInput) -> ConversionMetrics:
    rate_a = calculate_conversion_rate(experiment.conversions_a, experiment.visitors_a)
    rate_b = calculate_conversion_rate(experiment.conversions_b, experiment.visitors_b)
    absolute_difference = rate_b - rate_a
    relative_improvement: float | None = (
        absolute_difference / rate_a if rate_a > 0 else None
    )
    return ConversionMetrics(
        conversion_rate_a=rate_a,
        conversion_rate_b=rate_b,
        absolute_difference=absolute_difference,
        relative_improvement=relative_improvement,
    )
