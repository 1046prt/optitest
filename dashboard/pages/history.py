"""Experiment history page — compare all runs side by side."""

from __future__ import annotations

import sys

import streamlit as st

from dashboard.config import APP_TITLE, FAVICON_PATH, SRC_PATH
from dashboard.components.layout import render_theme_toggle, render_page_header
from dashboard.utils.state import clear_history, get_history, init_state, undo_last

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


def _decision_class(decision: str) -> str:
    if "Reject" in decision:
        return "positive"
    return "neutral"


def _lift_class(val: float) -> str:
    if val > 0:
        return "positive"
    if val < 0:
        return "negative"
    return ""


def run_history() -> None:
    st.set_page_config(
        page_title=f"History — {APP_TITLE}",
        page_icon=str(FAVICON_PATH),
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    init_state()
    render_page_header("Experiment History", "All runs from this session, newest last")
    render_theme_toggle()

    history = get_history()

    if not history:
        st.info("No experiments run yet. Go to the Analysis page and run a test — results will appear here.")
        return

    # ── action buttons ─────────────────────────────────────────────────────────
    col_undo, col_clear, _ = st.columns([1, 1, 8])
    with col_undo:
        if st.button("↩ Undo last", disabled=len(history) == 0):
            undo_last()
            st.rerun()
    with col_clear:
        if st.button("🗑 Clear all", disabled=len(history) == 0):
            clear_history()
            st.rerun()

    st.markdown("<div class='section-label'>Comparison table</div>", unsafe_allow_html=True)

    # ── build HTML table ───────────────────────────────────────────────────────
    headers = [
        "#", "Time / label",
        "Control n", "Control conv.", "Control rate",
        "Treatment n", "Treatment conv.", "Treatment rate",
        "Abs. lift", "Rel. lift", "P-value", "Decision",
        "SRM", "Power",
    ]
    header_html = "".join(f"<th>{h}</th>" for h in headers)

    rows_html = ""
    for i, entry in enumerate(reversed(history), start=1):
        r  = entry["result"]
        m  = r.metrics
        pa = r.power_analysis
        srm = r.srm

        abs_lift = m.absolute_difference
        rel_lift = m.relative_improvement
        rel_str  = f"{rel_lift:.2%}" if rel_lift is not None else "N/A"
        lift_cls = _lift_class(abs_lift)
        dec_cls  = _decision_class(r.decision)
        srm_str  = f"⚠ {srm.severity}" if srm.srm_detected else "✓ ok"
        srm_cls  = "negative" if srm.srm_detected else ""

        rows_html += f"""
        <tr>
            <td>{i}</td>
            <td style="white-space:nowrap;font-size:0.8rem">{entry['label']}</td>
            <td>{entry['visitors_a']:,}</td>
            <td>{entry['conversions_a']:,}</td>
            <td>{m.conversion_rate_a:.2%}</td>
            <td>{entry['visitors_b']:,}</td>
            <td>{entry['conversions_b']:,}</td>
            <td>{m.conversion_rate_b:.2%}</td>
            <td class="{lift_cls}">{abs_lift:+.2%}</td>
            <td class="{lift_cls}">{rel_str}</td>
            <td>{r.z_test.p_value:.4f}</td>
            <td class="{dec_cls}">{r.decision}</td>
            <td class="{srm_cls}">{srm_str}</td>
            <td>{'✓' if pa.power >= 0.8 else '⚠'} {pa.power:.0%}</td>
        </tr>"""

    st.markdown(
        f"""
        <div style="overflow-x:auto;">
          <table class="history-table">
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── per-run detail expanders ───────────────────────────────────────────────
    st.markdown("<div class='section-label'>Run detail</div>", unsafe_allow_html=True)
    for i, entry in enumerate(reversed(history), start=1):
        r = entry["result"]
        with st.expander(f"Run {i}  —  {entry['label']}"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Control rate",   f"{r.metrics.conversion_rate_a:.2%}")
            c2.metric("Treatment rate", f"{r.metrics.conversion_rate_b:.2%}")
            c3.metric("P-value",        f"{r.z_test.p_value:.4f}")
            c4.metric("Power",          f"{r.power_analysis.power:.1%}")
            st.markdown(f"**Decision:** {r.decision}")
            st.markdown(f"**Recommendation:** {r.recommendation}")
            if r.srm.srm_detected:
                st.warning(
                    f"SRM {r.srm.severity.upper()}: observed {r.srm.observed_a:,} / {r.srm.observed_b:,}, "
                    f"expected {r.srm.expected_a:,.0f} / {r.srm.expected_b:,.0f} (p = {r.srm.p_value:.4f})"
                )


if __name__ == "__main__":
    run_history()
