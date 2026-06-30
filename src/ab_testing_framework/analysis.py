"""High-level orchestration for A/B testing.

This module is the main entry point for programmatic use of the framework.
:func:`run_ab_test` wires together every sub-module — validation, metrics,
z-test, chi-square test, confidence interval, effect size, and power analysis
— and returns a single immutable :class:`AbTestResult` dataclass.

Typical usage::

    from ab_testing_framework import run_ab_test

    result = run_ab_test(
        visitors_a=10_000, conversions_a=450,
        visitors_b=10_000, conversions_b=520,
    )
    print(result.decision)          # "Reject H₀"
    print(result.recommendation)    # "Deploy Version B …"
    print(result.chi_square.p_value)
"""

from __future__ import annotations

from dataclasses import dataclass

from .chi_square import ChiSquareResult, perform_chi_square_test
from .confidence_interval import ConfidenceInterval, calculate_ci
from .effect_size import EffectSizeResult, calculate_effect_size
from .metrics import ConversionMetrics, calculate_metrics
from .power_analysis import PowerAnalysisResult, analyze_power
from .validation import ExperimentInput, validate_input
from .z_test import ZTestResult, perform_z_test


@dataclass(frozen=True)
class AbTestResult:
    """Complete, immutable result of a two-proportion A/B test.

    Attributes
    ----------
    experiment:
        The validated input parameters used to run the test.
    metrics:
        Conversion rates, absolute lift, and relative improvement.
    z_test:
        Z-score, p-value, pooled rate, and alternative hypothesis direction.
    chi_square:
        Chi-square statistic, p-value, Cramér's V, and Yates correction flag.
    confidence_interval:
        Wald CI for the lift (rate_B − rate_A).
    effect_size:
        Absolute difference, relative improvement, and Cohen's h.
    power_analysis:
        Observed power and required sample size per group.
    decision:
        ``"Reject H₀"`` or ``"Fail to reject H₀"``, driven by the z-test p-value.
    recommendation:
        Plain-English business recommendation.
    summary:
        One-line statistical summary suitable for logging or email.
    """

    experiment: ExperimentInput
    metrics: ConversionMetrics
    z_test: ZTestResult
    chi_square: ChiSquareResult
    confidence_interval: ConfidenceInterval
    effect_size: EffectSizeResult
    power_analysis: PowerAnalysisResult
    decision: str
    recommendation: str
    summary: str

    @property
    def is_statistically_significant(self) -> bool:
        """``True`` when the z-test p-value < alpha.

        Note: this checks the p-value threshold only.  A ``True`` value does
        *not* imply a positive effect — use ``confidence_interval.lower_bound > 0``
        alongside this to confirm direction before deploying.
        """
        return bool(self.z_test.p_value < self.experiment.alpha)


def _build_recommendation(
    metrics: ConversionMetrics,
    z_test: ZTestResult,
    ci: ConfidenceInterval,
    experiment: ExperimentInput,
) -> str:
    """Build a plain-English recommendation covering all four decision cases.

    - Significant + CI fully above zero  → deploy
    - Significant + CI fully below zero  → do not deploy (negative effect)
    - Significant + CI spans zero        → inconclusive (borderline)
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
    """Run a complete two-proportion A/B test.

    Runs a z-test, chi-square test, confidence interval, effect size, and
    power analysis in a single call and returns everything in one immutable
    result object.

    Parameters
    ----------
    visitors_a, conversions_a:
        Visitor and conversion counts for the control group.
    visitors_b, conversions_b:
        Visitor and conversion counts for the treatment group.
    alpha:
        Significance level (default 0.05).
    alternative:
        Hypothesis direction for the z-test — ``"two-sided"`` (default),
        ``"larger"`` (treatment > control), or ``"smaller"``
        (treatment < control).  The chi-square test is always two-sided.

    Returns
    -------
    AbTestResult
        Fully populated, frozen result dataclass.

    Raises
    ------
    ValueError
        If inputs fail validation or *alternative* is not recognised.
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
    metrics             = calculate_metrics(experiment)
    z_test              = perform_z_test(experiment, alternative=alternative)
    chi_square          = perform_chi_square_test(experiment)
    confidence_interval = calculate_ci(experiment)
    effect_size         = calculate_effect_size(experiment)
    power_analysis      = analyze_power(
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
        f"χ² = {chi_square.chi2_stat:.3f}, "
        f"absolute lift = {metrics.absolute_difference:.2%}."
    )

    return AbTestResult(
        experiment=experiment,
        metrics=metrics,
        z_test=z_test,
        chi_square=chi_square,
        confidence_interval=confidence_interval,
        effect_size=effect_size,
        power_analysis=power_analysis,
        decision=decision,
        recommendation=recommendation,
        summary=summary,
    )
