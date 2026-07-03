"""Input validation helpers for A/B testing experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class ExperimentInputDict(TypedDict):
    visitors_a: int
    conversions_a: int
    visitors_b: int
    conversions_b: int
    alpha: float


class ExperimentInputModel(BaseModel):
    visitors_a: int
    conversions_a: int
    visitors_b: int
    conversions_b: int
    alpha: float = Field(default=0.05)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _coerce_whole_numbers(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise TypeError("Experiment input must be provided as a mapping")

        coerced = dict(data)
        for field_name in ("visitors_a", "conversions_a", "visitors_b", "conversions_b"):
            coerced[field_name] = _coerce_int(coerced[field_name], field_name)
        return coerced

    @model_validator(mode="after")
    def _validate_ranges(self) -> "ExperimentInputModel":
        if self.visitors_a <= 0 or self.visitors_b <= 0:
            raise ValueError("visitor counts must be greater than zero")
        if self.conversions_a < 0 or self.conversions_b < 0:
            raise ValueError("conversion counts cannot be negative")
        if self.conversions_a > self.visitors_a:
            raise ValueError("conversions_a cannot exceed visitors_a")
        if self.conversions_b > self.visitors_b:
            raise ValueError("conversions_b cannot exceed visitors_b")
        if not 0 < self.alpha < 1:
            raise ValueError("alpha must be between 0 and 1")
        return self


@dataclass(frozen=True)
class ExperimentInput:
    visitors_a: int
    conversions_a: int
    visitors_b: int
    conversions_b: int
    alpha: float = 0.05

    def to_dict(self) -> ExperimentInputDict:
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
    try:
        model = ExperimentInputModel.model_validate(
            {
                "visitors_a": visitors_a,
                "conversions_a": conversions_a,
                "visitors_b": visitors_b,
                "conversions_b": conversions_b,
                "alpha": alpha,
            }
        )
    except ValidationError as exc:
        first_message = exc.errors()[0].get("msg", "Invalid experiment input")
        if first_message.startswith("Value error, "):
            first_message = first_message.removeprefix("Value error, ")
        raise ValueError(first_message) from exc

    return ExperimentInput(
        visitors_a=model.visitors_a,
        conversions_a=model.conversions_a,
        visitors_b=model.visitors_b,
        conversions_b=model.conversions_b,
        alpha=float(model.alpha),
    )
