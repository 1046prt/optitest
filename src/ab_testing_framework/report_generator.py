"""Human-readable report generation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .analysis import AbTestResult


def _format_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2%}"


def generate_summary(result: AbTestResult) -> str:
    metrics = result.metrics
    ci = result.confidence_interval
    effect = result.effect_size

    return (
        "A/B Testing Summary\n"
        f"Control conversion rate: {_format_pct(metrics.conversion_rate_a)}\n"
        f"Treatment conversion rate: {_format_pct(metrics.conversion_rate_b)}\n"
        f"Absolute lift: {_format_pct(metrics.absolute_difference)}\n"
        f"Relative lift: {_format_pct(metrics.relative_improvement)}\n"
        f"Z-score: {result.z_test.z_score:.3f}\n"
        f"P-value: {result.z_test.p_value:.4f}\n"
        f"95% CI for lift: {_format_pct(ci.lower_bound)} to {_format_pct(ci.upper_bound)}\n"
        f"Cohen's h: {effect.cohens_h:.3f}\n"
        f"Observed power: {result.power_analysis.power:.1%}\n"
        f"Required sample size per group: {result.power_analysis.required_sample_size_per_group:,}\n"
        f"Decision: {result.decision}\n"
        f"Recommendation: {result.recommendation}"
    )


def generate_markdown_report(result: AbTestResult) -> str:
    metrics = result.metrics
    ci = result.confidence_interval
    effect = result.effect_size

    return f"""# A/B Test Report

## Executive Summary
{result.summary}

## Key Metrics
- Control conversion rate: {_format_pct(metrics.conversion_rate_a)}
- Treatment conversion rate: {_format_pct(metrics.conversion_rate_b)}
- Absolute difference: {_format_pct(metrics.absolute_difference)}
- Relative improvement: {_format_pct(metrics.relative_improvement)}
- Z-score: {result.z_test.z_score:.3f}
- P-value: {result.z_test.p_value:.4f}
- 95% CI: {_format_pct(ci.lower_bound)} to {_format_pct(ci.upper_bound)}
- Cohen's h: {effect.cohens_h:.3f}
- Observed power: {result.power_analysis.power:.1%}
- Required sample size per group: {result.power_analysis.required_sample_size_per_group:,}

## Decision
{result.decision}

## Recommendation
{result.recommendation}
"""


def save_report(result: AbTestResult, output_dir: str | Path = "reports", stem: str | None = None) -> dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_stem = stem or f"ab_test_report_{timestamp}"
    markdown_path = output_path / f"{file_stem}.md"
    json_path = output_path / f"{file_stem}.json"

    markdown_path.write_text(generate_markdown_report(result), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "summary": result.summary,
                "decision": result.decision,
                "recommendation": result.recommendation,
                "experiment": result.experiment.to_dict(),
                "metrics": {
                    "conversion_rate_a": result.metrics.conversion_rate_a,
                    "conversion_rate_b": result.metrics.conversion_rate_b,
                    "absolute_difference": result.metrics.absolute_difference,
                    "relative_improvement": result.metrics.relative_improvement,
                },
                "z_test": {
                    "z_score": result.z_test.z_score,
                    "p_value": result.z_test.p_value,
                    "pooled_rate": result.z_test.pooled_rate,
                    "alternative": result.z_test.alternative,
                },
                "confidence_interval": {
                    "lower_bound": result.confidence_interval.lower_bound,
                    "upper_bound": result.confidence_interval.upper_bound,
                    "margin_of_error": result.confidence_interval.margin_of_error,
                    "confidence_level": result.confidence_interval.confidence_level,
                },
                "effect_size": {
                    "absolute_difference": result.effect_size.absolute_difference,
                    "relative_improvement": result.effect_size.relative_improvement,
                    "cohens_h": result.effect_size.cohens_h,
                },
                "power_analysis": {
                    "control_rate": result.power_analysis.control_rate,
                    "treatment_rate": result.power_analysis.treatment_rate,
                    "effect_size_h": result.power_analysis.effect_size_h,
                    "power": result.power_analysis.power,
                    "required_sample_size_per_group": result.power_analysis.required_sample_size_per_group,
                    "alpha": result.power_analysis.alpha,
                    "target_power": result.power_analysis.target_power,
                },
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return {"markdown": markdown_path, "json": json_path}
