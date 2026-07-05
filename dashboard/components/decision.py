"""Decision card component."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from ab_testing_framework.analysis import AbTestResult


def render_decision_card(result: "AbTestResult", alpha: float) -> None:
    ci = result.confidence_interval
    is_sig = result.z_test.p_value < alpha
    is_positive = ci.lower_bound > 0

    if is_sig and is_positive:
        card_cls, label = "positive", "Significant · Deploy"
    elif is_sig and not is_positive:
        card_cls, label = "negative", "Significant · Do not deploy"
    else:
        card_cls, label = "neutral", "Not significant · Hold"

    st.markdown(
        f"""
        <div class="decision-card {card_cls}">
            <div class="decision-label">{label}</div>
            <p class="decision-text">{result.recommendation}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
