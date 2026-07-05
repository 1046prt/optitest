"""Key metrics and power analysis warning components."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from dashboard.utils.helpers import _pval_badge, _rel_lift_display

if TYPE_CHECKING:
    from ab_testing_framework.analysis import AbTestResult


def render_key_metrics(result: "AbTestResult", alpha: float) -> None:
    m = result.metrics
    rel_display = _rel_lift_display(m.relative_improvement)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Control rate", f"{m.conversion_rate_a:.2%}")
    c2.metric("Treatment rate", f"{m.conversion_rate_b:.2%}")
    c3.metric(
        "Absolute lift",
        f"{m.absolute_difference:.2%}",
        delta=f"{rel_display} relative" if m.relative_improvement is not None else "N/A",
        delta_color="normal" if (m.relative_improvement or 0) >= 0 else "inverse",
    )
    c4.metric("P-value", f"{result.z_test.p_value:.4f}")

    st.markdown(
        f"<div style='margin-top:0.4rem;margin-bottom:0.25rem;font-size:0.84rem;"
        f"color:var(--text-secondary);'>Significance: {_pval_badge(result.z_test.p_value)}</div>",
        unsafe_allow_html=True,
    )


def render_underpowered_warning(
    power_analysis: object,
    visitors_a: int,
    visitors_b: int,
) -> None:
    pa = power_analysis
    if pa.power < 0.8:
        needed = pa.required_sample_size_per_group
        current = min(int(visitors_a), int(visitors_b))
        st.markdown(
            f"<div class='warn-block'>"
            f"<strong>⚠ Underpowered sample.</strong> Observed power is {pa.power:.1%} — "
            f"below the 80% threshold. You need ~<strong>{needed:,}</strong> visitors per group; "
            f"currently running {current:,}. Results may not be reliable."
            f"</div>",
            unsafe_allow_html=True,
        )
