"""About page — statistical methods, assumptions, and limitations."""

from __future__ import annotations

import sys

import streamlit as st

from dashboard.config import APP_TITLE, FAVICON_PATH, SRC_PATH
from dashboard.components.layout import render_theme_toggle
from dashboard.utils.theme import inject_css
from dashboard.utils.state import init_state

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


def run_about() -> None:
    st.set_page_config(
        page_title=f"About — {APP_TITLE}",
        page_icon=str(FAVICON_PATH),
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    init_state()
    inject_css()
    render_theme_toggle()

    st.markdown(
        """
        <div class="page-header">
            <h2>About Split Testing Suite</h2>
            <p>Statistical methods, assumptions, and limitations</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── What it does ───────────────────────────────────────────────────────────
    st.markdown("<div class='section-label'>What it does</div>", unsafe_allow_html=True)
    st.markdown(
        """
Split Testing Suite is a statistically rigorous A/B testing framework for
comparing a control variant (A) and a treatment variant (B).  It combines
multiple complementary methods into one analysis and surfaces the results
through an interactive dashboard.

**One call gives you everything:**
- Two-proportion z-test with configurable hypothesis direction
- Chi-square test of independence (with automatic Yates correction)
- Sample Ratio Mismatch (SRM) detection
- Wald confidence interval for the lift
- Cohen's h effect size
- Power analysis and minimum sample size planning
- Bayesian complement — P(B > A)
- Multiple testing correction (Bonferroni, Holm, Benjamini-Hochberg)
- Sequential / early stopping (O'Brien-Fleming, SPRT)
        """
    )

    # ── Decision logic ─────────────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Decision logic</div>", unsafe_allow_html=True)
    st.markdown(
        """
A **"Deploy"** recommendation requires **both** conditions:

1. **p-value < α** — the z-test rejects H₀ at the chosen significance level.
2. **CI lower bound > 0** — the confidence interval for the lift is entirely positive.

The p-value alone is not sufficient.  A significant p-value with a CI that
spans zero indicates the effect may be negligible in practical terms.
        """
    )

    # ── Statistical methods ────────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Statistical methods</div>", unsafe_allow_html=True)

    with st.expander("Two-proportion z-test"):
        st.markdown(
            r"""
The z-test uses a **pooled standard error** under H₀:

$$p_{pool} = \frac{c_A + c_B}{n_A + n_B}, \quad SE = \sqrt{p_{pool}(1-p_{pool})\left(\frac{1}{n_A}+\frac{1}{n_B}\right)}$$

$$z = \frac{\hat{p}_B - \hat{p}_A}{SE}$$

The pooled SE is appropriate for testing H₀: p_A = p_B.

**Alternatives:**
- `two-sided` — H₁: p_B ≠ p_A (default, most conservative)
- `larger` — H₁: p_B > p_A (use only when direction is pre-specified)
- `smaller` — H₁: p_B < p_A

**Assumptions:** Large samples (n·p ≥ 5 and n·(1−p) ≥ 5 for each cell),
independent observations, binary outcome.
            """
        )

    with st.expander("Confidence interval"):
        st.markdown(
            r"""
The Wald interval uses an **unpooled standard error** — appropriate for
estimating the difference directly (rather than testing under H₀):

$$SE_{unpooled} = \sqrt{\frac{\hat{p}_A(1-\hat{p}_A)}{n_A} + \frac{\hat{p}_B(1-\hat{p}_B)}{n_B}}$$

$$CI = (\hat{p}_B - \hat{p}_A) \pm z_{\alpha/2} \cdot SE_{unpooled}$$

This intentionally uses a different SE from the z-test — the two tests
answer complementary questions.
            """
        )

    with st.expander("Chi-square test"):
        st.markdown(
            r"""
The 2×2 Pearson chi-square test of independence is mathematically equivalent
to the two-sided z-test (χ² = z² without Yates correction).  It is provided
as a cross-check and for users who prefer the contingency-table framing.

**Yates continuity correction** is applied automatically when any expected
cell count is below 5 (small samples), reducing over-rejection of H₀.

**Cramér's V** is a normalised effect size in [0, 1] derived from χ²:

$$V = \sqrt{\frac{\chi^2}{n}}$$

Interpretation (Cohen 1988): small ≈ 0.10, medium ≈ 0.30, large ≈ 0.50.
            """
        )

    with st.expander("Effect size — Cohen's h"):
        st.markdown(
            r"""
Cohen's h applies an arcsine transformation to stabilise the variance of
proportions before computing a standardised difference:

$$h = 2\arcsin(\sqrt{\hat{p}_B}) - 2\arcsin(\sqrt{\hat{p}_A})$$

Range: approximately −π to π.  Sign: positive when B > A.

**Conventional thresholds (Cohen 1988):**

| |h| | Magnitude |
|-------|-----------|
| < 0.20 | Small |
| < 0.50 | Medium |
| ≥ 0.50 | Large |

Cohen's h is preferable to raw differences when comparing experiments with
very different baseline rates.
            """
        )

    with st.expander("Power analysis"):
        st.markdown(
            r"""
Power is estimated via `statsmodels.stats.power.NormalIndPower` using the
normal approximation to the binomial.

**Observed power** — probability that the test would detect the observed lift
with the current sample sizes and α.  Values below 0.80 indicate the experiment
may be underpowered.

**Required sample size** — minimum n per group to achieve the target power
(default 80%) at the observed effect size and α.  Computed by solving:

$$n = \text{NormalIndPower.solve\_power}(h, \text{power}=0.80, \alpha)$$

**Assumptions:** Large-sample normal approximation, equal or known variance
between groups.
            """
        )

    with st.expander("Bayesian A/B testing"):
        st.markdown(
            r"""
The Bayesian module uses a **Beta-Binomial conjugate model**.  With a uniform
prior Beta(1, 1), the posterior for each group's true rate is:

$$\text{posterior}_A \sim \text{Beta}(1 + c_A,\ 1 + n_A - c_A)$$
$$\text{posterior}_B \sim \text{Beta}(1 + c_B,\ 1 + n_B - c_B)$$

**P(B > A)** is estimated by Monte Carlo:
draw 100,000 samples from each posterior and compute the fraction where B > A.

**Expected loss** — the expected regret of choosing the wrong variant.
Choosing B when it is actually worse costs E[max(rate_A − rate_B, 0)].

P(B > A) ≥ 0.95 is a common threshold for a "Deploy" decision in Bayesian
experimentation frameworks.
            """
        )

    with st.expander("Sample Ratio Mismatch (SRM)"):
        st.markdown(
            r"""
SRM occurs when the observed traffic split differs significantly from the
intended ratio.  It is detected with a **chi-square goodness-of-fit test**:

$$\chi^2 = \frac{(n_A - E_A)^2}{E_A} + \frac{(n_B - E_B)^2}{E_B}$$

where $E_A = (n_A + n_B) \cdot r_A$ is the expected count under the intended
ratio $r_A$.

**Severity:**
- p ≥ 0.05 → no SRM
- 0.01 ≤ p < 0.05 → warning (minor imbalance)
- p < 0.01 → critical (strong evidence of SRM — do not act on results)

**Common causes:** bot traffic filtered differently per variant, caching
artefacts, session replay tools, redirect-based assignment dropping users.
            """
        )

    with st.expander("Multiple testing correction"):
        st.markdown(
            r"""
Running k simultaneous tests at level α inflates the family-wise false
positive rate to 1 − (1 − α)^k.  Three correction methods are available:

| Method | Controls | Power |
|--------|----------|-------|
| Bonferroni | FWER | Lowest |
| Holm (stepwise Bonferroni) | FWER | Medium |
| Benjamini-Hochberg | FDR | Highest |

**FDR** (False Discovery Rate) — expected proportion of false positives among
all rejections.  Use BH when running many variant comparisons and you can
tolerate a controlled fraction of false discoveries.

**FWER** — probability of *any* false positive.  Use Bonferroni or Holm when
no false positive is acceptable.
            """
        )

    with st.expander("Sequential testing / early stopping"):
        st.markdown(
            r"""
Standard tests assume you look at the data exactly once.  Peeking repeatedly
inflates the false positive rate.  Two methods handle this:

**O'Brien-Fleming (OBF)**
Pre-allocates the α budget across K planned interim looks.  At look k of K:

$$\alpha_k = 2\left(1 - \Phi\left(\frac{z_{\alpha/2}}{\sqrt{k/K}}\right)\right)$$

Very conservative early (spending little α), nearly recovering the full α at
the final look.  Standard in clinical trials and large-scale web experiments.

**SPRT (Sequential Probability Ratio Test)**
Computes a likelihood ratio Λ comparing H₁ (effect of size δ) against H₀
(no effect).  Stop when:
- Λ ≥ (1 − β) / α → reject H₀
- Λ ≤ β / (1 − α) → accept H₀

Controls both α and β at every look without a pre-specified sample size.
            """
        )

    # ── Limitations ────────────────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Limitations and assumptions</div>", unsafe_allow_html=True)
    st.markdown(
        """
- **Binary outcomes only.** The framework tests conversion rates (0/1 outcomes).
  Continuous metrics (revenue, session time) require t-tests or Mann-Whitney.
- **Independence.** Each visitor must appear in only one group, with no
  network effects between users.
- **Large-sample approximation.** The z-test and CI rely on the normal
  approximation to the binomial.  When n·p < 5 for any cell, Yates correction
  is applied for the chi-square test, but consider Fisher's exact test for
  very small samples.
- **No temporal effects.** The framework does not account for novelty effects,
  day-of-week variation, or seasonality.  Run experiments for at least one full
  business cycle.
- **Pre-specified hypotheses.** Choosing the alternative hypothesis or deciding
  the MDE *after* seeing data invalidates the test. Decide these upfront.
        """
    )

    # ── Tech stack ─────────────────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Technology</div>", unsafe_allow_html=True)
    st.markdown(
        """
| Component | Library |
|-----------|---------|
| Statistical tests | scipy, statsmodels |
| Bayesian sampling | numpy |
| Input validation | pydantic v2 |
| Visualisation | plotly |
| Dashboard | streamlit |
| Python | ≥ 3.10 |
        """
    )


if __name__ == "__main__":
    run_about()
