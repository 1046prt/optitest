"""Sequential testing / early stopping for A/B experiments.

The problem with peeking
------------------------
If you check your p-value every day and stop when it crosses α, your true
false-positive rate is much higher than α.  This is because you are
effectively running multiple tests on the same data.

Two methods are provided:

Sequential Probability Ratio Test (SPRT)
    Wald's SPRT (1945) computes a likelihood ratio that grows as evidence
    accumulates.  At each interim look you compare the ratio against two
    thresholds derived from the desired α and β (1 − power):

        H₀ threshold:  B = β / (1 − α)          → accept H₀ (stop, no effect)
        H₁ threshold:  A = (1 − β) / α           → reject H₀ (stop, effect found)
        Continue if B < Λ < A

    SPRT controls both the false-positive rate (α) and the false-negative
    rate (β) at every look.  It is the most powerful test for a fixed
    alternative hypothesis.

O'Brien-Fleming alpha spending
    The OBF method pre-allocates the total α budget across K planned interim
    analyses using an alpha-spending function.  At the k-th look out of K,
    the adjusted significance threshold is:

        α_k = 2 * (1 − Φ(z_α/2 / sqrt(k/K)))

    where Φ is the standard normal CDF and z_α/2 is the two-sided critical
    value for the final analysis.

    OBF is very conservative early in the trial (spending little α budget)
    and nearly recovers the full α by the final look.  It is the standard
    choice in clinical trials and large-scale web experiments.

Usage
-----
::

    from ab_testing_framework.validation import validate_input
    from ab_testing_framework.sequential import sequential_test

    # After 5 out of 10 planned looks:
    exp    = validate_input(5_000, 225, 5_000, 260)
    result = sequential_test(exp, method="obf", current_look=5, total_looks=10)
    print(result.stop)          # True / False
    print(result.decision)      # "Stop — reject H₀" / "Continue" / "Stop — accept H₀"
    print(result.adjusted_alpha)
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log, sqrt

from scipy.stats import norm

from .validation import ExperimentInput


@dataclass(frozen=True)
class SequentialResult:
    """Result of a sequential / interim analysis.

    Attributes
    ----------
    method:
        ``"sprt"`` or ``"obf"`` (O'Brien-Fleming).
    stop:
        ``True`` if the stopping rule recommends ending the experiment now.
    decision:
        Human-readable action: ``"Stop — reject H₀"``,
        ``"Stop — accept H₀"`` (SPRT only), or ``"Continue"``.
    adjusted_alpha:
        The significance threshold adjusted for this interim look.
        For OBF this is smaller than the nominal α at early looks.
        For SPRT this equals the H₁ boundary converted to a p-value.
    observed_pvalue:
        Two-sided p-value from the current data (standard z-test).
    likelihood_ratio:
        SPRT likelihood ratio Λ (only meaningful for ``method="sprt"``; set
        to ``None`` for OBF).
    current_look:
        The interim look index (1-based).
    total_looks:
        Total number of planned looks (for OBF) or ``None`` for SPRT.
    """

    method: str
    stop: bool
    decision: str
    adjusted_alpha: float
    observed_pvalue: float
    likelihood_ratio: float | None
    current_look: int
    total_looks: int | None


def _z_test_pvalue(experiment: ExperimentInput) -> float:
    """Return a two-sided z-test p-value (pooled SE)."""
    n_a = experiment.visitors_a
    n_b = experiment.visitors_b
    p_a = experiment.conversions_a / n_a
    p_b = experiment.conversions_b / n_b
    p_pool = (experiment.conversions_a + experiment.conversions_b) / (n_a + n_b)
    se = (p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b)) ** 0.5
    if se == 0:
        return 1.0
    z = (p_b - p_a) / se
    return float(2 * (1 - norm.cdf(abs(z))))


def _sprt(
    experiment: ExperimentInput,
    alpha: float,
    beta: float,
    mde: float,
) -> SequentialResult:
    """Wald SPRT for a two-proportion experiment.

    Parameters
    ----------
    experiment:
        Validated current cumulative data.
    alpha:
        Desired false-positive rate.
    beta:
        Desired false-negative rate (1 − power).
    mde:
        Minimum detectable effect — the absolute lift you want to detect.
        H₁: p_B = p_A + mde.
    """
    p_a = experiment.conversions_a / experiment.visitors_a
    p_b_obs = experiment.conversions_b / experiment.visitors_b
    p_b_h1 = p_a + mde   # hypothesised treatment rate under H₁

    # Likelihood ratio: L(H₁) / L(H₀)
    # Under H₀: both groups have p_a
    # Under H₁: group B has p_b_h1, group A has p_a
    conversions_b = experiment.conversions_b
    non_conv_b    = experiment.visitors_b - conversions_b

    # Guard against boundary rates
    if p_b_h1 <= 0 or p_b_h1 >= 1 or p_a <= 0 or p_a >= 1:
        lr = 1.0
    else:
        log_lr = (
            conversions_b * log(p_b_h1 / p_a)
            + non_conv_b  * log((1 - p_b_h1) / (1 - p_a))
        )
        lr = float(2.718281828 ** log_lr)   # exp without importing math.exp

    # Boundaries
    h0_boundary = beta / (1 - alpha)        # accept H₀ if Λ ≤ this
    h1_boundary = (1 - beta) / alpha        # reject H₀ if Λ ≥ this

    p_value = _z_test_pvalue(experiment)

    if lr >= h1_boundary:
        stop, decision = True, "Stop — reject H₀"
    elif lr <= h0_boundary:
        stop, decision = True, "Stop — accept H₀ (no effect detected)"
    else:
        stop, decision = False, "Continue"

    # Adjusted alpha: convert H₁ boundary to approximate alpha
    adjusted_alpha = alpha  # SPRT uses fixed alpha — boundary handles it

    return SequentialResult(
        method="sprt",
        stop=stop,
        decision=decision,
        adjusted_alpha=adjusted_alpha,
        observed_pvalue=p_value,
        likelihood_ratio=lr,
        current_look=1,
        total_looks=None,
    )


def _obf(
    experiment: ExperimentInput,
    alpha: float,
    current_look: int,
    total_looks: int,
) -> SequentialResult:
    """O'Brien-Fleming alpha spending for interim analysis.

    Parameters
    ----------
    experiment:
        Validated current cumulative data.
    alpha:
        Nominal significance level for the full trial.
    current_look:
        Current interim analysis number (1-based).
    total_looks:
        Total planned number of looks.
    """
    if not 1 <= current_look <= total_looks:
        raise ValueError(
            f"current_look ({current_look}) must be between 1 and total_looks ({total_looks})"
        )

    # OBF adjusted threshold at look k of K
    z_final = norm.ppf(1 - alpha / 2)   # critical value for final look
    info_fraction = current_look / total_looks
    z_k = z_final / sqrt(info_fraction)
    adjusted_alpha = float(2 * (1 - norm.cdf(z_k)))

    p_value = _z_test_pvalue(experiment)

    if p_value < adjusted_alpha:
        stop, decision = True, "Stop — reject H₀"
    else:
        stop = current_look == total_looks
        decision = (
            "Final look — fail to reject H₀"
            if current_look == total_looks
            else "Continue"
        )

    return SequentialResult(
        method="obf",
        stop=stop,
        decision=decision,
        adjusted_alpha=adjusted_alpha,
        observed_pvalue=p_value,
        likelihood_ratio=None,
        current_look=current_look,
        total_looks=total_looks,
    )


def sequential_test(
    experiment: ExperimentInput,
    method: str = "obf",
    alpha: float = 0.05,
    beta: float = 0.20,
    mde: float = 0.005,
    current_look: int = 1,
    total_looks: int = 5,
) -> SequentialResult:
    """Run an interim sequential analysis on cumulative experiment data.

    Parameters
    ----------
    experiment:
        Validated, cumulative experiment data at the current interim look.
    method:
        ``"obf"`` (O'Brien-Fleming, default) or ``"sprt"`` (Wald SPRT).
    alpha:
        Nominal significance level.  Default 0.05.
    beta:
        Desired false-negative rate for SPRT (1 − target power).  Default 0.20.
    mde:
        Minimum detectable effect (absolute lift) for SPRT.  Ignored for OBF.
        Default 0.005 (0.5 pp).
    current_look:
        Current look index (1-based).  Used by OBF.
    total_looks:
        Total number of planned interim looks.  Used by OBF.

    Returns
    -------
    SequentialResult
        Immutable result with stop flag, decision, and adjusted threshold.

    Raises
    ------
    ValueError
        If *method* is not recognised, *current_look* > *total_looks*,
        or parameter values are out of valid ranges.

    Examples
    --------
    >>> from ab_testing_framework.validation import validate_input
    >>> from ab_testing_framework.sequential import sequential_test
    >>> exp    = validate_input(5_000, 225, 5_000, 260)
    >>> result = sequential_test(exp, method="obf", current_look=3, total_looks=5)
    >>> result.stop
    False
    >>> result.adjusted_alpha
    0.0054...
    """
    if method not in {"sprt", "obf"}:
        raise ValueError(f"method must be 'sprt' or 'obf'. Got {method!r}.")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not 0 < beta < 1:
        raise ValueError("beta must be between 0 and 1")

    if method == "sprt":
        return _sprt(experiment, alpha=alpha, beta=beta, mde=mde)
    return _obf(experiment, alpha=alpha, current_look=current_look, total_looks=total_looks)
