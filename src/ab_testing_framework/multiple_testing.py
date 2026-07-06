"""Multiple testing correction for A/B/C/D experiments.

The problem
-----------
When you run several hypothesis tests simultaneously (e.g. comparing variants
B, C, and D each against a control A), the probability of at least one false
positive grows with the number of comparisons:

    P(at least one false positive) = 1 − (1 − α)^k

For k=5 tests at α=0.05, this is already 23%.  Multiple testing correction
methods adjust the raw p-values (or the rejection threshold) to control either:

- **FWER** — Family-Wise Error Rate: probability of *any* false positive.
- **FDR**  — False Discovery Rate: expected *proportion* of false positives
  among all rejected hypotheses.

Methods provided
----------------
``"bonferroni"``
    Multiply each p-value by k (or equivalently divide α by k).
    Controls FWER.  Very conservative — best when all tests are independent
    and you cannot afford any false positive.

``"holm"``
    Stepwise Bonferroni (Holm-Bonferroni).  Sort p-values ascending;
    compare the i-th smallest p to α / (k − i + 1).  Uniformly more
    powerful than plain Bonferroni while still controlling FWER.

``"benjamini_hochberg"``
    BH procedure (1995).  Controls FDR at level α.  More powerful than
    FWER-controlling methods when many tests are run.  The standard choice
    for exploratory multi-variant experiments.

Usage
-----
::

    from ab_testing_framework.multiple_testing import correct_pvalues

    raw = [0.03, 0.048, 0.20, 0.001, 0.12]
    result = correct_pvalues(raw, alpha=0.05, method="benjamini_hochberg")
    print(result.adjusted_pvalues)
    print(result.rejected)          # [True, False, False, True, False]
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MultipleTestingResult:
    """Adjusted p-values and rejection decisions for a family of tests.

    Attributes
    ----------
    method:
        The correction method applied: ``"bonferroni"``, ``"holm"``, or
        ``"benjamini_hochberg"``.
    alpha:
        The family-wise significance level used.
    raw_pvalues:
        Original p-values in the order they were supplied.
    adjusted_pvalues:
        Corrected p-values, clipped to [0, 1].  For Bonferroni and Holm these
        are adjusted p-values directly comparable to *alpha*.  For BH they are
        the BH-adjusted p-values (q-values).
    rejected:
        ``True`` for each test whose adjusted p-value < *alpha*.
    num_comparisons:
        Total number of tests in the family (k).
    """

    method: str
    alpha: float
    raw_pvalues: tuple[float, ...]
    adjusted_pvalues: tuple[float, ...]
    rejected: tuple[bool, ...]
    num_comparisons: int

    @property
    def num_rejected(self) -> int:
        """Number of null hypotheses rejected after correction."""
        return sum(self.rejected)


def _bonferroni(pvalues: list[float], alpha: float) -> tuple[list[float], list[bool]]:
    k = len(pvalues)
    adjusted = [min(p * k, 1.0) for p in pvalues]
    rejected = [p_adj < alpha for p_adj in adjusted]
    return adjusted, rejected


def _holm(pvalues: list[float], alpha: float) -> tuple[list[float], list[bool]]:
    k = len(pvalues)
    order = sorted(range(k), key=lambda i: pvalues[i])
    adjusted = [0.0] * k
    rejected = [False] * k

    running_max = 0.0
    for rank, idx in enumerate(order):
        factor = k - rank
        adj = min(pvalues[idx] * factor, 1.0)
        # Holm adjusted p-values must be non-decreasing (step-down enforcement)
        running_max = max(running_max, adj)
        adjusted[idx] = running_max

    for i in range(k):
        rejected[i] = adjusted[i] < alpha

    return adjusted, rejected


def _benjamini_hochberg(pvalues: list[float], alpha: float) -> tuple[list[float], list[bool]]:
    k = len(pvalues)
    order = sorted(range(k), key=lambda i: pvalues[i])
    adjusted = [0.0] * k

    # BH step-up: work from largest p-value downward
    running_min = 1.0
    for rank in range(k - 1, -1, -1):
        idx = order[rank]
        bh_val = pvalues[idx] * k / (rank + 1)
        running_min = min(running_min, bh_val)
        adjusted[idx] = min(running_min, 1.0)

    rejected = [adj < alpha for adj in adjusted]
    return adjusted, rejected


_METHODS = {
    "bonferroni":        _bonferroni,
    "holm":              _holm,
    "benjamini_hochberg": _benjamini_hochberg,
}


def correct_pvalues(
    pvalues: list[float],
    alpha: float = 0.05,
    method: str = "benjamini_hochberg",
) -> MultipleTestingResult:
    """Apply a multiple testing correction to a list of raw p-values.

    Parameters
    ----------
    pvalues:
        Raw p-values from each individual test.  Order is preserved in the
        output — adjusted p-values correspond positionally to raw p-values.
    alpha:
        Family-wise significance level.  Default 0.05.
    method:
        Correction method.  One of:

        - ``"bonferroni"`` — most conservative, controls FWER.
        - ``"holm"`` — stepwise Bonferroni, controls FWER, more powerful.
        - ``"benjamini_hochberg"`` — controls FDR, most powerful (default).

    Returns
    -------
    MultipleTestingResult
        Immutable result with adjusted p-values, rejection flags, and metadata.

    Raises
    ------
    ValueError
        If *pvalues* is empty, any p-value is outside [0, 1],
        *alpha* is outside (0, 1), or *method* is not recognised.

    Examples
    --------
    >>> from ab_testing_framework.multiple_testing import correct_pvalues
    >>> raw = [0.03, 0.048, 0.20, 0.001]
    >>> r = correct_pvalues(raw, alpha=0.05, method="holm")
    >>> r.rejected
    (True, False, False, True)
    >>> r.num_rejected
    2
    """
    if not pvalues:
        raise ValueError("pvalues must not be empty")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1 (exclusive)")
    if method not in _METHODS:
        raise ValueError(
            f"method must be one of: {', '.join(sorted(_METHODS))}. Got {method!r}."
        )
    for i, p in enumerate(pvalues):
        if not 0.0 <= p <= 1.0:
            raise ValueError(
                f"p-value at index {i} is {p}, which is outside [0, 1]."
            )

    adjusted, rejected = _METHODS[method](list(pvalues), alpha)

    return MultipleTestingResult(
        method=method,
        alpha=alpha,
        raw_pvalues=tuple(pvalues),
        adjusted_pvalues=tuple(adjusted),
        rejected=tuple(rejected),
        num_comparisons=len(pvalues),
    )
