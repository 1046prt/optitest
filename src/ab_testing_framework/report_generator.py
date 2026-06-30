"""Report generation"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .analysis import AbTestResult


def _fmt_pct(value: float | None, decimals: int = 2) -> str:
    """Format a float as a percentage, handling None gracefully."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}%}"


def generate_summary(result: AbTestResult) -> str:
    m  = result.metrics
    ci = result.confidence_interval
    es = result.effect_size
    pa = result.power_analysis

    lines = [
        "A/B Testing Summary",
        f"Control conversion rate:        {_fmt_pct(m.conversion_rate_a)}",
        f"Treatment conversion rate:       {_fmt_pct(m.conversion_rate_b)}",
        f"Absolute lift:                   {_fmt_pct(m.absolute_difference)}",
        f"Relative lift:                   {_fmt_pct(m.relative_improvement)}",
        f"Z-score:                         {result.z_test.z_score:.4f}",
        f"P-value:                         {result.z_test.p_value:.4f}",
        f"Test type:                       {result.z_test.alternative}",
        f"{int(ci.confidence_level * 100)}% CI for lift:               "
        f"{_fmt_pct(ci.lower_bound, 4)} to {_fmt_pct(ci.upper_bound, 4)}",
        f"Cohen's h:                       {es.cohens_h:.4f}",
        f"Observed power:                  {pa.power:.1%}",
        f"Required sample size per group:  {pa.required_sample_size_per_group:,}",
        f"Decision:                        {result.decision}",
        f"Recommendation:                  {result.recommendation}",
    ]
    return "\n".join(lines)


def generate_markdown_report(result: AbTestResult) -> str:
    m  = result.metrics
    ci = result.confidence_interval
    es = result.effect_size
    pa = result.power_analysis

    return f"""# A/B Test Report

## Executive Summary
{result.summary}

## Key Metrics

| Metric | Value |
|--------|-------|
| Control conversion rate | {_fmt_pct(m.conversion_rate_a)} |
| Treatment conversion rate | {_fmt_pct(m.conversion_rate_b)} |
| Absolute lift | {_fmt_pct(m.absolute_difference)} |
| Relative lift | {_fmt_pct(m.relative_improvement)} |
| Z-score | {result.z_test.z_score:.4f} |
| P-value | {result.z_test.p_value:.4f} |
| Test type | {result.z_test.alternative} |
| {int(ci.confidence_level * 100)}% CI lower | {_fmt_pct(ci.lower_bound, 4)} |
| {int(ci.confidence_level * 100)}% CI upper | {_fmt_pct(ci.upper_bound, 4)} |
| Cohen's h | {es.cohens_h:.4f} |
| Observed power | {pa.power:.1%} |
| Required n / group | {pa.required_sample_size_per_group:,} |

## Decision
**{result.decision}**

## Recommendation
{result.recommendation}
"""


def save_report(
    result: AbTestResult,
    output_dir: str | Path = "reports",
    stem: str | None = None,
) -> dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_stem = stem or f"ab_test_report_{timestamp}"
    markdown_path = output_path / f"{file_stem}.md"
    json_path = output_path / f"{file_stem}.json"

    markdown_path.write_text(generate_markdown_report(result), encoding="utf-8")

    # relative_improvement may be None; serialise as null in JSON
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
