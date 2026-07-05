"""Statistical detail table components."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from dashboard.utils.helpers import _lift_class, _rel_lift_display

if TYPE_CHECKING:
    from ab_testing_framework.analysis import AbTestResult


def render_stat_tables(result: "AbTestResult", alpha: float, visitors_a: int, visitors_b: int) -> None:
    m = result.metrics
    pa = result.power_analysis
    ci = result.confidence_interval
    lift_cls = _lift_class(m.absolute_difference)

    with st.columns(2)[0]:
        st.markdown(
            f"""
            <div class="stat-block">
              <table class="stat-table">
                <tr><td class="stat-key">Z-score</td>
                    <td class="stat-val">{result.z_test.z_score:.4f}</td></tr>
                <tr><td class="stat-key">P-value (z-test)</td>
                    <td class="stat-val">{result.z_test.p_value:.4f}</td></tr>
                <tr><td class="stat-key">Chi-square (χ²)</td>
                    <td class="stat-val">{result.chi_square.chi2_stat:.4f}</td></tr>
                <tr><td class="stat-key">P-value (chi-square)</td>
                    <td class="stat-val">{result.chi_square.p_value:.4f}</td></tr>
                <tr><td class="stat-key">Significance level (α)</td>
                    <td class="stat-val">{alpha:.2f}</td></tr>
                <tr><td class="stat-key">95% CI — lower</td>
                    <td class="stat-val {_lift_class(ci.lower_bound)}">{ci.lower_bound:.4%}</td></tr>
                <tr><td class="stat-key">95% CI — upper</td>
                    <td class="stat-val {_lift_class(ci.upper_bound)}">{ci.upper_bound:.4%}</td></tr>
                <tr><td class="stat-key">Decision</td>
                    <td class="stat-val">{result.decision}</td></tr>
              </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.columns(2)[1]:
        st.markdown(
            f"""
            <div class="stat-block">
              <table class="stat-table">
                <tr><td class="stat-key">Absolute lift</td>
                    <td class="stat-val {lift_cls}">{m.absolute_difference:.4%}</td></tr>
                <tr><td class="stat-key">Relative lift</td>
                    <td class="stat-val {lift_cls}">{_rel_lift_display(m.relative_improvement)}</td></tr>
                <tr><td class="stat-key">Cohen's h</td>
                    <td class="stat-val">{result.effect_size.cohens_h:.4f}</td></tr>
                <tr><td class="stat-key">Cramér's V</td>
                    <td class="stat-val">{result.chi_square.cramers_v:.4f}</td></tr>
                <tr><td class="stat-key">Yates correction</td>
                    <td class="stat-val">{'yes' if result.chi_square.yates_correction else 'no'}</td></tr>
                <tr><td class="stat-key">Observed power</td>
                    <td class="stat-val {'positive' if pa.power >= 0.8 else 'negative'}">{pa.power:.1%}</td></tr>
                <tr><td class="stat-key">Required n / group</td>
                    <td class="stat-val">{pa.required_sample_size_per_group:,}</td></tr>
                <tr><td class="stat-key">Target power</td>
                    <td class="stat-val">{pa.target_power:.0%}</td></tr>
              </table>
            </div>
            """,
            unsafe_allow_html=True,
        )
