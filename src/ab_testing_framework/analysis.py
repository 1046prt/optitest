"""High-level orchestration for A/B testing."""

from __future__ import annotations

from dataclasses import dataclass

from .confidence_interval import ConfidenceInterval, calculate_ci
from .effect_size import EffectSizeResult, calculate_effect_size
from .metrics import ConversionMetrics, calculate_metrics
from .power_analysis import PowerAnalysisResult, analyze_power
from .validation import ExperimentInput, validate_input
from .z_test import ZTestResult, perform_z_test


@dataclass(frozen=True)
class AbTestResult:
    experiment: ExperimentInput
    metrics: ConversionMetrics
    z_test: ZTestResult
    confidence_interval: ConfidenceInterval
    effect_size: EffectSizeResult
    power_analysis: PowerAnalysisResult
    decision: str
    recommendation: str
    summary: str

    @property
    def is_statistically_significant(self) -> bool:
        return bool(self.z_test.p_value < self.experiment.alpha)


def _build_recommendation(
    metrics: ConversionMetrics,
    z_test: ZTestResult,
    ci: ConfidenceInterval,
    experiment: ExperimentInput,
) -> str:
    """
    Build a plain-English recommendation covering all four decision cases:

    - Significant + CI fully above zero  → deploy
    - Significant + CI fully below zero  → do not deploy (negative effect)
    - Significant + CI spans zero        → inconclusive (borderline case)
    - Not significant                    → hold / collect more data
    """
    sig = z_test.p_value < experiment.alpha

    if sig and ci.lower_bound > 0:
        rel = metrics.relative_improvement
        rel_str = f"{rel:.1%}" if rel is not None else "N/A"
        return (
            f"Deploy Version B. Conversion increased by {rel_str} "
            f"and the {int(ci.confidence_level * 100)}% confidence interval "
            "is fully positive."
        )

    if sig and ci.upper_bound < 0:
        return (
            "Do not deploy Version B. The effect is statistically significant "
            "but negative — Version B performs worse than the control."
        )

    if sig:
        # p < alpha but CI spans zero — borderline; both conditions must hold
        return (
            "Results are inconclusive. The p-value crossed the threshold but "
            "the confidence interval spans zero, suggesting the true effect "
            "may be negligible. Collect more data before deciding."
        )

    return (
        "Hold the rollout or collect more data. The observed lift is not "
        f"statistically significant at α = {experiment.alpha:.2f}."
    )


def run_ab_test(
    visitors_a: int | float,
    conversions_a: int | float,
    visitors_b: int | float,
    conversions_b: int | float,
    alpha: float = 0.05,
    alternative: str = "two-sided",
) -> AbTestResult:
    """
    Run a complete two-proportion A/B test.

    Parameters
    ----------
    visitors_a, conversions_a:
        Visitor and conversion counts for the control group.
    visitors_b, conversions_b:
        Visitor and conversion counts for the treatment group.
    alpha:
        Significance level (default 0.05).
    alternative:
        Hypothesis direction — ``"two-sided"`` (default), ``"larger"``
        (treatment > control), or ``"smaller"`` (treatment < control).

    Returns
    -------
    AbTestResult
        Fully populated, frozen result dataclass.
    """
    if alternative not in {"two-sided", "larger", "smaller"}:
        raise ValueError(
            "alternative must be one of: 'two-sided', 'larger', 'smaller'"
        )

    experiment = validate_input(
        visitors_a=visitors_a,
        conversions_a=conversions_a,
        visitors_b=visitors_b,
        conversions_b=conversions_b,
        alpha=alpha,
    )
    metrics            = calculate_metrics(experiment)
    z_test             = perform_z_test(experiment, alternative=alternative)
    confidence_interval = calculate_ci(experiment)
    effect_size        = calculate_effect_size(experiment)
    power_analysis     = analyze_power(
        visitors_a=experiment.visitors_a,
        conversions_a=experiment.conversions_a,
        visitors_b=experiment.visitors_b,
        conversions_b=experiment.conversions_b,
        alpha=experiment.alpha,
    )

    decision = (
        "Reject H\u2080" if z_test.p_value < experiment.alpha
        else "Fail to reject H\u2080"
    )
    recommendation = _build_recommendation(
        metrics, z_test, confidence_interval, experiment
    )
    summary = (
        f"A/B test completed with z = {z_test.z_score:.3f}, "
        f"p = {z_test.p_value:.4f} ({alternative}), "
        f"absolute lift = {metrics.absolute_difference:.2%}."
    )

    return AbTestResult(
        experiment=experiment,
        metrics=metrics,
        z_test=z_test,
        confidence_interval=confidence_interval,
        effect_size=effect_size,
        power_analysis=power_analysis,
        decision=decision,
        recommendation=recommendation,
        summary=summary,
    )
