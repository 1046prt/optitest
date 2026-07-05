"""Utility helpers for the Split Testing Suite dashboard."""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Callable

import streamlit as st

from dashboard.config import PROJECT_ROOT, REPORTS_DIR

logger = logging.getLogger(__name__)


def _pval_badge(p: float) -> str:
    if p < 0.001:
        return "<span class=\"pval-badge strong\">p &lt; 0.001 ✦✦✦</span>"
    if p < 0.01:
        return "<span class=\"pval-badge strong\">p &lt; 0.01 ✦✦</span>"
    if p < 0.05:
        return "<span class=\"pval-badge moderate\">p &lt; 0.05 ✦</span>"
    return "<span class=\"pval-badge weak\">not significant</span>"


def _rel_lift_display(rel: float | None) -> str:
    if rel is None:
        return "N/A (zero baseline)"
    return f"{rel:.2%}"


def _lift_class(val: float) -> str:
    if val > 0:
        return "positive"
    if val < 0:
        return "negative"
    return ""


def _uploaded_csv_help() -> str:
    return (
        "Upload an aggregated CSV with visitors_a/conversions_a/visitors_b/conversions_b, "
        "or a per-user CSV with variant and converted. Commas, semicolons, tabs, and UTF-8 BOMs are handled automatically."
    )


@st.cache_data(show_spinner=False)
def _run(
    va: int,
    ca: int,
    vb: int,
    cb: int,
    alpha: float,
    alternative: str,
) -> "AbTestResult":  # type: ignore[name-defined]
    from ab_testing_framework.analysis import run_ab_test

    return run_ab_test(va, ca, vb, cb, alpha=alpha, alternative=alternative)


@st.cache_data(show_spinner=False)
def _generate_report(result: "AbTestResult") -> str:  # type: ignore[name-defined]
    from ab_testing_framework.report_generator import generate_markdown_report

    return generate_markdown_report(result)


@st.cache_data(show_spinner=False)
def _load_uploaded_experiment(
    file_bytes: bytes,
    file_name: str,
) -> tuple[object | None, str | None]:
    """Load an experiment from uploaded CSV bytes."""
    try:
        from ab_testing_framework.data_loader import load_data

        return load_data(BytesIO(file_bytes)), None
    except Exception as exc:
        source_name = file_name
        logger.exception(
            "dashboard_csv_load_failed",
            extra={"source": source_name},
        )
        message = (
            f"Could not use {source_name}: {exc}. "
            "Check that the file uses one of the supported column layouts, has a consistent delimiter, "
            "and contains numeric visitor/conversion counts. The dashboard will keep the manual inputs so you can continue."
        )
        return None, message


def _get_report_paths(stem: str) -> dict[str, Path]:
    return {
        "markdown": REPORTS_DIR / f"{stem}.md",
        "json": REPORTS_DIR / f"{stem}.json",
    }
