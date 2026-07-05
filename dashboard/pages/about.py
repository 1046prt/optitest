"""About page for the Split Testing Suite dashboard."""

from __future__ import annotations

import streamlit as st

from dashboard.config import APP_TITLE, FAVICON_PATH

st.set_page_config(
    page_title=f"About — {APP_TITLE}",
    page_icon=str(FAVICON_PATH),
    layout="wide",
)

st.markdown("## About Split Testing Suite")
st.markdown(
    """
    **Split Testing Suite** is a statistically sound A/B testing framework
    with analysis and dashboard support.

    It runs a complete frequentist analysis:
    - Two-proportion z-test (two-sided, one-sided, or directional)
    - 95% confidence interval for the lift
    - Effect size — Cohen's h
    - Power analysis and required sample size
    - Decision recommendation with plain-English explanation
    - Exportable Markdown and JSON reports
    """
)
st.markdown(
    """
    ### Decision logic

    A "Deploy" recommendation requires two conditions to both be true:

    1. p-value < α
    2. The confidence interval lower bound > 0

    Passing the p-value threshold alone is not sufficient — the CI must fully exclude zero.
    """
)
