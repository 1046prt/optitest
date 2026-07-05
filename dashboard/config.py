"""Configuration and constants for the Split Testing Suite dashboard."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "dashboard" / "assets"
FAVICON_PATH = ASSETS_DIR / "favicon.svg"
SRC_PATH = PROJECT_ROOT / "src"
REPORTS_DIR = PROJECT_ROOT / "reports"

APP_TITLE = "Split Testing Suite"

DEFAULTS = {
    "visitors_a": 10_000,
    "conversions_a": 450,
    "visitors_b": 10_000,
    "conversions_b": 520,
}

ALPHA_DEFAULT = 0.05
ALPHA_MIN = 0.01
ALPHA_MAX = 0.20
ALPHA_STEP = 0.01

ALTERNATIVE_OPTIONS = ["two-sided", "larger", "smaller"]

SIDEBAR_LABELS = {
    "title": "Split Testing Suite",
    "data_source": "Data source",
    "upload_caption": "CSV upload is optional. If it fails, the manual inputs below remain usable.",
    "control": "Control (A)",
    "treatment": "Treatment (B)",
    "csv_preview": "Uploaded CSV preview",
    "csv_preview_caption": (
        "If the CSV loads successfully, its values override the manual inputs. "
        "If it fails, the dashboard keeps the values above."
    ),
    "test_settings": "Test settings",
    "sample_csv": "Sample CSV format",
    "footer": (
        "<p style='font-size:0.75rem;color:#555a72;line-height:1.5;'>"
        "Two-proportion z-test · 95% CI<br>"
        "Power via statsmodels NormalIndPower."
        "</p>"
    ),
}

CSV_HELP_TEXT = (
    "Upload an aggregated CSV with visitors_a/conversions_a/visitors_b/conversions_b, "
    "or a per-user CSV with variant and converted. Commas, semicolons, tabs, and UTF-8 BOMs are handled automatically."
)

SAMPLE_CSV = (
    "visitors_a,conversions_a,visitors_b,conversions_b\n"
    "10000,450,10000,520\n"
)

INPUT_HELP = {
    "visitors_a": "Total visitors in the control group. Must be greater than zero.",
    "conversions_a": "Number of conversions in the control group. Must not exceed visitors.",
    "visitors_b": "Total visitors in the treatment group. Must be greater than zero.",
    "conversions_b": "Number of conversions in the treatment group. Must not exceed visitors.",
    "alpha": "Threshold for rejecting H₀. Common values: 0.05 (standard) · 0.01 (strict) · 0.10 (exploratory).",
    "alternative": (
        "two-sided: test whether B ≠ A (most common).\n"
        "larger: test whether B > A (directional, more power).\n"
        "smaller: test whether B < A."
    ),
}
