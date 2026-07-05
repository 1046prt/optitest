"""Export and report download component."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from dashboard.config import REPORTS_DIR
from dashboard.utils.helpers import _generate_report
from ab_testing_framework.report_generator import save_report


def render_export(result: object, visitors_a: int, visitors_b: int) -> None:
    report_stem = f"ab_test_report_{datetime.now():%Y%m%d_%H%M%S}"
    report_markdown = _generate_report(result)

    with st.expander("Markdown report"):
        st.code(report_markdown, language="markdown")
        col_dl, col_save, _ = st.columns([1, 1, 4])
        with col_dl:
            st.download_button(
                label="Download .md",
                data=report_markdown,
                file_name=f"{report_stem}.md",
                mime="text/markdown",
            )
        with col_save:
            if st.button("Save to reports/"):
                saved = save_report(
                    result,
                    output_dir=REPORTS_DIR,
                    stem=report_stem,
                )
                st.success(f"Saved: {saved['markdown'].name}  ·  {saved['json'].name}")

    with st.expander("Power analysis detail"):
        pa = result.power_analysis
        st.markdown(
            f"""
            **Observed power:** {pa.power:.1%} at α = {pa.alpha:.2f}

            To reach **{pa.target_power:.0%} power**, you need approximately
            **{pa.required_sample_size_per_group:,} visitors per group**.
            Currently running **{int(visitors_a):,}** (control) and
            **{int(visitors_b):,}** (treatment).

            {'⚠ Current sample is below the required size — interpret results with caution.' if min(int(visitors_a), int(visitors_b)) < pa.required_sample_size_per_group else '✓ Sample size meets the power requirement.'}
            """
        )
