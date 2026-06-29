import pytest

from ab_testing_framework.analysis import run_ab_test
from ab_testing_framework.power_analysis import analyze_power, estimate_sample_size, estimate_power
from ab_testing_framework.report_generator import generate_markdown_report, generate_summary, save_report
from ab_testing_framework.data_loader import load_data
from ab_testing_framework.validation import validate_input


def test_validate_input_returns_clean_dataclass():
    experiment = validate_input(100, 12, 120, 18)

    assert experiment.visitors_a == 100
    assert experiment.conversions_b == 18
    assert experiment.alpha == 0.05


def test_run_ab_test_detects_positive_lift():
    result = run_ab_test(10000, 450, 10000, 520)

    assert result.decision == "Reject H0"
    assert result.z_test.p_value < 0.05
    assert result.metrics.conversion_rate_b > result.metrics.conversion_rate_a
    assert result.confidence_interval.lower_bound > 0
    assert "Deploy Version B" in result.recommendation


def test_run_ab_test_handles_no_lift():
    result = run_ab_test(5000, 250, 5000, 250)

    assert result.decision == "Fail to reject H0"
    assert result.z_test.p_value == pytest.approx(0.5, abs=0.5)
    assert result.metrics.absolute_difference == 0
    assert result.is_statistically_significant is False
    assert "Hold the rollout" in result.recommendation


@pytest.mark.parametrize(
    "kwargs, expected_message",
    [
        ({"visitors_a": 0, "conversions_a": 0, "visitors_b": 10, "conversions_b": 1}, "visitor counts must be greater than zero"),
        ({"visitors_a": 10, "conversions_a": -1, "visitors_b": 10, "conversions_b": 1}, "conversion counts cannot be negative"),
        ({"visitors_a": 10, "conversions_a": 11, "visitors_b": 10, "conversions_b": 1}, "conversions_a cannot exceed visitors_a"),
        ({"visitors_a": 10, "conversions_a": 1, "visitors_b": 10, "conversions_b": 11}, "conversions_b cannot exceed visitors_b"),
    ],
)
def test_validate_input_rejects_invalid_data(kwargs, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        validate_input(**kwargs)


def test_validate_input_rejects_non_integer_values():
    with pytest.raises(ValueError, match="must be a whole number"):
        validate_input(10.5, 1, 10, 1)


def test_load_data_requires_expected_columns(tmp_path):
    csv_file = tmp_path / "invalid.csv"
    csv_file.write_text("visitors_a,conversions_a\n10,1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        load_data(csv_file)


def test_report_generation_includes_summary_fields():
    result = run_ab_test(10000, 450, 10000, 520)

    summary = generate_summary(result)
    markdown = generate_markdown_report(result)

    assert "A/B Testing Summary" in summary
    assert "Decision" in summary
    assert "# A/B Test Report" in markdown
    assert "Recommendation" in markdown


def test_power_analysis_reports_sample_size_and_power():
    result = analyze_power(10000, 450, 10000, 520)

    assert 0 <= result.power <= 1
    assert result.required_sample_size_per_group > 0
    assert result.effect_size_h > 0


def test_estimate_power_matches_observed_input_shape():
    power = estimate_power(10000, 450, 10000, 520)

    assert 0 <= power <= 1


def test_estimate_sample_size_validates_parameters():
    with pytest.raises(ValueError, match="baseline_rate must be between 0 and 1"):
        estimate_sample_size(0.0, 0.1)

    with pytest.raises(ValueError, match="target_power must be between 0 and 1"):
        estimate_sample_size(0.1, 0.2, target_power=1.0)


def test_power_analysis_is_reflected_in_result():
    result = run_ab_test(10000, 450, 10000, 520)

    assert result.power_analysis.required_sample_size_per_group > 0
    assert "Required sample size per group" in generate_summary(result)


def test_save_report_persists_files(tmp_path):
    result = run_ab_test(10000, 450, 10000, 520)

    paths = save_report(result, output_dir=tmp_path, stem="experiment_summary")

    assert paths["markdown"].exists()
    assert paths["json"].exists()
    assert paths["markdown"].read_text(encoding="utf-8").startswith("# A/B Test Report")


def test_load_data_aggregates_csv(tmp_path):
    csv_file = tmp_path / "experiment.csv"
    csv_file.write_text(
        "visitors_a,conversions_a,visitors_b,conversions_b\n"
        "100,4,100,6\n"
        "200,8,200,10\n",
        encoding="utf-8",
    )

    experiment = load_data(csv_file)

    assert experiment.visitors_a == 300
    assert experiment.conversions_b == 16
