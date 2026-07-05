"""Analysis page for the Split Testing Suite dashboard."""

from __future__ import annotations

import sys

import streamlit as st

from dashboard.config import (
    ALPHA_MAX,
    ALPHA_MIN,
    ALPHA_STEP,
    ALTERNATIVE_OPTIONS,
    APP_TITLE,
    DEFAULTS,
    FAVICON_PATH,
    INPUT_HELP,
    SAMPLE_CSV,
    SIDEBAR_LABELS,
    SRC_PATH,
)
from dashboard.components.charts import render_charts
from dashboard.components.decision import render_decision_card
from dashboard.components.export import render_export
from dashboard.components.layout import render_footnote, render_page_header
from dashboard.components.metrics import render_key_metrics, render_underpowered_warning
from dashboard.components.stat_tables import render_stat_tables
from dashboard.utils.helpers import _load_uploaded_experiment, _run

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


def run_analysis() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=str(FAVICON_PATH),
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.sidebar:
        st.markdown(f"### {SIDEBAR_LABELS['title']}")
        st.markdown("---")

        st.markdown(f"#### {SIDEBAR_LABELS['data_source']}")
        uploaded_file = st.file_uploader(
            "Upload CSV",
            type=["csv"],
            label_visibility="collapsed",
            help=_load_uploaded_experiment.__doc__ or "",
        )
        st.caption(SIDEBAR_LABELS["upload_caption"])

        st.markdown(f"#### {SIDEBAR_LABELS['control']}")
        visitors_a = st.number_input(
            "Visitors",
            min_value=1,
            value=DEFAULTS["visitors_a"],
            step=100,
            key="va",
            help=INPUT_HELP["visitors_a"],
        )
        conversions_a = st.number_input(
            "Conversions",
            min_value=0,
            value=DEFAULTS["conversions_a"],
            step=1,
            key="ca",
            help=INPUT_HELP["conversions_a"],
        )

        st.markdown(f"#### {SIDEBAR_LABELS['treatment']}")
        visitors_b = st.number_input(
            "Visitors",
            min_value=1,
            value=DEFAULTS["visitors_b"],
            step=100,
            key="vb",
            help=INPUT_HELP["visitors_b"],
        )
        conversions_b = st.number_input(
            "Conversions",
            min_value=0,
            value=DEFAULTS["conversions_b"],
            step=1,
            key="cb",
            help=INPUT_HELP["conversions_b"],
        )

        st.markdown(f"#### {SIDEBAR_LABELS['csv_preview']}")
        st.caption(SIDEBAR_LABELS["csv_preview_caption"])

        st.markdown(f"#### {SIDEBAR_LABELS['test_settings']}")
        alpha = st.slider(
            "Significance level (α)",
            min_value=ALPHA_MIN,
            max_value=ALPHA_MAX,
            value=0.05,
            step=ALPHA_STEP,
            help=INPUT_HELP["alpha"],
        )
        alternative = st.selectbox(
            "Hypothesis",
            options=ALTERNATIVE_OPTIONS,
            index=0,
            help=INPUT_HELP["alternative"],
        )

        st.markdown("---")
        st.markdown(f"#### {SIDEBAR_LABELS['sample_csv']}")
        st.download_button(
            label="Download template",
            data=SAMPLE_CSV,
            file_name="ab_test_template.csv",
            mime="text/csv",
            help="Use this as a starting point for your own experiment data.",
        )

        st.markdown("---")
        st.markdown(SIDEBAR_LABELS["footer"], unsafe_allow_html=True)

    uploaded_error = None
    if uploaded_file is not None:
        raw_content = uploaded_file.read()
        if isinstance(raw_content, str):
            file_bytes = raw_content.encode("utf-8")
        else:
            file_bytes = raw_content
        file_name = getattr(uploaded_file, "name", "uploaded.csv")
        experiment_data, uploaded_error = _load_uploaded_experiment(file_bytes, file_name)
        if experiment_data is not None:
            visitors_a = experiment_data.visitors_a
            conversions_a = experiment_data.conversions_a
            visitors_b = experiment_data.visitors_b
            conversions_b = experiment_data.conversions_b
            st.info("Loaded values from the uploaded CSV.")
        else:
            st.warning(uploaded_error)
            st.info(
                "Fix the CSV and upload again, or edit the manual inputs to continue with the dashboard."
            )

    input_errors: list[str] = []
    if conversions_a > visitors_a:
        input_errors.append(
            f"Control: conversions ({conversions_a:,}) exceed visitors ({visitors_a:,})."
        )
    if conversions_b > visitors_b:
        input_errors.append(
            f"Treatment: conversions ({conversions_b:,}) exceed visitors ({visitors_b:,})."
        )

    if input_errors:
        render_page_header("A/B Test Results", "Two-proportion z-test  ·  confidence intervals  ·  power analysis")
        for err in input_errors:
            st.error(
                f"⚠ {err} Adjust the counts so conversions stay between 0 and visitors, then rerun the analysis."
            )
        st.stop()

    try:
        result = _run(
            int(visitors_a),
            int(conversions_a),
            int(visitors_b),
            int(conversions_b),
            float(alpha),
            alternative,
        )
    except ValueError as exc:
        st.error(f"Validation error: {exc}")
        st.stop()
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")
        st.stop()

    render_page_header("A/B Test Results", "Two-proportion z-test  ·  confidence intervals  ·  power analysis")

    st.markdown("<div class='section-label'>Key metrics</div>", unsafe_allow_html=True)
    render_key_metrics(result, alpha)
    render_underpowered_warning(result.power_analysis, visitors_a, visitors_b)

    st.markdown("<div class='section-label'>Decision</div>", unsafe_allow_html=True)
    render_decision_card(result, alpha)

    st.markdown("<div class='section-label'>Statistical detail</div>", unsafe_allow_html=True)
    render_stat_tables(result, alpha, visitors_a, visitors_b)

    st.markdown("<div class='section-label'>Visual analysis</div>", unsafe_allow_html=True)
    render_charts(result)

    st.markdown("<div class='section-label'>Export</div>", unsafe_allow_html=True)
    render_export(result, visitors_a, visitors_b)

    render_footnote(result)


if __name__ == "__main__":
    run_analysis()
