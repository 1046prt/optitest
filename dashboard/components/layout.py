"""Layout components: page header, footnote, and theme toggle."""

from __future__ import annotations

import streamlit as st

from dashboard.utils.theme import inject_css, toggle_theme


def render_theme_toggle() -> None:
    """Render a small dark/light toggle button in the top-right corner."""
    is_dark = st.session_state.get("theme", "dark") == "dark"
    label   = "☀ Light mode" if is_dark else "🌙 Dark mode"
    _, btn_col = st.columns([10, 1])
    with btn_col:
        if st.button(label, key="_theme_toggle", help="Switch between dark and light theme"):
            toggle_theme()
            st.rerun()


def render_page_header(title: str, subtitle: str) -> None:
    inject_css()
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
