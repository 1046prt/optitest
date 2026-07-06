"""Export and report download component."""

from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from dashboard.config import REPORTS_DIR
from dashboard.utils.helpers import _generate_report
from ab_testing_framework.report_generator import save_report


def _result_to_json_str(result: object) -> str:
    """Serialise AbTestResult to a formatted JSON string for download."""
    srm = result.srm
    cs  = result.chi_square
    pa  = result.power_analysis
    m   = result.metrics
    ci  = result.confidence_interval
    es  = result.effect_size

    data = {
        "summary": result.summary,
        "decision": result.decision,
        "recommendation": result.recommendation,
        "experiment": result.experiment.to_dict(),
        "metrics": {
            "conversion_rate_a": m.conversion_rate_a,
            "conversion_rate_b": m.conversion_rate_b,
            "absolute_difference": m.absolute_difference,
            "relative_improvement": m.relative_improvement,
        },
        "z_test": {
            "z_score": result.z_test.z_score,
            "p_value": result.z_test.p_value,
            "pooled_rate": result.z_test.pooled_rate,
            "alternative": result.z_test.alternative,
        },
        "chi_square": {
            "chi2_stat": cs.chi2_stat,
            "p_value": cs.p_value,
            "cramers_v": cs.cramers_v,
            "yates_correction": cs.yates_correction,
        },
        "srm": {
            "srm_detected": srm.srm_detected,
            "severity": srm.severity,
            "p_value": srm.p_value,
            "observed_a": srm.observed_a,
            "observed_b": srm.observed_b,
        },
        "confidence_interval": {
            "lower_bound": ci.lower_bound,
            "upper_bound": ci.upper_bound,
            "margin_of_error": ci.margin_of_error,
            "confidence_level": ci.confidence_level,
        },
        "effect_size": {
            "absolute_difference": es.absolute_difference,
            "relative_improvement": es.relative_improvement,
            "cohens_h": es.cohens_h,
        },
        "power_analysis": {
            "power": pa.power,
            "required_sample_size_per_group": pa.required_sample_size_per_group,
            "alpha": pa.alpha,
            "target_power": pa.target_power,
        },
    }
    return json.dumps(data, indent=2, sort_keys=True)


def render_export(result: object, visitors_a: int, visitors_b: int) -> None:
    report_stem     = f"ab_test_report_{datetime.now():%Y%m%d_%H%M%S}"
    report_markdown = _generate_report(result)
    report_json     = _result_to_json_str(result)

    with st.expander("Download report"):
        col_md, col_json, col_save, _ = st.columns([1, 1, 1, 3])

        with col_md:
            st.download_button(
                label="⬇ Markdown",
                data=report_markdown,
                file_name=f"{report_stem}.md",
                mime="text/markdown",
                help="Download the full report as a Markdown file.",
            )

        with col_json:
            st.download_button(
                label="⬇ JSON",
                data=report_json,
                file_name=f"{report_stem}.json",
                mime="application/json",
                help="Download all results as a structured JSON file.",
            )

        with col_save:
            if st.button("💾 Save to reports/", help="Save both .md and .json to the local reports/ folder."):
                saved = save_report(
                    result,
                    output_dir=REPORTS_DIR,
                    stem=report_stem,
                )
                st.success(f"Saved: {saved['markdown'].name}  ·  {saved['json'].name}")

        st.code(report_markdown, language="markdown")

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
