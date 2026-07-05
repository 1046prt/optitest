"""Chart rendering component."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from ab_testing_framework.visualization import (
    bar_chart,
    confidence_plot,
    distribution_plot,
    histogram,
    z_score_plot,
)

if TYPE_CHECKING:
    from ab_testing_framework.analysis import AbTestResult


def render_charts(result: "AbTestResult") -> None:
    r1l, r1r = st.columns(2)
    with r1l:
        st.plotly_chart(bar_chart(result), use_container_width=True)
    with r1r:
        st.plotly_chart(confidence_plot(result), use_container_width=True)

    r2l, r2r = st.columns(2)
    with r2l:
        st.plotly_chart(z_score_plot(result), use_container_width=True)
    with r2r:
        st.plotly_chart(distribution_plot(result), use_container_width=True)

    st.plotly_chart(histogram(result), use_container_width=True)
