"""Power and sample-size estimation for A/B tests."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

from .validation import ExperimentInput, validate_input


@dataclass(frozen=True)
class PowerAnalysisResult:
    control_rate: float
    treatment_rate: float
    effect_size_h: float
    power: float
    required_sample_size_per_group: int
    alpha: float
    target_power: float


def estimate_power(
    visitors_a: int | float,
    conversions_a: int | float,
    visitors_b: int | float,
    conversions_b: int | float,
    alpha: float = 0.05,
) -> float:
    experiment = validate_input(
        visitors_a=visitors_a,
        conversions_a=conversions_a,
        visitors_b=visitors_b,
        conversions_b=conversions_b,
        alpha=alpha,
    )
    rate_a = experiment.conversions_a / experiment.visitors_a
    rate_b = experiment.conversions_b / experiment.visitors_b
    effect_size = proportion_effectsize(rate_b, rate_a)
    if effect_size == 0:
        return float(alpha)
    solver = NormalIndPower()
    return float(solver.power(effect_size=effect_size, nobs1=experiment.visitors_a, alpha=alpha, ratio=experiment.visitors_b / experiment.visitors_a))


def estimate_sample_size(
    baseline_rate: float,
    expected_rate: float,
    alpha: float = 0.05,
    target_power: float = 0.8,
    ratio: float = 1.0,
) -> int:
    if not 0 < baseline_rate < 1:
        raise ValueError("baseline_rate must be between 0 and 1")
    if not 0 < expected_rate < 1:
        raise ValueError("expected_rate must be between 0 and 1")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not 0 < target_power < 1:
        raise ValueError("target_power must be between 0 and 1")
    if ratio <= 0:
        raise ValueError("ratio must be greater than zero")

    effect_size = proportion_effectsize(expected_rate, baseline_rate)
    if effect_size == 0:
        raise ValueError(
            "baseline_rate and expected_rate are equal — there is no detectable effect to power against. "
            "Provide a non-zero expected lift."
        )
    solver = NormalIndPower()
    nobs = solver.solve_power(effect_size=effect_size, power=target_power, alpha=alpha, ratio=ratio)
    return int(ceil(nobs))


def analyze_power(
    visitors_a: int | float,
    conversions_a: int | float,
    visitors_b: int | float,
    conversions_b: int | float,
    alpha: float = 0.05,
    target_power: float = 0.8,
) -> PowerAnalysisResult:
    experiment = validate_input(
        visitors_a=visitors_a,
        conversions_a=conversions_a,
        visitors_b=visitors_b,
        conversions_b=conversions_b,
        alpha=alpha,
    )
    control_rate = experiment.conversions_a / experiment.visitors_a
    treatment_rate = experiment.conversions_b / experiment.visitors_b
    effect_size_h = float(proportion_effectsize(treatment_rate, control_rate))
    solver = NormalIndPower()
    if effect_size_h == 0:
        power = float(alpha)
        required_sample_size_per_group = experiment.visitors_a
    elif control_rate <= 0 or control_rate >= 1 or treatment_rate <= 0 or treatment_rate >= 1:
        # Cannot compute sample size when rates are at the boundary;
        # power is still valid from the effect size and observed n.
        power = float(
            solver.power(
                effect_size=effect_size_h,
                nobs1=experiment.visitors_a,
                alpha=alpha,
                ratio=experiment.visitors_b / experiment.visitors_a,
            )
        )
        required_sample_size_per_group = experiment.visitors_a
    else:
        power = float(
            solver.power(
                effect_size=effect_size_h,
                nobs1=experiment.visitors_a,
                alpha=alpha,
                ratio=experiment.visitors_b / experiment.visitors_a,
            )
        )
        required_sample_size_per_group = estimate_sample_size(
            baseline_rate=control_rate,
            expected_rate=treatment_rate,
            alpha=alpha,
            target_power=target_power,
            ratio=experiment.visitors_b / experiment.visitors_a,
        )
    return PowerAnalysisResult(
        control_rate=control_rate,
        treatment_rate=treatment_rate,
        effect_size_h=float(effect_size_h),
        power=power,
        required_sample_size_per_group=required_sample_size_per_group,
        alpha=alpha,
        target_power=target_power,
    )
