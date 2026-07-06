"""Bayesian A/B testing via the Beta-Binomial conjugate model.

Why Bayesian?
-------------
Frequentist hypothesis testing tells you the probability of observing data
*at least this extreme* under H₀ (the p-value).  This is often misread as
"the probability that B is better than A."

A Bayesian approach directly answers the question practitioners actually ask:

    **"Given what we observed, how likely is it that B is truly better than A?"**

Model
-----
We model each group's true conversion rate as a Beta distribution — the
conjugate prior for a Binomial likelihood.  A uniform (uninformative) prior
Beta(1, 1) is used by default, which means the posterior is driven entirely
by the data:

    posterior_A ~ Beta(α_prior + conversions_A,  β_prior + non_conversions_A)
    posterior_B ~ Beta(α_prior + conversions_B,  β_prior + non_conversions_B)

Key outputs
-----------
``prob_b_beats_a``
    The probability that B's true rate > A's true rate, estimated via Monte
    Carlo sampling.  This is the headline metric for business decisions.

``expected_loss_a``, ``expected_loss_b``
    The expected loss (regret) of choosing A or B respectively.  Choosing B
    when it is actually worse costs you ``E[max(rate_A - rate_B, 0)]``.
    The smaller of the two losses indicates the safer choice.

``credible_interval_a``, ``credible_interval_b``
    95% highest-density credible intervals for each group's true rate.

``posterior_mean_a``, ``posterior_mean_b``
    Posterior mean estimates for each group's true rate.

References
----------
- Evan Miller (2015) — "Formulas for Bayesian A/B Testing"
  https://www.evanmiller.org/bayesian-ab-testing.html
- Chris Stucchio (2015) — "Bayesian A/B Testing at VWO"
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .validation import ExperimentInput


@dataclass(frozen=True)
class BayesianResult:
    """Result of a Bayesian A/B test.

    Attributes
    ----------
    prob_b_beats_a:
        Monte Carlo estimate of P(rate_B > rate_A).  Values above 0.95 are
        conventionally treated as strong evidence to deploy B.
    prob_a_beats_b:
        Complement: P(rate_A > rate_B) = 1 − prob_b_beats_a.
    expected_loss_a:
        Expected loss (in percentage points) of deploying A when B might be
        better.  Lower is better.
    expected_loss_b:
        Expected loss of deploying B when A might be better.
    posterior_mean_a:
        Posterior mean of the Beta distribution for group A.
    posterior_mean_b:
        Posterior mean of the Beta distribution for group B.
    credible_interval_a:
        95% equal-tailed credible interval for group A's true rate.
    credible_interval_b:
        95% equal-tailed credible interval for group B's true rate.
    prior_alpha, prior_beta:
        Hyperparameters of the Beta prior used.
    samples:
        Number of Monte Carlo samples drawn.
    """

    prob_b_beats_a: float
    prob_a_beats_b: float
    expected_loss_a: float
    expected_loss_b: float
    posterior_mean_a: float
    posterior_mean_b: float
    credible_interval_a: tuple[float, float]
    credible_interval_b: tuple[float, float]
    prior_alpha: float
    prior_beta: float
    samples: int


def bayesian_test(
    experiment: ExperimentInput,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    samples: int = 100_000,
    seed: int | None = 42,
) -> BayesianResult:
    """Run a Bayesian A/B test using a Beta-Binomial conjugate model.

    Parameters
    ----------
    experiment:
        Validated experiment inputs.
    prior_alpha, prior_beta:
        Hyperparameters of the Beta prior.  Defaults to Beta(1, 1) — a
        uniform, uninformative prior.  To encode a weak belief that
        conversion rates cluster around 5%, use e.g. Beta(5, 95).
    samples:
        Number of Monte Carlo draws used to estimate probabilities and
        expected losses.  Default 100 000 gives ~0.1% precision.
    seed:
        Random seed for reproducibility.  Pass ``None`` for a random seed.

    Returns
    -------
    BayesianResult
        Immutable result with all posterior statistics.

    Raises
    ------
    ValueError
        If *prior_alpha* or *prior_beta* is not positive.

    Notes
    -----
    Time complexity is O(samples).  At 100 000 samples this runs in < 50 ms
    on a modern CPU.  The result is deterministic when *seed* is set.
    """
    if prior_alpha <= 0 or prior_beta <= 0:
        raise ValueError("prior_alpha and prior_beta must both be positive")

    # ── posterior parameters ──────────────────────────────────────────────────
    alpha_a = prior_alpha + experiment.conversions_a
    beta_a  = prior_beta  + (experiment.visitors_a - experiment.conversions_a)
    alpha_b = prior_alpha + experiment.conversions_b
    beta_b  = prior_beta  + (experiment.visitors_b - experiment.conversions_b)

    # ── posterior means ───────────────────────────────────────────────────────
    posterior_mean_a = alpha_a / (alpha_a + beta_a)
    posterior_mean_b = alpha_b / (alpha_b + beta_b)

    # ── 95% credible intervals (equal-tailed) ─────────────────────────────────
    from scipy.stats import beta as beta_dist  # local import — optional dep

    ci_a = (
        float(beta_dist.ppf(0.025, alpha_a, beta_a)),
        float(beta_dist.ppf(0.975, alpha_a, beta_a)),
    )
    ci_b = (
        float(beta_dist.ppf(0.025, alpha_b, beta_b)),
        float(beta_dist.ppf(0.975, alpha_b, beta_b)),
    )

    # ── Monte Carlo: draw from both posteriors ────────────────────────────────
    rng = np.random.default_rng(seed)
    draws_a = rng.beta(alpha_a, beta_a, size=samples)
    draws_b = rng.beta(alpha_b, beta_b, size=samples)

    # ── P(B > A) ──────────────────────────────────────────────────────────────
    prob_b_beats_a = float(np.mean(draws_b > draws_a))
    prob_a_beats_b = 1.0 - prob_b_beats_a

    # ── expected loss ─────────────────────────────────────────────────────────
    # Loss of choosing A when B is better: E[max(draws_b - draws_a, 0)]
    expected_loss_a = float(np.mean(np.maximum(draws_b - draws_a, 0.0)))
    # Loss of choosing B when A is better: E[max(draws_a - draws_b, 0)]
    expected_loss_b = float(np.mean(np.maximum(draws_a - draws_b, 0.0)))

    return BayesianResult(
        prob_b_beats_a=prob_b_beats_a,
        prob_a_beats_b=prob_a_beats_b,
        expected_loss_a=expected_loss_a,
        expected_loss_b=expected_loss_b,
        posterior_mean_a=float(posterior_mean_a),
        posterior_mean_b=float(posterior_mean_b),
        credible_interval_a=ci_a,
        credible_interval_b=ci_b,
        prior_alpha=prior_alpha,
        prior_beta=prior_beta,
        samples=samples,
    )
