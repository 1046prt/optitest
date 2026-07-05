"""Layout components: page header and footnote."""

from __future__ import annotations

import streamlit as st


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="page-header">
            <h2>{title}</h2>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footnote(result: object) -> None:
    st.markdown(
        f"<p class='footnote'>"
        f"Decision rule: reject H₀ when p-value &lt; α and the lift confidence interval "
        f"excludes zero. Test is <strong>{result.z_test.alternative}</strong>. "
        f"Power calculated via statsmodels NormalIndPower."
        f"</p>",
        unsafe_allow_html=True,
    )
