"""Plotly visualizations for the A/B testing dashboard — dark theme."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots  # noqa: F401  (reserved for future multi-panel charts)
from scipy import stats

from .analysis import AbTestResult

# ── shared dark palette ────────────────────────────────────────────────────────
_BG        = "#13151c"   # panel / paper background
_BG_INNER  = "#0d0f14"   # inner plot area
_GRID      = "#232635"   # gridlines
_TEXT      = "#8b90a7"   # axis labels / secondary text
_TITLE     = "#e8eaf0"   # chart titles / primary text

_CONTROL   = "#4f8ef7"   # blue  — control group
_TREATMENT = "#34d399"   # green — treatment group
_LIFT_DOT  = "#fbbf24"   # amber — observed lift marker
_CI_LINE   = "#8b90a7"   # muted — CI span line
_CRITICAL  = "#f87171"   # red   — critical / rejection region


def _dark_layout(**overrides) -> dict:
    """Base dark layout dict; overrides are merged in."""
    base = dict(
        paper_bgcolor=_BG,
        plot_bgcolor=_BG_INNER,
        font=dict(
            family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            color=_TEXT,
            size=12,
        ),
        title_font=dict(
            color=_TITLE,
            size=13,
            family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        ),
        xaxis=dict(
            gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID,
            tickfont=dict(color=_TEXT), title_font=dict(color=_TEXT),
        ),
        yaxis=dict(
            gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID,
            tickfont=dict(color=_TEXT), title_font=dict(color=_TEXT),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=_TEXT),
            bordercolor=_GRID,
            borderwidth=1,
        ),
        margin=dict(l=52, r=24, t=52, b=44),
    )
    base.update(overrides)
    return base


# ── individual charts ─────────────────────────────────────────────────────────

def bar_chart(result: AbTestResult) -> go.Figure:
    """Side-by-side conversion rate bars with value labels."""
    m = result.metrics
    fig = go.Figure(
        go.Bar(
            x=["Control", "Treatment"],
            y=[m.conversion_rate_a, m.conversion_rate_b],
            marker_color=[_CONTROL, _TREATMENT],
            marker_line_color="rgba(0,0,0,0)",
            text=[f"{m.conversion_rate_a:.2%}", f"{m.conversion_rate_b:.2%}"],
            textposition="outside",
            textfont=dict(color=_TITLE, size=12),
        )
    )
    fig.update_layout(
        _dark_layout(
            title="Conversion Rate Comparison",
            yaxis=dict(
                title="Conversion rate",
                tickformat=".1%",
                gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID,
                tickfont=dict(color=_TEXT), title_font=dict(color=_TEXT),
            ),
            height=360,
            bargap=0.45,
        )
    )
    return fig


def confidence_plot(result: AbTestResult) -> go.Figure:
    """Horizontal CI bar with observed lift dot and zero reference."""
    ci = result.confidence_interval
    m  = result.metrics

    fig = go.Figure()
    fig.add_vline(x=0, line=dict(color=_GRID, width=1, dash="dot"))

    # CI span
    fig.add_trace(go.Scatter(
        x=[ci.lower_bound, ci.upper_bound], y=["Lift", "Lift"],
        mode="lines", line=dict(color=_CI_LINE, width=3), name="95% CI",
    ))
    # end caps
    fig.add_trace(go.Scatter(
        x=[ci.lower_bound, ci.upper_bound], y=["Lift", "Lift"],
        mode="markers",
        marker=dict(symbol="line-ns", size=10, color=_CI_LINE,
                    line=dict(color=_CI_LINE, width=2)),
        showlegend=False,
    ))
    # observed lift dot
    fig.add_trace(go.Scatter(
        x=[m.absolute_difference], y=["Lift"],
        mode="markers",
        marker=dict(size=13, color=_LIFT_DOT, line=dict(color=_BG, width=2)),
        name="Observed lift",
    ))

    fig.update_layout(
        _dark_layout(
            title=f"{int(ci.confidence_level * 100)}% Confidence Interval for Lift",
            xaxis=dict(
                title="Difference in conversion rate",
                tickformat=".2%",
                gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID,
                tickfont=dict(color=_TEXT), title_font=dict(color=_TEXT),
            ),
            height=280,
            showlegend=False,
            margin=dict(l=52, r=24, t=52, b=44),
        )
    )
    return fig


def z_score_plot(result: AbTestResult) -> go.Figure:
    """
    Standard normal curve with:
    - critical region(s) shaded in red
    - observed z-score marked with a vertical line + annotation
    """
    z_obs   = result.z_test.z_score
    alpha   = result.experiment.alpha
    z_crit  = float(stats.norm.ppf(1 - alpha / 2))   # two-sided

    xs = np.linspace(-4.5, 4.5, 400)
    ys = stats.norm.pdf(xs)

    fig = go.Figure()

    # ── body of the curve ──
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines",
        line=dict(color=_CI_LINE, width=2),
        fill="tozeroy", fillcolor="rgba(139,144,167,0.08)",
        showlegend=False,
    ))

    # ── critical regions (two-sided) ──
    def _shade(x_from: float, x_to: float) -> None:
        mask = (xs >= x_from) & (xs <= x_to)
        x_seg = np.concatenate([[x_from], xs[mask], [x_to]])
        y_seg = np.concatenate([[0], ys[mask], [0]])
        fig.add_trace(go.Scatter(
            x=x_seg, y=y_seg, mode="lines",
            fill="tozeroy", fillcolor="rgba(248,113,113,0.25)",
            line=dict(color=_CRITICAL, width=1),
            showlegend=False,
        ))

    _shade(-4.5, -z_crit)
    _shade(z_crit,  4.5)

    # ── critical boundary lines ──
    for xv in (-z_crit, z_crit):
        fig.add_vline(
            x=xv,
            line=dict(color=_CRITICAL, width=1, dash="dash"),
            annotation_text=f"±{z_crit:.2f}",
            annotation_font_color=_CRITICAL,
            annotation_font_size=10,
        )

    # ── observed z-score line ──
    fig.add_vline(
        x=z_obs,
        line=dict(color=_LIFT_DOT, width=2),
        annotation_text=f"z = {z_obs:.3f}",
        annotation_font_color=_LIFT_DOT,
        annotation_font_size=11,
    )

    fig.update_layout(
        _dark_layout(
            title="Z-Score Distribution",
            xaxis=dict(
                title="Standard deviations from mean",
                gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID,
                tickfont=dict(color=_TEXT), title_font=dict(color=_TEXT),
            ),
            yaxis=dict(
                title="Density",
                gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID,
                tickfont=dict(color=_TEXT), title_font=dict(color=_TEXT),
                showgrid=False,
            ),
            height=300,
            showlegend=False,
        )
    )
    return fig


def distribution_plot(result: AbTestResult, points: int = 300) -> go.Figure:
    """Normal approximation of the two conversion rate distributions."""
    m  = result.metrics
    ex = result.experiment

    std_a = np.sqrt(m.conversion_rate_a * (1 - m.conversion_rate_a) / ex.visitors_a)
    std_b = np.sqrt(m.conversion_rate_b * (1 - m.conversion_rate_b) / ex.visitors_b)
    spread = 4 * max(std_a, std_b)
    xs = np.linspace(
        max(0.0, min(m.conversion_rate_a, m.conversion_rate_b) - spread),
        min(1.0, max(m.conversion_rate_a, m.conversion_rate_b) + spread),
        points,
    )

    def _pdf(x: np.ndarray, mean: float, std: float) -> np.ndarray:
        s = max(std, 1e-9)
        return np.exp(-0.5 * ((x - mean) / s) ** 2) / (s * np.sqrt(2 * np.pi))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=_pdf(xs, m.conversion_rate_a, std_a),
        name="Control", line=dict(color=_CONTROL, width=2),
        fill="tozeroy", fillcolor="rgba(79,142,247,0.12)",
    ))
    fig.add_trace(go.Scatter(
        x=xs, y=_pdf(xs, m.conversion_rate_b, std_b),
        name="Treatment", line=dict(color=_TREATMENT, width=2),
        fill="tozeroy", fillcolor="rgba(52,211,153,0.12)",
    ))
    fig.update_layout(
        _dark_layout(
            title="Sampling Distributions",
            xaxis=dict(
                title="Conversion rate",
                gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID,
                tickfont=dict(color=_TEXT), title_font=dict(color=_TEXT),
            ),
            yaxis=dict(
                title="Density",
                gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID,
                tickfont=dict(color=_TEXT), title_font=dict(color=_TEXT),
                showgrid=False,
            ),
            height=340,
        )
    )
    return fig


def histogram(result: AbTestResult, sample_size: int = 1000, seed: int = 42) -> go.Figure:
    """Bootstrap histogram of simulated conversion rates."""
    rng = np.random.default_rng(seed)
    m   = result.metrics
    ex  = result.experiment

    sim_a = rng.binomial(ex.visitors_a, m.conversion_rate_a, size=sample_size) / ex.visitors_a
    sim_b = rng.binomial(ex.visitors_b, m.conversion_rate_b, size=sample_size) / ex.visitors_b

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=sim_a, nbinsx=35, name="Control", opacity=0.70,
        marker_color=_CONTROL, marker_line_color="rgba(0,0,0,0)",
    ))
    fig.add_trace(go.Histogram(
        x=sim_b, nbinsx=35, name="Treatment", opacity=0.70,
        marker_color=_TREATMENT, marker_line_color="rgba(0,0,0,0)",
    ))
    fig.update_layout(
        _dark_layout(
            title="Simulated Conversion Distribution",
            xaxis=dict(
                title="Conversion rate",
                gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID,
                tickfont=dict(color=_TEXT), title_font=dict(color=_TEXT),
            ),
            yaxis=dict(
                title="Frequency",
                gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID,
                tickfont=dict(color=_TEXT), title_font=dict(color=_TEXT),
            ),
            barmode="overlay",
            height=340,
        )
    )
    return fig
