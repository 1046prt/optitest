"""Theme definitions and CSS injection for the Split Testing Suite dashboard.

Two themes are supported: dark (default) and light.
The active theme is stored in ``st.session_state["theme"]``.
"""

from __future__ import annotations

import streamlit as st

# ── token maps ─────────────────────────────────────────────────────────────────
_DARK = {
    "bg":              "#0d0f14",
    "bg_panel":        "#13151c",
    "bg_hover":        "#1a1d27",
    "border":          "#232635",
    "border_soft":     "#1c1f2e",
    "text_primary":    "#e8eaf0",
    "text_secondary":  "#8b90a7",
    "text_muted":      "#555a72",
    "accent_blue":     "#4f8ef7",
    "accent_green":    "#34d399",
    "accent_red":      "#f87171",
    "accent_amber":    "#fbbf24",
}

_LIGHT = {
    "bg":              "#f5f6fa",
    "bg_panel":        "#ffffff",
    "bg_hover":        "#eef0f7",
    "border":          "#d6d9e8",
    "border_soft":     "#e2e5f0",
    "text_primary":    "#1a1d27",
    "text_secondary":  "#4a4f6a",
    "text_muted":      "#9399b5",
    "accent_blue":     "#2563eb",
    "accent_green":    "#059669",
    "accent_red":      "#dc2626",
    "accent_amber":    "#d97706",
}

_PLOTLY_DARK  = {"bg": "#13151c", "bg_inner": "#0d0f14", "grid": "#232635", "text": "#8b90a7", "title": "#e8eaf0"}
_PLOTLY_LIGHT = {"bg": "#ffffff", "bg_inner": "#f5f6fa", "grid": "#d6d9e8", "text": "#4a4f6a", "title": "#1a1d27"}


def get_tokens() -> dict[str, str]:
    """Return the CSS token map for the current theme."""
    return _DARK if st.session_state.get("theme", "dark") == "dark" else _LIGHT


def get_plotly_tokens() -> dict[str, str]:
    return _PLOTLY_DARK if st.session_state.get("theme", "dark") == "dark" else _PLOTLY_LIGHT


def init_theme() -> None:
    """Set default theme in session state if not already set."""
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"


def toggle_theme() -> None:
    """Flip between dark and light."""
    st.session_state["theme"] = (
        "light" if st.session_state.get("theme", "dark") == "dark" else "dark"
    )


def inject_css() -> None:
    """Inject theme-aware CSS variables and component styles."""
    t = get_tokens()
    st.markdown(
        f"""
<style>
:root {{
    --bg:              {t['bg']};
    --bg-panel:        {t['bg_panel']};
    --bg-hover:        {t['bg_hover']};
    --border:          {t['border']};
    --border-soft:     {t['border_soft']};
    --text-primary:    {t['text_primary']};
    --text-secondary:  {t['text_secondary']};
    --text-muted:      {t['text_muted']};
    --accent-blue:     {t['accent_blue']};
    --accent-green:    {t['accent_green']};
    --accent-red:      {t['accent_red']};
    --accent-amber:    {t['accent_amber']};
    --radius: 10px;
}}

html, body, [class*="css"], .stApp {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif !important;
    font-size: 15px;
    color: var(--text-primary);
    background-color: var(--bg) !important;
}}

#MainMenu, footer, [data-testid="stStatusWidget"] {{ display: none !important; }}

.stApp > header {{
    background-color: var(--bg-panel) !important;
    border-bottom: 1px solid var(--border) !important;
}}
.stApp > header button {{ color: var(--text-secondary) !important; }}
.stApp > header button:hover {{
    color: var(--text-primary) !important;
    background: var(--bg-hover) !important;
    border-radius: 5px !important;
}}
[data-testid="collapsedControl"] button {{ color: var(--text-secondary) !important; }}
[data-testid="collapsedControl"] button:hover {{
    color: var(--text-primary) !important;
    background: var(--bg-hover) !important;
}}

.block-container {{
    max-width: 1200px;
    padding: 1.5rem 2rem 3rem 2rem;
    background-color: var(--bg);
}}

[data-testid="stSidebar"] {{
    background-color: var(--bg-panel) !important;
    border-right: 1px solid var(--border);
}}
[data-testid="stSidebar"] * {{ color: var(--text-primary) !important; }}
[data-testid="stSidebar"] .stMarkdown h3,
[data-testid="stSidebar"] .stMarkdown h4 {{
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
    margin-top: 1.25rem !important;
    margin-bottom: 0.3rem !important;
}}
[data-testid="stSidebar"] input[type="number"] {{
    background-color: var(--bg-hover) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 6px !important;
}}
[data-testid="stSidebar"] hr {{ border-color: var(--border) !important; }}

.page-header {{ margin-bottom: 1.5rem; }}
.page-header h2 {{
    margin: 0 0 0.2rem 0;
    font-size: 1.45rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.02em;
}}
.page-header p {{
    margin: 0;
    font-size: 0.87rem;
    color: var(--text-secondary);
}}

.section-label {{
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 1.75rem 0 0.7rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid var(--border);
}}

div[data-testid="metric-container"] {{
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
}}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
    font-size: 0.76rem; font-weight: 500; color: var(--text-secondary) !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 1.5rem; font-weight: 700;
    color: var(--text-primary) !important;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
}}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {{
    color: var(--accent-green) !important;
}}

.decision-card {{
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.1rem 1.25rem;
}}
.decision-card.positive {{ border-left: 3px solid var(--accent-green); }}
.decision-card.negative {{ border-left: 3px solid var(--accent-red);   }}
.decision-card.neutral  {{ border-left: 3px solid var(--accent-amber);  }}
.decision-label {{
    font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.4rem;
}}
.decision-card.positive .decision-label {{ color: var(--accent-green); }}
.decision-card.negative .decision-label {{ color: var(--accent-red);   }}
.decision-card.neutral  .decision-label {{ color: var(--accent-amber);  }}
.decision-text {{ font-size: 0.93rem; color: var(--text-secondary); line-height: 1.6; margin: 0; }}

.pval-badge {{
    display: inline-block; font-size: 0.72rem; font-weight: 700;
    letter-spacing: 0.05em; padding: 0.15rem 0.5rem;
    border-radius: 999px; margin-left: 0.5rem; vertical-align: middle;
}}
.pval-badge.strong   {{ background: rgba(52,211,153,0.15);  color: var(--accent-green); }}
.pval-badge.moderate {{ background: rgba(251,191,36,0.15);  color: var(--accent-amber); }}
.pval-badge.weak     {{ background: rgba(248,113,113,0.15); color: var(--accent-red);   }}

.warn-block {{
    background: rgba(251,191,36,0.08);
    border: 1px solid rgba(251,191,36,0.3);
    border-left: 3px solid var(--accent-amber);
    border-radius: var(--radius);
    padding: 0.75rem 1rem;
    font-size: 0.875rem; color: var(--accent-amber); margin-top: 0.5rem;
}}
.warn-block strong {{ color: var(--accent-amber); }}

.srm-critical {{
    background: rgba(248,113,113,0.08);
    border: 1px solid rgba(248,113,113,0.3);
    border-left: 3px solid var(--accent-red);
    border-radius: var(--radius);
    padding: 0.75rem 1rem;
    font-size: 0.875rem; color: var(--accent-red); margin-top: 0.5rem;
}}
.srm-critical strong {{ color: var(--accent-red); }}

.stat-block {{
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden; height: 100%;
}}
.stat-table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
.stat-table td {{
    padding: 0.58rem 0.85rem;
    border-bottom: 1px solid var(--border-soft);
    vertical-align: middle; line-height: 1.4;
}}
.stat-table tr:last-child td {{ border-bottom: none; }}
.stat-table tr:hover td {{ background-color: var(--bg-hover); }}
.stat-key {{ color: var(--text-secondary); font-weight: 400; width: 58%; }}
.stat-val {{ color: var(--text-primary); font-weight: 600; font-variant-numeric: tabular-nums; text-align: right; }}
.stat-val.positive {{ color: var(--accent-green); }}
.stat-val.negative {{ color: var(--accent-red);   }}

div[data-testid="stExpander"] {{
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}}
div[data-testid="stExpander"] summary {{
    font-weight: 600; font-size: 0.88rem;
    color: var(--text-primary) !important; padding: 0.75rem 1rem;
}}
div[data-testid="stExpander"] p,
div[data-testid="stExpander"] li {{ color: var(--text-secondary) !important; }}
div[data-testid="stExpander"] pre,
div[data-testid="stExpander"] code {{
    background: var(--bg) !important; color: #a8b3cf !important;
    border: 1px solid var(--border) !important; border-radius: 6px;
}}

.stButton > button, .stDownloadButton > button {{
    border-radius: 7px !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-hover) !important;
    color: var(--text-primary) !important;
    font-size: 0.84rem !important; font-weight: 600 !important;
    padding: 0.45rem 1rem !important;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}}
.stButton > button:hover {{
    background: var(--accent-blue) !important;
    border-color: var(--accent-blue) !important;
    color: #ffffff !important;
}}
.stDownloadButton > button:hover {{
    background: var(--bg-hover) !important;
    border-color: var(--accent-blue) !important;
    color: var(--accent-blue) !important;
}}

[data-testid="stPlotlyChart"] {{
    margin-top: 0 !important;
    border-radius: var(--radius); overflow: hidden;
    border: 1px solid var(--border);
}}

[data-testid="stAlert"] {{
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
    border-radius: var(--radius) !important;
}}

.footnote {{
    font-size: 0.76rem; color: var(--text-muted);
    margin-top: 2.5rem; padding-top: 0.75rem;
    border-top: 1px solid var(--border);
}}

/* history table */
.history-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
.history-table th {{
    padding: 0.5rem 0.85rem;
    background: var(--bg-hover);
    border-bottom: 2px solid var(--border);
    color: var(--text-muted);
    font-size: 0.7rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.07em;
    text-align: left;
}}
.history-table td {{
    padding: 0.55rem 0.85rem;
    border-bottom: 1px solid var(--border-soft);
    color: var(--text-secondary);
}}
.history-table tr:hover td {{ background: var(--bg-hover); }}
.history-table .positive {{ color: var(--accent-green); font-weight: 600; }}
.history-table .negative {{ color: var(--accent-red);   font-weight: 600; }}
.history-table .neutral  {{ color: var(--accent-amber); font-weight: 600; }}
</style>
""",
        unsafe_allow_html=True,
    )
