"""Streamlit dashboard for the Split Testing Suite."""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR   = PROJECT_ROOT / "dashboard" / "assets"
FAVICON_PATH = ASSETS_DIR / "favicon.svg"
SRC_PATH     = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ab_testing_framework.analysis import run_ab_test          # noqa: E402
from ab_testing_framework.data_loader import load_data         # noqa: E402
from ab_testing_framework.report_generator import (            # noqa: E402
    generate_markdown_report, save_report,
)
from ab_testing_framework.visualization import (               # noqa: E402
    bar_chart, confidence_plot, distribution_plot,
    histogram, z_score_plot,
)

APP_TITLE = "Split Testing Suite"

# ── page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=str(FAVICON_PATH),
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --bg:          #0d0f14;
    --bg-panel:    #13151c;
    --bg-hover:    #1a1d27;
    --border:      #232635;
    --border-soft: #1c1f2e;

    --text-primary:   #e8eaf0;
    --text-secondary: #8b90a7;
    --text-muted:     #555a72;

    --accent-blue:   #4f8ef7;
    --accent-green:  #34d399;
    --accent-red:    #f87171;
    --accent-amber:  #fbbf24;

    --radius: 10px;
}

html, body, [class*="css"], .stApp {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif !important;
    font-size: 15px;
    color: var(--text-primary);
    background-color: var(--bg) !important;
}

/* keep sidebar toggle; hide only the noisy bits */
#MainMenu, footer, [data-testid="stStatusWidget"] { display: none !important; }

.stApp > header {
    background-color: var(--bg-panel) !important;
    border-bottom: 1px solid var(--border) !important;
}
.stApp > header button { color: var(--text-secondary) !important; }
.stApp > header button:hover {
    color: var(--text-primary) !important;
    background: var(--bg-hover) !important;
    border-radius: 5px !important;
}
[data-testid="collapsedControl"] button { color: var(--text-secondary) !important; }
[data-testid="collapsedControl"] button:hover {
    color: var(--text-primary) !important;
    background: var(--bg-hover) !important;
}

.block-container {
    max-width: 1200px;
    padding: 1.5rem 2rem 3rem 2rem;
    background-color: var(--bg);
}

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--bg-panel) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
[data-testid="stSidebar"] .stMarkdown h3,
[data-testid="stSidebar"] .stMarkdown h4 {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
    margin-top: 1.25rem !important;
    margin-bottom: 0.3rem !important;
}
[data-testid="stSidebar"] input[type="number"] {
    background-color: var(--bg-hover) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] hr { border-color: var(--border) !important; }

/* ── page header ── */
.page-header { margin-bottom: 1.5rem; }
.page-header h2 {
    margin: 0 0 0.2rem 0;
    font-size: 1.45rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.02em;
}
.page-header p {
    margin: 0;
    font-size: 0.87rem;
    color: var(--text-secondary);
}

/* ── section labels ── */
.section-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 1.75rem 0 0.7rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid var(--border);
}

/* ── metric cards ── */
div[data-testid="metric-container"] {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.76rem;
    font-weight: 500;
    color: var(--text-secondary) !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary) !important;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    color: var(--accent-green) !important;
}

/* ── decision card ── */
.decision-card {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.1rem 1.25rem;
}
.decision-card.positive { border-left: 3px solid var(--accent-green); }
.decision-card.negative { border-left: 3px solid var(--accent-red);   }
.decision-card.neutral  { border-left: 3px solid var(--accent-amber);  }
.decision-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.decision-card.positive .decision-label { color: var(--accent-green); }
.decision-card.negative .decision-label { color: var(--accent-red);   }
.decision-card.neutral  .decision-label { color: var(--accent-amber);  }
.decision-text { font-size: 0.93rem; color: var(--text-secondary); line-height: 1.6; margin: 0; }

/* ── p-value badge ── */
.pval-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    margin-left: 0.5rem;
    vertical-align: middle;
}
.pval-badge.strong  { background: rgba(52,211,153,0.15); color: var(--accent-green); }
.pval-badge.moderate{ background: rgba(251,191,36,0.15);  color: var(--accent-amber); }
.pval-badge.weak    { background: rgba(248,113,113,0.15); color: var(--accent-red);  }

/* ── underpowered warning ── */
.warn-block {
    background: rgba(251,191,36,0.08);
    border: 1px solid rgba(251,191,36,0.3);
    border-left: 3px solid var(--accent-amber);
    border-radius: var(--radius);
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    color: var(--accent-amber);
    margin-top: 0.5rem;
}
.warn-block strong { color: var(--accent-amber); }

/* ── stat tables ── */
.stat-block {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    height: 100%;
}
.stat-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.stat-table td {
    padding: 0.58rem 0.85rem;
    border-bottom: 1px solid var(--border-soft);
    vertical-align: middle;
    line-height: 1.4;
}
.stat-table tr:last-child td { border-bottom: none; }
.stat-table tr:hover td { background-color: var(--bg-hover); }
.stat-key { color: var(--text-secondary); font-weight: 400; width: 58%; }
.stat-val { color: var(--text-primary); font-weight: 600; font-variant-numeric: tabular-nums; text-align: right; }
.stat-val.positive { color: var(--accent-green); }
.stat-val.negative { color: var(--accent-red);   }

/* ── expanders ── */
div[data-testid="stExpander"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}
div[data-testid="stExpander"] summary {
    font-weight: 600; font-size: 0.88rem;
    color: var(--text-primary) !important;
    padding: 0.75rem 1rem;
}
div[data-testid="stExpander"] p,
div[data-testid="stExpander"] li { color: var(--text-secondary) !important; }
div[data-testid="stExpander"] pre,
div[data-testid="stExpander"] code {
    background: var(--bg) !important;
    color: #a8b3cf !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px;
}

/* ── buttons ── */
.stButton > button, .stDownloadButton > button {
    border-radius: 7px !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-hover) !important;
    color: var(--text-primary) !important;
    font-size: 0.84rem !important;
    font-weight: 600 !important;
    padding: 0.45rem 1rem !important;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}
.stButton > button:hover {
    background: var(--accent-blue) !important;
    border-color: var(--accent-blue) !important;
    color: #ffffff !important;
}
.stDownloadButton > button:hover {
    background: #1e2235 !important;
    border-color: var(--accent-blue) !important;
    color: var(--accent-blue) !important;
}
.stDownloadButton > button:hover span { color: var(--accent-blue) !important; }

/* ── charts ── */
[data-testid="stPlotlyChart"] {
    margin-top: 0 !important;
    border-radius: var(--radius);
    overflow: hidden;
    border: 1px solid var(--border);
}

/* ── alerts ── */
[data-testid="stAlert"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
    border-radius: var(--radius) !important;
}

.footnote {
    font-size: 0.76rem; color: var(--text-muted);
    margin-top: 2.5rem; padding-top: 0.75rem;
    border-top: 1px solid var(--border);
}
</style>
""", unsafe_allow_html=True)


# ── cached analysis ────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _run(va: int, ca: int, vb: int, cb: int, alpha: float, alternative: str):
    return run_ab_test(va, ca, vb, cb, alpha=alpha, alternative=alternative)


# ── helpers ────────────────────────────────────────────────────────────────────
def _pval_badge(p: float) -> str:
    if p < 0.001:
        return '<span class="pval-badge strong">p &lt; 0.001 ✦✦✦</span>'
    if p < 0.01:
        return '<span class="pval-badge strong">p &lt; 0.01 ✦✦</span>'
    if p < 0.05:
        return '<span class="pval-badge moderate">p &lt; 0.05 ✦</span>'
    return '<span class="pval-badge weak">not significant</span>'


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


if __name__ == "__main__":
    # ── sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Split Testing Suite")
        st.markdown("---")

        st.markdown("#### Data source")
        uploaded_file = st.file_uploader(
            "Upload CSV", type=["csv"], label_visibility="collapsed",
        )

        if uploaded_file is None:
            st.markdown("#### Control (A)")
            visitors_a    = st.number_input("Visitors",    min_value=1, value=10_000, step=100, key="va")
            conversions_a = st.number_input("Conversions", min_value=0, value=450,    step=1,   key="ca")

            st.markdown("#### Treatment (B)")
            visitors_b    = st.number_input("Visitors",    min_value=1, value=10_000, step=100, key="vb")
            conversions_b = st.number_input("Conversions", min_value=0, value=520,    step=1,   key="cb")

        st.markdown("#### Test settings")
        alpha = st.slider(
            "Significance level (α)",
            min_value=0.01, max_value=0.20, value=0.05, step=0.01,
            help="Threshold for rejecting H₀. Common values: 0.05 (standard) · 0.01 (strict) · 0.10 (exploratory).",
        )
        alternative = st.selectbox(
            "Hypothesis",
            options=["two-sided", "larger", "smaller"],
            index=0,
            help=(
                "two-sided: test whether B ≠ A (most common).\n"
                "larger: test whether B > A (directional, more power).\n"
                "smaller: test whether B < A."
            ),
        )

        st.markdown("---")
        st.markdown("#### Sample CSV format")
        _sample_csv = (
            "visitors_a,conversions_a,visitors_b,conversions_b\n"
            "10000,450,10000,520\n"
        )
        st.download_button(
            label="Download template",
            data=_sample_csv,
            file_name="ab_test_template.csv",
            mime="text/csv",
            help="Use this as a starting point for your own experiment data.",
        )

        st.markdown("---")
        st.markdown(
            "<p style='font-size:0.75rem;color:#555a72;line-height:1.5;'>"
            "Two-proportion z-test · 95% CI<br>"
            "Power via statsmodels NormalIndPower."
            "</p>",
            unsafe_allow_html=True,
        )

    # ── load CSV if uploaded ───────────────────────────────────────────────────
    if uploaded_file is not None:
        try:
            experiment_data = load_data(uploaded_file)
            visitors_a    = experiment_data.visitors_a
            conversions_a = experiment_data.conversions_a
            visitors_b    = experiment_data.visitors_b
            conversions_b = experiment_data.conversions_b
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")
            st.stop()

    # ── input validation ───────────────────────────────────────────────────────
    input_errors: list[str] = []
    if conversions_a > visitors_a:
        input_errors.append(f"Control: conversions ({conversions_a:,}) exceed visitors ({visitors_a:,}).")
    if conversions_b > visitors_b:
        input_errors.append(f"Treatment: conversions ({conversions_b:,}) exceed visitors ({visitors_b:,}).")

    if input_errors:
        st.markdown(
            """
            <div class="page-header">
                <h2>A/B Test Results</h2>
                <p>Two-proportion z-test &nbsp;·&nbsp; confidence intervals &nbsp;·&nbsp; power analysis</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for err in input_errors:
            st.error(f"⚠ {err}")
        st.stop()

    # ── run analysis (cached) ──────────────────────────────────────────────────
    try:
        result = _run(
            int(visitors_a), int(conversions_a),
            int(visitors_b), int(conversions_b),
            float(alpha),
            alternative,
        )
    except ValueError as exc:
        st.error(f"Validation error: {exc}")
        st.stop()
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")
        st.stop()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE CONTENT
    # ══════════════════════════════════════════════════════════════════════════

    st.markdown(
        """
        <div class="page-header">
            <h2>A/B Test Results</h2>
            <p>Two-proportion z-test &nbsp;·&nbsp; confidence intervals &nbsp;·&nbsp; power analysis</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── section: key metrics ───────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Key metrics</div>", unsafe_allow_html=True)

    m  = result.metrics
    pa = result.power_analysis
    ci = result.confidence_interval
    is_sig      = result.z_test.p_value < alpha
    is_positive = ci.lower_bound > 0

    rel_display = _rel_lift_display(m.relative_improvement)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Control rate",   f"{m.conversion_rate_a:.2%}")
    c2.metric("Treatment rate", f"{m.conversion_rate_b:.2%}")
    c3.metric(
        "Absolute lift",
        f"{m.absolute_difference:.2%}",
        delta=f"{rel_display} relative" if m.relative_improvement is not None else "N/A",
        delta_color="normal" if (m.relative_improvement or 0) >= 0 else "inverse",
    )
    c4.metric("P-value", f"{result.z_test.p_value:.4f}")

    # p-value badge row
    st.markdown(
        f"<div style='margin-top:0.4rem;margin-bottom:0.25rem;font-size:0.84rem;"
        f"color:var(--text-secondary);'>Significance: {_pval_badge(result.z_test.p_value)}</div>",
        unsafe_allow_html=True,
    )

    # underpowered warning
    if pa.power < 0.8:
        needed = pa.required_sample_size_per_group
        current = min(visitors_a, visitors_b)
        st.markdown(
            f"<div class='warn-block'>"
            f"<strong>⚠ Underpowered sample.</strong> Observed power is {pa.power:.1%} — "
            f"below the 80% threshold. You need ~<strong>{needed:,}</strong> visitors per group; "
            f"currently running {current:,}. Results may not be reliable."
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── section: decision ──────────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Decision</div>", unsafe_allow_html=True)

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

    # ── section: statistical detail ──────────────────────────────────────────────
    st.markdown("<div class='section-label'>Statistical detail</div>", unsafe_allow_html=True)

    lift_cls = _lift_class(m.absolute_difference)
    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown(
            f"""
            <div class="stat-block">
              <table class="stat-table">
                <tr><td class="stat-key">Z-score</td>
                    <td class="stat-val">{result.z_test.z_score:.4f}</td></tr>
                <tr><td class="stat-key">P-value (z-test)</td>
                    <td class="stat-val">{result.z_test.p_value:.4f}</td></tr>
                <tr><td class="stat-key">Chi-square (χ²)</td>
                    <td class="stat-val">{result.chi_square.chi2_stat:.4f}</td></tr>
                <tr><td class="stat-key">P-value (chi-square)</td>
                    <td class="stat-val">{result.chi_square.p_value:.4f}</td></tr>
                <tr><td class="stat-key">Significance level (α)</td>
                    <td class="stat-val">{alpha:.2f}</td></tr>
                <tr><td class="stat-key">95% CI — lower</td>
                    <td class="stat-val {_lift_class(ci.lower_bound)}">{ci.lower_bound:.4%}</td></tr>
                <tr><td class="stat-key">95% CI — upper</td>
                    <td class="stat-val {_lift_class(ci.upper_bound)}">{ci.upper_bound:.4%}</td></tr>
                <tr><td class="stat-key">Decision</td>
                    <td class="stat-val">{result.decision}</td></tr>
              </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown(
            f"""
            <div class="stat-block">
              <table class="stat-table">
                <tr><td class="stat-key">Absolute lift</td>
                    <td class="stat-val {lift_cls}">{m.absolute_difference:.4%}</td></tr>
                <tr><td class="stat-key">Relative lift</td>
                    <td class="stat-val {lift_cls}">{rel_display}</td></tr>
                <tr><td class="stat-key">Cohen's h</td>
                    <td class="stat-val">{result.effect_size.cohens_h:.4f}</td></tr>
                <tr><td class="stat-key">Cramér's V</td>
                    <td class="stat-val">{result.chi_square.cramers_v:.4f}</td></tr>
                <tr><td class="stat-key">Yates correction</td>
                    <td class="stat-val">{'yes' if result.chi_square.yates_correction else 'no'}</td></tr>
                <tr><td class="stat-key">Observed power</td>
                    <td class="stat-val {'positive' if pa.power >= 0.8 else 'negative'}">{pa.power:.1%}</td></tr>
                <tr><td class="stat-key">Required n / group</td>
                    <td class="stat-val">{pa.required_sample_size_per_group:,}</td></tr>
                <tr><td class="stat-key">Target power</td>
                    <td class="stat-val">{pa.target_power:.0%}</td></tr>
              </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── section: visual analysis ────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Visual analysis</div>", unsafe_allow_html=True)

    # Row 1: conversion bars + CI plot
    r1l, r1r = st.columns(2)
    with r1l:
        st.plotly_chart(bar_chart(result), use_container_width=True)
    with r1r:
        st.plotly_chart(confidence_plot(result), use_container_width=True)

    # Row 2: z-score distribution + sampling distributions
    r2l, r2r = st.columns(2)
    with r2l:
        st.plotly_chart(z_score_plot(result), use_container_width=True)
    with r2r:
        st.plotly_chart(distribution_plot(result), use_container_width=True)

    # Row 3: bootstrap histogram (full width)
    st.plotly_chart(histogram(result), use_container_width=True)

    # ── section: export ──────────────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Export</div>", unsafe_allow_html=True)

    report_stem    = f"ab_test_report_{datetime.now():%Y%m%d_%H%M%S}"
    report_markdown = generate_markdown_report(result)

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
                    output_dir=PROJECT_ROOT / "reports",
                    stem=report_stem,
                )
                st.success(f"Saved: {saved['markdown'].name}  ·  {saved['json'].name}")

    with st.expander("Power analysis detail"):
        st.markdown(
            f"""
            **Observed power:** {pa.power:.1%} at α = {pa.alpha:.2f}

            To reach **{pa.target_power:.0%} power**, you need approximately
            **{pa.required_sample_size_per_group:,} visitors per group**.
            Currently running **{int(visitors_a):,}** (control) and
            **{int(visitors_b):,}** (treatment).

            {'⚠ Current sample is below the required size — interpret results with caution.' if min(visitors_a, visitors_b) < pa.required_sample_size_per_group else '✓ Sample size meets the power requirement.'}
            """
        )

    # ── footnote ────────────────────────────────────────────────────────────────
    st.markdown(
        f"<p class='footnote'>"
        f"Decision rule: reject H₀ when p-value &lt; α and the lift confidence interval "
        f"excludes zero. Test is <strong>{result.z_test.alternative}</strong>. "
        f"Power calculated via statsmodels NormalIndPower."
        f"</p>",
        unsafe_allow_html=True,
    )
