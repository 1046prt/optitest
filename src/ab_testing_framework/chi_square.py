"""Chi-square test of independence for two-proportion A/B tests.

Statistical background
----------------------
The 2×2 contingency table is:

                Converted   Not converted   Total
    Control         a            b            n_A
    Treatment       c            d            n_B
    Total         a+c          b+d           n_A+n_B

The Pearson chi-square statistic with 1 degree of freedom is:

    χ² = n * (|ad - bc| - n/2)²  /  [(a+c)(b+d)(a+b)(c+d)]     (with Yates)
    χ² = n * (ad - bc)²           /  [(a+c)(b+d)(a+b)(c+d)]     (without Yates)

Yates' continuity correction
    Applied by default when any expected cell count is < 5, or when
    ``yates=True`` is passed explicitly.  Reduces the tendency to over-reject
    H₀ with small samples.

Relationship to the z-test
    For a two-sided two-proportion z-test, χ² = z² (without Yates), so the
    two tests are mathematically equivalent and will produce the same p-value.
    The chi-square formulation is preferred when the data are naturally
    expressed as a contingency table.

Cramér's V
    A normalised effect size in [0, 1]:

        V = sqrt(χ² / (n * (k-1)))

    For a 2×2 table k=2, so V = sqrt(χ² / n).
    Interpretation (Cohen 1988): small ≈ 0.10, medium ≈ 0.30, large ≈ 0.50.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from scipy.stats import chi2

from .validation import ExperimentInput


@dataclass(frozen=True)
class ChiSquareResult:
    """Result of a chi-square test of independence.

    Attributes
    ----------
    chi2_stat:
        Pearson chi-square test statistic (with or without Yates correction).
    p_value:
        Two-sided p-value from the chi-square distribution with 1 degree of
        freedom.
    degrees_of_freedom:
        Always 1 for a 2×2 contingency table.
    yates_correction:
        Whether Yates' continuity correction was applied.
    cramers_v:
        Cramér's V effect size in [0, 1].
    expected_min:
        Smallest expected cell count in the 2×2 table.  Values below 5 suggest
        the chi-square approximation may be unreliable; consider Fisher's exact
        test instead.
    """

    chi2_stat: float
    p_value: float
    degrees_of_freedom: int
    yates_correction: bool
    cramers_v: float
    expected_min: float


def perform_chi_square_test(
    experiment: ExperimentInput,
    yates: bool | None = None,
) -> ChiSquareResult:
    """Perform a chi-square test of independence on a 2×2 contingency table.

    Parameters
    ----------
    experiment:
        Validated experiment inputs.
    yates:
        Whether to apply Yates' continuity correction.

        - ``True``  — always apply.
        - ``False`` — never apply.
        - ``None``  (default) — apply automatically when any expected cell
          count is < 5.

    Returns
    -------
    ChiSquareResult
        Immutable result with χ², p-value, Cramér's V, and diagnostic info.

    Notes
    -----
    The p-value is always two-sided.  If you need a one-sided test, use the
    z-test in ``z_test.py`` with ``alternative="larger"`` or ``"smaller"``.
    """
    a = experiment.conversions_a           # control   — converted
    b = experiment.visitors_a - a          # control   — not converted
    c = experiment.conversions_b           # treatment — converted
    d = experiment.visitors_b - c          # treatment — not converted
    n = experiment.visitors_a + experiment.visitors_b

    # ── expected cell counts under H₀ ────────────────────────────────────────
    row_a  = experiment.visitors_a
    row_b  = experiment.visitors_b
    col_c  = a + c   # total converted
    col_nc = b + d   # total not converted

    exp_a_c  = row_a * col_c  / n
    exp_a_nc = row_a * col_nc / n
    exp_b_c  = row_b * col_c  / n
    exp_b_nc = row_b * col_nc / n
    expected_min = min(exp_a_c, exp_a_nc, exp_b_c, exp_b_nc)

    # ── decide whether to apply Yates correction ─────────────────────────────
    apply_yates = (expected_min < 5) if yates is None else yates

    # ── compute χ² ───────────────────────────────────────────────────────────
    ad_minus_bc = a * d - b * c

    if apply_yates:
        # Yates: subtract n/2 from |ad - bc| before squaring
        numerator = (abs(ad_minus_bc) - n / 2) ** 2
    else:
        numerator = ad_minus_bc ** 2

    denominator = row_a * row_b * col_c * col_nc

    if denominator == 0:
        # Degenerate table: one row or column is all-zero
        chi2_stat = 0.0
    else:
        chi2_stat = n * numerator / denominator

    p_value = float(1 - chi2.cdf(chi2_stat, df=1))

    # ── Cramér's V ───────────────────────────────────────────────────────────
    # Use the uncorrected χ² for effect size (correction is a bias fix, not
    # part of the effect magnitude estimate)
    if denominator == 0:
        cramers_v = 0.0
    else:
        chi2_uncorrected = n * (ad_minus_bc ** 2) / denominator
        cramers_v = sqrt(chi2_uncorrected / n)

    return ChiSquareResult(
        chi2_stat=chi2_stat,
        p_value=p_value,
        degrees_of_freedom=1,
        yates_correction=apply_yates,
        cramers_v=cramers_v,
        expected_min=expected_min,
    )
