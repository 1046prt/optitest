"""Input validation helpers for A/B testing experiments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExperimentInput:
    visitors_a: int
    conversions_a: int
    visitors_b: int
    conversions_b: int
    alpha: float = 0.05

    def to_dict(self) -> dict[str, float | int]:
        return {
            "visitors_a": self.visitors_a,
            "conversions_a": self.conversions_a,
            "visitors_b": self.visitors_b,
            "conversions_b": self.conversions_b,
            "alpha": self.alpha,
        }


def _coerce_int(value: int | float, field_name: str) -> int:
    try:
        coerced = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if coerced != value:
        raise ValueError(f"{field_name} must be a whole number")
    return coerced


def validate_input(
    visitors_a: int | float,
    conversions_a: int | float,
    visitors_b: int | float,
    conversions_b: int | float,
    alpha: float = 0.05,
) -> ExperimentInput:
    visitors_a_i = _coerce_int(visitors_a, "visitors_a")
    conversions_a_i = _coerce_int(conversions_a, "conversions_a")
    visitors_b_i = _coerce_int(visitors_b, "visitors_b")
    conversions_b_i = _coerce_int(conversions_b, "conversions_b")

    if visitors_a_i <= 0 or visitors_b_i <= 0:
        raise ValueError("visitor counts must be greater than zero")
    if conversions_a_i < 0 or conversions_b_i < 0:
        raise ValueError("conversion counts cannot be negative")
    if conversions_a_i > visitors_a_i:
        raise ValueError("conversions_a cannot exceed visitors_a")
    if conversions_b_i > visitors_b_i:
        raise ValueError("conversions_b cannot exceed visitors_b")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    return ExperimentInput(
        visitors_a=visitors_a_i,
        conversions_a=conversions_a_i,
        visitors_b=visitors_b_i,
        conversions_b=conversions_b_i,
        alpha=float(alpha),
    )
