"""Home page for the Split Testing Suite dashboard."""

from __future__ import annotations

import logging
import sys

import streamlit as st

from dashboard.config import APP_TITLE, FAVICON_PATH, SRC_PATH
from dashboard.utils.helpers import (
    _lift_class,
    _pval_badge,
    _rel_lift_display,
)

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=str(FAVICON_PATH),
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .hero {
        text-align: center;
        padding: 4rem 2rem 3rem 2rem;
    }
    .hero h1 {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 0.75rem;
    }
    .hero p {
        font-size: 1.1rem;
        color: var(--text-secondary);
        max-width: 600px;
        margin: 0 auto 2rem auto;
        line-height: 1.6;
    }
    .hero .cta {
        display: inline-block;
        padding: 0.7rem 2rem;
        background: var(--accent-blue);
        color: #fff;
        border-radius: 8px;
        font-weight: 600;
        text-decoration: none;
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="hero">
        <h1>{APP_TITLE}</h1>
        <p>Compare two variants. Measure lift. Make a confident decision.</p>
        <a href="/A%2BAnalysis" class="cta">Open A/B Analysis →</a>
    </div>
    """,
    unsafe_allow_html=True,
)

__all__ = [
    "APP_TITLE",
    "_lift_class",
    "_pval_badge",
    "_rel_lift_display",
]
