"""Full test suite for the Split Testing Suite."""

from __future__ import annotations

import json
import math
from types import SimpleNamespace

import pytest

from ab_testing_framework.analysis import _build_recommendation, run_ab_test
from ab_testing_framework.confidence_interval import calculate_ci
from ab_testing_framework.data_loader import load_data
from ab_testing_framework.effect_size import calculate_effect_size
from ab_testing_framework.metrics import calculate_metrics
from ab_testing_framework.power_analysis import analyze_power, estimate_power, estimate_sample_size
from ab_testing_framework.report_generator import generate_markdown_report, generate_summary, save_report
from ab_testing_framework.validation import ExperimentInputModel, validate_input
from ab_testing_framework.z_test import perform_z_test


# VALIDATION

def test_validate_input_returns_clean_dataclass():
    exp = validate_input(100, 12, 120, 18)
    assert exp.visitors_a == 100
    assert exp.conversions_b == 18
    assert exp.alpha == 0.05


def test_validate_input_to_dict():
    exp = validate_input(100, 10, 200, 20)
    d = exp.to_dict()
    assert d["visitors_a"] == 100
    assert d["conversions_b"] == 20
    assert d["alpha"] == 0.05


@pytest.mark.parametrize(
    "kwargs, expected_message",
    [
        (
            {"visitors_a": 0, "conversions_a": 0, "visitors_b": 10, "conversions_b": 1},
            "visitor counts must be greater than zero",
        ),
        (
            {"visitors_a": 10, "conversions_a": -1, "visitors_b": 10, "conversions_b": 1},
            "conversion counts cannot be negative",
        ),
        (
            {"visitors_a": 10, "conversions_a": 11, "visitors_b": 10, "conversions_b": 1},
            "conversions_a cannot exceed visitors_a",
        ),
        (
            {"visitors_a": 10, "conversions_a": 1, "visitors_b": 10, "conversions_b": 11},
            "conversions_b cannot exceed visitors_b",
        ),
        (
            {"visitors_a": 10, "conversions_a": 1, "visitors_b": 10, "conversions_b": 1, "alpha": 0},
            "alpha must be between 0 and 1",
        ),
        (
            {"visitors_a": 10, "conversions_a": 1, "visitors_b": 10, "conversions_b": 1, "alpha": 1},
            "alpha must be between 0 and 1",
        ),
    ],
)
def test_validate_input_rejects_invalid_data(kwargs, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        validate_input(**kwargs)


def test_validate_input_rejects_non_integer_values():
    with pytest.raises(ValueError, match="must be a whole number"):
        validate_input(10.5, 1, 10, 1)


def test_validate_input_accepts_whole_float_values():
    exp = validate_input(10.0, 1.0, 20.0, 2.0)
    assert exp.visitors_a == 10
    assert exp.conversions_b == 2


def test_validate_input_rejects_non_numeric_alpha():
    with pytest.raises(ValueError, match="Input should be a valid number"):
        validate_input(10, 1, 10, 1, alpha="bad")


def test_experiment_input_model_rejects_non_mapping():
    with pytest.raises(TypeError, match="must be provided as a mapping"):
        ExperimentInputModel.model_validate(None)


def test_experiment_input_model_rejects_non_mapping():
    with pytest.raises(TypeError, match="must be provided as a mapping"):
        ExperimentInputModel.model_validate(None)


# METRICS

def test_metrics_basic():
    exp = validate_input(1000, 100, 1000, 120)
    m = calculate_metrics(exp)
    assert m.conversion_rate_a == pytest.approx(0.10)
    assert m.conversion_rate_b == pytest.approx(0.12)
    assert m.absolute_difference == pytest.approx(0.02)
    assert m.relative_improvement == pytest.approx(0.20)


def test_metrics_zero_baseline_returns_none():
    """relative_improvement must be None, not inf, when control rate is zero."""
    exp = validate_input(1000, 0, 1000, 10)
    m = calculate_metrics(exp)
    assert m.relative_improvement is None
    assert math.isfinite(m.absolute_difference)


def test_metrics_no_lift():
    exp = validate_input(500, 50, 500, 50)
    m = calculate_metrics(exp)
    assert m.absolute_difference == 0.0
    assert m.relative_improvement == pytest.approx(0.0)


# EFFECT SIZE

def test_effect_size_zero_baseline_returns_none():
    """relative_improvement in EffectSizeResult must also be None, not inf."""
    exp = validate_input(1000, 0, 1000, 10)
    es = calculate_effect_size(exp)
    assert es.relative_improvement is None


def test_effect_size_cohens_h_positive_lift():
    exp = validate_input(10000, 450, 10000, 520)
    es = calculate_effect_size(exp)
    assert es.cohens_h > 0
    assert math.isfinite(es.cohens_h)


def test_effect_size_no_lift():
    exp = validate_input(1000, 100, 1000, 100)
    es = calculate_effect_size(exp)
    assert es.cohens_h == pytest.approx(0.0)
    assert es.absolute_difference == 0.0


# Z-TEST

def test_z_test_two_sided_positive_lift():
    exp = validate_input(10000, 450, 10000, 520)
    r = perform_z_test(exp, alternative="two-sided")
    assert r.p_value < 0.05
    # rate_b (0.052) > rate_a (0.045) → difference > 0 → z_score > 0
    assert r.z_score > 0
    assert r.alternative == "two-sided"


def test_z_test_two_sided_no_lift():
    exp = validate_input(5000, 250, 5000, 250)
    r = perform_z_test(exp, alternative="two-sided")
    assert r.p_value == pytest.approx(1.0, abs=0.01)
    assert r.z_score == pytest.approx(0.0, abs=1e-9)


def test_z_test_one_sided_larger():
    exp = validate_input(10000, 450, 10000, 520)
    two = perform_z_test(exp, alternative="two-sided")
    one = perform_z_test(exp, alternative="larger")
    # one-sided p is roughly half of two-sided for same z
    assert one.p_value == pytest.approx(two.p_value / 2, rel=0.05)


def test_z_test_invalid_alternative():
    exp = validate_input(100, 10, 100, 12)
    with pytest.raises(ValueError, match="alternative must be one of"):
        perform_z_test(exp, alternative="unknown")


def test_z_test_zero_standard_error():
    """When both groups have rate=0, SE=0 and z_score should be 0."""
    exp = validate_input(100, 0, 100, 0)
    r = perform_z_test(exp)
    assert r.z_score == 0.0
    assert math.isfinite(r.p_value)


# CONFIDENCE INTERVAL

def test_ci_positive_lift_excludes_zero():
    exp = validate_input(10000, 450, 10000, 520)
    ci = calculate_ci(exp)
    assert ci.lower_bound > 0
    assert ci.upper_bound > ci.lower_bound
    assert ci.confidence_level == pytest.approx(0.95)


def test_ci_no_lift_spans_zero():
    exp = validate_input(5000, 250, 5000, 250)
    ci = calculate_ci(exp)
    assert ci.lower_bound < 0
    assert ci.upper_bound > 0


def test_ci_custom_confidence_level():
    exp = validate_input(10000, 450, 10000, 520)
    ci_99 = calculate_ci(exp, confidence_level=0.99)
    ci_95 = calculate_ci(exp, confidence_level=0.95)
    # wider interval at higher confidence
    assert ci_99.margin_of_error > ci_95.margin_of_error


def test_ci_invalid_confidence_level():
    exp = validate_input(100, 10, 100, 12)
    with pytest.raises(ValueError, match="confidence_level must be between 0 and 1"):
        calculate_ci(exp, confidence_level=1.5)


# ANALYSIS (end-to-end)

def test_run_ab_test_detects_positive_lift():
    result = run_ab_test(10000, 450, 10000, 520)
    assert result.decision == "Reject H\u2080"
    assert result.z_test.p_value < 0.05
    assert result.metrics.conversion_rate_b > result.metrics.conversion_rate_a
    assert result.confidence_interval.lower_bound > 0
    assert "Deploy Version B" in result.recommendation
    assert result.is_statistically_significant is True


def test_run_ab_test_handles_no_lift():
    result = run_ab_test(5000, 250, 5000, 250)
    assert result.decision == "Fail to reject H\u2080"
    assert result.metrics.absolute_difference == 0.0
    assert result.is_statistically_significant is False
    assert "Hold the rollout" in result.recommendation


def test_run_ab_test_negative_lift():
    """Significant negative effect → 'Do not deploy' recommendation."""
    result = run_ab_test(10000, 520, 10000, 450)
    assert result.is_statistically_significant is True
    assert result.confidence_interval.upper_bound < 0
    assert "Do not deploy" in result.recommendation


def test_run_ab_test_alternative_parameter():
    r_two  = run_ab_test(10000, 450, 10000, 520, alternative="two-sided")
    r_one  = run_ab_test(10000, 450, 10000, 520, alternative="larger")
    assert r_two.z_test.alternative == "two-sided"
    assert r_one.z_test.alternative == "larger"
    assert r_one.z_test.p_value < r_two.z_test.p_value


def test_run_ab_test_invalid_alternative():
    with pytest.raises(ValueError, match="alternative must be one of"):
        run_ab_test(10000, 450, 10000, 520, alternative="bad")


def test_run_ab_test_summary_contains_alternative():
    result = run_ab_test(10000, 450, 10000, 520, alternative="two-sided")
    assert "two-sided" in result.summary


def test_build_recommendation_inconclusive_branch():
    metrics = SimpleNamespace(relative_improvement=0.1)
    z_test = SimpleNamespace(p_value=0.03)
    confidence_interval = SimpleNamespace(lower_bound=-0.01, upper_bound=0.02, confidence_level=0.95)
    experiment = SimpleNamespace(alpha=0.05)

    recommendation = _build_recommendation(metrics, z_test, confidence_interval, experiment)

    assert "inconclusive" in recommendation.lower()


@pytest.mark.parametrize(
    "value, expected",
    [
        (0.0005, "p < 0.001"),
        (0.005, "p < 0.01"),
        (0.03, "p < 0.05"),
        (0.2, "not significant"),
    ],
)
def test_dashboard_pval_badge_thresholds(value, expected):
    from dashboard.app import _pval_badge

    assert expected.replace("<", "&lt;") in _pval_badge(value)
# POWER ANALYSIS

def test_power_analysis_reports_sample_size_and_power():
    r = analyze_power(10000, 450, 10000, 520)
    assert 0.0 <= r.power <= 1.0
    assert r.required_sample_size_per_group > 0
    assert r.effect_size_h > 0


def test_power_analysis_zero_effect():
    """Zero lift → power equals alpha (no discriminative ability)."""
    r = analyze_power(5000, 250, 5000, 250)
    assert r.power == pytest.approx(r.alpha, abs=0.01)


def test_estimate_power_shape():
    p = estimate_power(10000, 450, 10000, 520)
    assert 0.0 <= p <= 1.0


def test_estimate_sample_size_basic():
    n = estimate_sample_size(baseline_rate=0.05, expected_rate=0.06)
    assert n > 0
    assert isinstance(n, int)


def test_estimate_sample_size_validates_parameters():
    with pytest.raises(ValueError, match="baseline_rate must be between 0 and 1"):
        estimate_sample_size(0.0, 0.1)
    with pytest.raises(ValueError, match="target_power must be between 0 and 1"):
        estimate_sample_size(0.1, 0.2, target_power=1.0)
    with pytest.raises(ValueError, match="alpha must be between 0 and 1"):
        estimate_sample_size(0.1, 0.2, alpha=0.0)


def test_estimate_sample_size_raises_on_equal_rates():
    """Equal rates produce zero effect — must raise, not return a wrong number."""
    with pytest.raises(ValueError, match="no detectable effect"):
        estimate_sample_size(0.05, 0.05)

# REPORT GENERATOR

def test_report_generation_includes_summary_fields():
    result = run_ab_test(10000, 450, 10000, 520)
    summary  = generate_summary(result)
    markdown = generate_markdown_report(result)

    assert "A/B Testing Summary" in summary
    assert "Decision" in summary
    assert "Recommendation" in summary
    assert "# A/B Test Report" in markdown
    assert "## Recommendation" in markdown


def test_report_handles_none_relative_improvement():
    """When control rate is zero, relative_improvement is None — must not crash."""
    result = run_ab_test(1000, 0, 1000, 10)
    summary  = generate_summary(result)
    markdown = generate_markdown_report(result)
    assert "N/A" in summary
    assert "N/A" in markdown


def test_report_includes_test_type():
    result = run_ab_test(10000, 450, 10000, 520, alternative="two-sided")
    summary = generate_summary(result)
    assert "two-sided" in summary


def test_save_report_persists_files(tmp_path):
    result = run_ab_test(10000, 450, 10000, 520)
    paths  = save_report(result, output_dir=tmp_path, stem="experiment_summary")

    assert paths["markdown"].exists()
    assert paths["json"].exists()
    assert set(paths.keys()) == {"markdown", "json"}
    assert paths["markdown"].read_text(encoding="utf-8").startswith("# A/B Test Report")

    data = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert "metrics" in data
    assert "z_test" in data
    assert "power_analysis" in data


def test_save_report_json_null_for_none_relative_improvement(tmp_path):
    result = run_ab_test(1000, 0, 1000, 10)
    paths  = save_report(result, output_dir=tmp_path, stem="zero_baseline")
    data   = json.loads(paths["json"].read_text(encoding="utf-8"))
    # JSON null → Python None
    assert data["metrics"]["relative_improvement"] is None


def test_power_analysis_is_reflected_in_summary():
    result = run_ab_test(10000, 450, 10000, 520)
    assert "Required sample size per group" in generate_summary(result)


# DATA LOADER

def test_load_data_aggregated_single_row(tmp_path):
    csv = tmp_path / "single.csv"
    csv.write_text(
        "visitors_a,conversions_a,visitors_b,conversions_b\n"
        "10000,450,10000,520\n",
        encoding="utf-8",
    )
    exp = load_data(csv)
    assert exp.visitors_a == 10000
    assert exp.conversions_b == 520


def test_load_data_aggregates_multiple_rows(tmp_path):
    csv = tmp_path / "segmented.csv"
    csv.write_text(
        "visitors_a,conversions_a,visitors_b,conversions_b\n"
        "100,4,100,6\n"
        "200,8,200,10\n",
        encoding="utf-8",
    )
    exp = load_data(csv)
    assert exp.visitors_a == 300
    assert exp.conversions_b == 16


def test_load_data_per_user_format(tmp_path):
    csv = tmp_path / "per_user.csv"
    csv.write_text(
        "variant,converted\n"
        "A,0\nA,1\nA,0\nA,1\nA,0\n"   # 5 visitors, 2 conversions
        "B,1\nB,1\nB,0\nB,1\nB,0\n",  # 5 visitors, 3 conversions
        encoding="utf-8",
    )
    exp = load_data(csv)
    assert exp.visitors_a == 5
    assert exp.conversions_a == 2
    assert exp.visitors_b == 5
    assert exp.conversions_b == 3


def test_load_data_per_user_case_insensitive(tmp_path):
    csv = tmp_path / "case.csv"
    csv.write_text(
        "variant,converted\n"
        "a,0\na,1\nb,1\nb,0\n",
        encoding="utf-8",
    )
    exp = load_data(csv)
    assert exp.visitors_a == 2
    assert exp.visitors_b == 2


def test_load_data_per_user_unknown_variant(tmp_path):
    csv = tmp_path / "bad_variant.csv"
    csv.write_text("variant,converted\nC,1\nD,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown variant labels"):
        load_data(csv)


def test_load_data_requires_expected_columns(tmp_path):
    csv = tmp_path / "invalid.csv"
    csv.write_text("visitors_a,conversions_a\n10,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required columns"):
        load_data(csv)


def test_load_data_rejects_conversions_exceeding_visitors_per_row(tmp_path):
    csv = tmp_path / "bad.csv"
    csv.write_text(
        "visitors_a,conversions_a,visitors_b,conversions_b\n"
        "10,15,10,5\n",                 # conversions_a > visitors_a
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="conversions_a > visitors_a"):
        load_data(csv)


def test_load_data_sample_file():
    """The bundled sample_experiment.csv must load without error."""
    from pathlib import Path
    sample = Path(__file__).resolve().parents[1] / "data" / "sample_experiment.csv"
    exp = load_data(sample)
    assert exp.visitors_a > 0
    assert exp.visitors_b > 0


# ══════════════════════════════════════════════════════════════════════════════
# CHI-SQUARE TEST
# ══════════════════════════════════════════════════════════════════════════════

from ab_testing_framework.chi_square import perform_chi_square_test


def test_chi_square_positive_lift_significant():
    exp = validate_input(10000, 450, 10000, 520)
    r = perform_chi_square_test(exp)
    assert r.p_value < 0.05
    assert r.chi2_stat > 0
    assert r.degrees_of_freedom == 1
    assert 0.0 <= r.cramers_v <= 1.0


def test_chi_square_no_lift_not_significant():
    exp = validate_input(5000, 250, 5000, 250)
    r = perform_chi_square_test(exp)
    assert r.p_value > 0.05
    assert r.cramers_v == pytest.approx(0.0, abs=1e-9)


def test_chi_square_p_value_matches_z_test_two_sided():
    """Without Yates, χ² = z², so p-values should be very close."""
    exp = validate_input(10000, 450, 10000, 520)
    z   = perform_z_test(exp, alternative="two-sided")
    cs  = perform_chi_square_test(exp, yates=False)
    assert cs.p_value == pytest.approx(z.p_value, rel=0.01)


def test_chi_square_yates_auto_applied_for_small_samples():
    """Small expected counts should trigger Yates automatically."""
    exp = validate_input(10, 1, 10, 3)
    r = perform_chi_square_test(exp)
    assert r.yates_correction is True


def test_chi_square_yates_not_applied_for_large_samples():
    """Large samples — all expected counts well above 5 — no Yates."""
    exp = validate_input(10000, 450, 10000, 520)
    r = perform_chi_square_test(exp)
    assert r.yates_correction is False


def test_chi_square_explicit_yates_override():
    exp = validate_input(10000, 450, 10000, 520)
    with_yates    = perform_chi_square_test(exp, yates=True)
    without_yates = perform_chi_square_test(exp, yates=False)
    assert with_yates.chi2_stat < without_yates.chi2_stat
    assert with_yates.p_value > without_yates.p_value


def test_chi_square_degenerate_all_zero():
    """All-zero conversions — degenerate table must not crash."""
    exp = validate_input(100, 0, 100, 0)
    r = perform_chi_square_test(exp)
    assert r.chi2_stat == 0.0
    assert math.isfinite(r.p_value)


def test_chi_square_in_run_ab_test():
    result = run_ab_test(10000, 450, 10000, 520)
    cs = result.chi_square
    assert isinstance(cs.chi2_stat, float)
    assert isinstance(cs.p_value, float)
    assert isinstance(cs.yates_correction, bool)
    assert 0.0 <= cs.cramers_v <= 1.0


def test_chi_square_in_summary_report():
    result = run_ab_test(10000, 450, 10000, 520)
    summary = generate_summary(result)
    assert "Chi-square" in summary
    assert "Cram" in summary   # Cramér — avoid encoding issues in match


def test_chi_square_in_markdown_report():
    result = run_ab_test(10000, 450, 10000, 520)
    md = generate_markdown_report(result)
    assert "Chi-square" in md
    assert "Cram" in md


def test_chi_square_in_json_export(tmp_path):
    result = run_ab_test(10000, 450, 10000, 520)
    paths = save_report(result, output_dir=tmp_path, stem="chi_sq_test")
    data = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert "chi_square" in data
    assert "chi2_stat" in data["chi_square"]
    assert "cramers_v" in data["chi_square"]


# VISUALIZATION SMOKE TESTS

import plotly.graph_objects as go
from ab_testing_framework.visualization import (
    bar_chart, confidence_plot, distribution_plot, histogram, z_score_plot,
)


@pytest.fixture(scope="module")
def sample_result():
    """Shared AbTestResult used by all visualization tests."""
    return run_ab_test(10000, 450, 10000, 520)


def test_bar_chart_returns_figure(sample_result):
    fig = bar_chart(sample_result)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1          # single Bar trace
    assert fig.data[0].type == "bar"


def test_confidence_plot_returns_figure(sample_result):
    fig = confidence_plot(sample_result)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 2          # CI line + lift dot


def test_z_score_plot_returns_figure(sample_result):
    fig = z_score_plot(sample_result)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 3          # normal curve + two critical region fills


def test_distribution_plot_returns_figure(sample_result):
    fig = distribution_plot(sample_result)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2          # control + treatment curves


def test_histogram_returns_figure(sample_result):
    fig = histogram(sample_result)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2          # control + treatment histograms


def test_visualization_figures_have_titles(sample_result):
    """All charts must carry a non-empty title."""
    charts = [
        bar_chart(sample_result),
        confidence_plot(sample_result),
        z_score_plot(sample_result),
        distribution_plot(sample_result),
        histogram(sample_result),
    ]
    for fig in charts:
        assert fig.layout.title.text, f"Missing title on {fig}"
